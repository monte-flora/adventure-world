class_name RealmProps
## The realm's props (WorldMap.props, from `prop:` lines) as y-sorted Sprite2Ds: each sorts by its
## anchor (the bottom of its footprint), so the hero walks behind a canopy and in front of the trunk.
## `front` rows of a prop go on the canopy layer (always over the hero); `lights` get a warm
## flickering PointLight2D (RealmLight.glow). Art: realm/props/<name>.png + .json (tools/art_import.gd).

const LIGHT_ENERGY := 0.8


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
		for l in m.get("lights", []):
			RealmLight.glow(s, Vector2(l[0], l[1]) - anchor, float(l[2]), LIGHT_ENERGY)
	return out


static func texture(name: String) -> Texture2D:
	var path := WorldMap.PROP_DIR + name + ".png"
	return load(path) if ResourceLoader.exists(path) else null
