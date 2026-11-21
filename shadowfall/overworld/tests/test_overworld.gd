extends TestCase
## The realm loads from levels/world/, the hero walks from home to a Mine and its cave opens,
## ability gates stay shut until Game.has_ability(), waystones light, Nightfall mirrors the centre.

const TILE := LevelFile.TILE


func _open(args := {}) -> Node:
	Scenes.goto("overworld", args)
	await physics_frames(2)
	return Scenes.screen


## Walks the hero along a path of squares by steering it like a player would.
func _walk(ow: Node, route: Array[Vector2i], max_frames := 3000) -> void:
	var h: HeroTop = ow.hero
	var i := 0
	for f in max_frames:
		if not is_instance_valid(h) or Scenes.current != "overworld" or i >= route.size():
			break
		var goal := Vector2(route[i]) * TILE + Vector2.ONE * TILE / 2.0
		var d := goal - h.position
		if d.length() < 4.0:
			i += 1
			continue
		h.drive = d.normalized()
		await physics_frames(1)


func test_every_land_loads() -> void:
	var files := Paths.level_files("world")
	check(files.size() >= 8, "8 or more land files (%d)" % files.size())
	for f in files:
		var lf := LevelFile.load_file(Paths.level(f))
		check(lf.error == "", "%s loads: %s" % [f, lf.error])
		check(lf.setting("at") != "", f + " has an at: line")
	var w := WorldMap.load_realm()
	check(w.errors.is_empty(), "lands stitch cleanly: " + ", ".join(w.errors))
	check_eq(w.lands.size(), files.size(), "every file is a land")
	for id in w.lands:
		check(w.land_name(id) != "", "land %s has a name" % id)
	check(w.at(w.home) == "H", "home is on a house")
	check(w.mines.size() >= 12, "the Mines are found (%d)" % w.mines.size())
	for m in w.mines:
		check(w.cave_of.has(m), "Mine %s plays a cave" % m)
	check(WorldMap.screen_of(Vector2i(31, 18)) == Vector2i(1, 1), "squares map to screens of 30 × 17")


func test_overworld_opens_at_home() -> void:
	var ow = await _open()
	check(ow.world != null and ow.map.get_used_cells().size() > 1000, "tiles are placed")
	check_eq(ow.hero.cell(), ow.world.home, "the hero starts at home")
	check(ow.cam.limit_right == ow.world.size.x * TILE, "the camera stays on the map")
	check(ow.monsters.size() > 0, "monsters roam the map")


func test_walk_home_to_a_mine_opens_its_cave() -> void:
	var ow = await _open()
	for m in ow.monsters:                     # this test is about walking, not fighting
		m.queue_free()
	ow.monsters.clear()
	var w: WorldMap = ow.world
	var route: Array[Vector2i] = []
	var mine := Vector2i(-1, -1)
	for m in w.mines:                         # nearest home first: the first reachable one
		route = w.path(w.home, m)
		if route.size() > 0:
			mine = m
			break
	check(route.size() > 0, "a Mine can be walked to from home")
	var opened := []
	Scenes.switched.connect(func(n): opened.append([n, Scenes.args.duplicate()]), CONNECT_ONE_SHOT)
	await _walk(ow, route)
	check(opened.size() == 1 and opened[0][0] == "cave", "walking onto the Mine opens the cave: %s" % [opened])
	if opened.size() == 1:
		check_eq(opened[0][1].get("file"), w.cave_of[mine], "it plays that Mine's cave")


func test_back_from_a_cave_stands_beside_the_mine() -> void:
	var w := WorldMap.load_realm()
	var ow = await _open({"at": w.mines[0]})
	check_eq(Scenes.current, "overworld", "doesn't walk straight back in")
	check(ow.hero.cell().distance_to(w.mines[0]) < 1.5, "next to the Mine")


func _gate_world(letter: String) -> WorldMap:
	var w := WorldMap.new()
	w.stitch({"world/01_test.txt": "at: 0 0\nhome: 1 1\nGGGGG\nGH%sGG\nGGGGG" % letter})
	return w


func test_gates_stay_shut_until_the_ability() -> void:
	for pair in [["Y", "climb", "leaf"], ["O", "pound", "crown"], ["K", "flare", "sun"], ["W", "swim", "tide"]]:
		Game.reset()
		var w := _gate_world(pair[0])
		check(not w.walkable(Vector2i(2, 1)), "%s is shut without %s" % pair.slice(0, 2))
		Game.take_stone(pair[2])
		check(Game.has_ability(pair[1]) and w.walkable(Vector2i(2, 1)), "%s opens with %s" % pair.slice(0, 2))
	Game.reset()
	var g := WorldMap.new()
	g.stitch({"world/01_t.txt": "at: 0 0\nhome: 1 1\ngate: Ivy Cliff 1 2 climb\ngate: Old Gate 1 3 2\nGGGGG\nGHXXG\nGGGGG"})
	check(not g.walkable(Vector2i(2, 1)) and not g.walkable(Vector2i(3, 1)), "gate: lines start shut")
	Game.take_stone("leaf")
	check(g.walkable(Vector2i(2, 1)), "an ability gate: line opens with it")
	check(not g.walkable(Vector2i(3, 1)), "a 2-stone gate needs 2 stones")
	Game.take_stone("dawn")
	check(g.walkable(Vector2i(3, 1)), "and opens at 2")


func test_hero_is_blocked_by_a_shut_gate() -> void:
	var ow = await _open()
	var w := _gate_world("Y")
	ow.world = w
	ow.hero.world = w
	ow.hero.place(Vector2i(1, 1))
	for m in ow.monsters:
		m.queue_free()
	ow.monsters.clear()
	ow.hero.drive = Vector2.RIGHT
	await physics_frames(40)
	check(ow.hero.position.x < 2 * TILE, "stops at the ivy cliff (x %.0f)" % ow.hero.position.x)
	Game.take_stone("leaf")
	await physics_frames(20)
	check(ow.hero.position.x > 2 * TILE, "climbs it with Ironclaw (x %.0f)" % ow.hero.position.x)


func test_walk_speed_and_roll() -> void:
	var ow = await _open()
	var w := WorldMap.new()
	var row := "G".repeat(40)
	var rows := PackedStringArray()
	for i in 12:
		rows.append(row)
	w.stitch({"world/01_t.txt": "at: 0 0\nhome: 1 1\n" + "\n".join(rows)})
	ow.world = w
	ow.hero.world = w
	ow.hero.place(Vector2i(1, 1))
	for m in ow.monsters:
		m.queue_free()
	ow.monsters.clear()
	var h: HeroTop = ow.hero
	h.drive = Vector2.RIGHT
	await physics_frames(10)
	var x0 := h.position.x
	await physics_frames(60)
	var sq := (h.position.x - x0) / TILE
	check(absf(sq - 5.5) < 0.2, "walks 5.5 squares/s (%.2f)" % sq)
	h.drive = Vector2(1, 1)
	await physics_frames(30)
	check(absf(h.velocity.length() - HeroTop.WALK) < 1.0, "diagonals are normalized")
	check(not h.roll(), "no roll without Wraithstep")
	Game.take_stone("dawn")
	h.drive = Vector2.ZERO
	h.facing = Vector2.RIGHT
	h.velocity = Vector2.ZERO
	var rx := h.position.x
	check(h.roll(), "rolls with Wraithstep")
	await physics_frames(HeroTop.ROLL_FRAMES)
	var rolled := (h.position.x - rx) / TILE
	check(absf(rolled - 3.5) < 0.3, "a roll covers 3.5 squares (%.2f)" % rolled)


func test_waystone_lights_and_heals() -> void:
	var ow = await _open()
	var w: WorldMap = ow.world
	check(w.waystones.size() >= 7, "a waystone per land (%d)" % w.waystones.size())
	var keys: Array = w.waystones.keys()
	Game.hearts = 1
	ow.light_waystone(keys[0])
	check(ow.waystone_lit(keys[0]) and Game.hearts == Game.max_hearts, "lighting heals fully")
	ow.light_waystone(keys[1])
	ow.hero.place(keys[0])
	check(ow.travel_from(keys[0]) and ow.hero.cell() != Vector2i(keys[0]), "travels between lit waystones")


func test_monster_hurts_and_sword_kills() -> void:
	var ow = await _open()
	var h: HeroTop = ow.hero
	var m: MapMonster = ow.monsters[0]
	for other in ow.monsters:
		if other != m:
			other.queue_free()
	ow.monsters.clear()
	ow.monsters.append(m)
	m.position = h.position + Vector2(8, 0)
	await physics_frames(2)
	check(Game.hearts == Game.START_HEARTS - 1, "a touch costs a heart (%d)" % Game.hearts)
	check(h.invulnerable(), "then i-frames")
	await physics_frames(20)                  # the knockback ends
	m.position = h.position + Vector2(30, 0)
	m.hp = 2
	h.facing = Vector2.RIGHT
	h.attack()
	await physics_frames(12)
	check(not is_instance_valid(m) or m.hp <= 0, "one sword hit kills a slime")


func test_nightfall_mirrors_the_centre() -> void:
	var light := WorldMap.load_realm()
	var night := WorldMap.load_nightfall()
	check_eq(night.size, WorldMap.MIRROR_SIZE * WorldMap.SCREEN, "3 × 3 screens")
	var from := WorldMap.MIRROR_FROM * WorldMap.SCREEN
	var same := 0
	var total := 0
	for p in night.cells:
		if light.cells.has(from + p):
			total += 1
			if night.at(p) == light.at(from + p) or night.at(p) == "G":
				same += 1
	check(total > 0 and same == total, "same footprint as the centre screens")
	check(night.mines.size() <= 3, "at most 3 shadow caves")
	for m in night.mines:
		check(night.cave_of[m].begins_with("shadow/"), "Nightfall Mines play shadow caves")
	check(night.land_name("nightfall") != "", "it has a name")
	var ow = await _open({"realm": "nightfall"})
	check(ow.world.nightfall and ow.map.get_used_cells().size() > 0, "the Umbral Reach opens")
