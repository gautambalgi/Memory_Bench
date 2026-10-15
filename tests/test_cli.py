import json
import os
import subprocess
import sys


def test_cli_demo_outputs_portable_record(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "memorybench", "--provider", "demo"],
        env={**os.environ, "MB_DATA_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    run = json.loads(result.stdout)
    assert run["status"] == "completed"
    assert "$8.59" in run["answer"]
    assert run["events"][-1]["kind"] == "run_finished"


def test_cli_does_not_present_demo_as_general_ai(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "memorybench", "--provider", "demo", "Do something else"],
        env={**os.environ, "MB_DATA_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 2
    assert "built-in sample" in result.stderr
