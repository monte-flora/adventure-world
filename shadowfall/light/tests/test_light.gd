extends TestCase
## Light (B3): gloom stages, the palette swap, darkness rings, lantern, crystals, dark caves,
## the Light Stone burst, and the HUD staying bright. test_render_* draws for real when a GPU is
## there (run without --headless); headless CI checks everything else.


func _light(dark := false) -> GloomLight:
	var l := GloomLight.new()
	l.dark = dark
	add_child(l)
	return l


func test_stage_per_gloom_value() -> void:
	var l := _light()
	for pair in [[0.0, 0], [0.2, 0], [0.33, 0], [0.34, 1], [0.5, 1], [0.66, 1], [0.67, 2], [0.9, 2], [1.0, 3]]:
		Game.gloom = pair[0]
		l.refresh()
		check_eq(l.stage, pair[1], "gloom %.2f -> stage" % pair[0])
		check_eq(l.world_material.get_shader_parameter("stage"), pair[1], "gloom %.2f -> shader stage" % pair[0])


func test_lut_follows_the_art_rules() -> void:
	var pal := GloomLut.palette()
	check_eq(pal.size(), 32, "Shadowfall 32")
	var img := GloomLut.image()
	check_eq(img.get_size(), Vector2i(32, 4), "LUT is 32 x 4")
	for hex in pal:
		check_eq(GloomLut.swap(hex, 0), hex, "stage 0 keeps " + hex)
		var lum := Color(hex).get_luminance()
		for s in range(1, 4):
			var out := GloomLut.swap(hex, s)
			check(out in pal, "stage %d of %s stays in the palette" % [s, hex])
			if GloomLut.is_accent(hex):
				check_eq(out, hex, "accent %s never changes" % hex)
			var l2 := Color(out).get_luminance()
			check(l2 <= lum + 0.0001, "stage %d of %s is no lighter than stage 0" % [s, hex])
	for ramp in ["moss", "earth", "water"]:
		for hex in GloomLut.RAMPS[ramp]:
			check(GloomLut.swap(hex, 3) in GloomLut.RAMPS["ink"], "stage 3: %s drops into ink" % hex)
	check_eq(GloomLut.swap("4f8a4b", 2), "1f4031", "moss3 two steps down at stage 2")
	check_eq(GloomLut.swap("d6d0e0", 3), "6b6187", "ink6 two steps down at stage 3")


func test_remap_off_palette_colours() -> void:
	var c := Color("363046")                          # a placeholder tile colour
	check_eq(GloomLut.remap(c, 0), c, "stage 0 leaves it alone")
	check(GloomLut.remap(c, 2).get_luminance() < c.get_luminance(), "stage 2 darkens it")
	check(GloomLut.remap(Color("4f8a4b"), 2).is_equal_approx(Color("1f4031")), "palette colour lands on its swap")


func test_darkness_has_three_hard_rings() -> void:
	var b := GloomLight.DARK_PLACE
	var pools := [[Vector2(100, 100), 100.0]]
	check_eq(GloomLight.darkness_at(Vector2(130, 100), b, pools), 0.0, "inner ring is clear")
	check(is_equal_approx(GloomLight.darkness_at(Vector2(160, 100), b, pools), b / 3.0), "middle ring 1/3")
	check(is_equal_approx(GloomLight.darkness_at(Vector2(190, 100), b, pools), b * 2.0 / 3.0), "outer ring 2/3")
	check_eq(GloomLight.darkness_at(Vector2(210, 100), b, pools), b, "outside is full dark")
	pools.append([Vector2(250, 100), 100.0])
	check_eq(GloomLight.darkness_at(Vector2(230, 100), b, pools), 0.0, "overlapping pools take the lowest dark")


func test_dark_caves_and_stage_3() -> void:
	var lf := LevelFile.from_text("theme: shadow\ndark: yes\n#####\n#S.E#\n#####\n")
	check(GloomLight.is_dark(lf), "dark: yes is read")
	check(not GloomLight.is_dark(LevelFile.from_text("theme: moss\n###\n#S#\n###\n")), "no header is not dark")
	var l := _light(true)
	check_eq(l.darkness(), GloomLight.DARK_PLACE, "a dark cave is dark")
	check(l.overlay.visible, "the dark is drawn")
	l.dark = false
	l.refresh()
	check_eq(l.darkness(), 0.0, "a normal cave at stage 0 is not")
	check(not l.overlay.visible, "nothing drawn when there's no dark")
	Game.gloom = 1.0
	l.refresh()
	check_eq(l.darkness(), GloomLight.DARK_STAGE_3, "stage 3 dims everywhere")


func test_lantern_and_crystals() -> void:
	var world := Node2D.new()
	add_child(world)
	var hero := Node2D.new()
	hero.position = Vector2(300, 200)
	world.add_child(hero)
	var l := _light(true)
	var lan := l.follow(hero)
	check_eq(lan.radius, 130.0, "lantern is 130 px")
	l.add_crystal(world, Vector2(500, 300))
	l.add_crystal(world, Vector2(5000, 300))          # off screen
	var pools := l.screen_pools()
	check_eq(pools.size(), 2, "lantern + the crystal on screen")
	check(pools[0][0].is_equal_approx(Vector2(300, 200)) and pools[0][1] == 130.0, "lantern pool on the hero")
	check(pools[1][1] >= 30.0 and pools[1][1] <= 40.0, "crystal pool 30-40 px")
	hero.position.x += 50
	check(l.screen_pools()[0][0].is_equal_approx(Vector2(350, 200)), "lantern walks with the hero")


func test_light_stone_burst() -> void:
	var hero := Node2D.new()
	hero.position = Vector2(200, 200)
	add_child(hero)
	var l := _light(true)
	l.follow(hero)
	Game.take_stone("dawn")
	check(l.bursting() and l.flash.visible and l.flash.color.a > 0.5, "a stone flashes gold")
	await frames(30)
	var pools := l.screen_pools()
	check(pools[0][1] > 900.0, "the burst of light fills the screen")
	check(GloomLight.darkness_at(Vector2(900, 500), l.darkness(), pools) == 0.0, "no dark during the burst")
	await frames(60)
	check(not l.bursting() and not l.flash.visible, "the burst ends")


func test_hud_is_never_darkened() -> void:
	var l := _light(true)
	Game.gloom = 1.0
	l.refresh()
	check(l.layer < GloomLight.HUD_LAYER, "the dark draws below the HUD layer")
	check(l.overlay.get_parent() == l and l.flash.get_parent() == l, "dark and flash live on the light's own layer")
	check(get_tree().root.find_children("*", "CanvasModulate", true, false).is_empty(), "nothing tints the whole canvas")


## Draws a world tile, a character and a HUD bar in a real viewport and reads the pixels back.
## Proves the shaders compile on the Compatibility renderer (the web export uses the same one).
func test_render_shaders_on_the_gpu() -> void:
	if DisplayServer.get_name() == "headless":
		return                                         # no GPU in CI; run without --headless to check
	var vp := SubViewport.new()
	vp.size = Vector2i(960, 540)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var bg := ColorRect.new()
	bg.color = Color("f4f1ea")
	bg.size = Vector2(960, 540)
	vp.add_child(bg)
	var light := GloomLight.new()
	light.dark = true
	vp.add_child(light)
	var tile := ColorRect.new()                       # world tile: palette-swapped
	tile.color = Color("4f8a4b")
	tile.position = Vector2(400, 200)
	tile.size = Vector2(64, 64)
	tile.material = light.world_material
	vp.add_child(tile)
	var hero := Node2D.new()
	hero.position = Vector2(432, 232)
	vp.add_child(hero)
	light.follow(hero)
	var guy := ColorRect.new()                        # a character: never remapped
	guy.color = Color("c23a3a")
	guy.position = Vector2(440, 260)
	guy.size = Vector2(8, 8)
	vp.add_child(guy)
	var hud := CanvasLayer.new()
	hud.layer = GloomLight.HUD_LAYER
	var bar := ColorRect.new()
	bar.color = Color("f7c64a")
	bar.size = Vector2(40, 10)
	hud.add_child(bar)
	vp.add_child(hud)
	Game.gloom = 0.7                                  # stage 2
	await frames(4)
	var img := vp.get_texture().get_image()
	check(img != null and not img.is_empty(), "the viewport rendered")
	if img == null or img.is_empty():
		return
	var near := func(a: Color, b: Color) -> bool: return absf(a.r - b.r) + absf(a.g - b.g) + absf(a.b - b.b) < 0.03
	check(near.call(img.get_pixel(432, 232), Color("1f4031")), "tile at stage 2 is moss1 (got %s)" % img.get_pixel(432, 232).to_html(false))
	check(near.call(img.get_pixel(444, 264), Color("c23a3a")), "character keeps its colour (got %s)" % img.get_pixel(444, 264).to_html(false))
	check(near.call(img.get_pixel(5, 5), Color("f7c64a")), "HUD keeps its colour in the dark (got %s)" % img.get_pixel(5, 5).to_html(false))
	var far := img.get_pixel(900, 500)
	var want := Color("f4f1ea").lerp(GloomLight.INK, GloomLight.DARK_PLACE)
	check(near.call(far, want), "far from the lantern is dark (got %s, want %s)" % [far.to_html(false), want.to_html(false)])
	var ring := img.get_pixel(432 + 110, 232)        # outer ring: 2/3 of the dark
	var want_ring := Color("f4f1ea").lerp(GloomLight.INK, GloomLight.DARK_PLACE * 2.0 / 3.0)
	check(near.call(ring, want_ring), "outer ring is 2/3 dark (got %s)" % ring.to_html(false))


func test_demo_opens_a_dark_cave() -> void:
	var demo: Node = load("res://light/demo.tscn").instantiate()
	add_child(demo)
	await frames(2)
	var l: GloomLight = demo.light
	check(l.dark and l.overlay.visible, "the demo cave is dark")
	check(l.screen_pools().size() >= 1, "the lantern lights it")
	demo.queue_free()
