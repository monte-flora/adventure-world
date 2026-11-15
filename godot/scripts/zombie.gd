extends CharacterBody3D
## A Zombie: shuffles back and forth, chases the Hero when he comes close,
## and is beaten by 3 sword hits or one jump on its head.

const B = preload("res://scripts/build.gd")

const WALK := 1.6
const CHASE := 3.3
const SEE := 8.0
const GIVE_UP := 13.0
const GRAVITY := 30.0

var hp := 3
var alive := true
var patrol: Array = []
var _leg := 0
var state := "patrol"
var stun := 0.0
var t := 0.0
var groan := 2.0
var model: Node3D
var arms: Array[Node3D] = []
var legs: Array[Node3D] = []
var _flash: Array[MeshInstance3D] = []


func _ready() -> void:
	add_to_group("monsters")
	add_to_group("hittable")
	collision_layer = B.MONSTER
	collision_mask = B.WORLD
	var cap := CapsuleShape3D.new()
	cap.radius = 0.45
	cap.height = 1.8
	B.shape(self, cap, Vector3(0, 0.9, 0))
	if patrol.is_empty():
		patrol = [global_position, global_position]
	_build_model()


func _build_model() -> void:
	model = Node3D.new()
	add_child(model)
	var skin := Color("8fd16a")
	var shirt := Color("8a4fc4")
	var pants := Color("5a5f6e")
	for side in [-1, 1]:
		var hip := Node3D.new()
		hip.position = Vector3(0.2 * side, 0.6, 0)
		model.add_child(hip)
		B.box(hip, Vector3(0.26, 0.6, 0.28), pants, Vector3(0, -0.3, 0))
		B.box(hip, Vector3(0.3, 0.14, 0.4), Color("3a2a1e"), Vector3(0, -0.56, -0.05))
		legs.append(hip)
	_flash.append(B.box(model, Vector3(0.78, 0.7, 0.45), shirt, Vector3(0, 0.98, 0), Vector3(0, 0, 4)))
	B.box(model, Vector3(0.3, 0.2, 0.47), Color("6c3a9c"), Vector3(0.18, 0.75, 0))  # a torn patch
	_flash.append(B.box(model, Vector3(0.62, 0.6, 0.58), skin, Vector3(0.03, 1.62, -0.02), Vector3(0, 0, -8)))
	B.box(model, Vector3(0.66, 0.14, 0.62), Color("3f6b2a"), Vector3(0.03, 1.94, -0.02), Vector3(0, 0, -8))  # messy hair
	for side in [-1, 1]:
		B.box(model, Vector3(0.14, 0.14, 0.05), Color("ffef5a"), Vector3(0.14 * side, 1.68, -0.32), Vector3.ZERO, 1.5)
		B.box(model, Vector3(0.06, 0.06, 0.03), Color("1a1a1a"), Vector3(0.14 * side, 1.68, -0.35))
	B.box(model, Vector3(0.3, 0.07, 0.04), Color("2e4a20"), Vector3(0.03, 1.45, -0.32))
	for side in [-1, 1]:
		var sh := Node3D.new()
		sh.position = Vector3(0.48 * side, 1.18, 0)
		model.add_child(sh)
		B.box(sh, Vector3(0.2, 0.2, 0.75), shirt, Vector3(0, 0, -0.3))
		_flash.append(B.box(sh, Vector3(0.18, 0.18, 0.25), skin, Vector3(0, 0, -0.78)))
		arms.append(sh)


func _player() -> Node3D:
	return get_tree().get_first_node_in_group("player") as Node3D


func _physics_process(delta: float) -> void:
	if not alive:
		return
	t += delta
	var p := _player()
	var dist := INF
	if p:
		dist = (p.global_position - global_position).length()
	if state == "patrol" and dist < SEE:
		state = "chase"
		Sfx.play("zombie")
	elif state == "chase" and dist > GIVE_UP:
		state = "patrol"
	var goal: Vector3 = patrol[_leg]
	var speed := WALK
	if state == "chase" and p:
		goal = p.global_position
		speed = CHASE
	var to := goal - global_position
	to.y = 0
	if state == "patrol" and to.length() < 0.4:
		_leg = (_leg + 1) % patrol.size()
	var move := Vector3.ZERO
	if to.length() > 0.2:
		move = to.normalized() * speed
	if stun > 0.0:
		stun -= delta
		velocity.x = move_toward(velocity.x, 0, 20 * delta)
		velocity.z = move_toward(velocity.z, 0, 20 * delta)
	else:
		velocity.x = move.x
		velocity.z = move.z
		if move.length() > 0.1:
			model.rotation.y = lerp_angle(model.rotation.y, atan2(-move.x, -move.z), minf(1.0, 6.0 * delta))
	velocity.y -= GRAVITY * delta
	move_and_slide()
	if global_position.y < -20.0:
		queue_free()
	# shuffle
	var s := sin(t * (7.0 if state == "chase" else 4.0))
	legs[0].rotation.x = s * 0.5
	legs[1].rotation.x = -s * 0.5
	arms[0].rotation.x = 0.15 + s * 0.15
	arms[1].rotation.x = 0.15 - s * 0.15
	model.rotation.z = s * 0.08
	groan -= delta
	if groan <= 0.0 and state == "chase":
		groan = randf_range(2.0, 4.0)
		Sfx.play("zombie")


func on_sword_hit(by: Node3D) -> void:
	take_hit(by.global_position)


func take_hit(from: Vector3) -> void:
	if not alive:
		return
	hp -= 1
	Sfx.play("hit")
	var push := global_position - from
	push.y = 0
	if push.length() > 0.01:
		push = push.normalized() * 8.0
	velocity = Vector3(push.x, 4.0, push.z)
	stun = 0.45
	state = "chase"
	_flash_white()
	if hp <= 0:
		die(false)


func stomp() -> void:
	if not alive:
		return
	hp = 0
	Sfx.play("stomp")
	die(true)


func die(squashed: bool) -> void:
	alive = false
	remove_from_group("monsters")
	remove_from_group("hittable")
	collision_layer = 0
	Game.say("Zombie beaten!")
	if not is_inside_tree():
		return
	var tw := create_tween()
	if squashed:
		tw.tween_property(model, "scale", Vector3(1.5, 0.12, 1.5), 0.12)
		tw.tween_interval(0.5)
	else:
		tw.tween_property(model, "rotation:x", -PI / 2.0, 0.35)
		tw.tween_interval(0.3)
	tw.tween_property(model, "scale", Vector3(0.01, 0.01, 0.01), 0.25)
	tw.tween_callback(queue_free)


func _flash_white() -> void:
	for m in _flash:
		m.material_overlay = B.mat(Color(1, 1, 1, 1), 2.0)
	get_tree().create_timer(0.12).timeout.connect(_unflash)


func _unflash() -> void:
	for m in _flash:
		if is_instance_valid(m):
			m.material_overlay = null
