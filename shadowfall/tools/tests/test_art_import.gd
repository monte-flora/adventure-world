extends TestCase
## The Gemini import (tools/art_import.gd): magenta keys out, the JSON is written, textures tile.


func _ints(a: Array) -> Array:
	return a.map(func(v): return int(v))


func _picture() -> Image:
	var img := Image.create(64, 64, false, Image.FORMAT_RGBA8)
	img.fill(Color(1, 0, 1))                                  # Gemini's flat magenta
	img.fill_rect(Rect2i(20, 10, 24, 50), Color(0.3, 0.5, 0.2))
	img.set_pixel(19, 30, Color(0.85, 0.2, 0.8))             # a pink fringe pixel
	return img


func test_magenta_keys_out_and_trims() -> void:
	var img := _picture()
	ArtImport.key_out(img)
	check(img.get_pixel(0, 0).a == 0.0, "magenta is transparent")
	check(img.get_pixel(30, 30).a == 1.0, "the object stays solid")
	check(img.get_pixel(19, 30).a < 0.5, "a pink fringe pixel goes (mostly) clear")
	var t := ArtImport.trim(img)
	check(t.get_size() == Vector2i(24, 50), "trimmed to the object: %s" % t.get_size())
	var f := ArtImport.fit(t, Vector2i(12, 100))
	check(f.get_size() == Vector2i(12, 25), "scaled to fit, shape kept: %s" % f.get_size())
	for y in f.get_height():
		for x in f.get_width():
			var c := f.get_pixel(x, y)
			check(c.a == 0.0 or c.a == 1.0, "hard alpha")
			check(ArtImport.magentaness(c) < 0.1, "no magenta left")


func test_import_writes_png_and_json() -> void:
	var src := OS.get_user_data_dir() + "/zz_test_prop.png"
	_picture().save_png(src)
	var d := {"size": [24, 50], "foot": [0.25, 0.8, 0.5, 0.2], "lights": [[0.5, 0.1, 40]]}
	var m := ArtImport.import_prop(src, "zz_test_prop", d)
	var png := ProjectSettings.globalize_path(ArtImport.PROPS + "zz_test_prop.png")
	var js := ProjectSettings.globalize_path(ArtImport.PROPS + "zz_test_prop.json")
	check(FileAccess.file_exists(png) and FileAccess.file_exists(js), "png + json written")
	var j: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(js))
	check(_ints(j.size) == [24, 50], "size %s" % [j.size])
	check(_ints(j.foot) == [6, 40, 12, 10], "footprint %s" % [j.foot])
	check(_ints(j.anchor) == [12, 50] and int(j.base) == 50, "anchor at the foot's bottom middle %s" % [j.anchor])
	check(_ints(j.lights[0]) == [12, 5, 40], "light point %s" % [j.lights])
	check(m.size == [24, 50], "returned meta")
	DirAccess.remove_absolute(png)
	DirAccess.remove_absolute(js)
	DirAccess.remove_absolute(src)


func test_ground_texture_tiles_without_a_seam() -> void:
	var img := Image.create(64, 64, false, Image.FORMAT_RGB8)
	for y in 64:
		for x in 64:
			img.set_pixel(x, y, Color(x / 64.0, y / 64.0, 0.5))   # a ramp: the worst seam there is
	var s := ArtImport.make_seamless(img)
	for i in 64:
		var dx := s.get_pixel(0, i).r - s.get_pixel(63, i).r
		var dy := s.get_pixel(i, 0).g - s.get_pixel(i, 63).g
		check(absf(dx) < 0.06 and absf(dy) < 0.06, "edges meet at %d (%.3f %.3f)" % [i, dx, dy])


func test_every_asset_has_a_prompt_and_art() -> void:
	var a := ArtImport.assets()
	for n in a["props"]:
		check(FileAccess.file_exists(ArtImport.GEMINI + "prompts/" + n + ".txt"), "prompt for " + n)
		check(ResourceLoader.exists(ArtImport.PROPS + n + ".png"), "realm/props/%s.png" % n)
	for n in a["ground"]:
		check(FileAccess.file_exists(ArtImport.GEMINI + "prompts/" + ArtImport.ground_stem(n) + ".txt"), "prompt for ground " + n)
		check(ResourceLoader.exists(ArtImport.GROUND + n + ".png"), "realm/ground/%s.png" % n)
