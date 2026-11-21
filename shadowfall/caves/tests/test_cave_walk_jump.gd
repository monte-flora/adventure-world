extends TestCase
## A real cave from levels/caves loads, and the Hero walks and jumps in it.

const FILE := "caves/01_the_easy_moss_cave.txt"


func _open() -> Node:
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(30)                   # fall onto the floor
	return Scenes.screen


func test_cave_loads() -> void:
	var cave = await _open()
	check(cave.level.error == "", "the level loads: " + cave.level.error)
	check(cave.map.get_used_cells().size() > 100, "rock tiles are placed")
	check(cave.hero.is_on_floor(), "the Hero stands on the floor")


func test_hero_walks() -> void:
	var cave = await _open()
	var h: HeroSide = cave.hero
	h.set_meta("test", true)
	var x0 := h.position.x
	h.ix = 1.0
	await physics_frames(15)
	h.ix = 0.0
	check(h.position.x > x0 + 30.0, "walks right (%.0f px)" % (h.position.x - x0))
	check(h.is_on_floor(), "still on the floor")


func test_hero_jumps_and_lands() -> void:
	var cave = await _open()
	var h: HeroSide = cave.hero
	h.set_meta("test", true)
	var y0 := h.position.y
	h.jump_pressed = true
	h.jump_held = true
	var top := y0
	for i in 60:
		await physics_frames(1)
		top = minf(top, h.position.y)
	h.jump_held = false
	await physics_frames(30)
	check(y0 - top > 2.0 * LevelFile.TILE, "jumps over 2 tiles (%.0f px)" % (y0 - top))
	check(h.is_on_floor() and absf(h.position.y - y0) < 1.0, "lands back on the floor")
