class_name HeroTop
extends Node2D
## The hooded wanderer on the map (top-down), docs/teen/gameplay §4 "Overworld": 8-way walk at
## 5.5 squares/s (0→max 5 f, stop 3 f), sword arc on R, roll on SHIFT once Wraithstep (dash) is owned.
## Collides square by square with WorldMap.walkable(), so ability gates open the moment Game has the
## ability. Placeholder art until art/ has the top-down sheet. B1 owns this file.

const TILE := LevelFile.TILE
const HALF := Vector2(10, 10)               # collision box half size (px)
const WALK := 5.5 * TILE                    # px/s
const ACCEL := WALK / (5.0 / 60.0)
const STOP := WALK / (3.0 / 60.0)
const ROLL_SPEED := 17.5 * TILE             # 12 f = 3.5 squares
const ROLL_FRAMES := 12
const ROLL_COOLDOWN := 27
const ATTACK := [3, 6, 8]                   # startup, active, recovery frames
const REACH := 1.25 * TILE
const ARC := deg_to_rad(100.0)
const HURT_IFRAMES := 60
const HURT_LOCK := 10
const KNOCKBACK := 2.0 * TILE / (10.0 / 60.0)

signal hurt(hearts_left: int)
signal swung(at: Vector2, facing: Vector2)  # one frame per active sword frame

var world: WorldMap
var velocity := Vector2.ZERO
var facing := Vector2.DOWN
var drive = null                            # tests set a Vector2 here instead of the keys
var roll_frames := 0
var roll_cooldown := 0
var roll_dir := Vector2.ZERO
var attack_frame := -1                      # -1 = not swinging
var iframes := 0
var lock_frames := 0


func cell() -> Vector2i:
	return Vector2i(floor(position.x / TILE), floor(position.y / TILE))


func place(at_cell: Vector2i) -> void:
	position = Vector2(at_cell) * TILE + Vector2.ONE * TILE / 2.0
	velocity = Vector2.ZERO


func is_rolling() -> bool:
	return roll_frames > 0


func invulnerable() -> bool:
	return iframes > 0 or (roll_frames > 0 and ROLL_FRAMES - roll_frames + 1 in range(2, 10))


func _move_input() -> Vector2:
	var v: Vector2 = drive if drive is Vector2 else Controls.move_vector()
	return v.limit_length(1.0)


func _physics_process(dt: float) -> void:
	if world == null:
		return
	iframes = maxi(0, iframes - 1)
	roll_cooldown = maxi(0, roll_cooldown - 1)
	var want := _move_input()
	if want.length() > 0.1 and not is_rolling():
		facing = want.normalized()
	if lock_frames > 0:
		lock_frames -= 1
	elif roll_frames > 0:
		roll_frames -= 1
		velocity = roll_dir * ROLL_SPEED
		if roll_frames == 0:
			velocity = roll_dir * WALK
	else:
		var target := want * WALK
		var rate := ACCEL if target.length() > 0.0 else STOP
		velocity = velocity.move_toward(target, rate * dt)
	_slide(velocity * dt)
	if attack_frame >= 0:
		attack_frame += 1
		if attack_frame > ATTACK[0] and attack_frame <= ATTACK[0] + ATTACK[1]:
			swung.emit(position, facing)
		if attack_frame >= ATTACK[0] + ATTACK[1] + ATTACK[2]:
			attack_frame = -1
	queue_redraw()


func roll() -> bool:
	if not Game.has_ability("dash") or roll_frames > 0 or roll_cooldown > 0 or lock_frames > 0:
		return false
	roll_dir = facing
	roll_frames = ROLL_FRAMES
	roll_cooldown = ROLL_FRAMES + ROLL_COOLDOWN
	return true


func attack() -> bool:
	if attack_frame >= 0 or is_rolling():
		return false
	attack_frame = 0
	return true


## Does the swing that's out now reach this point?
func sword_hits(p: Vector2) -> bool:
	var d := p - position
	return d.length() <= REACH + HALF.x and absf(facing.angle_to(d)) <= ARC / 2.0


## A monster touched the hero. Returns true if it hurt.
func take_hit(from: Vector2, damage := 1) -> bool:
	if invulnerable():
		return false
	Game.hearts = maxi(0, Game.hearts - damage)
	Game.changed.emit()
	iframes = HURT_IFRAMES
	lock_frames = HURT_LOCK
	var away := (position - from).normalized()
	velocity = (away if away != Vector2.ZERO else -facing) * KNOCKBACK
	hurt.emit(Game.hearts)
	return true


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("dash"):
		roll()
	elif event.is_action_pressed("attack"):
		attack()


## Moves by `step`, one axis at a time, stopping at squares the hero can't stand on.
func _slide(step: Vector2) -> void:
	for axis in 2:
		var delta := step[axis]
		if delta == 0.0:
			continue
		var p := position
		p[axis] += delta
		if _fits(p):
			position = p
		else:
			# stop flush against the square in the way
			var edge := (p[axis] + signf(delta) * HALF[axis])
			var blocked := floorf(edge / TILE) * TILE
			p[axis] = blocked - HALF[axis] - 0.01 if delta > 0 else blocked + TILE + HALF[axis] + 0.01
			if _fits(p):
				position = p
			velocity[axis] = 0.0


func _fits(p: Vector2) -> bool:
	for corner in [Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]:
		var q: Vector2 = p + corner * (HALF - Vector2(0.01, 0.01))
		if not world.walkable(Vector2i(floor(q.x / TILE), floor(q.y / TILE))):
			return false
	return true


func _draw() -> void:
	if iframes > 0 and (iframes / 4) % 2 == 0:
		return
	draw_circle(Vector2(0, 2), 11, Color("1c1a26"))                          # cloak
	draw_circle(facing * 3 + Vector2(0, -3), 7, Color("3b3552"))              # hood
	var lamp := facing.rotated(PI / 2) * 10 + facing * 4
	draw_circle(lamp, 9, Color(1.0, 0.8, 0.4, 0.18))                          # lantern glow
	draw_circle(lamp, 3, Color("f7c64a"))
	if attack_frame > ATTACK[0] and attack_frame <= ATTACK[0] + ATTACK[1]:
		var a := facing.angle()
		draw_arc(Vector2.ZERO, REACH, a - ARC / 2.0, a + ARC / 2.0, 12, Color("e8e4d8"), 3.0)
