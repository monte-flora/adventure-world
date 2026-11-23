class_name RealmProps
## The realm's props (WorldMap.props, from `prop:` lines) as y-sorted Sprite2Ds: each sorts by its
## anchor (the bottom of its footprint), so the hero walks behind a canopy and in front of the trunk.
## `front` rows of a prop go on the canopy layer (always over the hero); `lights` get a warm
## LanternLight (it burns brighter as the dusk deepens, so it reads at every gloom stage) of the prop's
## kind (LIGHTS), at the .json's radius. Art: realm/props/<name>.png + .json (tools/art_import.gd).
## The overworld shades every prop (and its front rows) with GloomLight.painted_material.

## How each prop's lights burn. All far under LanternLight.HERO (176 px, 1.4): the hero stays the
## strongest light. amount/speed tune its Flicker (fire: big and fast; a window: a slow candle).
const WINDOW := {"energy": 0.55, "color": Color("f7c64a"), "amount": 0.08, "speed": 3.0}
const LAMP := {"energy": 0.8, "color": Color("ffc56a"), "amount": 0.1, "speed": 5.0}
const FORGE := {"energy": 0.9, "color": Color("f0784a"), "amount": 0.2, "speed": 7.0}
const FIRE := {"energy": 1.0, "color": Color("f0784a"), "amount": 0.3, "speed": 10.0}
const LIGHTS := {"cottage_a": WINDOW, "cottage_b": WINDOW, "tavern": WINDOW, "smithy": FORGE,
	"lamppost": LAMP, "campfire": FIRE}


## Adds one Sprite2D per prop to `sorted` (a y-sorted node); front rows to `over` if given.
static func build(world: WorldMap, sorted: Node2D, over: Node2D = null) -> Array[Sprite2D]:
	var out: Array[Sprite2D] = []
	for p in world.props:
		var tex := texture(p.name)
		if tex == null:
			continue
		var m: Dictionary = p.meta
		var anchor := Vector2(m.anchor[0], m.anchor[1])
		var s := Sprite2D.new()
		s.name = "prop_" + p.name
		s.texture = tex
		s.centered = false
		s.offset = -anchor
		s.position = p.at
		s.set_meta("prop", p.name)
		sorted.add_child(s)
		out.append(s)
		var front := int(m.get("front", 0))
		if front > 0 and over:
			var f := Sprite2D.new()
			f.texture = tex
			f.centered = false
			f.region_enabled = true
			f.region_rect = Rect2(0, 0, tex.get_width(), front)
			f.position = p.at - anchor
			over.add_child(f)
			s.set_meta("front", f)
		for l in m.get("lights", []):
			light(s, p.name, Vector2(l[0], l[1]) - anchor, float(l[2]))
	return out


## A prop's light of its kind: a LanternLight on `parent` at `pos`, `radius` px.
static func light(parent: Node, prop: String, pos: Vector2, radius: float) -> LanternLight:
	var k: Dictionary = LIGHTS.get(prop, WINDOW)
	var l := LanternLight.new({"radius": radius, "energy": k.energy, "color": k.color})
	l.name = "light"
	l.position = pos
	l.add_to_group(RealmLight.GROUP)
	var f: Flicker = l.get_child(0)
	f.amount = k.amount
	f.speed = k.speed
	parent.add_child(l)
	return l


## Shades every prop sprite (and its front rows) with `mat` (GloomLight.painted_material).
static func shade(sprites: Array[Sprite2D], mat: Material) -> void:
	for s in sprites:
		s.material = mat
		if s.has_meta("front"):
			(s.get_meta("front") as Sprite2D).material = mat


static func texture(name: String) -> Texture2D:
	var path := WorldMap.PROP_DIR + name + ".png"
	return load(path) if ResourceLoader.exists(path) else null
