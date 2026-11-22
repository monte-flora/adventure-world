class_name HeroSide
extends CharacterBody2D
## The side-view Hero in caves. Feel numbers from docs/teen/gameplay/README.md section 4, in tiles
## and frames at 60 fps (the numbers check_feel.py measured). Tests drive it by setting the input
## fields below and adding the "test" meta. The cave (cave.gd) tells it about ladders, walls, ice.

const T := 32.0                                  # one tile in pixels
# --- run ---
const RUN_SPEED := 7.5 * T                       # 7.5 tiles a second
const RUN_FRAMES := 6                            # 0 to full speed
const STOP_FRAMES := 5                           # full speed to a stop
const AIR_CONTROL := 0.67                        # run accel in the air
const ICE_CONTROL := 0.15                        # run accel on ice
# --- jump: g = 2h/t², v0 = 2h/t ---
const JUMP_HEIGHT := 3.4                         # tiles (with the apex float you get 3.29)
const JUMP_APEX_TIME := 0.38                     # seconds to the top
const GRAVITY := 2.0 * JUMP_HEIGHT * T / (JUMP_APEX_TIME * JUMP_APEX_TIME)
const JUMP_SPEED := 2.0 * JUMP_HEIGHT * T / JUMP_APEX_TIME
const FALL_GRAVITY := 1.6                        # falling is faster than rising
const APEX_GRAVITY := 0.6                        # floaty top while you hold jump
const APEX_SPEED := 2.5 * T
const JUMP_CUT := 0.45                           # let go early: a short hop
const MAX_FALL := 20.0 * T
const COYOTE_FRAMES := 6                         # jump just after running off a ledge
const BUFFER_FRAMES := 8                         # jump pressed just before landing
# --- abilities (only once you hold their Light Stone) ---
const DOUBLE_JUMP_HEIGHT := 2.25                 # Stormwing
const DASH_SPEED := 30.0 * T                     # Wraithstep: 11 frames, no gravity
const DASH_FRAMES := 11
const DASH_COOLDOWN := 21
const WALL_SLIDE := 4.5 * T                      # on % walls, or any wall with Ironclaw
const WALL_JUMP_OUT := 9.0 * T
const WALL_JUMP_UP := 15.0 * T
const WALL_LOCK := 8                             # frames you can't steer back to the wall
const POUND_SPEED := 22.0 * T                    # Kingsfall: DOWN+dash in the air
# --- sword (R) ---
const ATTACK_STARTUP := 2
const ATTACK_ACTIVE := 5
const ATTACK_RECOVERY := 8
const ATTACK_REACH := 1.5 * T
const POGO_SPEED := 15.5 * T                     # down strike hit: bounce up 2.46 tiles
# --- getting hurt ---
const HURT_KNOCK_X := 7.0 * T
const HURT_KNOCK_Y := 9.0 * T
const HURT_LOCK := 12                            # frames with no control
const IFRAMES := 60
# --- ladders ---
const CLIMB_SPEED := 4.0 * T
const SIZE := Vector2(20, 28)

enum { NORMAL, CLIMB, ROPE, DASH, POUND }

var cave                                         # the CaveScene, or null
var state := NORMAL
var facing := 1
var coyote := 0
var buffer := 0
var jumps := 0                                   # jumps made (tests count them)
var air_jump_used := false
var dash_used := false
var dash_left := 0
var dash_cool := 0
var wall_lock := 0
var wall_dir := 0                                # -1/1 while wall sliding
var attack_t := -1                               # frames into the swing, -1 when not swinging
var attack_dir := Vector2i(1, 0)
var attack_hits: Array = []                      # what this swing has hit already
var hurt_lock := 0
var iframes := 0
var rope: Node = null
var rope_grab_cool := 0
var safe_spot := Vector2.ZERO                    # last safe ground (hazards put you back here)
var was_rising_held := false
# input for this physics tick (set by the keyboard/gamepad, or by a test)
var ix := 0.0
var iy := 0.0
var jump_pressed := false
var jump_held := false
var attack_pressed := false
var dash_pressed := false
var tool_pressed := false
var interact_pressed := false


func _ready() -> void:
	var box := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = SIZE
	box.shape = rect
	add_child(box)
	collision_layer = 2
	collision_mask = 1
	floor_snap_length = 6.0
	floor_constant_speed = true
	safe_spot = position


func rect() -> Rect2:
	return Rect2(position - SIZE / 2.0, SIZE)


func _draw() -> void:
	if iframes > 0 and (iframes / 4) % 2 == 0:
		return
	draw_rect(Rect2(-SIZE / 2.0, SIZE), Color("3a2f4a"))                       # hooded cloak
	draw_rect(Rect2(Vector2(-6 + 3 * facing, -11), Vector2(8, 5)), Color("e6c878"))  # face in the hood
	draw_circle(Vector2(9 * facing, 2), 4.0, Color("f7c64a"))                   # the lantern
	if attack_t >= ATTACK_STARTUP and attack_t < ATTACK_STARTUP + ATTACK_ACTIVE:
		var r := attack_rect()
		draw_rect(Rect2(r.position - position, r.size), Color(1, 1, 1, 0.5))


func _read_input() -> void:
	ix = Input.get_axis("move_left", "move_right")
	iy = Input.get_axis("move_up", "move_down")
	jump_pressed = Input.is_action_just_pressed("jump")
	jump_held = Input.is_action_pressed("jump")
	attack_pressed = Input.is_action_just_pressed("attack")
	dash_pressed = Input.is_action_just_pressed("dash")
	tool_pressed = Input.is_action_just_pressed("tool")
	interact_pressed = Input.is_action_just_pressed("interact")


func _physics_process(dt: float) -> void:
	if not has_meta("test"):
		_read_input()
	step(dt)
	jump_pressed = false
	attack_pressed = false
	dash_pressed = false
	tool_pressed = false
	interact_pressed = false
	queue_redraw()


func _has(ability: String) -> bool:
	return Game.has_ability(ability)


func step(dt: float) -> void:
	iframes = maxi(0, iframes - 1)
	hurt_lock = maxi(0, hurt_lock - 1)
	wall_lock = maxi(0, wall_lock - 1)
	dash_cool = maxi(0, dash_cool - 1)
	rope_grab_cool = maxi(0, rope_grab_cool - 1)
	if jump_pressed:
		buffer = BUFFER_FRAMES
	var steer := ix if hurt_lock == 0 else 0.0
	if absf(steer) > 0.1:
		facing = 1 if steer > 0 else -1
	_attack_step()
	if cave and interact_pressed:
		cave.dig()
	if cave and tool_pressed and _has("flare"):
		cave.flare()
	match state:
		ROPE:
			_rope_step(steer)
		CLIMB:
			_climb_step(steer)
		DASH:
			_dash_step()
		POUND:
			_pound_step()
		_:
			_normal_step(steer, dt)
	buffer = maxi(0, buffer - 1)


func _normal_step(steer: float, dt: float) -> void:
	var on_floor := is_on_floor()
	if on_floor:
		coyote = COYOTE_FRAMES
		air_jump_used = false
		dash_used = false
		if cave and cave.is_safe_ground(self):
			safe_spot = position
	# ladders and vines: UP or DOWN grabs them
	if cave and absf(iy) > 0.5 and cave.ladder_at(self) and hurt_lock == 0:
		state = CLIMB
		velocity = Vector2.ZERO
		return
	# dash (Wraithstep), and the heavy slam (Kingsfall) as DOWN+dash in the air
	if dash_pressed and hurt_lock == 0:
		if not on_floor and iy > 0.5 and _has("pound"):
			state = POUND
			velocity = Vector2(0, POUND_SPEED)
			return
		if _has("dash") and dash_cool == 0 and not dash_used:
			state = DASH
			dash_left = DASH_FRAMES
			dash_used = not on_floor
			velocity = Vector2(facing * DASH_SPEED, 0)
			return
	# run
	var target := steer * RUN_SPEED
	var accel := RUN_SPEED / (RUN_FRAMES / 60.0)
	if absf(target) < absf(velocity.x) or signf(target) != signf(velocity.x):
		accel = RUN_SPEED / (STOP_FRAMES / 60.0)
	if not on_floor:
		accel *= AIR_CONTROL
	elif cave and cave.floor_letter(self) == "I":
		accel *= ICE_CONTROL
	if wall_lock > 0 and signf(target) == -signf(velocity.x):
		target = velocity.x
	velocity.x = move_toward(velocity.x, target, accel * dt)
	# wall slide on % walls (or any wall with Ironclaw)
	wall_dir = 0
	if not on_floor and velocity.y > 0.0 and is_on_wall() and absf(steer) > 0.1:
		var d := -int(signf(get_wall_normal().x))
		if d == int(signf(steer)) and _wall_ok(d):
			wall_dir = d
			dash_used = false
	# jumps
	if buffer > 0:
		if coyote > 0:
			_jump(JUMP_SPEED)
		elif wall_dir != 0:
			velocity.x = -wall_dir * WALL_JUMP_OUT
			facing = -wall_dir
			wall_lock = WALL_LOCK
			_jump(WALL_JUMP_UP)
		elif _has("double_jump") and not air_jump_used:
			air_jump_used = true
			_jump(sqrt(2.0 * GRAVITY * DOUBLE_JUMP_HEIGHT * T))
	# short hop: let go of jump while rising
	if was_rising_held and not jump_held and velocity.y < 0.0:
		velocity.y *= JUMP_CUT
	was_rising_held = jump_held and velocity.y < 0.0
	# gravity
	var g := 1.0
	if velocity.y > 0.0:
		g = FALL_GRAVITY
	elif absf(velocity.y) < APEX_SPEED and jump_held:
		g = APEX_GRAVITY
	velocity.y = minf(MAX_FALL, velocity.y + GRAVITY * g * dt)
	if wall_dir != 0:
		velocity.y = minf(velocity.y, WALL_SLIDE)
	move_and_slide()
	if not is_on_floor():
		coyote = maxi(0, coyote - 1)
	elif cave:
		cave.landed_on(self)
	if cave and rope_grab_cool == 0:
		var r = cave.rope_at(self)
		if r:
			rope = r
			state = ROPE
			r.grab(self)


func _jump(speed: float) -> void:
	velocity.y = -speed
	buffer = 0
	coyote = 0
	jumps += 1
	was_rising_held = true


func _wall_ok(d: int) -> bool:
	if cave == null:
		return _has("climb")
	var ch: String = cave.wall_letter(self, d)
	return ch == "%" or (_has("climb") and CaveTiles.is_solid(ch))


func _climb_step(steer: float) -> void:
	if buffer > 0 or not cave.ladder_at(self):
		state = NORMAL
		if buffer > 0:
			velocity.x = steer * RUN_SPEED
			_jump(JUMP_SPEED * 0.8)
		elif iy < 0.0:
			velocity.y = -JUMP_SPEED * 0.5             # pop up over the top
		return
	velocity = Vector2(steer * CLIMB_SPEED * 0.6, iy * CLIMB_SPEED)
	move_and_slide()
	air_jump_used = false
	dash_used = false


func _dash_step() -> void:
	dash_left -= 1
	velocity = Vector2(facing * DASH_SPEED, 0)
	move_and_slide()
	if dash_left <= 0 or is_on_wall():
		state = NORMAL
		dash_cool = DASH_COOLDOWN
		velocity.x = facing * RUN_SPEED


func _pound_step() -> void:
	velocity = Vector2(0, POUND_SPEED)
	move_and_slide()
	if is_on_floor():
		state = NORMAL
		if cave:
			cave.pounded(self)


func _rope_step(steer: float) -> void:
	if not is_instance_valid(rope):
		state = NORMAL
		return
	rope.pump(steer)
	if buffer > 0:
		var v: Vector2 = rope.release()
		state = NORMAL
		rope = null
		rope_grab_cool = 20
		velocity = v + Vector2(0, -JUMP_SPEED * 0.5)
		_jump(-velocity.y)


## Swing the sword: R; UP+R up, DOWN+R down (in the air: the pogo).
func _attack_step() -> void:
	if attack_t >= 0:
		attack_t += 1
		if attack_t >= ATTACK_STARTUP + ATTACK_ACTIVE + ATTACK_RECOVERY:
			attack_t = -1
	if attack_pressed and attack_t < 0 and hurt_lock == 0 and state != DASH:
		attack_t = 0
		attack_hits.clear()
		if iy > 0.5 and not is_on_floor():
			attack_dir = Vector2i(0, 1)
		elif iy < -0.5:
			attack_dir = Vector2i(0, -1)
		else:
			attack_dir = Vector2i(facing, 0)


func attacking() -> bool:
	return attack_t >= ATTACK_STARTUP and attack_t < ATTACK_STARTUP + ATTACK_ACTIVE


## The sword's box while it can hit.
func attack_rect() -> Rect2:
	var r := ATTACK_REACH
	match attack_dir:
		Vector2i(0, 1):
			return Rect2(position + Vector2(-SIZE.x * 0.75, SIZE.y / 2.0 - 4), Vector2(SIZE.x * 1.5, r))
		Vector2i(0, -1):
			return Rect2(position + Vector2(-SIZE.x * 0.75, -SIZE.y / 2.0 - r), Vector2(SIZE.x * 1.5, r))
	var x := position.x + SIZE.x / 2.0 if attack_dir.x > 0 else position.x - SIZE.x / 2.0 - r
	return Rect2(Vector2(x, position.y - SIZE.y / 2.0), Vector2(r, SIZE.y))


## A down strike hit something: bounce, and get the air dash and double jump back.
func pogo() -> void:
	velocity.y = -POGO_SPEED
	was_rising_held = false
	air_jump_used = false
	dash_used = false
	state = NORMAL


## Hit by a monster or a hazard. Returns false while flickering (no damage).
func hurt(from: Vector2, amount := 1) -> bool:
	if iframes > 0:
		return false
	iframes = IFRAMES
	hurt_lock = HURT_LOCK
	if state == ROPE and is_instance_valid(rope):
		rope.release()
		rope = null
		rope_grab_cool = 30
	state = NORMAL
	var away := 1.0 if position.x >= from.x else -1.0
	velocity = Vector2(away * HURT_KNOCK_X, -HURT_KNOCK_Y)
	Vitals.hurt(amount >= Vitals.BOSS_HIT)
	return true
