class_name GloomLight
extends CanvasLayer
## The dark of the world (B3). One per screen (overworld, cave, boss):
##   var light := GloomLight.new()
##   light.dark = level.setting("dark") == "yes"     # a dark cave: only light pools show the way
##   add_child(light)
##   map.material = light.world_material             # world tiles darken with the gloom stage
##   light.follow(hero)                              # the hero's lantern, 130 px
##   light.add_crystal(parent, pos)                  # a crystal's small pool
## What it does:
## - Gloom stage (Game.gloom_stage(): 0..3) drives a palette swap on whatever uses world_material.
##   Characters don't use it, so they always read.
## - Darkness (ink0) over the world, cut by every LightPool in 3 hard rings. On in `dark: yes`
##   places, and (lighter) everywhere at gloom stage 3.
## - A Light Stone taken: a burst of light from the lantern and a gold flash.
## The HUD is never darkened: this draws on canvas layer LAYER, and the HUD sits on a layer above it
## (HUD_LAYER or higher). Nothing here tints the main canvas (no CanvasModulate).

const LAYER := 50
const HUD_LAYER := 100
const DARK_PLACE := 0.75             # ink0 alpha in a dark cave (art README: about 75%)
const DARK_STAGE_3 := 0.5            # ink0 alpha at gloom stage 3 outside dark places
const MAX_POOLS := 16
const RINGS := [[0.45, 0.0], [0.72, 1.0 / 3.0], [1.0, 2.0 / 3.0]]   # [radius fraction, share of the dark]
const BURST_SECONDS := 1.2
const FLASH_SECONDS := 0.6
const FLASH_ALPHA := 0.6
const INK := Color("0b0a12")
const FLASH := Color("fff2a8")       # light1

var dark := false                    # a `dark: yes` cave (or any pitch-dark place)
var stage := 0                       # the gloom stage now showing
var world_material := ShaderMaterial.new()
var overlay := ColorRect.new()
var flash := ColorRect.new()
var lantern: LightPool
var _dark_material := ShaderMaterial.new()
var _burst_t := -1.0                 # seconds since the last Light Stone, or < 0


func _init() -> void:
	layer = LAYER
	name = "GloomLight"
	world_material.shader = preload("res://light/palette_swap.gdshader")
	world_material.set_shader_parameter("lut", GloomLut.texture())
	_dark_material.shader = preload("res://light/darkness.gdshader")
	_dark_material.set_shader_parameter("ink", INK)
	for r: ColorRect in [overlay, flash]:
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		r.set_anchors_preset(Control.PRESET_FULL_RECT)
		add_child(r)
	overlay.name = "Darkness"
	overlay.material = _dark_material
	flash.name = "Flash"
	flash.color = Color(FLASH, 0.0)


func _ready() -> void:
	Game.stone_taken.connect(_on_stone)
	refresh()


func _process(dt: float) -> void:
	if _burst_t >= 0.0:
		_burst_t += dt
		if _burst_t > BURST_SECONDS:
			_burst_t = -1.0
	refresh()


## The hero's lantern: a LightPool that walks with `who`.
func follow(who: Node2D, radius := LightPool.LANTERN) -> LightPool:
	if lantern:
		lantern.queue_free()
	lantern = LightPool.new(radius)
	lantern.name = "Lantern"
	who.add_child(lantern)
	return lantern


func add_crystal(parent: Node, pos: Vector2, radius := LightPool.CRYSTAL) -> LightPool:
	var p := LightPool.new(radius)
	p.position = pos
	parent.add_child(p)
	return p


## A level file's `dark: yes` header (docs/teen/levels/README.md).
static func is_dark(level: LevelFile) -> bool:
	return level.setting("dark").to_lower() in ["yes", "true", "1"]


## How dark the world is now (ink0 alpha before the light pools).
func darkness() -> float:
	if dark:
		return DARK_PLACE
	return DARK_STAGE_3 if stage >= 3 else 0.0


## The dark left at a screen point once the pools cut it (what the shader draws).
static func darkness_at(p: Vector2, base: float, pools: Array) -> float:
	var a := base
	for pool in pools:                        # [screen position, radius]
		var d: float = p.distance_to(pool[0]) / maxf(pool[1], 0.001)
		var k := 1.0
		for ring in RINGS:
			if d < ring[0]:
				k = ring[1]
				break
		a = minf(a, base * k)
	return a


## The light pools on screen now: [[screen position, screen radius], ...], the burst first.
func screen_pools() -> Array:
	var size := _view_size()
	var out := []
	if _burst_t >= 0.0:
		var centre := size / 2.0
		if lantern and lantern.is_inside_tree():
			centre = lantern.get_global_transform_with_canvas().origin
		out.append([centre, size.length() * 2.5 * clampf(_burst_t / (BURST_SECONDS * 0.5), 0.0, 1.0)])
	var view := Rect2(Vector2.ZERO, size)
	for n in get_tree().get_nodes_in_group(LightPool.GROUP):
		var p := n as LightPool
		if p == null or not p.is_visible_in_tree():
			continue
		var xf := p.get_global_transform_with_canvas()
		var r := p.radius * xf.get_scale().x
		if view.grow(r).has_point(xf.origin):
			out.append([xf.origin, r])
	return out.slice(0, MAX_POOLS)


func refresh() -> void:
	stage = Game.gloom_stage()
	world_material.set_shader_parameter("stage", stage)
	var base := darkness()
	overlay.visible = base > 0.0
	if overlay.visible:
		var pools := screen_pools()
		var pos := PackedVector2Array()
		var radii := PackedFloat32Array()
		for p in pools:
			pos.append(p[0])
			radii.append(p[1])
		pos.resize(MAX_POOLS)
		radii.resize(MAX_POOLS)
		_dark_material.set_shader_parameter("darkness", base)
		_dark_material.set_shader_parameter("rect_size", _view_size())
		_dark_material.set_shader_parameter("count", pools.size())
		_dark_material.set_shader_parameter("pools", pos)
		_dark_material.set_shader_parameter("radii", radii)
	var f := 0.0
	if _burst_t >= 0.0:
		f = FLASH_ALPHA * clampf(1.0 - _burst_t / FLASH_SECONDS, 0.0, 1.0)
	flash.color.a = f
	flash.visible = f > 0.0


## True while a Light Stone's burst of light is playing.
func bursting() -> bool:
	return _burst_t >= 0.0


func _on_stone(_stone: String) -> void:
	_burst_t = 0.0
	refresh()


func _view_size() -> Vector2:
	return get_viewport().get_visible_rect().size if is_inside_tree() else Vector2(960, 540)
