class_name ThroneBot
extends RefCounted
## A scripted player for the Shadow King fight (like cave_solver.py for caves). It reads the
## telegraphs a player sees and answers them: back off from the glow, jump the fireballs and
## waves, step off the shimmer, stay low under the frost breath, cut the orbs, strike in the
## punish windows, dodge the beam and pogo the crown. tests/test_boss.gd uses it.

var _jumping := false
var _dodge := 0.0                        # which way to run from this beam (chosen once)


func drive(f: ThroneFight) -> void:
	var h := f.hero
	h.ix = 0.0
	h.jump_pressed = false
	h.attack_pressed = false
	h.down_held = false
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
			"slash":
				if z["tele"] <= 0.0 and r.get_center().distance_to(h.pos) < 60.0:
					h.facing = 1 if dx > 0 else -1
					h.ix = 0.0
					h.attack_pressed = true
					if r.get_center().y > h.pos.y + 10 and not h.on_floor:
						h.down_held = true
					return
	if stay_low:
		h.jump_pressed = false
		h.jump_held = false
	# the King's own telegraphs
	var kd := f.king.x - h.pos.x
	match f.state:
		"glow", "slash":
			if absf(kd) < ThroneFight.SLASH_REACH + 70.0 and signf(-kd) == f.facing:
				var away := _away(h, f.king.x)
				if signf(away) == signf(kd) or absf(kd) < 90.0:
					h.ix = signf(kd)                # cornered: Wraithstep through him
					h.facing = 1 if kd > 0 else -1
					if absf(kd) < 105.0:
						h.dash_pressed = true
					return
				move = away
				danger = true
		"mark", "slam", "shimmer", "rise":
			if absf(f.target.x - h.pos.x) < 90.0:
				move = _away(h, f.target.x)
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


func _fall(f: ThroneFight) -> void:
	var h := f.hero
	var goal := h.pos.x
	if f.state not in ["beam_aim", "beam"]:
		_dodge = 0.0
	elif _dodge == 0.0 and _near_beam(f, h.pos):
		_dodge = _beam_side(f, h)
	if _dodge != 0.0 and _near_beam(f, h.pos):
		goal = h.pos.x + _dodge * 140.0
	elif f.crown_open():
		goal = f.crown.x
	for z in f.hazards:
		var r: Rect2 = z["rect"]
		if absf(r.get_center().x - h.pos.x) < 36.0 and r.get_center().y < h.pos.y and h.on_floor and not f.crown_open():
			goal = h.pos.x + (1.0 if r.get_center().x < h.pos.x else -1.0) * 60.0
	# stay on solid ground: never walk off a platform except by jumping the gap
	var p := f.nearest_platform(h.pos.x)
	var dx := goal - h.pos.x
	if absf(dx) > 6.0:
		h.ix = signf(dx)
		var ahead := h.pos.x + h.ix * 16.0
		if h.on_floor and not f.ground_at(ahead):
			if absf(dx) > 30.0:
				_jump(h)
			else:
				h.ix = 0.0
	elif h.on_floor and h.pos.x < p.position.x + 6:
		h.ix = 1.0
	elif h.on_floor and h.pos.x > p.end.x - 6:
		h.ix = -1.0
	if not h.on_floor and _jumping:
		h.jump_held = h.vel.y < 0.0
	# the crown: jump under it, then pogo it on the way down
	if f.crown_open() and absf(f.crown.x - h.pos.x) < 14.0:
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


func _near_beam(f: ThroneFight, at: Vector2) -> bool:
	var c := Geometry2D.get_closest_point_to_segment(at, f.beam_from, f.beam_end())
	return c.distance_to(at) < ThroneFight.BEAM_WIDTH / 2.0 + 50.0


func _beam_side(f: ThroneFight, h: ArenaHero) -> float:
	for dir in [1.0, -1.0]:
		var x: float = h.pos.x + dir * 140.0
		if x > ThroneFight.WALL_L + 20 and x < ThroneFight.WALL_R - 20 and not _near_beam(f, Vector2(x, h.pos.y)):
			return dir
	return 1.0 if h.pos.x < ThroneFight.W / 2.0 else -1.0
