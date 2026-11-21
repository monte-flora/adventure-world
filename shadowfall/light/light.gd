class_name GloomLight
extends CanvasModulate
## The dark of the world. B3 owns this folder: the 4 gloom stages, the palette-swap shader,
## lantern and crystal lights, Light Stone effects. Placeholder: tints by Game.gloom.
## A scene adds one:  add_child(GloomLight.new())

func _process(_dt: float) -> void:
	var k := 1.0 - 0.7 * Game.gloom
	color = Color(k, k, minf(1.0, k * 1.15))
