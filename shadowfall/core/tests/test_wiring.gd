extends TestCase
## B9 wiring: every play screen has the HUD above the dark, and the gloom light.


func _layers(screen: Node) -> Dictionary:
	var out := {}
	for c in screen.get_children():
		if c is GloomLight:
			out["light"] = c
		elif c is CanvasLayer and c.get_script() == preload("res://ui/hud.gd"):
			out["hud"] = c
	return out


func test_play_screens_have_hud_and_light() -> void:
	for s in ["overworld", "cave"]:
		Scenes.goto(s)
		await physics_frames(2)
		var l := _layers(Scenes.screen)
		check(l.has("light"), s + " has the gloom light")
		check(l.has("hud"), s + " has the HUD")
		if l.has("light") and l.has("hud"):
			check(l.hud.layer >= GloomLight.HUD_LAYER and l.hud.layer > l.light.layer, s + ": HUD above the dark")
			check(l.light.lantern != null, s + ": the hero carries the lantern")


func test_dark_cave_is_dark() -> void:
	Scenes.goto("cave", {"text": "theme: stone\ndark: yes\n#####\n#S.E#\n#####"})
	await physics_frames(2)
	check(_layers(Scenes.screen).light.dark, "dark: yes makes the cave dark")


func test_hud_shows_a_taken_stone() -> void:
	Scenes.goto("overworld")
	await physics_frames(1)
	var hud = _layers(Scenes.screen).hud
	Game.take_stone("dawn")
	await frames(3)
	check("1/" in hud.stones.text, "the HUD counts the stone: " + hud.stones.text)


func test_checkpoint_and_stone_save() -> void:
	Scenes.goto("cave", {"text": "theme: stone\nstone: dawn\n########\n#S.C.*E#\n########"})
	await physics_frames(2)
	var cave: CaveScene = Scenes.screen
	check(not Game.has_save(), "no save yet")
	cave.hero.position = cave._cell_spot(Vector2i(3, 1))
	await physics_frames(2)
	check(Game.has_save(), "a checkpoint saves")
	cave.hero.position = cave._cell_spot(Vector2i(5, 1))
	await physics_frames(2)
	Game.reset()
	check(Game.load_save() and Game.has_ability("dash"), "the Stone is in the save")


func test_m_mutes() -> void:
	var was: bool = Audio.muted
	var m := InputEventKey.new()
	m.physical_keycode = KEY_M
	m.pressed = true
	check(InputMap.action_has_event("mute", m), "M is the mute key")
	Scenes._unhandled_input(m)
	check(Audio.muted != was, "M flips the sound")
	Audio.toggle_mute()
	check_eq(Audio.muted, was, "and back")
