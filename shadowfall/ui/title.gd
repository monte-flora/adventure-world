extends Control
## The title screen. B5 (ui/) owns it. Placeholder: SPACE/A starts, a save continues.

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var label := Label.new()
	label.text = "SHADOWFALL\n\nThe Shadow King stirs.\n\nPress SPACE"
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(label)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("jump") or event.is_action_pressed("interact"):
		if Game.has_save():
			Game.load_save()
		else:
			Game.reset()
		Scenes.goto("overworld")
