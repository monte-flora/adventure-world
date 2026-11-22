extends TestCase
## The exit, hazards, checkpoints, levers, digging, stones and monsters.

const T := 32.0


func _open(text: String) -> HeroSide:
	Scenes.goto("cave", {"text": text})
	await physics_frames(20)
	var h: HeroSide = Scenes.screen.hero
	h.set_meta("test", true)
	return h


func _walk(h: HeroSide, dir: float, frames: int) -> void:
	h.ix = dir
	await physics_frames(frames)
	h.ix = 0.0


func test_touching_E_returns_to_the_overworld() -> void:
	var h := await _open("theme: stone\n########\n#......#\n#S...E.#\n########")
	await _walk(h, 1.0, 40)
	check_eq(Scenes.current, "overworld", "touching E goes back to the overworld")


func test_E_in_a_real_cave() -> void:
	Scenes.goto("cave", {"file": "caves/01_the_easy_moss_cave.txt"})
	await physics_frames(5)
	var cave = Scenes.screen
	var e: Vector2i = cave.level.find("E")[0]
	cave.hero.position = cave.cell_rect(e).get_center()
	await physics_frames(3)
	check_eq(Scenes.current, "overworld", "back to the overworld from cave 01")
	check_eq(Scenes.args.get("from_cave"), "caves/01_the_easy_moss_cave.txt", "the overworld hears which cave")


func test_walking_out_the_left_gap_leaves() -> void:
	var h := await _open("theme: stone\n######\n.....#\n.S...#\n######")
	await _walk(h, -1.0, 40)
	check_eq(Scenes.current, "overworld", "the gap in the left wall is the way out")


func test_spikes_hurt_and_put_you_back() -> void:
	var h := await _open("theme: stone\n############\n#..........#\n#S...^^....#\n############")
	var safe := h.position
	await _walk(h, 1.0, 45)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "spikes cost 1 heart")
	await physics_frames(5)
	check(h.position.distance_to(safe) < 3.0 * T, "back on safe ground (%s)" % str(h.position))


func test_dying_wakes_you_at_the_checkpoint() -> void:
	var h := await _open("theme: stone\n############\n#..........#\n#S..C.^....#\n############")
	await _walk(h, 1.0, 25)
	var cave = Scenes.screen
	check(cave.checkpoint.x > 3.0 * T, "the lantern shrine is the new checkpoint")
	Game.hearts = 1
	h.iframes = 0
	cave.hurt_hero(h.position + Vector2(10, 0))
	check_eq(Game.hearts, Game.max_hearts, "wake with full hearts")
	check(h.position.distance_to(cave.checkpoint) < 1.0, "at the checkpoint")


func test_lever_opens_the_gates() -> void:
	var h := await _open("theme: stone\n##########\n#....G...#\n#S.L.G...#\n##########")
	var cave = Scenes.screen
	h.position.x = 3.0 * T
	await physics_frames(3)
	h.facing = 1
	h.attack_pressed = true
	await physics_frames(10)
	check_eq(cave.letter(Vector2i(5, 2)), ".", "R on the lever opens every gate")
	check(cave.map.get_cell_source_id(Vector2i(5, 1)) == -1, "the gate's bars are gone")


func test_dig_cracked_rock() -> void:
	var h := await _open("theme: stone\n#######\n#S.B..#\n#######")
	var cave = Scenes.screen
	await _walk(h, 1.0, 15)
	h.interact_pressed = true
	await physics_frames(2)
	check_eq(cave.letter(Vector2i(3, 1)), ".", "G digs the cracked rock in front")


func test_kingsfall_breaks_cracked_floor() -> void:
	var h := await _open("theme: stone\n#######\n#.....#\n#.....#\n#S....#\n##BB###\n#.....#\n#######")
	var cave = Scenes.screen
	h.position.x = 3.0 * T
	await physics_frames(3)
	h.jump_pressed = true
	h.jump_held = true
	await physics_frames(10)
	h.iy = 1.0
	h.dash_pressed = true
	await physics_frames(20)
	check_eq(cave.letter(Vector2i(2, 4)) + cave.letter(Vector2i(3, 4)), "BB", "no slam without the Crown of Ash")
	Game.take_stone("crown")
	h.iy = 0.0
	h.jump_pressed = true
	await physics_frames(10)
	h.iy = 1.0
	h.dash_pressed = true
	await physics_frames(20)
	h.iy = 0.0
	check(cave.letter(Vector2i(2, 4)) == "." or cave.letter(Vector2i(3, 4)) == ".", "Kingsfall breaks the cracked floor")


func test_stone_diamond_gives_its_ability() -> void:
	var h := await _open("theme: stone\nstone: Dawnstone\n#######\n#S.*..#\n#######")
	await _walk(h, 1.0, 20)
	check(Game.has_ability("dash"), "the diamond of a stone: cave gives its Light Stone")
	check(Game.flags.has("cave_done:"), "the cave is marked done")


func test_gems_and_chests_give_gold() -> void:
	var h := await _open("theme: stone\n#########\n#S.$.T..#\n#########")
	await _walk(h, 1.0, 30)
	check_eq(Game.gold, 1 + 10, "a gem and a chest")


func test_mushroom_bounces() -> void:
	var h := await _open("theme: stone\n#####\n#...#\n#...#\n#...#\n#...#\n#...#\n#...#\n#.S.#\n#...#\n##o##\n#####")
	var top := h.position.y
	for i in 60:
		await physics_frames(1)
		top = minf(top, h.position.y)
	check(top < 5.0 * T, "the mushroom throws you up (%.0f)" % top)


func test_sword_kills_a_zombie() -> void:
	var h := await _open("theme: stone\n##############\n#............#\n#S..z........#\n##############")
	var cave = Scenes.screen
	var z: CaveMonster = cave.monsters.get_child(0)
	z.set_physics_process(false)
	h.position.x = z.position.x - 40
	await physics_frames(2)
	h.facing = 1
	for i in 3:
		h.attack_pressed = true
		await physics_frames(16)
	check(not is_instance_valid(z), "3 hits kill a zombie")


func test_sword_reflects_arrows() -> void:
	var h := await _open("theme: stone\n##############\n#............#\n#S...........#\n##############")
	var cave = Scenes.screen
	cave.shoot(h.position + Vector2(80, 0), Vector2(-CaveMonster.ARROW_SPEED, 0), null)
	h.facing = 1
	await physics_frames(5)
	h.attack_pressed = true
	await physics_frames(12)
	check_eq(Game.hearts, Game.START_HEARTS, "the arrow is knocked back")


func test_crumbly_ledge_falls_and_returns() -> void:
	var h := await _open("theme: stone\n#######\n#.S...#\n#.--..#\n#.....#\n#######")
	var cave = Scenes.screen
	await physics_frames(CaveScene.CRUMBLE_SHAKE + 10)
	check(cave.letter(Vector2i(2, 2)) == ".", "the crumbly ledge falls")
	await physics_frames(CaveScene.CRUMBLE_BACK + 10)
	check(cave.letter(Vector2i(2, 2)) == "-", "and comes back")


func test_platforms_move() -> void:
	await _open("theme: stone\n##########\n#........#\n#.PPPPP..#\n#........#\n#.U......#\n#.U......#\n#S.......#\n##########")
	var cave = Scenes.screen
	var plats: Array = cave.props.get_children().filter(func(n): return n is CaveProps.Platform)
	check_eq(plats.size(), 2, "one P platform and one U platform")
	var before: Array = plats.map(func(p): return p.position)
	await physics_frames(30)
	check(plats[0].position.x > before[0].x, "P slides along its row")
	check(plats[1].b.y > plats[1].a.y and plats[1].position != before[1], "U rides up and down its column")


func test_secret_wall_lets_you_through() -> void:
	var h := await _open("theme: stone\n#########\n#S..F...#\n#########")
	await _walk(h, 1.0, 50)
	check(h.position.x > 5.0 * T, "walk right through F (%.0f)" % h.position.x)
