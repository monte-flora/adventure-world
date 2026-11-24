class_name CharImport
## Turns Gemini character pictures (art/gemini/README.txt; `pixi run import-characters`) into game art:
##   portrait_hero, portrait_shadow_king -> art/ui/hero_portrait.png, shadow_king_portrait.png
##   face_<look>                         -> art/ui/faces/<look>.png (the dialogue box's face)
##   people_<look>                       -> art/sheets/people_<look>.png: 1 idle + 1 "breath" frame fill
##                                          every row of the sheet; its .json is kept as it is
##   hero_walk_down                      -> art/sheets/candidates/hero_top_walk_down.png (a test only)
## Each picture is keyed off its flat background (magenta, or green where assets.json says), cut into its
## figures, scaled (one scale for all frames) and stood on the sheet's origin. Everything written is listed
## in art/gemini/painted.json, so ArtCheck lets its full colour through (like the realm's props).

const GEMINI := "res://art/gemini/"
const ART := "res://art/"
const PAINTED := GEMINI + "painted.json"


static func assets() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(GEMINI + "assets.json"))


## How green a colour is: 1 for #00FF00, 0 when red or blue is as strong.
static func greenness(c: Color) -> float:
	return clampf(c.g - maxf(c.r, c.b), 0.0, 1.0)


## The background -> transparent. key is "magenta" (realm's ArtImport.key_out) or "green".
static func key_out(img: Image, key := "magenta") -> void:
	if key != "green":
		ArtImport.key_out(img)
		return
	img.convert(Image.FORMAT_RGBA8)
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			var m := greenness(c)
			if m >= 0.5:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
			elif m > 0.1:                       # despill: pull green down to the others
				c.g -= m
				c.a *= clampf((0.5 - m) / 0.4, 0.0, 1.0)
				img.set_pixel(x, y, c)


## The figures side by side in a keyed-out picture, left to right, each trimmed. Figures are split at
## empty columns; specks are dropped. If that doesn't give `want` figures (want 0 = any), the picture is
## cut into `want` equal columns instead.
static func figures(img: Image, want := 0) -> Array[Image]:
	var w := img.get_width()
	var h := img.get_height()
	var runs: Array[Vector2i] = []             # [start x, end x)
	var start := -1
	for x in w + 1:
		var used := false
		if x < w:
			for y in h:
				if img.get_pixel(x, y).a > 0.5:
					used = true
					break
		if used and start < 0:
			start = x
		elif not used and start >= 0:
			if x - start >= maxi(2, w / 40):
				runs.append(Vector2i(start, x))
			start = -1
	if want > 0 and runs.size() != want:
		runs.clear()
		for i in want:
			runs.append(Vector2i(i * w / want, (i + 1) * w / want))
	var out: Array[Image] = []
	for r in runs:
		var part := img.get_region(Rect2i(r.x, 0, r.y - r.x, h))
		if part.get_used_rect().size.x > 0:
			out.append(ArtImport.trim(part))
	return out


## Scales every frame by one factor so the biggest fits inside `box`.
static func fit_all(frames: Array[Image], box: Vector2i) -> Array[Image]:
	var mw := 1
	var mh := 1
	for f in frames:
		mw = maxi(mw, f.get_width())
		mh = maxi(mh, f.get_height())
	var s := minf(float(box.x) / mw, float(box.y) / mh)
	var out: Array[Image] = []
	for f in frames:
		out.append(ArtImport.fit(f, Vector2i(maxi(1, roundi(f.get_width() * s)), maxi(1, roundi(f.get_height() * s)))))
	return out


## Draws `frame` onto `sheet` so its bottom middle stands on `foot` (sheet pixels).
static func stand(sheet: Image, frame: Image, foot: Vector2i) -> void:
	var at := foot - Vector2i(frame.get_width() / 2, frame.get_height())
	sheet.blend_rect(frame, Rect2i(Vector2i.ZERO, frame.get_size()), at)


## A people_<look> sheet in the layout its .json already has (so overworld/person.gd needs no change).
## Idle rows: idle, idle, breath, breath. Walk rows: idle, breath, idle, breath with a 1-pixel bob.
## Every row faces the camera (Gemini draws one view); side rows are flipped by the game as before.
static func people_sheet(frames: Array[Image], meta: Dictionary) -> Image:
	var c := Vector2i(int(meta["cell"][0]), int(meta["cell"][1]))
	var o := Vector2i(int(meta["origin"][0]), int(meta["origin"][1]))
	var cols := 0
	var rows := 0
	for a in meta["anims"].values():
		cols = maxi(cols, int(a["col"]) + int(a["frames"]))
		rows = maxi(rows, int(a["row"]) + 1)
	var sheet := Image.create(cols * c.x, rows * c.y, false, Image.FORMAT_RGBA8)
	var breath := frames[1] if frames.size() > 1 else frames[0]
	for anim in meta["anims"]:
		var a: Dictionary = meta["anims"][anim]
		var walk := str(anim).begins_with("walk")
		for i in int(a["frames"]):
			var f: Image = (breath if i % 2 == 1 else frames[0]) if walk else (breath if i >= 2 else frames[0])
			var cell := Vector2i((int(a["col"]) + i) * c.x, int(a["row"]) * c.y)
			stand(sheet, f, cell + o - Vector2i(0, 1 if walk and i % 2 == 1 else 0))
	return sheet


## A portrait or face: the figure fit into `size`, stood at the bottom middle of a picture that size.
static func portrait(img: Image, size: Vector2i) -> Image:
	var f := ArtImport.fit(ArtImport.trim(img), size)
	var out := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	stand(out, f, Vector2i(size.x / 2, size.y))
	return out


## Where a prompt's picture goes (res://art/...), or "" if the name is unknown.
static func out_path(name: String) -> String:
	if name.begins_with("portrait_"):
		return ART + "ui/" + name.trim_prefix("portrait_") + "_portrait.png"
	if name.begins_with("face_"):
		return ART + "ui/faces/" + name.trim_prefix("face_") + ".png"
	if name.begins_with("people_"):
		return ART + "sheets/" + name + ".png"
	if name == "hero_walk_down":
		return ART + "sheets/candidates/hero_top_walk_down.png"
	return ""


## Makes one picture's game art from `src`. Returns the path written, or "! why".
static func import_one(src: String, name: String, a: Dictionary) -> String:
	var dst := out_path(name)
	if dst == "":
		return "! no idea where %s goes" % name
	var img := Image.load_from_file(src)
	if img == null or img.is_empty():
		return "! can't read " + src
	var look := name.trim_prefix("face_").trim_prefix("people_")
	key_out(img, "green" if look in a.get("green_key", []) or name in a.get("green_key", []) else "magenta")
	var out: Image
	if name.begins_with("portrait_") or name.begins_with("face_"):
		var s: Array = a["portraits"].get(name, a["face_size"])
		out = portrait(img, Vector2i(int(s[0]), int(s[1])))
	elif name.begins_with("people_"):
		var meta := ArtSheet.meta(name)
		if meta.is_empty():
			return "! no art/sheets/%s.json: a new look needs its sheet made first" % name
		var b: Array = a["people_box"].get(look, a["people_box"]["default"])
		var fr := figures(img)
		if fr.is_empty():
			return "! nothing left after keying out " + src
		if fr.size() > 2:
			fr = figures(img, 2)
		out = people_sheet(fit_all(fr, Vector2i(int(b[0]), int(b[1]))), meta)
	else:
		var h: Dictionary = a["hero_walk_down"]
		var meta := ArtSheet.meta(str(h["like"]))
		var c := Vector2i(int(meta["cell"][0]), int(meta["cell"][1]))
		var o := Vector2i(int(meta["origin"][0]), int(meta["origin"][1]))
		var fr := fit_all(figures(img, int(h["frames"])), Vector2i(int(h["box"][0]), int(h["box"][1])))
		out = Image.create(c.x * fr.size(), c.y, false, Image.FORMAT_RGBA8)
		for i in fr.size():
			stand(out, fr[i], Vector2i(i * c.x, 0) + o)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dst.get_base_dir()))
	out.save_png(ProjectSettings.globalize_path(dst))
	mark_painted(dst)
	return dst


## Lists `path` in painted.json (ArtCheck skips the palette rule for these).
static func mark_painted(path: String) -> void:
	var files := painted()
	if path in files:
		return
	files.append(path)
	files.sort()
	var f := FileAccess.open(ProjectSettings.globalize_path(PAINTED), FileAccess.WRITE)
	f.store_string(JSON.stringify({"about": "Art made from Gemini pictures (tools/char_import.gd writes this). ArtCheck lets these use any colour.", "files": files}, " ", false) + "\n")
	f.close()


static func painted() -> PackedStringArray:
	var p := ProjectSettings.globalize_path(PAINTED)
	if not FileAccess.file_exists(p):
		return PackedStringArray()
	var d = JSON.parse_string(FileAccess.get_file_as_string(p))
	return PackedStringArray(d.get("files", [])) if d is Dictionary else PackedStringArray()


## Imports every picture in art/gemini/in/ (or just `only`). One log line each; errors start with "!".
static func run(only := PackedStringArray()) -> PackedStringArray:
	var a := assets()
	var log := PackedStringArray()
	var dir := ProjectSettings.globalize_path(GEMINI + "in/")
	if not DirAccess.dir_exists_absolute(dir):
		return log
	var files := DirAccess.get_files_at(dir)
	files.sort()
	for f in files:
		var n := f.get_basename()
		if f.get_extension().to_lower() not in ["png", "jpg", "jpeg", "webp"] or (only.size() > 0 and n not in only):
			continue
		var r := import_one(dir + f, n, a)
		log.append(r if r.begins_with("!") else "%s <- %s" % [r.trim_prefix("res://"), f])
	return log
