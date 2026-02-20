"""
Phase 3 — MUIO Transformer.

Converts normalised GMPL tuples into the exact JSON structures
consumed by MUIO's ``CaseClass`` and UI grids.

Public API
----------
    MuioTransformer.transform(parsed, normalized) → dict[str, dict]
"""

from __future__ import annotations

import json
from typing import Optional, Union

from Classes.Case.GMPLParser import GMPLParseResult
from Classes.Case.SliceInterpreter import SliceInterpreter

# ────────────────────────────────────────────────────────────
# Constants
# ────────────────────────────────────────────────────────────

_SET_ALIASES: dict[str, str] = {
    "FUEL": "COMMODITY",
}

_MUIO_ONLY_SETS: list[str] = [
    "STORAGEINTRADAY",
    "STORAGEINTRAYEAR",
    "UDC",
]

_ID_PREFIXES: dict[str, str] = {
    "TECHNOLOGY":           "T",
    "COMMODITY":            "C",
    "FUEL":                 "C",      # FUEL → COMMODITY alias
    "EMISSION":             "E",
    "STORAGE":              "S",
    "TIMESLICE":            "Ts",
    "SEASON":               "SE",
    "DAYTYPE":              "DT",
    "DAILYTIMEBRACKET":     "DTB",
}

# ────────────────────────────────────────────────────────────
# Parameter mapping registry  (param_name → file group + key + dims)
# ────────────────────────────────────────────────────────────

PARAM_MAPPING: dict[str, dict] = {
    # ── R ──
    "DiscountRate":                             {"file": "R",     "key": "DR",     "dims": ["region"]},
    "DepreciationMethod":                       {"file": "R",     "key": "DM",     "dims": ["region"]},
    # ── RY ──
    "AccumulatedAnnualDemand":                  {"file": "RY",    "key": "AAD",    "dims": ["region", "commodity", "year"]},
    "SpecifiedAnnualDemand":                    {"file": "RY",    "key": "SAD",    "dims": ["region", "commodity", "year"]},
    "REMinProductionTarget":                    {"file": "RY",    "key": "REPT",   "dims": ["region", "year"]},
    # ── RT ──
    "OperationalLife":                          {"file": "RT",    "key": "OL",     "dims": ["region", "technology"]},
    "CapacityToActivityUnit":                   {"file": "RT",    "key": "CAU",    "dims": ["region", "technology"]},
    "TotalTechnologyModelPeriodActivityUpperLimit": {"file": "RT", "key": "TTMPAU", "dims": ["region", "technology"]},
    "TotalTechnologyModelPeriodActivityLowerLimit": {"file": "RT", "key": "TTMPAL", "dims": ["region", "technology"]},
    "DiscountRateIdv":                          {"file": "RT",    "key": "DRI",    "dims": ["region", "technology"]},
    "DiscountRateTech":                         {"file": "RT",    "key": "DRT",    "dims": ["region", "technology"]},
    # ── RE ──
    "AnnualExogenousEmission":                  {"file": "RE",    "key": "AEE",    "dims": ["region", "emission"]},
    "ModelPeriodExogenousEmission":              {"file": "RE",    "key": "MPEE",   "dims": ["region", "emission"]},
    # ── RS ──
    "OperationalLifeStorage":                   {"file": "RS",    "key": "OLS",    "dims": ["region", "storage"]},
    "DiscountRateStorage":                      {"file": "RS",    "key": "DRS",    "dims": ["region", "storage"]},
    "MinStorageCharge":                         {"file": "RS",    "key": "MSC",    "dims": ["region", "storage"]},
    "StorageMaxChargeRate":                     {"file": "RS",    "key": "SMCR",   "dims": ["region", "storage"]},
    "StorageMaxDischargeRate":                  {"file": "RS",    "key": "SMDR",   "dims": ["region", "storage"]},
    # ── RYT ──
    "CapitalCost":                              {"file": "RYT",   "key": "CC",     "dims": ["region", "technology", "year"]},
    "FixedCost":                                {"file": "RYT",   "key": "FC",     "dims": ["region", "technology", "year"]},
    "VariableCost":                             {"file": "RYT",   "key": "VC",     "dims": ["region", "technology", "year"]},
    "ResidualCapacity":                         {"file": "RYT",   "key": "RC",     "dims": ["region", "technology", "year"]},
    "TotalAnnualMaxCapacity":                   {"file": "RYT",   "key": "TAMC",   "dims": ["region", "technology", "year"]},
    "TotalAnnualMinCapacity":                   {"file": "RYT",   "key": "TAMiC",  "dims": ["region", "technology", "year"]},
    "TotalAnnualMaxCapacityInvestment":         {"file": "RYT",   "key": "TAMCI",  "dims": ["region", "technology", "year"]},
    "TotalAnnualMinCapacityInvestment":         {"file": "RYT",   "key": "TAMiCI", "dims": ["region", "technology", "year"]},
    "TotalTechnologyAnnualActivityUpperLimit":  {"file": "RYT",   "key": "TTAAUL", "dims": ["region", "technology", "year"]},
    "TotalTechnologyAnnualActivityLowerLimit":  {"file": "RYT",   "key": "TTAALL", "dims": ["region", "technology", "year"]},
    "AvailabilityFactor":                       {"file": "RYT",   "key": "AF",     "dims": ["region", "technology", "year"]},
    "RETagTechnology":                          {"file": "RYT",   "key": "RETT",   "dims": ["region", "technology", "year"]},
    "NumberOfNewTechnologyUnits":               {"file": "RYT",   "key": "NONTU",  "dims": ["region", "technology", "year"]},
    "CapacityOfOneTechnologyUnit":              {"file": "RYT",   "key": "COOTU",  "dims": ["region", "technology", "year"]},
    # ── RYC ──
    "RETagFuel":                                {"file": "RYC",   "key": "RETF",   "dims": ["region", "commodity", "year"]},
    # ── RYE ──
    "AnnualEmissionLimit":                      {"file": "RYE",   "key": "AEL",    "dims": ["region", "emission", "year"]},
    "EmissionsPenalty":                         {"file": "RYE",   "key": "EP",     "dims": ["region", "emission", "year"]},
    "ModelPeriodEmissionLimit":                 {"file": "RYE",   "key": "MPEL",   "dims": ["region", "emission"]},
    # ── RYS ──
    "CapitalCostStorage":                       {"file": "RYS",   "key": "CCS",    "dims": ["region", "storage", "year"]},
    "ResidualStorageCapacity":                   {"file": "RYS",   "key": "RSC",    "dims": ["region", "storage", "year"]},
    # ── RYCn (constraints — not in UTOPIA but in schema) ──
    # ── RYTs ──
    "YearSplit":                                {"file": "RYTs",  "key": "YS",     "dims": ["region", "timeslice", "year"]},
    # ── RYSeDt ──
    "DaysInDayType":                            {"file": "RYSeDt","key": "DDT",    "dims": ["region", "season", "daytype", "year"]},
    # ── RYDtb ──
    "DaySplit":                                 {"file": "RYDtb", "key": "DS",     "dims": ["region", "dailytimebracket", "year"]},
    # ── RYTTs ──
    "CapacityFactor":                           {"file": "RYTTs", "key": "CF",     "dims": ["region", "technology", "timeslice", "year"]},
    "SpecifiedDemandProfile":                   {"file": "RYCTs", "key": "SDP",    "dims": ["region", "commodity", "timeslice", "year"]},
    # ── RYTM ──
    "InputActivityRatio":                       {"file": "RYTCM", "key": "IAR",    "dims": ["region", "technology", "commodity", "mode", "year"]},
    "OutputActivityRatio":                      {"file": "RYTCM", "key": "OAR",    "dims": ["region", "technology", "commodity", "mode", "year"]},
    # ── RYTEM ──
    "EmissionActivityRatio":                    {"file": "RYTE",  "key": "EAR",    "dims": ["region", "technology", "emission", "mode", "year"]},
    # ── RTSM (storage links) ──
    "TechnologyToStorage":                      {"file": "RTSM",  "key": "TTS",    "dims": ["region", "technology", "storage", "mode"]},
    "TechnologyFromStorage":                    {"file": "RTSM",  "key": "TFS",    "dims": ["region", "technology", "storage", "mode"]},
    # ── Conversions ──
    "Conversionls":                             {"file": "RYTs",  "key": "CLS",    "dims": ["region", "timeslice", "season"]},
    "Conversionld":                             {"file": "RYTs",  "key": "CLD",    "dims": ["region", "timeslice", "daytype"]},
    "Conversionlh":                             {"file": "RYTs",  "key": "CLH",    "dims": ["region", "timeslice", "dailytimebracket"]},
}

# ────────────────────────────────────────────────────────────
# ID generation
# ────────────────────────────────────────────────────────────

def _generate_id_map(set_name: str, members: list[str]) -> dict[str, str]:
    """Sorted, deterministic ID mapping.  MODE_OF_OPERATION keeps raw strings."""
    if set_name == "MODE_OF_OPERATION":
        return {m: m for m in members}
    prefix = _ID_PREFIXES.get(set_name)
    if prefix is None:
        return {m: m for m in members}
    sorted_members = sorted(members)
    return {m: f"{prefix}_{i}" for i, m in enumerate(sorted_members)}


# ────────────────────────────────────────────────────────────
# Builder helpers
# ────────────────────────────────────────────────────────────

def _map_id(raw_val: str, set_name: str, id_maps: dict[str, dict[str, str]]) -> str:
    """Look up the MUIO ID for a raw value, trying aliases."""
    m = id_maps.get(set_name, {})
    if raw_val in m:
        return m[raw_val]
    # Try alias
    alias = _SET_ALIASES.get(set_name, set_name)
    m2 = id_maps.get(alias, {})
    return m2.get(raw_val, raw_val)


def _dim_to_set(dim: str) -> str:
    """Map a dimension label to its set name."""
    return {
        "region": "REGION",
        "technology": "TECHNOLOGY",
        "commodity": "COMMODITY",
        "fuel": "COMMODITY",
        "emission": "EMISSION",
        "storage": "STORAGE",
        "mode": "MODE_OF_OPERATION",
        "year": "YEAR",
        "timeslice": "TIMESLICE",
        "season": "SEASON",
        "daytype": "DAYTYPE",
        "dailytimebracket": "DAILYTIMEBRACKET",
    }.get(dim, dim.upper())


def _dim_to_field(dim: str) -> str:
    """Map a dimension label to its MUIO JSON field name."""
    return {
        "region": "RegId",
        "technology": "TechId",
        "commodity": "CommId",
        "fuel": "CommId",
        "emission": "EmisId",
        "storage": "StgId",
        "mode": "MoId",
        "year": "Year",
        "timeslice": "TsId",
        "season": "SeId",
        "daytype": "DtId",
        "dailytimebracket": "DtbId",
    }.get(dim, dim)


# ────────────────────────────────────────────────────────────
# Transformer
# ────────────────────────────────────────────────────────────

class MuioTransformer:
    """
    Converts normalised GMPL tuples into MUIO JSON file group dicts.

    Usage::

        parsed = GMPLParser.parse_file("utopia.txt")
        normalized = SliceInterpreter().interpret(parsed)
        result = MuioTransformer.transform(parsed, normalized)

    Returns a dict keyed by file group name  (``"genData"``, ``"RYT"``,
    ``"RYTCM"``, etc.)  where each value is a dict matching the
    JSON structure written by ``CaseClass.createCase()``.
    """

    @staticmethod
    def transform(
        parsed: GMPLParseResult,
        normalized: dict[str, dict[tuple, Union[int, float]]],
    ) -> dict[str, dict]:
        """
        Build the full bag of MUIO JSON dicts.

        Parameters
        ----------
        parsed : GMPLParseResult
            Raw parse output (needed for set definitions).
        normalized : dict
            ``{param_name: {tuple: value}}`` from ``SliceInterpreter``.

        Returns
        -------
        dict[str, dict]
            Keys are file group names; values are MUIO-format dicts.
        """
        # 1. Normalise sets
        sets = MuioTransformer._normalise_sets(parsed.sets)

        # 2. ID maps
        id_maps: dict[str, dict[str, str]] = {}
        for sn, members in sets.items():
            id_maps[sn] = _generate_id_map(sn, members)

        # 3. Build genData
        gen = MuioTransformer._build_gen_data(sets, id_maps)

        # 4. Group params by file group
        file_groups: dict[str, dict[str, dict]] = {}
        for param_name, data in normalized.items():
            mapping = PARAM_MAPPING.get(param_name)
            if mapping is None:
                continue
            fg = mapping["file"]
            key = mapping["key"]
            dims = mapping["dims"]

            records = MuioTransformer._build_long_records(dims, data, id_maps)
            if fg not in file_groups:
                file_groups[fg] = {}
            file_groups[fg][key] = {"SC_0": records}

        # 5. Ensure all standard file groups exist (even if empty)
        for fg_name in _all_file_groups():
            if fg_name not in file_groups:
                file_groups[fg_name] = {}

        # 6. Package
        result = {"genData": gen}
        result.update(file_groups)
        return result

    # ── set normalisation ───────────────────────────────────
    @staticmethod
    def _normalise_sets(raw_sets: dict[str, list[str]]) -> dict[str, list[str]]:
        """Rename FUEL→COMMODITY, inject MUIO-only empty sets."""
        out: dict[str, list[str]] = {}
        for name, members in raw_sets.items():
            canonical = _SET_ALIASES.get(name, name)
            if canonical in out:
                # merge
                existing = set(out[canonical])
                existing.update(members)
                out[canonical] = sorted(existing)
            else:
                out[canonical] = list(members)
        for extra in _MUIO_ONLY_SETS:
            if extra not in out:
                out[extra] = []
        return out

    # ── genData builder ─────────────────────────────────────
    @staticmethod
    def _build_gen_data(
        sets: dict[str, list[str]],
        id_maps: dict[str, dict[str, str]],
    ) -> dict:
        years = sorted(sets.get("YEAR", []))
        techs = sets.get("TECHNOLOGY", [])
        comms = sets.get("COMMODITY", [])
        emis = sets.get("EMISSION", [])
        stgs = sets.get("STORAGE", [])
        tss = sets.get("TIMESLICE", [])
        ses = sets.get("SEASON", [])
        dts = sets.get("DAYTYPE", [])
        dtbs = sets.get("DAILYTIMEBRACKET", [])
        mos = sets.get("MODE_OF_OPERATION", [])

        tech_map = id_maps.get("TECHNOLOGY", {})
        comm_map = id_maps.get("COMMODITY", {})
        emis_map = id_maps.get("EMISSION", {})
        stg_map = id_maps.get("STORAGE", {})
        ts_map = id_maps.get("TIMESLICE", {})
        se_map = id_maps.get("SEASON", {})
        dt_map = id_maps.get("DAYTYPE", {})
        dtb_map = id_maps.get("DAILYTIMEBRACKET", {})

        gen: dict = {
            "osy-scenarios": [{"ScenarioId": "SC_0"}],
            "osy-years": years,
            "osy-mo": str(len(mos)),
            "osy-tech": [{"TechId": tech_map[t], "TechName": t} for t in sorted(techs)],
            "osy-comm": [{"CommId": comm_map[c], "CommName": c} for c in sorted(comms)],
            "osy-emis": [{"EmisId": emis_map[e], "EmisName": e} for e in sorted(emis)],
            "osy-stg":  [{"StgId": stg_map[s], "StgName": s} for s in sorted(stgs)],
            "osy-ts":   [{"TsId": ts_map[t], "TsName": t} for t in sorted(tss)],
            "osy-se":   [{"SeId": se_map[s], "SeName": s} for s in sorted(ses)],
            "osy-dt":   [{"DtId": dt_map[d], "DtName": d} for d in sorted(dts)],
            "osy-dtb":  [{"DtbId": dtb_map[d], "DtbName": d} for d in sorted(dtbs)],
            "osy-constraints": [],
        }
        return gen

    # ── record builder ──────────────────────────────────────
    @staticmethod
    def _build_long_records(
        dims: list[str],
        data: dict[tuple, Union[int, float]],
        id_maps: dict[str, dict[str, str]],
    ) -> list[dict]:
        """Build long-form records {Field: ID, ..., Value: num}."""
        records = []
        for tup, val in data.items():
            rec: dict = {}
            for di, dim in enumerate(dims):
                if di < len(tup):
                    raw = tup[di]
                    set_name = _dim_to_set(dim)
                    field_name = _dim_to_field(dim)

                    if dim == "year":
                        rec[field_name] = str(raw)
                    elif dim == "mode":
                        rec[field_name] = str(raw)
                    else:
                        rec[field_name] = _map_id(raw, set_name, id_maps)
            rec["Value"] = val
            records.append(rec)

        # Sort for deterministic output
        records.sort(key=lambda r: tuple(str(v) for v in r.values()))
        return records


# ────────────────────────────────────────────────────────────
# Standard file groups
# ────────────────────────────────────────────────────────────

def _all_file_groups() -> list[str]:
    return [
        "R", "RY", "RT", "RE", "RS",
        "RYT", "RYC", "RYE", "RYS",
        "RYCn", "RYTs", "RYSeDt", "RYDtb",
        "RYTTs", "RYCTs",
        "RYTM", "RYTCM",
        "RYTE", "RYTEM",
        "RYTSM", "RTSM",
        "RYTCn",
        "RYTTs",
        "RYCTs",
    ]


# ────────────────────────────────────────────────────────────
# CLI entry point
# ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from Classes.Case.GMPLParser import GMPLParser

    if len(sys.argv) < 2:
        print("Usage: python MuioTransformer.py <gmpl_file>")
        sys.exit(1)

    parsed = GMPLParser.parse_file(sys.argv[1])
    normalized = SliceInterpreter().interpret(parsed)
    result = MuioTransformer.transform(parsed, normalized)

    print(f"\nGenerated {len(result)} file groups:")
    for name, data in sorted(result.items()):
        if name == "genData":
            continue
        keys = list(data.keys())
        if keys:
            print(f"  {name}.json — keys: {keys[:8]}{'...' if len(keys) > 8 else ''}")

    # Print sample
    for sample_key in ["RYT", "RYTCM", "RT"]:
        if sample_key in result and result[sample_key]:
            print(f"\n── {sample_key}.json (excerpt) ──")
            print(json.dumps(result[sample_key], indent=2, default=str)[:1000])
