class_name Flicker
extends Node
## Firelight: wobbles its parent PointLight2D's energy with fast noise (plus a small scale breath).
## Attach to any light:   var f := Flicker.new(); light.add_child(f)
## Each Flicker gets its own noise seed so a row of lanterns never pulses in step.

@export var amount := 0.22           # energy swing, as a share of the light's base energy
@export var speed := 9.0             # noise steps per second (fast = fire, slow = embers)
@export var breath := 0.04           # texture_scale swing

var _light: PointLight2D
var _base_energy := 1.0
var _base_scale := 1.0
var _noise := FastNoiseLite.new()
var _t := 0.0
static var _seed := 0


func _ready() -> void:
	_light = get_parent() as PointLight2D
	if _light == null:
		push_warning("Flicker: parent is not a PointLight2D")
		set_process(false)
		return
	_base_energy = _light.energy
	_base_scale = _light.texture_scale
	_seed += 1
	_noise.seed = _seed
	_noise.frequency = 1.0
	_t = randf() * 100.0


## The energy at time t (s): base × (1 ± amount), never below zero.
func energy_at(t: float) -> float:
	return maxf(0.0, _base_energy * (1.0 + amount * _noise.get_noise_1d(t * speed)))


func _process(dt: float) -> void:
	_t += dt
	_light.energy = energy_at(_t)
	_light.texture_scale = _base_scale * (1.0 + breath * _noise.get_noise_1d(_t * speed * 0.5 + 50.0))
