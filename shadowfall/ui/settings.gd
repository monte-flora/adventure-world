class_name UiSettings
## Player settings the pause screen changes: the 3 volumes, remapped keys and screen shake on/off.
## Kept in user://shadowfall_settings.cfg (per machine, not per save file), applied on the title.
## Volumes in steps of 10% (docs/teen/audio/README.md). A bus that doesn't exist yet is skipped.

const PATH := "user://shadowfall_settings.cfg"
const BUSES := ["Master", "Music", "SFX"]
const DEFAULT_VOLUME := {"Master": 1.0, "Music": 0.35, "SFX": 0.8}

## Actions the player may remap, in menu order, with their menu label. Pause stays on ESC/Start.
const REMAPPABLE := {
	"move_left": "Move left", "move_right": "Move right", "move_up": "Move up", "move_down": "Move down",
	"jump": "Jump", "attack": "Attack", "dash": "Dash", "shoot": "Shoot", "interact": "Interact",
	"heal": "Heal", "tool": "Tool", "map": "Map",
}

static var volume := DEFAULT_VOLUME.duplicate()
static var keys := {}     # action -> physical keycode the player chose
static var screen_shake := true   # accessibility: false = the camera never shakes (overworld/juice.gd)
static var path := PATH   # tests point this elsewhere


static func set_volume(bus: String, v: float) -> void:
	volume[bus] = clampf(snappedf(v, 0.1), 0.0, 1.0)
	_apply_bus(bus)


static func _apply_bus(bus: String) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i >= 0:
		AudioServer.set_bus_volume_db(i, linear_to_db(volume[bus]))
		AudioServer.set_bus_mute(i, volume[bus] <= 0.0)


## Puts `keycode` on `action` in place of its keyboard keys (gamepad stays). The key is taken
## off any other action that had it, so one key never does two things.
static func remap_key(action: String, keycode: Key) -> void:
	for other in REMAPPABLE:
		if other != action:
			for e in InputMap.action_get_events(other):
				if e is InputEventKey and e.physical_keycode == keycode:
					InputMap.action_erase_event(other, e)
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			InputMap.action_erase_event(action, e)
	var k := InputEventKey.new()
	k.physical_keycode = keycode
	InputMap.action_add_event(action, k)
	keys[action] = keycode


## Puts `button` on `action` in place of its gamepad buttons (keys and sticks stay).
static func remap_button(action: String, button: JoyButton) -> void:
	for other in REMAPPABLE:
		if other != action:
			for e in InputMap.action_get_events(other):
				if e is InputEventJoypadButton and e.button_index == button:
					InputMap.action_erase_event(other, e)
	for e in InputMap.action_get_events(action):
		if e is InputEventJoypadButton:
			InputMap.action_erase_event(action, e)
	var b := InputEventJoypadButton.new()
	b.button_index = button
	InputMap.action_add_event(action, b)


## The key shown in menus for an action ("R", "Space", "Left").
static func key_name(action: String) -> String:
	for e in InputMap.action_get_events(action):
		if e is InputEventKey:
			return OS.get_keycode_string(e.physical_keycode)
	return "-"


static func reset_controls() -> void:
	keys.clear()
	Controls.setup()


static func reset() -> void:
	volume = DEFAULT_VOLUME.duplicate()
	screen_shake = true
	keys.clear()
	Controls.setup()
	for b in BUSES:
		_apply_bus(b)


static func save() -> bool:
	var c := ConfigFile.new()
	for b in BUSES:
		c.set_value("volume", b, volume[b])
	for a in keys:
		c.set_value("keys", a, int(keys[a]))
	c.set_value("access", "screen_shake", screen_shake)
	return c.save(path) == OK


## Reads the file and applies it: bus volumes and remapped keys. No file: defaults.
static func load_and_apply() -> void:
	reset()
	var c := ConfigFile.new()
	if c.load(path) != OK:
		return
	for b in BUSES:
		set_volume(b, float(c.get_value("volume", b, DEFAULT_VOLUME[b])))
	screen_shake = bool(c.get_value("access", "screen_shake", true))
	if c.has_section("keys"):
		for a in c.get_section_keys("keys"):
			if REMAPPABLE.has(a):
				remap_key(a, int(c.get_value("keys", a)) as Key)
