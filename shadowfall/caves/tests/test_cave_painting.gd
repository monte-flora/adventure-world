extends TestCase
## A painted backdrop (levels/polish/<cave>/painted.*) sits behind the blocks; the blocks and the
## robot's result stay the same. These use a made-up painting in user://, not levels/polish/.

const FILE := "caves/05_green_lvl_1.txt"


func _fake_painting() -> String:
	var root := ProjectSettings.globalize_path("user://polish_test")
	DirAccess.make_dir_recursive_absolute(root.path_join("05_green_lvl_1"))
	var img := Image.create(275, 153, false, Image.FORMAT_RGB8)
	img.fill(Color("3a2a50"))
	img.save_png(root.path_join("05_green_lvl_1/painted.png"))
	return root


func test_no_painting_keeps_the_parallax() -> void:
	CaveArt.polish_root = ProjectSettings.globalize_path("user://polish_none")
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	var cave = Scenes.screen
	check(cave.painting == null, "no painting")
	check(cave.parallax[0].visible, "the far layer shows")
	CaveArt.polish_root = ""


func test_a_painting_fills_the_cave_behind_the_blocks() -> void:
	CaveArt.polish_root = _fake_painting()
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	var cave = Scenes.screen
	check(cave.painting != null, "the painting is used")
	if cave.painting:
		var size: Vector2 = cave.painting.texture.get_size() * cave.painting.scale
		check(size.is_equal_approx(Vector2(cave.level.width, cave.level.height) * LevelFile.TILE), "fits the cave: %s" % size)
		check(cave.painting.get_index() < cave.map.get_index(), "drawn behind the blocks")
		check(cave.painting.material == cave.map.material, "the gloom light applies to it")
	check(not cave.parallax[0].visible, "the parallax behind it is hidden")
	check(cave.map.get_used_cells().size() > 50, "the blocks are all there")
	CaveArt.polish_root = ""


func test_robot_still_beats_a_painted_cave() -> void:
	CaveArt.polish_root = _fake_painting()
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	Game.hearts = 99
	Game.max_hearts = 99
	check(Scenes.screen.painting != null, "painted")
	var bot := CaveRobot.new(Scenes.screen)
	var ok: bool = await bot.run(self)
	check(ok, "the robot beats the painted cave too")
	CaveArt.polish_root = ""


## Is every pixel of this atlas tile see-through?
func _blank(cave, atlas: Vector2i) -> bool:
	var img: Image = cave.map.tile_set.get_source(0).texture.get_image()
	var r := img.get_region(Rect2i(atlas * LevelFile.TILE, Vector2i(LevelFile.TILE, LevelFile.TILE)))
	return r.is_invisible()


func _first(cave, ch: String) -> Vector2i:
	for y in cave.level.height:
		var x: int = cave.grid[y].find(ch)
		if x >= 0:
			return Vector2i(x, y)
	return Vector2i(-1, -1)


func test_a_painted_cave_hides_rock_but_keeps_its_collision() -> void:
	CaveArt.polish_root = _fake_painting()
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	var cave = Scenes.screen
	var rock: Vector2i = _first(cave, "#")
	var atlas: Vector2i = cave.map.get_cell_atlas_coords(rock)
	check(_blank(cave, atlas), "rock is not drawn: the painting shows it")
	check(_blank(cave, Vector2i(cave._solid_index["="], 0)), "ledges are not drawn")
	check(cave.map.get_cell_tile_data(rock).get_collision_polygons_count(0) > 0, "rock still blocks")
	for ch in "BMGo*s-<>n":                           # they change, move or must be readable
		check(not _blank(cave, Vector2i(cave._solid_index[ch], 0)), "'%s' still draws" % ch)
	for ch in CaveTiles.HAZARD + CaveTiles.PICKUP + CaveTiles.MONSTER + CaveTiles.MOVING + "ECLHV":
		check(ch not in CaveArt.HIDE_PAINTED, "'%s' is never hidden" % ch)
	CaveArt.polish_root = ""


func test_no_painting_draws_the_rock() -> void:
	CaveArt.polish_root = ProjectSettings.globalize_path("user://polish_none")
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	var cave = Scenes.screen
	check(not _blank(cave, cave.map.get_cell_atlas_coords(_first(cave, "#"))), "rock tiles as before")
	CaveArt.polish_root = ""


func test_F3_shows_the_hidden_collision() -> void:
	CaveArt.polish_root = _fake_painting()
	Scenes.goto("cave", {"file": FILE})
	await physics_frames(2)
	var cave = Scenes.screen
	check(not cave.show_collision, "off by default")
	var key := InputEventKey.new()
	key.keycode = KEY_F3
	key.pressed = true
	cave._unhandled_input(key)
	check(cave.show_collision, "F3 shows the outlines")
	cave._unhandled_input(key)
	check(not cave.show_collision, "F3 again hides them")
	CaveArt.polish_root = ""



## Every cell's tile and collision, to compare a painted cave with the same cave unpainted.
func _collision(cave) -> Array:
	var out := []
	for cell in cave.map.get_used_cells():
		var td: TileData = cave.map.get_cell_tile_data(cell)
		out.append([cell, cave.map.get_cell_atlas_coords(cell), td.get_collision_polygons_count(0), td.get_collision_polygons_count(1)])
	out.sort()
	return out


## The real painting (levels/polish/02_the_vine_garden). The Godot robot can't route this cave yet
## (vines, painted or not); the robot test above covers a painted cave, this checks collision is the same.
func test_the_painted_vine_garden_keeps_every_block() -> void:
	const VINE := "caves/02_the_vine_garden.txt"
	CaveArt.polish_root = ProjectSettings.globalize_path("user://polish_none")
	Scenes.goto("cave", {"file": VINE})
	await physics_frames(2)
	var plain := _collision(Scenes.screen)
	CaveArt.polish_root = ""
	Scenes.goto("cave", {"file": VINE})
	await physics_frames(2)
	check(Scenes.screen.painting != null, "the Vine Garden has its painting")
	check(_collision(Scenes.screen) == plain, "same blocks, same collision as unpainted")
	check(plain.size() > 300, "a full cave: %d blocks" % plain.size())
