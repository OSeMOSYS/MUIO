"""
Integration tests for the /generateDataFile Flask route.

These tests exercise the full route handler including Flask request
parsing, DataFile construction, and file writing — all against
a temporary filesystem.
"""
import json
from pathlib import Path


def test_generate_datafile_route_returns_200(app_client, minimal_case_dir):
    """
    POST /generateDataFile with valid casename + caserunname should:
    - return HTTP 200
    - return JSON with status_code == 'success'
    - create data.txt in the run directory
    """
    root = minimal_case_dir

    # Pre-create the run directory (mirrors what createCaseRun does)
    run_dir = root / "TestModel" / "res" / "run1"
    run_dir.mkdir(parents=True, exist_ok=True)

    response = app_client.post(
        "/generateDataFile",
        data=json.dumps({
            "casename": "TestModel",
            "caserunname": "run1"
        }),
        content_type="application/json",
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.data}"
    )

    body = response.get_json()
    assert body["status_code"] == "success"
    assert "message" in body

    data_txt = run_dir / "data.txt"
    assert data_txt.exists(), "data.txt should be created by the route"
    assert data_txt.stat().st_size > 0, "data.txt should not be empty"
