class_name Sigils
## Sigils: the old level-up powers, now charms you slot in at a lantern. Spec: gameplay §5.
## 3 slots, +1 at the 2nd, 4th and 6th Light Stone (6 at most). Each sigil costs slots.
## Owned and worn sigils live in Game.flags["sigils_owned"] and ["sigils_on"] (lists of ids).

const BASE_SLOTS := 3
const SLOT_AT_STONES := [2, 4, 6]
## id: [display name, slot cost, what it does]
const ALL := {
	"keen_edge":    ["Keen Edge",     3, "+1 sword damage"],
	"hardy":        ["Hardy",         2, "+1 heart"],
	"springstep":   ["Springstep",    1, "+0.5 tile jump"],
	"swiftfoot":    ["Swiftfoot",     1, "run 8.5 tiles a second"],
	"fortune":      ["Fortune",       1, "+50% gold and rings"],
	"forager":      ["Forager",       1, "Lumen fills 33% faster"],
	"sharpshooter": ["Sharpshooter",  2, "arrows +1 damage, +10 arrows"],
	"long_edge":    ["Long Edge",     2, "+25% sword reach"],
	"steady":       ["Steady",        1, "no recoil, half knockback"],
	"lantern_heart":["Lantern Heart", 2, "+1 Lumen charge"],
}
const RUN_SPEED := 6.0             # tiles a second without Swiftfoot (caves/ may use its own)
const SWIFT_RUN_SPEED := 8.5
const JUMP_BONUS := 0.5
const ARROW_BONUS_AMMO := 10


static func display_name(id: String) -> String:
	return ALL[id][0] if ALL.has(id) else id


static func cost(id: String) -> int:
	return ALL[id][1] if ALL.has(id) else 99


static func slots() -> int:
	var n := BASE_SLOTS
	for at in SLOT_AT_STONES:
		if Game.stones.size() >= at:
			n += 1
	return n


static func owned() -> Array:
	return Game.flags.get("sigils_owned", [])


static func worn() -> Array:
	return Game.flags.get("sigils_on", [])


static func used_slots() -> int:
	var n := 0
	for id in worn():
		n += cost(id)
	return n


static func is_on(id: String) -> bool:
	return id in worn()


## You found or bought a sigil. False if you had it already (or it isn't one).
static func gain(id: String) -> bool:
	if not ALL.has(id) or id in owned():
		return false
	var o := owned().duplicate()
	o.append(id)
	Game.flags["sigils_owned"] = o
	Game.changed.emit()
	return true


static func can_wear(id: String) -> bool:
	return id in owned() and not is_on(id) and used_slots() + cost(id) <= slots()


## Slot a sigil in (only at a lantern; the UI opens this screen there). False if it doesn't fit.
static func wear(id: String) -> bool:
	if not can_wear(id):
		return false
	var w := worn().duplicate()
	w.append(id)
	Game.flags["sigils_on"] = w
	_after_change()
	return true


static func remove(id: String) -> bool:
	if not is_on(id):
		return false
	var w := worn().duplicate()
	w.erase(id)
	Game.flags["sigils_on"] = w
	_after_change()
	return true


static func _after_change() -> void:
	Vitals.refresh_max_hearts()
	Game.flags["lumen"] = minf(Vitals.lumen(), Vitals.lumen_max())
	Game.changed.emit()


# ----- what the worn sigils do (other areas read these) ---------------------------------------

static func sword_bonus() -> int:
	return 1 if is_on("keen_edge") else 0

static func extra_hearts() -> int:
	return 1 if is_on("hardy") else 0

static func jump_bonus_tiles() -> float:
	return JUMP_BONUS if is_on("springstep") else 0.0

static func run_speed() -> float:
	return SWIFT_RUN_SPEED if is_on("swiftfoot") else RUN_SPEED

static func gold_multiplier() -> float:
	return 1.5 if is_on("fortune") else 1.0

static func lumen_rate() -> float:
	return 1.33 if is_on("forager") else 1.0

static func arrow_bonus_damage() -> int:
	return 1 if is_on("sharpshooter") else 0

static func arrow_bonus_ammo() -> int:
	return ARROW_BONUS_AMMO if is_on("sharpshooter") else 0

static func reach_multiplier() -> float:
	return 1.25 if is_on("long_edge") else 1.0

static func recoil() -> bool:
	return not is_on("steady")

static func knockback_multiplier() -> float:
	return 0.5 if is_on("steady") else 1.0

static func extra_lumen() -> float:
	return 1.0 if is_on("lantern_heart") else 0.0
