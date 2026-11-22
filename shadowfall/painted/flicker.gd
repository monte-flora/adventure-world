extends PointLight2D
## P1 stand-in for E1's warm flicker: a slow wobble of energy and size.

var base_energy := 1.0
var base_scale := 1.0
var _t := randf() * 10.0


func _process(dt: float) -> void:
	_t += dt
	var f := 0.06 * sin(_t * 7.3) + 0.04 * sin(_t * 13.1 + 1.7)
	energy = base_energy * (1.0 + f)
	texture_scale = base_scale * (1.0 + f * 0.4)
