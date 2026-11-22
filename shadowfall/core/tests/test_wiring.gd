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
