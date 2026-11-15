extends StaticBody3D
## Iron bars across the cave. A lever opens them (they slide down into the floor).

const B = preload("res://scripts/build.gd")

var width := 10.0
var height := 4.0
var is_open := false
var bars: Node3D
var _shape: CollisionShape3D


func _ready() -> void:
	add_to_group("gates")
	collision_layer = B.WORLD
	bars = Node3D.new()
	add_child(bars)
	var n := int(width / 0.8)
	for i in n + 1:
		var x := -width / 2.0 + i * width / n
		B.cyl(bars, 0.09, 0.09, height, Color("4a4f5c"), Vector3(x, height / 2.0, 0), Vector3.ZERO, 6)
		B.prism(bars, Vector3(0.25, 0.3, 0.25), Color("4a4f5c"), Vector3(x, height + 0.15, 0))
	for y in [0.6, height - 0.6]:
		B.box(bars, Vector3(width, 0.18, 0.18), Color("3a3e48"), Vector3(0, y, 0))
	var s := BoxShape3D.new()
	s.size = Vector3(width, height + 2.0, 0.6)
	_shape = B.shape(self, s, Vector3(0, (height + 2.0) / 2.0, 0))


func open() -> void:
	if is_open:
		return
	is_open = true
	_shape.set_deferred("disabled", true)
	Sfx.play("gate")
	if is_inside_tree():
		var tw := create_tween()
		tw.tween_property(bars, "position:y", -height - 0.4, 1.2).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)


func is_blocking() -> bool:
	return not _shape.disabled
