extends TestCase
## One test per cave letter (levels/README.md): the Hero really meets it, like in the pygame game
## (caves.py). The table of letter -> behaviour -> test is in caves/README.md. Some letters are
## tested in test_cave_toys.gd instead (named there in the table).

const T := 32.0


func _open(text: String) -> HeroSide:
	Scenes.goto("cave", {"text": text})
	await physics_frames(20)
	var h: HeroSide = Scenes.screen.hero
	h.set_meta("test", true)
	return h


func _hold(h: HeroSide, x: float, y: float, frames: int) -> void:
	h.ix = x
	h.iy = y
	await physics_frames(frames)
	h.ix = 0.0
	h.iy = 0.0


## Highest point (smallest y) over some frames.
func _top(h: HeroSide, frames: int) -> float:
	var top := h.position.y
	for i in frames:
		await physics_frames(1)
		top = minf(top, h.position.y)
	return top


func _cell(h: HeroSide) -> Vector2i:
	return Scenes.screen.cell_of(h.position)


func test_hash_rock_blocks_and_dot_air_is_open() -> void:
	var h := await _open("theme: stone\n#######\n#S..#.#\n#######")
	await _hold(h, 1.0, 0.0, 60)
	check(h.is_on_floor(), "# is floor")
	check(h.position.x < 4.0 * T, "# is a wall (%.0f)" % h.position.x)
	check(h.position.x > 3.0 * T - 2.0, ". is open: you walked to the wall")


func test_S_is_where_you_start() -> void:
	var h := await _open("theme: stone\n#######\n#...S.#\n#######")
	check_eq(_cell(h), Vector2i(4, 1), "the Hero starts on S")


func test_B_cracked_rock_breaks_to_a_sword_strike() -> void:
	var h := await _open("theme: stone\n#######\n#S.B..#\n#######")
	var cave = Scenes.screen
	await _hold(h, 1.0, 0.0, 15)
	check_eq(cave.letter(Vector2i(3, 1)), "B", "B is solid")
	h.facing = 1
	h.attack_pressed = true
	await physics_frames(10)
	check_eq(cave.letter(Vector2i(3, 1)), ".", "R breaks cracked rock like the pickaxe")


func test_s_sun_shard_ore_digs_out() -> void:
	var h := await _open("theme: shadow\n#######\n#S..s.#\n#######")
	var cave = Scenes.screen
	check(cave.map.get_cell_source_id(Vector2i(4, 1)) != -1, "Sun Shard ore is a solid tile")
	h.position.x = 3.5 * T
	h.facing = 1
	h.facing = 1
	h.interact_pressed = true
	await physics_frames(2)
	check_eq(cave.letter(Vector2i(4, 1)), ".", "dug out")
	check_eq(int(Game.flags.get("sun_ore", 0)), 1, "you hold a Sun Shard")


func test_equals_ledge_jump_up_through_and_stand() -> void:
	var h := await _open("theme: stone\n#####\n#...#\n#...#\n#.=.#\n#...#\n#.S.#\n#####")
	h.position.x = 2.5 * T
	h.jump_pressed = true
	h.jump_held = true
	await physics_frames(40)
	h.jump_held = false
	await physics_frames(40)
	check(h.is_on_floor() and h.position.y < 3.0 * T, "standing on the ledge (%.0f)" % h.position.y)


func test_A_spike_trap_hurts_only_when_up() -> void:
	var h := await _open("theme: stone\n#######\n#.....#\n#S.A..#\n#######")
	var cave = Scenes.screen
	cave.clock = 0                                     # down for TRAP_DOWN frames
	h.position = cave.cell_rect(Vector2i(3, 2)).get_center()
	await physics_frames(10)
	check_eq(Game.hearts, Game.START_HEARTS, "a trap that's down is safe")
	cave.clock = CaveScene.TRAP_DOWN
	h.position = cave.cell_rect(Vector2i(3, 2)).get_center()
	await physics_frames(3)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "up, it hurts")


func test_bang_fire_hurts() -> void:
	var h := await _open("theme: lava\n#######\n#.....#\n#S.!..#\n#######")
	await _hold(h, 1.0, 0.0, 30)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "fire costs a heart")


func test_tilde_lava_pool_hurts() -> void:
	var h := await _open("theme: lava\n#######\n#.....#\n#S....#\n###~###\n#######")
	h.position = Vector2(3.5 * T, 2.5 * T)
	await physics_frames(30)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "the lava costs a heart")
	check(h.position.y < 3.0 * T, "and puts you back on safe ground")


func test_lava_rises_waits_then_stops_below_the_exit() -> void:
	var h := await _open("theme: lava\nlava rises: yes\n########\n#......#\n#.E....#\n####=###\n#......#\n#......#\n#......#\n#S.*...#\n########")
	var cave = Scenes.screen
	await _hold(h, 1.0, 0.0, 20)
	check(cave.lava_top < INF, "the diamond wakes the lava")
	var y0: float = cave.lava_top
	await physics_frames(CaveScene.LAVA_WAIT - 20)
	check_eq(cave.lava_top, y0, "it waits 2 s first")
	cave.lava_top = 3.0 * T
	await physics_frames(60)
	check_eq(cave.lava_top, 3.0 * T, "it never rises above the row below E")


func test_o_mushroom_bounces_6_tiles() -> void:
	var h := await _open("theme: moss\n#####\n#...#\n#...#\n#...#\n#...#\n#...#\n#...#\n#...#\n#...#\n#...#\n#.S.#\n##o##\n#####")
	var y0 := 11.0 * T                                  # standing on the mushroom
	var top := await _top(h, 80)
	check(y0 - (top + HeroSide.SIZE.y / 2.0) > 5.8 * T, "about 6 tiles up (%.1f)" % ((y0 - top - 14.0) / T))


func test_M_geyser_throws_you_7_tiles_when_it_puffs() -> void:
	var h := await _open("theme: stone\n#####\n" + "#...#\n".repeat(11) + "#.S.#\n##M##\n#####")
	var cave = Scenes.screen
	cave.clock = 0
	await physics_frames(CaveScene.TRAP_DOWN - CaveScene.TRAP_WARN - 2)
	check(h.is_on_floor(), "nothing while it's quiet")
	await physics_frames(4)
	check(cave.about_to_go_off(), "it fizzles first")
	var y0 := h.position.y
	var top := await _top(h, 90)
	check((y0 - top) / T > 6.8, "WHOOSH: about 7 tiles up (%.1f)" % ((y0 - top) / T))


func test_H_ladder_climb_stand_on_top_and_climb_down() -> void:
	var h := await _open("theme: stone\n#######\n#.....#\n#.....#\n###H###\n#..H..#\n#..H..#\n#S.H..#\n#######")
	h.position.x = 3.5 * T
	await _hold(h, 0.0, -1.0, 80)
	await physics_frames(30)
	check(h.is_on_floor() and h.position.y < 3.0 * T, "climbed up and stands on the ladder's top (%.0f)" % h.position.y)
	await _hold(h, 0.0, 1.0, 30)
	check(h.position.y > 3.5 * T, "DOWN climbs back down through the top (%.0f)" % h.position.y)


func test_V_vine_grab_in_the_air() -> void:
	var h := await _open("theme: moss\n#######\n#..V..#\n#..V..#\n#..V..#\n#.....#\n#..S..#\n#######")
	h.jump_pressed = true
	h.jump_held = true
	await physics_frames(12)
	h.iy = -1.0
	await physics_frames(4)
	check_eq(h.state, HeroSide.CLIMB, "UP grabs the vine")
	await physics_frames(30)
	h.iy = 0.0
	check(h.position.y < 3.0 * T, "and climbs it (%.0f)" % h.position.y)


func test_percent_climbing_wall_up_climbs() -> void:
	var h := await _open("theme: moss\n#######\n#.....#\n#....%#\n#....%#\n#....%#\n#S...%#\n#######")
	await _hold(h, 1.0, -1.0, 80)
	check(h.position.y < 4.0 * T, "UP on %% climbs it (%.0f)" % h.position.y)


func test_I_ice_slides() -> void:
	var stops := []
	for floor_row in ["###########", "#IIIIIIIII#"]:
		var h := await _open("theme: frost\n###########\n#.........#\n#S........#\n" + floor_row + "\n###########")
		await _hold(h, 1.0, 0.0, 25)
		var x := h.position.x
		await physics_frames(40)
		stops.append(h.position.x - x)
	check(stops[1] > stops[0] + 0.5 * T, "you slide further on ice (%.0f vs %.0f)" % [stops[1], stops[0]])


func test_u_healing_spring_heals_then_refills() -> void:
	var h := await _open("theme: stone\n#######\n#S.u..#\n#######")
	Game.hearts = 1
	await _hold(h, 1.0, 0.0, 15)
	check_eq(Game.hearts, Game.max_hearts, "the spring heals you")
	Game.hearts = 1
	await physics_frames(10)
	check_eq(Game.hearts, 1, "empty until it fills up again")


func test_J_flame_jet_burns_its_block_and_2_above() -> void:
	var h := await _open("theme: lava\n#######\n#.....#\n#.....#\n#.....#\n#S.J..#\n#######")
	var cave = Scenes.screen
	cave.clock = 0
	h.position = Vector2(3.5 * T, 2.5 * T)              # 2 above the jet, in the air
	h.velocity = Vector2.ZERO
	await physics_frames(1)
	check_eq(Game.hearts, Game.START_HEARTS, "off: safe")
	cave.clock = CaveScene.TRAP_DOWN
	h.position = Vector2(3.5 * T, 2.5 * T)
	await physics_frames(1)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "on: it burns 2 blocks above")


func test_P_platform_carries_you() -> void:
	var h := await _open("theme: stone\n###########\n#.........#\n#.PPPPPP..#\n#.........#\n#.........#\n#S........#\n###########")
	var cave = Scenes.screen
	var plat = cave.props.get_child(0)
	h.position = plat.position + Vector2(T, -HeroSide.SIZE.y / 2.0 - 1)
	await physics_frames(10)
	var x0 := h.position.x
	await physics_frames(40)
	check(h.is_on_floor(), "standing on the platform")
	check(h.position.x > x0 + 1.0 * T, "it carries you along (%.0f px)" % (h.position.x - x0))


func test_U_platform_lifts_you() -> void:
	var h := await _open("theme: stone\n#######\n#.....#\n#.....#\n#..U..#\n#..U..#\n#..U..#\n#S.U..#\n#######")
	var cave = Scenes.screen
	var plat = cave.props.get_child(0)
	plat.t = 1.0
	plat.dir = -1.0
	plat.position = plat.b
	h.position = plat.position + Vector2(T / 2.0, -HeroSide.SIZE.y / 2.0 - 1)
	await physics_frames(5)
	var y0 := h.position.y
	await physics_frames(50)
	check(h.position.y < y0 - 1.5 * T, "it lifts you (%.0f px)" % (y0 - h.position.y))


func test_R_swinging_vine_grab_and_let_go() -> void:
	var h := await _open("theme: moss\n##########\n#...R....#\n#...R....#\n#...R....#\n#........#\n#........#\n#S.......#\n##########")
	h.position.x = 2.5 * T
	h.ix = 1.0
	h.jump_pressed = true
	h.jump_held = true
	await physics_frames(25)
	check_eq(h.state, HeroSide.ROPE, "jumping into the vine grabs it")
	await physics_frames(20)
	h.jump_pressed = true
	await physics_frames(2)
	check_eq(h.state, HeroSide.NORMAL, "SPACE lets go")


func test_monsters_zkcx_hurt_on_touch() -> void:
	for ch in "zkcx":
		Game.hearts = Game.START_HEARTS
		await _open("theme: stone\n##########\n#........#\n#S...." + ch + "..#\n##########")
		var cave = Scenes.screen
		var m = cave.monsters.get_child(0)
		check(m is CaveMonster, "%s is a monster" % ch)
		cave.hero.position = m.position
		await physics_frames(3)
		check_eq(Game.hearts, Game.START_HEARTS - 1, "%s hurts on touch" % ch)


func test_one_way_doors() -> void:
	var h := await _open("theme: stone\n##########\n#S..>...E#\n##########")
	var cave = Scenes.screen
	await _hold(h, 1.0, 0.0, 30)
	check_eq(cave.letter(Vector2i(4, 1)), ">", "> is shut from the left")
	check(h.position.x < 4.0 * T, "and solid")
	h.position.x = 6.5 * T
	await _hold(h, -1.0, 0.0, 20)
	check_eq(cave.letter(Vector2i(4, 1)), ".", "touched from the right: open for good")


func test_n_thorns_hurt_until_the_flare() -> void:
	var h := await _open("theme: shadow\n########\n#......#\n#S.n...#\n########")
	await _hold(h, 1.0, 0.0, 20)
	check_eq(Game.hearts, Game.START_HEARTS - 1, "shadow thorns hurt")
	Game.take_stone("sun")
	h.iframes = 0
	h.tool_pressed = true
	await physics_frames(2 + CaveJuice.STOP_HURT)       # the hurt hit-stop may still hold the Hero
	check_eq(Scenes.screen.letter(Vector2i(3, 2)), ".", "the flare burns them")


func test_decor_iwf_is_just_for_looks() -> void:
	var h := await _open("theme: castle\n#########\n#S.iwf..#\n#########")
	await _hold(h, 1.0, 0.0, 40)
	check(h.position.x > 6.0 * T, "walk past torch, window and banner (%.0f)" % h.position.x)
	check_eq(Game.hearts, Game.START_HEARTS, "they don't hurt")
