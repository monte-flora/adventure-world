extends Node3D
## Sets everything up: the Hero, the camera, the HUD, and whichever level he's in.
## Run with `-- --cave` to start in the cave, or `-- --shots` to save screenshots and quit.

const Player = preload("res://scripts/player.gd")
const CameraRig = preload("res://scripts/camera_rig.gd")
const Hud = preload("res://scripts/hud.gd")
const Controls = preload("res://scripts/controls.gd")
const LEVELS := {
	"meadow": preload("res://scripts/meadow.gd"),
	"cave": preload("res://scripts/cave.gd"),
}

var player: CharacterBody3D
var rig: Node3D
var hud: CanvasLayer
var level: Node3D
var level_name := ""


func _ready() -> void:
	Controls.setup()
	player = Player.new()
	add_child(player)
	rig = CameraRig.new()
	rig.target = player
	add_child(rig)
	hud = Hud.new()
	add_child(hud)
	Game.travel_requested.connect(func(l: String, s: String): go_to.call_deferred(l, s))
	var args := OS.get_cmdline_user_args()
	go_to("cave" if "--cave" in args else "meadow", "start")
	if "--shots" in args:
		_take_shots()


func go_to(name: String, spawn: String) -> void:
	if level:
		remove_child(level)
		level.free()
	level = LEVELS[name].new()
	level.name = name.capitalize()
	add_child(level)
	level_name = name
	var s: Array = level.spawns[spawn]
	player.kill_y = level.kill_y
	player.teleport(s[0], s[1])
	rig.yaw = s[1]
	rig.snap()
	Game.say(level.title)


# ---------- screenshots (needs a window: `godot --path godot -- --shots`) ----------

func _wait(frames: int) -> void:
	for i in frames:
		await get_tree().process_frame


func _shot(file: String) -> void:
	var img := get_viewport().get_texture().get_image()
	if img == null or img.is_empty():
		push_warning("no image (headless?)")
		return
	var dir := ProjectSettings.globalize_path("res://screenshots")
	DirAccess.make_dir_recursive_absolute(dir)
	img.save_png(dir.path_join(file))
	print("saved ", dir.path_join(file))


func _take_shots() -> void:
	hud.help_time = 0.0
	await _wait(20)
	# 1. the meadow: the Hero near the path, looking toward the Mine and the floating blocks
	player.teleport(Vector3(3, 0.1, 4), 2.6)
	rig.yaw = 0.15
	rig.pitch = -0.36
	rig.distance = 11.0
	rig.snap()
	await _wait(40)
	_shot("meadow.png")
	# 2. The Hero swinging at the Zombie
	var z: Node3D = level.zombie
	z.set_physics_process(false)
	z.global_position = Vector3(-2, 0, -14)
	z.model.rotation.y = 0.0
	z.model.rotation.y = PI
	player.teleport(Vector3(-2.2, 0.1, -11.6), 0.0)
	player.frozen = true
	rig.yaw = 1.75
	rig.pitch = -0.2
	rig.distance = 6.0
	rig.snap()
	await _wait(20)
	player.swing = Player.SWING_TIME * 0.55
	player._update_swing(0.0)
	await _wait(2)
	_shot("zombie.png")
	player.frozen = false
	z.set_physics_process(true)
	# 3. the cave: lava stepping stones, with the lever and gate beyond
	go_to("cave", "start")
	hud.msg_time = 0.0
	player.teleport(Vector3(-0.6, 1.9, -10.2), -0.3)
	player.frozen = true
	player.legs[0].rotation.x = -0.6
	player.legs[1].rotation.x = 0.4
	player.arms[0].rotation.x = -2.2
	rig.yaw = -0.3
	rig.pitch = -0.62
	rig.distance = 10.0
	rig.snap()
	await _wait(40)
	_shot("cave.png")
	get_tree().quit()
