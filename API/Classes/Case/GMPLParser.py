"""
Phase 1 — Pure GMPL syntax extraction.

Parses a GMPL data file (.txt / .dat) into structured objects without
semantic interpretation.  Every ``set`` and ``param`` declaration is
captured, including multi-slice blocks, headerless tables, and empty
param bodies.

Public API
----------
    GMPLParser.parse_file(path)   → GMPLParseResult
    GMPLParser.parse_string(text) → GMPLParseResult
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

# ────────────────────────────────────────────────────────────
# Data structures
# ────────────────────────────────────────────────────────────

@dataclass
class RowEntry:
    """One data row: a key string followed by numeric values."""
    key: str
    values: list[Union[int, float]]


@dataclass
class SliceBlock:
    """
    One slice of a ``param`` declaration.

    *   ``header`` – the square-bracket header tokens, e.g. ``["RE1","*","*"]``.
        ``None`` for headerless tables.
    *   ``column_labels`` – the column names after ``:`` on the header line.
    *   ``rows`` – the data rows.
    """
    header: Optional[list[str]] = None
    column_labels: list[str] = field(default_factory=list)
    rows: list[RowEntry] = field(default_factory=list)


@dataclass
class ParsedParam:
    """A complete ``param`` declaration with its name, default, and slices."""
    name: str
    default: Optional[Union[int, float]] = None
    slices: list[SliceBlock] = field(default_factory=list)


@dataclass
class GMPLParseResult:
    """Bag holding every ``set`` and ``param`` extracted from a GMPL file."""
    sets: dict[str, list[str]] = field(default_factory=dict)
    params: list[ParsedParam] = field(default_factory=list)

    # convenience
    def param_names(self) -> list[str]:
        return [p.name for p in self.params]

    def summary(self) -> str:
        lines = [f"Sets  : {len(self.sets)}"]
        for sn, sv in self.sets.items():
            lines.append(f"  {sn} ({len(sv)}) : {sv[:6]}{'...' if len(sv) > 6 else ''}")
        lines.append(f"Params: {len(self.params)}")
        for p in self.params:
            total_rows = sum(len(s.rows) for s in p.slices)
            lines.append(f"  {p.name} (default={p.default}, slices={len(p.slices)}, rows={total_rows})")
        return "\n".join(lines)


# ────────────────────────────────────────────────────────────
# Tokeniser helpers
# ────────────────────────────────────────────────────────────

_COMMENT_RE = re.compile(r"#.*")

def _strip_comments(text: str) -> str:
    return _COMMENT_RE.sub("", text)

def _tokenise(text: str) -> list[str]:
    """Split GMPL text into semicolon-terminated statements."""
    clean = _strip_comments(text)
    parts = clean.split(";")
    return [p.strip() for p in parts if p.strip()]

def _try_number(s: str) -> Union[int, float, str]:
    """Try to cast *s* to int or float; fall back to the original string."""
    try:
        v = float(s)
        return int(v) if v == int(v) else v
    except (ValueError, OverflowError):
        return s


# ────────────────────────────────────────────────────────────
# Parser
# ────────────────────────────────────────────────────────────

class GMPLParser:
    """
    Pure-syntax GMPL parser.

    Usage::

        result = GMPLParser.parse_file("utopia.txt")
        print(result.summary())
    """

    # ── public ──────────────────────────────────────────────
    @staticmethod
    def parse_file(path: str | Path) -> GMPLParseResult:
        """Parse a ``.txt`` / ``.dat`` GMPL file and return structured result."""
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        return GMPLParser.parse_string(text)

    @staticmethod
    def parse_string(text: str) -> GMPLParseResult:
        """Parse raw GMPL text and return structured result."""
        result = GMPLParseResult()
        stmts = _tokenise(text)
        for stmt in stmts:
            first = stmt.split()[0].lower() if stmt.split() else ""
            if first == "end":
                break
            if first == "set":
                GMPLParser._parse_set(stmt, result)
            elif first == "param":
                GMPLParser._parse_param(stmt, result)
        return result

    # ── set ─────────────────────────────────────────────────
    @staticmethod
    def _parse_set(stmt: str, result: GMPLParseResult) -> None:
        tokens = stmt.split()
        name = tokens[1]
        # find := position
        body = ""
        for i, t in enumerate(tokens):
            if ":=" in t:
                # Handle glued tokens like "YEAR:="
                after = t.split(":=", 1)[1]
                rest = tokens[i + 1 :]
                body = (after + " " + " ".join(rest)).strip()
                break
        members = [m for m in body.split() if m]
        result.sets[name] = members

    # ── param ──────────────────────────────────────────────
    @staticmethod
    def _parse_param(stmt: str, result: GMPLParseResult) -> None:
        tokens = stmt.split()
        name = tokens[1]

        # extract default
        default_val: Optional[Union[int, float]] = None
        for i, t in enumerate(tokens):
            if t.lower() == "default":
                dv = _try_number(tokens[i + 1])
                if isinstance(dv, (int, float)):
                    default_val = dv
                break

        # find := position
        assign_pos = None
        for i, t in enumerate(tokens):
            if ":=" in t:
                assign_pos = i
                break

        if assign_pos is None:
            # declaration only, no data
            result.params.append(ParsedParam(name=name, default=default_val))
            return

        # Rejoin everything after := (handle glued tokens)
        glued_after = tokens[assign_pos].split(":=", 1)[1]
        body_tokens = ([glued_after] if glued_after else []) + tokens[assign_pos + 1 :]
        body = " ".join(body_tokens).strip()

        if not body:
            result.params.append(ParsedParam(name=name, default=default_val))
            return

        # Split into slices by `[` headers
        slices = GMPLParser._split_slices(body)
        parsed = ParsedParam(name=name, default=default_val)
        for sl in slices:
            parsed.slices.append(GMPLParser._parse_slice_block(sl))
        result.params.append(parsed)

    @staticmethod
    def _split_slices(body: str) -> list[str]:
        """Split param body into per-slice strings."""
        # Find all '[' positions
        bracket_positions = [m.start() for m in re.finditer(r"\[", body)]
        if not bracket_positions:
            return [body]

        result = []
        # Anything before first bracket is a headerless slice
        prefix = body[: bracket_positions[0]].strip()
        if prefix:
            result.append(prefix)

        for i, pos in enumerate(bracket_positions):
            end = bracket_positions[i + 1] if i + 1 < len(bracket_positions) else len(body)
            result.append(body[pos:end].strip())

        return result

    @staticmethod
    def _parse_slice_block(text: str) -> SliceBlock:
        """Parse one slice block into a SliceBlock object."""
        block = SliceBlock()

        # Extract header if present
        if text.startswith("["):
            bracket_end = text.index("]")
            header_str = text[1:bracket_end]
            block.header = [h.strip() for h in header_str.split(",")]
            text = text[bracket_end + 1 :].strip()

        # Look for colon separator (column labels)
        if ":" in text:
            parts = text.split(":")
            # Column labels are between first and second ':'
            if len(parts) >= 3:
                # header : col1 col2 ... : \n row data
                col_part = parts[1].strip()
                block.column_labels = col_part.split()
                # Rejoin remaining for rows
                row_text = ":".join(parts[2:]).strip()
                # Handle `:=` at start of row_text
                if row_text.startswith("="):
                    row_text = row_text[1:].strip()
            elif len(parts) == 2:
                # Might be `key : val` pairs or `:=` continuation
                left = parts[0].strip()
                right = parts[1].strip()
                if right.startswith("="):
                    # it's `:=` continuation
                    row_text = right[1:].strip()
                    # If left has column labels
                    col_tokens = left.split()
                    if col_tokens:
                        block.column_labels = col_tokens
                else:
                    row_text = text
            else:
                row_text = text
        else:
            row_text = text

        # Parse rows
        if row_text:
            GMPLParser._parse_rows(row_text, block)

        return block

    @staticmethod
    def _parse_rows(text: str, block: SliceBlock) -> None:
        """Parse row data into RowEntry objects."""
        # Tokenize by whitespace
        tokens = text.split()
        if not tokens:
            return

        n_cols = len(block.column_labels) if block.column_labels else 0

        if n_cols > 0:
            # Table format: key val1 val2 ... valN
            i = 0
            while i < len(tokens):
                key = tokens[i]
                i += 1
                vals = []
                while len(vals) < n_cols and i < len(tokens):
                    v = _try_number(tokens[i])
                    if isinstance(v, (int, float)):
                        vals.append(v)
                        i += 1
                    else:
                        break
                if vals:
                    block.rows.append(RowEntry(key=key, values=vals))
        else:
            # Headerless: key value pairs or single values
            i = 0
            while i < len(tokens):
                key = tokens[i]
                i += 1
                vals = []
                while i < len(tokens):
                    v = _try_number(tokens[i])
                    if isinstance(v, (int, float)):
                        vals.append(v)
                        i += 1
                    else:
                        break
                if vals:
                    block.rows.append(RowEntry(key=key, values=vals))


# ────────────────────────────────────────────────────────────
# CLI entry point
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python GMPLParser.py <data_file.txt>")
        sys.exit(1)

    result = GMPLParser.parse_file(sys.argv[1])
    print(result.summary())
    print("\n" + "=" * 60 + "\n")

    for p in result.params[:10]:
        print(f"\nparam {p.name} (default={p.default}):")
        for si, s in enumerate(p.slices):
            print(f"  slice[{si}]: header={s.header}")
            print(f"    columns: {s.column_labels}")
            for r in s.rows[:3]:
                print(f"    {r}")
            if len(s.rows) > 3:
                print(f"    ... ({len(s.rows)} rows total)")
