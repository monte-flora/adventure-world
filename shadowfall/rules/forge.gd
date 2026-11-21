class_name Forge
## The forge: the sword never breaks, it only gets stronger. Spec: gameplay §5.
## Tiers raise damage 2 -> 3 -> 4 -> 5 with sun ore and gold; Sunfang (7) is the last, forged from
## the 7 Light Stones at the castle gate. Each forge is 3 hammer strikes on the timing bar; any
## Miss and the metal cools (nothing spent). A Perfect forge (3 Perfect strikes) adds +5% crit.
## State: Game.flags["forge_tier"] (0..4) and ["crit"] (0.0..).

const DAMAGE := [2, 3, 4, 5, 7]                 # by tier; tier 4 is Sunfang
const TIER_NAME := ["Wanderer's Blade", "Tempered Blade", "Emberforged Blade", "Dawnsteel Blade", "Sunfang"]
const ORE_COST := [2, 4, 6]                     # to go from tier 0, 1, 2 to the next
const GOLD_COST := [30, 60, 100]
const SUNFANG_TIER := 4
const STRIKES := 3
const PERFECT_CRIT := 0.05
const PERFECT_WINDOW := 0.05                    # marker within 0.05 of the bar's centre: Perfect
const GOOD_WINDOW := 0.20                       # within 0.20: Good; farther: Miss


static func tier() -> int:
	return int(Game.flags.get("forge_tier", 0))


static func crit_chance() -> float:
	return float(Game.flags.get("crit", 0.0))


static func blade_name() -> String:
	return TIER_NAME[tier()]


## Sword damage now: the tier, plus the Keen Edge sigil.
static func sword_damage() -> int:
	return DAMAGE[tier()] + Sigils.sword_bonus()


## A strike on the timing bar. pos is where the marker stopped, 0..1 (0.5 is the centre).
static func grade(pos: float) -> String:
	var off := absf(pos - 0.5)
	if off <= PERFECT_WINDOW:
		return "perfect"
	if off <= GOOD_WINDOW:
		return "good"
	return "miss"


## Why you can't forge the next tier, or "" if you can.
static func problem() -> String:
	var t := tier()
	if t >= SUNFANG_TIER:
		return "This blade can be forged no further."
	if t == SUNFANG_TIER - 1:
		return "" if Game.stones.size() >= Game.STONES.size() else "Sunfang needs all seven Light Stones."
	if Vitals.count("sun_ore") < ORE_COST[t]:
		return "You need %d sun ore." % ORE_COST[t]
	if Game.gold < GOLD_COST[t]:
		return "You need %d gold." % GOLD_COST[t]
	return ""


## Forge with these 3 strike positions (from the timing bar). Returns "done", "perfect",
## "cooled" (a Miss: nothing spent) or "can't" (see problem()).
static func forge(strikes: Array) -> String:
	if problem() != "" or strikes.size() != STRIKES:
		return "can't"
	var grades := strikes.map(func(p): return grade(p))
	if "miss" in grades:
		return "cooled"
	var t := tier()
	if t < SUNFANG_TIER - 1:
		Vitals.take("sun_ore", ORE_COST[t])
		Vitals.take("gold", GOLD_COST[t])
	Game.flags["forge_tier"] = t + 1
	var perfect := grades.count("perfect") == STRIKES
	if perfect:
		Game.flags["crit"] = crit_chance() + PERFECT_CRIT
	Game.changed.emit()
	return "perfect" if perfect else "done"
