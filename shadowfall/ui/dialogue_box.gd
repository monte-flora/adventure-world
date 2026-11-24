extends CanvasLayer
## The 3-line text box, shown only when someone talks (docs/teen/art/README.md, HUD row).
##   var box = preload("res://ui/dialogue_box.tscn").instantiate(); add_child(box)
##   box.say("Warden Hollis", "The *Dawnstone* sleeps beneath the Weepingwold.")
##   await box.finished
## Long text is split into pages of 3 lines; JUMP / INTERACT / ATTACK shows the next page (or
## the rest of a page still typing). *Word* marks the important word in light0.
##   await box.talk(Conversation.new("maera"))     a whole talk from rules/data/people.json: its pages,
##                                                 then its choices (UP/DOWN picks, JUMP/INTERACT/ATTACK takes)
## A face (art/ui/faces/<look>.png, made with Gemini: art/gemini/README.txt) shows in a small frame left of the
## box when the speaker has one: talk() finds it from the person's look; say(..., face) takes a texture.
## A moving face (art/ui/faces/<look>_anim.png, a strip of 64x64 frames, + <look>_anim.json {"fps", "frames"})
## plays while the words type, then rests on its frame 0; say(..., face, anim) takes face_anim_for(look).

signal finished
signal chosen(i: int)

const LAYER := GloomLight.HUD_LAYER + 10
const LINES := 3
const WIDTH := 640                     # text width (px) inside the frame
const CHARS_PER_SECOND := 60.0
const FACES := "res://art/ui/faces/"
const FACE_GAP := 8                    # px between the face's frame and the box

var pages: PackedStringArray = []      # each page: up to 3 lines joined by "\n", with *marks*
var page := 0
var speaker_label: Label
var text: RichTextLabel
var _panel: PanelContainer
var face_panel: PanelContainer         # the speaker's face, left of the box (hidden when they have none)
var face_rect: TextureRect
var anim_frames: Array[Texture2D] = [] # the moving face's frames ([] for a still face)
var anim_fps := 10.0
var _anim_time := 0.0
var _shown_chars := 0.0
var choices: PackedStringArray = []    # shown instead of the text while you pick one
var cursor := 0


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
	face_panel = PanelContainer.new()
	face_panel.add_theme_stylebox_override("panel", UiStyle.frame(12))
	face_panel.visible = false
	add_child(face_panel)
	face_rect = TextureRect.new()
	face_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	face_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	face_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	var inner := _panel.custom_minimum_size.y - 24
	face_rect.custom_minimum_size = Vector2(inner, inner)
	face_panel.add_child(face_rect)
	visible = false


## The face of someone with this look (art/ui/faces/<look>.png), or null if none has been made.
static func face_for(look: String) -> Texture2D:
	var p := FACES + look + ".png"
	return load(p) if look != "" and ResourceLoader.exists(p) else null


## The moving face of this look: {"fps": .., "frames": [AtlasTexture, ..]} from <look>_anim.png/.json,
## or {} if none has been made.
static func face_anim_for(look: String) -> Dictionary:
	var p := FACES + look + "_anim"
	if look == "" or not ResourceLoader.exists(p + ".png") or not FileAccess.file_exists(p + ".json"):
		return {}
	var meta = JSON.parse_string(FileAccess.get_file_as_string(p + ".json"))
	return face_anim(load(p + ".png"), meta) if meta is Dictionary else {}


## A strip of frames side by side + its .json ({"fps", "frames", "size"}) -> {"fps", "frames": [AtlasTexture]}.
static func face_anim(strip: Texture2D, meta: Dictionary) -> Dictionary:
	if strip == null:
		return {}
	var size := Vector2(meta.get("size", [64, 64])[0], meta.get("size", [64, 64])[1])
	var frames: Array[Texture2D] = []
	for i in mini(int(meta.get("frames", 0)), int(strip.get_width() / size.x)):
		var t := AtlasTexture.new()
		t.atlas = strip
		t.region = Rect2(Vector2(i * size.x, 0), size)
		frames.append(t)
	return {"fps": float(meta.get("fps", 10)), "frames": frames} if not frames.is_empty() else {}


## Shows `face` beside the box (or the moving face `anim`, resting on its frame 0); hides the slot when
## there is neither.
func show_face(face: Texture2D, anim := {}) -> void:
	anim_frames.assign(anim.get("frames", []))
	anim_fps = float(anim.get("fps", 10.0))
	_anim_time = 0.0
	face_rect.texture = anim_frames[0] if not anim_frames.is_empty() else face
	face_panel.visible = face_rect.texture != null


## Shows `speaker`'s words, page by page. Emits `finished` after the last page.
func say(speaker: String, words: String, face: Texture2D = null, anim := {}) -> void:
	show_face(face, anim)
	speaker_label.text = speaker
	speaker_label.visible = speaker != ""
	pages = paginate(words)
	page = 0
	visible = true
	_show_page()


func is_open() -> bool:
	return visible


## Runs a Conversation to its end. Returns what it opens after ("shop", "forge" or "").
func talk(c) -> String:
	var look := str(c.person.get("look", ""))
	var face := face_for(look)
	var anim := face_anim_for(look)
	while not c.done:
		say(c.name(), c.page(), face, anim)
		await finished
		var cs: PackedStringArray = c.choice_texts()
		if cs.is_empty():
			c.next_page()
		else:
			c.choose(await ask(c.name(), cs, face, anim))
	return c.then


## Shows `options` to pick from; returns the index picked.
func ask(speaker: String, options: PackedStringArray, face: Texture2D = null, anim := {}) -> int:
	show_face(face, anim)
	speaker_label.text = speaker
	speaker_label.visible = speaker != ""
	choices = options
	cursor = 0
	visible = true
	_show_choices()
	var i: int = await chosen
	return i


func _show_choices() -> void:
	var lines := PackedStringArray()
	for i in choices.size():
		var t := choices[i].replace("[", "[lb]")
		lines.append(("[color=#%s]> %s[/color]" % [UiStyle.LIGHT0.to_html(false), t]) if i == cursor else "  " + t)
	text.text = "\n".join(lines)
	text.visible_characters = -1


func _pick(i: int) -> void:
	choices = []
	visible = false
	chosen.emit(i)


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
	_panel.position.y = UiStyle.VIEW.y - 24 - _panel.size.y      # grows up when there are 4+ choices
	face_panel.position = Vector2(_panel.position.x - FACE_GAP - face_panel.size.x, UiStyle.VIEW.y - 24 - face_panel.size.y)
	if visible and text.visible_characters >= 0:
		_shown_chars += delta * CHARS_PER_SECOND
		text.visible_characters = int(_shown_chars)
		if text.visible_characters >= text.get_total_character_count():
			text.visible_characters = -1
	_animate_face(delta)


## The moving face plays while the words type, then rests on frame 0.
func _animate_face(delta: float) -> void:
	if anim_frames.is_empty():
		return
	var typing := visible and choices.is_empty() and text.visible_characters >= 0
	_anim_time = _anim_time + delta if typing else 0.0
	face_rect.texture = anim_frames[int(_anim_time * anim_fps) % anim_frames.size()]


func _unhandled_input(event: InputEvent) -> void:
	if visible and not choices.is_empty():
		if event.is_action_pressed("move_up") or event.is_action_pressed("move_down"):
			cursor = wrapi(cursor + (1 if event.is_action_pressed("move_down") else -1), 0, choices.size())
			_show_choices()
		elif event.is_action_pressed("jump") or event.is_action_pressed("interact") or event.is_action_pressed("attack"):
			_pick(cursor)
		get_viewport().set_input_as_handled()
	elif visible and (event.is_action_pressed("jump") or event.is_action_pressed("interact") or event.is_action_pressed("attack")):
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
