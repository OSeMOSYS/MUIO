from pathlib import Path
from zipfile import ZipFile

class Security:
    @staticmethod
    def safeCasePath(baseDir, casename):
        """Resolve casename under baseDir and ensure it stays within baseDir"""
        base = Path(baseDir).resolve()
        target = (base / casename).resolve()

        if not str(target).startswith(str(base) + "\\") and target != base:
            if not str(target).startswith(str(base) + "/") and target != base:
                raise ValueError(
                    "Path traversal detected: '" + casename + "' escapes base directory"
                )

        return target

    @staticmethod
    def safeExtractall(zf, targetDir):
        """Extract ZIP only after verifying no entry escapes targetDir"""
        target = Path(targetDir).resolve()

        for member in zf.infolist():
            memberPath = (target / member.filename).resolve()

            if not str(memberPath).startswith(str(target) + "\\") and \
               not str(memberPath).startswith(str(target) + "/") and \
               memberPath != target:
                raise ValueError(
                    "ZIP slip detected: '" + member.filename + "' would escape target directory"
                )

        #all entries validated, safe to extract
        zf.extractall(str(targetDir))
