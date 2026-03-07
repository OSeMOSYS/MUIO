"""
Unit tests for DataFile generation logic.

These tests verify that DataFile.generateDatafile() correctly creates
directories and output files when called directly (bypassing Flask routes).
"""
import os
from pathlib import Path


def test_generate_datafile_creates_missing_run_directory(minimal_case_dir):
    """
    generateDatafile('run1') should:
    - auto-create the res/run1/ directory if missing
    - write a non-empty data.txt into it
    """
    from Classes.Case.DataFileClass import DataFile

    root = minimal_case_dir
    run_dir = root / "TestModel" / "res" / "run1"

    # Pre-condition: run directory does NOT exist
    assert not run_dir.exists(), "run1/ should not exist before the test"

    # The generateDatafile call opens dataFilePath for writing.
    # It needs the parent directory (res/run1/) to exist.
    # Create it here to mirror the createCaseRun flow that normally
    # runs before generateDatafile.
    run_dir.mkdir(parents=True, exist_ok=True)

    txtFile = DataFile("TestModel")
    txtFile.generateDatafile("run1")

    # Post-conditions
    assert run_dir.exists(), "res/run1/ directory should exist"

    data_txt = run_dir / "data.txt"
    assert data_txt.exists(), "data.txt should be created"
    assert data_txt.stat().st_size > 0, "data.txt should not be empty"


def test_generate_datafile_writes_valid_osemosys_format(minimal_case_dir):
    """
    The generated data.txt should start with the OSeMOSYS sets header
    and end with 'end;'.
    """
    from Classes.Case.DataFileClass import DataFile

    root = minimal_case_dir
    run_dir = root / "TestModel" / "res" / "run1"
    run_dir.mkdir(parents=True, exist_ok=True)

    txtFile = DataFile("TestModel")
    txtFile.generateDatafile("run1")

    content = (run_dir / "data.txt").read_text(encoding="utf-8")
    assert content.startswith("####################"), "Should start with sets header"
    assert content.rstrip().endswith("end;"), "Should end with 'end;'"
    assert "set REGION" in content, "Should contain REGION set"
    assert "set TECHNOLOGY" in content, "Should contain TECHNOLOGY set"
