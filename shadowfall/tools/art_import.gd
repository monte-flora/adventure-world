class_name ArtImport
## Turns Gemini pictures into game art (realm/gemini/README.txt; `pixi run import-art` runs import_art.gd):
##   props:  magenta key-out to alpha (+ despill, hard 1-bit edges), trim, scale to assets.json size,
##           write realm/props/<name>.png + <name>.json (footprint, base y, anchor, lights, front rows)
##   ground: scale to 256x256, make it tile (offset by half, blend the edges), realm/ground/<name>.png
## Everything is static so tests can call each step on a made-up Image.

const GEMINI := "res://realm/gemini/"
const PROPS := "res://realm/props/"
const GROUND := "res://realm/ground/"
const TEX := 256                       # ground texture size in game pixels (8 x 8 squares)
const BLEND := 0.25                    # share of the texture blended at each edge


static func assets() -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(GEMINI + "assets.json"))


## How magenta a colour is: 1 for #FF00FF, 0 when green is as strong as red or blue.
static func magentaness(c: Color) -> float:
	return clampf(minf(c.r, c.b) - c.g, 0.0, 1.0)


## Magenta -> transparent. Near-magenta edges get a partial alpha and lose their pink tint.
static func key_out(img: Image) -> void:
	img.convert(Image.FORMAT_RGBA8)
	for y in img.get_height():
		for x in img.get_width():
			var c := img.get_pixel(x, y)
			var m := magentaness(c)
			if m >= 0.5:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
				continue
			if m > 0.1:                          # despill: pull red and blue down to green
				var k := m
				c.r -= k
				c.b -= k
				c.a *= clampf((0.5 - m) / 0.4, 0.0, 1.0)
			img.set_pixel(x, y, c)


## Crops to the visible pixels (alpha > 0.1). Returns the cropped image.
static func trim(img: Image) -> Image:
	var r := img.get_used_rect()
	return img.get_region(r) if r.size.x > 0 else img


## Scales to fit inside `box` (keeps its shape), premultiplied so no magenta bleeds into the edges;
## alpha ends hard (0 or 1) like the rest of the pixel art.
static func fit(img: Image, box: Vector2i) -> Image:
	var s := minf(float(box.x) / img.get_width(), float(box.y) / img.get_height())
	var w := maxi(1, roundi(img.get_width() * s))
	var h := maxi(1, roundi(img.get_height() * s))
	var pm := img.duplicate() as Image
	for y in pm.get_height():
		for x in pm.get_width():
			var c := pm.get_pixel(x, y)
			pm.set_pixel(x, y, Color(c.r * c.a, c.g * c.a, c.b * c.a, c.a))
	pm.resize(w, h, Image.INTERPOLATE_CUBIC)
	for y in h:
		for x in w:
			var c := pm.get_pixel(x, y)
			if c.a < 0.5:
				pm.set_pixel(x, y, Color(0, 0, 0, 0))
			else:
				pm.set_pixel(x, y, Color(clampf(c.r / c.a, 0, 1), clampf(c.g / c.a, 0, 1), clampf(c.b / c.a, 0, 1), 1.0))
	return pm


## The prop's JSON from its size and assets.json entry. Rects are [x, y, w, h] in the PNG's pixels.
static func prop_meta(name: String, size: Vector2i, d: Dictionary, placeholder := false) -> Dictionary:
	var out := {"name": name, "size": [size.x, size.y], "placeholder": placeholder, "keep": false,
		"front": int(d.get("front", 0)), "lights": []}
	var f: Array = d.get("foot", [])
	if f.size() == 4:
		var r := Rect2i(roundi(f[0] * size.x), roundi(f[1] * size.y), maxi(1, roundi(f[2] * size.x)), maxi(1, roundi(f[3] * size.y)))
		out["foot"] = [r.position.x, r.position.y, r.size.x, r.size.y]
		out["anchor"] = [r.position.x + r.size.x / 2, r.end.y]
	else:
		out["foot"] = []
		out["anchor"] = [size.x / 2, size.y]
	out["base"] = out["anchor"][1]
	for l in d.get("lights", []):
		out["lights"].append([roundi(l[0] * size.x), roundi(l[1] * size.y), int(l[2])])
	return out


## A picture tiles with no seams: each axis is blended with itself shifted by half near the edges.
static func make_seamless(img: Image) -> Image:
	var out := img.duplicate() as Image
	for axis in 2:
		var src := out.duplicate() as Image
		var w := src.get_width()
		var h := src.get_height()
		var n := w if axis == 0 else h
		for y in h:
			for x in w:
				var t := (x if axis == 0 else y) + 0.5
				var e := minf(t, n - t) / (n * BLEND)        # 0 at the edges, 1 inside
				var k := smoothstep(0.0, 1.0, e)
				var sx := (x + w / 2) % w if axis == 0 else x
				var sy := (y + h / 2) % h if axis == 1 else y
				out.set_pixel(x, y, src.get_pixel(sx, sy).lerp(src.get_pixel(x, y), k))
	return out


static func import_prop(src: String, name: String, d: Dictionary, placeholder := false) -> Dictionary:
	var img := Image.load_from_file(src)
	if img == null or img.is_empty():
		return {"error": "can't read " + src}
	key_out(img)
	img = trim(img)
	var box: Array = d.get("size", [64, 64])
	img = fit(img, Vector2i(int(box[0]), int(box[1])))
	var meta := prop_meta(name, img.get_size(), d, placeholder)
	var json_path := ProjectSettings.globalize_path(PROPS + name + ".json")
	if FileAccess.file_exists(json_path):               # hand-tweaked: keep foot, anchor, lights, front
		var old = JSON.parse_string(FileAccess.get_file_as_string(json_path))
		if old is Dictionary and old.get("keep", false):
			for k in ["foot", "anchor", "base", "lights", "front", "keep"]:
				if old.has(k):
					meta[k] = old[k]
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(PROPS))
	img.save_png(ProjectSettings.globalize_path(PROPS + name + ".png"))
	var f := FileAccess.open(json_path, FileAccess.WRITE)
	f.store_string(JSON.stringify(meta, " ", false) + "\n")
	f.close()
	return meta


static func import_ground(src: String, name: String) -> String:
	var img := Image.load_from_file(src)
	if img == null or img.is_empty():
		return "can't read " + src
	img.convert(Image.FORMAT_RGB8)
	var side := mini(img.get_width(), img.get_height())
	img = img.get_region(Rect2i(0, 0, side, side))
	img.resize(TEX, TEX, Image.INTERPOLATE_LANCZOS)
	img = make_seamless(img)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(GROUND))
	img.save_png(ProjectSettings.globalize_path(GROUND + name + ".png"))
	return ""


## The picture for an asset in a folder of realm/gemini/ (any of png, jpg, webp), or "".
static func source(folder: String, file_stem: String) -> String:
	for ext in ["png", "jpg", "jpeg", "webp"]:
		var p := ProjectSettings.globalize_path(GEMINI + folder + "/" + file_stem + "." + ext)
		if FileAccess.file_exists(p):
			return p
	return ""


## A ground texture's picture name: grass -> ground_grass; a land's own (wintermarch_ground_snow) keeps its name.
static func ground_stem(n: String) -> String:
	return n if "_ground_" in n else "ground_" + n


## Imports everything in realm/gemini/in/; with placeholders, also the placeholder of each asset that
## has no picture in in/ yet. Returns one line per asset done (errors start with "!").
static func run(placeholders := false, only := PackedStringArray()) -> PackedStringArray:
	var a := assets()
	var log := PackedStringArray()
	for n in a["ground"]:
		if only.size() > 0 and n not in only:
			continue
		var src := source("in", ground_stem(n))
		if src == "" and placeholders:
			src = source("placeholder", ground_stem(n))
		if src != "":
			var err := import_ground(src, n)
			log.append(("! " + err) if err != "" else "ground %s <- %s" % [n, src.get_file()])
	for n in a["props"]:
		if only.size() > 0 and n not in only:
			continue
		var src := source("in", n)
		var ph := false
		if src == "" and placeholders:
			src = source("placeholder", n)
			ph = true
		if src != "":
			var m := import_prop(src, n, a["props"][n], ph)
			log.append(("! " + m.error) if m.has("error") else "prop %s %dx%d <- %s%s" % [n, m.size[0], m.size[1], src.get_file(), " (placeholder)" if ph else ""])
	return log
