class_name RealmLight
extends Node2D
## The realm's dusk (overworld only; caves keep GloomLight's darkness):
##   var rl := RealmLight.new(); add_child(rl)              # a CanvasModulate tints the main canvas
##   RealmLight.glow(node, Vector2(0, -8))                  # a warm flickering PointLight2D on node
## The tint follows the gloom stage: dusk at stage 0, deeper violet as the Shadow King drains the light.
## CanvasModulate only touches canvas layer 0, so the HUD (layer >= GloomLight.HUD_LAYER) stays bright.

## Gloom stage -> tint. Stage 3 is the brief's #2e2c4d; stage 0 is a readable dusk.
const TINT := [Color("8a86b8"), Color("6c6899"), Color("4b4775"), Color("2e2c4d")]
const WARM := Color("ffc56a")         # lantern gold (outside Shadowfall 32: light, not a pixel)
const LANTERN := 130.0                # px radius, like LightPool.LANTERN
const PERSON := 72.0
const WINDOW := 44.0
const GROUP := "realm_lights"

var modulate_node := CanvasModulate.new()
var stage := -1
static var _tex: GradientTexture2D


func _init() -> void:
	name = "RealmLight"
	modulate_node.name = "Dusk"


func _ready() -> void:
	add_child(modulate_node)
	refresh()


func _process(_dt: float) -> void:
	if Game.gloom_stage() != stage:
		refresh()


func refresh() -> void:
	stage = clampi(Game.gloom_stage(), 0, TINT.size() - 1)
	modulate_node.color = TINT[stage]


## A soft radial falloff (white centre to clear edge), shared by every light.
static func falloff() -> GradientTexture2D:
	if _tex == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.35, 0.7, 1.0])
		g.colors = PackedColorArray([Color(1, 1, 1, 1), Color(1, 1, 1, 0.55), Color(1, 1, 1, 0.15), Color(1, 1, 1, 0)])
		_tex = GradientTexture2D.new()
		_tex.gradient = g
		_tex.fill = GradientTexture2D.FILL_RADIAL
		_tex.fill_from = Vector2(0.5, 0.5)
		_tex.fill_to = Vector2(1.0, 0.5)
		_tex.width = 128
		_tex.height = 128
	return _tex


## A warm PointLight2D of `radius` px on `parent` at `pos`, flickering like fire unless flicker = false.
static func glow(parent: Node, pos := Vector2.ZERO, radius := PERSON, energy := 1.0, color := WARM,
		flicker := true) -> PointLight2D:
	var l := PointLight2D.new()
	l.texture = falloff()
	l.texture_scale = radius * 2.0 / 128.0
	l.color = color
	l.energy = energy
	l.position = pos
	l.blend_mode = Light2D.BLEND_MODE_ADD
	l.add_to_group(GROUP)
	if flicker:
		l.add_child(Flicker.new())
	parent.add_child(l)
	return l


## True if node already carries a PointLight2D child (E2's own rig on the hero or a person).
static func has_light(node: Node) -> bool:
	for c in node.get_children():
		if c is PointLight2D:
			return true
	return false
