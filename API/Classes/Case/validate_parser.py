#!/usr/bin/env python3
"""
Validation script for GMPLParser Phase 1.

Parses both UTOPIA and MUIO sample fixtures, then dumps the
parsed structures in a human-readable format for review.
"""

import sys
import os
from pathlib import Path

# Add the API directory to path so we can import GMPLParser
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from Classes.Case.GMPLParser import GMPLParser


FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def dump_result(label: str, result) -> str:
    """Produce a detailed human-readable dump."""
    lines = []
    lines.append(f"{'='*70}")
    lines.append(f"  {label}")
    lines.append(f"{'='*70}")
    lines.append("")

    # Sets
    lines.append(f"SETS ({len(result.sets)}):")
    for name, members in result.sets.items():
        if len(members) <= 10:
            lines.append(f"  {name}: {members}")
        else:
            lines.append(f"  {name}: [{', '.join(members[:5])}, ... ({len(members)} total)]")
    lines.append("")

    # Params summary
    lines.append(f"PARAMS ({len(result.params)}):")
    lines.append(f"  {'Name':<50} {'Default':<12} {'Slices':<8} {'Rows':<8}")
    lines.append(f"  {'-'*50} {'-'*12} {'-'*8} {'-'*8}")
    for p in result.params:
        n_rows = sum(len(s.rows) for s in p.slices)
        lines.append(f"  {p.name:<50} {str(p.default):<12} {len(p.slices):<8} {n_rows:<8}")
    lines.append("")

    # Detailed: show first 3 params with data, plus specific interesting ones
    interesting = {
        "InputActivityRatio", "OutputActivityRatio", "CapacityFactor",
        "YearSplit", "CapacityToActivityUnit", "OperationalLife",
        "ReserveMargin", "TechnologyToStorage", "TechnologyFromStorage",
        "Conversionls", "EmissionActivityRatio", "VariableCost",
    }

    lines.append("DETAILED PARAM STRUCTURES (selected):")
    for p in result.params:
        if p.name not in interesting:
            continue
        lines.append(f"\n  param {p.name} (default={p.default}):")
        if not p.slices:
            lines.append("    <empty body>")
            continue
        for si, s in enumerate(p.slices):
            hdr = ",".join(s.header) if s.header else "<headerless>"
            lines.append(f"    slice[{si}]: [{hdr}]")
            cols_str = ", ".join(s.column_labels[:8])
            if len(s.column_labels) > 8:
                cols_str += f", ... ({len(s.column_labels)} cols)"
            lines.append(f"      columns: [{cols_str}]")
            for ri, r in enumerate(s.rows):
                vals = ", ".join(str(v) for v in r.values[:5])
                if len(r.values) > 5:
                    vals += ", ..."
                lines.append(f"      row[{ri}]: key={r.key!r:<15} values=[{vals}]")

    lines.append("")
    return "\n".join(lines)


def main():
    utopia_path = FIXTURES / "utopia.txt"
    muio_path = FIXTURES / "muio_sample.txt"

    if not utopia_path.exists():
        print(f"ERROR: {utopia_path} not found")
        sys.exit(1)
    if not muio_path.exists():
        print(f"ERROR: {muio_path} not found")
        sys.exit(1)

    print("Parsing UTOPIA...")
    utopia_result = GMPLParser.parse_file(utopia_path)

    print("Parsing MUIO sample...")
    muio_result = GMPLParser.parse_file(muio_path)

    print()
    print(dump_result("UTOPIA (Standard OSeMOSYS GMPL)", utopia_result))
    print()
    print(dump_result("MUIO SAMPLE (MUIO-style GMPL)", muio_result))

    # Quick assertions
    errors = []
    # UTOPIA checks
    if len(utopia_result.sets) != 11:
        errors.append(f"UTOPIA: expected 11 sets, got {len(utopia_result.sets)}")
    if "FUEL" not in utopia_result.sets:
        errors.append("UTOPIA: missing FUEL set")
    if len(utopia_result.sets.get("TECHNOLOGY", [])) != 21:
        errors.append(f"UTOPIA: expected 21 technologies, got {len(utopia_result.sets.get('TECHNOLOGY', []))}")
    if len(utopia_result.params) != 54:
        errors.append(f"UTOPIA: expected 54 params, got {len(utopia_result.params)}")

    # Check YearSplit has data
    ys = next((p for p in utopia_result.params if p.name == "YearSplit"), None)
    if ys and sum(len(s.rows) for s in ys.slices) != 6:
        errors.append(f"UTOPIA: YearSplit expected 6 rows, got {sum(len(s.rows) for s in ys.slices)}")

    # Check InputActivityRatio has 8 slices
    iar = next((p for p in utopia_result.params if p.name == "InputActivityRatio"), None)
    if iar and len(iar.slices) != 8:
        errors.append(f"UTOPIA: InputActivityRatio expected 8 slices, got {len(iar.slices)}")

    # MUIO checks
    if len(muio_result.sets) != 14:
        errors.append(f"MUIO: expected 14 sets, got {len(muio_result.sets)}")
    if "COMMODITY" not in muio_result.sets:
        errors.append("MUIO: missing COMMODITY set")
    if len(muio_result.sets.get("STORAGEINTRADAY", ["x"])) != 0:
        errors.append("MUIO: STORAGEINTRADAY should be empty")

    # Check InputActivityRatio has 2 slices
    iar_m = next((p for p in muio_result.params if p.name == "InputActivityRatio"), None)
    if iar_m and len(iar_m.slices) != 2:
        errors.append(f"MUIO: InputActivityRatio expected 2 slices, got {len(iar_m.slices)}")

    if errors:
        print("\n❌ VALIDATION ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\n✅ All validation checks passed!")


if __name__ == "__main__":
    main()
