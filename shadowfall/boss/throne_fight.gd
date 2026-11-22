class_name ThroneFight
extends RefCounted
## The Shadow King fight as plain rules and numbers (docs/teen/gameplay/README.md §6), so a test
## can run it frame by frame with no screen. boss.gd draws it and feeds it the keys; ThroneBot
## (throne_bot.gd) plays it in the tests.
##   1 Blade   (100-60%) glow 0.8 s -> slash -> sword stuck 1 s; floor fireballs; the leap and slam
##   2 Eclipse (60-30%)  dark; shadow-step (vanish 36 f, shimmer 30 f, rise); echoes of 2 of the
##                       7 lieutenants; shadow orbs you can pogo
##   3 Fall    (30-0%)   the floor breaks over the void; his crown floats free: pogo it 3 times
##                       while he sweeps a beam (36 f warning line); the Sunfang blow ends it
## Every telegraph >= 30 f, every attack leaves a punish window >= 0.8 s, his hits cost 2 hearts.

const W := 960.0
const H := 540.0
const FLOOR_Y := 448.0
const WALL_L := 32.0
const WALL_R := 928.0
const CEIL_Y := 32.0
const FR := 1.0 / 60.0                  # one frame
const MAX_HP := 90                      # at Sunfang damage (7)
const PHASE_2_AT := 54                  # 60%
const PHASE_3_AT := 27                  # 30%
const CROWN_HITS := 3
const HIT := 2                          # bosses hit for 2 hearts
const PIT := 1                          # falling into the void costs 1
const KING_SIZE := Vector2(64, 120)
const KING_SPEED := 80.0
const SLASH_REACH := 130.0
const CROWN_SIZE := Vector2(34, 22)
const CROWN_LOW_Y := FLOOR_Y - 52.0
const BEAM_WIDTH := 26.0

## The 7 lieutenants' signature attacks he calls back in the Eclipse. Display names come from
## rules/names.gd (LIEUTENANT) when B4 adds them; these are the fallbacks from the gameplay spec.
const LIEUTENANTS := {
	"thornwarden": {"name": "the Thornwarden", "attack": "charge", "color": "6fae4f"},
	"loom_widow": {"name": "the Loom Widow", "attack": "drop", "color": "b9b4c9"},
	"bellwarden": {"name": "the Bellwarden", "attack": "toll", "color": "4fa3b5"},
	"rust_regent": {"name": "the Rust Regent", "attack": "rain", "color": "b5653a"},
	"rime_matriarch": {"name": "the Rime Matriarch", "attack": "breath", "color": "cfeeff"},
	"glass_wyrm": {"name": "the Glass Wyrm", "attack": "erupt", "color": "e8c26a"},
	"mire_lantern": {"name": "the Mire Lantern", "attack": "wisps", "color": "8fe07a"},
}

const LINES := {
	"intro": "Seven stones you tore from my dark, little lantern. Kneel, and I will let your flame go out gently.",
	"eclipse": "Enough. Let the sun forget your name.",
	"echo": "Rise, my fallen. Rise once more!",
	"fall": "If I fall, this whole hall falls with me!",
	"finale": "The dawn... remembers...",
	"won": "The Shadow King is no more. The stones burn bright, and the long night breaks.",
}

var hero := ArenaHero.new()
var hp := MAX_HP
var phase := 1
var phases_seen: Array[int] = [1]
var state := "intro"
var t := 0.0                            # seconds in this state
var time := 0.0
var king := Vector2(760, FLOOR_Y - KING_SIZE.y / 2.0)
var facing := -1
var alpha := 1.0                        # 0 when he has stepped into the shadows
var safe := 0.0                         # can't be hurt again for a moment
var flash := 0.0
var slide := 0.0                        # knock-back speed
var shots := 0
var picks := 0
var last := ""
var target := Vector2()                 # shimmer / slam spot / beam end
var beam_from := Vector2()
var echoes: Array[String] = []         # the 2 lieutenants called this time
var echo_next := ""
var said := false
var dark := false
var crown := Vector2()
var crown_state := "on"                 # on, float, sink, low, reel
var crown_t := 0.0
var crown_goal := Vector2()
var crown_hits := 0
var hazards: Array[Dictionary] = []
var solids: Array[Rect2] = []
var ledges: Array[Rect2] = []
var hitstop := 0.0
var slowmo := 0.0
var events: Array[Dictionary] = []      # for the screen: shake, sfx, say, phase, music
var won := false
var lost := false
var damage := 7
var rng := RandomNumberGenerator.new()


func _init(seed_value := 0, sword_damage := 7) -> void:
	rng.seed = seed_value
	damage = sword_damage
	solids = [Rect2(0, FLOOR_Y, W, H - FLOOR_Y), Rect2(0, 0, WALL_L, H), Rect2(WALL_R, 0, W - WALL_R, H),
		Rect2(0, 0, W, CEIL_Y)]
	hero.pos = Vector2(200, FLOOR_Y - ArenaHero.SIZE.y / 2.0)


# ---- the frame ------------------------------------------------------------------------------

func tick(dt: float) -> void:
	if won or lost:
		return
	if events.size() > 64:
		events = events.slice(-32)
	if hitstop > 0.0:
		hitstop -= dt
		return
	if slowmo > 0.0:
		slowmo -= dt
		dt *= 0.5
	time += dt
	t += dt
	hero.frozen = state == "finale" or state == "dead"
	hero.step(dt, solids, ledges)
	_void_check()
	safe = maxf(0.0, safe - dt)
	flash = maxf(0.0, flash - dt)
	_king(dt)
	if phase == 3:
		_crown(dt)
	_hazards(dt)
	_blade()
	if Game.hearts <= 0 and not won:
		lost = true
		_ev("lost")


func _ev(kind: String, data := {}) -> void:
	var e := data.duplicate()
	e["kind"] = kind
	events.append(e)


func _shake(px: float, frames: int) -> void:
	_ev("shake", {"px": px, "time": frames * FR})


func _say(line: String) -> void:
	_ev("say", {"text": LINES[line]})


func _go(s: String) -> void:
	state = s
	t = 0.0


func body() -> Rect2:
	return Rect2(king - KING_SIZE / 2.0, KING_SIZE)


func crown_rect() -> Rect2:
	return Rect2(crown - CROWN_SIZE / 2.0, CROWN_SIZE)


func gap() -> float:
	return absf(hero.pos.x - king.x) - KING_SIZE.x / 2.0


func hp_share() -> float:
	return float(hp) / MAX_HP


## He can be cut now (visible, on the ground, not between phases).
func hittable() -> bool:
	return phase < 3 and alpha > 0.5 and safe <= 0.0 and state not in \
		["intro", "roar", "shatter", "vanish", "shimmer", "leap", "mark", "finale", "dead"]


## The 4 moments a player can punish him (the bot and the screen read this).
func punishable() -> bool:
	return state in ["stuck", "tired", "landed", "exposed", "spent"]


func _face() -> void:
	facing = 1 if hero.pos.x > king.x else -1


func _hurt_hero(from_x: float, hearts := HIT) -> void:
	if hero.untouchable() or won:
		return
	Game.hearts = maxi(0, Game.hearts - hearts)
	hero.hurt(from_x)
	hitstop = 10 * FR
	_shake(5, 12)
	_ev("sfx", {"name": "hurt"})


# ---- the King -------------------------------------------------------------------------------

func _king(dt: float) -> void:
	if slide != 0.0:
		king.x = clampf(king.x + slide * dt, WALL_L + KING_SIZE.x, WALL_R - KING_SIZE.x)
		slide = move_toward(slide, 0.0, 1400.0 * dt)
	if phase < 3 and alpha > 0.5 and not hero.dashing() and hero.rect().intersects(body()) and hero.feet() > king.y - KING_SIZE.y / 2.0 + 6.0:
		var side := 1.0 if hero.pos.x >= king.x else -1.0    # too big to walk through
		hero.pos.x = king.x + side * (KING_SIZE.x + ArenaHero.SIZE.x) / 2.0
		hero.vel.x = 0.0
	match phase:
		1: _blade_phase(dt)
		2: _eclipse_phase(dt)
		_: _fall_phase(dt)


func _blade_phase(dt: float) -> void:
	match state:
		"intro":
			if t >= 2.0 and not said:                # 2 s of silence before he speaks
				said = true
				_say("intro")
				_ev("music", {"name": "boss_a"})
			if t >= 4.0:
				_go("idle")
		"idle":
			_face()
			if t >= 0.6:
				_next_blade()
		"walk":
			_face()
			king.x = clampf(king.x + facing * KING_SPEED * dt, WALL_L + KING_SIZE.x, WALL_R - KING_SIZE.x)
			if gap() <= SLASH_REACH - 30.0:
				_go("glow")
				_ev("sfx", {"name": "boss_glow"})
			elif t >= 2.5:
				_start_aim()
		"glow":                                      # 48 f: his blade burns brighter
			if t >= 0.8:
				_go("slash")
				_ev("sfx", {"name": "boss_slash"})
		"slash":
			if hero.rect().intersects(slash_box()):
				_hurt_hero(king.x)
			if t >= 10 * FR:
				_go("stuck")
				_shake(3, 8)
		"stuck":                                     # the punish window
			if t >= 1.0:
				_go("pull")
		"pull":
			if t >= 0.35:
				_go("idle")
		"aim":                                       # 36 f: his hand fills with fire
			_face()
			if t >= 0.6:
				shots = 3
				_go("throw")
				t = 0.45
		"throw":
			if t >= 0.45:
				t = 0.0
				shots -= 1
				_add({"kind": "fireball", "rect": Rect2(king.x + facing * 40.0 - 11, FLOOR_Y - 24, 22, 22),
					"vel": Vector2(facing * 270.0, 0), "life": 6.0, "dodge": "jump", "slash": true})
				_ev("sfx", {"name": "boss_fire"})
				if shots <= 0:
					_go("tired")
		"tired":
			if t >= 0.9:
				_go("idle")
		"crouch":
			_face()
			if t >= 0.5:
				_go("leap")
				_ev("sfx", {"name": "boss_leap"})
		"leap":
			king.y -= 1500.0 * dt
			if t >= 0.35:
				target = Vector2(clampf(hero.pos.x, WALL_L + KING_SIZE.x, WALL_R - KING_SIZE.x), FLOOR_Y)
				_go("mark")
		"mark":                                      # 42 f: his shadow grows where he will land
			if t >= 0.7:
				king = Vector2(target.x, -KING_SIZE.y)
				_go("slam")
		"slam":
			king.y = minf(FLOOR_Y - KING_SIZE.y / 2.0, king.y + 1800.0 * dt)
			if hero.rect().intersects(body()):
				_hurt_hero(king.x)
			if king.y >= FLOOR_Y - KING_SIZE.y / 2.0:
				_shake(8, 20)
				_ev("sfx", {"name": "boss_land"})
				for dir in [-1, 1]:
					_add({"kind": "wave", "rect": Rect2(king.x + dir * 36.0 - 8, FLOOR_Y - 18, 16, 18),
						"vel": Vector2(dir * 330.0, 0), "life": 3.0, "dodge": "jump"})
				_go("landed")
		"landed":
			if t >= 0.9:
				_go("idle")


func _next_blade() -> void:
	picks += 1
	if last != "aim" and (picks % 3 == 0 or gap() > 420.0):
		_start_aim()
	elif last != "crouch" and rng.randf() < 0.3:
		last = "crouch"
		_go("crouch")
	else:
		last = "walk"
		_go("walk")


func _start_aim() -> void:
	last = "aim"
	_go("aim")
	_ev("sfx", {"name": "boss_aim"})


func slash_box() -> Rect2:
	var x := king.x if facing > 0 else king.x - SLASH_REACH - KING_SIZE.x / 2.0
	return Rect2(x + (KING_SIZE.x / 2.0 if facing > 0 else 0.0), FLOOR_Y - 96, SLASH_REACH, 96)


func _eclipse_phase(_dt: float) -> void:
	match state:
		"roar":
			_face()
			if t >= 1.6:
				dark = true
				_ev("music", {"name": "boss_b"})
				_go("vanish")
		"vanish":                                    # 36 f
			alpha = clampf(1.0 - t / 0.6, 0.0, 1.0)
			if t >= 0.6:
				target = Vector2(clampf(hero.pos.x, WALL_L + KING_SIZE.x, WALL_R - KING_SIZE.x), FLOOR_Y)
				_go("shimmer")
				_ev("sfx", {"name": "boss_shimmer"})
		"shimmer":                                   # 30 f: the floor ripples where he will rise
			if t >= 0.5:
				king = Vector2(target.x, FLOOR_Y - KING_SIZE.y / 2.0)
				alpha = 1.0
				_face()
				_go("rise")
				_shake(4, 10)
		"rise":
			if hero.rect().intersects(rise_box()):
				_hurt_hero(king.x)
			if t >= 12 * FR:
				_go("exposed")
		"exposed":
			if t >= 1.0:
				_call_echoes()
		"echo":                                      # he calls 2 fallen lieutenants; he stands still
			if t >= 1.3 and echo_next != "":
				_echo(echo_next)
				echo_next = ""
			if t >= 2.8:
				_go("cast")
				_ev("sfx", {"name": "boss_aim"})
		"cast":                                      # 36 f: shadow gathers in his hand
			_face()
			if t >= 0.6:
				for i in 3:
					_add({"kind": "orb", "rect": Rect2(king.x - 12 + (i - 1) * 40, king.y - 70 - i * 10, 24, 24),
						"vel": Vector2(), "life": 5.0, "home": 75.0 + i * 10.0, "dodge": "slash",
						"pogo": true, "slash": true})
				_go("spent")
		"spent":
			if t >= 1.1:
				_go("vanish")


func rise_box() -> Rect2:
	return Rect2(target.x - 40, FLOOR_Y - 160, 80, 160)


func _call_echoes() -> void:
	var ids := LIEUTENANTS.keys()
	var a: String = ids[rng.randi() % ids.size()]
	var b := a
	while b == a:
		b = ids[rng.randi() % ids.size()]
	echoes = [a, b]
	echo_next = b
	_go("echo")
	_say("echo")
	_echo(a)


## One lieutenant's signature attack, as a ghost: telegraph 36-40 f, then it strikes.
func _echo(id: String) -> void:
	var l: Dictionary = LIEUTENANTS[id]
	var side := 1.0 if rng.randf() < 0.5 else -1.0
	var x0 := WALL_L if side > 0 else WALL_R
	var hx := clampf(hero.pos.x, WALL_L + 30, WALL_R - 30)
	var base := {"lieu": id, "color": l["color"], "tele": 0.6}
	_ev("echo", {"name": Castle.display("LIEUTENANT", id, l["name"]), "id": id})
	match l["attack"]:
		"charge":       # the Thornwarden's antlers lowered: jump the charge
			_add(_with(base, {"kind": "charge", "rect": Rect2(x0 - (56 if side > 0 else 0), FLOOR_Y - 40, 56, 40),
				"vel": Vector2(side * 560.0, 0), "life": 3.0, "dodge": "jump"}))
		"drop":         # the Loom Widow drops on her thread: step aside
			_add(_with(base, {"kind": "drop", "rect": Rect2(hx - 18, CEIL_Y, 36, 32),
				"vel": Vector2(0, 950.0), "life": 2.0, "dodge": "away", "x": hx, "lands": true}))
		"toll":         # the Bellwarden's toll wave rolls out both ways: jump it
			for dir in [-1, 1]:
				_add(_with(base, {"kind": "toll", "rect": Rect2(king.x + dir * 40.0 - 10, FLOOR_Y - 26, 20, 26),
					"vel": Vector2(dir * 300.0, 0), "life": 3.5, "dodge": "jump"}))
		"rain":         # the Rust Regent's armor rain: 4 marked spots
			var xs := [hx]
			while xs.size() < 4:
				var x := rng.randf_range(WALL_L + 30, WALL_R - 30)
				if xs.all(func(o): return absf(o - x) > 110.0):
					xs.append(x)
			for x in xs:
				_add(_with(base, {"kind": "rain", "rect": Rect2(x - 15, CEIL_Y, 30, 30),
					"vel": Vector2(0, 760.0), "life": 2.0, "dodge": "away", "x": x, "lands": true}))
		"breath":       # the Rime Matriarch's frost breath at head height: stay low, don't jump
			_add(_with(base, {"kind": "breath", "rect": Rect2(x0 - (140 if side > 0 else 0), FLOOR_Y - 118, 140, 62),
				"vel": Vector2(side * 520.0, 0), "life": 3.0, "dodge": "ground"}))
		"erupt":        # the Glass Wyrm erupts where the sand ripples (40 f)
			_add(_with(base, {"kind": "erupt", "rect": Rect2(hx - 32, FLOOR_Y - 150, 64, 150), "tele": 40 * FR,
				"vel": Vector2(), "life": 0.4, "dodge": "away", "x": hx}))
		"wisps":        # the Mire Lantern's wisps drift after you: cut them down
			for i in 3:
				var wx := WALL_L + 60 + i * 380.0
				_add(_with(base, {"kind": "wisp", "rect": Rect2(wx, 120 + i * 40, 18, 18),
					"vel": Vector2(), "life": 4.5, "home": 95.0, "dodge": "slash", "slash": true, "pogo": true}))


func _with(a: Dictionary, b: Dictionary) -> Dictionary:
	var d := a.duplicate()
	d.merge(b, true)
	return d


func _fall_phase(dt: float) -> void:
	match state:
		"shatter":
			king = king.lerp(Vector2(W / 2.0, 104), minf(1.0, dt * 2.5))
			if t >= 2.0:
				_ev("music", {"name": "boss_b"})
				_go("hover")
		"hover":
			king = king.lerp(Vector2(W / 2.0 + sin(time * 0.7) * 60.0, 104), minf(1.0, dt * 3.0))
			if t >= 0.9:
				picks += 1
				if picks % 3 == 0:
					_go("rain")
					for i in 4:
						var x := rng.randf_range(WALL_L + 40, WALL_R - 40)
						_add({"kind": "orb", "rect": Rect2(x - 12, CEIL_Y + 10, 24, 24), "vel": Vector2(0, 150.0),
							"tele": 0.6, "life": 4.0, "dodge": "away", "x": x, "pogo": true, "slash": true})
				else:
					_go("beam_aim")
					beam_from = king + Vector2(0, 40)
					target = hero.pos
					_ev("sfx", {"name": "boss_aim"})
		"beam_aim":                                  # 36 f warning line, aimed where you stood
			if t >= 0.6:
				_go("beam")
				_shake(4, 18)
				_ev("sfx", {"name": "boss_beam"})
		"beam":
			if beam_hits(hero.rect()):
				_hurt_hero(beam_from.x)
			if t >= 0.4:
				_sink_crown()
				_go("watch")
		"rain":
			if t >= 1.2:
				_go("hover")
		"watch":                                     # the crown hangs low: the punish window
			if t >= 2.6:
				_go("hover")
		"finale":                                    # the Sunfang blow, a short cut-scene
			alpha = clampf(1.0 - (t - 1.2) / 1.6, 0.0, 1.0)
			if t >= 3.2:
				_go("dead")
				won = true
				Game.flags["shadow_king_beaten"] = true
				Game.gloom = 0.0
				Game.changed.emit()
				_say("won")
				_ev("won")


## The beam: from his hand through the spot you stood on, to the edge of the room.
func beam_end() -> Vector2:
	var d := (target - beam_from).normalized()
	if d == Vector2.ZERO:
		d = Vector2.DOWN
	return beam_from + d * 1400.0


func beam_hits(r: Rect2) -> bool:
	return Geometry2D.get_closest_point_to_segment(r.get_center(), beam_from, beam_end()) \
		.distance_to(r.get_center()) < BEAM_WIDTH / 2.0 + 10.0


# ---- phase changes, the crown, the end ------------------------------------------------------

func _hurt_king(amount: int) -> void:
	hp = maxi(phase_floor(), hp - amount)
	safe = 0.4
	flash = 0.12
	hitstop = 3 * FR
	_shake(1, 4)
	_ev("sfx", {"name": "boss_hit"})
	if not punishable() and state != "slam":
		slide = 260.0 * (1.0 if king.x >= hero.pos.x else -1.0)
	if phase == 1 and hp <= PHASE_2_AT:
		_phase(2)
	elif phase == 2 and hp <= PHASE_3_AT:
		_phase(3)


## Body blows can't take him under the Fall: only the crown ends him.
func phase_floor() -> int:
	return PHASE_3_AT if phase < 3 else 0


func _phase(n: int) -> void:
	phase = n
	phases_seen.append(n)
	hazards.clear()
	alpha = 1.0
	hitstop = 20 * FR
	slowmo = 0.4
	_shake(6, 30)
	_ev("phase", {"phase": n})
	if n == 2:
		_say("eclipse")
		_go("roar")
	else:
		hp = PHASE_3_AT
		dark = false
		_say("fall")
		_break_floor()
		crown = king + Vector2(0, -KING_SIZE.y / 2.0 - 8)
		crown_state = "float"
		_go("shatter")


## The floor breaks into 5 platforms over the void, with 2 high ledges.
const PLATFORM_W := 140.0
const PLATFORM_GAP := 49.0
func _break_floor() -> void:
	solids = [Rect2(0, 0, WALL_L, H), Rect2(WALL_R, 0, W - WALL_R, H), Rect2(0, 0, W, CEIL_Y)]
	for i in 5:
		solids.append(Rect2(WALL_L + i * (PLATFORM_W + PLATFORM_GAP), FLOOR_Y, PLATFORM_W, 24))
	ledges = [Rect2(318, 344, 96, 12), Rect2(546, 344, 96, 12)]
	hero.pos = Vector2(nearest_platform(hero.pos.x).get_center().x, FLOOR_Y - ArenaHero.SIZE.y / 2.0)
	hero.vel = Vector2()


func platforms() -> Array[Rect2]:
	var out: Array[Rect2] = []
	for s in solids:
		if s.position.y == FLOOR_Y and s.size.x < W:
			out.append(s)
	return out


func nearest_platform(x: float) -> Rect2:
	var best := Rect2()
	var bd := INF
	for p in platforms():
		var d := absf(p.get_center().x - x)
		if d < bd:
			bd = d
			best = p
	return best


## Ground under x (phase 3 has gaps). The bot asks this.
func ground_at(x: float) -> bool:
	if phase < 3:
		return x > WALL_L and x < WALL_R
	for p in platforms():
		if x >= p.position.x and x <= p.end.x:
			return true
	return false


func _void_check() -> void:
	if hero.pos.y > H + 40.0:
		Game.hearts = maxi(0, Game.hearts - PIT)
		var p := nearest_platform(hero.pos.x)
		hero.pos = Vector2(p.get_center().x, p.position.y - ArenaHero.SIZE.y / 2.0)
		hero.vel = Vector2()
		hero.safe = ArenaHero.HURT_SAFE
		_ev("sfx", {"name": "hurt"})


func _sink_crown() -> void:
	var p := nearest_platform(hero.pos.x)
	crown_goal = Vector2(clampf(hero.pos.x, p.position.x + 30, p.end.x - 30), CROWN_LOW_Y)
	crown_state = "sink"
	crown_t = 0.0


func _crown(dt: float) -> void:
	crown_t += dt
	match crown_state:
		"float":
			var goal := Vector2(W / 2.0 + sin(time * 1.1) * 260.0, 200 + sin(time * 2.3) * 30.0)
			crown = crown.lerp(goal, minf(1.0, dt * 2.0))
		"sink":
			crown = crown.move_toward(crown_goal, 520.0 * dt)
			if crown.distance_to(crown_goal) < 1.0:
				crown_state = "low"
				crown_t = 0.0
		"low":
			crown = crown_goal + Vector2(0, sin(crown_t * 5.0) * 3.0)
			if crown_t >= 2.0:
				crown_state = "float"
		"reel":
			crown = crown.move_toward(Vector2(crown.x, 180), 700.0 * dt)
			if crown_t >= 0.6:
				crown_state = "float"


func crown_open() -> bool:
	return phase == 3 and crown_state in ["sink", "low"] and state != "finale"


func _hit_crown() -> void:
	crown_hits += 1
	hp = PHASE_3_AT - crown_hits * (PHASE_3_AT / CROWN_HITS)
	crown_state = "reel"
	crown_t = 0.0
	hitstop = 6 * FR
	_shake(3, 10)
	_ev("sfx", {"name": "crown_hit"})
	if crown_hits >= CROWN_HITS:
		hp = 0
		hazards.clear()
		slowmo = 1.2
		hitstop = 20 * FR
		_shake(8, 40)
		_ev("sunfang")
		_say("finale")
		_go("finale")


# ---- hazards and the blade ------------------------------------------------------------------

func _add(h: Dictionary) -> void:
	if not h.has("tele"):
		h["tele"] = 0.0
	hazards.append(h)


func _hazards(dt: float) -> void:
	for h in hazards.duplicate():
		if h["tele"] > 0.0:
			h["tele"] -= dt
			continue
		var r: Rect2 = h["rect"]
		if h.has("home"):
			var want: Vector2 = (hero.pos - r.get_center()).normalized() * h["home"]
			h["vel"] = (h["vel"] as Vector2).move_toward(want, 300.0 * dt)
		r.position += h["vel"] * dt
		if h.get("lands", false) and r.end.y >= FLOOR_Y and phase < 3:
			r.position.y = FLOOR_Y - r.size.y
			if h["vel"] != Vector2.ZERO:
				h["vel"] = Vector2()
				h["life"] = minf(h["life"], 0.35)
				_shake(2, 6)
		h["rect"] = r
		h["life"] -= dt
		if h["life"] <= 0.0 or r.end.x < -80 or r.position.x > W + 80 or r.position.y > H + 40:
			hazards.erase(h)
		elif hero.rect().intersects(r):
			_hurt_hero(r.get_center().x)
			if h["kind"] in ["fireball", "orb", "wisp"]:
				hazards.erase(h)


func _blade() -> void:
	if not hero.swinging():
		return
	var b := hero.blade()
	if hittable() and b.intersects(body()) and hero.first_hit("king"):
		if hero.swing_down:
			hero.bounce()
		if punishable():
			_hurt_king(damage)
		else:                                    # his shadow armour turns the blade: wait for an opening
			hero.vel.x = -hero.facing * 220.0
			_ev("sfx", {"name": "clang"})
			_ev("clang")
	if crown_open() and hero.swing_down and b.intersects(crown_rect()) and hero.first_hit("crown"):
		hero.bounce()
		_hit_crown()
	for h in hazards.duplicate():
		if h["tele"] > 0.0 or not b.intersects(h["rect"]):
			continue
		if h.get("pogo", false) and hero.swing_down:
			hero.bounce()
			hazards.erase(h)
			_ev("sfx", {"name": "pogo"})
		elif h.get("slash", false):
			hazards.erase(h)
			_ev("sfx", {"name": "cut"})
