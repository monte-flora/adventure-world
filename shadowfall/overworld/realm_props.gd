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
const RUNE := {"energy": 0.9, "color": Color("8fb4ff"), "amount": 0.15, "speed": 6.0}     # the Shadowgate: cold silver-blue
const WISP := {"energy": 0.9, "color": Color("a070f0"), "amount": 0.25, "speed": 9.0}     # the Umbral Reach: cold violet
const FIRE := {"energy": 1.0, "color": Color("f0784a"), "amount": 0.3, "speed": 10.0}
const HALO_SHARE := 0.3                   # a halo is this share of its light's pool across
const LIGHTS := {"cottage_a": WINDOW, "cottage_b": WINDOW, "tavern": WINDOW, "smithy": FORGE,
	"lamppost": LAMP, "campfire": FIRE,
	"cinder_wastes_forge_temple": FORGE, "cinder_wastes_ash_shrine": FIRE, "cinder_wastes_lava_crack": FIRE,
	"mirefen_wisp_lantern": LAMP,
	"shadowgate_portal_arch": RUNE, "shadowgate_rune_brazier": RUNE,
	"umbral_reach_ruined_shrine": WISP, "umbral_reach_wisp_fire": WISP, "umbral_reach_weeping_throne": WISP,
	"umbral_reach_ruined_arch": WISP}


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


## Painted lands draw their letters with props too (drawing only: the letters keep the collision):
## every gate square gets its gate prop (shown while shut), and F and X squares a tree or a crag
## every other square (a checkerboard, nudged a little), from the land's `forest:` / `crags:` lists.
const GATE_PROPS := {"Y": "ivy_cliff", "O": "rubble_heap", "K": "shadow_thorns"}
const GATE_ROCK := "riven_boulder"            # a `gate:` rock (the Riven Gap)
const FOREST := ["oak", "pine", "dead_tree"]
const CRAGS := ["crag"]


## Adds the decor sprites for every painted square to `sorted`. Returns {"sprites": [...], "gates":
## {square: sprite}} (refresh_gates shows a gate's sprite only while it is shut).
static func scatter(world: WorldMap, sorted: Node2D) -> Dictionary:
	var out: Array[Sprite2D] = []
	var gates := {}
	var t := float(LevelFile.TILE)
	for p: Vector2i in world.cells:
		var land: Dictionary = world.lands.get(world.land(p), {})
		if land.get("ground", "") != "painted":
			continue
		var ch: String = world.cells[p]
		var name := ""
		var nudge := Vector2.ZERO
		if world.gates.has(p):
			name = GATE_ROCK
		elif GATE_PROPS.has(ch):
			name = GATE_PROPS[ch]
		elif ch in "FX" and (p.x + p.y) % 2 == 0 and not world.prop_cover.has(p):
			var kinds: Array = land.get("forest" if ch == "F" else "crags", [])
			if kinds.is_empty():
				kinds = FOREST if ch == "F" else CRAGS
			name = kinds[RealmTiles.variant(p, kinds.size())]
			nudge = Vector2(RealmTiles.variant(p + Vector2i(7, 3), 13) - 6, RealmTiles.variant(p + Vector2i(2, 9), 9) - 4)
		if name == "":
			continue
		var tex := texture(name)
		var m := WorldMap.prop_meta(name)
		if tex == null or m.is_empty():
			continue
		var s := Sprite2D.new()
		s.name = "decor_" + name
		s.texture = tex
		s.centered = false
		s.offset = -Vector2(m.anchor[0], m.anchor[1])
		s.position = (Vector2(p) + Vector2(0.5, 0.9)) * t + nudge    # stands near the square's bottom
		s.set_meta("prop", name)
		sorted.add_child(s)
		out.append(s)
		if name == GATE_ROCK or GATE_PROPS.has(ch):
			gates[p] = s
	refresh_gates(world, gates)
	return {"sprites": out, "gates": gates}


## Shows each gate's sprite only while the gate is shut.
static func refresh_gates(world: WorldMap, gates: Dictionary) -> void:
	for p in gates:
		(gates[p] as Sprite2D).visible = not (world.gate_open(p) if world.gates.has(p) else world.walkable(p))


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
	if k != WINDOW:                       # a flame or lamp glows itself; a window's glass is painted lit
		l.add_child(halo(k.color, radius * HALO_SHARE))
	parent.add_child(l)
	return l


## A small glow on the flame itself (additive, unshaded), so a lamp's head reads as lit at every gloom
## stage, not just the ground round it. LanternLight fades it with its flicker.
static func halo(color: Color, across: float) -> Sprite2D:
	var h := Sprite2D.new()
	h.name = "halo"
	h.texture = LanternLight.glow()
	h.scale = Vector2.ONE * across / LanternLight.TEX
	h.modulate = color
	var m := CanvasItemMaterial.new()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	h.material = m
	return h


## Shades every prop sprite (and its front rows) with `mat` (GloomLight.painted_material).
static func shade(sprites: Array[Sprite2D], mat: Material) -> void:
	for s in sprites:
		s.material = mat
		if s.has_meta("front"):
			(s.get_meta("front") as Sprite2D).material = mat


static func texture(name: String) -> Texture2D:
	var path := WorldMap.PROP_DIR + name + ".png"
	return load(path) if ResourceLoader.exists(path) else null
