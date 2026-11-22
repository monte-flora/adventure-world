extends TestCase
## The playthrough robot (B9 MVP): boot -> title -> New journey -> walk the realm to the nearest Mine
## that holds a Light Stone -> its cave -> take the Stone -> out the exit -> back on the realm beside
## that Mine. On the map it steers the hero like a player; in the cave it is a "ghost" that glides
## along a path of open squares (the pygame robot, cave_solver.py, proves each cave can be beaten
## for real), so this checks that the screens join up, not the jumps.

const TILE := LevelFile.TILE


func test_boot_to_first_stone_and_back() -> void:
	Scenes.goto("boot")
	await frames(3)
	check_eq(Scenes.current, "title", "boot opens the title")
	var title = Scenes.screen
	for i in title.items.size():
		if title.items[title.cursor] == "New journey":
			break
		title.press("move_down")
	title.press("jump")
	await physics_frames(2)
	check_eq(Scenes.current, "overworld", "New journey opens the realm")
	var ow = Scenes.screen
	if Scenes.current != "overworld":
		return
	check_eq(ow.hero.cell(), ow.world.home, "the journey starts at home")
	for m in ow.monsters:                     # the robot walks; fights have their own tests
		m.queue_free()
	ow.monsters.clear()

	var w: WorldMap = ow.world
	var pick := _stone_mine(w)
	var mine: Vector2i = pick[0]
	var route: Array[Vector2i] = pick[1]
	var any_stone: bool = pick[2]
	check(route.size() > 0, "a Mine can be walked to from home")
	if route.is_empty():
		return
	await _walk(ow, route)
	check_eq(Scenes.current, "cave", "walking onto the Mine opens its cave")
	if Scenes.current != "cave":
		return
	var cave: CaveScene = Scenes.screen
	check_eq(cave.file, w.cave_of[mine], "it is that Mine's cave")
	for m in cave.monsters.get_children():
		m.queue_free()

	var stone: String = cave.stone_id()
	check(any_stone, "levels/ has a Light Stone cave on the map")
	check_eq(stone, "dawn", "the nearest Stone cave holds the %s" % Names.STONE["dawn"])
	var diamonds := cave.level.find("*")
	check(diamonds.size() > 0, "the cave has a diamond")
	if diamonds.is_empty():
		return
	var hero := cave.hero
	hero.set_physics_process(false)           # the ghost moves it; the cave still does the touching
	var at := cave.cell_of(hero.position)
	await _glide(cave, _cave_path(cave, at, diamonds[0]))
	if stone != "":
		check(Game.stones.has(stone), "the robot took the %s" % Names.STONE[stone])
		check(Game.has_ability(Game.ABILITY_OF[stone]), "the Stone gives its ability")
		check(Game.has_save(), "taking the Stone saves")
	check(Game.flags.get("cave_done:" + cave.file, false), "the cave counts as done")
	var exits := cave.level.find("E")
	check(exits.size() > 0, "the cave has an exit")
	if exits.is_empty():
		return
	await _glide(cave, _cave_path(cave, diamonds[0], exits[0]))
	await physics_frames(2)
	check_eq(Scenes.current, "overworld", "the exit leads back to the realm")
	if Scenes.current == "overworld":
		var back: Vector2i = Scenes.screen.hero.cell()
		check((back - mine).length() < 2.0, "back beside the Mine (%s, Mine %s)" % [back, mine])
		check(Scenes.screen.world.at(back) not in "MSP", "not standing in the Mine again")


## The nearest reachable Mine whose cave has a `stone:` line, else the nearest reachable Mine.
## Returns [mine, route, whether any Mine on the map holds a stone].
func _stone_mine(w: WorldMap) -> Array:
	var first := []
	var any_stone := false
	for m in w.mines:                         # nearest home first
		var has_stone := LevelFile.load_file(Paths.level(w.cave_of.get(m, ""))).setting("stone") != ""
		any_stone = any_stone or has_stone
		var route := w.path(w.home, m)
		if route.is_empty():
			continue
		if has_stone:
			return [m, route, true]
		if first.is_empty():
			first = [m, route]
	return [first[0], first[1], any_stone] if first.size() > 0 else [Vector2i(-1, -1), [] as Array[Vector2i], any_stone]


## Steers the map hero along squares, like a player pressing the stick.
func _walk(ow: Node, route: Array[Vector2i], max_frames := 6000) -> void:
	var h: HeroTop = ow.hero
	var i := 0
	for f in max_frames:
		if not is_instance_valid(h) or Scenes.current != "overworld" or i >= route.size():
			break
		var d := Vector2(route[i]) * TILE + Vector2.ONE * TILE / 2.0 - h.position
		if d.length() < 4.0:
			i += 1
			continue
		h.drive = d.normalized()
		await physics_frames(1)


## Squares the ghost may pass: anything but rock and the level's edge; hazards only if it must.
func _cave_path(cave: CaveScene, from: Vector2i, to: Vector2i) -> Array[Vector2i]:
	var safe := _bfs(cave, from, to, true)
	return safe if safe.size() > 0 else _bfs(cave, from, to, false)


func _bfs(cave: CaveScene, from: Vector2i, to: Vector2i, avoid_hazards: bool) -> Array[Vector2i]:
	var came := {from: from}
	var queue: Array[Vector2i] = [from]
	var head := 0
	while head < queue.size():
		var p := queue[head]
		head += 1
		if p == to:
			var out: Array[Vector2i] = []
			while p != from:
				out.push_front(p)
				p = came[p]
			return out
		for d in [Vector2i.RIGHT, Vector2i.LEFT, Vector2i.DOWN, Vector2i.UP]:
			var q: Vector2i = p + d
			if came.has(q) or q.x < 0 or q.y < 0 or q.x >= cave.level.width or q.y >= cave.level.height:
				continue
			var ch := cave.letter(q)
			if ch == "#" or (avoid_hazards and ch in CaveTiles.HAZARD):
				continue
			came[q] = p
			queue.append(q)
	return []


## Moves the cave hero square by square (4 px a frame); hurts can't stop a ghost.
func _glide(cave: CaveScene, route: Array[Vector2i]) -> void:
	var h := cave.hero
	for cell in route:
		var goal := Vector2(cell) * TILE + Vector2.ONE * TILE / 2.0
		while true:
			if Scenes.current != "cave" or not is_instance_valid(h):
				return
			if h.position.distance_to(goal) <= 0.5:
				break
			h.iframes = 60
			h.velocity = Vector2.ZERO
			h.position = h.position.move_toward(goal, 4.0)
			await physics_frames(1)
