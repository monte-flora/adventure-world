extends Area3D
## A spinning diamond. Touch it to collect it; it stays collected.

const B = preload("res://scripts/build.gd")

var id := ""
var big := false
var color := Color("4fe3ff")
var gem: Node3D
var t := 0.0
var taken := false


func _ready() -> void:
	add_to_group("diamonds")
	collision_layer = 0
	collision_mask = B.PLAYER
	if id != "" and Game.has_collected(id):
		queue_free()
		return
	var s := SphereShape3D.new()
	s.radius = 0.7 if not big else 1.1
	B.shape(self, s, Vector3(0, 0.0, 0))
	gem = Node3D.new()
	add_child(gem)
	var k := 1.7 if big else 1.0
	B.cyl(gem, 0.0, 0.38 * k, 0.5 * k, color, Vector3(0, 0.25 * k, 0), Vector3.ZERO, 6, 0.6)
	B.cyl(gem, 0.38 * k, 0.0, 0.32 * k, color.lightened(0.35), Vector3(0, -0.16 * k, 0), Vector3.ZERO, 6, 0.6)
	t = randf() * TAU
	body_entered.connect(_on_body)


func _process(delta: float) -> void:
	if gem == null or taken:
		return
	t += delta
	gem.rotation.y += delta * 2.5
	gem.position.y = sin(t * 2.5) * 0.15


func _on_body(b: Node) -> void:
	if b.is_in_group("player"):
		collect()


func collect() -> void:
	if taken:
		return
	taken = true
	if Game.collect_diamond(id):
		Sfx.play("diamond")
	set_deferred("monitoring", false)
	if gem and is_inside_tree():
		var tw := create_tween()
		tw.tween_property(gem, "position:y", 1.2, 0.2)
		tw.parallel().tween_property(gem, "scale", Vector3(0.05, 0.05, 0.05), 0.25)
		tw.tween_callback(queue_free)
	else:
		queue_free()
