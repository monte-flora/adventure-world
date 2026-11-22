extends TestCase
## Quests (main chain, goals, rewards) and dialogue (people.json talk nodes).


func _talk(id: String, picks := []) -> Conversation:
	var c := Conversation.new(id)
	var guard := 0
	while not c.done and guard < 50:
		guard += 1
		if not c.choices().is_empty():
			c.choose(picks.pop_front() if not picks.is_empty() else c.choices().size() - 1)
		else:
			c.next_page()
	return c


func test_main_quest_gives_the_dawnstone() -> void:
	Quests.start_main()
	check_eq(Quests.status("main_home"), "active", "starts")
	check(Quests.step_text("main_home").contains("Mine"), "step 1 is the Mine")
	check_eq(Quests.step_target("main_home"), "mine:home", "the arrow points at the Mine")
	check(not Quests.event("cave:woods"), "another land's cave doesn't count")
	check(Quests.event("cave:home"), "beat the cave")
	check_eq(Quests.step("main_home"), 1, "now go back")
	_talk("maera")
	check_eq(Quests.status("main_home"), "done", "Maera ends it")
	check(Game.has_ability("dash"), "the Dawnstone gives Wraithstep")
	check_eq(Game.gold, 20, "reward gold")
	check_eq(Quests.status("main_woods"), "active", "the next chapter starts")


func test_defeat_goals_count_kills() -> void:
	Quests.start("main_woods")
	Quests.advance("main_woods")
	for i in 3:
		Quests.event("defeat:woods:slime")
	Quests.event("defeat:lake:slime")
	check_eq(Quests.step("main_woods"), 1, "3 of 4 (the lake doesn't count)")
	Quests.event("defeat:woods:spider")
	check_eq(Quests.step("main_woods"), 2, "4: next step")
	Quests.start("main_ruins")
	Quests.advance("main_ruins")
	Quests.event("defeat:ruins:slime")
	check_eq(Quests.step("main_ruins"), 1, "only skeletons count")


func test_stone_goal_opens_by_itself() -> void:
	for s in ["dawn", "leaf", "tide", "crown"]:
		Game.take_stone(s)
	Quests.start("main_desert")
	check_eq(Quests.step("main_desert"), 0, "4 stones: gate shut")
	Game.take_stone("frost")
	Quests.check_goals()
	check_eq(Quests.step("main_desert"), 1, "5 stones: through")


func test_whole_main_quest_reaches_the_king() -> void:
	Quests.start_main()
	var guard := 0
	while Quests.status("main_gate") != "done" and guard < 200:
		guard += 1
		for id in Quests.active():
			var g: String = Quests._step_dict(id, Quests.step(id)).get("goal", "")
			if g.begins_with("defeat:"):
				var p := g.split(":")
				Quests.event("defeat:%s:%s" % [p[1], "slime" if p[2] == "any" else p[2]])
			elif g.begins_with("stones:"):
				Quests.check_goals()
			elif g != "":
				Quests.event(g)
			else:
				_talk(Quests.step_target(id).trim_prefix("person:"))
	check_eq(Quests.status("main_gate"), "done", "the Shadow King falls")
	check_eq(Game.stones.size(), 7, "all 7 stones from the quest")


func test_side_quest_by_dialogue() -> void:
	var c := Conversation.new("wren")
	check(c.page().contains("hound"), "Wren asks")
	c.next_page()
	check_eq(c.choice_texts().size(), 2, "2 choices")
	c.choose(0)
	check_eq(Quests.status("lost_hound"), "active", "accepted")
	check(Conversation.visible("ash"), "now the hound shows")
	_talk("ash")
	check_eq(Quests.step("lost_hound"), 1, "found him")
	check(not Conversation.visible("ash"), "and he's gone home")
	_talk("wren")
	check_eq(Quests.status("lost_hound"), "done", "done")
	check_eq(Vitals.count("shard"), 1, "a heart shard")


func test_smith_opens_the_forge_and_takes_ore() -> void:
	var c := _talk("garrick", [1, 0])
	check_eq(Quests.status("ore_for_the_forge"), "active", "took the work")
	Vitals.give("sun_ore", 3)
	check_eq(Quests.step("ore_for_the_forge"), 0, "giving alone isn't an event")
	Quests.check_goals()
	_talk("garrick")
	check_eq(Quests.status("ore_for_the_forge"), "done", "ore handed over")
	check_eq(Vitals.count("sun_ore"), 0, "ore taken")
	check(Sigils.owned().has("keen_edge"), "a sigil")
	c = Conversation.new("garrick")
	c.next_page()
	c.choose(0)
	check(c.done and c.then == "forge", "the forge opens")


func test_first_time_and_names_fill_in() -> void:
	Game.flags["hero_name"] = "Kael"
	var c := Conversation.new("maera")
	check(c.page().contains("Kael"), "{hero} filled in")
	_talk("maera")
	check(not Conversation.new("maera").first_time, "only the first time")
	check_eq(Conversation.new("tamsin").name(), "Tamsin the Pedlar", "name")


func test_every_person_talks() -> void:
	Quests.start_main()
	for p in RulesData.get_file("people").get("people", []):
		var c := _talk(p["id"])
		check(c.done, p["id"] + " finishes talking")
		for node in p["talk"].values():
			for v in node:
				for cond in v.get("if", []):
					Conversation.check_condition(cond, false)
