class_name PaintedHero
extends HeroTop
## P1 prototype: the map hero (overworld/hero_top.gd, reused as is) on a painted screen. Only the
## collision changes: the hero's box is tested against the screen's hand-made shapes, pixel by pixel,
## instead of 32-px squares.

var scene: Node                             # the PaintedScreen: blocked(Rect2) -> bool


func _fits(p: Vector2) -> bool:
	return scene == null or not scene.blocked(Rect2(p - HALF, HALF * 2.0))


func _slide(step: Vector2) -> void:
	for axis in 2:
		var delta := step[axis]
		if delta == 0.0:
			continue
		var n := ceili(absf(delta))
		for i in n:
			var p := position
			p[axis] += delta / n
			if not _fits(p):
				velocity[axis] = 0.0
				break
			position = p
