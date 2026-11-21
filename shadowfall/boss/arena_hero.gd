class_name ArenaHero
extends RefCounted
## The Hero inside the throne room: a plain box platformer (no physics engine), so the whole fight
## runs frame by frame in tests. Movement numbers match caves/hero_side.gd (B2); B9 may swap this
## for HeroSide once that has the sword and pogo. Sword and pogo from docs/teen/gameplay §4.

const SIZE := Vector2(20, 28)
const RUN_SPEED := 192.0
const RUN_ACCEL := 2400.0
const AIR_ACCEL := 1600.0
const GRAVITY := 1960.0
const JUMP_SPEED := 600.0
const JUMP_CUT := 0.45
const MAX_FALL := 720.0
const COYOTE := 6.0 / 60.0
const BUFFER := 8.0 / 60.0
const POGO_SPEED := 540.0
## Sword arc 3 + 6 + 8 frames, reach 1.25 squares (40 px).
const SWING_START := 3.0 / 60.0
const SWING_ACTIVE := 6.0 / 60.0
const SWING_END := 8.0 / 60.0
const REACH := 40.0
const HURT_SAFE := 1.0          # 60 f of i-frames
## Wraithstep (the Dawnstone's dash): 17.5 sq/s for 12 f, i-frames f2-f9, 27 f cooldown.
const DASH_SPEED := 560.0
const DASH_TIME := 12.0 / 60.0
const DASH_SAFE := [2.0 / 60.0, 10.0 / 60.0]
const DASH_COOLDOWN := 27.0 / 60.0
const HURT_LOCK := 10.0 / 60.0

var pos := Vector2()            # centre
var vel := Vector2()
var facing := 1
var on_floor := false
var coyote := 0.0
var buffer := 0.0
var bouncing := false           # rising from a pogo: letting go of jump doesn't cut it
var swing := -1.0               # seconds since the swing began; < 0 = not swinging
var swing_down := false         # a pogo (DOWN + R in the air)
var swing_hits := {}            # what this swing already hit
var safe := 0.0                 # i-frames left
var lock := 0.0                 # knocked back: no control
var frozen := false             # cut-scene
var dash := -1.0                # seconds into the dash; < 0 = not dashing
var dash_cool := 0.0
# input for this tick (keys, or ThroneBot)
var ix := 0.0
var jump_pressed := false
var jump_held := false
var attack_pressed := false
var down_held := false
var dash_pressed := false


func rect() -> Rect2:
	return Rect2(pos - SIZE / 2.0, SIZE)


func feet() -> float:
	return pos.y + SIZE.y / 2.0


func step(dt: float, solids: Array[Rect2], ledges: Array[Rect2]) -> void:
	safe = maxf(0.0, safe - dt)
	lock = maxf(0.0, lock - dt)
	dash_cool = maxf(0.0, dash_cool - dt)
	if frozen:
		ix = 0.0
		jump_pressed = false
		attack_pressed = false
		dash_pressed = false
	if dash_pressed and dash < 0.0 and dash_cool <= 0.0 and lock <= 0.0:
		dash = 0.0
		if ix != 0.0:
			facing = 1 if ix > 0.0 else -1
	if dash >= 0.0:
		dash += dt
		vel = Vector2(facing * DASH_SPEED, 0.0)
		_move(vel * dt, solids, ledges)
		if dash >= DASH_TIME:
			dash = -1.0
			dash_cool = DASH_COOLDOWN
			vel.x = facing * RUN_SPEED
		jump_pressed = false
		attack_pressed = false
		dash_pressed = false
		return
	if attack_pressed and swing < 0.0:
		swing = 0.0
		swing_down = down_held and not on_floor
		swing_hits.clear()
	elif swing >= 0.0:
		swing += dt
		if swing > SWING_START + SWING_ACTIVE + SWING_END:
			swing = -1.0
	if jump_pressed:
		buffer = BUFFER
	if lock <= 0.0:
		var rate := RUN_ACCEL if on_floor else AIR_ACCEL
		vel.x = move_toward(vel.x, ix * RUN_SPEED, rate * dt)
		if ix != 0.0 and swing < 0.0:
			facing = 1 if ix > 0.0 else -1
	if on_floor:
		coyote = COYOTE
	if buffer > 0.0 and coyote > 0.0 and lock <= 0.0:
		vel.y = -JUMP_SPEED
		buffer = 0.0
		coyote = 0.0
		bouncing = false
	if vel.y >= 0.0:
		bouncing = false
	if not jump_held and vel.y < 0.0 and not bouncing:
		vel.y *= pow(JUMP_CUT, dt * 60.0)
	vel.y = minf(MAX_FALL, vel.y + GRAVITY * dt)
	_move(vel * dt, solids, ledges)
	if not on_floor:
		coyote = maxf(0.0, coyote - dt)
	buffer = maxf(0.0, buffer - dt)
	jump_pressed = false
	attack_pressed = false
	dash_pressed = false


func _move(d: Vector2, solids: Array[Rect2], ledges: Array[Rect2]) -> void:
	pos.x += d.x
	for s in solids:
		if rect().intersects(s):
			pos.x = s.position.x - SIZE.x / 2.0 if d.x > 0.0 else s.end.x + SIZE.x / 2.0
			vel.x = 0.0
	var old_feet := feet()
	on_floor = false
	pos.y += d.y
	for s in solids:
		if rect().intersects(s):
			if d.y > 0.0:
				pos.y = s.position.y - SIZE.y / 2.0
				on_floor = true
			else:
				pos.y = s.end.y + SIZE.y / 2.0
			vel.y = 0.0
	if d.y > 0.0:
		for s in ledges:                         # one-way: only from above
			if old_feet <= s.position.y + 0.01 and rect().intersects(s):
				pos.y = s.position.y - SIZE.y / 2.0
				on_floor = true
				vel.y = 0.0


func dashing() -> bool:
	return dash >= 0.0


## Can't be hurt: after a hit, or in the middle of a Wraithstep.
func untouchable() -> bool:
	return safe > 0.0 or (dash >= DASH_SAFE[0] and dash < DASH_SAFE[1])


func swinging() -> bool:
	return swing >= SWING_START and swing < SWING_START + SWING_ACTIVE


## Where the blade is this frame (only while swinging()).
func blade() -> Rect2:
	if swing_down:
		return Rect2(pos.x - 18.0, feet() - 4.0, 36.0, 36.0)
	var x := pos.x + SIZE.x / 2.0 if facing > 0 else pos.x - SIZE.x / 2.0 - REACH
	return Rect2(x, pos.y - 22.0, REACH, 40.0)


## True the first time this swing touches `what` (one hit per swing).
func first_hit(what: String) -> bool:
	if swing_hits.has(what):
		return false
	swing_hits[what] = true
	return true


func bounce() -> void:
	vel.y = -POGO_SPEED
	bouncing = true
	on_floor = false


func hurt(from_x: float) -> void:
	safe = HURT_SAFE
	lock = HURT_LOCK
	var away := 1.0 if pos.x >= from_x else -1.0
	vel = Vector2(away * 300.0, -320.0)
	bouncing = false
