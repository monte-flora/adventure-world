extends Area3D
## An invisible box that does something when the Hero walks in:
## kind "hazard" (lava: costs a heart) or "portal" (go to another level).

const B = preload("res://scripts/build.gd")

var kind := "hazard"
var size := Vector3.ONE
var to_level := ""
var to_spawn := ""


func _ready() -> void:
	add_to_group(kind)
	collision_layer = 0
	collision_mask = B.PLAYER
	var s := BoxShape3D.new()
	s.size = size
	B.shape(self, s)
	body_entered.connect(_on_body)


func _on_body(b: Node) -> void:
	if not b.is_in_group("player"):
		return
	if kind == "hazard":
		b.fall_out()
	elif kind == "portal":
		Sfx.play("portal")
		Game.travel(to_level, to_spawn)
