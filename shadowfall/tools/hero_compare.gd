extends SceneTree
## pixi run hero-compare: the drawn map hero vs the Gemini one, for every row with a Gemini picture
## (art/sheets/candidates/hero_top_<anim>.png, from `pixi run gemini-next --set characters hero_<anim>`), into
## art/sheets/candidates/hero_compare.png on the realm's dusk grass. Per row, top to bottom: 1x (left drawn,
## right Gemini); then drawn at 4x; then Gemini at 4x. "Drawn" is the sheet from before the first Gemini row
## (CharImport.DRAWN), or today's hero_top.png when there is none yet.

const OUT := "res://art/sheets/candidates/hero_compare.png"
const BG := Color("3b4a2c")         # about the colour of Emberhold's grass at dusk
const PAD := 8


## The drawn frames of one anim, side by side.
static func today(anim := "walk_down") -> Image:
	var path := ProjectSettings.globalize_path(CharImport.DRAWN)
	if not FileAccess.file_exists(path):
		path = ProjectSettings.globalize_path(ArtSheet.DIR + ArtSheet.meta("hero_top")["image"])
	var img := Image.load_from_file(path)
	img.convert(Image.FORMAT_RGBA8)
	var c := ArtSheet.cell("hero_top")
	var n := int(ArtSheet.meta("hero_top")["anims"][anim]["frames"])
	var out := Image.create(c.x * n, c.y, false, Image.FORMAT_RGBA8)
	for i in n:
		out.blit_rect(img, ArtSheet.region("hero_top", anim, i), Vector2i(i * c.x, 0))
	return out


static func big(img: Image, k: int) -> Image:
	var out := img.duplicate() as Image
	out.resize(img.get_width() * k, img.get_height() * k, Image.INTERPOLATE_NEAREST)
	return out


## The comparison picture of two strips.
static func compare(a: Image, b: Image) -> Image:
	var a4 := big(a, 4)
	var b4 := big(b, 4)
	var w := maxi(a.get_width() + b.get_width() + PAD, maxi(a4.get_width(), b4.get_width())) + 2 * PAD
	var h := maxi(a.get_height(), b.get_height()) + a4.get_height() + b4.get_height() + 4 * PAD
	var out := Image.create(w, h, false, Image.FORMAT_RGBA8)
	out.fill(BG)
	var y := PAD
	out.blend_rect(a, Rect2i(Vector2i.ZERO, a.get_size()), Vector2i(PAD, y))
	out.blend_rect(b, Rect2i(Vector2i.ZERO, b.get_size()), Vector2i(2 * PAD + a.get_width(), y))
	y += maxi(a.get_height(), b.get_height()) + PAD
	out.blend_rect(a4, Rect2i(Vector2i.ZERO, a4.get_size()), Vector2i(PAD, y))
	y += a4.get_height() + PAD
	out.blend_rect(b4, Rect2i(Vector2i.ZERO, b4.get_size()), Vector2i(PAD, y))
	return out


## Every row's comparison stacked, in hero_top.json's order ({anim: Image} strips).
static func compare_all(strips: Dictionary) -> Image:
	var parts: Array[Image] = []
	var w := 0
	var h := 0
	for anim in ArtSheet.meta("hero_top")["anims"]:
		if strips.has(anim):
			var p := compare(today(anim), strips[anim])
			parts.append(p)
			w = maxi(w, p.get_width())
			h += p.get_height()
	var out := Image.create(maxi(w, 1), maxi(h, 1), false, Image.FORMAT_RGBA8)
	out.fill(BG)
	var y := 0
	for p in parts:
		out.blit_rect(p, Rect2i(Vector2i.ZERO, p.get_size()), Vector2i(0, y))
		y += p.get_height()
	return out


func _init() -> void:
	var strips := CharImport.hero_strips()
	if strips.is_empty():
		print("hero-compare: no Gemini hero rows yet. Make one: pixi run gemini-next --set characters hero_walk_down")
		quit(1)
		return
	compare_all(strips).save_png(ProjectSettings.globalize_path(OUT))
	print("hero-compare: %s (top to bottom) in %s" % [", ".join(strips.keys()), ProjectSettings.globalize_path(OUT)])
	quit(0)
