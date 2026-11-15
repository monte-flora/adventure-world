"""The Phase 3 Godot prototype (godot/): it loads with no script errors and its logic tests pass.

Skipped when the `godot` command isn't installed (for example on GitHub's test machines).
Run the Godot tests by hand with:  godot --headless --path godot res://tests/run_tests.tscn
"""

import shutil
import subprocess
from pathlib import Path

import pytest

GODOT = shutil.which("godot")
PROJECT = Path(__file__).resolve().parent.parent / "godot"

pytestmark = pytest.mark.skipif(GODOT is None, reason="godot isn't installed")

ERRORS = ("SCRIPT ERROR", "Parse Error", "Compile Error", "Failed to load script")


def godot(*args, timeout=180):
    result = subprocess.run([GODOT, "--headless", "--path", str(PROJECT), *args],
                            capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout + result.stderr


def test_godot_prototype():
    # One test, so two pytest workers never run Godot on the same project at once.
    code, out = godot("--import", timeout=300)
    assert code == 0, out
    code, out = godot("--quit")
    assert code == 0, out
    assert not any(e in out for e in ERRORS), out
    code, out = godot("res://tests/run_tests.tscn")
    assert not any(e in out for e in ERRORS), out
    assert code == 0 and " 0 failed" in out, out
