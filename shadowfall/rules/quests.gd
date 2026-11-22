class_name Quests
## Quests: the main quest (rules/data/main_quest.json, one Light Stone per chapter) and side quests
## (rules/data/quests.json). A step is done by talking (dialogue does advance_quest) or by its goal,
## which other areas report with Quests.event("cave:home"), event("defeat:woods:skeleton"),
## event("lookout:frost"), event("found:ash"), event("portal"), event("castle"), event("king").
## stones:N and has:ITEM:N goals are checked by themselves. Rewards: gold, arrows, sun_ore, shard,
## sigil; a chapter's 'relic' is the Light Stone it gives (Game.take_stone).
## State: Game.flags["quests"] = {id: step number, or -1 when done}, ["quest_kills"] = {id: n}.

const DONE := -1


static func _all() -> Dictionary:
	var out: Dictionary = RulesData.get_file("main_quest").get("quests", {}).duplicate()
	out.merge(RulesData.get_file("quests").get("quests", {}))
	return out


static func quest(id: String) -> Dictionary:
	return _all().get(id, {})


static func _state() -> Dictionary:
	if not Game.flags.has("quests"):
		Game.flags["quests"] = {}
	return Game.flags["quests"]


## "new", "active" or "done".
static func status(id: String) -> String:
	if not _state().has(id):
		return "new"
	return "done" if int(_state()[id]) == DONE else "active"


## The step you are on (0 is the first), or -1 if the quest isn't active.
static func step(id: String) -> int:
	return int(_state()[id]) if status(id) == "active" else -1


static func steps(id: String) -> Array:
	return quest(id).get("steps", [])


static func _step_dict(id: String, n: int) -> Dictionary:
	var s = steps(id)[n]
	return s if typeof(s) == TYPE_DICTIONARY else {"text": s}


static func step_text(id: String) -> String:
	return _step_dict(id, step(id)).get("text", "") if status(id) == "active" else ""


## Where the quest log's arrow points for the step you're on ("person:maera", "land:woods"...).
static func step_target(id: String) -> String:
	return _step_dict(id, step(id)).get("to", "") if status(id) == "active" else ""


static func active() -> Array:
	return _all().keys().filter(func(id): return status(id) == "active")


static func is_main(id: String) -> bool:
	return quest(id).get("main", false)


## Starts the main quest at the beginning of a new game.
static func start_main() -> void:
	start(RulesData.get_file("main_quest").get("first", ""))


static func start(id: String) -> bool:
	if quest(id).is_empty() or status(id) != "new":
		return false
	_state()[id] = 0
	Game.flags.get_or_add("quest_kills", {})[id] = 0
	Game.changed.emit()
	check_goals()
	return true


## The step you are on is done. The last step finishes the quest.
static func advance(id: String) -> bool:
	if status(id) != "active":
		return false
	var n := step(id) + 1
	if n >= steps(id).size():
		return finish(id)
	_state()[id] = n
	Game.flags.get_or_add("quest_kills", {})[id] = 0
	Game.changed.emit()
	check_goals()
	return true


## Ends a quest: its reward, its Light Stone, and the next chapter starts.
static func finish(id: String) -> bool:
	if status(id) != "active":
		return false
	_state()[id] = DONE
	var q := quest(id)
	give_reward(q.get("reward", {}))
	if q.has("relic"):
		Game.take_stone(q["relic"])
	Game.changed.emit()
	if q.has("next"):
		start(q["next"])
	check_goals()
	return true


## Gives a reward: {"gold": 20, "arrows": 5, "sun_ore": 1, "shard": 1, "sigil": "keen_edge"}.
static func give_reward(r: Dictionary) -> void:
	for k in r:
		if k == "sigil":
			Sigils.gain(r[k])
		else:
			Vitals.give(k, int(r[k]))


## Something happened in the world. Returns true if it moved a quest on.
static func event(what: String) -> bool:
	var moved := false
	for id in active():
		var goal: String = _step_dict(id, step(id)).get("goal", "")
		if goal == "":
			continue
		var g := goal.split(":")
		if g[0] == "defeat" and what.begins_with("defeat:"):
			var e := what.split(":")      # defeat:LAND:KIND
			if e.size() >= 3 and e[1] == g[1] and (g[2] == "any" or g[2] == e[2]):
				var kills: Dictionary = Game.flags.get_or_add("quest_kills", {})
				kills[id] = int(kills.get(id, 0)) + 1
				if int(kills[id]) >= int(g[3]):
					advance(id)
					moved = true
		elif goal == what:
			advance(id)
			moved = true
	return check_goals() or moved


## Steps whose goal is something you hold (stones:N, has:ITEM:N) are done as soon as it's true.
static func check_goals() -> bool:
	for id in active():
		var g: PackedStringArray = str(_step_dict(id, step(id)).get("goal", "")).split(":")
		if (g[0] == "stones" and Game.stones.size() >= int(g[1])) \
				or (g[0] == "has" and g.size() == 3 and Vitals.count(g[1]) >= int(g[2])):
			advance(id)
			return true
	return false


## Story cards: [[title, words, picture], ...] with {hero}, {relic} and {count} filled in.
static func story(which: String, words := {}) -> Array:
	var w := {"hero": Game.flags.get("hero_name", "Wanderer"), "count": Game.stones.size()}
	w.merge(words, true)
	var out := []
	for card in RulesData.get_file("main_quest").get("story", {}).get(which, []):
		out.append([card[0].format(w), card[1].format(w), card[2]])
	return out
