class_name ArtCheck
## The art checker: every PNG under res://art uses only Shadowfall 32 colours (alpha 0 or 255), and
## every sheet's image is a whole number of cells with each animation inside it.
## Run: sh shadowfall/tools/run_tests.sh --only=art

const ROOT := "res://art"


static func palette() -> Dictionary:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "/palette.json"))
	var out := {}
	for h in doc["hex"]:
		out[Color(h).to_rgba32() | 0xff] = true
	return out


static func pngs(dir := ROOT, out := PackedStringArray()) -> PackedStringArray:
	for d in DirAccess.get_directories_at(dir):
		if d != "src" and d != "tests":
			pngs(dir.path_join(d), out)
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".png"):
			out.append(dir.path_join(f))
	return out


static func image(path: String) -> Image:
	var tex: Texture2D = load(path)
	if tex == null:
		return null
	var img := tex.get_image()
	if img.is_compressed():
		img.decompress()
	img.convert(Image.FORMAT_RGBA8)
	return img


## Problems with one PNG's colours (empty = fine).
static func check_png(path: String, pal: Dictionary) -> PackedStringArray:
	var img := image(path)
	if img == null:
		return PackedStringArray(["%s: can't load" % path])
	return check_image(img, path, pal)


static func check_image(img: Image, path: String, pal: Dictionary) -> PackedStringArray:
	var bad := PackedStringArray()
	img.convert(Image.FORMAT_RGBA8)
	var data := img.get_data()
	var w := img.get_width()
	for i in range(0, data.size(), 4):
		var a := data[i + 3]
		if a == 0:
			continue
		var rgba := (data[i] << 24) | (data[i + 1] << 16) | (data[i + 2] << 8) | 0xff
		if a != 255 or not pal.has(rgba):
			var p := i / 4
			bad.append("%s: pixel %d,%d is %s (alpha %d), not a Shadowfall 32 colour"
				% [path, p % w, p / w, Color.hex(rgba).to_html(false), a])
			if bad.size() >= 3:
				break
	return bad


## Problems with one sheet's cells (empty = fine).
static func check_sheet(name: String) -> PackedStringArray:
	var bad := PackedStringArray()
	var m := ArtSheet.meta(name)
	for k in ["image", "cell", "origin", "anims"]:
		if not m.has(k):
			return PackedStringArray(["%s.json: no \"%s\"" % [name, k]])
	var c := ArtSheet.cell(name)
	var img := image(ArtSheet.DIR + m["image"])
	if img == null:
		return PackedStringArray(["%s: can't load %s" % [name, m["image"]]])
	if img.get_width() % c.x or img.get_height() % c.y:
		bad.append("%s: %dx%d is not a whole number of %dx%d cells" % [name, img.get_width(), img.get_height(), c.x, c.y])
	var cols := img.get_width() / c.x
	var rows := img.get_height() / c.y
	for anim in m["anims"]:
		var a: Dictionary = m["anims"][anim]
		if int(a["frames"]) < 1 or int(a["col"]) + int(a["frames"]) > cols or int(a["row"]) >= rows:
			bad.append("%s: anim %s runs outside the sheet" % [name, anim])
		elif img.get_region(ArtSheet.region(name, anim, 0)).is_invisible():
			bad.append("%s: anim %s frame 0 is empty" % [name, anim])
	return bad


static func check_all() -> PackedStringArray:
	var bad := PackedStringArray()
	var pal := palette()
	if pal.size() != 32:
		bad.append("palette.json has %d colours, want 32" % pal.size())
	for p in pngs():
		bad.append_array(check_png(p, pal))
	for n in ArtSheet.names():
		bad.append_array(check_sheet(n))
	return bad
