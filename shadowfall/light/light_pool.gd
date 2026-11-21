class_name LightPool
extends Node2D
## A pool of light that cuts the dark (the hero's lantern, a crystal). Put it anywhere in the world;
## GloomLight finds every pool in the "light_pools" group. Radius in world pixels.

const GROUP := "light_pools"
const LANTERN := 130.0               # the hero's lantern (docs/teen/art/README.md, Lighting)
const CRYSTAL := 36.0                # crystals: 30-40

@export var radius := LANTERN


func _init(r := LANTERN) -> void:
	radius = r


func _enter_tree() -> void:
	add_to_group(GROUP)
