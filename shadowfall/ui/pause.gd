extends CanvasLayer
## The pause screen, opened by Scenes.pause() (ESC / Start; ESC again resumes).
## Tabs: JOURNEY (resume, save and quit, quest log) · MAP · SIGILS · SOUND · CONTROLS (remap).
## Q / E (LB / LT) change tab, UP/DOWN choose, LEFT/RIGHT change a value, SPACE / G confirm.
## TAB opens straight on the map. Quests come from Quests.log_entries(), sigils from Sigils
## (rules/), the map from Game.flags ("map_screen": [x, y], "map_seen": [[x, y], ...]).

const TABS := ["JOURNEY", "MAP", "SIGILS", "SOUND", "CONTROLS"]
const BOX := Rect2(80, 40, 800, 460)
const GRID := Vector2i(6, 5)          # the realm's screen grid (B1)
const CELL := Vector2(56, 40)
const COLUMN := 200                   # width of the name column in menu rows

var tab := 0
var cursor := 0
var rows: Array = []                  # [{text, ok: Callable, change: Callable}] for this tab
var remapping := ""                   # action waiting for a key, or ""
var _content: VBoxContainer
var _tabs: Label
var _hint: Label


func _ready() -> void:
	layer = GloomLight.HUD_LAYER + 20
	process_mode = Node.PROCESS_MODE_WHEN_PAUSED
	var dim := ColorRect.new()
	dim.color = Color(UiStyle.INK0, 0.75)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var panel := Panel.new()
	panel.theme = UiStyle.theme()
	panel.position = BOX.position
	panel.size = BOX.size
	add_child(panel)
	_tabs = UiStyle.label("", "body", UiStyle.INK5)
	_tabs.position = BOX.position + Vector2(16, 12)
	add_child(_tabs)
	_content = VBoxContainer.new()
	_content.theme = UiStyle.theme()
	_content.position = BOX.position + Vector2(24, 48)
	_content.size = Vector2(BOX.size.x - 48, BOX.size.y - 80)
	_content.add_theme_constant_override("separation", 4)
	add_child(_content)
	_hint = UiStyle.label("Q/E tab   UP/DOWN choose   LEFT/RIGHT change   SPACE ok   ESC back", "small", UiStyle.INK4)
	_hint.position = BOX.position + Vector2(16, BOX.size.y - 20)
	add_child(_hint)
	show_tab(0)


func show_tab(i: int) -> void:
	tab = posmod(i, TABS.size())
	cursor = 0
	remapping = ""
	_build()


func _build() -> void:
	var parts := PackedStringArray()
	for i in TABS.size():
		parts.append("[%s]" % TABS[i] if i == tab else TABS[i])
	_tabs.text = "  ".join(parts)
	for c in _content.get_children():
		_content.remove_child(c)
		c.queue_free()
	rows = []
	call("_tab_" + TABS[tab].to_lower())
	_draw_rows()


## A row the cursor can land on: a name, an optional value in a second column.
func _row(text: String, value := "", ok := Callable(), change := Callable()) -> void:
	var line := HBoxContainer.new()
	_content.add_child(line)
	var l := UiStyle.label(text, "body", UiStyle.INK6)
	l.custom_minimum_size.x = COLUMN
	line.add_child(l)
	var v := UiStyle.label(value, "body", UiStyle.INK5)
	line.add_child(v)
	rows.append({"label": l, "value_label": v, "text": text, "value": value, "ok": ok, "change": change})


func _note(text: String, color := UiStyle.INK5, which := "body") -> Label:
	var l := UiStyle.label(text, which, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD
	l.custom_minimum_size.x = BOX.size.x - 48
	_content.add_child(l)
	return l


func _draw_rows() -> void:
	for i in rows.size():
		var r: Dictionary = rows[i]
		var on: bool = i == cursor
		r.label.text = ("> " if on else "  ") + r.text
		r.label.add_theme_color_override("font_color", UiStyle.LIGHT0 if on else UiStyle.INK6)
		r.value_label.text = r.value
		r.value_label.add_theme_color_override("font_color", UiStyle.LIGHT0 if on else UiStyle.INK5)


# --- tabs ----------------------------------------------------------------------------------

func _tab_journey() -> void:
	_row("Resume", "", Scenes.resume)
	_row("Save and return to the title", "", save_and_quit)
	_note("")
	_note("QUEST LOG", UiStyle.INK7)
	var entries := quest_entries()
	if entries.is_empty():
		_note("No oaths sworn yet.")
	for e in entries:
		var done: bool = e.get("done", false)
		_note(("[x] " if done else "[ ] ") + str(e.get("title", "?")), UiStyle.INK4 if done else UiStyle.INK6)
		if str(e.get("text", "")) != "" and not done:
			_note("    " + str(e.text), UiStyle.INK5, "small")


func _tab_map() -> void:
	_note("THE REALM", UiStyle.INK7)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 32)
	_content.add_child(row)
	var grid := Control.new()
	grid.custom_minimum_size = Vector2(GRID) * CELL
	row.add_child(grid)
	var here := _cell(Game.flags.get("map_screen"))
	var seen := {}
	for s in Game.flags.get("map_seen", []):
		seen[_cell(s)] = true
	for y in GRID.y:
		for x in GRID.x:
			var c := ColorRect.new()
			var p := Vector2i(x, y)
			c.color = UiStyle.LIGHT0 if p == here else (UiStyle.INK3 if seen.has(p) else UiStyle.INK2)
			c.position = Vector2(p) * CELL + Vector2(1, 1)
			c.size = CELL - Vector2(2, 2)
			grid.add_child(c)
	var stones := VBoxContainer.new()
	stones.add_theme_constant_override("separation", 2)
	row.add_child(stones)
	stones.add_child(UiStyle.label("LIGHT STONES  %d/%d" % [Game.stones.size(), Game.STONES.size()], "body", UiStyle.INK7))
	for s in Game.STONES:
		var got: bool = s in Game.stones
		var l := UiStyle.label("%s %s" % [UiStyle.STONE, UiStyle.name_of("STONE", s) if got else "???"], "body", UiStyle.LIGHT0 if got else UiStyle.INK3)
		stones.add_child(l)


func _tab_sigils() -> void:
	var worn := sigils_equipped()
	_note("SIGILS  %d of %d slots" % [Sigils.used_slots(), sigil_slots()], UiStyle.INK7)
	_note("Swap sigils when you rest at a lantern.", UiStyle.INK5, "small")
	if worn.is_empty():
		_note("- none worn -", UiStyle.INK3)
	for s in worn:
		_note(_sigil_line(s), UiStyle.SHADOW2)
	var carried := Sigils.owned().filter(func(s): return s not in worn)
	if not carried.is_empty():
		_note("")
		_note("CARRIED", UiStyle.INK6)
		for s in carried:
			_note(_sigil_line(s), UiStyle.INK4)


func _sigil_line(id: String) -> String:
	var what: String = Sigils.ALL[id][2] if Sigils.ALL.has(id) else ""
	return "%s  (%d)  %s" % [Sigils.display_name(id), Sigils.cost(id), what]


func _tab_sound() -> void:
	for b in UiSettings.BUSES:
		_row(b, "", Callable(), _change_volume.bind(b))
	_relabel_sound()


func _relabel_sound() -> void:
	for i in UiSettings.BUSES.size():
		var b: String = UiSettings.BUSES[i]
		var v: float = UiSettings.volume[b]
		var steps := int(round(v * 10))
		rows[i].value = "<%s%s>  %d%%" % ["|".repeat(steps), ".".repeat(10 - steps), steps * 10]


func _change_volume(dir: int, bus: String) -> void:
	UiSettings.set_volume(bus, UiSettings.volume[bus] + 0.1 * dir)
	UiSettings.save()
	_relabel_sound()


func _tab_controls() -> void:
	for a in UiSettings.REMAPPABLE:
		_row(UiSettings.REMAPPABLE[a], UiSettings.key_name(a), begin_remap.bind(a))
	_row("Reset to defaults", "", _reset_controls)


func _reset_controls() -> void:
	UiSettings.reset_controls()
	UiSettings.save()
	_build()


# --- remapping -----------------------------------------------------------------------------

func begin_remap(action: String) -> void:
	remapping = action
	rows[cursor].value = "press a key or button... (ESC cancels)"
	_draw_rows()


## A key or gamepad button while remapping: put it on the action. ESC cancels.
func capture(event: InputEvent) -> bool:
	if remapping == "" or not event.is_pressed() or event.is_echo():
		return false
	if event is InputEventKey:
		var k: Key = event.physical_keycode if event.physical_keycode != KEY_NONE else event.keycode
		if k != KEY_ESCAPE:
			UiSettings.remap_key(remapping, k)
	elif event is InputEventJoypadButton:
		if event.button_index != JOY_BUTTON_START:
			UiSettings.remap_button(remapping, event.button_index)
	else:
		return false
	UiSettings.save()
	var keep := cursor
	remapping = ""
	_build()
	cursor = keep
	_draw_rows()
	return true


# --- data ----------------------------------------------------------------------------------

## Quest log entries [{title, text, done}].
func quest_entries() -> Array:
	return Quests.log_entries()


func sigil_slots() -> int:
	return Sigils.slots()


func sigils_equipped() -> Array:
	return Sigils.worn()


static func _cell(v) -> Vector2i:
	if v is Vector2i:
		return v
	if v is Array and v.size() >= 2:
		return Vector2i(int(v[0]), int(v[1]))
	return Vector2i(-1, -1)


# --- input ---------------------------------------------------------------------------------

func save_and_quit() -> void:
	Game.save()
	Scenes.goto("title")


func press(action: String) -> void:
	match action:
		"heal":
			show_tab(tab - 1)
		"tool":
			show_tab(tab + 1)
		"map":
			show_tab(TABS.find("MAP"))
		"move_up", "move_down":
			if rows.size() > 0:
				cursor = posmod(cursor + (1 if action == "move_down" else -1), rows.size())
				_draw_rows()
		"move_left", "move_right":
			if cursor < rows.size() and rows[cursor].change.is_valid():
				rows[cursor].change.call(1 if action == "move_right" else -1)
				_draw_rows()
		"jump", "interact":
			if cursor < rows.size() and rows[cursor].ok.is_valid():
				rows[cursor].ok.call()


func _input(event: InputEvent) -> void:
	if remapping != "" and capture(event):
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	for a in ["heal", "tool", "map", "move_up", "move_down", "move_left", "move_right", "jump", "interact"]:
		if event.is_action_pressed(a):
			press(a)
			get_viewport().set_input_as_handled()
			return
