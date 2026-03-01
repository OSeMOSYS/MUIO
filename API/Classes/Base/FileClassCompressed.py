import os
import io
import json
import gzip
import time
import tempfile
import warnings
from pathlib import Path
from typing import Any, List, Optional
from contextlib import contextmanager

# Optional fast JSON libs
try:
    import orjson  # type: ignore
    _HAS_ORJSON = True
except Exception:
    _HAS_ORJSON = False

try:
    import ujson  # type: ignore
    _HAS_UJSON = True
except Exception:
    _HAS_UJSON = False

# Optional Zstandard compression
try:
    import zstandard as zstd  # type: ignore
    _HAS_ZSTD = True
except Exception:
    _HAS_ZSTD = False


class File:
    """
    Cross-platform, atomic JSON read/write with optional compression and fast JSON libs.

    - Plain JSON:      "file.json"
    - Gzip JSON:       "file.json.gz"
    - Zstd JSON:       "file.json.zst"   (requires: pip install zstandard)

    Uses orjson (bytes, fastest) if available; otherwise ujson; otherwise stdlib json.
    All text paths use UTF-8. Atomic writes: temp -> flush -> fsync -> os.replace.

    Backward compatibility helpers:
      * readFile("file.json") will also try "file.json.zst" then "file.json.gz" if "file.json" does not exist.
      * You can opt-in to default compression for writes without changing call sites.
    """

    # ---------------------------
    # Defaults / configuration (you can change these at runtime)
    # ---------------------------
    _DEFAULT_COMPRESSION: Optional[str] = 'zst'   # None | 'zst' | 'gz'
    _AUTO_EXTEND_ON_WRITE: bool = True            # If True and default compression is set, append .zst/.gz when path lacks it
    _MIRROR_LEGACY_JSON: bool = False             # If True and writing compressed, also write uncompressed .json alongside
    _ZSTD_LEVEL: int = 3                          # Good balance for APIs
    _GZIP_LEVEL: int = 6                          # Default gzip level

    # ---------------------------
    # Internal path normalizer
    # ---------------------------
    @staticmethod
    def _to_str(p) -> str:
        """Normalize str/Path/os.PathLike to str for internal use."""
        return str(p)

    # ---------------------------
    # Public configuration API
    # ---------------------------
    @staticmethod
    def configure(
        default_compression: Optional[str] = 'zst',  # 'zst' | 'gz' | None
        auto_extend_on_write: bool = True,
        mirror_legacy_json: bool = False,
        zstd_level: int = 3,
        gzip_level: int = 6,
    ) -> None:
        """
        Configure default behavior without breaking legacy call sites.
        Example:
            File.configure(default_compression='zst', mirror_legacy_json=True)
        """
        if default_compression not in (None, "zst", "gz"):
            raise ValueError("default_compression must be None, 'zst', or 'gz'")
        File._DEFAULT_COMPRESSION = default_compression
        File._AUTO_EXTEND_ON_WRITE = auto_extend_on_write
        File._MIRROR_LEGACY_JSON = mirror_legacy_json
        File._ZSTD_LEVEL = int(zstd_level)
        File._GZIP_LEVEL = int(gzip_level)

    @staticmethod
    def set_default_compression(kind: Optional[str]) -> None:
        """Shortcut: File.set_default_compression('zst') or 'gz' or None."""
        File.configure(default_compression=kind)

    @staticmethod
    def set_mirror_legacy_json(mirror: bool) -> None:
        File._MIRROR_LEGACY_JSON = bool(mirror)

    # ---------------------------
    # Path helpers
    # ---------------------------
    @staticmethod
    def _is_gzip_path(path: str) -> bool:
        path = str(path)
        return path.endswith(".gz")

    @staticmethod
    def _is_zstd_path(path: str) -> bool:
        path = str(path)
        return path.endswith(".zst")

    @staticmethod
    def _exists(path: str) -> bool:
        path = str(path)
        try:
            return Path(path).exists()
        except Exception:
            return False

    @staticmethod
    def _candidate_read_paths(path: str) -> List[str]:
        """
        Return a list of candidate paths to try for reading, preserving legacy behavior.
        If the given path exists, return [path].
        If not and it ends with '.json', also try '.json.zst' then '.json.gz'.
        Otherwise, try [path], then path+'.zst', then path+'.gz'.
        """
        path = str(path)

        if File._exists(path):
            return [path]

        # If explicitly asks for .zst/.gz and it's missing, just return [path] (will error)
        if File._is_zstd_path(path) or File._is_gzip_path(path):
            return [path]

        candidates = [path]

        if path.endswith(".json"):
            candidates.append(path + ".zst")
            candidates.append(path + ".gz")
        else:
            # If caller passed a bare stem or other extension, be helpful:
            candidates.append(path + ".zst")
            candidates.append(path + ".gz")

        # Keep unique while preserving order
        seen = set()
        uniq = []
        for p in candidates:
            if p not in seen:
                seen.add(p)
                uniq.append(p)
        return uniq

    @staticmethod
    def _effective_write_path(path: str) -> str:
        """
        Decide where to write based on default compression and the provided path.
        - If path already ends with .zst/.gz: use it as-is.
        - Else if default compression is set and auto-extend is True: append .zst/.gz.
        - Else: return original path unchanged.
        """
        path = str(path)

        if File._is_zstd_path(path) or File._is_gzip_path(path):
            return path

        if File._DEFAULT_COMPRESSION and File._AUTO_EXTEND_ON_WRITE:
            if File._DEFAULT_COMPRESSION == "zst":
                if not _HAS_ZSTD:
                    warnings.warn(
                        "Default compression 'zst' requested but 'zstandard' not installed. "
                        "Falling back to gzip.", RuntimeWarning
                    )
                    return path + ".gz"
                return path + ".zst"
            elif File._DEFAULT_COMPRESSION == "gz":
                return path + ".gz"

        return path

    @staticmethod
    def _legacy_json_path_for(effective_path: str) -> Optional[str]:
        """
        If mirroring is enabled and we're writing compressed .json.zst/.json.gz,
        return the corresponding legacy .json path to mirror. Otherwise None.
        """
        effective_path = str(effective_path)

        if not File._MIRROR_LEGACY_JSON:
            return None
        if effective_path.endswith(".json.zst"):
            return effective_path[:-4]  # strip .zst -> .json
        if effective_path.endswith(".json.gz"):
            return effective_path[:-3]  # strip .gz -> .json
        return None

    # ---------------------------
    # Robust Windows-safe atomic helpers
    # ---------------------------
    @staticmethod
    def _mkstemp_in_dir(dir_path: str, suffix: str = "") -> str:
        """
        Create a temporary file path in the target directory and CLOSE the fd immediately.
        This avoids Windows locking issues (can't re-open same file for writing twice).
        """
        dir_path = str(dir_path)
        fd, tmp_path = tempfile.mkstemp(prefix=".tmp-", suffix=suffix, dir=dir_path)
        os.close(fd)  # VERY IMPORTANT on Windows
        return tmp_path

    @staticmethod
    def _safe_remove(path: str, retries: int = 50, delay: float = 0.1) -> None:
        """Best-effort remove with retries (helps with transient Windows locks)."""
        path = str(path)
        last_err = None
        for _ in range(retries):
            try:
                if os.path.exists(path):
                    os.remove(path)
                return
            except (PermissionError, OSError) as e:
                last_err = e
                time.sleep(delay)
            except FileNotFoundError:
                return
        if os.path.exists(path):
            raise last_err or PermissionError(f"Failed to remove temp file: {path}")

    @staticmethod
    def _atomic_write_text(path: str, write_fn) -> None:
        """
        Atomic write for TEXT (str) content.
        write_fn(file_obj_text) must write to the provided text stream.
        """
        path = str(path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent))
        try:
            with open(tmp_path, mode="w", encoding="utf-8", newline="") as tmp:
                write_fn(tmp)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    @staticmethod
    def _atomic_write_bytes(path: str, write_bytes_fn) -> None:
        """
        Atomic write for BYTES content.
        write_bytes_fn(file_obj_bin) must write bytes to the provided binary stream.
        """
        path = str(path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent))
        try:
            with open(tmp_path, mode="wb") as tmp:
                write_bytes_fn(tmp)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    @staticmethod
    def _atomic_write_gzip_text(path: str, write_text_fn) -> None:
        """
        Atomic write for GZIP text content.
        write_text_fn(gzip_text_file) must write str to the provided gzip text stream.
        """
        path = str(path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent), suffix=".gz")
        try:
            with gzip.open(tmp_path, mode="wt", encoding="utf-8", newline="", compresslevel=File._GZIP_LEVEL) as gz:
                write_text_fn(gz)
                gz.flush()
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    @staticmethod
    def _atomic_write_gzip_bytes(path: str, write_bytes_fn) -> None:
        """
        Atomic write for GZIP binary content.
        write_bytes_fn(gzip_bin_file) must write BYTES to the provided gzip binary stream.
        """
        path = str(path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent), suffix=".gz")
        try:
            with gzip.open(tmp_path, mode="wb", compresslevel=File._GZIP_LEVEL) as gz:
                write_bytes_fn(gz)  # bytes into gzip stream
                gz.flush()
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    @staticmethod
    def _atomic_write_zstd_text(path: str, write_text_fn, level: int = None) -> None:
        """
        Atomic write for Zstandard TEXT content (requires zstandard).
        write_text_fn(text_file) must write str to the provided text wrapper.
        """
        path = str(path)
        if not _HAS_ZSTD:
            raise RuntimeError("zstandard is not installed; run `pip install zstandard`.")

        if level is None:
            level = File._ZSTD_LEVEL

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent), suffix=".zst")
        try:
            cctx = zstd.ZstdCompressor(level=int(level))
            with open(tmp_path, "wb") as raw:
                # Keep underlying 'raw' open until we fsync it
                with cctx.stream_writer(raw, closefd=False) as zf_bin:
                    with io.TextIOWrapper(zf_bin, encoding="utf-8", newline="") as zf_txt:
                        write_text_fn(zf_txt)
                        zf_txt.flush()
                # 'raw' is still open here
                raw.flush()
                os.fsync(raw.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    @staticmethod
    def _atomic_write_zstd_bytes(path: str, write_bytes_fn, level: int = None) -> None:
        """
        Atomic write for Zstandard BYTES content (requires zstandard).
        write_bytes_fn(bin_file) must write BYTES to the provided stream.
        """
        path = str(path)
        if not _HAS_ZSTD:
            raise RuntimeError("zstandard is not installed; run `pip install zstandard`.")

        if level is None:
            level = File._ZSTD_LEVEL

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = File._mkstemp_in_dir(str(target.parent), suffix=".zst")
        try:
            cctx = zstd.ZstdCompressor(level=int(level))
            with open(tmp_path, "wb") as raw:
                # Keep underlying 'raw' open until we fsync it
                with cctx.stream_writer(raw, closefd=False) as zf_bin:
                    write_bytes_fn(zf_bin)
                    zf_bin.flush()
                # 'raw' is still open here
                raw.flush()
                os.fsync(raw.fileno())
            os.replace(tmp_path, path)
        except Exception:
            try:
                File._safe_remove(tmp_path)
            finally:
                raise

    # ---------------------------
    # Zstd reader (as a context manager)
    # ---------------------------
    @staticmethod
    @contextmanager
    def _open_read_zstd_text(path: str):
        """
        Open a .zst file and yield a UTF-8 text stream (context manager).
        Ensures proper closing order of zstd stream and raw file.
        """
        path = str(path)
        if not _HAS_ZSTD:
            raise RuntimeError("zstandard is not installed; run `pip install zstandard`.")

        raw = open(path, "rb")
        dctx = zstd.ZstdDecompressor()
        zstream = dctx.stream_reader(raw)
        txt = io.TextIOWrapper(zstream, encoding="utf-8", newline="")
        try:
            yield txt
        finally:
            try:
                try:
                    txt.flush()
                finally:
                    txt.detach()
            except Exception:
                pass
            try:
                zstream.close()
            except Exception:
                pass
            raw.close()

    # ---------------------------
    # Readers
    # ---------------------------
    @staticmethod
    def readFile(path) -> Any:
        """
        Read JSON from file (UTF-8). Supports .json, .json.gz, .json.zst.
        If 'path' does not exist and ends with '.json', will try '.json.zst' then '.json.gz'.
        Uses orjson/ujson/json based on availability.
        """
        path = File._to_str(path)

        # Try legacy-friendly candidates
        candidates = File._candidate_read_paths(path)
        last_error = None

        for candidate in candidates:
            try:
                if File._is_zstd_path(candidate):
                    with File._open_read_zstd_text(candidate) as f:
                        if _HAS_ORJSON:
                            return orjson.loads(f.read())
                        elif _HAS_UJSON:
                            return ujson.load(f)
                        else:
                            return json.load(f)

                if File._is_gzip_path(candidate):
                    with gzip.open(candidate, mode="rt", encoding="utf-8", newline="") as f:
                        if _HAS_ORJSON:
                            return orjson.loads(f.read())
                        elif _HAS_UJSON:
                            return ujson.load(f)
                        else:
                            return json.load(f)

                # Plain file
                with open(candidate, mode="r", encoding="utf-8", newline="") as f:
                    if _HAS_ORJSON:
                        return orjson.loads(f.read())
                    elif _HAS_UJSON:
                        return ujson.load(f)
                    else:
                        return json.load(f)

            except FileNotFoundError as e:
                # Try next candidate
                last_error = e
            except Exception:
                # Bubble up non-not-found errors immediately for correctness
                raise

        # If none succeeded, raise the last FileNotFoundError or a generic one
        if last_error:
            raise last_error
        raise FileNotFoundError(f"File not found: {path}")

    @staticmethod
    def readParamFile(path) -> Any:
        """Backward-compatible alias for readFile()."""
        path = File._to_str(path)
        return File.readFile(path)

    # ---------------------------
    # Writers
    # ---------------------------
    @staticmethod
    def writeFile(data, path) -> None:
        """
        Default JSON writer: compact, UTF-8, atomic.
        Uses orjson (bytes) if available; else text with ujson/json.
        Supports .json, .json.gz, .json.zst (zstandard required for .zst).

        Backward-compat convenience:
          - If File._DEFAULT_COMPRESSION is set (e.g., 'zst') and the provided 'path'
            does not already end with .zst/.gz, we will append that extension.
          - If File._MIRROR_LEGACY_JSON is True and we write to .json.zst/.json.gz,
            we also write an uncompressed .json next to it.
        """
        path = File._to_str(path)

        # Decide effective destination path based on config
        effective_path = File._effective_write_path(path)

        def _write_orjson_bytes(fbin):
            fbin.write(orjson.dumps(data))

        def _write_ujson_text(ftxt):
            # UTF-8 output (no ASCII escaping)
            ujson.dump(data, ftxt, ensure_ascii=False)

        def _write_std_text(ftxt):
            json.dump(
                data,
                ftxt,
                ensure_ascii=False,          # keep real UTF-8 (Cyrillic etc.)
                separators=(",", ":"),       # compact form
                sort_keys=False,
            )

        try:
            # Primary write (effective path)
            if _HAS_ORJSON:
                if File._is_zstd_path(effective_path):
                    File._atomic_write_zstd_bytes(effective_path, _write_orjson_bytes, level=File._ZSTD_LEVEL)
                elif File._is_gzip_path(effective_path):
                    File._atomic_write_gzip_bytes(effective_path, _write_orjson_bytes)
                else:
                    File._atomic_write_bytes(effective_path, _write_orjson_bytes)

            elif _HAS_UJSON:
                if File._is_zstd_path(effective_path):
                    File._atomic_write_zstd_text(effective_path, _write_ujson_text, level=File._ZSTD_LEVEL)
                elif File._is_gzip_path(effective_path):
                    File._atomic_write_gzip_text(effective_path, _write_ujson_text)
                else:
                    File._atomic_write_text(effective_path, _write_ujson_text)

            else:
                if File._is_zstd_path(effective_path):
                    File._atomic_write_zstd_text(effective_path, _write_std_text, level=File._ZSTD_LEVEL)
                elif File._is_gzip_path(effective_path):
                    File._atomic_write_gzip_text(effective_path, _write_std_text)
                else:
                    File._atomic_write_text(effective_path, _write_std_text)

            # Optional legacy mirror (.json) if we wrote compressed
            legacy_json_path = File._legacy_json_path_for(effective_path)
            if legacy_json_path:
                if _HAS_ORJSON:
                    File._atomic_write_bytes(legacy_json_path, _write_orjson_bytes)
                elif _HAS_UJSON:
                    File._atomic_write_text(legacy_json_path, _write_ujson_text)
                else:
                    File._atomic_write_text(legacy_json_path, _write_std_text)

        except (IOError, IndexError):
            # Preserve your previous exception contract if needed
            raise IndexError
        except OSError:
            raise OSError

    @staticmethod
    def writeFileUJson(data, path) -> None:
        """
        Prefer ujson if present; otherwise delegate to writeFile.
        Also atomic + gzip/zstd-aware and honors default compression/mirroring config.
        """
        path = File._to_str(path)

        if _HAS_UJSON:
            # Respect default compression config
            effective_path = File._effective_write_path(path)

            def _write_ujson_text(ftxt):
                ujson.dump(data, ftxt, ensure_ascii=False)

            try:
                if File._is_zstd_path(effective_path):
                    File._atomic_write_zstd_text(effective_path, _write_ujson_text, level=File._ZSTD_LEVEL)
                elif File._is_gzip_path(effective_path):
                    File._atomic_write_gzip_text(effective_path, _write_ujson_text)
                else:
                    File._atomic_write_text(effective_path, _write_ujson_text)

                # Optional legacy mirror
                legacy_json_path = File._legacy_json_path_for(effective_path)
                if legacy_json_path:
                    File._atomic_write_text(legacy_json_path, _write_ujson_text)

            except (IOError, IndexError):
                raise IndexError
            except OSError:
                raise OSError
        else:
            # Fall back to writeFile (will use orjson or stdlib)
            File.writeFile(data, path)