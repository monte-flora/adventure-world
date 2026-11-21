extends Node2D
## The overworld (top-down). B1 owns this folder: TileMapLayer from levels/world/*.txt, the hero,
## camera, waystones, map monsters, Hearthvale and the Nightfall mirror.
## Placeholder: an empty field; arrows walk, G (interact) enters the first cave.

const TILE := LevelFile.TILE
var hero: CharacterBody2D


func _ready() -> void:
	var note := Label.new()
	note.text = "The Realm (overworld placeholder, B1)\nG: enter a cave   ESC: pause"
	note.position = Vector2(16, 16)
	add_child(note)
	hero = CharacterBody2D.new()
	hero.motion_mode = CharacterBody2D.MOTION_MODE_FLOATING
	hero.position = Vector2(480, 270)
	var box := ColorRect.new()
	box.color = Color("e6c878")
	box.size = Vector2(16, 24)
	box.position = Vector2(-8, -12)
	hero.add_child(box)
	add_child(hero)


func _physics_process(_dt: float) -> void:
	hero.velocity = Controls.move_vector() * 176.0      # 5.5 squares/s (gameplay spec)
	hero.move_and_slide()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		Scenes.goto("cave")
