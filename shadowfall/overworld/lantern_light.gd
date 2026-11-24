class_name LanternLight
extends PointLight2D
## A warm lamp light (PointLight2D, works in the Compatibility renderer and the web build). The
## Lanternbearer's "old light" is HERO: the strongest light in the realm. Torches and small lanterns
## carried by people use NPC, TORCH or CANDLE (all far weaker and smaller), so the hero stays the focal point.
##   add_child(LanternLight.new(LanternLight.HERO))
## In full daylight (no CanvasModulate, or a bright one) it fades to a faint glow; the darker the
## dusk (RealmLight's CanvasModulate), the stronger it burns: that scales the colour, and light/flicker.gd
## (Flicker) wobbles the energy like fire.

const HERO := {"radius": 176.0, "energy": 1.4, "color": Color("f7b24a")}
const NPC := {"radius": 72.0, "energy": 0.5, "color": Color("f0904a")}        # a person's hand lantern
const TORCH := {"radius": 84.0, "energy": 0.7, "color": Color("f0784a")}      # redder, a little wider
const CANDLE := {"radius": 44.0, "energy": 0.35, "color": Color("f7c64a")}
const UNLIT := {"radius": 40.0, "energy": 0.2, "color": Color("d9a95f")}      # no flame: just enough to see a face
const DAY_SHARE := 0.3                      # of the energy left in full daylight
const TEX := 128                            # px across the light texture

static var _tex: GradientTexture2D

var base_energy := 1.0
var radius := 100.0
var base_color := Color.WHITE
var dusk: CanvasModulate
var _look := 0.0


func _init(kind: Dictionary = NPC) -> void:
	radius = kind.radius
	base_energy = kind.energy
	base_color = kind.color
	color = base_color
	texture = glow()
	texture_scale = radius * 2.0 / TEX
	energy = base_energy
	blend_mode = Light2D.BLEND_MODE_ADD
	add_child(Flicker.new())


## A soft round falloff, made once.
static func glow() -> GradientTexture2D:
	if _tex == null:
		var g := Gradient.new()
		g.offsets = PackedFloat32Array([0.0, 0.35, 1.0])
		g.colors = PackedColorArray([Color.WHITE, Color(1, 1, 1, 0.55), Color(1, 1, 1, 0)])
		_tex = GradientTexture2D.new()
		_tex.gradient = g
		_tex.width = TEX
		_tex.height = TEX
		_tex.fill = GradientTexture2D.FILL_RADIAL
		_tex.fill_from = Vector2(0.5, 0.5)
		_tex.fill_to = Vector2(1.0, 0.5)
	return _tex


## How dark the world is (0 = daylight, 1 = black), from the scene's CanvasModulate.
func darkness() -> float:
	if dusk == null or not is_instance_valid(dusk):
		return 0.0
	return clampf(1.0 - dusk.color.get_luminance(), 0.0, 1.0)


## How strong the light is before the flicker: the base energy, cut down in daylight.
func steady_energy() -> float:
	return base_energy * lerpf(DAY_SHARE, 1.0, darkness())


func _process(dt: float) -> void:
	_look -= dt
	if _look <= 0.0 and is_inside_tree():     # the dusk may be added after us: look again now and then
		_look = 1.0
		var found := get_tree().root.find_children("*", "CanvasModulate", true, false)
		dusk = found[0] if not found.is_empty() else null
	var k := lerpf(DAY_SHARE, 1.0, darkness())
	color = Color(base_color.r * k, base_color.g * k, base_color.b * k)
	var h := get_node_or_null("halo") as Sprite2D      # a prop flame's own glow (RealmProps.halo)
	if h:
		h.modulate.a = clampf(energy / maxf(base_energy, 0.01), 0.0, 1.0) * lerpf(0.6, 1.0, darkness())
