extends Node2D
## The Shadow King's castle and throne room. B8 owns this folder (castle levels from
## levels/castle/*.txt, the 3-phase Shadow King). Placeholder: a label.

func _ready() -> void:
	var note := Label.new()
	note.text = "The Shadow King's throne (placeholder, B8)"
	note.position = Vector2(16, 16)
	add_child(note)
