class_name ArtSheet
## Loads an art sheet (art/sheets/<name>.png + .json) as SpriteFrames, or one tile as a texture.
##   var spr := AnimatedSprite2D.new(); spr.sprite_frames = ArtSheet.frames("hero_side")
##   spr.offset = ArtSheet.offset("hero_side")   # puts the JSON origin (the feet) on the node
## Left-facing = flip_h (sheets face right). Format: art/README.md.

const DIR := "res://art/sheets/"
static var _meta := {}
static var _frames := {}


static func meta(name: String) -> Dictionary:
	if not _meta.has(name):
		var f := FileAccess.open(DIR + name + ".json", FileAccess.READ)
		_meta[name] = JSON.parse_string(f.get_as_text()) if f else {}
	return _meta[name]


static func names() -> PackedStringArray:
	var out := PackedStringArray()
	for f in DirAccess.get_files_at(DIR):
		if f.ends_with(".json"):
			out.append(f.get_basename())
	out.sort()
	return out


static func cell(name: String) -> Vector2i:
	var c: Array = meta(name)["cell"]
	return Vector2i(int(c[0]), int(c[1]))


## Draw offset so the JSON origin sits on the node (AnimatedSprite2D with centered = true).
static func offset(name: String) -> Vector2:
	var o: Array = meta(name)["origin"]
	return Vector2(cell(name)) / 2.0 - Vector2(float(o[0]), float(o[1]))


static func texture(name: String) -> Texture2D:
	return load(DIR + meta(name)["image"])


static func region(name: String, anim: String, frame := 0) -> Rect2i:
	var a: Dictionary = meta(name)["anims"][anim]
	var c := cell(name)
	return Rect2i((int(a["col"]) + frame) * c.x, int(a["row"]) * c.y, c.x, c.y)


## One frame (a tile, say "solid_5") as an AtlasTexture.
static func tile(name: String, anim: String, frame := 0) -> AtlasTexture:
	var t := AtlasTexture.new()
	t.atlas = texture(name)
	t.region = Rect2(region(name, anim, frame))
	return t


static func frames(name: String) -> SpriteFrames:
	if _frames.has(name):
		return _frames[name]
	var sf := SpriteFrames.new()
	sf.remove_animation("default")
	var tex := texture(name)
	var anims: Dictionary = meta(name)["anims"]
	for anim in anims:
		var a: Dictionary = anims[anim]
		sf.add_animation(anim)
		sf.set_animation_speed(anim, float(a["fps"]))
		sf.set_animation_loop(anim, bool(a["loop"]))
		for i in int(a["frames"]):
			var t := AtlasTexture.new()
			t.atlas = tex
			t.region = Rect2(region(name, anim, i))
			sf.add_frame(anim, t)
	_frames[name] = sf
	return sf
