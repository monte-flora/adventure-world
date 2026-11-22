class_name UiStyle
## The look every screen shares: the Shadowfall 32 colours the UI uses, our pixel font
## (assets/fonts/ from the font PR; copies in ui/fonts/ so the web export has them), the text-box frame.
## Font sizes are whole multiples of each font's line height, so text stays sharp at 960×540 ×1 and ×2.

const INK0 := Color("0b0a12")
const INK1 := Color("1a1626")
const INK2 := Color("2b2540")
const INK3 := Color("463d5e")
const INK4 := Color("6b6187")
const INK5 := Color("9c93b0")
const INK6 := Color("d6d0e0")
const INK7 := Color("f4f1ea")
const LIGHT0 := Color("f7c64a")
const LIGHT1 := Color("fff2a8")
const EMBER2 := Color("c23a3a")
const EMBER3 := Color("f0784a")
const SHADOW2 := Color("a04ce0")

const BODY := 16    # body line height (px): dialogue, menus
const SMALL := 10   # small line height (px): HUD numbers, labels, key hints

## Game symbols in the font's Private Use Area (assets/fonts/README.md).
const HEART := ""
const STONE := ""
const COIN := ""

const VIEW := Vector2(960, 540)

static var _fonts := {}
static var _theme: Theme


static func font(which := "body") -> FontFile:
	if not _fonts.has(which):
		var f: FontFile = load("res://ui/fonts/ShadowfallBody.ttf" if which == "body" else "res://ui/fonts/ShadowfallSmall.ttf").duplicate()
		f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		f.hinting = TextServer.HINTING_NONE
		f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		f.generate_mipmaps = false
		_fonts[which] = f
	return _fonts[which]


## The theme for every UI screen: body font, ink text, the text-box frame on panels.
static func theme() -> Theme:
	if _theme == null:
		var t := Theme.new()
		t.default_font = font("body")
		t.default_font_size = BODY
		t.set_color("font_color", "Label", INK6)
		t.set_color("default_color", "RichTextLabel", INK6)
		t.set_stylebox("panel", "PanelContainer", frame())
		t.set_stylebox("panel", "Panel", frame())
		_theme = t
	return _theme


## The text-box frame: ink1 fill, ink4 1-px border (docs/teen/art/README.md, HUD row).
static func frame(pad := 8) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = INK1
	s.border_color = INK4
	s.set_border_width_all(1)
	s.set_content_margin_all(pad)
	s.anti_aliasing = false
	return s


## A label in one of our fonts. size 0 = the font's own line height (1×); pass 2× for headings.
static func label(text: String, which := "body", color := INK6, size := 0) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font(which))
	l.add_theme_font_size_override("font_size", size if size > 0 else (BODY if which == "body" else SMALL))
	l.add_theme_color_override("font_color", color)
	return l


## A display name from rules/names.gd (B4 owns it), read by constant name so a missing table
## (LAND, SIGIL, QUEST...) falls back instead of breaking the parse.
static func name_of(table: String, id: String) -> String:
	var t = load("res://rules/names.gd").get_script_constant_map().get(table, {})
	if t is Dictionary and t.has(id):
		return t[id]
	return id.replace("_", " ").capitalize()
