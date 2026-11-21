extends CanvasLayer
## The 3-line text box, shown only when someone talks (docs/teen/art/README.md, HUD row).
##   var box = preload("res://ui/dialogue_box.tscn").instantiate(); add_child(box)
##   box.say("Warden Hollis", "The *Dawnstone* sleeps beneath the Weepingwold.")
##   await box.finished
## Long text is split into pages of 3 lines; JUMP / INTERACT / ATTACK shows the next page (or
## the rest of a page still typing). *Word* marks the important word in light0.

signal finished

const LAYER := 60
const LINES := 3
const WIDTH := 640                     # text width (px) inside the frame
const CHARS_PER_SECOND := 60.0

var pages: PackedStringArray = []      # each page: up to 3 lines joined by "\n", with *marks*
var page := 0
var speaker_label: Label
var text: RichTextLabel
var _panel: PanelContainer
var _shown_chars := 0.0


func _ready() -> void:
	layer = LAYER
	process_mode = Node.PROCESS_MODE_ALWAYS
	var font := UiStyle.font("body")
	_panel = PanelContainer.new()
	_panel.theme = UiStyle.theme()
	_panel.add_theme_stylebox_override("panel", UiStyle.frame(12))
	_panel.position = Vector2((UiStyle.VIEW.x - WIDTH - 24) / 2, UiStyle.VIEW.y - 24 - (LINES + 1) * UiStyle.BODY - 24)
	_panel.custom_minimum_size = Vector2(WIDTH + 24, (LINES + 1) * UiStyle.BODY + 24)
	add_child(_panel)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 0)
	_panel.add_child(col)
	speaker_label = UiStyle.label("", "body", UiStyle.LIGHT0)
	col.add_child(speaker_label)
	text = RichTextLabel.new()
	text.bbcode_enabled = true
	text.fit_content = true
	text.scroll_active = false
	text.custom_minimum_size = Vector2(WIDTH, LINES * UiStyle.BODY)
	text.add_theme_font_override("normal_font", font)
	text.add_theme_font_size_override("normal_font_size", UiStyle.BODY)
	text.add_theme_constant_override("line_separation", 0)
	col.add_child(text)
	visible = false


## Shows `speaker`'s words, page by page. Emits `finished` after the last page.
func say(speaker: String, words: String) -> void:
	speaker_label.text = speaker
	speaker_label.visible = speaker != ""
	pages = paginate(words)
	page = 0
	visible = true
	_show_page()


func is_open() -> bool:
	return visible


## The next page, or close. A page still typing finishes first.
func advance() -> void:
	if not visible:
		return
	if text.visible_characters >= 0 and text.visible_characters < text.get_total_character_count():
		text.visible_characters = -1
		return
	page += 1
	if page >= pages.size():
		visible = false
		finished.emit()
	else:
		_show_page()


func _show_page() -> void:
	text.text = _bbcode(pages[page])
	_shown_chars = 0.0
	text.visible_characters = 0


func _process(delta: float) -> void:
	if visible and text.visible_characters >= 0:
		_shown_chars += delta * CHARS_PER_SECOND
		text.visible_characters = int(_shown_chars)
		if text.visible_characters >= text.get_total_character_count():
			text.visible_characters = -1


func _unhandled_input(event: InputEvent) -> void:
	if visible and (event.is_action_pressed("jump") or event.is_action_pressed("interact") or event.is_action_pressed("attack")):
		advance()
		get_viewport().set_input_as_handled()


## Word-wraps `words` to WIDTH in the body font, then groups the lines 3 to a page.
## A blank line ("\n\n") always starts a new page.
static func paginate(words: String) -> PackedStringArray:
	var font := UiStyle.font("body")
	var out := PackedStringArray()
	for para in words.split("\n\n", false):
		var lines := PackedStringArray()
		var line := ""
		for w in para.strip_edges().split(" ", false):
			var trial := w if line == "" else line + " " + w
			if line != "" and font.get_string_size(trial.replace("*", ""), HORIZONTAL_ALIGNMENT_LEFT, -1, UiStyle.BODY).x > WIDTH:
				lines.append(line)
				line = w
			else:
				line = trial
		if line != "":
			lines.append(line)
		for i in range(0, lines.size(), LINES):
			out.append("\n".join(lines.slice(i, i + LINES)))
	if out.is_empty():
		out.append("")
	return out


## *word* -> the word in light0. Square brackets from the text are shown, not read as tags.
static func _bbcode(s: String) -> String:
	s = s.replace("[", "[lb]")
	var parts := s.split("*")
	var out := ""
	for i in parts.size():
		out += ("[color=#%s]%s[/color]" % [UiStyle.LIGHT0.to_html(false), parts[i]]) if i % 2 == 1 else parts[i]
	return out
