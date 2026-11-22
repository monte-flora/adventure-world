class_name CaveArt
## How a cave looks, from art/ (C2's sheets): the tiles_<theme> sheet for every letter, the four
## parallax layers behind (and one in front of) the cave, and the monster sheet for each cave monster.

const TILE := LevelFile.TILE
const VIEW := Vector2(960, 540)
## Cave monster letter -> art sheet (z Zombie, k Skeleton, c Ember Skull, x Spider).
const MONSTER := {"z": "monster_barrow_wight", "k": "monster_bone_crawler", "c": "monster_ember_imp",
	"x": "monster_cave_bat"}
## Letters in the TileMap -> tile. # and F pick solid_<bits> from their neighbours; the < > markers are drawn in code.
const MAP_TILE := {"B": "cracked", "M": "geyser", "G": "gate", "%": "climb_wall", "I": "ice",
	"o": "mushroom", "*": "ore_diamond", "s": "ore_sun", "=": "ledge", "-": "ledge_crumbly",
	"<": "solid_15", ">": "solid_15", "n": "thorns"}
## Letters drawn over the TileMap -> tile (animated ones play at the sheet's fps).
const SPRITE := {"^": "spikes", "!": "fire", "~": "lava", "J": "flame_jet", "$": "gem", "T": "chest",
	"E": "door", "H": "ladder", "V": "vine", "i": "torch", "w": "window", "f": "banner", "L": "lever"}
## Parallax: layer, scroll speed (0 = fixed to the screen; front passes in front of the Hero and
## only scrolls sideways, so its rocks frame the top and bottom of the screen).
const FRONT_ALPHA := 0.6                          # see the floor, gems and spikes through the front rocks
const LAYERS := [["far", 0.0], ["back", 0.25], ["mid", 0.5], ["front", 1.4]]


## The tile sheet for a theme (stone when the theme has none).
static func sheet(theme: String) -> String:
	var s := "tiles_" + theme
	return s if FileAccess.file_exists(ArtSheet.DIR + s + ".json") else "tiles_stone"


static func parallax_theme(theme: String) -> String:
	return theme if ResourceLoader.exists("res://art/parallax/%s_far.png" % theme) else "stone"


## One tile of a sheet as an RGBA8 image (to copy into the cave's own atlas).
static func tile_image(sheet_name: String, anim: String, frame := 0) -> Image:
	var img := ArtSheet.texture(sheet_name).get_image()
	if img.is_compressed():
		img.decompress()
	img.convert(Image.FORMAT_RGBA8)
	return img.get_region(ArtSheet.region(sheet_name, anim, frame))


## The frame an animated tile shows at this clock (60 frames a second).
static func frame_at(sheet_name: String, anim: String, clock: int) -> int:
	var a: Dictionary = ArtSheet.meta(sheet_name)["anims"][anim]
	return int(clock * float(a["fps"]) / 60.0) % int(a["frames"])


## A parallax layer: one 960x540 picture repeated in both directions.
static func layer(theme: String, which: String, speed: float) -> Parallax2D:
	var p := Parallax2D.new()
	p.name = "parallax_" + which
	p.scroll_scale = Vector2(speed, speed if speed <= 1.0 else 0.0)
	p.repeat_size = VIEW
	p.repeat_times = 2
	var s := Sprite2D.new()
	s.texture = load("res://art/parallax/%s_%s.png" % [parallax_theme(theme), which])
	s.centered = false
	if speed > 1.0:
		s.modulate.a = FRONT_ALPHA
	p.add_child(s)
	return p


## Painted backdrops from Gemini (levels/README.md, "Polish a cave with Gemini"):
## levels/polish/<cave file name>/painted.* fills the cave's bounds behind the blocks.
static var polish_root := ""                      # tests point this somewhere else; "" = levels/polish
const PAINTED := ["painted.webp", "painted.png", "painted.jpg", "painted.jpeg"]


## The cave's painting, or null when it has none (then the parallax layers show as before).
static func painting(cave_file: String) -> Texture2D:
	if cave_file == "":
		return null
	var dir := (polish_root if polish_root != "" else Paths.level("polish")).path_join(cave_file.get_file().get_basename())
	for n in PAINTED:
		var path := dir.path_join(n)
		if FileAccess.file_exists(path):              # the web build ships painted.webp as is ("keep")
			var img := Image.new()                    # from bytes: also works in the pack, no warning
			var bytes := FileAccess.get_file_as_bytes(path)
			var err: Error = img.load_webp_from_buffer(bytes) if n.ends_with(".webp") else \
				img.load_png_from_buffer(bytes) if n.ends_with(".png") else img.load_jpg_from_buffer(bytes)
			if err == OK and not img.is_empty():
				return ImageTexture.create_from_image(img)
	return null


## The painting as a sprite stretched over the cave: w x h blocks.
static func backdrop(tex: Texture2D, w: int, h: int) -> Sprite2D:
	var s := Sprite2D.new()
	s.name = "painting"
	s.texture = tex
	s.centered = false
	s.scale = Vector2(w * TILE, h * TILE) / tex.get_size()
	return s
