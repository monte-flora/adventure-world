extends Node
## The game's memory (autoload `Game`): Light Stones, abilities, gloom, hearts, gold, and save/load.
## Owned by core (B0). Other areas read it and call its functions; ask before adding fields.
## Cut on purpose (user, 2026-11-21): XP, lives, food and sword wear.

signal changed                          # anything below changed
signal stone_taken(stone: String)

## The 7 Light Stones in story order, and the ability each one gives (ids only; names live in
## rules/names.gd so they can be renamed without touching code). The ability works in both views.
const STONES := ["dawn", "leaf", "crown", "tide", "frost", "sun", "moon"]
const ABILITY_OF := {
	"dawn": "dash",         # dash in caves, roll on the map: crosses gaps
	"leaf": "climb",        # wall jump on any wall, climbs ivy cliffs (% tiles)
	"crown": "pound",       # heavy slam: breaks cracked rock (B) and rubble
	"tide": "swim",         # swim and sail: open water
	"frost": "double_jump", # a second jump in the air
	"sun": "flare",         # the lantern flares: lights the pitch dark, burns shadow thorns
	"moon": "truesight",    # shows secret walls (F) and hidden caves
}

## Gloom (the darkening world), from docs/teen/gameplay/README.md section 7: it grows to 1.0 in
## 90 minutes of play; each stone pushes it back 0.25 and lowers the cap by 0.1.
const GLOOM_MINUTES := 90.0
const GLOOM_PUSH := 0.25
const GLOOM_CAP_DROP := 0.1
const START_HEARTS := 5
const MAX_HEARTS := 10
const SAVE_PATH := "user://shadowfall_save.json"
const SAVE_VERSION := 1

var stones: Array[String] = []          # Light Stones taken, in the order taken
var gloom := 0.0                        # 0 (bright) .. 1 (full dark)
var hearts := START_HEARTS
var max_hearts := START_HEARTS
var gold := 0
var flags := {}                         # free-form story/quest flags: id -> value (rules/ owns their meaning)
var play_seconds := 0.0
var gloom_running := false              # true while the clock should darken the world (map and caves)


func reset() -> void:
	stones.clear()
	gloom = 0.0
	hearts = START_HEARTS
	max_hearts = START_HEARTS
	gold = 0
	flags.clear()
	play_seconds = 0.0
	gloom_running = false
	changed.emit()


func _process(delta: float) -> void:
	if gloom_running and not get_tree().paused:
		tick(delta)


## Moves the clock on: play time and gloom. Tests call this directly.
func tick(seconds: float) -> void:
	play_seconds += seconds
	gloom = minf(gloom_cap(), gloom + seconds / (GLOOM_MINUTES * 60.0))


func gloom_cap() -> float:
	return maxf(0.0, 1.0 - GLOOM_CAP_DROP * stones.size())


## The art's 4 darkening stages (docs/teen/art/README.md): 0, 1, 2, 3.
func gloom_stage() -> int:
	return clampi(int(floor(gloom * 3.0 + 0.0001)), 0, 3)


func has_ability(ability: String) -> bool:
	for s in stones:
		if ABILITY_OF[s] == ability:
			return true
	return false


func abilities() -> Array[String]:
	var out: Array[String] = []
	for s in stones:
		out.append(ABILITY_OF[s])
	return out


## Takes a Light Stone. Returns false if it was taken already (or isn't a stone).
func take_stone(stone: String) -> bool:
	if stone not in STONES or stone in stones:
		return false
	stones.append(stone)
	gloom = clampf(gloom - GLOOM_PUSH, 0.0, gloom_cap())
	stone_taken.emit(stone)
	changed.emit()
	return true


func to_dict() -> Dictionary:
	return {"version": SAVE_VERSION, "stones": stones.duplicate(), "gloom": gloom, "hearts": hearts,
		"max_hearts": max_hearts, "gold": gold, "flags": flags.duplicate(true), "play_seconds": play_seconds}


func from_dict(d: Dictionary) -> void:
	reset()
	for s in d.get("stones", []):
		if s in STONES and s not in stones:
			stones.append(s)
	gloom = clampf(float(d.get("gloom", 0.0)), 0.0, gloom_cap())
	max_hearts = clampi(int(d.get("max_hearts", START_HEARTS)), 1, MAX_HEARTS)
	hearts = clampi(int(d.get("hearts", max_hearts)), 1, max_hearts)
	gold = maxi(0, int(d.get("gold", 0)))
	flags = d.get("flags", {})
	play_seconds = float(d.get("play_seconds", 0.0))
	changed.emit()


func save(path := SAVE_PATH) -> bool:
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(to_dict(), "\t"))
	return true


## Loads a save. Returns false (and changes nothing) if there is none or it can't be read.
func load_save(path := SAVE_PATH) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(d) != TYPE_DICTIONARY:
		return false
	from_dict(d)
	return true


func has_save(path := SAVE_PATH) -> bool:
	return FileAccess.file_exists(path)
