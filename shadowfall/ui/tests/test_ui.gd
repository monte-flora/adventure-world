extends TestCase
## UI: every screen opens, the HUD follows Game, the text box pages, the pause tabs, remapping.

const SETTINGS := "user://test_ui_settings.cfg"


func _before() -> void:
	UiSettings.path = SETTINGS
	DirAccess.remove_absolute(SETTINGS)


func _after() -> void:
	UiSettings.reset()
	DirAccess.remove_absolute(SETTINGS)
	UiSettings.path = UiSettings.PATH


func _open_pause() -> Node:
	Scenes.goto("overworld")
	await frames(1)
	Scenes.pause()
	await frames(1)
	return Scenes._pause


## Every visible Control inside the 960×540 view.
func _fits(root: Node, what: String) -> void:
	var view := Rect2(Vector2.ZERO, UiStyle.VIEW)
	for c in root.find_children("*", "Control", true, false):
		var ctl := c as Control
		if ctl.is_visible_in_tree() and ctl.size != Vector2.ZERO:
			var r := ctl.get_global_rect()
			check(view.encloses(r.grow(-0.5)), "%s: %s at %s is inside 960x540" % [what, ctl.name, r])


func test_title_opens_and_menu_starts() -> void:
	_before()
	Scenes.goto("title")
	await frames(2)
	var t = Scenes.screen
	check(t != null and t.name == "Title", "title opens")
	check("New journey" in t.items, "New journey in the menu")
	_fits(t, "title")
	t.cursor = t.items.find("New journey")
	t.press("jump")
	await frames(2)
	check_eq(Scenes.current, "overworld", "New journey goes to the realm")
	_after()


func test_hud_shows_hearts_stones_gold() -> void:
	var hud = load("res://ui/hud.tscn").instantiate()
	add_child(hud)
	await frames(1)
	check_eq(hud.hearts.text.length(), Game.hearts, "one heart per heart")
	check_eq(hud.stones.text, UiStyle.STONE + " 0/7", "no stones yet")
	Game.hearts = 3
	Game.gold = 120
	Game.take_stone("dawn")
	await frames(1)
	check_eq(hud.hearts.text.length(), 3, "3 full hearts")
	check_eq(hud.lost.text.length(), Game.max_hearts - 3, "the lost hearts show dim")
	check_eq(hud.gold.text, UiStyle.COIN + " 120", "gold")
	check_eq(hud.stones.text, UiStyle.STONE + " 1/7", "1 stone")
	check(hud.layer > 10, "HUD sits above the light layer")
	_fits(hud, "hud")
	hud.queue_free()


func test_dialogue_box_three_lines_and_pages() -> void:
	var box = load("res://ui/dialogue_box.tscn").instantiate()
	add_child(box)
	await frames(1)
	check(not box.visible, "hidden until someone talks")
	var long := "The *Dawnstone* sleeps beneath the Weepingwold, where the old roots drink the dark. ".repeat(6)
	box.say("Warden", long)
	check(box.visible, "shows")
	check(box.pages.size() >= 2, "long talk makes more than one page (%d)" % box.pages.size())
	for p in box.pages:
		check(p.split("\n").size() <= 3, "at most 3 lines a page")
	check("[color=#f7c64a]Dawnstone[/color]" in box.text.text, "the important word is light0")
	_fits(box, "dialogue")
	var done := [false]
	box.finished.connect(func(): done[0] = true)
	for i in box.pages.size() * 2 + 1:
		box.advance()
	check(done[0] and not box.visible, "closes after the last page")
	box.queue_free()


func test_pause_opens_every_tab() -> void:
	_before()
	Game.flags["quests"] = {"the_drowned_bell": "active", "warden_oath": "done"}
	Game.flags["sigils"] = ["keen_edge"]
	Game.flags["map_screen"] = [2, 1]
	Game.take_stone("dawn")
	var p = await _open_pause()
	check(p != null, "pause opens")
	for i in p.TABS.size():
		p.show_tab(i)
		await frames(1)
		check(p._content.get_child_count() > 0, p.TABS[i] + " has content")
		_fits(p, "pause " + p.TABS[i])
	p.show_tab(0)
	check_eq(p.quest_entries().size(), 2, "quest log lists 2 quests")
	check_eq(p.sigil_slots(), 3, "3 sigil slots with 1 stone")
	p.press("map")
	check_eq(p.TABS[p.tab], "MAP", "TAB opens the map")
	p.press("tool")
	check_eq(p.TABS[p.tab], "SIGILS", "E: next tab")
	p.press("heal")
	p.press("heal")
	check_eq(p.TABS[p.tab], "JOURNEY", "Q: back a tab")
	p.press("jump")   # Resume
	await frames(1)
	check(not get_tree().paused, "Resume unpauses")
	_after()


func test_volume_steps_and_saves() -> void:
	_before()
	var p = await _open_pause()
	p.show_tab(p.TABS.find("SOUND"))
	var before: float = UiSettings.volume["Master"]
	p.press("move_left")
	check(is_equal_approx(UiSettings.volume["Master"], before - 0.1), "LEFT lowers master 10%")
	check(is_equal_approx(db_to_linear(AudioServer.get_bus_volume_db(0)), before - 0.1), "the Master bus follows")
	UiSettings.volume["Master"] = 1.0
	UiSettings.load_and_apply()
	check(is_equal_approx(UiSettings.volume["Master"], before - 0.1), "saved and read back")
	Scenes.resume()
	_after()


func test_remap_changes_input_map() -> void:
	_before()
	var p = await _open_pause()
	p.show_tab(p.TABS.find("CONTROLS"))
	p.cursor = UiSettings.REMAPPABLE.keys().find("attack")
	p.press("jump")
	check_eq(p.remapping, "attack", "waiting for a key")
	var k := InputEventKey.new()
	k.physical_keycode = KEY_J
	k.pressed = true
	check(p.capture(k), "key taken")
	var r := InputEventKey.new()
	r.physical_keycode = KEY_R
	check(InputMap.action_has_event("attack", k), "J attacks now")
	check(not InputMap.action_has_event("attack", r), "R no longer attacks")
	var pad := InputEventJoypadButton.new()
	pad.button_index = JOY_BUTTON_X
	check(InputMap.action_has_event("attack", pad), "the gamepad button stays")
	# a key moves off the action that had it
	UiSettings.remap_key("jump", KEY_J)
	check(not InputMap.action_has_event("attack", k), "J left attack when it went to jump")
	# ESC cancels without changing anything
	p.cursor = UiSettings.REMAPPABLE.keys().find("dash")
	p.press("jump")
	var esc := InputEventKey.new()
	esc.physical_keycode = KEY_ESCAPE
	esc.pressed = true
	p.capture(esc)
	check_eq(UiSettings.key_name("dash"), OS.get_keycode_string(KEY_SHIFT), "ESC cancels")
	# saved and applied again on the next run
	Controls.setup()
	UiSettings.load_and_apply()
	var j := InputEventKey.new()
	j.physical_keycode = KEY_J
	check(InputMap.action_has_event("jump", j), "the remap comes back from the settings file")
	UiSettings.reset()
	check(InputMap.action_has_event("attack", r), "reset: R attacks again")
	Scenes.resume()
	_after()


func test_pixel_font_and_whole_scale() -> void:
	var body := UiStyle.font("body")
	check(body.get_data().size() > 0, "body font loaded")
	check_eq(body.antialiasing, TextServer.FONT_ANTIALIASING_NONE, "no antialiasing")
	check(body.has_char(0xE000) and UiStyle.font("small").has_char(0xE002), "heart and coin glyphs")
	check_eq(get_tree().root.content_scale_size, Vector2i(UiStyle.VIEW), "view is 960x540")
	check_eq(get_tree().root.content_scale_stretch, Window.CONTENT_SCALE_STRETCH_INTEGER, "whole-number scale (×1, ×2)")
	# every label's font size is a whole multiple of its font's line height, so ×1 and ×2 stay sharp
	var hud = load("res://ui/hud.tscn").instantiate()
	add_child(hud)
	var box = load("res://ui/dialogue_box.tscn").instantiate()
	add_child(box)
	await frames(1)
	for root in [hud, box]:
		for l in root.find_children("*", "Label", true, false):
			var s: int = l.get_theme_font_size("font_size")
			check(s % UiStyle.SMALL == 0 or s % UiStyle.BODY == 0, "%s size %d is a whole multiple" % [l.name, s])
	hud.queue_free()
	box.queue_free()


func test_ui_fonts_match_assets() -> void:
	# ui/fonts/ holds copies of assets/fonts/ (the web export can't reach outside res://)
	var src := ProjectSettings.globalize_path("res://").path_join("../assets/fonts").simplify_path()
	if not DirAccess.dir_exists_absolute(src):
		return   # font PR not merged here yet
	for f in ["ShadowfallBody.ttf", "ShadowfallSmall.ttf", "shadowfall_logo.png"]:
		check_eq(FileAccess.get_md5("res://ui/fonts/" + f), FileAccess.get_md5(src.path_join(f)), f + " matches assets/fonts")
