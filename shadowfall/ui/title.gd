extends Control
## The title screen: the Shadowfall logo, a line of lore, and the menu
## (Continue when there is a save, New journey, Quit on desktop). UP/DOWN choose, SPACE/G confirm.
## Applies the player's settings (volume, remapped keys) once per run.

const LOGO := "res://ui/fonts/shadowfall_logo.png"

static var _settings_applied := false

var items: PackedStringArray = []
var cursor := 0
var _rows: Array[Label] = []


func _ready() -> void:
	if not _settings_applied:
		UiSettings.load_and_apply()
		_settings_applied = true
	theme = UiStyle.theme()
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var bg := ColorRect.new()
	bg.color = UiStyle.INK0
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var logo := TextureRect.new()
	logo.texture = load(LOGO)
	logo.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	logo.stretch_mode = TextureRect.STRETCH_KEEP
	logo.size = logo.texture.get_size()
	logo.scale = Vector2(2, 2)
	logo.position = Vector2((UiStyle.VIEW.x - logo.size.x * 2) / 2, 96)
	add_child(logo)
	var lore := UiStyle.label("The last light gutters. The Shadow King wakes.", "body", UiStyle.INK5)
	_center(lore, 96 + logo.size.y * 2 + 24)
	items = PackedStringArray(["Continue"]) if Game.has_save() else PackedStringArray()
	items.append("New journey")
	if not OS.has_feature("web"):
		items.append("Quit")
	for i in items.size():
		var row := UiStyle.label("", "body", UiStyle.INK6, UiStyle.BODY * 2)
		_center(row, 340 + i * UiStyle.BODY * 2 + i * 4)
		_rows.append(row)
	var hint := UiStyle.label("UP/DOWN choose   SPACE confirm", "small", UiStyle.INK4)
	_center(hint, UiStyle.VIEW.y - 24)
	_draw_menu()


func _center(l: Label, y: float) -> void:
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.position = Vector2(0, y)
	l.size.x = UiStyle.VIEW.x
	add_child(l)


func _draw_menu() -> void:
	for i in _rows.size():
		var on := i == cursor
		_rows[i].text = ("> %s <" if on else "%s") % items[i]
		_rows[i].add_theme_color_override("font_color", UiStyle.LIGHT0 if on else UiStyle.INK5)


func press(action: String) -> void:
	match action:
		"move_up":
			cursor = posmod(cursor - 1, items.size())
			_draw_menu()
		"move_down":
			cursor = posmod(cursor + 1, items.size())
			_draw_menu()
		"jump", "interact":
			choose(items[cursor])


func choose(item: String) -> void:
	match item:
		"Continue":
			if not Game.load_save():
				Game.reset()
			Scenes.goto("overworld")
		"New journey":
			Game.reset()
			Scenes.goto("overworld")
		"Quit":
			get_tree().quit()


func _unhandled_input(event: InputEvent) -> void:
	for a in ["move_up", "move_down", "jump", "interact"]:
		if event.is_action_pressed(a):
			press(a)
			get_viewport().set_input_as_handled()
			return
