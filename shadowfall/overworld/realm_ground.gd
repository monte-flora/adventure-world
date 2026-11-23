class_name RealmGround
extends Sprite2D
## The painted ground under lands whose file says `ground: painted`: realm/ground/ textures blended
## square by square from the level letters (realm_ground.gdshader), soft wobbly edges, no seams
## between screens (one quad for the whole realm). Squares of other lands, and materials whose
## texture is missing, are see-through: today's tiles (RealmTiles) show there.

const TILE := LevelFile.TILE
## The ground roles a square can have (role_at). Each is the shared texture of that name; a land's
## `paint: <role> <texture>` line swaps in its own (`paint: grass wintermarch_ground_snow`).
const MATERIALS := ["grass", "dirt_road", "cobblestone", "mud", "shallow_water", "rocky_ground",
	"cliff", "deep_water", "forest_floor", "ice"]
## A role whose texture is missing borrows this one (then grass).
const FALLBACK := {"cliff": "rocky_ground", "deep_water": "shallow_water", "forest_floor": "grass",
	"ice": "rocky_ground"}
const WATER := ["shallow_water", "deep_water"]   # these ripple (the shader moves them with TIME)
const DIR := "res://realm/ground/"
const VILLAGE_COBBLES := 3.5          # squares from a village's middle where the road is cobbled
const COLS := 8                       # atlas textures per row

var world: WorldMap
var have := {}                        # texture name -> its index in the atlas (1..)
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
	if lands.is_empty() or not ResourceLoader.exists(DIR + "grass.png"):
		return false
	var villages := _villages()
	var names := {}                       # (land, role) texture picks, so each square is one lookup
	var cell_tex := {}
	var water := {}
	for r in world.size.y:
		for c in world.size.x:
			var p := Vector2i(c, r)
			var id := world.land(p)
			if id in lands:
				var role := role_at(p, villages)
				var key := id + ":" + role
				if not names.has(key):
					names[key] = texture_for(id, role)
				cell_tex[p] = names[key]
				if role in WATER:
					water[names[key]] = true
	var order: Array = []                 # still ground first, then water (the shader ripples from water_first)
	for t in names.values():
		if not water.has(t) and t not in order:
			order.append(t)
	var water_first := order.size() + 1
	for t in names.values():
		if water.has(t) and t not in order:
			order.append(t)
	var size := 256
	var rows := ceili(order.size() / float(COLS))
	atlas_image = Image.create(size * mini(order.size(), COLS), size * rows, false, Image.FORMAT_RGBA8)
	for i in order.size():
		var img: Image = (load(DIR + order[i] + ".png") as Texture2D).get_image()
		img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		atlas_image.blit_rect(img, Rect2i(0, 0, size, size), Vector2i(i % COLS, i / COLS) * size)
		have[order[i]] = i + 1
	map_image = Image.create(world.size.x, world.size.y, false, Image.FORMAT_R8)
	for p in cell_tex:
		map_image.set_pixelv(p, Color8(have[cell_tex[p]], 0, 0))
	texture = ImageTexture.create_from_image(map_image)
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://overworld/realm_ground.gdshader")
	mat.set_shader_parameter("atlas", ImageTexture.create_from_image(atlas_image))
	mat.set_shader_parameter("count", order.size())
	mat.set_shader_parameter("cols", COLS)
	mat.set_shader_parameter("water_first", water_first)
	mat.set_shader_parameter("tex_size", float(size))
	mat.set_shader_parameter("tile", float(TILE))
	material = mat
	return true


## The texture a land draws a role with: its `paint:` pick, else the shared one, else the fallback.
func texture_for(land_id: String, role: String) -> String:
	for line in world.lands[land_id].get("paint", []):
		var parts: PackedStringArray = line.split(" ", false)
		if parts.size() == 2 and parts[0] == role and ResourceLoader.exists(DIR + parts[1] + ".png"):
			return parts[1]
	if ResourceLoader.exists(DIR + role + ".png"):
		return role
	return texture_for(land_id, FALLBACK[role]) if FALLBACK.has(role) else "grass"


## Which ground role a square gets from its letter.
func role_at(p: Vector2i, villages: Array = []) -> String:
	var ch := world.at(p)
	if ch in "R#":
		for v in villages:
			if (Vector2(p) - v).length() <= VILLAGE_COBBLES:
				return "cobblestone"
		return "dirt_road"
	if ch == "X":
		return "rocky_ground" if world.gates.has(p) else "cliff"
	if ch in "YOK":
		return "rocky_ground"
	if ch in "W~=.":
		for d in [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(-1, 0), Vector2i(1, 0),
				Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)]:
			if world.at(p + d) not in "W~=." and world.cells.has(p + d):
				return "shallow_water"          # the shore
		return "deep_water"
	if ch == "I":
		return "ice"
	if ch == "F":
		return "forest_floor"
	if ch == "B" or WorldMap.realm_id(world.land(p)) == "mirefen":
		return "mud"
	return "grass"


## The texture a square is drawn with (the land's pick for its role).
func material_at(p: Vector2i, villages: Array = []) -> String:
	return texture_for(world.land(p), role_at(p, villages)) if world.lands.has(world.land(p)) else ""


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


## The shader's colour at realm pixel px at gloom `stage`, worked out on the CPU (tests check seams
## and the gloom with it). Keep in step with realm_ground.gdshader.
func color_at(px: Vector2, stage := 0) -> Color:
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
			if m > 0:                    # the still frame: water's ripple is not worked out here
				var t := Vector2i(int(fposmod(px.x, 256.0)), int(fposmod(px.y, 256.0))) + Vector2i((m - 1) % COLS, (m - 1) / COLS) * 256
				col += atlas.get_pixelv(t) * w
	return PaintedGloom.grade(col, stage)


static func _hash(p: Vector2) -> float:
	var v := sin(p.dot(Vector2(127.1, 311.7))) * 43758.5453
	return v - floorf(v)


static func _noise(p: Vector2) -> float:
	var i := p.floor()
	var f := p - i
	var u := f * f * (Vector2(3, 3) - 2.0 * f)
	return lerpf(lerpf(_hash(i), _hash(i + Vector2(1, 0)), u.x), lerpf(_hash(i + Vector2(0, 1)), _hash(i + Vector2(1, 1)), u.x), u.y)
