extends TestCase
## The cave robot (caves/robot/cave_robot.gd) beats real caves with real physics: it only presses
## buttons. It would have caught a geyser that doesn't throw you or a gate a lever can't open.
## Not here: stone 2 (needs ropes and the dash, which the robot can't use yet).


func _beat(file: String) -> void:
	Scenes.goto("cave", {"file": file})
	await physics_frames(2)
	Game.hearts = 99
	Game.max_hearts = 99
	var bot := CaveRobot.new(Scenes.screen)
	var ok: bool = await bot.run(self)
	check(ok, "%s: the robot takes the diamond and gets out\n%s" % [file, "\n".join(bot.log.slice(maxi(0, bot.log.size() - 15)))])


func test_robot_beats_stone_1_crumbling_ledges() -> void:
	await _beat("stone/1_the_crumbling_vigil.txt")


func test_robot_beats_stone_3_crumbling_floors_and_a_lever() -> void:
	await _beat("stone/3_the_sunken_bell.txt")


func test_robot_beats_classic_05() -> void:
	await _beat("caves/05_green_lvl_1.txt")


func test_robot_beats_classic_07() -> void:
	await _beat("caves/07_red_lvl_1.txt")


func test_robot_beats_classic_12() -> void:
	await _beat("caves/12_the_crystal_cave.txt")
