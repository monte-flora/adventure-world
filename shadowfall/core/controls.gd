extends Node
## The input map (autoload `Controls`), keyboard + gamepad, from docs/teen/gameplay/README.md section 3.
## R attacks everywhere. Actions are made in code so tests and the remap screen (ui/) share one list.
## Owned by core (B0).

const DEADZONE := 0.25

## action -> [keys], [gamepad buttons], [gamepad axis, direction]
const BINDINGS := {
	"move_left": [[KEY_LEFT, KEY_A], [JOY_BUTTON_DPAD_LEFT], [JOY_AXIS_LEFT_X, -1.0]],
	"move_right": [[KEY_RIGHT, KEY_D], [JOY_BUTTON_DPAD_RIGHT], [JOY_AXIS_LEFT_X, 1.0]],
	"move_up": [[KEY_UP, KEY_W], [JOY_BUTTON_DPAD_UP], [JOY_AXIS_LEFT_Y, -1.0]],
	"move_down": [[KEY_DOWN, KEY_S], [JOY_BUTTON_DPAD_DOWN], [JOY_AXIS_LEFT_Y, 1.0]],
	"jump": [[KEY_SPACE], [JOY_BUTTON_A], []],
	"attack": [[KEY_R], [JOY_BUTTON_X], []],
	"dash": [[KEY_SHIFT], [JOY_BUTTON_RIGHT_SHOULDER], [JOY_AXIS_TRIGGER_RIGHT, 1.0]],
	"shoot": [[KEY_F], [JOY_BUTTON_Y], []],
	"interact": [[KEY_G], [JOY_BUTTON_B], []],
	"heal": [[KEY_Q], [JOY_BUTTON_LEFT_SHOULDER], []],
	"tool": [[KEY_E], [], [JOY_AXIS_TRIGGER_LEFT, 1.0]],
	"map": [[KEY_TAB], [JOY_BUTTON_BACK], []],
	"pause": [[KEY_ESCAPE], [JOY_BUTTON_START], []],
}


func _enter_tree() -> void:
	setup()


func setup() -> void:
	for action in BINDINGS:
		if InputMap.has_action(action):
			InputMap.erase_action(action)
		InputMap.add_action(action, DEADZONE)
		var b: Array = BINDINGS[action]
		for key in b[0]:
			var e := InputEventKey.new()
			e.physical_keycode = key
			InputMap.action_add_event(action, e)
		for button in b[1]:
			var e := InputEventJoypadButton.new()
			e.button_index = button
			InputMap.action_add_event(action, e)
		if b[2].size() == 2:
			var e := InputEventJoypadMotion.new()
			e.axis = b[2][0]
			e.axis_value = b[2][1]
			InputMap.action_add_event(action, e)


## The move stick/keys as a vector (length <= 1).
func move_vector() -> Vector2:
	return Input.get_vector("move_left", "move_right", "move_up", "move_down")
