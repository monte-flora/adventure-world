extends CharacterBody3D
## The Hero, a young knight. Runs with a little momentum, jumps, double-jumps
## (with a flip), swings his sword, and bounces off monsters' heads.

const B = preload("res://scripts/build.gd")

const SPEED := 8.0
const ACCEL := 45.0
const AIR_ACCEL := 16.0
const FRICTION := 38.0
const GRAVITY := 32.0
const JUMP := 12.0
const DOUBLE_JUMP := 10.5
const COYOTE := 0.12
const BUFFER := 0.12
const SWING_TIME := 0.32
const SWORD_REACH := 2.1
const INVULNERABLE := 1.4

var cam_yaw := 0.0          # set by the camera every frame, so "up" means "away from the camera"
var kill_y := -12.0         # falling below this costs a heart
var safe_pos := Vector3.ZERO
var frozen := false         # true while the level changes

var model: Node3D
var sword: Node3D
var legs: Array[Node3D] = []
var arms: Array[Node3D] = []
var air_jumps := 1
var coyote := 0.0
var buffer := 0.0
var swing := 0.0
var swing_hit_done := false
var hurt_time := 0.0
var ground_time := 0.0
var run_phase := 0.0
var was_on_floor := true
var flip := 0.0


func _ready() -> void:
	add_to_group("player")
	collision_layer = B.PLAYER
	collision_mask = B.WORLD
	floor_snap_length = 0.3
	var cap := CapsuleShape3D.new()
	cap.radius = 0.42
	cap.height = 1.6
	B.shape(self, cap, Vector3(0, 0.8, 0))
	_build_model()
	safe_pos = global_position


func _build_model() -> void:
	model = Node3D.new()
	add_child(model)
	var skin := Color("ffc896")
	var tunic := Color("2f6fe0")
	var steel := Color("d8dde6")
	var boot := Color("7a4a24")
	# legs (each a pivot at the hip so they can swing)
	for side in [-1, 1]:
		var hip := Node3D.new()
		hip.position = Vector3(0.18 * side, 0.55, 0)
		model.add_child(hip)
		B.capsule(hip, 0.13, 0.5, Color("2a3b7a"), Vector3(0, -0.22, 0))
		B.box(hip, Vector3(0.26, 0.18, 0.36), boot, Vector3(0, -0.47, -0.05))
		legs.append(hip)
	# body: a blue tunic with a shiny chest plate and a belt
	B.cyl(model, 0.33, 0.42, 0.55, tunic, Vector3(0, 0.82, 0))
	B.cyl(model, 0.36, 0.36, 0.38, steel, Vector3(0, 0.92, -0.02), Vector3.ZERO, 8)
	B.cyl(model, 0.43, 0.43, 0.09, Color("6b3e1c"), Vector3(0, 0.62, 0))
	B.box(model, Vector3(0.12, 0.1, 0.05), Color("ffd23c"), Vector3(0, 0.62, -0.42))
	# a little red cape
	B.box(model, Vector3(0.6, 0.7, 0.06), Color("d8322c"), Vector3(0, 0.82, 0.38), Vector3(-12, 0, 0))
	# big head with a knight's helmet and a plume
	B.ball(model, 0.36, skin, Vector3(0, 1.42, 0))
	B.dome(model, 0.39, 0.42, steel, Vector3(0, 1.48, 0))
	B.cyl(model, 0.42, 0.42, 0.07, steel, Vector3(0, 1.5, 0), Vector3.ZERO, 12)
	B.capsule(model, 0.07, 0.5, Color("e83a3a"), Vector3(0, 1.95, 0.1), Vector3(-30, 0, 0))
	for side in [-1, 1]:
		B.capsule(model, 0.065, 0.2, Color("1d1d2b"), Vector3(0.13 * side, 1.4, -0.33))
		B.ball(model, 0.06, Color("ff9a8a"), Vector3(0.22 * side, 1.3, -0.27))
	B.box(model, Vector3(0.12, 0.03, 0.03), Color("8a3b2b"), Vector3(0, 1.26, -0.35))
	# arms: left holds a round shield, right holds the sword
	for side in [-1, 1]:
		var shoulder := Node3D.new()
		shoulder.position = Vector3(0.47 * side, 1.0, 0)
		model.add_child(shoulder)
		B.capsule(shoulder, 0.11, 0.45, tunic, Vector3(0, -0.18, 0))
		B.ball(shoulder, 0.12, skin, Vector3(0, -0.42, 0))
		arms.append(shoulder)
	var shield := B.cyl(arms[0], 0.3, 0.3, 0.08, Color("2f6fe0"), Vector3(-0.1, -0.35, -0.1), Vector3(0, 0, 90), 10)
	B.cyl(shield, 0.2, 0.2, 0.1, Color("ffd23c"), Vector3.ZERO, Vector3.ZERO, 5)
	sword = Node3D.new()
	sword.position = Vector3(0, -0.42, 0)
	arms[1].add_child(sword)
	B.box(sword, Vector3(0.09, 0.09, 0.22), Color("6b3e1c"), Vector3(0, 0, 0))
	B.box(sword, Vector3(0.42, 0.08, 0.08), Color("ffd23c"), Vector3(0, 0, -0.13))
	B.box(sword, Vector3(0.12, 0.05, 0.95), Color("eef3ff"), Vector3(0, 0, -0.62), Vector3.ZERO, 0.15)
	_rest_sword()


func _rest_sword() -> void:
	sword.rotation_degrees = Vector3(70, 0, 0)
	arms[1].rotation_degrees = Vector3(-20, 0, 0)


func facing() -> Vector3:
	return -model.global_transform.basis.z


func teleport(pos: Vector3, yaw := 0.0) -> void:
	global_position = pos
	velocity = Vector3.ZERO
	model.rotation = Vector3(0, yaw, 0)
	safe_pos = pos
	ground_time = 0.0


func _physics_process(delta: float) -> void:
	if frozen:
		return
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var wish := Vector3(input.x, 0, input.y).rotated(Vector3.UP, cam_yaw)
	var on_floor := is_on_floor()

	# running, with a little momentum
	var hv := Vector2(velocity.x, velocity.z)
	var target := Vector2(wish.x, wish.z) * SPEED
	var accel := ACCEL if on_floor else AIR_ACCEL
	if wish.length() < 0.05 and on_floor:
		accel = FRICTION
	hv = hv.move_toward(target, accel * delta)
	velocity.x = hv.x
	velocity.z = hv.y
	if hv.length() > 0.3:
		model.rotation.y = lerp_angle(model.rotation.y, atan2(-hv.x, -hv.y), minf(1.0, 14.0 * delta))

	# jumping: a little forgiveness at ledges (coyote time) and for early presses (buffer)
	coyote = COYOTE if on_floor else coyote - delta
	buffer = BUFFER if Input.is_action_just_pressed("jump") else buffer - delta
	if on_floor:
		air_jumps = 1
	if buffer > 0.0:
		if coyote > 0.0:
			_jump(JUMP, "jump")
		elif air_jumps > 0:
			air_jumps -= 1
			_jump(DOUBLE_JUMP, "double")
			flip = 1.0
	if Input.is_action_just_released("jump") and velocity.y > 4.0:
		velocity.y *= 0.55
	var g := GRAVITY * (1.35 if velocity.y < 0.0 else 1.0)
	velocity.y = maxf(velocity.y - g * delta, -30.0)

	if Input.is_action_just_pressed("attack"):
		attack()

	var falling := velocity.y < 0.0
	move_and_slide()
	_check_monsters(falling)
	_update_swing(delta)

	# remember a safe spot to come back to after a fall
	if is_on_floor():
		ground_time += delta
		if ground_time > 0.3:
			safe_pos = global_position
	else:
		ground_time = 0.0
	if global_position.y < kill_y:
		fall_out()
	hurt_time = maxf(0.0, hurt_time - delta)
	_animate(delta, on_floor)


func _jump(speed: float, sound: String) -> void:
	velocity.y = speed
	coyote = 0.0
	buffer = 0.0
	model.scale = Vector3(0.8, 1.25, 0.8)
	Sfx.play(sound)


## Starts a sword swing. The hit lands a moment later (see _update_swing).
func attack() -> void:
	if swing > 0.0:
		return
	swing = SWING_TIME
	swing_hit_done = false
	Sfx.play("swing")


func _update_swing(delta: float) -> void:
	if swing <= 0.0:
		return
	swing -= delta
	var p := 1.0 - swing / SWING_TIME
	# the arm sweeps from the Hero's right side across to his left
	arms[1].rotation_degrees = Vector3(-80, lerpf(-70.0, 80.0, ease(p, 0.5)), 0)
	sword.rotation_degrees = Vector3(80, 0, 0)
	if not swing_hit_done and p > 0.3:
		swing_hit_done = true
		sword_hit()
	if swing <= 0.0:
		_rest_sword()


## Hits everything in front of the Hero within reach (monsters, levers). Returns how many.
func sword_hit() -> int:
	var hits := 0
	var fwd := facing()
	fwd.y = 0
	fwd = fwd.normalized()
	for n in get_tree().get_nodes_in_group("hittable"):
		var to: Vector3 = n.global_position - global_position
		if absf(to.y) > 1.9:
			continue
		var flat := Vector3(to.x, 0, to.z)
		if flat.length() > SWORD_REACH:
			continue
		if flat.length() > 0.5 and fwd.dot(flat.normalized()) < 0.1:
			continue
		n.on_sword_hit(self)
		hits += 1
	return hits


## Jump on a monster's head to beat it; touch it any other way and it hurts.
func _check_monsters(falling: bool) -> void:
	for z in get_tree().get_nodes_in_group("monsters"):
		if not z.alive:
			continue
		var to: Vector3 = global_position - z.global_position
		var flat := Vector2(to.x, to.z).length()
		if flat > 1.1:
			continue
		if falling and to.y > 0.9 and to.y < 2.3:
			z.stomp()
			velocity.y = 11.0
			air_jumps = 1
		elif absf(to.y) < 1.2:
			hurt(z.global_position)


func hurt(from: Vector3) -> void:
	if hurt_time > 0.0:
		return
	hurt_time = INVULNERABLE
	Sfx.play("hurt")
	var push := global_position - from
	push.y = 0
	push = push.normalized() * 9.0 if push.length() > 0.01 else -facing() * 9.0
	velocity = Vector3(push.x, 7.0, push.z)
	if Game.lose_heart():
		_back_to_start()
	else:
		Game.say("Ouch!")


## Fell into lava or off the world: lose a heart and pop back to a safe spot.
func fall_out() -> void:
	if hurt_time > INVULNERABLE - 0.3 and global_position.y > kill_y:
		return   # just got hurt; don't count the same splash twice
	Sfx.play("hurt")
	hurt_time = INVULNERABLE
	if Game.lose_heart():
		_back_to_start()
		return
	Game.say("Oops! Try again.")
	teleport(safe_pos + Vector3(0, 0.2, 0), model.rotation.y)


func _back_to_start() -> void:
	Game.say("Out of hearts! Back to the start.")
	var main := get_parent()
	if main != null and "level" in main and main.level != null:
		var s: Array = main.level.spawns["start"]
		teleport(s[0], s[1])
	else:
		teleport(safe_pos)


func _animate(delta: float, on_floor: bool) -> void:
	var speed := Vector2(velocity.x, velocity.z).length()
	# squash when landing, stretch back to normal
	if on_floor and not was_on_floor:
		model.scale = Vector3(1.25, 0.75, 1.25)
	was_on_floor = on_floor
	model.scale = model.scale.lerp(Vector3.ONE, minf(1.0, 10.0 * delta))
	# double-jump flip
	if flip > 0.0:
		flip = maxf(0.0, flip - delta * 2.6)
		model.rotation.x = -(1.0 - flip) * TAU
		if flip == 0.0:
			model.rotation.x = 0.0
	# running: swing the legs and arms, bob up and down
	if on_floor and speed > 0.5:
		run_phase += delta * speed * 1.7
		var s := sin(run_phase)
		legs[0].rotation.x = s * 0.9
		legs[1].rotation.x = -s * 0.9
		arms[0].rotation.x = -s * 0.7
		if swing <= 0.0:
			arms[1].rotation.x = deg_to_rad(-20) + s * 0.5
		model.position.y = absf(s) * 0.12
	elif not on_floor:
		legs[0].rotation.x = -0.6
		legs[1].rotation.x = 0.4
		arms[0].rotation.x = -2.2
		model.position.y = 0.0
	else:
		for l in legs:
			l.rotation.x = lerpf(l.rotation.x, 0.0, minf(1.0, 12.0 * delta))
		arms[0].rotation.x = lerpf(arms[0].rotation.x, 0.0, minf(1.0, 12.0 * delta))
		model.position.y = 0.0
	# blink while hurt
	model.visible = hurt_time <= 0.0 or int(hurt_time * 12.0) % 2 == 0
