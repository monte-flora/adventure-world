extends RefCounted
## The keys. Arrows move, SPACE jumps (press again in the air to double-jump),
## A or J (or the left mouse button) swings the sword, Q and E turn the camera.
## A is the attack key in the pygame game too, so WASD is not used for moving.

static func setup() -> void:
	_add("move_left", [KEY_LEFT], [], [[JOY_AXIS_LEFT_X, -1.0]])
	_add("move_right", [KEY_RIGHT], [], [[JOY_AXIS_LEFT_X, 1.0]])
	_add("move_forward", [KEY_UP], [], [[JOY_AXIS_LEFT_Y, -1.0]])
	_add("move_back", [KEY_DOWN], [], [[JOY_AXIS_LEFT_Y, 1.0]])
	_add("jump", [KEY_SPACE], [JOY_BUTTON_A])
	_add("attack", [KEY_A, KEY_J], [JOY_BUTTON_X], [], [MOUSE_BUTTON_LEFT])
	_add("cam_left", [KEY_Q], [JOY_BUTTON_LEFT_SHOULDER])
	_add("cam_right", [KEY_E], [JOY_BUTTON_RIGHT_SHOULDER])


static func _add(action: String, keys: Array, buttons := [], axes := [], mouse := []) -> void:
	if InputMap.has_action(action):
		return
	InputMap.add_action(action, 0.2)
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
	for b in buttons:
		var e := InputEventJoypadButton.new()
		e.button_index = b
		InputMap.action_add_event(action, e)
	for a in axes:
		var e := InputEventJoypadMotion.new()
		e.axis = a[0]
		e.axis_value = a[1]
		InputMap.action_add_event(action, e)
	for m in mouse:
		var e := InputEventMouseButton.new()
		e.button_index = m
		InputMap.action_add_event(action, e)
