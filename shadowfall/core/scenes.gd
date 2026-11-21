extends Node
## Switches between the game's screens (autoload `Scenes`), and opens the pause screen.
##   Scenes.goto("cave", {"file": "caves/01_the_easy_moss_cave.txt"})
## The screen reads its arguments from Scenes.args in _ready(). Owned by core (B0).

signal switched(name: String)

## Each screen's scene. A worker owns the scene in its own folder; add a new screen here (ask B0).
const SCENES := {
	"boot": "res://core/boot.tscn",
	"title": "res://ui/title.tscn",
	"overworld": "res://overworld/overworld.tscn",
	"cave": "res://caves/cave.tscn",
	"boss": "res://boss/boss.tscn",
}
const PAUSE_SCENE := "res://ui/pause.tscn"
const PAUSABLE := ["overworld", "cave", "boss"]

var current := ""
var args := {}
var screen: Node                       # the screen now showing
## Tests set a host node: screens then go inside it instead of replacing the whole scene.
var host: Node
var _pause: Node


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS


func goto(scene_name: String, scene_args := {}) -> void:
	assert(SCENES.has(scene_name), "no such screen: " + scene_name)
	resume()
	current = scene_name
	args = scene_args
	if host:
		for c in host.get_children():
			c.queue_free()
		screen = load(SCENES[scene_name]).instantiate()
		host.add_child(screen)
	else:
		get_tree().change_scene_to_file(SCENES[scene_name])
		screen = null
	Game.gloom_running = scene_name in PAUSABLE
	switched.emit(scene_name)


func is_paused() -> bool:
	return _pause != null


func pause() -> void:
	if _pause or current not in PAUSABLE:
		return
	_pause = load(PAUSE_SCENE).instantiate()
	_pause.process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	add_child(_pause)
	get_tree().paused = true


func resume() -> void:
	if _pause:
		_pause.queue_free()
		_pause = null
	get_tree().paused = false


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		if _pause:
			resume()
		else:
			pause()
		get_viewport().set_input_as_handled()
