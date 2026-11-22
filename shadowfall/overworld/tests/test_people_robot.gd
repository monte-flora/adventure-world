extends TestCase
## The people robot: from home it walks to Tamsin the pedlar, talks, buys arrows in her shop, then
## walks to Garrick the smith and takes his quest; the pause JOURNEY lists it. Every key is a real
## input event (Input.parse_input_event), so the whole chain runs: overworld, dialogue box, shop.

const TILE := LevelFile.TILE


func _press(action: String) -> void:
	for down in [true, false]:
		var ev := InputEventAction.new()
		ev.action = action
		ev.pressed = down
		Input.parse_input_event(ev)
		await physics_frames(2)


## Walks the hero to a square beside p (by the map's own path), then faces p.
func _walk_to(ow: Node, p: Person) -> bool:
	var h: HeroTop = ow.hero
	for side in [Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP]:
		var goal: Vector2i = p.cell + side
		if not ow._can_stand(goal):
			continue
		var route: Array[Vector2i] = ow.world.path(h.cell(), goal)
		if route.is_empty() and h.cell() != goal:
			continue
		var i := 0
		for f in 4000:
			if i >= route.size():
				break
			var d := Vector2(route[i]) * TILE + Vector2.ONE * TILE / 2.0 - h.position
			if d.length() < 4.0:
				i += 1
				continue
			h.drive = d.normalized()
			await physics_frames(1)
		h.drive = Vector2(-side)                            # a tap toward them: turn to face them
		await physics_frames(1)
		h.drive = Vector2.ZERO
		await physics_frames(10)
		return ow.person_in_front() == p
	return false


## Presses through the talk: ↓ `downs` times on the first choice list, then confirm; the last
## choice (Farewell) after that. Stops when the talk is over or a shop or forge opens.
func _talk_through(ow: Node, downs: Array) -> void:
	for i in 200:
		if not ow.talking or ow.screen != null:
			return
		if not ow.box.choices.is_empty():
			var n: int = downs.pop_front() if not downs.is_empty() else ow.box.choices.size() - 1
			for k in n:
				await _press("move_down")
		await _press("interact")


func test_robot_walks_to_the_pedlar_buys_and_takes_the_smiths_quest() -> void:
	Scenes.goto("overworld")
	await physics_frames(3)
	var ow = Scenes.screen
	Game.gold = 50
	var tamsin: Person
	var garrick: Person
	for p in ow.people:
		if p.id == "tamsin":
			tamsin = p
		elif p.id == "garrick":
			garrick = p
	check(await _walk_to(ow, tamsin), "walked to Tamsin and faces her")
	await _press("interact")
	check(ow.talking, "G talks")
	await _talk_through(ow, [0])                          # "Show me your wares."
	check(ow.screen is ShopScreen, "her shop opens")
	if ow.screen is ShopScreen:
		check_eq(ow.screen.rows()[ow.screen.cursor].id, "arrows", "arrows first")
		await _press("jump")
		check_eq(Game.gold, 44, "bought arrows for 6 gold")
		check_eq(Vitals.count("arrows"), 5, "+5 arrows")
		await _press("pause")
	check(not ow.talking and ow.screen == null, "ESC leaves the shop and the walk goes on")
	check(not Scenes.is_paused(), "ESC in the shop doesn't pause")
	check(await _walk_to(ow, garrick), "walked to Garrick")
	await _press("interact")
	await _talk_through(ow, [1, 0])                       # "Any work?", then "I'll find it."
	check_eq(Quests.status("ore_for_the_forge"), "active", "the smith's quest is on")
	check(not ow.talking, "the talk is over")
	check(Quests.log_entries().any(func(e): return e.id == "ore_for_the_forge"), "the JOURNEY lists it")
