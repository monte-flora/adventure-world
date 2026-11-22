extends Node2D
## The light play-test (B3): a real dark cave in the dark, the lantern, crystals, gloom stages.
##   godot --path shadowfall res://light/demo.tscn [-- --file=shadow/2_the_hollow_stair.txt]
## Arrows move the lantern, 0-3 set the gloom stage, D toggles the dark, T takes the next Light Stone.

const TILE := LevelFile.TILE
const DEFAULT_FILE := "shadow/1_the_whisper_hollow.txt"
const ROCK := ["463d5e", "2b2540"]     # ink3 face, ink2 lip (palette colours, so they swap)
const CRYSTALS := "*s"                 # diamond ore and Sun Shard ore glow
const SPEED := 260.0

var light: GloomLight
var hero := Node2D.new()
var info := Label.new()


func _ready() -> void:
	var lf := LevelFile.load_file(Paths.level(Paths.cmdline().get("file", DEFAULT_FILE)))
	light = GloomLight.new()
	light.dark = true if lf.setting("dark") == "" else GloomLight.is_dark(lf)
	add_child(light)
	var tiles := Node2D.new()
	tiles.material = light.world_material
	tiles.draw.connect(func():
		tiles.draw_rect(Rect2(0, 0, lf.width * TILE, lf.height * TILE), Color("1f4031"))   # moss1 back wall
		for r in lf.height:
			for c in lf.width:
				if lf.at(c, r) in "#BMG%F":
					tiles.draw_rect(Rect2(c * TILE, r * TILE, TILE, TILE), Color(ROCK[0]))
					tiles.draw_rect(Rect2(c * TILE, r * TILE, TILE, 4), Color(ROCK[1])))
	add_child(tiles)
	for ch in CRYSTALS:
		for cell in lf.find(ch):
			var gem := Polygon2D.new()                 # a crystal: accent colour, never swapped
			gem.polygon = PackedVector2Array([Vector2(0, -10), Vector2(7, 0), Vector2(0, 10), Vector2(-7, 0)])
			gem.color = Color("a04ce0" if ch == "*" else "f7c64a")
			gem.position = Vector2(cell) * TILE + Vector2(TILE, TILE) / 2.0
			add_child(gem)
			light.add_crystal(self, gem.position)
	var body := Polygon2D.new()                         # the hero: never swapped
	body.polygon = PackedVector2Array([Vector2(-8, -16), Vector2(8, -16), Vector2(8, 16), Vector2(-8, 16)])
	body.color = Color("4a8fb8")
	hero.add_child(body)
	hero.position = Vector2(lf.start()) * TILE + Vector2(TILE / 2.0, TILE / 2.0)
	add_child(hero)
	light.follow(hero)
	var cam := Camera2D.new()
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	hero.add_child(cam)
	var hud := CanvasLayer.new()                        # the HUD: above the dark, never darkened
	hud.layer = GloomLight.HUD_LAYER
	info.position = Vector2(8, 8)
	info.add_theme_color_override("font_color", Color("fff2a8"))
	hud.add_child(info)
	add_child(hud)


func _process(dt: float) -> void:
	hero.position += Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down") * SPEED * dt
	info.text = "gloom %.2f  stage %d  dark %s  stones %d   [arrows] [0-3] [D] [T]" % [
		Game.gloom, light.stage, "on" if light.dark else "off", Game.stones.size()]


func _unhandled_key_input(e: InputEvent) -> void:
	var k := e as InputEventKey
	if not k.pressed or k.echo:
		return
	if k.keycode >= KEY_0 and k.keycode <= KEY_3:
		Game.gloom = minf(1.0, (k.keycode - KEY_0) / 3.0 + 0.001)
	elif k.keycode == KEY_D:
		light.dark = not light.dark
	elif k.keycode == KEY_T:
		for s in Game.STONES:
			if Game.take_stone(s):
				break
