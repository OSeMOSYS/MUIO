#!/usr/bin/env python3
"""
Validation script for SliceInterpreter Phase 2.

Parses both UTOPIA and MUIO sample fixtures, then
validates the interpreted tuple data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from Classes.Case.GMPLParser import GMPLParser
from Classes.Case.SliceInterpreter import SliceInterpreter


FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def check(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def validate_utopia(norm: dict, errors: list[str]) -> None:
    """Validate UTOPIA interpreted results."""

    # ── CapitalCost ──
    cc = norm.get("CapitalCost", {})
    check(len(cc) > 0, "CapitalCost: no tuples", errors)
    # Expect 21 techs × 21 years but only non-default values
    check(("UTOPIA", "E01", "1990") in cc, "CapitalCost: missing (UTOPIA,E01,1990)", errors)
    check(cc.get(("UTOPIA", "E01", "1990")) == 1400, f"CapitalCost (UTOPIA,E01,1990) expected 1400, got {cc.get(('UTOPIA','E01','1990'))}", errors)
    check(("UTOPIA", "E21", "2000") in cc, "CapitalCost: missing (UTOPIA,E21,2000)", errors)

    # Verify dimension ordering: (REGION, TECHNOLOGY, YEAR)
    for tup in list(cc.keys())[:5]:
        check(len(tup) == 3, f"CapitalCost: expected 3-tuple, got {len(tup)}: {tup}", errors)
        check(tup[0] == "UTOPIA", f"CapitalCost: dim[0] should be REGION, got {tup[0]}", errors)

    # ── InputActivityRatio ──
    iar = norm.get("InputActivityRatio", {})
    check(len(iar) > 0, "InputActivityRatio: no tuples", errors)
    check(("UTOPIA", "E70", "DSL", "1", "1990") in iar, "InputActivityRatio: missing (UTOPIA,E70,DSL,1,1990)", errors)
    check(iar.get(("UTOPIA", "E70", "DSL", "1", "1990")) == 3.4,
          f"InputActivityRatio (UTOPIA,E70,DSL,1,1990) expected 3.4, got {iar.get(('UTOPIA','E70','DSL','1','1990'))}", errors)

    # Verify 5-tuple: (REGION, TECHNOLOGY, FUEL, MODE, YEAR)
    for tup in list(iar.keys())[:5]:
        check(len(tup) == 5, f"InputActivityRatio: expected 5-tuple, got {len(tup)}: {tup}", errors)

    # ── CapacityFactor ──
    cf = norm.get("CapacityFactor", {})
    check(len(cf) > 0, "CapacityFactor: no tuples", errors)
    check(("UTOPIA", "E01", "ID", "1990") in cf, "CapacityFactor: missing (UTOPIA,E01,ID,1990)", errors)
    check(cf.get(("UTOPIA", "E01", "ID", "1990")) == 0.8,
          f"CapacityFactor (UTOPIA,E01,ID,1990) expected 0.8, got {cf.get(('UTOPIA','E01','ID','1990'))}", errors)

    # 4-tuple: (REGION, TECHNOLOGY, TIMESLICE, YEAR)
    for tup in list(cf.keys())[:5]:
        check(len(tup) == 4, f"CapacityFactor: expected 4-tuple, got {len(tup)}: {tup}", errors)

    # ── Conversion matrices ──
    cls = norm.get("Conversionls", {})
    check(len(cls) == 6, f"Conversionls: expected 6 tuples, got {len(cls)}", errors)
    check(("ID", "2") in cls, "Conversionls: missing (ID,2)", errors)
    check(cls.get(("ID", "2")) == 1, f"Conversionls (ID,2) expected 1, got {cls.get(('ID','2'))}", errors)

    # ── Storage params ──
    tts = norm.get("TechnologyToStorage", {})
    check(len(tts) == 1, f"TechnologyToStorage: expected 1, got {len(tts)}", errors)
    check(("UTOPIA", "E51", "DAM", "2") in tts, "TechnologyToStorage: missing (UTOPIA,E51,DAM,2)", errors)

    tfs = norm.get("TechnologyFromStorage", {})
    check(len(tfs) == 1, f"TechnologyFromStorage: expected 1, got {len(tfs)}", errors)
    check(("UTOPIA", "E51", "DAM", "1") in tfs, "TechnologyFromStorage: missing (UTOPIA,E51,DAM,1)", errors)

    # ── OperationalLife ──
    ol = norm.get("OperationalLife", {})
    check(len(ol) > 0, "OperationalLife: no tuples", errors)
    check(("UTOPIA", "E01") in ol, "OperationalLife: missing (UTOPIA,E01)", errors)
    check(ol.get(("UTOPIA", "E01")) == 40, f"OperationalLife (UTOPIA,E01) expected 40, got {ol.get(('UTOPIA','E01'))}", errors)

    # ── YearSplit (headerless 2D) ──
    ys = norm.get("YearSplit", {})
    check(len(ys) > 0, "YearSplit: no tuples", errors)
    check(("ID", "1990") in ys, "YearSplit: missing (ID,1990)", errors)
    check(ys.get(("ID", "1990")) == 0.1667, f"YearSplit (ID,1990) expected 0.1667, got {ys.get(('ID','1990'))}", errors)

    # ── No duplicate keys ──
    for pname, data in norm.items():
        # Dict keys are inherently unique, so just check no None in tuples
        for tup in data.keys():
            check(None not in tup, f"{pname}: tuple contains None: {tup}", errors)


def validate_muio(norm: dict, errors: list[str]) -> None:
    """Validate MUIO sample interpreted results."""

    # ── CapitalCost ──
    cc = norm.get("CapitalCost", {})
    check(len(cc) == 9, f"MUIO CapitalCost: expected 9 tuples, got {len(cc)}", errors)
    check(("RE1", "Coal", "2020") in cc, "MUIO CapitalCost: missing (RE1,Coal,2020)", errors)
    check(cc.get(("RE1", "Coal", "2020")) == 1500, f"MUIO CapitalCost (RE1,Coal,2020) expected 1500, got {cc.get(('RE1','Coal','2020'))}", errors)

    # Uses COMMODITY in set definitions but dimension registry says FUEL
    # The interpreter should handle this via _SET_ALIASES
    iar = norm.get("InputActivityRatio", {})
    check(len(iar) == 6, f"MUIO InputActivityRatio: expected 6 tuples, got {len(iar)}", errors)
    check(("RE1", "Coal", "Heat", "1", "2020") in iar, "MUIO InputActivityRatio: missing (RE1,Coal,Heat,1,2020)", errors)

    # ── OutputActivityRatio with mode 2 ──
    oar = norm.get("OutputActivityRatio", {})
    check(("RE1", "Gas", "Electricity", "2", "2020") in oar,
          "MUIO OutputActivityRatio: missing mode=2 entry (RE1,Gas,Electricity,2,2020)", errors)
    check(oar.get(("RE1", "Gas", "Electricity", "2", "2020")) == 0.5,
          f"MUIO OutputActivityRatio mode=2 expected 0.5", errors)

    # ── OperationalLife via oversized header ──
    ol = norm.get("OperationalLife", {})
    check(len(ol) > 0, "MUIO OperationalLife: no tuples", errors)
    check(("RE1", "Coal") in ol, "MUIO OperationalLife: missing (RE1,Coal)", errors)
    check(ol.get(("RE1", "Coal")) == 40, f"MUIO OperationalLife (RE1,Coal) expected 40", errors)

    # ── Storage ──
    tts = norm.get("TechnologyToStorage", {})
    check(("RE1", "Wind", "Battery", "2") in tts, "MUIO TechnologyToStorage: missing (RE1,Wind,Battery,2)", errors)

    # ── No None in tuples ──
    for pname, data in norm.items():
        for tup in data.keys():
            check(None not in tup, f"MUIO {pname}: tuple contains None: {tup}", errors)


def print_sample(norm: dict, params: list[str]) -> None:
    """Print sample output for requested params."""
    for pname in params:
        data = norm.get(pname, {})
        print(f"\n  {pname} ({len(data)} tuples):")
        if not data:
            print("    <empty>")
            continue
        items = sorted(data.items())
        for tup, val in items[:6]:
            print(f"    {tup} → {val}")
        if len(items) > 6:
            print(f"    ... ({len(items)} total)")


def main():
    utopia_path = FIXTURES / "utopia.txt"
    muio_path = FIXTURES / "muio_sample.txt"

    if not utopia_path.exists() or not muio_path.exists():
        print("ERROR: fixtures not found")
        sys.exit(1)

    errors: list[str] = []

    # ── UTOPIA ──
    print("Parsing & interpreting UTOPIA...")
    r1 = GMPLParser.parse_file(utopia_path)
    interp1 = SliceInterpreter(r1)
    norm1 = interp1.interpret()
    print(f"  → {len(norm1)} params with data")
    validate_utopia(norm1, errors)

    print("\n  Sample UTOPIA output:")
    print_sample(norm1, ["CapitalCost", "InputActivityRatio", "CapacityFactor"])

    # ── MUIO ──
    print("\n\nParsing & interpreting MUIO sample...")
    r2 = GMPLParser.parse_file(muio_path)
    interp2 = SliceInterpreter(r2)
    norm2 = interp2.interpret()
    print(f"  → {len(norm2)} params with data")
    validate_muio(norm2, errors)

    print("\n  Sample MUIO output:")
    print_sample(norm2, ["CapitalCost", "InputActivityRatio", "CapacityFactor"])

    # ── Results ──
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ All Phase 2 validation checks passed!")


if __name__ == "__main__":
    main()
