class_name GloomLut
extends RefCounted
## The darkening world as a palette swap (docs/teen/art/README.md, "Darkening world"): Shadowfall 32
## and the 4 gloom stages, each a palette -> palette remap. Same rule as spikes/art/sf_art.py gloom_lut:
## each stage moves a colour one step down its own ramp (ink moves half as fast); at stage 3 moss,
## earth and water drop into the ink ramp. Accents (light, ember highs, shadow) never change.
## The shader (palette_swap.gdshader) reads image(): 32 x 4, column = palette index, row = stage.

const RAMPS := {
	"ink": ["0b0a12", "1a1626", "2b2540", "463d5e", "6b6187", "9c93b0", "d6d0e0", "f4f1ea"],
	"moss": ["12261f", "1f4031", "2f6142", "4f8a4b", "8bbd5a"],
	"earth": ["2a1b17", "4a2f25", "74482f", "a8703f", "d9a95f"],
	"water": ["0f1d33", "1b3557", "2c5a85", "4a8fb8", "8fd0e0"],
	"ember": ["3d0f1f", "7a1c2e", "c23a3a", "f0784a"],
	"light": ["f7c64a", "fff2a8"],
	"shadow": ["2a0f3d", "5a1f78", "a04ce0"],
}
const STAGES := 4

static var _image: Image
static var _texture: ImageTexture


## The 32 colours, in ramp order (ink first). Column i of the LUT.
static func palette() -> PackedStringArray:
	var out := PackedStringArray()
	for ramp in RAMPS.values():
		out.append_array(ramp)
	return out


static func is_accent(hex: String) -> bool:
	return hex in RAMPS["light"] or hex in RAMPS["ember"].slice(2) or hex in RAMPS["shadow"]


## The palette colour `hex` becomes at `stage` (0..3).
static func swap(hex: String, stage: int) -> String:
	for ramp_name in RAMPS:
		var ramp: Array = RAMPS[ramp_name]
		var i := ramp.find(hex)
		if i < 0:
			continue
		if stage <= 0 or is_accent(hex):
			return hex
		if stage >= 3 and ramp_name in ["moss", "earth", "water"]:
			return RAMPS["ink"][maxi(1, i)]
		if ramp_name == "ink":
			return ramp[maxi(0, i - (stage + 1) / 2)]
		return ramp[maxi(0, i - stage)]
	return hex


static func image() -> Image:
	if _image == null:
		var pal := palette()
		_image = Image.create(pal.size(), STAGES, false, Image.FORMAT_RGBA8)
		for s in STAGES:
			for i in pal.size():
				_image.set_pixel(i, s, Color(swap(pal[i], s)))
	return _image


static func texture() -> ImageTexture:
	if _texture == null:
		_texture = ImageTexture.create_from_image(image())
	return _texture


## What the shader does to any colour, on the CPU (tests compare the two): find the nearest palette
## colour and move by the same step it moves. Palette colours land exactly on their swap; off-palette
## placeholder colours darken by the same amount.
static func remap(c: Color, stage: int) -> Color:
	if stage <= 0 or c.a <= 0.0:
		return c
	var img := image()
	var best := 0
	var bd := INF
	for i in img.get_width():
		var p := img.get_pixel(i, 0)
		var d := Vector3(c.r - p.r, c.g - p.g, c.b - p.b).length_squared()
		if d < bd:
			bd = d
			best = i
	var from := img.get_pixel(best, 0)
	var to := img.get_pixel(best, clampi(stage, 0, STAGES - 1))
	return Color(clampf(c.r + to.r - from.r, 0, 1), clampf(c.g + to.g - from.g, 0, 1),
		clampf(c.b + to.b - from.b, 0, 1), c.a)
