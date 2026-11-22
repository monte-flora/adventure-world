extends TestCase
## Wave E2 characters: the Lanternbearer's light rig (the strongest light, embers, follows his facing).


func _open() -> Node:
	Scenes.goto("overworld")
	await physics_frames(2)
	return Scenes.screen


func test_hero_carries_the_strongest_light() -> void:
	var ow = await _open()
	var hero: HeroTop = ow.hero
	check(hero.light is PointLight2D and hero.light.texture != null, "the hero has a PointLight2D")
	check(hero.light.color.r > hero.light.color.b * 2.0, "the light is warm gold")
	check(hero.embers is CPUParticles2D and hero.embers.emitting, "embers rise from the lantern")
	check(hero.embers.gravity.y < 0, "embers drift up")
	check(LanternLight.NPC.energy < LanternLight.HERO.energy * 0.6, "a person's torch is far weaker")
	check(LanternLight.NPC.radius < LanternLight.HERO.radius * 0.6, "and far smaller")


func test_light_follows_the_lantern_and_the_dusk() -> void:
	var ow = await _open()
	var hero: HeroTop = ow.hero
	hero.drive = Vector2.RIGHT
	await physics_frames(4)
	var right := hero.light.position.x
	hero.drive = Vector2.LEFT
	await physics_frames(12)
	check(hero.light.position.x == -right and right != 0.0, "the light swaps sides when he turns")
	hero.drive = Vector2.ZERO
	var day := hero.light.steady_energy()
	var dusk := CanvasModulate.new()
	dusk.color = Color("3a4068")
	ow.add_child(dusk)
	hero.light._look = 0.0
	await frames(3)
	check(hero.light.steady_energy() > day * 1.5, "the lantern burns brighter at dusk (%.2f > %.2f)" % [hero.light.steady_energy(), day])
	dusk.queue_free()


func test_sunfang_runes_show_while_walking() -> void:
	for a in ["idle_down", "walk_side", "attack_up"]:
		check(ArtSheet.frames("hero_top").has_animation(a + "_sunfang"), "hero_top has %s_sunfang" % a)
