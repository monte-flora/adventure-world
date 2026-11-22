class_name CaveRobot
extends RefCounted
## A robot that beats a cave with real physics: it only presses the Hero's buttons (ix, iy, jump,
## attack, interact) and never moves the Hero by hand. It plans a route over the cells you can stand
## in (walk, jump up to 3, drop, climb, ride a geyser or mushroom), does one move, looks where it really
## landed, and plans again. Goal: take the diamond (*), then touch E.
##   var bot := CaveRobot.new(cave); var ok: bool = await bot.run(test_case, 20000)

const T := 32.0
const AVOID := "^~!nAJ"

var cave: CaveScene
var h: HeroSide
var log := PackedStringArray()                   # what it did, for a failing test's message
var _tc                                           # the TestCase (for physics_frames)
var _dig_ok := false                             # may plan through cracked rock (it strikes it)


func _init(c: CaveScene) -> void:
	cave = c
	h = c.hero
	h.set_meta("test", true)


# ------------------------------------------------------------------ the map as the robot sees it

func _has(ch: String) -> bool:
	for row in cave.grid:
		if ch in row:
			return true
	return false


func _l(c: Vector2i) -> String:
	return cave.letter(c)


func _free(c: Vector2i) -> bool:
	var ch := _l(c)
	if ch == "B" and _dig_ok:
		return true
	return not CaveTiles.is_solid(ch) and ch not in AVOID and not _jet_fire(c)


func _jet_fire(c: Vector2i) -> bool:
	for k in CaveScene.JET_HEIGHT:
		if _l(c + Vector2i(0, k)) == "J":
			return true
	return false


func _support(c: Vector2i) -> bool:
	var ch := _l(c)
	return CaveTiles.is_solid(ch) or ch in "=-" or cave.ladder_top(c)


func standable(c: Vector2i) -> bool:
	return c.x >= 0 and _free(c) and (_support(c + Vector2i.DOWN) or _l(c) in CaveTiles.CLIMB)


## Where the Hero stands now (its cell), or the cell below if it is still in the air.
func here() -> Vector2i:
	return cave.cell_of(h.position + Vector2(0, HeroSide.SIZE.y / 2.0 - 4))


# ------------------------------------------------------------------ moves

## Moves from a cell: [kind, target]. kind: walk, drop, jump, climb, launch.
func moves(c: Vector2i) -> Array:
	var out := []
	for d in [-1, 1]:
		var n := c + Vector2i(d, 0)
		if standable(n):
			out.append(["walk", n])
		elif _free(n):
			var f := n
			for k in 14:
				f += Vector2i.DOWN
				if not _free(f):
					break
				if standable(f):
					out.append(["drop", f])
					break
	var below := _l(c + Vector2i.DOWN)
	var lift := 3
	if below == "o":
		lift = 6
	elif below == "M":
		lift = 7
	for dy in range(-3, lift + 1):
		for dx in range(-4, 5):
			if dx == 0 and dy <= 0:
				continue
			if absi(dx) <= 1 and dy == 0:
				continue
			var t := c + Vector2i(dx, -dy)
			if standable(t) and _arc_clear(c, t, maxi(dy, 0)):
				out.append(["launch" if lift > 3 else "jump", t])
	if _l(c) in CaveTiles.CLIMB or _l(c + Vector2i.DOWN) in CaveTiles.CLIMB:
		var u := c
		while _l(u) in CaveTiles.CLIMB or (u == c and _l(u + Vector2i.DOWN) in CaveTiles.CLIMB):
			u += Vector2i.UP
			if standable(u) and u != c:
				out.append(["climb", u])
		var dn := c
		while _l(dn + Vector2i.DOWN) in CaveTiles.CLIMB:
			dn += Vector2i.DOWN
			if standable(dn) and _support(dn + Vector2i.DOWN):
				out.append(["climb", dn])
	return out


## Room for the arc: headroom over the start, a clear corridor along the higher end, and down into the target.
func _arc_clear(a: Vector2i, b: Vector2i, up: int) -> bool:
	for k in range(1, maxi(up, 1) + 1):
		if not _pass(a + Vector2i(0, -k)):
			return false
	var far := absi(b.x - a.x) >= 3
	var hi := mini(a.y, b.y)
	var rows := [hi] if up > 0 else [hi - 1]        # going up you arrive level with the target
	if far:
		rows.append(rows[0] - 1)
	var step := signi(b.x - a.x)
	var x := a.x
	while x != b.x:
		x += step
		var col := rows.duplicate()
		if x == b.x:
			col = range(rows.min(), b.y + 1)
		for y in col:
			if not _pass(Vector2i(x, y)):
				return false
	return true


func _pass(c: Vector2i) -> bool:
	return _free(c) or _l(c) in "=-" + CaveTiles.CLIMB


## Breadth-first route to any goal cell: a list of [kind, cell].
func route(goals: Array) -> Array:
	var start := here()
	var prev := {start: null}
	var q := [start]
	while not q.is_empty():
		var c: Vector2i = q.pop_front()
		if c in goals:
			var path := []
			while prev[c] != null:
				path.push_front([prev[c][0], c])
				c = prev[c][1]
			return path
		for m in moves(c):
			if not prev.has(m[1]):
				prev[m[1]] = [m[0], c]
				q.append(m[1])
	return []


# ------------------------------------------------------------------ doing a move with the buttons

func _frames(n := 1) -> void:
	await _tc.physics_frames(n)


func _cx(c: Vector2i) -> float:
	return c.x * T + T / 2.0


func _done() -> bool:
	return cave.leaving or not is_instance_valid(h)


func _wait_trap_safe() -> void:
	for i in 200:
		if (cave.clock % (CaveScene.TRAP_DOWN + CaveScene.TRAP_UP)) < 8:
			return
		await _frames()


func _center_on(c: Vector2i) -> void:
	for i in 60:
		var dx := _cx(c) - h.position.x
		if absf(dx) < 3.0 and absf(h.velocity.x) < 30.0:
			break
		h.ix = clampf(dx / 12.0, -1.0, 1.0)
		await _frames()
	h.ix = 0.0


func _fight() -> void:
	for m in cave.monsters.get_children():
		if m is CaveMonster and m.position.distance_to(h.position) < 1.6 * T:
			h.facing = 1 if m.position.x > h.position.x else -1
			h.attack_pressed = true


func do_move(kind: String, t: Vector2i) -> void:
	var from := here()
	var crosses := false
	for x in range(mini(from.x, t.x), maxi(from.x, t.x) + 1):
		for y in range(mini(from.y, t.y) - 1, maxi(from.y, t.y) + 2):
			if _l(Vector2i(x, y)) in "AJ":
				crosses = true
	if kind in ["jump", "launch", "climb"]:
		await _center_on(from)
	if crosses:
		await _wait_trap_safe()
	var tx := _cx(t)
	var floor_y := (t.y + 1) * T
	match kind:
		"walk", "drop":
			for i in 90:
				_fight()
				var dx := tx - h.position.x
				h.ix = clampf(dx / 8.0, -1.0, 1.0)
				await _frames()
				if _done() or (absf(dx) < 5.0 and h.is_on_floor()):
					break
				if kind == "walk" and i > 30 and absf(h.velocity.x) < 1.0:
					await _clear_ahead(signf(dx))
		"climb":
			h.iy = -1.0 if t.y < from.y else 1.0
			for i in 240:
				await _frames()
				if _done() or (h.state == HeroSide.NORMAL and i > 2):
					break
			h.iy = 0.0
			for i in 40:
				h.ix = clampf((tx - h.position.x) / 8.0, -1.0, 1.0)
				await _frames()
				if _done() or (h.is_on_floor() and absf(tx - h.position.x) < 5.0):
					break
		"jump", "launch":
			if kind == "launch":                       # wait for the geyser to throw you (a mushroom bounces anyway)
				for i in 200:
					if not h.is_on_floor():
						break
					await _frames()
			else:
				h.jump_pressed = true
			h.jump_held = true
			var wide := absi(t.x - from.x) >= 2 or t.y >= from.y
			for i in 150:
				await _frames()
				if _done():
					break
				var bottom := h.position.y + HeroSide.SIZE.y / 2.0
				if wide or bottom < floor_y - 4.0 or h.velocity.y > 0.0:
					var dx := tx - h.position.x
					h.ix = clampf(dx / 10.0, -1.0, 1.0) if absf(dx) > 3.0 else 0.0
				if i > 3 and h.is_on_floor():
					break
			h.jump_held = false
	h.ix = 0.0
	h.iy = 0.0


## Stuck against something: strike it and dig (cracked rock, a lever's gate is opened elsewhere).
func _clear_ahead(d: float) -> void:
	h.facing = 1 if d > 0 else -1
	h.attack_pressed = true
	await _frames(16)
	h.interact_pressed = true
	await _frames(2)


# ------------------------------------------------------------------ the whole cave

func _goals_next_to(letters: String) -> Array:
	var out := []
	for r in cave.grid.size():
		for c in cave.grid[r].length():
			if cave.grid[r][c] in letters:
				for d in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1)]:
					if standable(Vector2i(c, r) + d):
						out.append(Vector2i(c, r) + d)
	return out


func _goals_on(letters: String) -> Array:
	var out := []
	for r in cave.grid.size():
		for c in cave.grid[r].length():
			if cave.grid[r][c] in letters and standable(Vector2i(c, r)):
				out.append(Vector2i(c, r))
	return out


## Take what's next to you: bump/strike ore, pull a lever.
func _use(letters: String) -> void:
	var c := here()
	for d in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		if _l(c + d) in letters:
			h.facing = 1 if d.x >= 0 else -1
			h.iy = float(d.y)
			h.ix = float(d.x)
			h.attack_pressed = true
			await _frames(16)
			h.iy = 0.0
			h.ix = 0.0
			h.interact_pressed = true
			await _frames(4)
			return


## Run the cave. True once it has the diamond (if there is one) and left through E.
func run(tc, max_moves := 400) -> bool:
	_tc = tc
	await _frames(20)
	var stuck := 0
	for n in max_moves:
		if _done():
			break
		var goals := _goals_next_to("*") if _has("*") else _goals_on("E")
		var path := route(goals)
		if path.is_empty() and _has("G"):
			path = route(_goals_next_to("L"))
			if not path.is_empty() and path.size() == 0:
				pass
		if path.is_empty():
			_dig_ok = true
			path = route(goals)
		if path.is_empty() and here() in goals:
			path = []
		if here() in goals:
			await _use("*" if _has("*") else "E")
			if not _has("*"):
				log.append("took the diamond")
			stuck += 1
			if _has("*") and stuck > 4:
				return false
			continue
		if path.is_empty():
			var lever := route(_goals_next_to("L"))
			if here() in _goals_next_to("L") and _has("G"):
				await _use("L")
				log.append("pulled a lever")
				continue
			if lever.is_empty():
				log.append("no route from %s" % str(here()))
				stuck += 3                           # crumbled ledges come back: wait and look again
				if stuck > 12:
					return false
				await _frames(60)
				continue
			path = lever
		var before := here()
		var m: Array = path[0]
		log.append("%s %s" % [m[0], str(m[1])])
		if log.size() > 60:
			log = log.slice(log.size() - 60)
		await do_move(m[0], m[1])
		stuck = stuck + 1 if here() == before else 0
		if stuck > 6:
			await _clear_ahead(1.0 if m[1].x > before.x else -1.0)
		if stuck > 12:
			log.append("stuck at %s" % str(here()))
			return false
	return cave.leaving and (cave.level.find("*").is_empty() or not _has("*"))
