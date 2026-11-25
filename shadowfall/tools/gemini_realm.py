"""pixi run gemini-realm B3 [--export | --import] [--style PICTURE] [--downloads DIR]: paint one realm
screen as one Gemini painting (levels/polish/README.txt, "Paint a realm screen").

--export writes levels/polish/realm_B3/: layout.png (the screen as a map, 2752x1536: ground colours,
our props drawn where the game puts them; tools/realm_layout.tscn makes it in Godot), legend.png,
prompt.txt (kept if you edited it) and README.txt.
--import turns the picture you saved there into painted.webp (960x544, the screen's own pixels, under
1 MB). The land file's `painted_screen: B3` line shows it in the game (painted/realm_screen.gd).
With neither: export, put the map on the clipboard and open Gemini; Enter -> your style picture (the
painted-realm mockup, --style) on the clipboard; Enter -> the words; then it waits for the painting
in ~/Downloads, moves it in and imports it. macOS (osascript, pbcopy, open). It never touches the
website beyond opening it: no clicking, no scraping, no API, no keys.
"""

import json
import os
import subprocess
import sys
import time

import gemini_caves as gc
import gemini_next as gn
import polish

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEVELS = os.path.join(ROOT, "levels")
SCREEN_PX = (960, 544)                       # 30 x 17 squares of 32 px
# The user's style picture (their own art: never in the repo), next to the checkouts by default.
STYLE = os.path.join(os.path.dirname(ROOT), "refs", "realm_target_painted_mockup.jpg")

# What each layout colour is, in words for the painter (painted/realm_screen.gd LAYOUT).
GROUND = {
    "grass": "green = wild grass", "forest_floor": "dark green = forest floor under the trees",
    "dirt_road": "tan = a worn dirt road", "cobblestone": "grey = old cobblestones (the village square)",
    "mud": "brown = mud", "shallow_water": "light blue = shallow water", "deep_water": "dark blue = deep water",
    "rocky_ground": "grey-brown = rocky ground",
    "cliff": "near-black = cliffs and rock walls: raised ledges with real height and a shadowed face",
    "ice": "pale blue = ice",
    "gate": "magenta = plain open ground of the path there (the game draws the rubble, thorns or ivy on top)",
}
# Our props, as the painter should see them (anything else: its name).
PROPS = {
    "cottage_a": "timber cottages with steep roofs and warm lit windows", "cottage_b": None,
    "tavern": "a long timber tavern with lit windows and a smoking chimney",
    "smithy": "a stone smithy with a glowing forge", "well": "a mossy stone well",
    "campfire": "a campfire in a ring of stones (the village heart)",
    "lamppost": "iron lampposts with burning lanterns", "fence": "split-rail wooden fences",
    "cart": "a wooden cart", "flowers": "small wildflower patches", "bush": "bushes",
    "rocks": "boulders", "fallen_log": "a fallen mossy log", "oak": "broad oaks", "pine": "dark pines",
    "dead_tree": "bare dead trees", "crag": "jagged grey crags along the rock walls",
    "mine_mouth": "a Mine mouth: a black cave arch cut into the rock, timber-framed",
    "waystone": "a carved runic waystone", "ruined_wall": "a ruined stone wall",
}


def folder(screen, levels=LEVELS):
    return os.path.join(levels, "polish", "realm_" + screen.upper())


def land_file(land, levels=LEVELS):
    d = os.path.join(levels, "realm")
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        path = os.path.join(d, f)
        if f.endswith(".txt") and polish.header(open(path, encoding="utf-8").read().splitlines(), "land") == land:
            return path
    return None


def villages(screen, land, levels=LEVELS):
    """The land's `village:` names whose middle is on this screen."""
    path = land_file(land, levels)
    if not path:
        return []
    lines = open(path, encoding="utf-8").read().splitlines()
    at = [int(v) for v in polish.header(lines, "at").split()] or [0, 0]
    col, row = ord(screen[0].upper()) - 65, int(screen[1:]) - 1
    out = []
    for line in lines:
        if line.startswith("village:"):
            parts = line.split(":", 1)[1].split()
            r, c = at[0] + float(parts[-2]), at[1] + float(parts[-1])
            if int(c // 30) == col and int(r // 17) == row:
                out.append(" ".join(parts[:-2]))
    return out


def prompt(info, village_names=()):
    """The words to paste into Gemini after the map and the style picture."""
    place = info.get("land_name") or info.get("land", "")
    if village_names:
        place = "%s, the last hearth-village of %s" % (" and ".join(village_names), place)
    roles = [GROUND[k] for k, _ in info.get("legend", []) if k in info.get("roles", {}) and k in GROUND]
    things = []
    for name in sorted(info.get("props", {}), key=lambda n: -info["props"][n]):
        words = PROPS["crag"] if name.endswith("crag") else PROPS.get(name, name.replace("_", " "))
        if name == "cottage_b":
            words = PROPS["cottage_a"] if "cottage_a" not in info["props"] else None
        if words and words not in things:
            things.append(words)
    return "\n".join([
        "Paint the first picture (the map) as ONE continuous hand-painted pixel-art scene: one screen of "
        "the overworld of a 2D top-down fantasy game, the same 3/4 top-down view as the map (not isometric).",
        "Style: exactly like the second picture (the style picture): ground that blends softly from one kind "
        "to the next, worn winding paths, cliffs and raised ledges with real height, every building and "
        "tree grounded with dirt, moss and roots at its base, composed and full of detail.",
        "",
        "Place: %s. Dusk: cold blue shadows, warm fire and window light." % place,
        "Mood: grim, epic and ancient, a war-torn realm of old kingdoms holding out against the dark. "
        "Original art, teen-safe, no gore.",
        "",
        "Keep the layout exactly: " + "; ".join(roles) + ".",
        "Every path, wall, cliff, water edge and building stays exactly where the map shows it, the same "
        "size; do not move, add or remove any.",
        "The shapes on the map are rough stand-ins for our props: paint each as a real, detailed thing in "
        "the same spot, size and outline: " + "; ".join(things) + ".",
        "",
        "No characters, creatures, people, animals, text, letters, numbers, UI or grid lines.",
        "Same size and shape as the map: 2752x1536, 16:9, the whole frame filled edge to edge, no border.",
    ]) + "\n"


README = """\
Paint this realm screen with Gemini: pixi run gemini-realm {screen}

1. The map (layout.png) goes into Gemini's chat first (Cmd+V), then your style picture
   (the painted-realm mockup), then the words (prompt.txt). Send.
2. Download the painting you like: gemini-realm moves it here and makes painted.webp.
   (By hand: save it in this folder, then pixi run gemini-realm {screen} --import)
3. pixi run game: the screen is the painting (the land file's `painted_screen: {screen}` line).

legend.png says what each colour on the map means. Change prompt.txt freely: it is never overwritten.
"""


def export(screen, levels=LEVELS, run_cmd=subprocess.run, godot=None):
    """layout.png + layout.json (Godot), legend.png, prompt.txt (kept if there), README.txt. Returns the folder."""
    out = folder(screen, levels)
    os.makedirs(out, exist_ok=True)
    godot = godot or os.environ.get("GODOT", "godot")
    run_cmd([godot, "--headless", "--audio-driver", "Dummy", "--path", polish.SHADOWFALL,
             "res://tools/realm_layout.tscn", "--", screen.upper(), out], check=True)
    info = json.load(open(os.path.join(out, "layout.json"), encoding="utf-8"))
    polish.pygame.image.save(polish.legend([(k.replace("_", " "), tuple(c)) for k, c in info["legend"]]),
                             os.path.join(out, "legend.png"))
    words = os.path.join(out, "prompt.txt")
    if not os.path.exists(words):
        with open(words, "w", encoding="utf-8") as f:
            f.write(prompt(info, villages(screen, info.get("land", ""), levels)))
    with open(os.path.join(out, "README.txt"), "w", encoding="utf-8") as f:
        f.write(README.format(screen=screen.upper()))
    return out


def import_painting(screen, levels=LEVELS, godot=None, run_cmd=None):
    """The picture you saved in the folder -> painted.webp (960x544). Returns (ok, message)."""
    out = folder(screen, levels)
    pics = [os.path.join(out, f) for f in os.listdir(out) if f.lower().endswith(polish.IMAGE_TYPES)
            and f not in polish.OURS] if os.path.isdir(out) else []
    if not pics:
        return False, "No picture yet: save Gemini's painting in %s" % os.path.relpath(out, ROOT)
    ok, why = polish.shrink(max(pics, key=os.path.getmtime), os.path.join(out, "painted.webp"),
                            SCREEN_PX[0], SCREEN_PX[1], godot, run_cmd)
    return (True, "Painted! %s is in the game now (pixi run game)." % screen.upper()) if ok else (False, why)


def run(screen, style=STYLE, downloads=None, levels=LEVELS, run_cmd=subprocess.run, wait=gn.wait_download,
        ask=input, importer=import_painting):
    downloads = downloads or os.path.expanduser("~/Downloads")
    out = export(screen, levels, run_cmd)
    gc.copy_picture(os.path.join(out, "layout.png"), run_cmd)
    run_cmd(["open", gn.GEMINI_URL], check=False)
    print("1/3 Paste the map into Gemini (Cmd+V), then press Enter here. (q = quit)")
    if gc.ask_enter(ask):
        return 0
    if os.path.exists(style):
        gc.copy_picture(style, run_cmd)
        print("2/3 Paste the style picture (Cmd+V), then press Enter here.")
    else:
        print("2/3 Drag your style picture (the painted-realm mockup) into Gemini, then press Enter here.")
    if gc.ask_enter(ask):
        return 0
    since = time.time()
    before = gn.images_in(downloads)
    run_cmd(["pbcopy"], input=open(os.path.join(out, "prompt.txt"), "rb").read(), check=True)
    print("3/3 Paste the words and send; download the painting you like. (q = quit)")
    undo = gn.cbreak()
    try:
        got = wait(downloads, before, since)
    finally:
        undo()
    if got in ("n", "q"):
        print("Bye.")
        return 0
    os.replace(got, os.path.join(out, "from_gemini" + os.path.splitext(got)[1].lower()))
    ok, message = importer(screen, levels)
    print(message)
    return 0 if ok else 1


def main(argv, levels=LEVELS):
    opts = {}
    for key in ("--style", "--downloads"):
        if key in argv:
            i = argv.index(key)
            opts[key] = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
    screens = [a for a in argv if not a.startswith("--")]
    if len(screens) != 1 or not screens[0][:1].isalpha() or not screens[0][1:].isdigit():
        print(__doc__)
        return 1
    screen = screens[0].upper()
    if "--export" in argv:
        print("Made", os.path.relpath(export(screen, levels), ROOT))
        return 0
    if "--import" in argv:
        ok, message = import_painting(screen, levels)
        print(message)
        return 0 if ok else 1
    try:
        return run(screen, opts.get("--style", STYLE), opts.get("--downloads"), levels)
    except KeyboardInterrupt:
        print("\nBye.")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
