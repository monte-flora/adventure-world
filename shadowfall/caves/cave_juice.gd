class_name CaveJuice
extends Node
## Game feel in a cave, matching the realm's (docs/teen/gameplay §4, overworld.gd): hit-stop, screen
## shake (Juice.Shake, off when UiSettings.screen_shake is off), sparks, dust, kill poofs and the red
## hurt edge. The cave calls these; it skips a frame of play while `stopped()`.

const STOP_HIT := 3
const STOP_KILL := 6
const STOP_HURT := 10
const SPARK := Color("fff2a8")
const MOTE := Color("f7c64a")
const DUST := Color("8a7a6a")

var cave                                          # CaveScene
var shake := Juice.Shake.new()
var stop := 0                                     # frames of hit-stop left
var edge: TextureRect
var frozen: Array = []                            # what the hit-stop paused


func _init(c) -> void:
	cave = c
	name = "juice"


func _ready() -> void:
	var ui := CanvasLayer.new()
	ui.layer = 5
	edge = _hurt_edge()
	ui.add_child(edge)
	add_child(ui)


## Called once a physics frame: moves the camera shake on, counts the hit-stop down.
func step(dt: float, cam: Camera2D) -> void:
	cam.offset = shake.step(dt)
	if stop > 0:
		stop -= 1
		if stop == 0:
			_freeze(false)


func stopped() -> bool:
	return stop > 0


## Freeze the Hero and the monsters for `frames` frames (a longer stop is never cut short).
func hit_stop(frames: int) -> void:
	if frames > stop:
		if stop == 0:
			_freeze(true)
		stop = frames


func _freeze(on: bool) -> void:
	if on:                                        # only what is running now (a test may hold a monster still)
		frozen = [cave.hero] if cave.hero.is_physics_processing() else []
		for m in cave.monsters.get_children():
			if m.is_physics_processing():
				frozen.append(m)
	for n in frozen:
		if is_instance_valid(n):
			n.set_physics_process(not on)
			if "sprite" in n and n.sprite:
				n.sprite.speed_scale = 0.0 if on else 1.0
	if not on:
		frozen = []


## A sword (or a sent-back arrow) hits a monster: sparks and a short stop; a kill stops longer,
## shakes harder, plays the monster's poof and lets its light out as motes.
func hit(m: CaveMonster, killed: bool) -> void:
	if not killed:
		hit_stop(STOP_HIT)
		shake.add(1, 4)
		Juice.burst(cave, m.position, SPARK, 6, 90.0, 0.2)
		return
	hit_stop(STOP_KILL)
	shake.add(2, 6)
	var poof := AnimatedSprite2D.new()
	poof.sprite_frames = m.sprite.sprite_frames
	poof.offset = m.sprite.offset
	poof.flip_h = m.sprite.flip_h
	poof.position = m.position + m.sprite.position
	poof.animation_finished.connect(poof.queue_free)
	cave.add_child(poof)
	poof.play("poof")
	Juice.burst(cave, m.position, MOTE, 16, 70.0, 0.9, 2.0, -40.0)


## The Hero is hurt: the longest stop, a hard shake and the screen edge pulses red. The last heart
## has no stop: you wake at the shrine straight away.
func hurt() -> void:
	if Game.hearts > 0:
		hit_stop(STOP_HURT)
	shake.add(5, 12)
	edge.modulate.a = 1.0
	edge.create_tween().tween_property(edge, "modulate:a", 0.0, 0.4)


## A down strike bounces off spikes or a monster: a spray of sparks under the blade.
func spark(at: Vector2) -> void:
	Juice.burst(cave, at, SPARK, 5, 110.0, 0.18)


## Feet hit the ground hard: a puff of dust either side.
func dust(at: Vector2, n := 6) -> void:
	Juice.burst(cave, at, DUST, n, 70.0, 0.35, 2.0, 60.0)


## Kingsfall lands: the heaviest shake (no stop) and a wide dust cloud.
func slam(at: Vector2) -> void:
	shake.add(8, 20)
	Juice.burst(cave, at, DUST, 14, 140.0, 0.5, 3.0, 120.0)


## Rock breaks: chips fly and fall.
func chips(at: Vector2, color: Color) -> void:
	Juice.burst(cave, at, color, 10, 120.0, 0.5, 3.0, 500.0)


func _hurt_edge() -> TextureRect:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array([0.0, 1.0])
	g.colors = PackedColorArray([Color(0.76, 0.23, 0.23, 0.0), Color(0.76, 0.23, 0.23, 0.7)])
	var tex := GradientTexture2D.new()
	tex.gradient = g
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.1, 0.5)
	var r := TextureRect.new()
	r.texture = tex
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.modulate.a = 0.0
	return r
