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
