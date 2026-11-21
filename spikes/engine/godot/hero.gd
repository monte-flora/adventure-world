extends CharacterBody2D
## The spike's hero. Top-down: walks with a little momentum. Side view: runs, jumps with
## coyote time, a jump buffer and a short hop, and walks up slopes (move_and_slide does that).
## Same numbers as spikes/engine/pygame/feel.py, in pixels (32-px tiles) and seconds.

const WALK_SPEED := 160.0
const WALK_ACCEL := 1800.0
const WALK_FRICTION := 2200.0
const RUN_SPEED := 192.0
const RUN_ACCEL := 2400.0
const AIR_ACCEL := 1600.0
const GRAVITY := 1960.0
const JUMP_SPEED := 600.0
const JUMP_CUT := 0.45
const MAX_FALL := 720.0
const COYOTE := 0.10
const BUFFER := 0.10

var side := false
var robot := false
var t := 0.0
var coyote := 0.0
var buffer := 0.0
var jumps := 0
# input for this physics tick (set by the robot, the keyboard or a test)
var ix := 0.0
var iy := 0.0
var jump_pressed := false
var jump_held := false
var _space_was := false


func _ready() -> void:
	var box := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(20, 28)
	box.shape = rect
	add_child(box)
	floor_snap_length = 8.0
	floor_constant_speed = true


func _draw() -> void:
	draw_rect(Rect2(-10, -14, 20, 28), Color("e6c878"))


func _read_input() -> void:
	if robot:
		var p := fmod(t, 8.0)
		if not side:
			var d: Vector2 = [Vector2.RIGHT, Vector2.DOWN, Vector2.LEFT, Vector2.UP][int(p / 2.0)]
			ix = d.x
			iy = d.y
		else:
			ix = 1.0 if fmod(t, 16.0) < 8.0 else -1.0
			jump_pressed = fmod(t, 0.8) < 1.0 / 60.0
			jump_held = fmod(t, 0.8) < 0.3
		return
	ix = float(Input.is_key_pressed(KEY_RIGHT)) - float(Input.is_key_pressed(KEY_LEFT))
	iy = float(Input.is_key_pressed(KEY_DOWN)) - float(Input.is_key_pressed(KEY_UP))
	var space := Input.is_key_pressed(KEY_SPACE)
	jump_pressed = space and not _space_was
	jump_held = space
	_space_was = space


func step(dt: float) -> void:
	## One physics tick of game feel. Tests call this through _physics_process.
	if side:
		if jump_pressed:
			buffer = BUFFER
		var rate := RUN_ACCEL if is_on_floor() else AIR_ACCEL
		velocity.x = move_toward(velocity.x, ix * RUN_SPEED, rate * dt)
		if is_on_floor():
			coyote = COYOTE
		if buffer > 0.0 and coyote > 0.0:
			velocity.y = -JUMP_SPEED
			buffer = 0.0
			coyote = 0.0
			jumps += 1
		if not jump_held and velocity.y < 0.0:
			velocity.y *= pow(JUMP_CUT, dt * 60.0)
		velocity.y = minf(MAX_FALL, velocity.y + GRAVITY * dt)
		move_and_slide()
		if not is_on_floor():
			coyote = maxf(0.0, coyote - dt)
		buffer = maxf(0.0, buffer - dt)
	else:
		var want := Vector2(ix, iy).limit_length(1.0) * WALK_SPEED
		var r := WALK_ACCEL if want != Vector2.ZERO else WALK_FRICTION
		velocity = velocity.move_toward(want, r * dt)
		move_and_slide()


func _physics_process(dt: float) -> void:
	t += dt
	if not has_meta("test"):
		_read_input()
	step(dt)
	jump_pressed = false
