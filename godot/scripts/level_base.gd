extends Node3D
## What every level has: where the Hero can appear, how far he can fall, and its name.

const B = preload("res://scripts/build.gd")
const Diamond = preload("res://scripts/diamond.gd")
const Trigger = preload("res://scripts/trigger.gd")

var title := ""
var kill_y := -12.0
var spawns := {}          # name -> [position, facing yaw]


func spawn_pos(name: String) -> Vector3:
	return spawns[name][0]


func add_diamond(id: String, pos: Vector3, big := false) -> Node:
	var d := Diamond.new()
	d.id = id
	d.big = big
	d.position = pos
	add_child(d)
	return d


func add_trigger(kind: String, pos: Vector3, size: Vector3, to_level := "", to_spawn := "") -> Node:
	var t := Trigger.new()
	t.kind = kind
	t.size = size
	t.to_level = to_level
	t.to_spawn = to_spawn
	t.position = pos
	add_child(t)
	return t
