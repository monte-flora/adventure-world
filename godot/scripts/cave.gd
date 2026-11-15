extends "res://scripts/level_base.gd"
## The tiny cave under the Mine: hop over the lava on stepping stones,
## pull the lever to open the gate, grab the big diamond, and head back out.

const Lever = preload("res://scripts/lever.gd")
const Gate = preload("res://scripts/gate.gd")

const ROCK := Color("6e5a4c")
const ROCK_DARK := Color("4e3f36")
const LAVA := Color("ff6a1a")
const WOOD := Color("8a5226")

var lever: Node
var gate: Node
var bubbles: Array[Node3D] = []
var torches: Array[OmniLight3D] = []
var t := 0.0


func _ready() -> void:
	title = "The Little Lava Cave"
	kill_y = -6.0
	spawns = {"start": [Vector3(0, 0.1, 1), 0.0]}
	_light()
	# floors: the start, a lava pit with stepping stones, and the far side
	B.solid_box(self, Vector3(10, 4, 10), ROCK, Vector3(0, -2, 0))
	B.solid_box(self, Vector3(10, 4, 24), ROCK, Vector3(0, -2, -36))
	var stones := [[Vector3(0, -2, -8), 0.0], [Vector3(-2, -2, -12), 0.6], [Vector3(1.5, -2, -16), 1.2], [Vector3(-1, -2, -20), 0.6]]
	for s in stones:
		var top: float = s[1]
		var st := B.solid_box(self, Vector3(2.6, 4 + top * 2, 2.6), ROCK_DARK, s[0])
		B.box(st, Vector3(2.8, 0.25, 2.8), Color("8b7768"), Vector3(0, 2 + top - 0.1, 0))
	# the lava, glowing and bubbling, with a hot invisible box just under its surface
	B.box(self, Vector3(10, 0.2, 19), LAVA, Vector3(0, -1.2, -14.5), Vector3.ZERO, 2.5)
	add_trigger("hazard", Vector3(0, -2.0, -14.5), Vector3(10, 1.6, 19))
	var rng := RandomNumberGenerator.new()
	rng.seed = 9
	for i in 10:
		var b := B.ball(self, rng.randf_range(0.2, 0.45), Color("ffb03a"), Vector3(rng.randf_range(-4.5, 4.5), -1.1, rng.randf_range(-21, -9)), 0.6, 3.0)
		bubbles.append(b)
	for i in 14:
		var c := Vector3(rng.randf_range(-4.2, 4.2), -1.08, rng.randf_range(-23, -6))
		B.cyl(self, rng.randf_range(0.5, 1.1), rng.randf_range(0.6, 1.2), 0.05, Color("d8401a"), c, Vector3.ZERO, 6, 1.2)
	var glow := OmniLight3D.new()
	glow.light_color = Color("ff7a2a")
	glow.light_energy = 3.0
	glow.omni_range = 14.0
	glow.position = Vector3(0, 0.5, -15)
	add_child(glow)
	_walls()
	# the lever on the far side, then the gate, then the big diamond
	gate = Gate.new()
	gate.width = 10.0
	gate.position = Vector3(0, 0, -34)
	add_child(gate)
	lever = Lever.new()
	lever.gate = gate
	lever.position = Vector3(-3.6, 0, -28)
	add_child(lever)
	B.label(self, "Pull the lever!", Vector3(-2.2, 3.0, -28), 40, Color("ffd23c"))
	B.solid_box(self, Vector3(2, 1, 2), Color("8b7768"), Vector3(0, 0.5, -40))
	add_diamond("c_big", Vector3(0, 2.2, -40), true)
	add_diamond("c_stone", Vector3(1.5, 2.4, -16))
	# a glowing hole at the very end takes you back to the meadow
	B.box(self, Vector3(3, 3.6, 0.3), Color("9ff0ff"), Vector3(0, 1.8, -47.6), Vector3.ZERO, 2.0)
	B.label(self, "Back to the meadow", Vector3(0, 4.6, -47.4), 40)
	add_trigger("portal", Vector3(0, 1.5, -47), Vector3(3, 3, 1.2), "meadow", "from_cave")
	# the way in is a way out too
	B.box(self, Vector3(3, 3.6, 0.3), Color("9ff0ff"), Vector3(0, 1.8, 4.85), Vector3.ZERO, 2.0)
	add_trigger("portal", Vector3(0, 1.5, 4.4), Vector3(3, 3, 0.6), "meadow", "from_cave")


func _light() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("120c0a")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("c9a88a")
	env.ambient_light_energy = 0.55
	env.fog_enabled = true
	env.fog_light_color = Color("1e1410")
	env.fog_density = 0.02
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-60, -20, 0)
	key.light_energy = 0.35
	key.light_color = Color("ffd8b0")
	add_child(key)


func _walls() -> void:
	# tall walls on both sides and at the ends (no roof, so the camera can always see the Hero)
	for x in [-5.75, 5.75]:
		B.solid_box(self, Vector3(1.5, 10, 54), ROCK_DARK, Vector3(x, 3, -21.5))
	B.solid_box(self, Vector3(13, 10, 1.5), ROCK_DARK, Vector3(0, 3, 5.75))
	B.solid_box(self, Vector3(13, 10, 1.5), ROCK_DARK, Vector3(0, 3, -48.5))
	# lumpy rocks and glowing crystals on the walls
	var rng := RandomNumberGenerator.new()
	rng.seed = 21
	var crystal := [Color("b06aff"), Color("4fe3ff"), Color("ff5ad0")]
	for i in 26:
		var side := -1.0 if i % 2 == 0 else 1.0
		var z := 4.0 - i * 2.0
		B.ball(self, rng.randf_range(0.8, 1.6), Color("5a4a40"), Vector3(side * 5.0, rng.randf_range(0.5, 6), z), 0.7)
		if i % 3 == 0:
			var c: Color = crystal[i % 3]
			B.cyl(self, 0.0, 0.3, 1.2, c, Vector3(side * 4.8, rng.randf_range(1.5, 4), z + 0.7), Vector3(0, 0, -side * 35), 5, 1.5)
	# wooden mine supports and torches
	for z in [2.0, -26.0, -38.0, -45.0]:
		for x in [-4.6, 4.6]:
			B.box(self, Vector3(0.5, 5, 0.5), WOOD, Vector3(x, 2.5, z))
		B.box(self, Vector3(9.7, 0.5, 0.6), WOOD, Vector3(0, 5.2, z))
	for p in [Vector3(-4.7, 2.6, -3), Vector3(4.7, 2.6, -24), Vector3(-4.7, 2.6, -31), Vector3(4.7, 2.6, -42)]:
		B.cyl(self, 0.1, 0.07, 0.7, WOOD, p, Vector3.ZERO, 5)
		B.ball(self, 0.22, Color("ffc23a"), p + Vector3(0, 0.5, 0), 1.3, 3.0)
		var l := OmniLight3D.new()
		l.light_color = Color("ffb060")
		l.light_energy = 2.2
		l.omni_range = 9.0
		l.position = p + Vector3(0, 0.6, 0)
		add_child(l)
		torches.append(l)


func _process(delta: float) -> void:
	t += delta
	for i in bubbles.size():
		var b := bubbles[i]
		b.position.y = -1.2 + absf(sin(t * 1.3 + i)) * 0.35
	for i in torches.size():
		torches[i].light_energy = 2.0 + sin(t * 9.0 + i * 2.0) * 0.25 + sin(t * 23.0 + i) * 0.1
