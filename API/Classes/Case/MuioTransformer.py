"""
Phase 3 — MUIO Transformer.

Transforms normalized tuple output from SliceInterpreter into the exact
MUIO JSON file structures used in WebAPP/DataStorage cases.

Input
-----
    normalized_data : dict[str, dict[tuple, float]]
        Output of SliceInterpreter.interpret()
    sets : dict[str, list[str]]
        Set membership from GMPLParseResult.sets

Output
------
    Dictionary of JSON-ready structures matching MUIO format:
        genData.json, R.json, RT.json, RYT.json, RYTCM.json, …

Does NOT write any files to disk.
All records are kept in long-form: {TechId, Year, Value} — no wide pivot.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional, Union


# ─────────────────────────────────────────────────────────────
#  Parameter Mapping Registry
#  Maps OSeMOSYS parameter name → {file, key, dims}
# ─────────────────────────────────────────────────────────────

PARAM_MAPPING: dict[str, dict] = {
    # ── R (REGION only) ──
    "DiscountRate": {
        "file": "R", "key": "DR",
        "dims": ["REGION"],
    },

    # ── RT (REGION × TECHNOLOGY) ──
    "DiscountRateIdv": {
        "file": "RT", "key": "DRI",
        "dims": ["REGION", "TECHNOLOGY"],
    },
    "CapacityToActivityUnit": {
        "file": "RT", "key": "CAU",
        "dims": ["REGION", "TECHNOLOGY"],
    },
    "OperationalLife": {
        "file": "RT", "key": "OL",
        "dims": ["REGION", "TECHNOLOGY"],
    },
    "TotalTechnologyModelPeriodActivityLowerLimit": {
        "file": "RT", "key": "TMPAL",
        "dims": ["REGION", "TECHNOLOGY"],
    },
    "TotalTechnologyModelPeriodActivityUpperLimit": {
        "file": "RT", "key": "TMPAU",
        "dims": ["REGION", "TECHNOLOGY"],
    },

    # ── RE (REGION × EMISSION) ──
    "ModelPeriodEmissionLimit": {
        "file": "RE", "key": "MPEL",
        "dims": ["REGION", "EMISSION"],
    },
    "ModelPeriodExogenousEmission": {
        "file": "RE", "key": "MPEE",
        "dims": ["REGION", "EMISSION"],
    },

    # ── RS (REGION × STORAGE) ──
    "OperationalLifeStorage": {
        "file": "RS", "key": "OLS",
        "dims": ["REGION", "STORAGE"],
    },
    "StorageLevelStart": {
        "file": "RS", "key": "SLS",
        "dims": ["REGION", "STORAGE"],
    },

    # ── RY (REGION × YEAR) ──
    "DiscountRateStorage": {
        "file": "RY", "key": "DRS",
        "dims": ["REGION", "YEAR"],
    },
    "ReserveMargin": {
        "file": "RY", "key": "RM",
        "dims": ["REGION", "YEAR"],
    },

    # ── RYT (REGION × YEAR × TECHNOLOGY) ──
    "AvailabilityFactor": {
        "file": "RYT", "key": "AF",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "CapitalCost": {
        "file": "RYT", "key": "CC",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "FixedCost": {
        "file": "RYT", "key": "FC",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "ResidualCapacity": {
        "file": "RYT", "key": "RC",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalAnnualMaxCapacity": {
        "file": "RYT", "key": "TAMaxC",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalAnnualMaxCapacityInvestment": {
        "file": "RYT", "key": "TAMaxCI",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalAnnualMinCapacity": {
        "file": "RYT", "key": "TAMinC",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalAnnualMinCapacityInvestment": {
        "file": "RYT", "key": "TAMinCI",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalTechnologyAnnualActivityLowerLimit": {
        "file": "RYT", "key": "TAL",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "TotalTechnologyAnnualActivityUpperLimit": {
        "file": "RYT", "key": "TAU",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },
    "CapacityOfOneTechnologyUnit": {
        "file": "RYT", "key": "COTU",
        "dims": ["REGION", "TECHNOLOGY", "YEAR"],
    },

    # ── RYTM (REGION × YEAR × TECHNOLOGY × MODE) ──
    "VariableCost": {
        "file": "RYTM", "key": "VC",
        "dims": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    },
    "TechnologyActivityByModeLowerLimit": {
        "file": "RYTM", "key": "TAMLL",
        "dims": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    },
    "TechnologyActivityByModeUpperLimit": {
        "file": "RYTM", "key": "TAMUL",
        "dims": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    },
    "TechnologyActivityDecreaseByModeLimit": {
        "file": "RYTM", "key": "TADML",
        "dims": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    },
    "TechnologyActivityIncreasedByModeLimit": {
        "file": "RYTM", "key": "TAIML",
        "dims": ["REGION", "TECHNOLOGY", "MODE_OF_OPERATION", "YEAR"],
    },

    # ── RYTC (REGION × YEAR × TECHNOLOGY × COMMODITY) ──
    "InputToNewCapacityRatio": {
        "file": "RYTC", "key": "INCR",
        "dims": ["REGION", "TECHNOLOGY", "COMMODITY", "YEAR"],
    },
    "InputToTotalCapacityRatio": {
        "file": "RYTC", "key": "ITCR",
        "dims": ["REGION", "TECHNOLOGY", "COMMODITY", "YEAR"],
    },

    # ── RYTCM (REGION × YEAR × TECHNOLOGY × COMMODITY × MODE) ──
    "InputActivityRatio": {
        "file": "RYTCM", "key": "IAR",
        "dims": ["REGION", "TECHNOLOGY", "COMMODITY", "MODE_OF_OPERATION", "YEAR"],
    },
    "OutputActivityRatio": {
        "file": "RYTCM", "key": "OAR",
        "dims": ["REGION", "TECHNOLOGY", "COMMODITY", "MODE_OF_OPERATION", "YEAR"],
    },

    # ── RYC (REGION × YEAR × COMMODITY) ──
    "AccumulatedAnnualDemand": {
        "file": "RYC", "key": "AAD",
        "dims": ["REGION", "COMMODITY", "YEAR"],
    },
    "SpecifiedAnnualDemand": {
        "file": "RYC", "key": "SAD",
        "dims": ["REGION", "COMMODITY", "YEAR"],
    },

    # ── RYE (REGION × YEAR × EMISSION) ──
    "AnnualEmissionLimit": {
        "file": "RYE", "key": "AEL",
        "dims": ["REGION", "EMISSION", "YEAR"],
    },
    "EmissionsPenalty": {
        "file": "RYE", "key": "EP",
        "dims": ["REGION", "EMISSION", "YEAR"],
    },
    "AnnualExogenousEmission": {
        "file": "RYE", "key": "AEE",
        "dims": ["REGION", "EMISSION", "YEAR"],
    },

    # ── RYS (REGION × YEAR × STORAGE) ──
    "CapitalCostStorage": {
        "file": "RYS", "key": "CCS",
        "dims": ["REGION", "STORAGE", "YEAR"],
    },
    "ResidualStorageCapacity": {
        "file": "RYS", "key": "RSC",
        "dims": ["REGION", "STORAGE", "YEAR"],
    },
    "MinStorageCharge": {
        "file": "RYS", "key": "MSC",
        "dims": ["REGION", "STORAGE", "YEAR"],
    },

    # ── RYTs (REGION × YEAR × TIMESLICE) ──
    "YearSplit": {
        "file": "RYTs", "key": "YS",
        "dims": ["REGION", "TIMESLICE", "YEAR"],
    },

    # ── RYTTs (REGION × YEAR × TECHNOLOGY × TIMESLICE) ──
    "CapacityFactor": {
        "file": "RYTTs", "key": "CF",
        "dims": ["REGION", "TECHNOLOGY", "TIMESLICE", "YEAR"],
    },

    # ── RYCTs (REGION × YEAR × COMMODITY × TIMESLICE) ──
    "SpecifiedDemandProfile": {
        "file": "RYCTs", "key": "SDP",
        "dims": ["REGION", "COMMODITY", "TIMESLICE", "YEAR"],
    },

    # ── RYTE (REGION × YEAR × TECHNOLOGY × EMISSION) ──
    "ReserveMarginTagFuel": {
        "file": "RYTE", "key": "RMTagF",
        "dims": ["REGION", "TECHNOLOGY", "EMISSION", "YEAR"],
    },
    "ReserveMarginTagTechnology": {
        "file": "RYTE", "key": "RMTagT",
        "dims": ["REGION", "TECHNOLOGY", "EMISSION", "YEAR"],
    },

    # ── RYTEM (REGION × YEAR × TECHNOLOGY × EMISSION × MODE) ──
    "EmissionActivityRatio": {
        "file": "RYTEM", "key": "EAR",
        "dims": ["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
    },
    "EmissionActivityChangeRatio": {
        "file": "RYTEM", "key": "EACR",
        "dims": ["REGION", "TECHNOLOGY", "EMISSION", "MODE_OF_OPERATION", "YEAR"],
    },

    # ── RTSM (REGION × TECHNOLOGY × STORAGE × MODE) — no YEAR ──
    "TechnologyToStorage": {
        "file": "RTSM", "key": "TTS",
        "dims": ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    },
    "TechnologyFromStorage": {
        "file": "RTSM", "key": "TFS",
        "dims": ["REGION", "TECHNOLOGY", "STORAGE", "MODE_OF_OPERATION"],
    },

    # ── RYDtb (REGION × YEAR × DAILYTIMEBRACKET) ──
    "DaySplit": {
        "file": "RYDtb", "key": "DS",
        "dims": ["REGION", "DAILYTIMEBRACKET", "YEAR"],
    },

    # ── RYSeDt (REGION × YEAR × SEASON × DAYTYPE) ──
    "DaysInDayType": {
        "file": "RYSeDt", "key": "DIDT",
        "dims": ["REGION", "SEASON", "DAYTYPE", "YEAR"],
    },

    # ── Conversion matrices (special — timeslice metadata) ──
    "Conversionls": {
        "file": "_conv", "key": "Conversionls",
        "dims": ["TIMESLICE", "SEASON"],
    },
    "Conversionld": {
        "file": "_conv", "key": "Conversionld",
        "dims": ["TIMESLICE", "DAYTYPE"],
    },
    "Conversionlh": {
        "file": "_conv", "key": "Conversionlh",
        "dims": ["TIMESLICE", "DAILYTIMEBRACKET"],
    },

    # ── RYCn (REGION × YEAR × CONSTRAINT) ──
    "UDCConstant": {
        "file": "RYCn", "key": "UCC",
        "dims": ["REGION", "CONSTRAINT", "YEAR"],
    },

    # ── RYTCn (REGION × YEAR × TECHNOLOGY × CONSTRAINT) ──
    "UDCMultiplierTotalCapacity": {
        "file": "RYTCn", "key": "CCM",
        "dims": ["REGION", "TECHNOLOGY", "CONSTRAINT", "YEAR"],
    },
    "UDCMultiplierNewCapacity": {
        "file": "RYTCn", "key": "CNCM",
        "dims": ["REGION", "TECHNOLOGY", "CONSTRAINT", "YEAR"],
    },
    "UDCMultiplierActivity": {
        "file": "RYTCn", "key": "CAM",
        "dims": ["REGION", "TECHNOLOGY", "CONSTRAINT", "YEAR"],
    },
}


# Map dimension names → MUIO record field names
DIM_TO_FIELD: dict[str, str] = {
    "REGION":           "RegId",
    "TECHNOLOGY":       "TechId",
    "COMMODITY":        "CommId",
    "EMISSION":         "EmisId",
    "STORAGE":          "StgId",
    "MODE_OF_OPERATION": "MoId",
    "TIMESLICE":        "TsId",
    "SEASON":           "SeId",
    "DAYTYPE":          "DtId",
    "DAILYTIMEBRACKET": "DtbId",
    "CONSTRAINT":       "ConId",
    "YEAR":             "Year",
}


class MuioTransformer:
    """Transform SliceInterpreter output to MUIO JSON structures."""

    def __init__(
        self,
        normalized_data: dict[str, dict[tuple, Union[int, float]]],
        sets: dict[str, list[str]],
        casename: str = "ImportedCase",
        description: str = "",
    ):
        self._norm = normalized_data
        self._raw_sets = dict(sets)
        self._casename = casename
        self._description = description

        # ── Step 1: Set Normalization ──
        self._sets = self._normalize_sets(self._raw_sets)

        # ── Step 2: ID Generation ──
        self._id_maps: dict[str, dict[str, str]] = {}
        self._gen_ids()

    # ─────────────────────────────────────────────────────────
    #  Step 1 — Set Normalization
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_sets(sets: dict[str, list[str]]) -> dict[str, list[str]]:
        """Rename FUEL → COMMODITY and inject MUIO-only sets."""
        out = dict(sets)

        # Rename FUEL → COMMODITY
        if "FUEL" in out and "COMMODITY" not in out:
            out["COMMODITY"] = out.pop("FUEL")
        elif "FUEL" in out and "COMMODITY" in out:
            combined = list(dict.fromkeys(out["COMMODITY"] + out["FUEL"]))
            out["COMMODITY"] = combined
            del out["FUEL"]

        # Inject empty MUIO-only sets if missing
        for s in ("STORAGEINTRADAY", "STORAGEINTRAYEAR", "UDC"):
            if s not in out:
                out[s] = []

        return out

    # ─────────────────────────────────────────────────────────
    #  Step 2 — ID Generation (deterministic, sorted)
    # ─────────────────────────────────────────────────────────

    def _gen_ids(self) -> None:
        """Generate deterministic MUIO IDs for all index sets."""
        id_specs = {
            "TECHNOLOGY":       "T",
            "COMMODITY":        "C",
            "EMISSION":         "E",
            "STORAGE":          "S",
            "TIMESLICE":        "Ts",
            "SEASON":           "SE",
            "DAYTYPE":          "DT",
            "DAILYTIMEBRACKET": "DTB",
        }

        for set_name, prefix in id_specs.items():
            members = sorted(self._sets.get(set_name, []))
            self._id_maps[set_name] = {
                member: f"{prefix}_{i}" for i, member in enumerate(members)
            }

        # MODE_OF_OPERATION — raw string, no remapping
        modes = self._sets.get("MODE_OF_OPERATION", [])
        self._id_maps["MODE_OF_OPERATION"] = {m: str(m) for m in modes}

        # REGION — keep original names
        regions = self._sets.get("REGION", [])
        self._id_maps["REGION"] = {r: r for r in regions}

        # YEAR — keep as string
        years = self._sets.get("YEAR", [])
        self._id_maps["YEAR"] = {y: str(y) for y in years}

    # ─────────────────────────────────────────────────────────
    #  Step 3 — ID translation helper
    # ─────────────────────────────────────────────────────────

    def _translate_id(self, dim_name: str, original_val: str) -> str:
        """Translate an original set member to its MUIO ID."""
        return self._id_maps.get(dim_name, {}).get(original_val, original_val)

    # ─────────────────────────────────────────────────────────
    #  Public API
    # ─────────────────────────────────────────────────────────

    def transform(self) -> dict[str, dict]:
        """
        Returns dict keyed by filename (without .json):
            {"genData": {...}, "RYT": {...}, "RT": {...}, ...}
        """
        result: dict[str, dict] = {}

        # Build genData
        result["genData"] = self._build_gen_data()

        # Build all file groups
        file_params: dict[str, list[tuple[str, str, list[str]]]] = defaultdict(list)
        for param_name, mapping in PARAM_MAPPING.items():
            fg = mapping["file"]
            key = mapping["key"]
            dims = mapping["dims"]
            if fg == "_conv":
                continue  # special
            file_params[fg].append((param_name, key, dims))

        for fg, params in file_params.items():
            if fg not in result:
                result[fg] = {}
            for param_name, muio_key, dims in params:
                data = self._norm.get(param_name, {})
                result[fg][muio_key] = self._build_records(fg, dims, data)

        # Conversion matrices
        result["_conv"] = self._build_conversions()

        return result

    # ─────────────────────────────────────────────────────────
    #  Step 5 — Record Builders
    #  Each returns {SC_0: [records]}
    #  All records are LONG-FORM — no wide year pivot.
    # ─────────────────────────────────────────────────────────

    def _build_records(
        self,
        file_group: str,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        """Route to the correct builder based on file group."""
        if file_group == "R":
            return self._build_R(data)
        elif file_group == "RT":
            return self._build_RT(dims, data)
        elif file_group == "RE":
            return self._build_RE(dims, data)
        elif file_group == "RS":
            return self._build_RS(dims, data)
        elif file_group == "RY":
            return self._build_RY(dims, data)
        elif file_group == "RYT":
            return self._build_RYT(dims, data)
        elif file_group == "RYTM":
            return self._build_RYTM(dims, data)
        elif file_group == "RYTC":
            return self._build_RYTC(dims, data)
        elif file_group == "RYTCM":
            return self._build_RYTCM(dims, data)
        elif file_group == "RYC":
            return self._build_RYC(dims, data)
        elif file_group == "RYE":
            return self._build_RYE(dims, data)
        elif file_group == "RYS":
            return self._build_RYS(dims, data)
        elif file_group == "RYTs":
            return self._build_RYTs(dims, data)
        elif file_group == "RYTTs":
            return self._build_RYTTs(dims, data)
        elif file_group == "RYCTs":
            return self._build_RYCTs(dims, data)
        elif file_group == "RYTE":
            return self._build_RYTE(dims, data)
        elif file_group == "RYTEM":
            return self._build_RYTEM(dims, data)
        elif file_group == "RTSM":
            return self._build_RTSM(dims, data)
        elif file_group == "RYDtb":
            return self._build_RYDtb(dims, data)
        elif file_group == "RYSeDt":
            return self._build_RYSeDt(dims, data)
        elif file_group == "RYCn":
            return self._build_RYCn(dims, data)
        elif file_group == "RYTCn":
            return self._build_RYTCn(dims, data)
        else:
            return self._build_generic_long(dims, data)

    # ── Generic long-form builder ──

    def _build_generic_long(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        """
        Generic long-form builder: one record per tuple.
        Record = {DimField1: id, DimField2: id, ..., Value: val}
        """
        records = []
        for tup, val in sorted(data.items()):
            record: dict = {}
            for i, dim in enumerate(dims):
                if i >= len(tup):
                    break
                field = DIM_TO_FIELD.get(dim, dim)
                record[field] = self._translate_id(dim, tup[i])
            record["Value"] = val
            records.append(record)
        return {"SC_0": records}

    # ── R: single value ──

    def _build_R(
        self,
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        if data:
            for tup, val in data.items():
                records.append({"Value": val})
                break
        return {"SC_0": records}

    # ── RT: REGION × TECHNOLOGY ──

    def _build_RT(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RE: REGION × EMISSION ──

    def _build_RE(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            emis = tup[1] if len(tup) > 1 else ""
            records.append({
                "EmisId": self._translate_id("EMISSION", emis),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RS: REGION × STORAGE ──

    def _build_RS(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            stg = tup[1] if len(tup) > 1 else ""
            records.append({
                "StgId": self._translate_id("STORAGE", stg),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RY: REGION × YEAR ──

    def _build_RY(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            year = tup[1] if len(tup) > 1 else ""
            records.append({
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYT: REGION × TECHNOLOGY × YEAR ──

    def _build_RYT(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTM: REGION × TECHNOLOGY × MODE × YEAR ──

    def _build_RYTM(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            mode = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "MoId": str(mode),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTC: REGION × TECHNOLOGY × COMMODITY × YEAR ──

    def _build_RYTC(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            comm = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "CommId": self._translate_id("COMMODITY", comm),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTCM: REGION × TECHNOLOGY × COMMODITY × MODE × YEAR ──

    def _build_RYTCM(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            comm = tup[2] if len(tup) > 2 else ""
            mode = tup[3] if len(tup) > 3 else ""
            year = tup[4] if len(tup) > 4 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "CommId": self._translate_id("COMMODITY", comm),
                "MoId": str(mode),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYC: REGION × COMMODITY × YEAR ──

    def _build_RYC(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            comm = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "CommId": self._translate_id("COMMODITY", comm),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYE: REGION × EMISSION × YEAR ──

    def _build_RYE(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            emis = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "EmisId": self._translate_id("EMISSION", emis),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYS: REGION × STORAGE × YEAR ──

    def _build_RYS(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            stg = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "StgId": self._translate_id("STORAGE", stg),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTs: REGION × TIMESLICE × YEAR ──

    def _build_RYTs(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            ts = tup[0] if len(tup) > 0 else ""
            year = tup[1] if len(tup) > 1 else ""
            records.append({
                "TsId": self._translate_id("TIMESLICE", ts),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTTs: REGION × TECHNOLOGY × TIMESLICE × YEAR ──

    def _build_RYTTs(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            ts = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "TsId": self._translate_id("TIMESLICE", ts),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYCTs: REGION × COMMODITY × TIMESLICE × YEAR ──

    def _build_RYCTs(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            comm = tup[1] if len(tup) > 1 else ""
            ts = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "CommId": self._translate_id("COMMODITY", comm),
                "TsId": self._translate_id("TIMESLICE", ts),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTE: REGION × TECHNOLOGY × EMISSION × YEAR ──

    def _build_RYTE(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            emis = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "EmisId": self._translate_id("EMISSION", emis),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTEM: REGION × TECHNOLOGY × EMISSION × MODE × YEAR ──

    def _build_RYTEM(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            emis = tup[2] if len(tup) > 2 else ""
            mode = tup[3] if len(tup) > 3 else ""
            year = tup[4] if len(tup) > 4 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "EmisId": self._translate_id("EMISSION", emis),
                "MoId": str(mode),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RTSM: REGION × TECHNOLOGY × STORAGE × MODE (no YEAR) ──

    def _build_RTSM(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            stg = tup[2] if len(tup) > 2 else ""
            mode = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "StgId": self._translate_id("STORAGE", stg),
                "MoId": str(mode),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYDtb: REGION × DAILYTIMEBRACKET × YEAR ──

    def _build_RYDtb(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            dtb = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "DtbId": self._translate_id("DAILYTIMEBRACKET", dtb),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYSeDt: REGION × SEASON × DAYTYPE × YEAR ──

    def _build_RYSeDt(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            se = tup[1] if len(tup) > 1 else ""
            dt = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "SeId": self._translate_id("SEASON", se),
                "DtId": self._translate_id("DAYTYPE", dt),
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYCn: REGION × CONSTRAINT × YEAR ──

    def _build_RYCn(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            con = tup[1] if len(tup) > 1 else ""
            year = tup[2] if len(tup) > 2 else ""
            records.append({
                "ConId": con,
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ── RYTCn: REGION × TECHNOLOGY × CONSTRAINT × YEAR ──

    def _build_RYTCn(
        self,
        dims: list[str],
        data: dict[tuple, Union[int, float]],
    ) -> dict[str, list]:
        records = []
        for tup, val in sorted(data.items()):
            tech = tup[1] if len(tup) > 1 else ""
            con = tup[2] if len(tup) > 2 else ""
            year = tup[3] if len(tup) > 3 else ""
            records.append({
                "TechId": self._translate_id("TECHNOLOGY", tech),
                "ConId": con,
                "Year": str(year),
                "Value": val,
            })
        return {"SC_0": records}

    # ─────────────────────────────────────────────────────────
    #  Step 6 — genData.json Builder
    # ─────────────────────────────────────────────────────────

    def _build_gen_data(self) -> dict:
        """Build genData.json metadata."""
        years = sorted(self._sets.get("YEAR", []))
        techs = sorted(self._sets.get("TECHNOLOGY", []))
        comms = sorted(self._sets.get("COMMODITY", []))
        emis = sorted(self._sets.get("EMISSION", []))
        stgs = sorted(self._sets.get("STORAGE", []))
        modes = sorted(self._sets.get("MODE_OF_OPERATION", []))
        ts_members = sorted(self._sets.get("TIMESLICE", []))
        seasons = sorted(self._sets.get("SEASON", []))
        daytypes = sorted(self._sets.get("DAYTYPE", []))
        dtbrackets = sorted(self._sets.get("DAILYTIMEBRACKET", []))
        regions = self._sets.get("REGION", [])

        # Technology entries (with IAR/OAR/EAR commodity/emission links)
        tech_entries = []
        for t in techs:
            tid = self._id_maps["TECHNOLOGY"][t]
            entry: dict = {
                "TechId": tid,
                "Tech": t,
                "Desc": "",
                "IAR": self._get_linked_commodities(t, "InputActivityRatio"),
                "OAR": self._get_linked_commodities(t, "OutputActivityRatio"),
                "EAR": self._get_linked_emissions(t),
                "TTS": self._get_linked_storage(t, "TechnologyToStorage"),
                "TFS": self._get_linked_storage(t, "TechnologyFromStorage"),
            }
            tech_entries.append(entry)

        # Commodity entries
        comm_entries = [
            {"CommId": self._id_maps["COMMODITY"][c], "Comm": c, "Desc": ""}
            for c in comms
        ]

        # Emission entries
        emis_entries = [
            {"EmisId": self._id_maps["EMISSION"][e], "Emis": e, "Desc": ""}
            for e in emis
        ]

        # Storage entries (with TTS/TFS tech links)
        stg_entries = []
        for s in stgs:
            sid = self._id_maps["STORAGE"][s]
            entry = {
                "StgId": sid,
                "Stg": s,
                "Desc": "",
                "TTS": self._get_storage_linked_tech(s, "TechnologyToStorage"),
                "TFS": self._get_storage_linked_tech(s, "TechnologyFromStorage"),
            }
            stg_entries.append(entry)

        # Timeslice entries
        ts_entries = [
            {"TsId": self._id_maps["TIMESLICE"].get(ts, f"Ts_{i}"), "Ts": ts, "Desc": ""}
            for i, ts in enumerate(ts_members)
        ]

        # Season entries
        se_entries = [
            {"SeId": self._id_maps.get("SEASON", {}).get(se, f"SE_{i}"), "Se": se, "Desc": ""}
            for i, se in enumerate(seasons)
        ] if seasons else [{"SeId": "SE_0", "Se": "1", "Desc": "Default season"}]

        # Day type entries
        dt_entries = [
            {"DtId": self._id_maps.get("DAYTYPE", {}).get(dt, f"DT_{i}"), "Dt": dt, "Desc": ""}
            for i, dt in enumerate(daytypes)
        ] if daytypes else [{"DtId": "DT_0", "Dt": "1", "Desc": "Default day type"}]

        # Daily time bracket entries
        dtb_entries = [
            {"DtbId": self._id_maps.get("DAILYTIMEBRACKET", {}).get(dtb, f"DTB_{i}"), "Dtb": dtb, "Desc": ""}
            for i, dtb in enumerate(dtbrackets)
        ] if dtbrackets else [{"DtbId": "DTB_0", "Dtb": "1", "Desc": "Default daily time bracket"}]

        gen_data = {
            "osy-casename": self._casename,
            "osy-desc": self._description,
            "osy-region": regions[0] if regions else "",
            "osy-years": years,
            "osy-mo": len(modes),
            "osy-ns": len(seasons) if seasons else 1,
            "osy-tech": tech_entries,
            "osy-comm": comm_entries,
            "osy-emis": emis_entries,
            "osy-stg": stg_entries,
            "osy-ts": ts_entries,
            "osy-se": se_entries,
            "osy-dt": dt_entries,
            "osy-dtb": dtb_entries,
            "osy-scenarios": [
                {"ScenarioId": "SC_0", "Sc": "Baseline", "Desc": "Default scenario"}
            ],
            "osy-techGroups": [
                {"TechId": e["TechId"], "group": ""} for e in tech_entries
            ],
            "osy-constraints": [],
        }

        return gen_data

    # ─────────────────────────────────────────────────────────
    #  Helpers — commodity/emission/storage linkage
    # ─────────────────────────────────────────────────────────

    def _get_linked_commodities(self, tech: str, param_name: str) -> list[str]:
        """Get commodity IDs linked to a technology via IAR or OAR."""
        data = self._norm.get(param_name, {})
        comms: set[str] = set()
        for tup in data.keys():
            if len(tup) >= 3 and tup[1] == tech:
                comm = tup[2]
                comm_id = self._id_maps.get("COMMODITY", {}).get(comm, comm)
                comms.add(comm_id)
        return sorted(comms)

    def _get_linked_emissions(self, tech: str) -> list[str]:
        """Get emission IDs linked to a technology via EAR."""
        data = self._norm.get("EmissionActivityRatio", {})
        emis: set[str] = set()
        for tup in data.keys():
            if len(tup) >= 3 and tup[1] == tech:
                emi = tup[2]
                emi_id = self._id_maps.get("EMISSION", {}).get(emi, emi)
                emis.add(emi_id)
        return sorted(emis)

    def _get_linked_storage(self, tech: str, param_name: str) -> Optional[str]:
        """Get storage ID linked to a tech via TTS or TFS."""
        data = self._norm.get(param_name, {})
        for tup in data.keys():
            if len(tup) >= 3 and tup[1] == tech:
                stg = tup[2]
                return self._id_maps.get("STORAGE", {}).get(stg, stg)
        return None

    def _get_storage_linked_tech(self, stg: str, param_name: str) -> Optional[str]:
        """Get technology ID linked to a storage via TTS or TFS."""
        data = self._norm.get(param_name, {})
        for tup in data.keys():
            if len(tup) >= 3 and tup[2] == stg:
                tech = tup[1]
                return self._id_maps.get("TECHNOLOGY", {}).get(tech, tech)
        return None

    # ─────────────────────────────────────────────────────────
    #  Conversion matrix handling
    # ─────────────────────────────────────────────────────────

    def _build_conversions(self) -> dict:
        """Build conversion matrices as timeslice → target mappings."""
        result = {}
        for param_name in ("Conversionls", "Conversionld", "Conversionlh"):
            data = self._norm.get(param_name, {})
            mapping = {}
            for tup, val in data.items():
                if len(tup) >= 2 and val == 1:
                    ts = tup[0]
                    target = tup[1]
                    ts_id = self._id_maps.get("TIMESLICE", {}).get(ts, ts)
                    mapping[ts_id] = target
            result[param_name] = mapping
        return result

    # ─────────────────────────────────────────────────────────
    #  Public getters
    # ─────────────────────────────────────────────────────────

    @property
    def id_maps(self) -> dict[str, dict[str, str]]:
        """Original name → MUIO ID mappings."""
        return dict(self._id_maps)

    @property
    def sets(self) -> dict[str, list[str]]:
        """Normalized sets."""
        return dict(self._sets)


# ─────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

    from Classes.Case.GMPLParser import GMPLParser
    from Classes.Case.SliceInterpreter import SliceInterpreter

    if len(sys.argv) < 2:
        print("Usage: python MuioTransformer.py <gmpl_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    parsed = GMPLParser.parse_file(filepath)
    interp = SliceInterpreter(parsed)
    norm = interp.interpret()

    transformer = MuioTransformer(
        normalized_data=norm,
        sets=parsed.sets,
        casename=Path(filepath).stem,
    )
    result = transformer.transform()

    print(f"\nGenerated {len(result)} file groups:")
    for name, data in sorted(result.items()):
        if isinstance(data, dict):
            keys = list(data.keys())
            print(f"  {name}.json — keys: {keys[:8]}{'...' if len(keys) > 8 else ''}")

    # Print sample long-form records
    for sample_key in ("RYT", "RYTCM", "RT"):
        if sample_key in result:
            print(f"\n── {sample_key}.json (excerpt) ──")
            print(json.dumps(result[sample_key], indent=2, default=str)[:1000])
