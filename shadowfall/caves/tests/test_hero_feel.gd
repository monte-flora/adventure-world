extends TestCase
## The side-view feel numbers (docs/teen/gameplay/README.md section 4): jump height, short hop,
## coyote time, jump buffer, pogo, and dash / wall jump / double jump only once you have them.

const T := 32.0
const ROOM := """theme: stone
##############################
#............................#
#............................#
#............................#
#............................#
#............................#
#............................#
#............................#
#............................#
#............................#
#S...........................#
##############################"""
## A step 3 tiles high, then open floor: for coyote time.
const STEP := """theme: stone
##############################
#............................#
#............................#
#............................#
#............................#
#............................#
#S...........................#
#####........................#
#####........................#
#####........................#
##############################"""
## Start high in the air: the Hero drops straight to the floor (jump buffer).
const DROP := """theme: stone
##########
#........#
#...S....#
#........#
#........#
#........#
#........#
#........#
#........#
#........#
##########"""
const WALLS := """theme: stone
##############################
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#.......%......#.............#
#S......%.....S#.............#
##############################"""


func _open(text: String) -> HeroSide:
	Scenes.goto("cave", {"text": text})
	await physics_frames(20)
	var h: HeroSide = Scenes.screen.hero
	h.set_meta("test", true)
	return h


## Frames until the Hero is back on the floor; returns the highest rise in tiles.
func _rise(h: HeroSide, hold_frames: int) -> float:
	var y0 := h.position.y
	var top := y0
	h.jump_pressed = true
	h.jump_held = true
	for i in 120:
		if i == hold_frames:
			h.jump_held = false
		await physics_frames(1)
		top = minf(top, h.position.y)
		if i > 3 and h.is_on_floor():
			break
	h.jump_held = false
	return (y0 - top) / T


func test_full_jump_is_about_3_3_tiles() -> void:
	var h := await _open(ROOM)
	var rise := await _rise(h, 999)
	check(rise > 3.15 and rise < 3.45, "full jump 3.29 tiles (got %.2f)" % rise)
	check(rise > 3.0, "clears 3 blocks")


func test_short_hop() -> void:
	var h := await _open(ROOM)
	var rise := await _rise(h, 4)
	check(rise > 1.25 and rise < 1.7, "4-frame tap hops 1.48 tiles (got %.2f)" % rise)
	check(rise > 1.0, "clears 1 block")


func _run_off_step(h: HeroSide) -> int:
	h.ix = 1.0
	for i in 120:
		await physics_frames(1)
		if not h.is_on_floor():
			return i
	return -1


func test_coyote_jump_just_after_the_edge() -> void:
	var h := await _open(STEP)
	check(await _run_off_step(h) >= 0, "runs off the step")
	await physics_frames(3)
	h.jump_pressed = true
	await physics_frames(2)
	check_eq(h.jumps, 1, "jump 4 frames after the edge still works")
	check(h.velocity.y < 0.0, "going up")


func test_no_coyote_jump_late() -> void:
	var h := await _open(STEP)
	await _run_off_step(h)
	await physics_frames(9)
	h.jump_pressed = true
	await physics_frames(2)
	check_eq(h.jumps, 0, "jump 10 frames after the edge doesn't")
	check(h.velocity.y > 0.0, "still falling")


func _drop_and_press(press_at: int) -> int:
	Scenes.goto("cave", {"text": DROP})
	await physics_frames(1)
	var h: HeroSide = Scenes.screen.hero
	h.set_meta("test", true)
	var landed := -1
	for i in 90:
		if i == press_at:
			h.jump_pressed = true
			h.jump_held = true
		await physics_frames(1)
		if landed < 0 and h.is_on_floor():
			landed = i
	h.jump_held = false
	return h.jumps if press_at >= 0 else landed


func test_jump_buffer() -> void:
	var land := await _drop_and_press(-1)
	check(land > 10, "the drop takes a while (%d frames)" % land)
	check_eq(await _drop_and_press(land - 6), 1, "jump pressed 6 frames before landing fires on landing")
	check_eq(await _drop_and_press(land - 14), 0, "jump pressed 14 frames before landing is forgotten")


func test_pogo_off_a_monster() -> void:
	var h := await _open(ROOM.replace("#S......", "#S....z."))
	var cave = Scenes.screen
	var z: CaveMonster = cave.monsters.get_child(0)
	Game.take_stone("dawn")
	h.dash_used = true
	h.position = z.position + Vector2(0, -60)
	h.velocity = Vector2.ZERO
	await physics_frames(1)                    # in the air now
	h.iy = 1.0
	h.attack_pressed = true
	var y0 := h.position.y
	var top := y0
	var fastest := 0.0
	var hearts_at_top := 0
	for i in 50:
		await physics_frames(1)
		if i == 15:
			hearts_at_top = Game.hearts           # (falling back onto it later does hurt)
		h.iy = 0.0
		top = minf(top, h.position.y)
		fastest = minf(fastest, h.velocity.y)
	check(z.hp < 3 or not is_instance_valid(z), "the down strike hits the zombie")
	check(absf(fastest + HeroSide.POGO_SPEED) < 30.0, "bounces at 15.5 tiles/s (%.0f)" % fastest)
	check((y0 - top) / T > 2.0, "pogo rises over 2 tiles (%.2f)" % ((y0 - top) / T))
	check(not h.dash_used, "the pogo gives the air dash back")
	check_eq(hearts_at_top, Game.START_HEARTS, "the strike itself does no damage")


func test_pogo_off_spikes() -> void:
	var h := await _open(ROOM.replace("#S..........", "#S...^^^^^^."))
	h.position = Vector2(8 * T, 10 * T - 40)
	h.velocity = Vector2.ZERO
	await physics_frames(1)
	h.iy = 1.0
	h.attack_pressed = true
	await physics_frames(4)
	h.iy = 0.0
	check(h.velocity.y < -300.0, "bounced off the spikes")
	check_eq(Game.hearts, Game.START_HEARTS, "no damage from a pogo")


func _dash_distance(h: HeroSide) -> float:
	var x0 := h.position.x
	h.facing = 1
	h.dash_pressed = true
	await physics_frames(HeroSide.DASH_FRAMES + 1)
	return (h.position.x - x0) / T


func test_dash_only_with_wraithstep() -> void:
	var h := await _open(ROOM)
	var d := await _dash_distance(h)
	check(d < 0.5, "no dash without the Dawnstone (%.2f tiles)" % d)
	Game.take_stone("dawn")
	await physics_frames(30)
	d = await _dash_distance(h)
	check(d > 4.5 and d < 6.0, "Wraithstep dashes about 5 tiles (%.2f)" % d)


func _double_jump(h: HeroSide) -> float:
	var y0 := h.position.y
	var top := y0
	h.jump_pressed = true
	h.jump_held = true
	for i in 100:
		if i == 22:
			h.jump_pressed = true
		await physics_frames(1)
		top = minf(top, h.position.y)
		if i > 30 and h.is_on_floor():
			break
	h.jump_held = false
	return (y0 - top) / T


func test_double_jump_only_with_stormwing() -> void:
	var h := await _open(ROOM)
	var rise := await _double_jump(h)
	check_eq(h.jumps, 1, "one jump without the Wintermark")
	Game.take_stone("frost")
	h.jumps = 0
	await physics_frames(10)
	rise = await _double_jump(h)
	check_eq(h.jumps, 2, "Stormwing jumps again in the air")
	check(rise > 4.5, "about 5.4 tiles in all (%.2f)" % rise)


## Jump at the wall on the right, holding toward it; press jump while sliding. Returns the jumps made.
func _wall_jump(h: HeroSide) -> int:
	h.ix = 1.0
	h.jump_pressed = true
	h.jump_held = true
	for i in 60:
		await physics_frames(1)
		if h.velocity.y > 0.0 and h.is_on_wall():   # sliding down the wall
			break
	h.jump_held = false
	h.jump_pressed = true
	await physics_frames(2)
	h.ix = 0.0
	return h.jumps


func test_wall_jump_on_climbing_wall() -> void:
	var h := await _open(WALLS)
	h.position = Vector2(6.5 * T, 10 * T - 14)
	await physics_frames(5)
	check_eq(await _wall_jump(h), 2, "wall jump off the % wall")
	check(h.velocity.x < 0.0, "pushed away from the wall")


func test_wall_jump_on_rock_only_with_ironclaw() -> void:
	var h := await _open(WALLS)
	h.position = Vector2(13.5 * T, 10 * T - 14)
	await physics_frames(5)
	check_eq(await _wall_jump(h), 1, "no wall jump on rock without the Thornheart")
	Game.take_stone("leaf")
	await physics_frames(60)
	h.jumps = 0
	check_eq(await _wall_jump(h), 2, "Ironclaw wall jumps off rock")
