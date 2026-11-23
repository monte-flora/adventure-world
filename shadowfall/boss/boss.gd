extends Node2D
## The Shadow Castle and the throne room (B8).
##   Scenes.goto("boss", {"castle": 1..5})   a castle level (played in B2's cave scene); its door
##                                           leads to the next level, the last one to the throne
##   Scenes.goto("boss")                      the Shadow King (ThroneFight), drawn here
## Art: shadow_king, hero_side, tiles_castle (walls, floor, platforms), lieutenant echoes from the
## monster sheets; the hall's windows, pillars and braziers are drawn in the palette. GloomLight on top.

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
var door_cell := Vector2i(-1, -1)
var key_cells: Array[Vector2i] = []     # K: the key to this level's door (taking one is enough)
var lever_cells: Array[Vector2i] = []   # L: levels 2 and 4 open their door with a lever instead
var has_key := false
var door_open_t := -1.0                 # seconds since the door opened (-1 = shut)
var bumped := 0                         # times you've tried the shut door
var bump_cool := 0.0
var door_art: Node2D
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
var king_spr: AnimatedSprite2D
var hero_spr: AnimatedSprite2D
var stage: Node2D                       # the hall (or the void): darkens with the gloom stage
var light: GloomLight
var castle_tex: Texture2D               # tiles_castle, loaded before any draw (loading inside a draw call shows nothing)
var hud: Control
var king_portrait: Texture2D            # art/ui/shadow_king_portrait.png, the intro card (art/src/make_king.py)

## Which monster sheet each lieutenant's echo borrows (tinted in its colour).
const ECHO_SHEET := {
	"thornwarden": "monster_stone_warden", "loom_widow": "monster_shade", "bellwarden": "monster_barrow_wight",
	"rust_regent": "monster_cinder_drake", "rime_matriarch": "monster_frost_matriarch",
	"glass_wyrm": "monster_sand_wyrm", "mire_lantern": "monster_bog_wisp",
}


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
		_say("The seven Light Stones burn together into one blade: %s." % Names.SUNFANG)
		_sfx("forge")
	Scenes.args["file"] = Castle.file(level)      # the cave scene reads its file from here
	cave = load("res://caves/cave.tscn").instantiate()
	add_child(cave)
	var lf: LevelFile = cave.get("level")
	if lf and lf.find("D").size() > 0:
		door_cell = lf.find("D")[0]
		door = Rect2(Vector2(door_cell) * LevelFile.TILE, Vector2.ONE * LevelFile.TILE).grow(6)
	if lf:
		key_cells.assign(lf.find("K"))
		lever_cells.assign(lf.find("L"))
	has_key = key_cells.is_empty() and lever_cells.is_empty()   # nothing to find: the door is open
	door_art = Node2D.new()
	door_art.z_index = 5
	door_art.draw.connect(_draw_door_and_key)
	cave.add_child(door_art)
	if caption == "" and lf:
		_say(lf.setting("name", "The Shadow Castle"))
	_music("castle")


func _castle_tick(dt: float) -> void:
	var h = cave.get("hero")
	if h == null:
		return
	bump_cool = maxf(0.0, bump_cool - dt)
	door_art.queue_redraw()
	if not has_key:
		_look_for_key(h)
	if door_open_t >= 0.0:
		door_open_t += dt
		if door_open_t >= DOOR_OPEN_TIME:
			cave = null
			Scenes.goto.call_deferred("boss", Castle.next(level))
		return
	if not (door.has_area() and door.has_point(h.position)):
		return
	if has_key:
		door_open_t = 0.0
		_say(DOOR_OPENS if level == Castle.LEVELS else "The door grinds open.")
		_sfx("door_open")
		cave.juice.shake.add(3, 14)
	elif bump_cool <= 0.0:
		bump_cool = 2.0
		bumped += 1
		_sfx("door_locked")
		var hint: String = cave.level.setting("locked door says", "")
		_say(hint if bumped % 2 == 0 and hint != "" else locked_line())


const DOOR_OPEN_TIME := 0.8
const DOOR_OPENS := "The great door groans open. Cold air, and the smell of old ash."


## What the shut door says the first time you touch it: grim, short.
func locked_line() -> String:
	if level == Castle.LEVELS:
		return "The great door will not yield. Its key hangs at the belt of the King's captain."
	if not lever_cells.is_empty():
		return "The door is barred. Somewhere in these halls, a lever holds it shut."
	return "The door is barred with black iron. Its key lies somewhere in these halls."


## K: walk into the key to take it. L: strike the lever (R) or pull it (interact) beside it.
func _look_for_key(h: HeroSide) -> void:
	var r: Rect2 = h.rect()
	for c in key_cells:
		if r.intersects(Rect2(Vector2(c) * LevelFile.TILE, Vector2.ONE * LevelFile.TILE)):
			_got_key("You take the key. Iron, and cold as a grave.")
			return
	for c in lever_cells:
		var near: bool = h.position.distance_to((Vector2(c) + Vector2(0.5, 0.5)) * LevelFile.TILE) < LevelFile.TILE * 1.6
		if c in h.attack_hits or (near and h.interact_pressed):
			_got_key("Far off, chains rattle. A bar lifts from the door.")
			return


func _got_key(text: String) -> void:
	has_key = true
	_say(text)
	_sfx("stone")


## The key until it's taken; the door, barred until it opens.
func _draw_door_and_key() -> void:
	var tile := Vector2.ONE * LevelFile.TILE
	if not has_key:
		for c in key_cells:
			var bob := Vector2(0, sin(Time.get_ticks_msec() / 250.0) * 2.0)
			door_art.draw_texture_rect(ArtSheet.tile("tiles_castle", "key"), Rect2(Vector2(c) * tile + bob, tile), false)
	if door_cell.x < 0:
		return
	var p := Vector2(door_cell) * tile
	if door_open_t >= 0.0:                       # swinging open: the dark beyond shows through
		var k := minf(1.0, door_open_t / 0.5)
		door_art.draw_rect(Rect2(p, tile), INK0)
		door_art.draw_texture_rect(ArtSheet.tile("tiles_castle", "door"), Rect2(p, Vector2(tile.x * (1.0 - k), tile.y)), false)
		return
	door_art.draw_texture_rect(ArtSheet.tile("tiles_castle", "door"), Rect2(p, tile), false)
	if not has_key:                              # black iron bars across it
		for y in [8.0, 20.0]:
			door_art.draw_rect(Rect2(p + Vector2(2, y), Vector2(tile.x - 4, 4)), INK1)


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
	castle_tex = ArtSheet.texture("tiles_castle")
	king_portrait = load("res://art/ui/shadow_king_portrait.png")
	stage = Node2D.new()
	stage.z_index = -1
	stage.draw.connect(_draw_stage)
	add_child(stage)
	king_spr = AnimatedSprite2D.new()            # art/sheets/shadow_king (B-Art), half size: 60 x 120 on screen
	king_spr.sprite_frames = ArtSheet.frames("shadow_king")
	king_spr.offset = ArtSheet.offset("shadow_king")
	king_spr.scale = Vector2(0.5, 0.5)
	king_spr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(king_spr)
	hero_spr = AnimatedSprite2D.new()
	hero_spr.sprite_frames = ArtSheet.frames("hero_side")
	hero_spr.offset = ArtSheet.offset("hero_side")
	hero_spr.play("idle")
	add_child(hero_spr)
	light = GloomLight.new()
	add_child(light)
	stage.material = light.world_material
	light.follow(hero_spr)
	add_child(preload("res://ui/hud.tscn").instantiate())
	glow = Node2D.new()                          # what shows through the dark: eyes, telegraphs
	glow.z_index = 20
	glow.draw.connect(_draw_glow)
	add_child(glow)
	_music("throne")
	Audio.play_sfx("king")                      # his motif: he is here


func _exit_tree() -> void:
	Audio.intensity = 0.0


func _physics_process(dt: float) -> void:
	caption_t = maxf(0.0, caption_t - dt)
	flash = maxf(0.0, flash - dt)
	hud.queue_redraw()
	if cave:
		_castle_tick(dt)
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
	cam.offset = Vector2(randf_range(-1, 1), randf_range(-1, 1)) * shake_px * k * Juice.shake_scale()
	dark_rect.visible = fight.dark
	Audio.intensity = intensity_of(fight)
	_king_anim(fight)
	if fight.dark:
		dark_rect.material.set_shader_parameter("hero_px", fight.hero.pos)
	_hero_anim(fight.hero)
	queue_redraw()
	stage.queue_redraw()
	glow.queue_redraw()


const VICTORY_AFTER := 2.6                 # s after he falls: the victory sting, once boss_defeat dies down


## How far the music's dark stem is pushed in: phase 1 none, phase 2 half (all of it while the hall is
## dark), phase 3 most; none once he falls.
static func intensity_of(f: ThroneFight) -> float:
	if f.won:
		return 0.0
	if f.dark:
		return 1.0
	return [0.0, 0.0, 0.5, 0.8][clampi(f.phase, 0, 3)]


## Boss sounds and tunes B6 hasn't made yet fall back to the nearest one it has (ask: B6).
const SFX_LIKE := {"boss_glow": "king", "boss_slash": "swing", "boss_fire": "dash", "boss_aim": "king",
	"boss_leap": "jump", "boss_land": "pound", "boss_shimmer": "king", "boss_beam": "die", "boss_hit": "hit",
	"boss_phase": "king", "crown_hit": "hit", "sunfang": "stone", "clang": "land", "cut": "swing",
	"pogo": "jump", "forge": "stone", "door_open": "pound", "door_locked": "land", "boss_defeat": "die", "victory": "stone"}
## The fight's tune per phase: the Blade, the Eclipse, the Fall.
const MUSIC_LIKE := {"castle": "cave", "throne": "boss", "boss_a": "boss", "boss_b": "boss_eclipse",
	"boss_c": "boss_fall"}


## Sparks and motes for the fight's big moments (overworld/juice.gd).
func _fx(name: String) -> void:
	var f := fight
	match name:
		"clang":                                 # blade on shadow armour: white-hot sparks where they met
			var at := f.hero.blade().intersection(f.body())
			Juice.burst(self, at.get_center() if at.has_area() else f.king, LIGHT, 10, 160.0, 0.25, 2.0, 300.0)
		"boss_hit":                              # a real cut: gold light bleeds out of him
			Juice.burst(self, f.king, GOLD, 12, 110.0, 0.5)
			Juice.burst(self, f.king, SHADOW2, 8, 70.0, 0.6)
		"crown_hit":
			Juice.burst(self, f.crown_rect().get_center(), EMBER2, 18, 140.0, 0.6, 3.0, 120.0)
		"boss_land":                             # stone dust from the floor either side of him
			Juice.burst(self, Vector2(f.king.x, ThroneFight.FLOOR_Y), STONE_HI, 14, 120.0, 0.5, 3.0, 200.0)


func _sfx(name: String) -> void:
	Audio.play_sfx(name if Audio.has_sfx(name) else SFX_LIKE.get(name, "hit"))


func _music(name: String) -> void:
	Audio.play_music(name if Audio.Tunes.TUNES.has(name) else MUSIC_LIKE.get(name, "boss"))


## Which row of his sheet fits what he is doing.
func _king_anim(f: ThroneFight) -> void:
	var anim := "idle"
	if f.state in ["finale", "dead"]:
		anim = "fade_out"
	elif f.flash > 0.0:
		anim = "hurt"
	elif f.phase == 3:
		anim = "cast" if f.state in ["beam_aim", "beam", "rain"] else "float"
	elif f.state in ["glow", "slash", "stuck", "pull"]:
		anim = "blade"
	elif f.state in ["aim", "throw", "cast", "spent"]:
		anim = "cast"
	elif f.state in ["echo", "roar"]:
		anim = "summon"
	if king_spr.animation != anim:
		king_spr.play(anim)
	king_spr.position = f.king + Vector2(0, ThroneFight.KING_SIZE.y / 2.0)
	king_spr.flip_h = f.facing < 0
	king_spr.modulate = Color(1, 1, 1, f.alpha) if f.flash <= 0.0 else Color(2, 2, 2, f.alpha)
	king_spr.visible = f.alpha > 0.01


## Which row of the hero's side sheet fits what ArenaHero is doing.
func _hero_anim(h: ArenaHero) -> void:
	var anim := "idle"
	if fight.lost:
		anim = "death"
	elif h.lock > 0.0:
		anim = "hurt"
	elif h.dashing():
		anim = "dash"
	elif h.swinging():
		anim = "pogo" if h.swing_down else ("attack" if h.on_floor else "air_attack")
	elif not h.on_floor:
		anim = "jump" if h.vel.y < 0.0 else "fall"
	elif absf(h.vel.x) > 10.0:
		anim = "run"
	if hero_spr.animation != anim:
		hero_spr.play(anim)
	hero_spr.position = h.pos + Vector2(0, ArenaHero.SIZE.y / 2.0)
	hero_spr.flip_h = h.facing < 0
	hero_spr.visible = not (h.safe > 0.0 and int(h.safe * 20.0) % 2 == 0)


## A fallen lieutenant's ghost rises at the wall for a moment when he calls its echo.
func _echo_ghost(id: String) -> void:
	if not ECHO_SHEET.has(id):
		return
	var g := AnimatedSprite2D.new()
	g.sprite_frames = ArtSheet.frames(ECHO_SHEET[id])
	g.offset = ArtSheet.offset(ECHO_SHEET[id])
	g.play("attack")
	var col := Color(ThroneFight.LIEUTENANTS[id]["color"])
	g.modulate = Color(col.r * 1.4, col.g * 1.4, col.b * 1.4, 0.0)
	var side := -1.0 if fight.hero.pos.x > ThroneFight.W / 2.0 else 1.0
	g.position = Vector2(ThroneFight.W / 2.0 + side * 330.0, ThroneFight.FLOOR_Y)   # the far side from you
	g.flip_h = side > 0                          # face the hero (sheets face right)
	g.scale = Vector2(1.5, 1.5) if ArtSheet.cell(ECHO_SHEET[id]).x < 96 else Vector2.ONE
	add_child(g)
	var t := g.create_tween()
	t.tween_property(g, "modulate:a", 0.55, 0.3)
	t.parallel().tween_property(g, "position:y", g.position.y - 12.0, 1.4)
	t.tween_property(g, "modulate:a", 0.0, 0.6)
	t.tween_callback(g.queue_free)


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
			_sfx(e["name"])
			_fx(e["name"])
		"music":
			_music(e["name"])
		"say":
			_say(e["text"])
		"echo":
			_say("An echo of %s rises!" % e["name"])
			_echo_ghost(e.get("id", ""))
		"clang":
			if not told_clang:
				told_clang = true
				_say("His shadow armour turns your blade. Strike when he is open: when his sword sticks, when he tires.")
		"phase":
			flash = 0.25
			_sfx("boss_phase")
		"sunfang":
			flash = 1.2
			_sfx("sunfang")
		"lost":
			end_t = 0.0
			_say("The dark takes you... The lantern by the door flickers back to life.")
		"won":
			end_t = 0.0
			_sfx("boss_defeat")
			Audio.stop_music(1.5)
			get_tree().create_timer(VICTORY_AFTER).timeout.connect(_sfx.bind("victory"))
			Juice.burst(self, fight.king, GOLD, 40, 160.0, 1.6, 3.0, -30.0)
			Juice.burst(self, fight.king, LIGHT, 24, 90.0, 2.0, 2.0, -50.0)


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
	_draw_king(f)
	for z in f.hazards:
		_draw_hazard(z, false)
	_draw_hero(f.hero)


func _draw_stage() -> void:
	if fight == null:
		return
	if fight.phase < 3:
		_draw_hall(fight)
	else:
		_draw_void(fight)


## A wall, floor or platform as castle tiles (tiles_castle solid_<bits>, bits N1 E2 S4 W8 = solid there).
func _draw_solid(ci: CanvasItem, r: Rect2, solids: Array[Rect2]) -> void:
	var T := float(LevelFile.TILE)
	var tex := castle_tex
	var y := r.position.y
	while y < r.end.y - 0.5:
		var x := r.position.x
		while x < r.end.x - 0.5:
			var size := Vector2(minf(T, r.end.x - x), minf(T, r.end.y - y))
			var mid := Vector2(x, y) + size / 2.0
			var bits := 0
			for i in 4:
				var q: Vector2 = mid + [Vector2(0, -T), Vector2(T, 0), Vector2(0, T), Vector2(-T, 0)][i]
				if q.y >= ThroneFight.H or q.y < 0.0 or q.x < 0.0 or q.x >= ThroneFight.W or solids.any(func(s): return s.has_point(q)):
					bits |= 1 << i
			var reg := Rect2(ArtSheet.region("tiles_castle", "solid_%d" % bits))
			ci.draw_texture_rect_region(tex, Rect2(Vector2(x, y), size), Rect2(reg.position, size))
			x += T
		y += T


func _draw_hall(f: ThroneFight) -> void:
	stage.draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), INK1)
	for i in 6:                                  # tall arched windows, a cold moon behind
		var x := 90.0 + i * 160.0
		stage.draw_rect(Rect2(x, 70, 44, 220), INK0)
		stage.draw_circle(Vector2(x + 22, 70), 22, INK0)
		stage.draw_rect(Rect2(x + 4, 90, 36, 196), Color(SHADOW1, 0.18))
	for x in [150.0, 400.0, 560.0, 810.0]:      # pillars with braziers
		stage.draw_rect(Rect2(x - 22, 40, 44, ThroneFight.FLOOR_Y - 40), INK2)
		stage.draw_rect(Rect2(x - 26, ThroneFight.FLOOR_Y - 20, 52, 20), STONE)
		if not f.dark:
			var flick := 6.0 + sin(f.time * 9.0 + x) * 2.0
			stage.draw_circle(Vector2(x, 236), 34, Color(EMBER1, 0.08))
			stage.draw_circle(Vector2(x, 240), flick, EMBER1)
			stage.draw_circle(Vector2(x, 242), flick * 0.5, EMBER2)
		stage.draw_rect(Rect2(x - 12, 248, 24, 10), STONE_HI)
	stage.draw_colored_polygon(PackedVector2Array([Vector2(820, ThroneFight.FLOOR_Y), Vector2(830, 230),
		Vector2(850, 190), Vector2(870, 230), Vector2(880, ThroneFight.FLOOR_Y)]), INK0)   # the throne
	for s in f.solids:
		_draw_solid(stage, s, f.solids)


func _draw_void(f: ThroneFight) -> void:
	stage.draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), Color("07050c"))
	for i in 40:                                 # motes rising out of the void
		var x := fmod(i * 97.0, ThroneFight.W)
		var y := ThroneFight.H - fmod(f.time * (20.0 + i % 5 * 8.0) + i * 53.0, ThroneFight.H)
		stage.draw_rect(Rect2(x, y, 2, 2), Color(SHADOW2, 0.35))
	for s in f.solids:
		if s.position.y == ThroneFight.FLOOR_Y:          # broken rock hanging under each platform
			stage.draw_colored_polygon(PackedVector2Array([Vector2(s.position.x, s.end.y), Vector2(s.end.x, s.end.y),
				Vector2(s.get_center().x + 14, s.end.y + 40), Vector2(s.get_center().x - 10, s.end.y + 28)]), STONE)
		_draw_solid(stage, s, f.solids)
	var ledge := castle_tex
	var lr := Rect2(ArtSheet.region("tiles_castle", "ledge"))
	for l in f.ledges:
		var x := l.position.x
		while x < l.end.x - 0.5:
			var w := minf(lr.size.x, l.end.x - x)
			stage.draw_texture_rect_region(ledge, Rect2(Vector2(x, l.position.y), Vector2(w, lr.size.y)), Rect2(lr.position, Vector2(w, lr.size.y)))
			x += lr.size.x


func _draw_king(f: ThroneFight) -> void:
	if f.alpha <= 0.01:
		return
	var c := f.king
	var a := f.alpha
	var hw := ThroneFight.KING_SIZE.x / 2.0
	var hh := ThroneFight.KING_SIZE.y / 2.0
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


func _draw_hero(h: ArenaHero) -> void:            # the sprite is hero_spr; this is the blade's flash
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
	layer.layer = GloomLight.HUD_LAYER + 1
	add_child(layer)
	hud = Control.new()
	hud.set_anchors_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.draw.connect(_draw_hud)
	layer.add_child(hud)


func _draw_hud() -> void:
	var font: Font = UiStyle.font("body")
	if flash > 0.0:
		hud.draw_rect(Rect2(0, 0, ThroneFight.W, ThroneFight.H), Color(LIGHT, minf(0.9, flash)))
	if fight:
		var bar := Rect2(180, 500, 600, 10)      # his bar, split into the 3 phases
		hud.draw_rect(bar.grow(2), INK0)
		hud.draw_rect(Rect2(bar.position, Vector2(bar.size.x * fight.hp_share(), bar.size.y)), SHADOW1)
		for cut in [0.3, 0.6]:
			hud.draw_line(Vector2(bar.position.x + bar.size.x * cut, bar.position.y - 3),
				Vector2(bar.position.x + bar.size.x * cut, bar.end.y + 3), GOLD, 2)
		var title := Names.BOSS.to_upper()
		hud.draw_string(font, Vector2(bar.position.x, bar.position.y - 8), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 14, LIGHT)
		var phase_name: String = ["", "I - BLADE", "II - ECLIPSE", "III - FALL"][fight.phase]
		hud.draw_string(font, Vector2(bar.position.x, bar.position.y - 8), phase_name, HORIZONTAL_ALIGNMENT_RIGHT, bar.size.x, 14, SHADOW2)
		if fight.phase == 1 and fight.state == "intro" and king_portrait:   # his card: fades in, holds, fades
			var ca := clampf(minf(fight.t / 0.6, (4.0 - fight.t) / 0.6), 0.0, 1.0)
			var at := Vector2((ThroneFight.W - 160) / 2.0, 60)
			hud.draw_texture(king_portrait, at, Color(1, 1, 1, ca))
			hud.draw_string(font, at + Vector2(0, 224), Names.BOSS.to_upper(), HORIZONTAL_ALIGNMENT_CENTER, 160, 16, Color(SHADOW2, ca))
		if fight.state == "finale" and fight.t < 2.2:
			var word := Names.SUNFANG.to_upper()
			hud.draw_string(font, Vector2(0, 250), word, HORIZONTAL_ALIGNMENT_CENTER, ThroneFight.W, 64, Color(GOLD, minf(1.0, fight.t * 2.0)))
	if caption_t > 0.0:
		var a := minf(1.0, caption_t)
		hud.draw_rect(Rect2(120, 400, 720, 52), Color(INK0, 0.75 * a))
		hud.draw_multiline_string(font, Vector2(136, 424), caption, HORIZONTAL_ALIGNMENT_CENTER, 688, 16, 2, Color(LIGHT, a))
