class_name Castle
## The road to the throne: the 5 castle levels in levels/castle/ (gate first, battlements last),
## Sunfang forged from the 7 Light Stones at the gate, then the Shadow King.
##   Scenes.goto("boss", {"castle": 1})   the gate (levels/castle/1_...)
##   Scenes.goto("boss")                  the throne room

const LEVELS := 5
const SUNFANG_DAMAGE := 7               # the last sword tier (gameplay §5)


## levels/castle/ files in order, as paths inside levels/ ("castle/1_the_gate_and_the_lava_moat.txt").
static func files() -> PackedStringArray:
	return Paths.level_files("castle")


static func file(level: int) -> String:
	var all := files()
	return all[clampi(level, 1, all.size()) - 1]


## Where the door of castle level n leads: the next level, or the throne after the last.
static func next(level: int) -> Dictionary:
	return {"castle": level + 1} if level < files().size() else {}


## The 7 stones melt into Sunfang at the castle gate. Returns true the first time.
static func forge_sunfang() -> bool:
	if Game.flags.get("sunfang", false):
		return false
	Game.flags["sunfang"] = true
	Game.changed.emit()
	return true


## Sunfang's damage, +1 for each light shard found in the castle (gameplay §6).
static func sword_damage() -> int:
	return SUNFANG_DAMAGE + int(Game.flags.get("light_shards", 0))


## A display name from rules/names.gd (B4 owns the names). `key` is a constant there: a String,
## or a Dictionary looked up by `id`. Falls back when B4 hasn't added it yet.
static func display(key: String, id := "", fallback := "") -> String:
	var script: GDScript = load("res://rules/names.gd")
	var names := script.get_script_constant_map() if script else {}
	if not names.has(key):
		return fallback
	var v = names[key]
	if typeof(v) == TYPE_DICTIONARY:
		return v.get(id, fallback)
	return str(v)
