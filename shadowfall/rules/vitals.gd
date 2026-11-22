class_name Vitals
## Hearts, heart shards, the Lumen meter, gold, things you carry, and the Lost Light.
## Spec: docs/teen/gameplay/README.md section 5. Numbers a kid can change sit at the top.
## State lives in Game (hearts, max_hearts, gold) and Game.flags (the rest), so it saves.

const SHARDS_PER_HEART := 4        # 4 heart shards make 1 more heart
const BOSS_HIT := 2                # a boss hit takes 2 hearts, anything else 1
const LUMEN_MAX := 3.0             # the meter holds 3 heal charges
const LUMEN_PER_SWORD_HIT := 1.0 / 3.0   # 3 sword hits fill 1 charge
const LUMEN_PER_ARROW_HIT := 1.0 / 9.0   # an arrow hit fills a third of a sword hit
const ITEMS := ["arrows", "sun_ore", "shard"]


static func _items() -> Dictionary:
	if not Game.flags.has("items"):
		Game.flags["items"] = {}
	return Game.flags["items"]


## How many of a thing you carry: "gold", "arrows", "sun_ore" or "shard" (heart shards ever found).
static func count(item: String) -> int:
	if item == "gold":
		return Game.gold
	return int(_items().get(item, 0))


## Gives n of a thing. Heart shards grow your hearts; gold goes to Game.gold.
static func give(item: String, n: int) -> void:
	if n <= 0:
		return
	if item == "gold":
		Game.gold += n
	elif item in ITEMS:
		_items()[item] = count(item) + n
		if item == "shard":
			var before := Game.max_hearts
			refresh_max_hearts()
			Game.hearts += Game.max_hearts - before   # a new heart comes full
	Game.changed.emit()


## Takes n of a thing. False (and nothing taken) if you don't have that many. Shards can't be taken.
static func take(item: String, n: int) -> bool:
	if item == "shard" or count(item) < n:
		return false
	if item == "gold":
		Game.gold -= n
	else:
		_items()[item] = count(item) - n
	Game.changed.emit()
	return true


## Gold picked up from a foe or a chest (the Fortune sigil adds 50%). Returns what you got.
static func pick_up_gold(n: int) -> int:
	var got := int(round(n * Sigils.gold_multiplier()))
	give("gold", got)
	return got


## Max hearts = 5 + one per 4 shards (+1 with the Hardy sigil), never more than Game.MAX_HEARTS.
static func refresh_max_hearts() -> void:
	var m := Game.START_HEARTS + count("shard") / SHARDS_PER_HEART + Sigils.extra_hearts()
	Game.max_hearts = mini(m, Game.MAX_HEARTS)
	Game.hearts = mini(Game.hearts, Game.max_hearts)


static func shards_toward_next_heart() -> int:
	return count("shard") % SHARDS_PER_HEART


## A hit. Returns true if it was the last heart (then call die()).
static func hurt(boss := false) -> bool:
	var dmg := BOSS_HIT if boss else 1
	Game.hearts = maxi(0, Game.hearts - dmg)
	Game.changed.emit()
	return Game.hearts == 0


static func heal(n := 1) -> void:
	Game.hearts = mini(Game.max_hearts, Game.hearts + n)
	Game.changed.emit()


## At a lantern: every heart back.
static func heal_full() -> void:
	heal(Game.max_hearts)


# ----- Lumen: the heal meter ---------------------------------------------------------------

static func lumen() -> float:
	return float(Game.flags.get("lumen", 0.0))


## Charges the meter can hold: 3, +1 with the Lantern Heart sigil.
static func lumen_max() -> float:
	return LUMEN_MAX + Sigils.extra_lumen()


static func _set_lumen(v: float) -> void:
	Game.flags["lumen"] = clampf(v, 0.0, lumen_max())
	Game.changed.emit()


## Your blade hit something: the meter fills (the Forager sigil fills it 33% faster).
static func lumen_hit(arrow := false) -> void:
	var gain := LUMEN_PER_ARROW_HIT if arrow else LUMEN_PER_SWORD_HIT
	_set_lumen(lumen() + gain * Sigils.lumen_rate())


## Whole charges you can spend now.
static func lumen_charges() -> int:
	return int(floor(lumen() + 0.0001))


static func spend_lumen_charge() -> bool:
	if lumen_charges() < 1 or Game.hearts >= Game.max_hearts:
		return false
	_set_lumen(lumen() - 1.0)
	return true


static func refund_lumen_charge() -> void:
	_set_lumen(lumen() + 1.0)


# ----- death and the Lost Light ------------------------------------------------------------

## You fell. Your gold drops where you died as a Lost Light (any older one is gone for good),
## and your hearts come back for the respawn at the last checkpoint. `where` is whatever the
## caller needs to find the spot again, e.g. {"scene": "cave", "file": ..., "x": .., "y": ..}.
## Assist can turn the Lost Light off (Game.flags["assist_keep_gold"] = true): then gold stays.
static func die(where: Dictionary) -> void:
	if Game.flags.get("assist_keep_gold", false):
		Game.flags.erase("lost_light")
	elif Game.gold > 0:
		Game.flags["lost_light"] = {"gold": Game.gold, "where": where}
		Game.gold = 0
	else:
		Game.flags.erase("lost_light")
	Game.hearts = Game.max_hearts
	Game.changed.emit()


## The Lost Light waiting for you, or {} if there is none.
static func lost_light() -> Dictionary:
	return Game.flags.get("lost_light", {})


## You touched your Lost Light: the gold comes back. Returns how much.
static func recover_lost_light() -> int:
	var ll := lost_light()
	if ll.is_empty():
		return 0
	var g := int(ll.get("gold", 0))
	Game.flags.erase("lost_light")
	give("gold", g)
	return g
