extends TestCase
## The Gemini character import (tools/char_import.gd): figures are cut apart and stood on the sheet's
## origin, people sheets keep their .json layout, portraits keep their size, the comparison picture is made.

const SKIN := Color(0.7, 0.5, 0.4)


## A made-up Gemini picture: `n` figures (w x h) on flat magenta (or green), gaps between them.
func _picture(n: int, w := 40, h := 90, bg := Color(1, 0, 1)) -> Image:
	var img := Image.create(n * (w + 30) + 30, h + 40, false, Image.FORMAT_RGBA8)
	img.fill(bg)
	for i in n:
		img.fill_rect(Rect2i(30 + i * (w + 30), 20, w, h - i * 2), SKIN)    # each a little shorter
	img.set_pixel(2, 2, SKIN)                                                 # a speck
	return img


func test_figures_split_at_gaps_and_drop_specks() -> void:
	var img := _picture(2)
	CharImport.key_out(img)
	var f := CharImport.figures(img)
	check_eq(f.size(), 2, "two figures, the speck dropped")
	check_eq(f[0].get_size(), Vector2i(40, 90), "trimmed to the figure")
	var four := _picture(3)
	CharImport.key_out(four)
	check_eq(CharImport.figures(four, 4).size(), 4, "wrong count: cut into equal columns")


func test_green_key_for_purple_characters() -> void:
	var img := _picture(1, 40, 90, Color(0, 1, 0))
	img.set_pixel(40, 40, Color(0.5, 0.1, 0.7))                               # violet stays
	CharImport.key_out(img, "green")
	check(img.get_pixel(0, 0).a == 0.0 and img.get_pixel(40, 40).a == 1.0, "green goes, violet stays")
	check(CharImport.figures(img).size() == 1, "one figure")


func test_people_sheet_keeps_the_layout() -> void:
	var img := _picture(2)
	CharImport.key_out(img)
	var meta := ArtSheet.meta("people_smith")
	var fr := CharImport.fit_all(CharImport.figures(img), Vector2i(28, 44))
	check(fr[0].get_height() == 44 and fr[0].get_width() <= 28, "biggest frame fits the box: %s" % fr[0].get_size())
	check(fr[1].get_height() < 44, "one scale for both frames: %s" % fr[1].get_size())
	var sheet := CharImport.people_sheet(fr, meta)
	var old := Image.load_from_file(ProjectSettings.globalize_path("res://art/sheets/people_smith.png"))
	check_eq(sheet.get_size(), old.get_size(), "same size as today's sheet")
	var c := ArtSheet.cell("people_smith")
	var o: Array = meta["origin"]
	for anim in meta["anims"]:
		var r := ArtSheet.region("people_smith", anim, 0)
		var used := sheet.get_region(r).get_used_rect()
		check_eq(used.end.y, int(o[1]), "%s stands on the origin" % anim)
		check(absi(used.get_center().x - int(o[0])) <= 1, "%s is centred" % anim)
	check(sheet.get_region(ArtSheet.region("people_smith", "idle_down", 2)).get_used_rect().size.y < 44, "idle frame 3 breathes")
	check(c == Vector2i(32, 48), "people cells are 32x48")


func test_portrait_keeps_its_size() -> void:
	var img := _picture(1, 300, 500)
	CharImport.key_out(img)
	var p := CharImport.portrait(img, Vector2i(128, 160))
	check_eq(p.get_size(), Vector2i(128, 160), "exact portrait size")
	check_eq(p.get_used_rect().end.y, 160, "stands on the bottom edge")


func test_out_paths() -> void:
	check_eq(CharImport.out_path("portrait_hero"), "res://art/ui/hero_portrait.png", "hero portrait")
	check_eq(CharImport.out_path("portrait_shadow_king"), "res://art/ui/shadow_king_portrait.png", "king portrait")
	check_eq(CharImport.out_path("face_seer"), "res://art/ui/faces/seer.png", "face")
	check_eq(CharImport.out_path("people_seer"), "res://art/sheets/people_seer.png", "villager")
	check_eq(CharImport.out_path("hero_walk_down"), "res://art/sheets/candidates/hero_top_walk_down.png", "hero test")


func test_every_prompt_has_a_home() -> void:
	var a := CharImport.assets()
	var looks := {}
	for p in JSON.parse_string(FileAccess.get_file_as_string("res://rules/data/people.json"))["people"]:
		looks[p["look"]] = true
	for f in DirAccess.get_files_at(CharImport.GEMINI + "prompts"):
		var n := f.get_basename()
		check(CharImport.out_path(n) != "", n + " has an output")
		if n.begins_with("people_"):
			check(not ArtSheet.meta(n).is_empty(), n + " has a sheet to write over")
	for look in looks:
		check(FileAccess.file_exists(CharImport.GEMINI + "prompts/people_%s.txt" % look), "a sprite prompt for " + look)
		check(FileAccess.file_exists(CharImport.GEMINI + "prompts/face_%s.txt" % look), "a face prompt for " + look)
	check(a["portraits"].has("portrait_hero") and a["portraits"].has("portrait_shadow_king"), "both portraits sized")


func test_import_one_writes_and_marks_painted() -> void:
	var keep := FileAccess.get_file_as_string(CharImport.PAINTED) if FileAccess.file_exists(CharImport.PAINTED) else ""
	var src := OS.get_user_data_dir() + "/zz_face.png"
	_picture(1, 200, 200).save_png(src)
	var r := CharImport.import_one(src, "face_zz_test", CharImport.assets())
	check_eq(r, "res://art/ui/faces/zz_test.png", "written to the faces folder")
	var img := Image.load_from_file(ProjectSettings.globalize_path(r))
	check(img != null and img.get_size() == Vector2i(64, 64), "64x64 face")
	check(r in CharImport.painted(), "listed in painted.json")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(r))
	DirAccess.remove_absolute(src)
	if keep == "":
		DirAccess.remove_absolute(ProjectSettings.globalize_path(CharImport.PAINTED))
	else:
		var f := FileAccess.open(CharImport.PAINTED, FileAccess.WRITE)
		f.store_string(keep)
		f.close()


func test_hero_compare_picture() -> void:
	var hc = load("res://tools/hero_compare.gd")
	var today: Image = hc.today()
	check_eq(today.get_size(), Vector2i(ArtSheet.cell("hero_top").x * 4, ArtSheet.cell("hero_top").y), "4 walk frames")
	check(not today.is_invisible(), "today's hero is in it")
	var cmp: Image = hc.compare(today, today)
	check(cmp.get_width() >= today.get_width() * 4 and cmp.get_height() > today.get_height() * 8, "1x and 4x rows: %s" % cmp.get_size())


## A made-up Gemini "animate" GIF: a tall figure on green whose head slides 1 px a frame and back.
func _moving_gif(n := 6) -> String:
	var dir := OS.get_user_data_dir() + "/zz_gif/"
	DirAccess.make_dir_recursive_absolute(dir)
	for i in n:
		var img := Image.create(160, 120, false, Image.FORMAT_RGBA8)
		img.fill(Color(0, 1, 0))
		img.fill_rect(Rect2i(60, 50, 40, 70), Color(0.4, 0.2, 0.5))             # body to the bottom edge
		img.fill_rect(Rect2i(68 + mini(i, n - i), 20, 24, 30), SKIN)             # head
		img.save_png(dir + "f%d.png" % i)
	var gif := dir + "face_zz_test.gif"
	OS.execute(CharImport.ffmpeg(), ["-v", "error", "-y", "-framerate", "5", "-i", dir + "f%d.png", gif])
	return gif


func _rm_gif_dir() -> void:
	var dir := OS.get_user_data_dir() + "/zz_gif/"
	for f in DirAccess.get_files_at(dir):
		DirAccess.remove_absolute(dir + f)
	DirAccess.remove_absolute(dir)


func test_moving_face_frames() -> void:
	if CharImport.ffmpeg() == "":
		print("  (skipped: no ffmpeg)")
		return
	var got := CharImport.face_frames(_moving_gif(), Vector2i(64, 64))
	_rm_gif_dir()
	check(not got.has("error"), "read the GIF: %s" % got.get("error", ""))
	var fr: Array = got["frames"]
	check_eq(fr.size(), 6, "6 frames (the ends nearly match, so no ping-pong)")
	check(is_equal_approx(float(got["fps"]), 5.0), "keeps its fps: %s" % got["fps"])
	for f in fr:
		check_eq((f as Image).get_size(), Vector2i(64, 64), "64x64 frames")
	var f0: Image = fr[0]
	check(f0.get_pixel(0, 0).a == 0.0, "green keyed out")
	var skin := 0
	for y in 64:
		for x in 64:
			skin += 1 if f0.get_pixel(x, y).a > 0.5 and f0.get_pixel(x, y).r > 0.6 else 0
	check(skin > 64 * 64 / 10, "cut round the head, not the whole figure: %d skin pixels" % skin)
	check(CharImport.difference(fr[1], fr[0]) > 0.0, "it moves")


func test_corner_key_and_loop() -> void:
	var g := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	g.fill(Color(0, 1, 0))
	var m := Image.create(8, 8, false, Image.FORMAT_RGBA8)
	m.fill(Color(1, 0, 1))
	check(CharImport.corner_key(g) == "green" and CharImport.corner_key(m) == "magenta", "key from the corners")
	var near: Array[Image] = []
	var far: Array[Image] = []
	for i in 8:
		var a := Image.create(4, 4, false, Image.FORMAT_RGBA8)
		a.fill(Color(0.5, 0.5, 0.5 + i * 0.002))
		near.append(a)
		var b := Image.create(4, 4, false, Image.FORMAT_RGBA8)
		b.fill(Color(i / 8.0, 0, 0))
		far.append(b)
	var n := CharImport.seamless(near)
	check(n.size() == 8 and n[7].get_pixel(0, 0).b < near[7].get_pixel(0, 0).b, "close ends: the last frames fade into the first")
	var f := CharImport.seamless(far)
	check(f.size() == 14 and f[13].get_pixel(0, 0).is_equal_approx(far[1].get_pixel(0, 0)), "far ends: ping-pong (8 + 6)")
	var many: Array[Image] = []
	for i in 50:
		many.append(g)
	check_eq(CharImport.cap(many).size(), CharImport.MAX_FRAMES, "capped")


func test_import_moving_face_writes_strip_json_and_still() -> void:
	if CharImport.ffmpeg() == "":
		print("  (skipped: no ffmpeg)")
		return
	var keep := FileAccess.get_file_as_string(CharImport.PAINTED) if FileAccess.file_exists(CharImport.PAINTED) else ""
	var r := CharImport.import_one(_moving_gif(), "face_zz_test", CharImport.assets())
	_rm_gif_dir()
	check_eq(r, "res://art/ui/faces/zz_test_anim.png", "the strip")
	var strip := Image.load_from_file(ProjectSettings.globalize_path(r))
	var meta = JSON.parse_string(FileAccess.get_file_as_string("res://art/ui/faces/zz_test_anim.json"))
	check(meta is Dictionary and int(meta["frames"]) == 6 and is_equal_approx(float(meta["fps"]), 5.0), "json: %s" % meta)
	check(meta is Dictionary and meta["size"] == [64.0, 64.0], "json size 64x64")
	check(strip != null and strip.get_size() == Vector2i(64 * 6, 64), "a strip of 6 frames side by side")
	var still := Image.load_from_file(ProjectSettings.globalize_path("res://art/ui/faces/zz_test.png"))
	check(still != null and still.get_data() == strip.get_region(Rect2i(0, 0, 64, 64)).get_data(), "the still is frame 0")
	check(r in CharImport.painted(), "listed in painted.json")
	for p in ["zz_test_anim.png", "zz_test_anim.json", "zz_test.png"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path("res://art/ui/faces/" + p))
	if keep == "":
		DirAccess.remove_absolute(ProjectSettings.globalize_path(CharImport.PAINTED))
	else:
		var f := FileAccess.open(CharImport.PAINTED, FileAccess.WRITE)
		f.store_string(keep)
		f.close()
