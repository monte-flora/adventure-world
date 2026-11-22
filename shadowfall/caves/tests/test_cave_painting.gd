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
