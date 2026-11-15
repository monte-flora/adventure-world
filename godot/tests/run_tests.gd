extends Node
## Headless logic tests. Run:  godot --headless --path godot res://tests/run_tests.tscn
## Prints one line per check and quits with code 0 when everything passes.

const Main = preload("res://scenes/main.tscn")
const Diamond = preload("res://scripts/diamond.gd")
const Zombie = preload("res://scripts/zombie.gd")

var passed := 0
var failed := 0
var main: Node


func check(ok: bool, what: String) -> void:
	if ok:
		passed += 1
		print("  ok    ", what)
	else:
		failed += 1
		print("  FAIL  ", what)


func physics(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _ready() -> void:
	_run()


func _run() -> void:
	main = Main.instantiate()
	add_child(main)
	await physics(10)
	for test in [test_diamond, test_diamond_by_touch, test_zombie_three_hits, test_sword_swing_hits_zombie,
			test_stomp, test_zombie_hurts_hero, test_fall_off_world, test_lava, test_out_of_hearts,
			test_mine_leads_to_cave, test_lever_opens_gate, test_walk_into_lever, test_cave_exit,
			test_jumps, test_robot_crosses_cave]:
		Game.reset()
		main.player.hurt_time = 0.0
		print(test.get_method())
		await test.call()
	print("%d passed, %d failed" % [passed, failed])
	main.queue_free()
	await get_tree().process_frame
	get_tree().quit(0 if failed == 0 else 1)


func _to(level: String) -> void:
	main.go_to(level, "start")
	await physics(5)


func test_diamond() -> void:
	await _to("meadow")
	var d := Diamond.new()
	d.id = "test_a"
	d.position = Vector3(0, 40, 0)
	main.level.add_child(d)
	d.collect()
	check(Game.diamonds == 1, "collecting a diamond counts it")
	var again := Diamond.new()
	again.id = "test_a"
	main.level.add_child(again)
	again.collect()
	check(Game.diamonds == 1, "the same diamond can't be counted twice")


func test_diamond_by_touch() -> void:
	await _to("meadow")
	var d := Diamond.new()
	d.id = "test_touch"
	d.position = main.player.global_position + Vector3(0, 0.8, 0)
	main.level.add_child(d)
	await physics(10)
	check(Game.diamonds == 1, "walking into a diamond collects it")
	check(Game.has_collected("test_touch"), "and it is remembered")


func _zombie_at(pos: Vector3) -> Node:
	var z := Zombie.new()
	z.position = pos
	main.level.add_child(z)
	return z


func test_zombie_three_hits() -> void:
	await _to("meadow")
	var z := _zombie_at(Vector3(30, 0.2, 30))
	check(z.hp == 3 and z.alive, "a zombie starts with 3 hp")
	z.take_hit(Vector3(29, 0, 30))
	z.take_hit(Vector3(29, 0, 30))
	check(z.alive and z.hp == 1, "2 hits: still standing")
	z.take_hit(Vector3(29, 0, 30))
	check(not z.alive, "3 hits: beaten")
	check(not z.is_in_group("monsters"), "a beaten zombie can't hurt you")


func test_sword_swing_hits_zombie() -> void:
	await _to("meadow")
	var p: Node3D = main.player
	p.teleport(Vector3(20, 0.1, 20), 0.0)  # facing -Z
	var z := _zombie_at(Vector3(20, 0.1, 18.4))
	z.set_physics_process(false)
	var behind := _zombie_at(Vector3(20, 0.1, 21.6))
	behind.set_physics_process(false)
	await physics(2)
	p.attack()
	await physics(20)
	check(z.hp == 2, "a sword swing hits the zombie in front")
	check(behind.hp == 3, "but not the one behind")
	z.queue_free()
	behind.queue_free()


func test_stomp() -> void:
	await _to("meadow")
	var z := _zombie_at(Vector3(-20, 0.1, 30))
	z.stomp()
	check(not z.alive, "a stomp beats a zombie at once")
	var z2 := _zombie_at(Vector3(20, 0.1, 25))
	z2.set_physics_process(false)
	await physics(2)
	main.player.teleport(Vector3(20, 3.2, 25))
	main.player.velocity.y = -4.0
	await physics(30)
	check(not z2.alive, "falling onto a zombie's head stomps it")
	check(Game.hearts == Game.MAX_HEARTS, "and doesn't hurt the Hero")


func test_zombie_hurts_hero() -> void:
	await _to("meadow")
	var p: Node3D = main.player
	p.teleport(Vector3(-5, 0.1, 30))
	var z := _zombie_at(Vector3(-5.6, 0.1, 30))
	z.set_physics_process(false)
	await physics(5)
	check(Game.hearts == Game.MAX_HEARTS - 1, "touching a zombie costs a heart")
	await physics(5)
	check(Game.hearts == Game.MAX_HEARTS - 1, "only one heart, then a moment of safety")
	z.queue_free()


func test_fall_off_world() -> void:
	await _to("meadow")
	var p: Node3D = main.player
	p.teleport(Vector3(0, 0.1, 14))
	await physics(30)
	p.global_position = Vector3(80, -20, 0)
	await physics(3)
	check(Game.hearts == Game.MAX_HEARTS - 1, "falling off the world costs a heart")
	check(p.global_position.distance_to(Vector3(0, 0.3, 14)) < 1.0, "and puts the Hero back where he stood")


func test_lava() -> void:
	await _to("cave")
	var p: Node3D = main.player
	await physics(30)
	p.global_position = Vector3(3.5, -1.6, -11)
	await physics(5)
	check(Game.hearts == Game.MAX_HEARTS - 1, "lava costs a heart")
	check(p.global_position.z > -1.0, "and the Hero pops back to safe ground")


func test_out_of_hearts() -> void:
	await _to("meadow")
	var p: Node3D = main.player
	p.teleport(Vector3(10, 0.1, -20))
	for i in Game.MAX_HEARTS:
		p.hurt_time = 0.0
		p.fall_out()
	check(Game.hearts == Game.MAX_HEARTS, "out of hearts: they fill up again")
	check(p.global_position.distance_to(main.level.spawn_pos("start")) < 0.5, "and the Hero goes back to the start")


func test_mine_leads_to_cave() -> void:
	await _to("meadow")
	main.player.teleport(Vector3(0, 0.1, -27.5), 0.0)
	await physics(10)
	await get_tree().process_frame
	check(main.level_name == "cave", "walking into the Mine leads to the cave")


func test_lever_opens_gate() -> void:
	await _to("cave")
	var gate: Node = main.level.gate
	check(not gate.is_open and gate.is_blocking(), "the gate starts shut")
	main.level.lever.pull()
	await physics(2)
	check(gate.is_open and not gate.is_blocking(), "pulling the lever opens the gate")


func test_walk_into_lever() -> void:
	await _to("cave")
	var lever: Node3D = main.level.lever
	main.player.teleport(lever.global_position + Vector3(0.5, 0.1, 0))
	await physics(10)
	check(lever.pulled and main.level.gate.is_open, "walking into the lever pulls it too")


func test_cave_exit() -> void:
	await _to("cave")
	main.player.teleport(Vector3(0, 0.1, -46), 0.0)
	await physics(10)
	await get_tree().process_frame
	check(main.level_name == "meadow", "the end of the cave leads back to the meadow")
	check(main.player.global_position.distance_to(main.level.spawn_pos("from_cave")) < 1.5, "and the Hero comes out by the Mine")


func _press(action: String, frames: int) -> void:
	Input.action_press(action)
	await physics(frames)
	Input.action_release(action)


func test_jumps() -> void:
	await _to("meadow")
	var p: Node3D = main.player
	p.teleport(Vector3(-5, 0.1, 30))
	await physics(20)
	var y0 := p.global_position.y
	Input.action_press("jump")
	var top := y0
	for i in 50:
		await physics(1)
		top = maxf(top, p.global_position.y)
	Input.action_release("jump")
	await physics(30)
	check(top - y0 > 2.0, "a jump goes over 2 m high (%.2f)" % (top - y0))
	Input.action_press("jump")
	await physics(18)
	Input.action_release("jump")
	await physics(1)
	Input.action_press("jump")
	var top2 := y0
	for i in 60:
		await physics(1)
		top2 = maxf(top2, p.global_position.y)
	Input.action_release("jump")
	await physics(30)
	check(top2 - top > 1.0, "a double jump goes higher (%.2f)" % (top2 - y0))


## A robot hops along the stepping stones to the far side: the jumps can be made.
func test_robot_crosses_cave() -> void:
	await _to("cave")
	var p: Node3D = main.player
	await physics(10)
	var aims := [Vector2(0, -8), Vector2(-2, -12), Vector2(1.5, -16), Vector2(-1, -20), Vector2(0, -27)]
	var hearts := Game.hearts
	var idx := 0
	for i in 600:
		var aim: Vector2 = aims[idx]
		var me := Vector2(p.global_position.x, p.global_position.z)
		var to := aim - me
		var push := to.normalized() * minf(1.0, to.length() / 1.5)
		_steer(push)
		if p.is_on_floor() and to.length() < 5.6 and to.length() > 1.5:
			Input.action_press("jump")
		elif p.velocity.y < 0.0:
			Input.action_release("jump")
		if p.is_on_floor() and to.length() < 0.9:
			idx += 1
			if idx == aims.size():
				break
		await physics(1)
	_steer(Vector2.ZERO)
	Input.action_release("jump")
	check(Game.hearts == hearts and p.global_position.z < -26.0, "a robot hops over the lava (reached z=%.1f, hearts %d)" % [p.global_position.z, Game.hearts])


func _steer(v: Vector2) -> void:
	for pair in [["move_left", -v.x], ["move_right", v.x], ["move_forward", -v.y], ["move_back", v.y]]:
		if pair[1] > 0.05:
			Input.action_press(pair[0], pair[1])
		else:
			Input.action_release(pair[0])
