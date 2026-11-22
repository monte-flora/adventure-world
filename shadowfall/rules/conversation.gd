class_name Conversation
extends RefCounted
## One talk with one person from rules/data/people.json (the format phase2/dialogue.py uses).
## The UI shows page(), then calls next_page(); on the last page it shows choices() and calls
## choose(i). When done is true the talk is over; `then` says what opens after ("shop", "forge").
##   var c := Conversation.new("maera")
## Conditions: first_time, quest_new|quest_active|quest_done:ID, quest_step:ID:N, has:ITEM:N,
## stones:N, flag:NAME, not:<condition>. Effects: start_quest|advance_quest|finish_quest:ID,
## give|take:ITEM:N, set_flag:NAME, open:shop|forge, event:<quest event>.

var person: Dictionary
var nodes: Dictionary
var node: Dictionary = {}
var page_i := 0
var done := false
var then := ""
var first_time := false


func _init(person_id: String) -> void:
	person = RulesData.person(person_id)
	nodes = person.get("talk", {})
	first_time = not Game.flags.has("met:" + person_id)
	go("start")


## False while a person's 'show_if' isn't true yet (the hound appears only while you look for him).
static func visible(person_id: String) -> bool:
	var p := RulesData.person(person_id)
	return p.get("show_if", []).all(func(cond): return check_condition(cond, false))


func name() -> String:
	return person.get("name", "")


func go(node_name: String) -> void:
	node = pick(node_name)
	page_i = 0
	if node.is_empty():
		end()
		return
	for e in node.get("do", []):
		run(e)
	if node.get("say", []).is_empty():
		_after_last_page()


## The first variant of a node whose "if" all pass ({} if none).
func pick(node_name: String) -> Dictionary:
	var n = nodes.get(node_name)
	var variants: Array = n if typeof(n) == TYPE_ARRAY else ([n] if n else [])
	for v in variants:
		if passes(v.get("if", [])):
			return v
	return {}


func passes(conds) -> bool:
	if typeof(conds) == TYPE_STRING:
		conds = [conds]
	for c in conds:
		if not check_condition(c, first_time):
			return false
	return true


func page() -> String:
	var pages: Array = node.get("say", [])
	return fill(pages[page_i]) if page_i < pages.size() else ""


func is_last_page() -> bool:
	return page_i >= node.get("say", []).size() - 1


## The choices you can pick now (only on the last page).
func choices() -> Array:
	if not is_last_page() or done:
		return []
	return node.get("choices", []).filter(func(c): return passes(c.get("if", [])))


func choice_texts() -> PackedStringArray:
	var out := PackedStringArray()
	for c in choices():
		out.append(fill(c["text"]))
	return out


func next_page() -> void:
	if done:
		return
	if not is_last_page():
		page_i += 1
	elif node.get("choices", []).is_empty() or choices().is_empty():
		_after_last_page()


func choose(i: int) -> void:
	var cs := choices()
	if i < 0 or i >= cs.size():
		return
	for e in cs[i].get("do", []):
		run(e)
	if cs[i].has("go") and not done:
		go(cs[i]["go"])
	else:
		end()


func _after_last_page() -> void:
	if node.has("next"):
		go(node["next"])
	else:
		end()


func end() -> void:
	done = true
	Game.flags["met:" + person.get("id", "")] = true


func fill(text: String) -> String:
	return text.format({"hero": Game.flags.get("hero_name", "Wanderer"), "gold": Game.gold,
		"stones": Game.stones.size(), "person": name()})


static func check_condition(cond: String, first: bool) -> bool:
	if cond.begins_with("not:"):
		return not check_condition(cond.substr(4), first)
	var a := cond.split(":")
	match a[0]:
		"first_time": return first
		"quest_new": return Quests.status(a[1]) == "new"
		"quest_active": return Quests.status(a[1]) == "active"
		"quest_done": return Quests.status(a[1]) == "done"
		"quest_step": return Quests.step(a[1]) == int(a[2])
		"has": return Vitals.count(a[1]) >= int(a[2])
		"stones": return Game.stones.size() >= int(a[1])
		"flag": return Game.flags.has(cond.substr(5))
	push_warning("unknown condition: " + cond)
	return false


func run(effect: String) -> void:
	var a := effect.split(":")
	match a[0]:
		"start_quest": Quests.start(a[1])
		"advance_quest": Quests.advance(a[1])
		"finish_quest": Quests.finish(a[1])
		"give": Quests.give_reward({a[1]: a[2] if a[1] == "sigil" else int(a[2])})
		"take": Vitals.take(a[1], int(a[2]))
		"set_flag": Game.flags[effect.substr(9)] = true
		"open": then = a[1]
		"event": Quests.event(effect.substr(6))
		_: push_warning("unknown effect: " + effect)
