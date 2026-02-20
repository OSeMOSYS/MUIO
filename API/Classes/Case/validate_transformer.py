"""Phase 3 — Validate MuioTransformer against UTOPIA and MUIO fixtures."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Classes.Case.GMPLParser import GMPLParser
from Classes.Case.SliceInterpreter import SliceInterpreter
from Classes.Case.MuioTransformer import MuioTransformer

_FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def _validate_fixture(label: str, path: Path) -> dict:
    print(f"\nPhase 3: Parsing & transforming {label}...")
    parsed = GMPLParser.parse_file(path)
    normalized = SliceInterpreter().interpret(parsed)
    result = MuioTransformer.transform(parsed, normalized)

    # Count file groups
    file_groups = [k for k in result if k != "genData"]
    print(f"  → {len(file_groups)} file groups")

    # genData checks
    gen = result["genData"]
    assert "osy-scenarios" in gen
    assert gen["osy-scenarios"][0]["ScenarioId"] == "SC_0"
    assert len(gen["osy-years"]) > 0
    assert len(gen["osy-tech"]) > 0
    assert "TechId" in gen["osy-tech"][0]
    assert gen["osy-tech"][0]["TechId"].startswith("T_")
    print(f"  → genData: {len(gen['osy-tech'])} techs, {len(gen['osy-years'])} years")

    # SC_0 envelope on all data
    for fg_name in file_groups:
        for key, val in result[fg_name].items():
            assert "SC_0" in val, f"{fg_name}.{key} missing SC_0 envelope"

    # Check CapitalCost exists in RYT
    if "RYT" in result and "CC" in result["RYT"]:
        cc = result["RYT"]["CC"]["SC_0"]
        assert len(cc) > 0
        rec = cc[0]
        assert "TechId" in rec
        assert "Year" in rec
        assert "Value" in rec
        print(f"  CapitalCost: {len(cc)} long-form records")
        for r in cc[:3]:
            print(f"    {r}")

    return result


def _run() -> None:
    # ── UTOPIA ──
    r1 = _validate_fixture("UTOPIA", _FIXTURES / "utopia.txt")

    # Specific UTOPIA checks
    assert len(r1["RYT"]["CC"]["SC_0"]) == 231
    assert r1["RYT"]["CC"]["SC_0"][0]["TechId"].startswith("T_")

    # RTSM
    if "RTSM" in r1 and r1["RTSM"]:
        tts = r1["RTSM"]["TTS"]["SC_0"]
        assert len(tts) == 1
        assert "StgId" in tts[0]
        assert tts[0]["StgId"].startswith("S_")
        assert tts[0]["TechId"].startswith("T_")
        print(f"  RTSM.TTS: {tts[0]}")

    # Determinism
    p1 = GMPLParser.parse_file(_FIXTURES / "utopia.txt")
    n1 = SliceInterpreter().interpret(p1)
    r1b = MuioTransformer.transform(p1, n1)
    import json
    j1 = json.dumps(r1, sort_keys=True, default=str)
    j2 = json.dumps(r1b, sort_keys=True, default=str)
    assert j1 == j2, "Output not deterministic!"
    print("  ✓ Deterministic output confirmed")

    # ── MUIO sample ──
    r2 = _validate_fixture("MUIO sample", _FIXTURES / "muio_sample.txt")

    # MUIO-specific: COMMODITY set (not FUEL)
    gen2 = r2["genData"]
    assert len(gen2["osy-comm"]) > 0
    assert gen2["osy-comm"][0]["CommId"].startswith("C_")

    # MUIO CC check
    if "RYT" in r2 and "CC" in r2["RYT"]:
        mcc = r2["RYT"]["CC"]["SC_0"]
        # Find a Coal/T_x record for year 2020
        coal_2020 = [r for r in mcc if r["Year"] == "2020" and r["Value"] == 1500]
        assert len(coal_2020) > 0, "Missing Coal CC=1500 for 2020"

    print()
    print("=" * 60)
    print("✅ All Phase 3 validation checks passed!")


if __name__ == "__main__":
    _run()
