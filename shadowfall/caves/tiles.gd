class_name CaveTiles
## What every letter in a cave file means (levels/README.md, plus the teen letters C < > n).
## The cave scene (cave.gd) builds from this table, and tests check no cave uses a letter missing here.

## Letters drawn as a solid tile in the TileMap (atlas column = index in this string).
const SOLID := "#BMG%Io<>nF*s"     # F is drawn like rock but has no collision (secret wall); * s: ore you dig
const LEDGE := "=-"                # one-way: jump up through it; - crumbles
const HAZARD := "^A!~Jn"           # hurt you (A and J only while they are up / on)
const PICKUP := "$*sTu"
const MONSTER := "zkcx"
const MOVING := "PUR"              # platform tracks and swinging vines (nodes, not tiles)
const CLIMB := "HV"                # ladder, vine
const MARK := "SECL"               # start, exit, checkpoint (lantern shrine), lever
const DECOR := "iwf"               # torch, moonlit window, banner
const AIR := "."

## Every letter a cave may use.
static func known() -> String:
	return AIR + SOLID + LEDGE + HAZARD + PICKUP + MONSTER + MOVING + CLIMB + MARK + DECOR


## Letters in this level that no rule covers, sorted, no repeats.
static func unknown(lf: LevelFile) -> PackedStringArray:
	var k := known()
	var out := PackedStringArray()
	for row in lf.rows:
		for ch in row:
			if ch not in k and ch not in out:
				out.append(ch)
	out.sort()
	return out


static func is_solid(ch: String) -> bool:
	return ch != "" and ch in SOLID and ch != "F"


## Colours by theme: rock, cracked rock, accent (ledges, crystal glow), background.
const THEMES := {
	"stone": ["3b3546", "6d4a34", "a8703f", "17141d"],
	"moss": ["2f3b2c", "5d4a2c", "7fa35a", "121812"],
	"crystal": ["2c3550", "4d4a6e", "8fd0e0", "10131f"],
	"lava": ["3d2522", "6b3a24", "e0753a", "1a0d0b"],
	"shadow": ["2a2238", "4a3658", "9a7ad0", "0c0912"],
	"frost": ["3a4a5c", "5c6a7c", "cfe8f5", "121a22"],
	"castle": ["4a4650", "6a5a4a", "c9a66b", "16141a"],
}


static func palette(theme: String) -> Array:
	return THEMES.get(theme, THEMES["stone"])
