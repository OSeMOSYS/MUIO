"""Phase 1 — Validate GMPLParser against UTOPIA and MUIO sample fixtures."""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from Classes.Case.GMPLParser import GMPLParser

_FIXTURES = Path(__file__).resolve().parent / "test_fixtures"


def _run() -> None:
    # ── UTOPIA ──
    print("Phase 1: Parsing UTOPIA...")
    u = GMPLParser.parse_file(_FIXTURES / "utopia.txt")
    assert len(u.sets) >= 10, f"Expected ≥10 sets, got {len(u.sets)}"
    assert "TECHNOLOGY" in u.sets
    assert "YEAR" in u.sets
    assert len(u.sets["TECHNOLOGY"]) == 21, f"Expected 21 techs, got {len(u.sets['TECHNOLOGY'])}"
    assert len(u.sets["YEAR"]) == 21
    assert len(u.params) >= 40, f"Expected ≥40 params, got {len(u.params)}"

    # Check a specific param
    cc = next((p for p in u.params if p.name == "CapitalCost"), None)
    assert cc is not None, "CapitalCost not found"
    assert cc.default == 0
    assert len(cc.slices) > 0
    total_rows = sum(len(s.rows) for s in cc.slices)
    assert total_rows > 0, "CapitalCost has no rows"
    print(f"  → {len(u.sets)} sets, {len(u.params)} params")
    print(f"  → CapitalCost: {len(cc.slices)} slices, {total_rows} rows")

    # Check set membership
    assert "E01" in u.sets["TECHNOLOGY"]
    assert "1990" in u.sets["YEAR"]

    # ── MUIO sample ──
    print("\nPhase 1: Parsing MUIO sample...")
    m = GMPLParser.parse_file(_FIXTURES / "muio_sample.txt")
    assert len(m.sets) >= 9, f"Expected ≥9 sets, got {len(m.sets)}"
    assert "COMMODITY" in m.sets, "Expected COMMODITY (not FUEL)"
    assert "Coal" in m.sets["TECHNOLOGY"]
    assert len(m.sets["YEAR"]) == 3

    mcc = next((p for p in m.params if p.name == "CapitalCost"), None)
    assert mcc is not None
    print(f"  → {len(m.sets)} sets, {len(m.params)} params")

    # Check storage params parsed
    tts = next((p for p in m.params if p.name == "TechnologyToStorage"), None)
    assert tts is not None, "TechnologyToStorage not found"
    assert len(tts.slices) > 0
    print(f"  → TechnologyToStorage: {len(tts.slices)} slices")

    # Check conversion matrix
    cls = next((p for p in m.params if p.name == "Conversionls"), None)
    assert cls is not None, "Conversionls not found"
    assert len(cls.slices) > 0
    print(f"  → Conversionls: {len(cls.slices)} slices")

    print()
    print("=" * 60)
    print("✅ All Phase 1 validation checks passed!")


if __name__ == "__main__":
    _run()
