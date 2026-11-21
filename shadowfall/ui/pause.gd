extends CanvasLayer
## The pause screen, opened by Scenes.pause() (ESC / Start). B5 owns it: quest log, map, sigils,
## volume, remapping. Placeholder: a dim layer, ESC resumes, G saves and goes to the title.

func _ready() -> void:
	layer = 100
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var label := Label.new()
	label.text = "PAUSED\n\nESC: back   G: save and leave"
	label.position = Vector2(400, 240)
	add_child(label)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("interact"):
		Game.save()
		Scenes.goto("title")
