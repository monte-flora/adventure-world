extends Node3D
## A friendly follow camera that orbits behind the Hero.
## Q / E (or drag with the right mouse button) turn it; the mouse wheel zooms.

const B = preload("res://scripts/build.gd")

var target: Node3D
var yaw := 0.0
var pitch := -0.38
var distance := 8.0
var arm: SpringArm3D
var camera: Camera3D


func _ready() -> void:
	arm = SpringArm3D.new()
	arm.collision_mask = B.WORLD
	arm.margin = 0.3
	var s := SphereShape3D.new()
	s.radius = 0.3
	arm.shape = s
	add_child(arm)
	camera = Camera3D.new()
	camera.fov = 62.0
	camera.current = true
	arm.add_child(camera)
	_apply()


func snap() -> void:
	if target:
		global_position = target.global_position + Vector3(0, 1.4, 0)
	_apply()


func _apply() -> void:
	arm.spring_length = distance
	arm.rotation = Vector3(pitch, yaw, 0)
	if target is CollisionObject3D:
		arm.clear_excluded_objects()
		arm.add_excluded_object(target.get_rid())


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and event.button_mask & MOUSE_BUTTON_MASK_RIGHT:
		yaw -= event.relative.x * 0.008
		pitch = clampf(pitch - event.relative.y * 0.006, -1.2, 0.15)
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP:
			distance = maxf(4.0, distance - 0.6)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			distance = minf(14.0, distance + 0.6)


func _process(delta: float) -> void:
	var turn := Input.get_axis("cam_right", "cam_left")
	yaw += turn * 2.6 * delta
	if target:
		var goal := target.global_position + Vector3(0, 1.4, 0)
		global_position = global_position.lerp(goal, minf(1.0, 9.0 * delta))
		if "cam_yaw" in target:
			target.cam_yaw = yaw
	arm.spring_length = distance
	arm.rotation = Vector3(pitch, yaw, 0)
