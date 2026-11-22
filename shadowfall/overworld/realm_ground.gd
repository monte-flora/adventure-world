class_name RealmGround
extends Sprite2D
## The painted ground under lands whose file says `ground: painted`: realm/ground/ textures blended
## square by square from the level letters (realm_ground.gdshader), soft wobbly edges, no seams
## between screens (one quad for the whole realm). Squares of other lands, and materials whose
## texture is missing, are see-through: today's tiles (RealmTiles) show there.

const TILE := LevelFile.TILE
const MATERIALS := ["grass", "dirt_road", "cobblestone", "mud", "shallow_water", "rocky_ground"]
const DIR := "res://realm/ground/"
const VILLAGE_COBBLES := 3.5          # squares from a village's middle where the road is cobbled

var world: WorldMap
var have := {}                        # material -> its index in the atlas (1..)
var map_image: Image
var atlas_image: Image


func _init(w: WorldMap) -> void:
	world = w
	name = "PaintedGround"
	centered = false
	scale = Vector2(TILE, TILE)
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST


## Builds the material map and atlas. False (and nothing drawn) when no land asks for it or the
## grass texture is missing.
func build() -> bool:
	var lands := []
	for id in world.lands:
		if world.lands[id].get("ground", "") == "painted":
			lands.append(id)
	var atlas_imgs: Array[Image] = []
	for m in MATERIALS:
		var p: String = DIR + m + ".png"
		if ResourceLoader.exists(p):
			var img: Image = (load(p) as Texture2D).get_image()
			img.convert(Image.FORMAT_RGBA8)
			atlas_imgs.append(img)
			have[m] = atlas_imgs.size()
	if lands.is_empty() or not have.has("grass"):
		return false
	var size := 256
	var atlas := Image.create(size * atlas_imgs.size(), size, false, Image.FORMAT_RGBA8)
	for i in atlas_imgs.size():
		atlas.blit_rect(atlas_imgs[i], Rect2i(0, 0, size, size), Vector2i(i * size, 0))
	map_image = Image.create(world.size.x, world.size.y, false, Image.FORMAT_R8)
	var villages := _villages()
	for r in world.size.y:
		for c in world.size.x:
			var p := Vector2i(c, r)
			if world.land(p) in lands:
				map_image.set_pixel(c, r, Color8(have.get(material_at(p, villages), 0), 0, 0))
	texture = ImageTexture.create_from_image(map_image)
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://overworld/realm_ground.gdshader")
	atlas_image = atlas
	mat.set_shader_parameter("atlas", ImageTexture.create_from_image(atlas))
	mat.set_shader_parameter("count", atlas_imgs.size())
	mat.set_shader_parameter("tex_size", float(size))
	mat.set_shader_parameter("tile", float(TILE))
	material = mat
	return true


## Which ground a square gets from its letter.
func material_at(p: Vector2i, villages: Array = []) -> String:
	var ch := world.at(p)
	if ch in "R#":
		for v in villages:
			if (Vector2(p) - v).length() <= VILLAGE_COBBLES:
				return "cobblestone"
		return "dirt_road"
	if ch in "XYOK":
		return "rocky_ground"
	if ch in "W~=.":
		return "shallow_water"
	if ch == "B" or WorldMap.realm_id(world.land(p)) == "mirefen":
		return "mud"
	return "grass"


## The middles of every land's `village:` squares, in realm squares.
func _villages() -> Array:
	var out := []
	for id in world.lands:
		var f: String = world.lands[id].file
		if f == "":
			continue
		var lf := LevelFile.load_file(Paths.level(f))
		for v in lf.all("village"):
			var parts := v.split(" ", false)
			if parts.size() >= 3:
				out.append(Vector2(world.lands[id].rect.position) + Vector2(float(parts[-1]), float(parts[-2])))
	return out


## The shader's colour at realm pixel px, worked out on the CPU (tests check seams with it). Keep in
## step with realm_ground.gdshader.
func color_at(px: Vector2) -> Color:
	var atlas := atlas_image
	var cells := map_image.get_size()
	var n := Vector2(_noise(px / 23.0), _noise(px / 23.0 + Vector2(17.3, 17.3))) - Vector2(0.5, 0.5)
	var n2 := Vector2(_noise(px / 7.0 + Vector2(3.1, 3.1)), _noise(px / 7.0 + Vector2(9.7, 9.7))) - Vector2(0.5, 0.5)
	var q := px / TILE + (n * 2.0 + n2 * 0.6) * 0.35 - Vector2(0.5, 0.5)
	var b := Vector2i(floori(q.x), floori(q.y))
	var fr := q - Vector2(b)
	var f := Vector2(smoothstep(0.2, 0.8, fr.x), smoothstep(0.2, 0.8, fr.y))
	var col := Color(0, 0, 0, 0)
	for j in 2:
		for i in 2:
			var c := (b + Vector2i(i, j)).clamp(Vector2i.ZERO, cells - Vector2i.ONE)
			var m := roundi(map_image.get_pixelv(c).r * 255.0)
			var w := (1.0 - f.x if i == 0 else f.x) * (1.0 - f.y if j == 0 else f.y)
			if m > 0:
				var t := Vector2i(int(fposmod(px.x, 256.0)) + (m - 1) * 256, int(fposmod(px.y, 256.0)))
				col += atlas.get_pixelv(t) * w
	return col


static func _hash(p: Vector2) -> float:
	var v := sin(p.dot(Vector2(127.1, 311.7))) * 43758.5453
	return v - floorf(v)


static func _noise(p: Vector2) -> float:
	var i := p.floor()
	var f := p - i
	var u := f * f * (Vector2(3, 3) - 2.0 * f)
	return lerpf(lerpf(_hash(i), _hash(i + Vector2(1, 0)), u.x), lerpf(_hash(i + Vector2(0, 1)), _hash(i + Vector2(1, 1)), u.x), u.y)
