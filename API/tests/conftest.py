"""
Shared pytest fixtures for MUIO backend tests.

All fixtures redirect Config.DATA_STORAGE to tmp_path,
so no real filesystem is touched.
"""
import sys
import os
import json
import pytest
from pathlib import Path

# ── Ensure API/ is on sys.path so 'from Classes.Base import Config' works ──
API_DIR = Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))


# ---------------------------------------------------------------------------
#  Constants used across fixtures
# ---------------------------------------------------------------------------
SC = "SC1"            # scenario id
YEAR = "2020"
TECH = "T1"
COMM = "C1"
EMIS = "E1"
STG = "S1"
TS = "TS1"
CON = "CN1"
MOD = 1
SE = "SE1"
DT = "DT1"
DTB = "DTB1"


# ---------------------------------------------------------------------------
#  Minimal fixture data generators
# ---------------------------------------------------------------------------

def _minimal_parameters():
    """Minimal Parameters.json — one param per group, matches real schema."""
    def _p(pid, val, default=0):
        return {"id": pid, "value": val, "default": default,
                "enable": True, "menu": 1, "unitRule": {"cat": []}}
    return {
        "R":     [_p("DR",   "Discount Rate",          0.05)],
        "RT":    [_p("DRI",  "Discount Rate Idv",      0.05)],
        "RE":    [_p("MPEL", "Model Period Emission Limit", 999999)],
        "RY":    [_p("DR2",  "Discount Rate",          0.05)],
        "RS":    [_p("OLS",  "Operational Life Storage",1)],
        "RYCn":  [_p("UCC",  "UDC Constant",           0)],
        "RYTCn": [_p("CCM",  "UDC Multiplier Total Capacity", 0)],
        "RYTs":  [_p("YS",   "Year Split",             1)],
        "RYDtb": [_p("DS",   "Day Split",              1)],
        "RYSeDt":[_p("DIDT", "Days In Day Type",       1)],
        "RYT":   [_p("AF",   "Availability Factor",    1)],
        "RYTM":  [_p("VC",   "Variable Cost",          0.0001)],
        "RYTC":  [_p("INCR", "Input To New Capacity Ratio", 0)],
        "RYTCM": [_p("IAR",  "Input Activity Ratio",   0)],
        "RTSM":  [_p("TTS",  "Technology To Storage",   0)],
        "RYTTs": [_p("CF",   "Capacity Factor",        1)],
        "RYC":   [_p("AAD",  "Accumulated Annual Demand",0)],
        "RYCTs": [_p("SDP",  "Specified Demand Profile",0)],
        "RYE":   [_p("AEL",  "Annual Emission Limit",  999999)],
        "RYTEM": [_p("EAR",  "Emission Activity Ratio",0)],
    }


def _minimal_variables():
    """Minimal Variables.json."""
    return {
        "R": [{"id": "OV", "value": "Objective Value",
               "name": "ObjectiveValue", "unitRule": {"cat": []}}],
    }


def _minimal_gen_data():
    """Minimal genData.json with one entry per set."""
    return {
        "osy-years": [YEAR],
        "osy-mo": "1",
        "osy-tech": [{
            "TechId": TECH, "Tech": "TECH1",
            "IAR": [COMM], "OAR": [COMM],
            "EAR": [EMIS],
            "INCR": [COMM], "ITCR": [],
            "EACR": [],
        }],
        "osy-comm": [{"CommId": COMM, "Comm": "COMM1"}],
        "osy-emis": [{"EmisId": EMIS, "Emis": "EMIS1"}],
        "osy-stg":  [{"StgId": STG, "Stg": "STG1",
                      "TTS": TECH, "TFS": TECH, "Operation": "Yearly"}],
        "osy-ts":   [{"TsId": TS, "Ts": "SLICE1",
                      "SE": SE, "DT": DT, "DTB": DTB}],
        "osy-se":   [{"SeId": SE, "Se": "SEASON1"}],
        "osy-dt":   [{"DtId": DT, "Dt": "DAYTYPE1"}],
        "osy-dtb":  [{"DtbId": DTB, "Dtb": "BRACKET1"}],
        "osy-scenarios": [{"ScenarioId": SC, "Scenario": "Base", "Active": True}],
        "osy-constraints": [{"ConId": CON, "Con": "CON1", "Tag": 1, "CM": [TECH]}],
    }


def _minimal_res_data():
    """Minimal resData.json with one case run referencing our scenario."""
    return {
        "osy-cases": [{
            "Case": "run1",
            "Scenarios": [
                {"ScenarioId": SC, "Scenario": "Base", "Active": True}
            ]
        }]
    }


# ── Per-group JSON data, matching the exact schema each parser expects ──

def _build_param_json_files():
    """
    Return a dict  {filename: data}  for every group-level JSON file.

    Each parser in OsemosysClass expects a specific nested structure:
      R.json     → { paramId: { sc: [ {value: X} ] } }
      RY.json    → { paramId: { sc: [ {year: val} ] } }
      RT.json    → { paramId: { sc: [ {techId: val} ] } }
      RE.json    → { paramId: { sc: [ {emisId: val} ] } }
      RS.json    → { paramId: { sc: [ {stgId: val} ] } }
      RYCn.json  → { paramId: { sc: [ {ConId: conId, year: val} ] } }
      RYTs.json  → { paramId: { sc: [ {TsId: tsId, year: val} ] } }
      RYDtb.json → { paramId: { sc: [ {DtbId: dtbId, year: val} ] } }
      RYSeDt.json→ { paramId: { sc: [ {SeId:.., DtId:.., year: val} ] } }
      RYT.json   → { paramId: { sc: [ {TechId:.., year: val} ] } }
      RYS.json   → { paramId: { sc: [ {StgId:.., year: val} ] } }
      RYTCn.json → { paramId: { sc: [ {TechId:.., ConId:.., year: val} ] } }
      RYTM.json  → { paramId: { sc: [ {TechId:.., MoId:.., year: val} ] } }
      RYC.json   → { paramId: { sc: [ {CommId:.., year: val} ] } }
      RYE.json   → { paramId: { sc: [ {EmisId:.., year: val} ] } }
      RYTC.json  → { paramId: { sc: [ {TechId:.., CommId:.., year: val} ] } }
      RYTCM.json → { paramId: { sc: [ {TechId:.., CommId:.., MoId:.., year: val} ] } }
      RTSM.json  → { paramId: { sc: [ {StgId:.., TechId:.., MoId:.., value: val} ] } }
      RYTSM.json → { paramId: { sc: [ {StgId:.., TechId:.., MoId:.., year: val} ] } }
      RYTE.json  → { paramId: { sc: [ {TechId:.., EmisId:.., year: val} ] } }
      RYTEM.json → { paramId: { sc: [ {TechId:.., EmisId:.., MoId:.., year: val} ] } }
      RYTTs.json → { paramId: { sc: [ {TechId:.., TsId:.., year: val} ] } }
      RYCTs.json → { paramId: { sc: [ {CommId:.., TsId:.., year: val} ] } }
    """
    y = str(YEAR)  # JSON keys for years are stringified in many parsers
    files = {}

    # R: {paramId: {sc: [{value: X}]}}
    files["R.json"] = {"DR": {SC: [{"value": 0.05}]}}

    # RY: {paramId: {sc: [{year: val}]}}
    files["RY.json"] = {"DR2": {SC: [{y: 0.05}]}}

    # RT: {paramId: {sc: [{techId: val}]}}
    files["RT.json"] = {"DRI": {SC: [{TECH: 0.05}]}}

    # RE: {paramId: {sc: [{emisId: val}]}}
    files["RE.json"] = {"MPEL": {SC: [{EMIS: 999999}]}}

    # RS: {paramId: {sc: [{stgId: val}]}}
    files["RS.json"] = {"OLS": {SC: [{STG: 1}]}}

    # RYCn: {ConId + year entries}
    files["RYCn.json"] = {"UCC": {SC: [{"ConId": CON, y: 0}]}}

    # RYTs: {TsId + year entries}
    files["RYTs.json"] = {"YS": {SC: [{"TsId": TS, y: 1}]}}

    # RYDtb: {DtbId + year entries}
    files["RYDtb.json"] = {"DS": {SC: [{"DtbId": DTB, y: 1}]}}

    # RYSeDt: {SeId + DtId + year entries}
    files["RYSeDt.json"] = {"DIDT": {SC: [{"SeId": SE, "DtId": DT, y: 1}]}}

    # RYT: {TechId + year entries}
    files["RYT.json"] = {"AF": {SC: [{"TechId": TECH, y: 1}]}}

    # RYS: {StgId + year entries}
    files["RYS.json"] = {"OLS": {SC: [{"StgId": STG, y: 1}]}}

    # RYTCn: {TechId + ConId + year entries}
    files["RYTCn.json"] = {"CCM": {SC: [{"TechId": TECH, "ConId": CON, y: 0}]}}

    # RYTM: {TechId + MoId + year entries}
    files["RYTM.json"] = {"VC": {SC: [{"TechId": TECH, "MoId": MOD, y: 0.0001}]}}

    # RYC: {CommId + year entries}
    files["RYC.json"] = {"AAD": {SC: [{"CommId": COMM, y: 0}]}}

    # RYE: {EmisId + year entries}
    files["RYE.json"] = {"AEL": {SC: [{"EmisId": EMIS, y: 999999}]}}

    # RYTC: {TechId + CommId + year entries}
    files["RYTC.json"] = {"INCR": {SC: [{"TechId": TECH, "CommId": COMM, y: 0}]}}

    # RYTCM: {TechId + CommId + MoId + year entries}
    files["RYTCM.json"] = {"IAR": {SC: [{"TechId": TECH, "CommId": COMM, "MoId": MOD, y: 0}]}}

    # RTSM: {StgId + TechId + MoId + value}  (no year dimension — directly value)
    files["RTSM.json"] = {"TTS": {SC: [{"StgId": STG, "TechId": TECH, "MoId": MOD, "value": 0}]}}

    # RYTSM: {StgId + TechId + MoId + year entries}
    files["RYTSM.json"] = {"TTS": {SC: [{"StgId": STG, "TechId": TECH, "MoId": MOD, y: 0}]}}

    # RYTE: {TechId + EmisId + year entries}
    files["RYTE.json"] = {"EAR": {SC: [{"TechId": TECH, "EmisId": EMIS, y: 0}]}}

    # RYTEM: {TechId + EmisId + MoId + year entries}
    files["RYTEM.json"] = {"EAR": {SC: [{"TechId": TECH, "EmisId": EMIS, "MoId": MOD, y: 0}]}}

    # RYTTs: {TechId + TsId + year entries}
    files["RYTTs.json"] = {"CF": {SC: [{"TechId": TECH, "TsId": TS, y: 1}]}}

    # RYCTs: {CommId + TsId + year entries}
    files["RYCTs.json"] = {"SDP": {SC: [{"CommId": COMM, "TsId": TS, y: 0}]}}

    return files


# ---------------------------------------------------------------------------
#  Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    """
    Redirect Config.DATA_STORAGE and Config.SOLVERs_FOLDER to tmp_path.
    """
    from Classes.Base import Config

    monkeypatch.setattr(Config, "DATA_STORAGE", tmp_path)
    monkeypatch.setattr(Config, "SOLVERs_FOLDER", tmp_path / "solvers")
    (tmp_path / "solvers").mkdir(exist_ok=True)

    return tmp_path


@pytest.fixture
def minimal_case_dir(temp_storage):
    """
    Scaffold a minimal model directory inside temp_storage so that
    DataFile('TestModel') can be constructed and generateDatafile() works.
    """
    root = temp_storage
    case_dir = root / "TestModel"
    case_dir.mkdir()

    # Global config files
    _write_json(root / "Parameters.json", _minimal_parameters())
    _write_json(root / "Variables.json", _minimal_variables())

    # Case-level genData
    _write_json(case_dir / "genData.json", _minimal_gen_data())

    # View directory & resData
    view_dir = case_dir / "view"
    view_dir.mkdir()
    _write_json(view_dir / "resData.json", _minimal_res_data())

    # res/ exists but run1/ does NOT — tests that need it can create it
    (case_dir / "res").mkdir()

    # Create param JSON files with structurally valid data
    for filename, data in _build_param_json_files().items():
        _write_json(case_dir / filename, data)

    return root


@pytest.fixture
def app_client(temp_storage):
    """Create a Flask test client with TESTING enabled."""
    from app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _write_json(path, data):
    """Write a Python dict as JSON to *path*."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=True, indent=2)
