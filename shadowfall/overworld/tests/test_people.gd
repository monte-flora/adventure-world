extends TestCase
## People in the realm (rules/data/people.json): each stands on an open square in their land, with
## their own art; pacers pace; face one, press G and the talk runs in the dialogue box.

const TILE := LevelFile.TILE


func _open() -> Node:
	Scenes.goto("overworld")
	await physics_frames(2)
	return Scenes.screen


func _person(ow: Node, id: String) -> Person:
	for p in ow.people:
		if p.id == id:
			return p
	return null


## Clicks through a talk the way a player would, taking choice `pick` (-1: the last, "Farewell").
func _click_through(ow: Node, pick := -1) -> void:
	for i in 300:
		if not ow.talking:
			return
		if not ow.box.choices.is_empty():
			ow.box._pick(pick if pick >= 0 else ow.box.choices.size() - 1)
			pick = -1
		else:
			ow.box.advance()
		await frames(1)


func test_everyone_has_a_place_and_a_look() -> void:
	var ow = await _open()
	var all: Array = RulesData.get_file("people").get("people", [])
	check_eq(ow.people.size(), all.size(), "everyone in people.json is in the realm")
	var cells := {}
	for p in ow.people:
		check(ow._can_stand(p.cell), "%s stands on an open square" % p.id)
		check(not cells.has(p.cell), "%s has a square to themselves" % p.id)
		cells[p.cell] = true
		check(not ArtSheet.meta("people_" + str(p.data.look)).is_empty(), "%s has art (people_%s)" % [p.id, p.data.look])
		var land := str(p.data.place.land)
		check(Names.LAND.has(land), "%s's land %s is a realm land in rules/names.gd" % [p.id, land])
		check_eq(ow.world.land(p.cell), land, "%s stands in %s" % [p.id, land])
	for role in ["shop", "smith"]:
		check(all.any(func(d): return d.get("role", "") == role), "someone is the " + role)


func test_pacers_pace_and_stop_for_the_hero() -> void:
	var ow = await _open()
	var p: Person = _person(ow, "wren")
	check(p.paces(), "Wren paces")
	p.hero = null
	var x0: float = p.position.x
	await physics_frames(240)
	check(absf(p.position.x - x0) > 4.0, "and moves")
	p.hero = ow.hero
	ow.hero.drive = Vector2.ZERO
	ow.hero.position = p.position + Vector2(0, TILE)
	await physics_frames(2)
	var x1: float = p.position.x
	await physics_frames(30)
	check_eq(p.position.x, x1, "stands still with the hero beside them")


func test_face_maera_press_talk_and_she_speaks() -> void:
	var ow = await _open()
	var m: Person = _person(ow, "maera")
	ow.hero.place(m.cell + Vector2i(0, 1))
	ow.hero.facing = Vector2.UP
	check(ow.person_in_front() == m, "Maera is in front of the hero")
	ow.hero.facing = Vector2.DOWN
	check(ow.person_in_front() == null, "not with your back to her")
	ow.hero.facing = Vector2.UP
	var ev := InputEventAction.new()
	ev.action = "interact"
	ev.pressed = true
	ow._unhandled_input(ev)
	check(ow.talking and ow.box.is_open(), "the talk key opens the box")
	check_eq(ow.box.speaker_label.text, "Warden Maera", "with her name")
	check(Audio.ducked, "the music ducks")
	check_eq(m.facing, Vector2.DOWN, "she turns to the hero")
	await _click_through(ow)
	check(not ow.talking and not ow.box.is_open(), "the talk ends")
	check(not Audio.ducked, "the music comes back")
	check(Game.flags.has("met:maera"), "she remembers you")


func test_lines_change_with_the_gloom() -> void:
	var c := Conversation.new("bram")
	check(c.page().contains("Maera"), "first time: Bram's greeting")
	Game.flags["met:bram"] = true
	Game.gloom = 0.7
	check(Conversation.new("bram").page().contains("watch-fires"), "deep gloom: the watch-fires line")


func test_hound_shows_only_while_you_look_for_him() -> void:
	var ow = await _open()
	var ash: Person = _person(ow, "ash")
	check(not ash.visible, "Ash is hidden before the quest")
	Quests.start("lost_hound")
	ow._show_people()
	check(ash.visible, "and there once you look for him")


func test_the_pedlar_opens_her_shop_and_the_smith_his_forge() -> void:
	var ow = await _open()
	for who in [["tamsin", "ShopScreen"], ["garrick", "ForgeScreen"]]:
		var p: Person = _person(ow, who[0])
		ow.talk(p)
		await _click_through(ow, 0)
		check(ow.screen != null and ow.screen.get_script().get_global_name() == who[1], "%s opens the %s" % who)
		check(ow.talking and Audio.ducked, "everyone waits while it is open")
		ow.screen.close()
		await frames(2)
		check(not ow.talking and ow.screen == null, "and the walk goes on after")
