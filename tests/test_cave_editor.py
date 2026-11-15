"""
The cave editor has its own tests, in test_editor.py (pixi run test-editor).
This runs them too, so `pixi run test` checks everything in one go.
"""

import os
import subprocess
import sys

from conftest import GAME_FOLDER
from helpers import ok


def test_the_cave_editor_tests_pass():
    result = subprocess.run([sys.executable, "test_editor.py"], cwd=GAME_FOLDER, capture_output=True, text=True,
                            timeout=300, env={**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
    ok(result.returncode == 0, "test_editor.py failed:\n" + result.stdout[-3000:] + result.stderr[-3000:])
    ok("All the cave editor tests passed!" in result.stdout, "test_editor.py didn't finish:\n" + result.stdout[-3000:])
