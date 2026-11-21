class_name HeroSide
extends CharacterBody2D
## The side-view Hero (placeholder from spikes/engine/godot/hero.gd). B2 owns it: retune to the
## gameplay spec (docs/teen/gameplay/README.md section 4), add dash, wall jump, pogo, crawl...
## Tests drive it by setting the input fields below and adding the "test" meta.

const RUN_SPEED := 192.0
const RUN_ACCEL := 2400.0
const AIR_ACCEL := 1600.0
const GRAVITY := 1960.0
const JUMP_SPEED := 600.0
const JUMP_CUT := 0.45
const MAX_FALL := 720.0
const COYOTE := 0.10
const BUFFER := 0.10
const SIZE := Vector2(20, 28)

var coyote := 0.0
var buffer := 0.0
var jumps := 0
# input for this physics tick (set by the keyboard/gamepad, or by a test)
var ix := 0.0
var jump_pressed := false
var jump_held := false


func _ready() -> void:
	var box := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = SIZE
	box.shape = rect
	add_child(box)
	floor_snap_length = 8.0
	floor_constant_speed = true


func _draw() -> void:
	draw_rect(Rect2(-SIZE / 2.0, SIZE), Color("e6c878"))


func _read_input() -> void:
	ix = Input.get_axis("move_left", "move_right")
	jump_pressed = Input.is_action_just_pressed("jump")
	jump_held = Input.is_action_pressed("jump")


func step(dt: float) -> void:
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


func _physics_process(dt: float) -> void:
	if not has_meta("test"):
		_read_input()
	step(dt)
	jump_pressed = false
