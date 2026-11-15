extends "res://scripts/level_base.gd"
## Home Meadow: the Hero's house, trees, a pond, hills, floating platforms,
## diamonds, a Zombie, and the Mine entrance to the cave.

const Zombie = preload("res://scripts/zombie.gd")

const GRASS := Color("58b83a")
const GRASS_DARK := Color("3f9a2c")
const DIRT := Color("a06a35")

var zombie: Node
var clouds: Array[Node3D] = []


func _ready() -> void:
	title = "Home Meadow"
	kill_y = -10.0
	spawns = {"start": [Vector3(0, 0.1, 14), 0.0], "from_cave": [Vector3(0, 0.1, -25), PI]}
	_sky()
	_island()
	_house(Vector3(-10, 0, 4))
	_pond(Vector3(11, 0, 9))
	_hills()
	_trees()
	_platforms()
	_mine(Vector3(0, 0, -33))
	_flowers()
	_diamonds()
	zombie = Zombie.new()
	zombie.position = Vector3(-6, 0.2, -16)
	zombie.patrol = [Vector3(-6, 0, -16), Vector3(6, 0, -16)]
	add_child(zombie)


func _sky() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color("3d8bff")
	sm.sky_horizon_color = Color("bfe6ff")
	sm.ground_horizon_color = Color("bfe6ff")
	sm.ground_bottom_color = Color("2a6fd6")
	sm.sun_angle_max = 20.0
	sky.sky_material = sm
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c8dcff")
	env.ambient_light_energy = 0.55
	env.fog_enabled = true
	env.fog_light_color = Color("bfe6ff")
	env.fog_density = 0.006
	env.fog_sky_affect = 0.0
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55, 35, 0)
	sun.light_energy = 1.15
	sun.light_color = Color("fff4dc")
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 80.0
	add_child(sun)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in 9:
		var c := Node3D.new()
		var a := TAU * i / 9.0
		c.position = Vector3(cos(a) * 45, rng.randf_range(16, 24), sin(a) * 45)
		add_child(c)
		for j in 3:
			B.ball(c, rng.randf_range(2.5, 4.0), Color.WHITE, Vector3(j * 3.2 - 3.2, rng.randf_range(-0.5, 0.5), 0), 0.6)
		clouds.append(c)


func _process(delta: float) -> void:
	for c in clouds:
		c.position = c.position.rotated(Vector3.UP, delta * 0.01)


func _island() -> void:
	# a round grassy island with a chunky dirt cliff, floating over the sea
	var top := B.body(self, Vector3(0, -0.3, 0))
	B.cyl(top, 46, 46, 0.6, GRASS, Vector3.ZERO, Vector3.ZERO, 24)
	var s := CylinderShape3D.new()
	s.radius = 46
	s.height = 0.6
	B.shape(top, s)
	B.cyl(self, 45.5, 40, 7, DIRT, Vector3(0, -4, 0), Vector3.ZERO, 24)
	B.cyl(self, 40, 30, 3, Color("8a5a2c"), Vector3(0, -9, 0), Vector3.ZERO, 24)
	B.cyl(self, 200, 200, 0.2, Color("2f86e8"), Vector3(0, -8.5, 0), Vector3.ZERO, 32)
	# a tan path from home to the Mine
	for i in 14:
		var z := 12.0 - i * 3.0
		B.cyl(self, 1.1, 1.1, 0.08, Color("e3c98f"), Vector3(sin(i * 0.7) * 1.2, 0.02, z), Vector3.ZERO, 7)


func _house(at: Vector3) -> void:
	var h := Node3D.new()
	h.position = at
	h.rotation_degrees = Vector3(0, 25, 0)
	add_child(h)
	B.solid_box(h, Vector3(6, 4, 5), Color("fff0c8"), Vector3(0, 2, 0))
	B.prism(h, Vector3(7.2, 2.6, 6), Color("e04a3a"), Vector3(0, 5.3, 0))
	B.box(h, Vector3(1.4, 2.4, 0.2), Color("8a5226"), Vector3(0, 1.2, -2.55))
	B.ball(h, 0.1, Color("ffd23c"), Vector3(0.45, 1.2, -2.7))
	for x in [-1.9, 1.9]:
		B.box(h, Vector3(1.1, 1.1, 0.2), Color("7fd7ff"), Vector3(x, 2.4, -2.55), Vector3.ZERO, 0.3)
		B.box(h, Vector3(1.3, 0.15, 0.25), Color("8a5226"), Vector3(x, 1.8, -2.6))
	B.solid_box(h, Vector3(0.9, 2.0, 0.9), Color("b0a8a0"), Vector3(1.8, 6.2, 1.2))
	B.label(h, "Hero's House", Vector3(0, 8.0, 0), 64)
	# a little fence
	for i in 7:
		B.box(h, Vector3(0.2, 1.0, 0.2), Color("fff7e6"), Vector3(-4.5 + i * 1.5, 0.5, -5))
	B.box(h, Vector3(9.2, 0.15, 0.12), Color("fff7e6"), Vector3(0, 0.75, -5))


func _pond(at: Vector3) -> void:
	B.cyl(self, 6.2, 6.2, 0.06, Color("f0dc9a"), at + Vector3(0, 0.02, 0), Vector3.ZERO, 14)
	B.cyl(self, 5.2, 5.2, 0.08, Color("38a8ff"), at + Vector3(0, 0.05, 0), Vector3.ZERO, 14, 0.15)
	var rng := RandomNumberGenerator.new()
	rng.seed = 3
	for i in 4:
		var p := at + Vector3(rng.randf_range(-3, 3), 0.11, rng.randf_range(-3, 3))
		B.cyl(self, 0.6, 0.6, 0.04, Color("3fae3a"), p, Vector3.ZERO, 8)
	for i in 10:
		var a := TAU * i / 10.0
		var r := B.ball(self, rng.randf_range(0.4, 0.7), Color("a9a9b4"), at + Vector3(cos(a) * 6.3, 0.1, sin(a) * 6.3), 0.6)
		B.make_solid(r)


func _hills() -> void:
	var hills := [[Vector3(-24, 0, -14), 11.0, 5.0], [Vector3(24, 0, -20), 9.0, 4.0], [Vector3(-18, 0, 24), 8.0, 3.0], [Vector3(26, 0, 18), 7.0, 3.5]]
	for h in hills:
		var d := B.dome(self, h[1], h[2], GRASS_DARK, h[0])
		B.make_solid(d)


func _trees() -> void:
	var spots := [Vector3(-16, 0, 10), Vector3(-19, 0, -2), Vector3(-4, 0, 22), Vector3(6, 0, 20), Vector3(20, 0, 3),
		Vector3(17, 0, -30), Vector3(-14, 0, -28), Vector3(-30, 0, 6), Vector3(31, 0, -6), Vector3(-8, 0, -22),
		Vector3(12, 0, -24), Vector3(-26, 0, 16)]
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in spots.size():
		var p: Vector3 = spots[i]
		var t := B.body(self, p)
		var k := rng.randf_range(0.85, 1.3)
		B.cyl(t, 0.35 * k, 0.5 * k, 2.4 * k, Color("8a5226"), Vector3(0, 1.2 * k, 0), Vector3.ZERO, 7)
		var s := CylinderShape3D.new()
		s.radius = 0.5 * k
		s.height = 2.4 * k
		B.shape(t, s, Vector3(0, 1.2 * k, 0))
		if i % 3 == 0:
			# a pointy pine
			for j in 3:
				B.cyl(t, 0.0, (2.0 - j * 0.5) * k, 1.8 * k, Color("2f9a44"), Vector3(0, (2.6 + j * 1.0) * k, 0), Vector3.ZERO, 8)
		else:
			# a round, puffy tree
			B.ball(t, 1.7 * k, Color("49c24a"), Vector3(0, 3.4 * k, 0))
			B.ball(t, 1.2 * k, Color("5fd85a"), Vector3(0.8 * k, 4.3 * k, 0.4 * k))
			B.ball(t, 1.1 * k, Color("3fb040"), Vector3(-0.9 * k, 3.9 * k, -0.3 * k))
			if i % 2 == 0:
				for a in 3:
					B.ball(t, 0.2, Color("ff4a4a"), Vector3(cos(a * 2.1) * 1.5 * k, 3.2 * k, sin(a * 2.1) * 1.5 * k))


func _platforms() -> void:
	# a staircase of floating blocks, with a diamond on top of each
	var steps := [Vector3(10, 1.6, -4), Vector3(14, 3.2, -7), Vector3(17, 4.8, -11), Vector3(14, 6.6, -15)]
	for p in steps:
		B.grass_block(self, Vector3(3, 1.0, 3), p)
	B.grass_block(self, Vector3(4.5, 1.0, 4.5), Vector3(9, 8.2, -18))
	# a lonely one by the house
	B.grass_block(self, Vector3(2.5, 0.8, 2.5), Vector3(-12, 2.0, -7))


func _mine(at: Vector3) -> void:
	var m := Node3D.new()
	m.position = at
	add_child(m)
	var rock := Color("8b8790")
	B.make_solid(B.dome(m, 7.5, 7.0, rock, Vector3(0, 0, -2)))
	B.ball(m, 2.5, Color("77737c"), Vector3(-5, 0.5, 1), 0.7)
	B.ball(m, 2.0, Color("9a96a0"), Vector3(5, 0.4, 0.5), 0.7)
	# the dark doorway with a wooden frame
	B.box(m, Vector3(3.6, 4.2, 1.0), Color("15100c"), Vector3(0, 2.1, 5.0))
	for x in [-2.0, 2.0]:
		B.box(m, Vector3(0.5, 4.6, 0.5), Color("8a5226"), Vector3(x, 2.3, 5.5))
	B.box(m, Vector3(4.8, 0.55, 0.6), Color("8a5226"), Vector3(0, 4.7, 5.5))
	B.label(m, "MINE", Vector3(0, 6.0, 5.7), 96, Color("ffd23c"))
	# rails coming out of the Mine
	for x in [-0.7, 0.7]:
		B.box(m, Vector3(0.12, 0.1, 6.0), Color("6a6e78"), Vector3(x, 0.08, 8.0))
	for i in 6:
		B.box(m, Vector3(2.0, 0.08, 0.35), Color("7a4a24"), Vector3(0, 0.04, 5.5 + i * 1.0))
	add_trigger("portal", at + Vector3(0, 1.5, 5.2), Vector3(3.2, 3.0, 1.0), "cave", "start")


func _flowers() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	var colors := [Color("ff5a8a"), Color("ffe14a"), Color("ffffff"), Color("b06aff")]
	for i in 60:
		var a := rng.randf() * TAU
		var r := rng.randf_range(4, 40)
		var p := Vector3(cos(a) * r, 0, sin(a) * r)
		if p.distance_to(Vector3(11, 0, 9)) < 7 or abs(p.x) < 2.5:
			continue
		B.cyl(self, 0.03, 0.03, 0.5, Color("2f8a2f"), p + Vector3(0, 0.25, 0), Vector3.ZERO, 4)
		B.ball(self, 0.17, colors[i % colors.size()], p + Vector3(0, 0.55, 0), 0.7)
	for i in 30:
		var a := rng.randf() * TAU
		var r := rng.randf_range(5, 42)
		B.cyl(self, 0.0, 0.25, 0.6, GRASS_DARK, Vector3(cos(a) * r, 0.3, sin(a) * r), Vector3.ZERO, 3)


func _diamonds() -> void:
	add_diamond("m_house", Vector3(-6, 1.0, 9))
	add_diamond("m_pond", Vector3(11, 1.0, 9))
	add_diamond("m_step1", Vector3(10, 3.0, -4))
	add_diamond("m_step2", Vector3(14, 4.6, -7))
	add_diamond("m_step3", Vector3(17, 6.2, -11))
	add_diamond("m_top", Vector3(9, 9.7, -18))
	add_diamond("m_hill", Vector3(-24, 6.0, -14))
	add_diamond("m_roof", Vector3(-12, 3.4, -7))
