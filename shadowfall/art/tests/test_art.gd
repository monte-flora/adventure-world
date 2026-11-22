extends TestCase
## The art checker passes, and every sheet loads as SpriteFrames.


func test_checker_passes() -> void:
	var bad := ArtCheck.check_all()
	for b in bad:
		print("    " + b)
	check(bad.is_empty(), "%d art problems (listed above)" % bad.size())


func test_checker_catches_bad_pixels() -> void:
	var pal := ArtCheck.palette()
	var img := Image.create(4, 4, false, Image.FORMAT_RGBA8)
	img.set_pixel(0, 0, Color("0b0a12"))
	check(ArtCheck.check_image(img, "ok", pal).is_empty(), "ink0 + clear passes")
	img.set_pixel(1, 1, Color(1, 0, 1))
	check_eq(ArtCheck.check_image(img, "bad", pal).size(), 1, "magenta is caught")
	img.set_pixel(1, 1, Color(Color("0b0a12"), 0.5))
	check_eq(ArtCheck.check_image(img, "bad", pal).size(), 1, "half alpha is caught")


func test_sheets_load_as_sprite_frames() -> void:
	var names := ArtSheet.names()
	check(names.size() >= 30, "found %d sheets" % names.size())
	for n in names:
		var sf := ArtSheet.frames(n)
		var anims: Dictionary = ArtSheet.meta(n)["anims"]
		check_eq(sf.get_animation_names().size(), anims.size(), n + " animations")
		for a in anims:
			check_eq(sf.get_frame_count(a), int(anims[a]["frames"]), "%s/%s frames" % [n, a])
			var t: AtlasTexture = sf.get_frame_texture(a, 0)
			check_eq(Vector2i(t.region.size), ArtSheet.cell(n), "%s/%s cell" % [n, a])


func test_hero_has_every_move() -> void:
	for a in ["idle", "run", "jump", "fall", "land", "attack", "air_attack", "pogo", "climb", "wall_slide",
			"dash", "swim", "lantern_raise", "hurt", "death"]:
		check(ArtSheet.frames("hero_side").has_animation(a), "hero_side has " + a)
	for d in ["down", "up", "side"]:
		for a in ["idle_", "walk_", "roll_", "attack_"]:
			check(ArtSheet.frames("hero_top").has_animation(a + d), "hero_top has " + a + d)
	check_eq(ArtSheet.cell("hero_side"), Vector2i(48, 64), "side hero cell")
	check_eq(ArtSheet.cell("hero_top"), Vector2i(48, 56), "top-down hero cell")


func test_sprite_plays_in_a_scene() -> void:
	var spr := AnimatedSprite2D.new()
	spr.sprite_frames = ArtSheet.frames("hero_side")
	spr.offset = ArtSheet.offset("hero_side")
	add_child(spr)
	spr.play("run")
	await frames(20)
	check(spr.frame > 0, "run animation advances")
	check_eq(ArtSheet.tile("tiles_stone", "solid_5").get_size(), Vector2(32, 32), "a tile is 32x32")
	spr.queue_free()


func test_fonts_load() -> void:
	for f in ["body", "num"]:
		var font: Font = load("res://art/font/%s.fnt" % f)
		check(font != null, f + ".fnt loads as a Font")
		if font:
			check(font.get_string_size("A1", HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x > 0, f + " measures text")
