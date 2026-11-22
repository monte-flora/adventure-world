class_name ThroneBot
extends RefCounted
## A scripted player for the Shadow King fight (like cave_solver.py for caves). It reads the
## telegraphs a player sees and answers them: back off from the glow, jump the fireballs and
## waves, step off the shimmer, stay low under the frost breath, cut the orbs, strike in the
## punish windows, dodge the beam and pogo the crown. tests/test_boss.gd uses it.

var _jumping := false
var _dodge := NAN                        # where to stand for this beam (chosen once)
var _plan := ""                          # this slash: "run" or "dash" (chosen once)
var _land_x := NAN                       # where this jump over the void comes down

## Centre to centre, out of his slash: half his body + reach + half the hero + a little.
const SAFE_GAP := ThroneFight.KING_SIZE.x / 2.0 + ThroneFight.SLASH_REACH + ArenaHero.SIZE.x / 2.0 + 10.0


func drive(f: ThroneFight) -> void:
	var h := f.hero
	h.ix = 0.0
	h.jump_pressed = false
	h.attack_pressed = false
	h.down_held = false
	h.dash_pressed = false
	h.jump_held = _jumping and h.vel.y < 0.0
	if h.on_floor and h.vel.y >= 0.0:
		_jumping = false
	if f.state in ["finale", "dead"]:
		return
	if f.phase == 3:
		_fall(f)
	else:
		_ground(f)


func _jump(h: ArenaHero) -> void:
	if h.on_floor:
		h.jump_pressed = true
		h.jump_held = true
		_jumping = true


func _away(h: ArenaHero, x: float) -> float:
	var dir := 1.0 if h.pos.x >= x else -1.0
	if (dir > 0 and h.pos.x > ThroneFight.WALL_R - 60) or (dir < 0 and h.pos.x < ThroneFight.WALL_L + 60):
		dir = -dir                              # cornered: go the other way
	return dir


func _ground(f: ThroneFight) -> void:
	var h := f.hero
	var stay_low := false
	var move := 0.0
	var danger := false
	for z in f.hazards:
		var r: Rect2 = z["rect"]
		var dx := r.get_center().x - h.pos.x
		match z["dodge"]:
			"jump":
				var v: Vector2 = z["vel"]
				var coming := signf(v.x) == -signf(dx) or absf(dx) < 20.0
				if z["tele"] <= 0.0 and coming and absf(dx) < 34.0 + absf(v.x) * 0.16:
					_jump(h)
			"ground":
				if z["tele"] <= 0.6 and r.end.x > h.pos.x - 260 and r.position.x < h.pos.x + 260:
					stay_low = true
			"away":
				if absf(z["x"] - h.pos.x) < r.size.x / 2.0 + 30.0:
					move = _away(h, z["x"])
					danger = true
					var kx := f.king.x - h.pos.x
					if f.alpha > 0.5 and signf(kx) == move and absf(kx) < 80.0:
						h.dash_pressed = true          # he blocks the way: Wraithstep through him
			"slash":
				if z["tele"] <= 0.0 and r.get_center().distance_to(h.pos) < 60.0:
					h.facing = 1 if dx > 0 else -1
					h.ix = 0.0
					h.attack_pressed = true
					if r.get_center().y > h.pos.y + 10 and not h.on_floor:
						h.down_held = true
					elif r.get_center().y < h.pos.y - 16 and h.on_floor:
						_jump(h)                       # above the blade: jump into the cut
					return
	if stay_low:
		h.jump_pressed = false
		h.jump_held = false
	# the King's own telegraphs
	var kd := f.king.x - h.pos.x
	if f.state not in ["glow", "slash"]:
		_plan = ""
	match f.state:
		"glow", "slash":
			if _plan == "":                         # decide once per swing: outrun it or Wraithstep through
				_plan = "run" if _room(f) >= SAFE_GAP + 8.0 and (SAFE_GAP - absf(kd)) / ArenaHero.RUN_SPEED < 0.8 - f.t - 0.1 else "dash"
			if signf(-kd) == f.facing and absf(kd) < SAFE_GAP + 20.0:
				if _plan == "dash":
					h.ix = signf(kd)
					h.facing = 1 if kd > 0 else -1
					if absf(kd) < 100.0:
						h.dash_pressed = true
					return
				move = -signf(kd)
				danger = true
		"mark", "slam", "shimmer", "rise":     # get clear of where he comes down; past him if cornered
			var tx := f.target.x
			if absf(tx - h.pos.x) < 64.0:
				var goal := tx - 64.0 if h.pos.x < tx else tx + 64.0
				if goal < ThroneFight.WALL_L + 12.0 or goal > ThroneFight.WALL_R - 12.0:
					goal = tx + 64.0 if goal < tx else tx - 64.0
				move = signf(goal - h.pos.x)
				h.facing = int(move)
				if absf(goal - h.pos.x) > 70.0:
					h.dash_pressed = true
				danger = true
	if danger:
		h.ix = move
		return
	if f.punishable() and f.alpha > 0.9:          # strike while he's open
		var reach := ThroneFight.KING_SIZE.x / 2.0 + ArenaHero.SIZE.x / 2.0 + ArenaHero.REACH - 6.0
		if absf(kd) > reach:
			h.ix = signf(kd)
		else:
			h.facing = 1 if kd > 0 else -1
			if h.swing < 0.0:
				h.attack_pressed = true
	elif f.alpha > 0.5 and absf(kd) < 200.0:     # otherwise keep out of his reach
		h.ix = _away(h, f.king.x)
		if signf(h.ix) == signf(kd):
			h.ix = 0.0                          # cornered: hold and wait for the glow
	elif absf(kd) > 280.0 and f.alpha > 0.5:
		h.ix = signf(kd)


## How far from his centre the hero could get on its side of him.
func _room(f: ThroneFight) -> float:
	var h := f.hero
	if h.pos.x >= f.king.x:
		return ThroneFight.WALL_R - ArenaHero.SIZE.x / 2.0 - f.king.x
	return f.king.x - ThroneFight.WALL_L - ArenaHero.SIZE.x / 2.0


func _fall(f: ThroneFight) -> void:
	var h := f.hero
	var goal := h.pos.x
	var beam := f.state in ["beam_aim", "beam"]
	if h.on_floor:
		_land_x = NAN
	if not beam:
		_dodge = NAN
	elif is_nan(_dodge) and h.on_floor:
		_dodge = _beam_spot(f, h)
	if beam:
		if not is_nan(_dodge):
			goal = _dodge
	elif f.crown_open():
		goal = f.crown.x
	else:
		for z in f.hazards:
			var r: Rect2 = z["rect"]
			if absf(r.get_center().x - h.pos.x) < 36.0 and r.get_center().y < h.pos.y and h.on_floor:
				goal = h.pos.x + (1.0 if r.get_center().x < h.pos.x else -1.0) * 60.0
	# stay on solid ground: never walk off a platform except by jumping the gap (never under the beam)
	var p := f.nearest_platform(h.pos.x)
	var dx := goal - h.pos.x
	if not h.on_floor and not is_nan(_land_x):
		dx = _land_x - h.pos.x
		h.ix = signf(dx) if absf(dx) > 3.0 else 0.0
	elif absf(dx) > 6.0:
		h.ix = signf(dx)
		if h.on_floor and not beam and _orb_over(f, h.pos + Vector2(h.ix * 24.0, 0)) and not _orb_over(f, h.pos):
			h.ix = 0.0                           # let the falling orb pass first
		var ahead := h.pos.x + h.ix * 16.0
		if h.on_floor and not _ground_ahead(f, h, ahead):
			var to := _next_platform(f, h.pos.x, h.ix)
			if absf(dx) > 30.0 and not beam and to != Rect2():
				_jump(h)
				_land_x = clampf(goal, to.position.x + 16.0, to.end.x - 16.0)
			else:
				h.ix = 0.0
	elif h.on_floor and h.pos.x < p.position.x + 6:
		h.ix = 1.0
	elif h.on_floor and h.pos.x > p.end.x - 6:
		h.ix = -1.0
	if not h.on_floor and _jumping:
		h.jump_held = h.vel.y < 0.0
	# the crown: jump under it, then pogo it on the way down
	if f.crown_open() and not beam and absf(f.crown.x - h.pos.x) < 14.0:
		if h.on_floor and f.crown_state == "low":
			_jump(h)
		elif not h.on_floor and h.feet() < f.crown.y - 2.0 and h.swing < 0.0:
			h.down_held = true
			h.attack_pressed = true
	# orbs falling onto you mid-air: pogo them
	if not h.on_floor and h.swing < 0.0:
		for z in f.hazards:
			var r: Rect2 = z["rect"]
			if z["tele"] <= 0.0 and r.get_center().y > h.pos.y and r.get_center().distance_to(h.pos) < 40.0:
				h.down_held = true
				h.attack_pressed = true


## The end of this platform farthest from the beam's line (it can't be jumped: the beam is long).
func _beam_spot(f: ThroneFight, h: ArenaHero) -> float:
	var p := f.nearest_platform(h.pos.x)
	var spots := [Vector2(p.position.x + 12.0, h.pos.y), Vector2(p.end.x - 12.0, h.pos.y)]
	for l in f.ledges:                         # on a high ledge: its ends, or drop to the floor below
		if absf(h.feet() - l.position.y) < 2.0 and h.pos.x >= l.position.x and h.pos.x <= l.end.x:
			var y := ThroneFight.FLOOR_Y - ArenaHero.SIZE.y / 2.0
			spots = [Vector2(l.position.x + 12.0, h.pos.y), Vector2(l.end.x - 12.0, h.pos.y)]
			for x in [l.position.x - 16.0, l.end.x + 16.0]:
				if f.ground_at(x - 10.0) and f.ground_at(x + 10.0):
					spots.append(Vector2(x, y))
	var best := h.pos.x
	var bd := -1.0
	for at: Vector2 in spots:
		var x := at.x
		var d := Geometry2D.get_closest_point_to_segment(at, f.beam_from, f.beam_end()).distance_to(at)
		if _orb_over(f, at) and d > 40.0:
			d = 40.0                             # safe from the beam, but an orb comes down there
		if d > bd:
			bd = d
			best = x
	return best


## A falling orb is about to come down on `at`.
func _orb_over(f: ThroneFight, at: Vector2) -> bool:
	for z in f.hazards:
		var c: Vector2 = (z["rect"] as Rect2).get_center()
		if z["kind"] == "orb" and absf(c.x - at.x) < 30.0 and c.y < at.y + 10.0 and at.y - c.y < 160.0:
			return true
	return false


## Solid ground at x for a hero on the floor: its own high ledge, or a platform.
func _ground_ahead(f: ThroneFight, h: ArenaHero, x: float) -> bool:
	for l in f.ledges:
		if absf(h.feet() - l.position.y) < 2.0 and x >= l.position.x and x <= l.end.x:
			return true
	return f.ground_at(x)


## The next platform from x going dir, or an empty Rect2.
func _next_platform(f: ThroneFight, x: float, dir: float) -> Rect2:
	var best := Rect2()
	for q in f.platforms():
		var c := q.get_center().x
		if signf(c - x) == dir and (best == Rect2() or absf(c - x) < absf(best.get_center().x - x)):
			best = q
	return best
