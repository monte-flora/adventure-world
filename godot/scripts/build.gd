extends RefCounted
## Little helpers that make chunky, flat-coloured shapes out of Godot primitives.
## Every piece of art in the prototype is built with these: no downloaded assets.

const WORLD := 1      # collision layer for the ground, walls and platforms
const PLAYER := 2     # collision layer for the Hero
const MONSTER := 4    # collision layer for monsters

static var _mats := {}


## A flat, cartoony (toon-shaded) material. Materials are shared by colour.
static func mat(color: Color, glow := 0.0) -> StandardMaterial3D:
	var key := "%s/%s" % [color.to_html(), glow]
	if _mats.has(key):
		return _mats[key]
	var m := StandardMaterial3D.new()
	m.albedo_color = color
	m.roughness = 1.0
	m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
	m.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	if glow > 0.0:
		m.emission_enabled = true
		m.emission = color
		m.emission_energy_multiplier = glow
	_mats[key] = m
	return m


static func mesh(parent: Node, m: Mesh, color: Color, pos := Vector3.ZERO, rot := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = mat(color, glow)
	mi.position = pos
	mi.rotation_degrees = rot
	parent.add_child(mi)
	return mi


static func box(parent: Node, size: Vector3, color: Color, pos := Vector3.ZERO, rot := Vector3.ZERO, glow := 0.0) -> MeshInstance3D:
	var b := BoxMesh.new()
	b.size = size
	return mesh(parent, b, color, pos, rot, glow)


## A ball. `squash` < 1 flattens it (height = 2 * radius * squash).
static func ball(parent: Node, radius: float, color: Color, pos := Vector3.ZERO, squash := 1.0, glow := 0.0) -> MeshInstance3D:
	var s := SphereMesh.new()
	s.radius = radius
	s.height = radius * 2.0 * squash
	s.radial_segments = 12
	s.rings = 6
	return mesh(parent, s, color, pos, Vector3.ZERO, glow)


## A dome (half a ball) sitting on its flat side.
static func dome(parent: Node, radius: float, height: float, color: Color, pos := Vector3.ZERO) -> MeshInstance3D:
	var s := SphereMesh.new()
	s.radius = radius
	s.height = height
	s.is_hemisphere = true
	s.radial_segments = 14
	s.rings = 5
	return mesh(parent, s, color, pos)


static func cyl(parent: Node, top: float, bottom: float, height: float, color: Color, pos := Vector3.ZERO, rot := Vector3.ZERO, sides := 10, glow := 0.0) -> MeshInstance3D:
	var c := CylinderMesh.new()
	c.top_radius = top
	c.bottom_radius = bottom
	c.height = height
	c.radial_segments = sides
	c.rings = 1
	return mesh(parent, c, color, pos, rot, glow)


static func capsule(parent: Node, radius: float, height: float, color: Color, pos := Vector3.ZERO, rot := Vector3.ZERO) -> MeshInstance3D:
	var c := CapsuleMesh.new()
	c.radius = radius
	c.height = height
	c.radial_segments = 10
	c.rings = 3
	return mesh(parent, c, color, pos, rot)


static func prism(parent: Node, size: Vector3, color: Color, pos := Vector3.ZERO, rot := Vector3.ZERO) -> MeshInstance3D:
	var p := PrismMesh.new()
	p.size = size
	return mesh(parent, p, color, pos, rot)


static func body(parent: Node, pos: Vector3, rot := Vector3.ZERO) -> StaticBody3D:
	var b := StaticBody3D.new()
	b.collision_layer = WORLD
	b.collision_mask = 0
	b.position = pos
	b.rotation_degrees = rot
	parent.add_child(b)
	return b


static func shape(parent: Node, s: Shape3D, pos := Vector3.ZERO) -> CollisionShape3D:
	var cs := CollisionShape3D.new()
	cs.shape = s
	cs.position = pos
	parent.add_child(cs)
	return cs


## A box you can stand on.
static func solid_box(parent: Node, size: Vector3, color: Color, pos: Vector3, rot := Vector3.ZERO) -> StaticBody3D:
	var b := body(parent, pos, rot)
	box(b, size, color)
	var s := BoxShape3D.new()
	s.size = size
	shape(b, s)
	return b


## A grassy floating block: green top, brown dirt underneath.
static func grass_block(parent: Node, size: Vector3, pos: Vector3, top := Color("5cc23c"), dirt := Color("9a6532")) -> StaticBody3D:
	var b := solid_box(parent, size, dirt, pos)
	box(b, Vector3(size.x + 0.15, 0.35, size.z + 0.15), top, Vector3(0, size.y / 2.0 - 0.12, 0))
	return b


## Gives a mesh a convex collision shape (good for hills and rocks).
static func make_solid(mi: MeshInstance3D) -> StaticBody3D:
	var parent := mi.get_parent()
	var b := body(parent, mi.position, mi.rotation_degrees)
	parent.remove_child(mi)
	mi.position = Vector3.ZERO
	mi.rotation = Vector3.ZERO
	b.add_child(mi)
	shape(b, mi.mesh.create_convex_shape())
	return b


static func label(parent: Node, text: String, pos: Vector3, size := 64, color := Color.WHITE) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font_size = size
	l.outline_size = 16
	l.modulate = color
	l.outline_modulate = Color("3b2412")
	l.position = pos
	l.pixel_size = 0.012
	l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	parent.add_child(l)
	return l
