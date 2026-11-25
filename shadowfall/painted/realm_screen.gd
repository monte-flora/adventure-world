class_name PaintedRealmScreen
extends Node2D
## One realm screen as one Gemini painting (a land file's `painted_screen: B3` line; the painting is
## levels/polish/realm_B3/painted.webp, made by `pixi run gemini-realm B3`). On that screen:
## - the painting lies over the painted ground and tiles (960 × 544 px: 1 painted px = 1 game px);
## - every prop and decor sprite there is re-skinned with the painting itself, cut out in the prop's
##   own shape: it keeps its y-sort (the hero still walks behind canopies and roofs), its lights and
##   its gloom shading, but shows the painted pixels, so it matches the picture under it;
## - gate sprites (rubble, thorns, ivy, the boulder) stay as they are: they open;
## - house and Mine tiles there are not drawn. Collision is the level file's, untouched.
## A screen with no painting yet looks as before. Play-test switches: -- --painted=off (today's look),
## -- --polish-root=DIR (read the paintings from DIR, e.g. a placeholder: tools/painted_compare.py).

const TILE := LevelFile.TILE
const SIZE := Vector2i(WorldMap.SCREEN * TILE)          # 960 × 544
const HIDE_TILES := "HMS"                               # object tiles the painting shows
## The layout's colours (gemini_realm.py draws the legend from these): ground roles, then gates.
const LAYOUT := {"grass": Color8(98, 150, 72), "forest_floor": Color8(38, 84, 44),
	"dirt_road": Color8(196, 154, 96), "cobblestone": Color8(150, 150, 156), "mud": Color8(112, 86, 60),
	"shallow_water": Color8(92, 162, 204), "deep_water": Color8(30, 70, 140),
	"rocky_ground": Color8(132, 122, 110), "cliff": Color8(40, 36, 44), "ice": Color8(204, 232, 246),
	"gate": Color8(230, 0, 200)}

var world: WorldMap
var paintings := {}                                     # screen -> Image (SIZE)
var backgrounds: Array[Sprite2D] = []


func _init(w: WorldMap) -> void:
	world = w
	name = "PaintedRealmScreens"
	var opts := Paths.cmdline()
	if str(opts.get("painted", "")) == "off":
		return
	if opts.has("polish-root"):
		CaveArt.polish_root = str(opts["polish-root"])
	for sc: Vector2i in w.painted_screens:
		var tex := CaveArt.painting(w.painted_screens[sc])
		if tex == null:
			continue
		var img := tex.get_image()
		img.convert(Image.FORMAT_RGBA8)
		if img.get_size() != SIZE:
			img.resize(SIZE.x, SIZE.y, Image.INTERPOLATE_LANCZOS)
		paintings[sc] = img
		var s := Sprite2D.new()
		s.name = "painting_" + WorldMap.screen_name(sc)
		s.texture = ImageTexture.create_from_image(img)
		s.centered = false
		s.position = Vector2(origin(sc))
		add_child(s)
		backgrounds.append(s)


static func origin(sc: Vector2i) -> Vector2i:
	return sc * SIZE


## Re-skins every sprite whose art touches a painted screen (gate sprites excepted) and drops the
## house/Mine tiles there. Returns how many sprites it re-skinned.
func apply(sprites: Array, gates: Dictionary, objects: TileMapLayer) -> int:
	if paintings.is_empty():
		return 0
	var keep := {}
	for p in gates:
		keep[gates[p]] = true
	var n := 0
	for s: Sprite2D in sprites:
		if keep.has(s) or s.texture == null:
			continue
		var at := Vector2i((s.position + s.offset).round())
		var img: Image = null
		for sc in paintings:
			if Rect2i(origin(sc), SIZE).intersects(Rect2i(at, Vector2i(s.texture.get_size()))):
				if img == null:
					img = s.texture.get_image()
					img.decompress()
					img.convert(Image.FORMAT_RGBA8)
				cut_out(img, paintings[sc], at - origin(sc))
		if img == null:
			continue
		s.texture = ImageTexture.create_from_image(img)
		if s.has_meta("front"):
			(s.get_meta("front") as Sprite2D).texture = s.texture
		n += 1
	if objects:
		for p: Vector2i in world.cells:
			if world.cells[p] in HIDE_TILES and paintings.has(WorldMap.screen_of(p)):
				objects.erase_cell(p)
	return n


## Paints `painting`'s pixels into `art` wherever art is opaque; `at` is art's top-left in the
## painting's px. Parts of art off the painting keep their own pixels.
static func cut_out(art: Image, painting: Image, at: Vector2i) -> void:
	var both := Rect2i(Vector2i.ZERO, painting.get_size()).intersection(Rect2i(at, art.get_size()))
	if both.size.x <= 0 or both.size.y <= 0:
		return
	var crop := painting.get_region(both)
	var mask := art.get_region(Rect2i(both.position - at, both.size))
	art.blit_rect_mask(crop, mask, Rect2i(Vector2i.ZERO, both.size), both.position - at)


func shade(mat: Material) -> void:
	for s in backgrounds:
		s.material = mat


## The screen as a map for Gemini (SIZE px): each square in its ground role's colour (RealmGround),
## gate squares magenta, then every prop and decor tree/crag drawn where the game puts it (lowest
## last, like the y-sort). Gate sprites are left out: the painting shows open ground there.
## Returns {"image": Image, "props": {name: count}, "gates": {letter: count}, "roles": {role: squares}}.
static func layout(w: WorldMap, sc: Vector2i) -> Dictionary:
	var img := Image.create(SIZE.x, SIZE.y, false, Image.FORMAT_RGBA8)
	var ground := RealmGround.new(w)
	var villages := ground._villages()
	var o := origin(sc)
	var first := sc * WorldMap.SCREEN
	var gates := {}
	var roles := {}
	for r in WorldMap.SCREEN.y:
		for c in WorldMap.SCREEN.x:
			var p := first + Vector2i(c, r)
			var ch := w.at(p)
			var gate := w.gates.has(p) or RealmProps.GATE_PROPS.has(ch)
			var role := "gate" if gate else ground.role_at(p, villages)
			if gate:
				gates[ch] = gates.get(ch, 0) + 1
			roles[role] = roles.get(role, 0) + 1
			img.fill_rect(Rect2i(Vector2i(c, r) * TILE, Vector2i(TILE, TILE)), LAYOUT.get(role, LAYOUT.grass))
	ground.free()
	var spots: Array = []
	for p in w.props:
		spots.append({"name": p.name, "at": p.at, "anchor": Vector2(p.meta.anchor[0], p.meta.anchor[1])})
	for d in RealmProps.decor_spots(w):
		if not d.gate:
			spots.append(d)
	spots.sort_custom(func(a, b): return a.at.y < b.at.y)
	var names := {}
	for d in spots:
		var tex := RealmProps.texture(d.name)
		var at := Vector2i((d.at - d.anchor).round()) - o
		if tex == null or not Rect2i(Vector2i.ZERO, SIZE).intersects(Rect2i(at, Vector2i(tex.get_size()))):
			continue
		var art := tex.get_image()
		art.decompress()
		art.convert(Image.FORMAT_RGBA8)
		img.blend_rect(art, Rect2i(Vector2i.ZERO, art.get_size()), at)
		names[d.name] = names.get(d.name, 0) + 1
	return {"image": img, "props": names, "gates": gates, "roles": roles}
