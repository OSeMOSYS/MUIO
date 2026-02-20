"""
Regression test for the restored-case bug.

Scenario: A case is restored from backup. The metadata (resData.json)
exists, but the run directory (res/run1/) does NOT. Calling
/generateDataFile should NOT fail.

See: conversation 72fd74f2 — "Fixing Restore Data Bug"
"""
import json
from pathlib import Path


def test_restored_case_no_500_on_generate(app_client, minimal_case_dir):
    """
    When resData.json exists with run metadata but res/run1/ directory
    is missing, the /generateDataFile route should:
    - return 200 with the directory auto-created
    - write data.txt successfully
    """
    root = minimal_case_dir
    run_dir = root / "TestModel" / "res" / "run1"

    # Confirm the restored-case scenario: metadata exists, dir does not
    res_data_path = root / "TestModel" / "view" / "resData.json"
    assert res_data_path.exists(), "resData.json should exist (restored metadata)"
    assert not run_dir.exists(), "run1/ should NOT exist (simulating restore)"

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
    assert run_dir.exists(), "Run directory should be auto-created"
    assert (run_dir / "data.txt").exists(), "data.txt should be created"
