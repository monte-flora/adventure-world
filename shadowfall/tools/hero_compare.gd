extends SceneTree
## pixi run hero-compare: today's hero walking down vs the Gemini candidate (art/sheets/candidates/
## hero_top_walk_down.png, from `pixi run gemini-next --set characters hero_walk_down`), into
## art/sheets/candidates/hero_compare.png on the realm's dusk grass. Top row 1x (left today, right Gemini);
## then today at 4x; then Gemini at 4x.

const CAND := "res://art/sheets/candidates/hero_top_walk_down.png"
const OUT := "res://art/sheets/candidates/hero_compare.png"
const BG := Color("3b4a2c")         # about the colour of Emberhold's grass at dusk
const PAD := 8


static func today() -> Image:
	var img := Image.load_from_file(ProjectSettings.globalize_path(ArtSheet.DIR + ArtSheet.meta("hero_top")["image"]))
	img.convert(Image.FORMAT_RGBA8)
	var c := ArtSheet.cell("hero_top")
	var out := Image.create(c.x * 4, c.y, false, Image.FORMAT_RGBA8)
	for i in 4:
		out.blit_rect(img, ArtSheet.region("hero_top", "walk_down", i), Vector2i(i * c.x, 0))
	return out


static func big(img: Image, k: int) -> Image:
	var out := img.duplicate() as Image
	out.resize(img.get_width() * k, img.get_height() * k, Image.INTERPOLATE_NEAREST)
	return out


## The comparison picture of two walk strips.
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


func _init() -> void:
	var cand := Image.load_from_file(ProjectSettings.globalize_path(CAND))
	if cand == null or cand.is_empty():
		print("hero-compare: no candidate yet. Make it: pixi run gemini-next --set characters hero_walk_down")
		quit(1)
		return
	cand.convert(Image.FORMAT_RGBA8)
	compare(today(), cand).save_png(ProjectSettings.globalize_path(OUT))
	print("hero-compare: wrote " + ProjectSettings.globalize_path(OUT))
	quit(0)
