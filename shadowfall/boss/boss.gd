extends Node2D
## The Shadow Castle and the throne room (B8).
##   Scenes.goto("boss", {"castle": 1..5})   a castle level (played in B2's cave scene); its door
##                                           leads to the next level, the last one to the throne
##   Scenes.goto("boss")                      the Shadow King (ThroneFight), drawn here
## Placeholder art (shapes in the art palette) until B-Art's boss sheets land.

const INK0 := Color("0d0a14")
const INK1 := Color("1a1424")
const INK2 := Color("2a2236")
const STONE := Color("3b3249")
const STONE_HI := Color("5a4d6e")
const SHADOW1 := Color("5b2a86")
const SHADOW2 := Color("c08cff")
const EMBER1 := Color("e8742c")
const EMBER2 := Color("ffc070")
const GOLD := Color("f7c64a")
const HERO := Color("e6c878")
const LIGHT := Color("fff4d6")

var level := 0                          # castle level, 0 = the throne room
var cave: Node                          # the castle level being played
var door := Rect2()
var fight: ThroneFight
var losses := 0
var told_clang := false
var caption := ""
var caption_t := 0.0
var shake_px := 0.0
var shake_t := 0.0
var shake_len := 0.0
var end_t := 0.0
var flash := 0.0
var cam: Camera2D
var dark_rect: ColorRect
var glow: Node2D
var hud: Control


func _ready() -> void:
	level = int(Scenes.args.get("castle", 0))
	_build_hud()
	if level > 0:
		_start_castle()
	else:
		_start_throne()


# ---- the castle levels ----------------------------------------------------------------------

func _start_castle() -> void:
	level = clampi(level, 1, Castle.LEVELS)
	if level == 1 and Game.stones.size() == Game.STONES.size() and Castle.forge_sunfang():
		_say("The seven Light Stones burn together into one blade: %s." % Castle.display("SUNFANG", "", "Sunfang"))
		Audio.play_sfx("forge")
	Scenes.args["file"] = Castle.file(level)      # the cave scene reads its file from here
	cave = load("res://caves/cave.tscn").instantiate()
	add_child(cave)
	var lf: LevelFile = cave.get("level")
	if lf and lf.find("D").size() > 0:
		door = Rect2(Vector2(lf.find("D")[0]) * LevelFile.TILE, Vector2.ONE * LevelFile.TILE).grow(6)
	if caption == "" and lf:
		_say(lf.setting("name", "The Shadow Castle"))
	Audio.play_music("castle")


func _castle_tick() -> void:
	var h = cave.get("hero")
	if h and door.has_area() and door.has_point(h.position):
		cave = null
		Scenes.goto.call_deferred("boss", Castle.next(level))


# ---- the throne room ------------------------------------------------------------------------

func _start_throne() -> void:
	Castle.forge_sunfang()                       # you can't reach the throne without it
	fight = ThroneFight.new(randi(), Castle.sword_damage())
	cam = Camera2D.new()
	cam.position = Vector2(ThroneFight.W, ThroneFight.H) / 2.0
	add_child(cam)
	dark_rect = ColorRect.new()
	dark_rect.size = Vector2(ThroneFight.W, ThroneFight.H)
	dark_rect.z_index = 10
	dark_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var mat := ShaderMaterial.new()
	mat.shader = load("res://boss/eclipse.gdshader")
	dark_rect.material = mat
	dark_rect.visible = false
	add_child(dark_rect)
	glow = Node2D.new()                          # what shows through the dark: eyes, telegraphs
	glow.z_index = 20
	glow.draw.connect(_draw_glow)
	add_child(glow)
	Audio.play_music("throne")


func _physics_process(dt: float) -> void:
	caption_t = maxf(0.0, caption_t - dt)
	flash = maxf(0.0, flash - dt)
	hud.queue_redraw()
	if cave:
		_castle_tick()
	if fight == null:
		return
	if not has_meta("test"):
		_read_keys()
	fight.tick(dt)
	for e in fight.events:
		_event(e)
	fight.events.clear()
	if fight.lost:
		end_t += dt
		if end_t > 1.6:
			_retry()
	elif fight.won:
		end_t += dt
		if end_t > 4.0 and (Input.is_action_just_pressed("jump") or Input.is_action_just_pressed("attack")):
			Scenes.goto("title")
	shake_t = maxf(0.0, shake_t - dt)
	var k := shake_t / shake_len if shake_len > 0.0 else 0.0
	cam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake_px * k
	dark_rect.visible = fight.dark
	if fight.dark:
		dark_rect.material.set_shader_parameter("hero_px", fight.hero.pos)
	queue_redraw()
	glow.queue_redraw()


func _read_keys() -> void:
	var h := fight.hero
	h.ix = Input.get_axis("move_left", "move_right")
	h.jump_pressed = Input.is_action_just_pressed("jump")
	h.jump_held = Input.is_action_pressed("jump")
	h.attack_pressed = Input.is_action_just_pressed("attack")
	h.down_held = Input.is_action_pressed("move_down")
	h.dash_pressed = Input.is_action_just_pressed("dash")


func _event(e: Dictionary) -> void:
	match e["kind"]:
		"shake":
			if e["px"] >= shake_px * (shake_t / maxf(shake_len, 0.001)):
				shake_px = e["px"]
				shake_t = e["time"]
				shake_len = e["time"]
		"sfx":
			Audio.play_sfx(e["name"])
		"music":
			Audio.play_music(e["name"])
		"say":
			_say(e["text"])
		"echo":
			_say("An echo of %s rises!" % e["name"])
		"clang":
			if not told_clang:
				told_clang = true
				_say("His shadow armour turns your blade. Strike when he is open: when his sword sticks, when he tires.")
		"phase":
			flash = 0.25
			Audio.play_sfx("boss_phase")
		"sunfang":
			flash = 1.2
			Audio.play_sfx("sunfang")
		"lost":
			end_t = 0.0
			_say("The dark takes you... The lantern by the door flickers back to life.")
		"won":
			end_t = 0.0


func _retry() -> void:
	losses += 1
	Game.flags["throne_losses"] = int(Game.flags.get("throne_losses", 0)) + 1
	Game.hearts = Game.max_hearts
	fight = ThroneFight.new(randi(), Castle.sword_damage())
	fight.state = "idle"                         # no speech the second time: straight in
	fight.t = -1.0
	end_t = 0.0


func _say(text: String) -> void:
	caption = text
	caption_t = 2.5 + text.length() * 0.04


# ---- drawing --------------------------------------------------------------------------------

func _draw() -> void:
	if fight == null:
		return
	var f := fight
	if f.phase < 3:
		_draw_hall(f)
	else:
		_draw_void(f)
	_draw_king(f)
	for z in f.hazards:
		_draw_hazard(z, false)
	_draw_hero(f.hero)


func _draw_hall(f: ThroneFight) -> void:
	draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), INK1)
	for i in 6:                                  # tall arched windows, a cold moon behind
		var x := 90.0 + i * 160.0
		draw_rect(Rect2(x, 70, 44, 220), INK0)
		draw_circle(Vector2(x + 22, 70), 22, INK0)
		draw_rect(Rect2(x + 4, 90, 36, 196), Color(SHADOW1, 0.18))
	for x in [150.0, 400.0, 560.0, 810.0]:      # pillars with braziers
		draw_rect(Rect2(x - 22, 40, 44, ThroneFight.FLOOR_Y - 40), INK2)
		draw_rect(Rect2(x - 26, ThroneFight.FLOOR_Y - 20, 52, 20), STONE)
		if not f.dark:
			var flick := 6.0 + sin(f.time * 9.0 + x) * 2.0
			draw_circle(Vector2(x, 236), 34, Color(EMBER1, 0.08))
			draw_circle(Vector2(x, 240), flick, EMBER1)
			draw_circle(Vector2(x, 242), flick * 0.5, EMBER2)
		draw_rect(Rect2(x - 12, 248, 24, 10), STONE_HI)
	draw_colored_polygon(PackedVector2Array([Vector2(820, ThroneFight.FLOOR_Y), Vector2(830, 230),
		Vector2(850, 190), Vector2(870, 230), Vector2(880, ThroneFight.FLOOR_Y)]), INK0)   # the throne
	draw_rect(Rect2(0, ThroneFight.FLOOR_Y, ThroneFight.W, ThroneFight.H - ThroneFight.FLOOR_Y), STONE)
	draw_line(Vector2(0, ThroneFight.FLOOR_Y + 1), Vector2(ThroneFight.W, ThroneFight.FLOOR_Y + 1), STONE_HI, 2)
	draw_rect(Rect2(0, 0, ThroneFight.WALL_L, ThroneFight.H), INK2)
	draw_rect(Rect2(ThroneFight.WALL_R, 0, ThroneFight.W - ThroneFight.WALL_R, ThroneFight.H), INK2)
	draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.CEIL_Y), INK2)


func _draw_void(f: ThroneFight) -> void:
	draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), Color("07050c"))
	for i in 40:                                 # motes rising out of the void
		var x := fmod(i * 97.0, ThroneFight.W)
		var y := ThroneFight.H - fmod(f.time * (20.0 + i % 5 * 8.0) + i * 53.0, ThroneFight.H)
		draw_rect(Rect2(x, y, 2, 2), Color(SHADOW2, 0.35))
	for s in f.solids:
		if s.position.y == ThroneFight.FLOOR_Y:
			draw_rect(s, STONE)
			draw_line(s.position + Vector2(0, 1), Vector2(s.end.x, s.position.y + 1), STONE_HI, 2)
			draw_colored_polygon(PackedVector2Array([Vector2(s.position.x, s.end.y), Vector2(s.end.x, s.end.y),
				Vector2(s.get_center().x + 14, s.end.y + 40), Vector2(s.get_center().x - 10, s.end.y + 28)]), STONE)
		else:
			draw_rect(s, INK2)
	for l in f.ledges:
		draw_rect(l, STONE_HI)


func _draw_king(f: ThroneFight) -> void:
	if f.alpha <= 0.01:
		return
	var c := f.king
	var a := f.alpha
	var ink := INK0 if f.flash <= 0.0 else LIGHT
	var hw := ThroneFight.KING_SIZE.x / 2.0
	var hh := ThroneFight.KING_SIZE.y / 2.0
	var cloak := PackedVector2Array([c + Vector2(-hw - 10, hh), c + Vector2(-hw + 4, -hh + 34),
		c + Vector2(-14, -hh + 14), c + Vector2(14, -hh + 14), c + Vector2(hw - 4, -hh + 34), c + Vector2(hw + 10, hh)])
	draw_colored_polygon(cloak, Color(ink, a))
	draw_polyline(cloak, Color(EMBER1, 0.55 * a), 1.5)                     # rim light from behind
	draw_circle(c + Vector2(0, -hh + 16), 15, Color(ink, a))                 # the hooded head
	if f.crown_state == "on":
		_draw_crown(c + Vector2(0, -hh - 2), a)
	for i in 5:                                                             # smoke rising off him
		var p := c + Vector2(sin(f.time * 2.0 + i) * hw, -hh - fmod(f.time * 30.0 + i * 17.0, 50.0))
		draw_circle(p, 3, Color(INK2, 0.5 * a))
	if f.phase < 3:
		_draw_sword(f, a)


func _draw_sword(f: ThroneFight, a: float) -> void:
	var c := f.king
	var d := float(f.facing)
	var hot := f.state in ["glow", "slash"]
	var col := EMBER2 if hot else SHADOW1
	match f.state:
		"stuck", "pull":                         # driven into the floor
			var tip := Vector2(c.x + d * 70, ThroneFight.FLOOR_Y + 6)
			draw_line(c + Vector2(d * 20, 0), tip, Color(col, a), 5)
			draw_circle(tip, 6, Color(EMBER1, 0.5 * a))
		"slash":
			draw_arc(Vector2(c.x + d * 30, ThroneFight.FLOOR_Y - 40), 100, -PI / 2 if d > 0 else PI / 2,
				PI / 2 * d if d > 0 else PI * 1.5, 16, Color(EMBER2, 0.8), 8)
		_:
			draw_line(c + Vector2(d * 22, -10), c + Vector2(d * 40, -90), Color(col, a), 5)


func _draw_crown(p: Vector2, a: float, ci: CanvasItem = self) -> void:
	var pts := PackedVector2Array([p + Vector2(-17, 8), p + Vector2(-17, -6), p + Vector2(-9, 0), p + Vector2(0, -12),
		p + Vector2(9, 0), p + Vector2(17, -6), p + Vector2(17, 8)])
	ci.draw_colored_polygon(pts, Color(INK0, a))
	ci.draw_polyline(pts + PackedVector2Array([pts[0]]), Color(GOLD, 0.8 * a), 1.5)
	ci.draw_circle(p + Vector2(0, 2), 3, Color(SHADOW2, a))


func _draw_hazard(z: Dictionary, glowing: bool, ci: CanvasItem = self) -> void:
	var r: Rect2 = z["rect"]
	var col := Color(z.get("color", "c08cff"))
	if z["kind"] == "fireball":
		col = EMBER1
	if z["tele"] > 0.0:
		if not glowing:
			return
		var pulse := 0.35 + 0.35 * sin(z["tele"] * 30.0)
		match z["kind"]:
			"drop", "rain", "erupt":
				var x: float = z["x"]
				ci.draw_line(Vector2(x, ThroneFight.CEIL_Y), Vector2(x, ThroneFight.FLOOR_Y), Color(col, pulse * 0.6), 2)
				ci.draw_rect(Rect2(x - r.size.x / 2.0, ThroneFight.FLOOR_Y - 4, r.size.x, 4), Color(col, pulse))
			_:
				ci.draw_rect(r, Color(col, pulse), false, 2)
		return
	match z["kind"]:
		"orb", "wisp", "fireball":
			ci.draw_circle(r.get_center(), r.size.x / 2.0 + 4, Color(col, 0.25))
			ci.draw_circle(r.get_center(), r.size.x / 2.0, col if glowing else Color(col, 0.6))
		"breath":
			ci.draw_rect(r, Color(col, 0.45 if glowing else 0.3))
		_:
			ci.draw_rect(r, Color(col, 0.75 if glowing else 0.5))
			ci.draw_rect(r, Color(LIGHT, 0.5), false, 1)


func _draw_hero(h: ArenaHero) -> void:
	if h.safe > 0.0 and int(h.safe * 20.0) % 2 == 0:
		return
	draw_rect(h.rect(), HERO)
	draw_rect(Rect2(h.pos + Vector2(h.facing * 4 - 2, -9), Vector2(4, 4)), INK0)
	if h.swinging():
		var b := h.blade()
		draw_rect(b, Color(GOLD, 0.35))
		draw_rect(b.grow(-6), Color(LIGHT, 0.8))


## Drawn over the dark: his eyes, the lantern, every telegraph, the crown, the beam.
func _draw_glow() -> void:
	if fight == null:
		return
	var ci: CanvasItem = glow
	var f := fight
	var h := f.hero
	ci.draw_circle(h.pos + Vector2(-h.facing * 10, 2), 3, EMBER2)              # your lantern
	if f.alpha > 0.05 and f.phase < 3 or f.state in ["shatter", "hover", "beam_aim", "beam", "rain", "watch"]:
		var eye := f.king + Vector2(0, -ThroneFight.KING_SIZE.y / 2.0 + 16)
		var ea := maxf(f.alpha, 0.3) if f.phase < 3 else 1.0
		ci.draw_circle(eye + Vector2(-6, 0), 2.5, Color(SHADOW2, ea))
		ci.draw_circle(eye + Vector2(6, 0), 2.5, Color(SHADOW2, ea))
	match f.state:
		"glow":
			var tip := f.king + Vector2(f.facing * 40, -90)
			ci.draw_circle(tip, 6 + f.t * 16, Color(EMBER2, 0.3 + f.t))
			ci.draw_rect(f.slash_box(), Color(EMBER1, 0.08 + f.t * 0.12))
		"aim", "cast":
			ci.draw_circle(f.king + Vector2(f.facing * 34, -20), 5 + f.t * 14, Color(EMBER1 if f.phase == 1 else SHADOW2, 0.6))
		"mark":
			var w := 30.0 + f.t * 80.0
			ci.draw_rect(Rect2(f.target.x - w / 2.0, ThroneFight.FLOOR_Y - 5, w, 5), Color(SHADOW2, 0.7))
		"shimmer":
			for i in 5:
				var x := f.target.x - 40 + i * 20
				ci.draw_line(Vector2(x, ThroneFight.FLOOR_Y), Vector2(x + sin(f.time * 30 + i) * 4, ThroneFight.FLOOR_Y - 14 - f.t * 30),
					Color(SHADOW2, 0.8), 2)
		"rise":
			ci.draw_rect(f.rise_box(), Color(SHADOW2, 0.4))
		"beam_aim":
			ci.draw_line(f.beam_from, f.beam_end(), Color(SHADOW2, 0.4 + 0.4 * sin(f.t * 40.0)), 2)
		"beam":
			ci.draw_line(f.beam_from, f.beam_end(), Color(SHADOW2, 0.5), ThroneFight.BEAM_WIDTH + 10)
			ci.draw_line(f.beam_from, f.beam_end(), LIGHT, ThroneFight.BEAM_WIDTH * 0.4)
		"finale":
			var top := Vector2(h.pos.x, -20)
			ci.draw_line(top, f.king, Color(LIGHT, clampf(1.6 - f.t, 0.0, 1.0)), 18)
	for z in f.hazards:
		if f.dark or z["tele"] > 0.0:
			_draw_hazard(z, true, glow)
	if f.phase == 3 and f.crown_state != "on" and f.state not in ["finale", "dead"]:
		if f.crown_open():
			ci.draw_circle(f.crown, 26, Color(GOLD, 0.15 + 0.1 * sin(f.time * 8.0)))
		_draw_crown(f.crown, 1.0, glow)


func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.draw.connect(_draw_hud)
	layer.add_child(hud)


func _draw_hud() -> void:
	var font := ThemeDB.fallback_font
	if flash > 0.0:
		hud.draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), Color(LIGHT, minf(0.9, flash)))
	if fight:
		for i in Game.max_hearts:                # hearts (B5's HUD will replace this)
			var col := Color("d9455f") if i < Game.hearts else INK2
			hud.draw_circle(Vector2(28 + i * 22, 26), 8, col)
		var bar := Rect2(180, 500, 600, 10)      # his bar, split into the 3 phases
		hud.draw_rect(bar.grow(2), INK0)
		hud.draw_rect(Rect2(bar.position, Vector2(bar.size.x * fight.hp_share(), bar.size.y)), SHADOW1)
		for cut in [0.3, 0.6]:
			hud.draw_line(Vector2(bar.position.x + bar.size.x * cut, bar.position.y - 3),
				Vector2(bar.position.x + bar.size.x * cut, bar.end.y + 3), GOLD, 2)
		var title := Castle.display("BOSS", "", "The Shadow King").to_upper()
		hud.draw_string(font, Vector2(bar.position.x, bar.position.y - 8), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, LIGHT)
		var phase_name: String = ["", "I · BLADE", "II · ECLIPSE", "III · FALL"][fight.phase]
		hud.draw_string(font, Vector2(bar.position.x, bar.position.y - 8), phase_name, HORIZONTAL_ALIGNMENT_RIGHT, bar.size.x, 14, SHADOW2)
		if fight.state == "finale" and fight.t < 2.2:
			var word := Castle.display("SUNFANG", "", "Sunfang").to_upper()
			hud.draw_string(font, Vector2(0, 250), word, HORIZONTAL_ALIGNMENT_CENTER, ThroneFight.W, 64, Color(GOLD, minf(1.0, fight.t * 2.0)))
	if caption_t > 0.0:
		var a := minf(1.0, caption_t)
		hud.draw_rect(Rect2(120, 400, 720, 52), Color(INK0, 0.75 * a))
		hud.draw_multiline_string(font, Vector2(136, 424), caption, HORIZONTAL_ALIGNMENT_CENTER, 688, 16, 2, Color(LIGHT, a))
