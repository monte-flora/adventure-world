extends TestCase
## Core: boot, screens, save/load, gloom, abilities, the input map, the level loader.


func test_boot_reaches_title() -> void:
	Scenes.goto("boot")
	await frames(3)
	check_eq(Scenes.current, "title", "boot goes to the title")
	check(Scenes.screen != null and Scenes.screen.name == "Title", "the title screen is showing")


func test_every_screen_opens() -> void:
	for s in Scenes.SCENES:
		if s == "boot":
			continue
		Scenes.goto(s)
		await frames(2)
		check(Scenes.screen != null and Scenes.screen.is_inside_tree(), s + " opens")


func test_goto_drops_the_old_screen_at_once() -> void:
	Scenes.goto("title")
	await frames(1)
	var old := Scenes.screen
	Scenes.goto("overworld")
	check(not old.is_inside_tree(), "the old screen leaves the same frame")
	check_eq(get_children().size(), 1, "only the new screen is in the host")


func test_pause_and_resume() -> void:
	Scenes.goto("overworld")
	await frames(1)
	Scenes.pause()
	check(get_tree().paused and Scenes.is_paused(), "pause stops the game")
	Scenes.resume()
	check(not get_tree().paused, "resume starts it again")
	Scenes.goto("title")
	Scenes.pause()
	check(not Scenes.is_paused(), "the title can't be paused")


func test_input_map() -> void:
	for a in ["move_left", "move_right", "move_up", "move_down", "jump", "attack", "dash", "pause"]:
		check(InputMap.has_action(a), "action " + a)
	var r := InputEventKey.new()
	r.physical_keycode = KEY_R
	check(InputMap.action_has_event("attack", r), "R attacks")
	var pad := InputEventJoypadButton.new()
	pad.button_index = JOY_BUTTON_A
	check(InputMap.action_has_event("jump", pad), "gamepad A jumps")


func test_stones_give_abilities_and_push_gloom_back() -> void:
	Game.tick(45 * 60.0)
	check(is_equal_approx(Game.gloom, 0.5), "45 of 90 minutes: half dark")
	check(not Game.has_ability("pound"), "no pound yet")
	check(Game.take_stone("crown"), "take the crown stone")
	check(not Game.take_stone("crown"), "only once")
	check(Game.has_ability("pound"), "the crown stone gives pound")
	check(is_equal_approx(Game.gloom, 0.25), "a stone pushes the gloom back 0.25")
	for s in Game.STONES:
		Game.take_stone(s)
	Game.tick(1000 * 60.0)
	check(Game.gloom <= 0.3 + 0.0001, "with 7 stones the gloom can't pass 0.3")
	check_eq(Game.abilities().size(), 7, "7 abilities")


func test_save_and_load() -> void:
	var path := "user://test_save.json"
	Game.take_stone("dawn")
	Game.gold = 42
	Game.flags["met_warden"] = true
	check(Game.save(path), "save")
	Game.reset()
	check(Game.load_save(path), "load")
	check_eq(Game.gold, 42, "gold comes back")
	check(Game.has_ability("dash"), "abilities come back")
	check_eq(Game.flags.get("met_warden"), true, "flags come back")
	DirAccess.remove_absolute(path)
	check(not Game.load_save(path), "no save: load says no")


func test_level_file_reads_settings_and_rows() -> void:
	var lf := LevelFile.from_text("theme: moss\nname: Test\nneeds: climb, pound\n#####\n#S.E#\n#####\n")
	check_eq(lf.error, "", "no error")
	check_eq(lf.theme(), "moss", "theme")
	check_eq(lf.needs(), PackedStringArray(["climb", "pound"]), "needs")
	check_eq(Vector2i(lf.width, lf.height), Vector2i(5, 3), "size")
	check_eq(lf.start(), Vector2i(1, 1), "start")
	check_eq(lf.find("E"), [Vector2i(3, 1)] as Array[Vector2i], "exit")
	var two := LevelFile.from_text("mine: A 1 1\ngate: Ivy 2 1 climb\nmine: B 3 1\n#####\n")
	check_eq(two.all("mine"), PackedStringArray(["A 1 1", "B 3 1"]), "repeated mine: keys are all kept")
	check_eq(two.all("gate").size(), 1, "one gate")
	check_eq(two.all("nope").size(), 0, "missing key: none")


func test_every_level_file_loads() -> void:
	var n := 0
	for folder in ["caves", "secret", "shadow", "castle", "world", "realm", "stone"]:
		if not DirAccess.dir_exists_absolute(Paths.level(folder)):
			continue                   # levels/realm and levels/stone come with the levels PR
		for f in Paths.level_files(folder):
			var lf := LevelFile.load_file(Paths.level(f))
			check(lf.error == "", f + ": " + lf.error)
			n += 1
	check(n >= 20, "found the levels (%d)" % n)
