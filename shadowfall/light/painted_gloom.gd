class_name PaintedGloom
## The gloom grade for painted art on the CPU (tests compare it with painted_gloom.gdshaderinc):
## per stage, drain the colour, pull it toward violet and darken it. Keep the numbers in step.

const SAT := [1.0, 0.8, 0.6, 0.4]
const SHIFT := [0.0, 0.12, 0.24, 0.36]
const VALUE := [1.0, 0.8, 0.64, 0.52]
const VIOLET := Vector3(0.82, 0.74, 1.3)


static func grade(c: Color, stage: int) -> Color:
	var s := clampi(stage, 0, 3)
	var v := Vector3(c.r, c.g, c.b)
	var l := v.dot(Vector3(0.299, 0.587, 0.114))
	v = Vector3(l, l, l).lerp(v, SAT[s])
	v = v.lerp(VIOLET * l, SHIFT[s])
	v = (v * VALUE[s]).clamp(Vector3.ZERO, Vector3.ONE)
	return Color(v.x, v.y, v.z, c.a)
