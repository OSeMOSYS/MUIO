"""Phase 2 — Validate SliceInterpreter against UTOPIA and MUIO fixtures."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Classes.Case.GMPLParser import GMPLParser
from Classes.Case.SliceInterpreter import SliceInterpreter

_FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def _run() -> None:
    interp = SliceInterpreter()

    # ── UTOPIA ──
    print("Phase 2: Interpreting UTOPIA...")
    u = GMPLParser.parse_file(_FIXTURES / "utopia.txt")
    n = interp.interpret(u)
    print(f"  → {len(n)} parameters with data")

    # CapitalCost
    assert "CapitalCost" in n, "CapitalCost missing"
    cc = n["CapitalCost"]
    assert len(cc) == 231, f"Expected 231 CC tuples, got {len(cc)}"
    assert ("UTOPIA", "E01", "1990") in cc
    assert cc[("UTOPIA", "E01", "1990")] == 1400
    print(f"  → CapitalCost: {len(cc)} tuples, ('UTOPIA','E01','1990')={cc[('UTOPIA','E01','1990')]}")

    # InputActivityRatio (5D)
    assert "InputActivityRatio" in n, "IAR missing"
    iar = n["InputActivityRatio"]
    assert len(iar) > 0
    sample_key = next(iter(iar))
    assert len(sample_key) == 5, f"IAR tuple should be 5D, got {len(sample_key)}D"
    print(f"  → IAR: {len(iar)} tuples, sample {sample_key}={iar[sample_key]}")

    # Conversionls — now 3D with region
    assert "Conversionls" in n
    cls = n["Conversionls"]
    sample = next(iter(cls))
    assert len(sample) == 3, f"CLS tuple should be 3D, got {len(sample)}D"
    assert sample[0] == "UTOPIA", f"CLS region should be UTOPIA, got {sample[0]}"
    print(f"  → Conversionls: {len(cls)} tuples, sample {sample}")

    # TTS/TFS
    assert "TechnologyToStorage" in n
    tts = n["TechnologyToStorage"]
    sample_tts = next(iter(tts))
    assert len(sample_tts) == 4, f"TTS should be 4D, got {len(sample_tts)}D"
    print(f"  → TTS: {tts}")

    # ── MUIO sample ──
    print("\nPhase 2: Interpreting MUIO sample...")
    m = GMPLParser.parse_file(_FIXTURES / "muio_sample.txt")
    nm = interp.interpret(m)
    print(f"  → {len(nm)} parameters with data")

    # CapitalCost
    assert "CapitalCost" in nm
    mcc = nm["CapitalCost"]
    assert ("RE1", "Coal", "2020") in mcc
    assert mcc[("RE1", "Coal", "2020")] == 1500
    print(f"  → CC: {len(mcc)} tuples, ('RE1','Coal','2020')={mcc[('RE1','Coal','2020')]}")

    # CapacityFactor (4D)
    assert "CapacityFactor" in nm
    cf = nm["CapacityFactor"]
    sample_cf = next(iter(cf))
    assert len(sample_cf) == 4, f"CF should be 4D, got {len(sample_cf)}D"
    print(f"  → CF: {len(cf)} tuples")

    # MUIO TTS
    assert "TechnologyToStorage" in nm
    mtts = nm["TechnologyToStorage"]
    print(f"  → TTS: {mtts}")

    print()
    print("=" * 60)
    print("✅ All Phase 2 validation checks passed!")


if __name__ == "__main__":
    _run()
