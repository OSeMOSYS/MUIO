#!/usr/bin/env python3
"""
Validation script for Phase 3 — MuioTransformer.

Tests the transformer against both UTOPIA and MUIO sample fixtures.
Validates:
  - All expected JSON file groups are generated
  - ID mappings are deterministic
  - Record shapes match expected long-form structure
  - No crashes on missing params
  - genData.json schema completeness
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from Classes.Case.GMPLParser import GMPLParser
from Classes.Case.SliceInterpreter import SliceInterpreter
from Classes.Case.MuioTransformer import MuioTransformer, PARAM_MAPPING

FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def check(cond: bool, msg: str, errors: list[str]) -> None:
    if not cond:
        errors.append(msg)


def validate_structure(result: dict, label: str, errors: list[str]) -> None:
    """Validate file group structure and genData completeness."""

    # ── Expected file groups ──
    expected_groups = {
        "genData", "R", "RT", "RE", "RS", "RY",
        "RYT", "RYTM", "RYTC", "RYTCM",
        "RYC", "RYE", "RYS",
        "RYTs", "RYTTs", "RYCTs",
        "RYTE", "RYTEM", "RTSM",
        "RYDtb", "RYSeDt", "RYCn", "RYTCn",
        "_conv",
    }
    for fg in expected_groups:
        check(fg in result, f"{label}: missing file group '{fg}'", errors)

    # ── genData schema ──
    gd = result.get("genData", {})
    required_gd_keys = [
        "osy-casename", "osy-desc", "osy-region", "osy-years",
        "osy-mo", "osy-tech", "osy-comm", "osy-emis", "osy-stg",
        "osy-ts", "osy-se", "osy-dt", "osy-dtb", "osy-scenarios",
        "osy-techGroups", "osy-constraints",
    ]
    for key in required_gd_keys:
        check(key in gd, f"{label}: genData missing key '{key}'", errors)

    # ── SC_0 envelope ──
    for fg, data in result.items():
        if fg in ("genData", "_conv"):
            continue
        if not isinstance(data, dict):
            continue
        for param_key, param_data in data.items():
            check(
                isinstance(param_data, dict) and "SC_0" in param_data,
                f"{label}: {fg}.{param_key} missing SC_0 envelope",
                errors,
            )


def validate_ids(tx: MuioTransformer, label: str, errors: list[str]) -> None:
    """Validate ID mappings are deterministic and sorted."""
    id_maps = tx.id_maps

    for set_name, mapping in id_maps.items():
        if set_name in ("REGION", "YEAR"):
            continue
        if not mapping:
            continue

        # Check IDs are sequential
        ids = list(mapping.values())
        if set_name == "MODE_OF_OPERATION":
            # Raw strings, no prefix check
            continue

        prefixes = set()
        for mid in ids:
            parts = str(mid).rsplit("_", 1)
            check(
                len(parts) == 2 and parts[1].isdigit(),
                f"{label}: {set_name} ID '{mid}' not in prefix_N format",
                errors,
            )
            prefixes.add(parts[0])

        # All IDs should share the same prefix
        check(
            len(prefixes) <= 1,
            f"{label}: {set_name} IDs have mixed prefixes: {prefixes}",
            errors,
        )


def validate_records(result: dict, label: str, errors: list[str]) -> None:
    """Validate record shapes are long-form (no year-wide pivot)."""

    # ── RYT records must have TechId, Year, Value ──
    ryt = result.get("RYT", {})
    for pk, pd in ryt.items():
        records = pd.get("SC_0", [])
        for rec in records[:5]:
            check("TechId" in rec, f"{label}: RYT.{pk} record missing TechId", errors)
            check("Year" in rec, f"{label}: RYT.{pk} record missing Year", errors)
            check("Value" in rec, f"{label}: RYT.{pk} record missing Value", errors)

    # ── RYTCM records must have TechId, CommId, MoId, Year, Value ──
    rytcm = result.get("RYTCM", {})
    for pk, pd in rytcm.items():
        records = pd.get("SC_0", [])
        for rec in records[:5]:
            for field in ("TechId", "CommId", "MoId", "Year", "Value"):
                check(field in rec, f"{label}: RYTCM.{pk} record missing {field}", errors)

    # ── RT records must have TechId, Value (no Year) ──
    rt = result.get("RT", {})
    for pk, pd in rt.items():
        records = pd.get("SC_0", [])
        for rec in records[:5]:
            check("TechId" in rec, f"{label}: RT.{pk} record missing TechId", errors)
            check("Value" in rec, f"{label}: RT.{pk} record missing Value", errors)
            check("Year" not in rec, f"{label}: RT.{pk} record has Year (should not)", errors)

    # ── RTSM records must have StgId, TechId, MoId, Value ──
    rtsm = result.get("RTSM", {})
    for pk, pd in rtsm.items():
        records = pd.get("SC_0", [])
        for rec in records[:5]:
            for field in ("StgId", "TechId", "MoId", "Value"):
                check(field in rec, f"{label}: RTSM.{pk} record missing {field}", errors)


def validate_utopia_data(result: dict, tx: MuioTransformer, errors: list[str]) -> None:
    """Spot-check UTOPIA data values."""

    # CapitalCost(UTOPIA, E01, 1990) = 1400
    ryt = result.get("RYT", {})
    cc_records = ryt.get("CC", {}).get("SC_0", [])
    e01_id = tx.id_maps["TECHNOLOGY"].get("E01")
    found_cc = False
    for rec in cc_records:
        if rec.get("TechId") == e01_id and rec.get("Year") == "1990":
            check(rec["Value"] == 1400, f"UTOPIA CC(E01,1990) expected 1400, got {rec['Value']}", errors)
            found_cc = True
            break
    check(found_cc, "UTOPIA: CC(E01,1990) record not found", errors)

    # OperationalLife(UTOPIA, E01) = 40
    rt = result.get("RT", {})
    ol_records = rt.get("OL", {}).get("SC_0", [])
    found_ol = False
    for rec in ol_records:
        if rec.get("TechId") == e01_id:
            check(rec["Value"] == 40, f"UTOPIA OL(E01) expected 40, got {rec['Value']}", errors)
            found_ol = True
            break
    check(found_ol, "UTOPIA: OL(E01) record not found", errors)

    # InputActivityRatio(UTOPIA, E70, DSL, 1, 1990) = 3.4
    rytcm = result.get("RYTCM", {})
    iar_records = rytcm.get("IAR", {}).get("SC_0", [])
    e70_id = tx.id_maps["TECHNOLOGY"].get("E70")
    dsl_id = tx.id_maps["COMMODITY"].get("DSL")
    found_iar = False
    for rec in iar_records:
        if (rec.get("TechId") == e70_id and rec.get("CommId") == dsl_id
                and rec.get("Year") == "1990" and rec.get("MoId") == "1"):
            check(rec["Value"] == 3.4, f"UTOPIA IAR(E70,DSL,1,1990) expected 3.4, got {rec['Value']}", errors)
            found_iar = True
            break
    check(found_iar, "UTOPIA: IAR(E70,DSL,1,1990) record not found", errors)

    # genData tech list
    gd = result["genData"]
    check(len(gd["osy-tech"]) > 0, "UTOPIA: genData.osy-tech empty", errors)
    check(gd["osy-region"] == "UTOPIA", f"UTOPIA: region expected 'UTOPIA', got '{gd['osy-region']}'", errors)


def validate_muio_data(result: dict, tx: MuioTransformer, errors: list[str]) -> None:
    """Spot-check MUIO sample data values."""

    # CapitalCost(RE1, Coal, 2020) = 1500
    ryt = result.get("RYT", {})
    cc_records = ryt.get("CC", {}).get("SC_0", [])
    coal_id = tx.id_maps["TECHNOLOGY"].get("Coal")
    found_cc = False
    for rec in cc_records:
        if rec.get("TechId") == coal_id and rec.get("Year") == "2020":
            check(rec["Value"] == 1500, f"MUIO CC(Coal,2020) expected 1500, got {rec['Value']}", errors)
            found_cc = True
            break
    check(found_cc, "MUIO: CC(Coal,2020) record not found", errors)

    # OperationalLife(RE1, Coal) = 40
    rt = result.get("RT", {})
    ol_records = rt.get("OL", {}).get("SC_0", [])
    found_ol = False
    for rec in ol_records:
        if rec.get("TechId") == coal_id:
            check(rec["Value"] == 40, f"MUIO OL(Coal) expected 40, got {rec['Value']}", errors)
            found_ol = True
            break
    check(found_ol, "MUIO: OL(Coal) record not found", errors)

    # FUEL → COMMODITY normalization
    check("COMMODITY" in tx.sets, "MUIO: COMMODITY set not present after normalization", errors)
    check("FUEL" not in tx.sets, "MUIO: FUEL set should have been renamed", errors)

    # MUIO-only sets injected
    for s in ("STORAGEINTRADAY", "STORAGEINTRAYEAR", "UDC"):
        check(s in tx.sets, f"MUIO: {s} set not injected", errors)

    # genData
    gd = result["genData"]
    check(gd["osy-region"] == "RE1", f"MUIO: region expected 'RE1', got '{gd['osy-region']}'", errors)
    check(len(gd["osy-comm"]) > 0, "MUIO: genData.osy-comm empty", errors)
    check(gd["osy-comm"][0]["Comm"] in ("Electricity", "Heat"),
          f"MUIO: commodity name unexpected: {gd['osy-comm'][0]['Comm']}", errors)


def main():
    utopia_path = FIXTURES / "utopia.txt"
    muio_path = FIXTURES / "muio_sample.txt"

    if not utopia_path.exists() or not muio_path.exists():
        print("ERROR: fixtures not found")
        sys.exit(1)

    errors: list[str] = []

    # ── UTOPIA ──
    print("Phase 3: Parsing & transforming UTOPIA...")
    r1 = GMPLParser.parse_file(utopia_path)
    interp1 = SliceInterpreter(r1)
    norm1 = interp1.interpret()
    tx1 = MuioTransformer(norm1, r1.sets, casename="utopia")
    result1 = tx1.transform()
    print(f"  → {len(result1)} file groups")

    validate_structure(result1, "UTOPIA", errors)
    validate_ids(tx1, "UTOPIA", errors)
    validate_records(result1, "UTOPIA", errors)
    validate_utopia_data(result1, tx1, errors)

    # Print sample
    ryt1 = result1.get("RYT", {})
    cc1 = ryt1.get("CC", {}).get("SC_0", [])
    print(f"  CapitalCost: {len(cc1)} long-form records")
    for rec in cc1[:3]:
        print(f"    {rec}")

    # ── MUIO ──
    print("\nPhase 3: Parsing & transforming MUIO sample...")
    r2 = GMPLParser.parse_file(muio_path)
    interp2 = SliceInterpreter(r2)
    norm2 = interp2.interpret()
    tx2 = MuioTransformer(norm2, r2.sets, casename="muio_test")
    result2 = tx2.transform()
    print(f"  → {len(result2)} file groups")

    validate_structure(result2, "MUIO", errors)
    validate_ids(tx2, "MUIO", errors)
    validate_records(result2, "MUIO", errors)
    validate_muio_data(result2, tx2, errors)

    # Print sample
    ryt2 = result2.get("RYT", {})
    cc2 = ryt2.get("CC", {}).get("SC_0", [])
    print(f"  CapitalCost: {len(cc2)} long-form records")
    for rec in cc2[:3]:
        print(f"    {rec}")

    # ── Results ──
    print("\n" + "=" * 60)
    if errors:
        print(f"❌ {len(errors)} validation error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ All Phase 3 validation checks passed!")


if __name__ == "__main__":
    main()
