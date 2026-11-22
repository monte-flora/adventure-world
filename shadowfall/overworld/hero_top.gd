class_name HeroTop
extends Entity
## The hooded wanderer on the map (top-down), docs/teen/gameplay §4 "Overworld": 8-way walk at
## 5.5 squares/s (0→max 5 f, stop 3 f), sword arc on R, roll on SHIFT once Wraithstep (dash) is owned.
## Collides square by square with WorldMap.walkable(), so ability gates open the moment Game has the
## ability. Art: art/sheets/hero_top (AnimatedSprite2D, feet on the bottom of the box). B1 owns this file.
## The lantern: `light` (LanternLight.HERO, the strongest light in the realm) sits on the lantern in his
## hand and moves with his facing; `embers` are a few sparks drifting up from it.

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
var light: LanternLight
var embers: CPUParticles2D
## Where the lantern hangs, from the middle of the box, by facing (the side one is for facing right).
const LANTERN_AT := {"_down": Vector2(9, 0), "_up": Vector2(-8, 0), "_side": Vector2(-5, 3)}


func _ready() -> void:
	gear_set = "tall"                                 # his sheet is taller: gear_tall_<item> (none drawn yet)
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = ArtSheet.frames("hero_top")
	sprite.offset = ArtSheet.offset("hero_top")
	sprite.position = Vector2(0, HALF.y + 2)          # the feet, just below the box's middle
	add_child(sprite)
	sprite.play("idle_down")
	light = LanternLight.new(LanternLight.HERO)
	light.name = "LanternLight"
	add_child(light)
	embers = _make_embers()
	add_child(embers)
	_place_lantern()


## Faint sparks rising from the lantern (CPU particles: safe in the web build).
func _make_embers() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.name = "Embers"
	p.amount = 9
	p.lifetime = 1.8
	p.local_coords = false                            # they stay behind as he walks on
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 4.0
	p.direction = Vector2.UP
	p.spread = 28.0
	p.gravity = Vector2(0, -14)
	p.initial_velocity_min = 6.0
	p.initial_velocity_max = 16.0
	p.scale_amount_min = 1.0
	p.scale_amount_max = 2.0
	var ramp := Gradient.new()
	ramp.offsets = PackedFloat32Array([0.0, 0.5, 1.0])
	ramp.colors = PackedColorArray([Color("fff2a8"), Color("f0784a"), Color(Color("c23a3a"), 0.0)])
	p.color_ramp = ramp
	var unlit := CanvasItemMaterial.new()             # sparks glow: the dusk does not dim them
	unlit.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	p.material = unlit
	p.z_index = 1
	return p


func _place_lantern() -> void:
	var at: Vector2 = LANTERN_AT[_dir()]
	if facing.x < -0.01 and _dir() == "_side":
		at.x = -at.x
	light.position = at
	embers.position = at


## The facing as a sheet suffix: _down, _up or _side (flip_h when facing left).
func _dir() -> String:
	if absf(facing.x) > absf(facing.y) + 0.01:
		return "_side"
	return "_up" if facing.y < 0 else "_down"


func _animate() -> void:
	if sprite == null:
		return
	var anim := "idle"
	if lock_frames > 0:
		anim = "hurt"
	elif roll_frames > 0:
		anim = "roll"
	elif attack_frame >= 0:
		anim = "attack"
	elif velocity.length() > 8.0:
		anim = "walk"
	if anim != "hurt":
		anim += _dir()
	if Forge.tier() >= Forge.SUNFANG_TIER and sprite.sprite_frames.has_animation(anim + "_sunfang"):
		anim += "_sunfang"                  # Sunfang's runes glow along the blade
	sprite.flip_h = facing.x < -0.01 and _dir() == "_side"
	if sprite.animation != anim:
		sprite.play(anim)
	elif anim.begins_with("attack") and attack_frame == 0:
		sprite.frame = 0
	sprite.visible = not (iframes > 0 and (iframes / 4) % 2 == 0)
	_place_lantern()


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
	_animate()
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
	Vitals.hurt(damage >= Vitals.BOSS_HIT)
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
	if attack_frame > ATTACK[0] and attack_frame <= ATTACK[0] + ATTACK[1]:   # the blade's arc
		var a := facing.angle()
		var t := float(attack_frame - ATTACK[0]) / ATTACK[1]
		var sweep := lerpf(-ARC / 2.0, ARC / 2.0, t)
		draw_arc(Vector2.ZERO, REACH, a - ARC / 2.0, a + sweep, 12, Color("f4f1ea"), 3.0)
		draw_arc(Vector2.ZERO, REACH - 4, a - ARC / 2.0, a + sweep, 12, Color("9c93b0"), 2.0)
