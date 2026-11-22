"""Play one cave file in Shadowfall (the Godot rebuild).

    pixi run godot-cave levels/caves/03_blue_lvl_1.txt
    pixi run godot-cave my_caves/lava_tower.txt

Any cave file works: the game's own (in levels/) or one you saved from the editor.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHADOWFALL = os.path.join(ROOT, "shadowfall")
LEVELS = os.path.join(ROOT, "levels")


def godot_command(cave, godot="godot"):
    """The command that opens Shadowfall straight in this cave. Godot looks for --file inside levels/."""
    path = os.path.abspath(cave)
    if not os.path.isfile(path):
        raise FileNotFoundError("There's no cave file at %s" % cave)
    inside_levels = os.path.relpath(path, LEVELS).replace(os.sep, "/")
    return [godot, "--path", SHADOWFALL, "--", "--scene=cave", "--file=" + inside_levels]


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    godot = os.environ.get("GODOT", "godot")
    if not shutil.which(godot):
        print("I can't find Godot. Install Godot 4.7.2 so 'godot' works (see shadowfall/README.md).")
        return 1
    try:
        command = godot_command(sys.argv[1], godot)
    except FileNotFoundError as problem:
        print(problem)
        return 1
    if not os.path.isdir(os.path.join(SHADOWFALL, ".godot")):     # a fresh checkout: Godot imports once first
        subprocess.call([godot, "--headless", "--path", SHADOWFALL, "--import"])
    return subprocess.call(command)


if __name__ == "__main__":
    sys.exit(main())
