extends Area3D
## A lever on a post. Walk into it or hit it with the sword to pull it; it opens its gate.

const B = preload("res://scripts/build.gd")

var gate: Node
var pulled := false
var handle: Node3D


func _ready() -> void:
	add_to_group("hittable")
	add_to_group("levers")
	collision_layer = 0
	collision_mask = B.PLAYER
	var s := SphereShape3D.new()
	s.radius = 1.1
	B.shape(self, s, Vector3(0, 0.8, 0))
	B.box(self, Vector3(0.9, 0.5, 0.6), Color("6b4a2e"), Vector3(0, 0.25, 0))
	B.box(self, Vector3(1.0, 0.1, 0.7), Color("ffd23c"), Vector3(0, 0.52, 0))
	handle = Node3D.new()
	handle.position = Vector3(0, 0.5, 0)
	add_child(handle)
	B.cyl(handle, 0.06, 0.06, 1.0, Color("c9cdd6"), Vector3(0, 0.5, 0), Vector3.ZERO, 6)
	B.ball(handle, 0.17, Color("e8322c"), Vector3(0, 1.05, 0), 1.0, 0.4)
	handle.rotation_degrees = Vector3(0, 0, 40)
	body_entered.connect(_on_body)


func _on_body(b: Node) -> void:
	if b.is_in_group("player"):
		pull()


func on_sword_hit(_by: Node3D) -> void:
	pull()


func pull() -> void:
	if pulled:
		return
	pulled = true
	Sfx.play("lever")
	if is_inside_tree():
		create_tween().tween_property(handle, "rotation_degrees:z", -40.0, 0.25)
	if gate:
		gate.open()
	Game.say("Click! The gate is open!")
