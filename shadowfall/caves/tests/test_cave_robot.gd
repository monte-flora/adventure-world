extends TestCase
## The cave robot (caves/robot/cave_robot.gd) beats real caves with real physics: it only presses
## buttons. It would have caught a geyser that doesn't throw you.

const CAVES := ["stone/1_the_crumbling_vigil.txt"]


func _beat(file: String) -> void:
	Scenes.goto("cave", {"file": file})
	await physics_frames(2)
	Game.hearts = 99
	Game.max_hearts = 99
	var bot := CaveRobot.new(Scenes.screen)
	var ok: bool = await bot.run(self)
	check(ok, "%s: the robot beats it\n%s" % [file, "\n".join(bot.log.slice(maxi(0, bot.log.size() - 15)))])


func test_robot_beats_stone_1() -> void:
	await _beat("stone/1_the_crumbling_vigil.txt")
