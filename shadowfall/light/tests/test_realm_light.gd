extends TestCase
## The realm's dusk (RealmLight): a CanvasModulate tint that darkens with the gloom stage, warm
## PointLight2Ds with a falloff texture, and the Flicker script that wobbles their energy.


func test_tint_darkens_with_the_gloom() -> void:
	var rl := RealmLight.new()
	add_child(rl)
	var last := 99.0
	for s in RealmLight.TINT.size():
		rl.modulate_node.color = RealmLight.TINT[s]
		var v: float = RealmLight.TINT[s].v
		check(v < last, "stage %d is darker than stage %d" % [s, s - 1])
		last = v
	check_eq(RealmLight.TINT[3], Color("2e2c4d"), "the darkest stage is the brief's #2e2c4d")
	rl.refresh()
	check_eq(rl.modulate_node.color, RealmLight.TINT[Game.gloom_stage()], "the tint follows Game.gloom_stage()")
	check(rl.modulate_node.get_parent() == rl, "the CanvasModulate lives on the RealmLight")
	rl.free()


func test_glow_flickers() -> void:
	var n := Node2D.new()
	add_child(n)
	var l := RealmLight.glow(n, Vector2(3, 4), 50.0, 1.0)
	check(l.get_parent() == n and l.position == Vector2(3, 4), "the light sits on its owner")
	check(is_equal_approx(l.texture_scale, 100.0 / 128.0), "radius 50 px")
	check(l.texture is GradientTexture2D, "a gradient falloff")
	check(RealmLight.has_light(n), "has_light sees it")
	var f: Flicker = l.get_child(0)
	await frames(1)
	var seen := {}
	for t in 40:
		var e := f.energy_at(t * 0.05)
		check(e >= 0.0 and absf(e - 1.0) <= f.amount + 0.001, "energy stays within base ± amount")
		seen[snappedf(e, 0.01)] = true
	check(seen.size() > 5, "the energy moves (%d values)" % seen.size())
	var plain := RealmLight.glow(n, Vector2.ZERO, 30.0, 1.0, RealmLight.WARM, false)
	check(plain.get_child_count() == 0, "flicker = false: a steady light")
	n.free()


func test_tinted_screen_has_no_stage_3_overlay() -> void:
	var l := GloomLight.new()
	l.stage = 3
	check_eq(l.darkness(), GloomLight.DARK_STAGE_3, "untinted: stage 3 dims")
	l.tinted = true
	check_eq(l.darkness(), 0.0, "tinted (the realm): the CanvasModulate does it instead")
	l.dark = true
	check_eq(l.darkness(), GloomLight.DARK_PLACE, "a dark place still goes dark")
	l.free()
