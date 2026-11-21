extends Node2D
## Engine spike (Godot): a top-down walk with a scrolling camera, then a side-view jump.
##   godot --path spikes/engine/godot                 play: arrows, SPACE jumps, TAB switches, ESC quits
##   godot --path spikes/engine/godot -- --bench      a robot plays 10 s of each scene, frame times -> JSON
##   godot --headless --fixed-fps 60 --path spikes/engine/godot -- --test     game-feel checks, exit code
## In a browser (web export) the robot runs and the numbers show on screen.
## Levels come from text, like levels/caves/*.txt: '#' wall, '/' slope up to the right, '.' open.

const Hero := preload("res://hero.gd")
const TILE := 32
const SECONDS := 10.0
const GLOOM := 0.7

var args := OS.get_cmdline_user_args()
var bench := "--bench" in args or OS.has_feature("web")
var scene := "top"
var world: Node2D
var hero: Hero
var t := 0.0
var last_us := 0
var times := {"top": [], "side": []}
var label: Label


static func top_level() -> PackedStringArray:
	var rows := PackedStringArray()
	rows.append("#".repeat(80))
	for r in range(1, 59):
		var s := "#"
		for c in 78:
			s += "#" if (c * 7 + r * 13) % 23 == 0 else "."
		rows.append(s + "#")
	rows.append("#".repeat(80))
	return rows


static func side_level() -> PackedStringArray:
	var rows := PackedStringArray()
	rows.append("#".repeat(120))
	for i in 14:
		rows.append("#" + ".".repeat(118) + "#")
	for c in range(4, 118, 9):
		var r := 10 - (c / 9) % 3
		rows[r] = rows[r].substr(0, c) + "#####" + rows[r].substr(c + 5)
	rows[14] = rows[14].substr(0, 10) + "/" + rows[14].substr(11)     # a slope onto a step
	rows[14] = rows[14].substr(0, 11) + "###" + rows[14].substr(14)
	var floor_row := "#"
	for c in range(1, 119):
		floor_row += "." if (c % 40 > 30 and c % 40 < 35) else "#"
	for i in 3:
		rows.append(floor_row + "#")
	return rows


func make_tileset() -> TileSet:
	var img := Image.create(96, 32, false, Image.FORMAT_RGBA8)
	img.fill_rect(Rect2i(0, 0, 32, 32), Color("363046"))
	img.fill_rect(Rect2i(2, 2, 28, 6), Color("544c68"))
	img.fill_rect(Rect2i(32, 0, 32, 32), Color("284834"))
	img.fill_rect(Rect2i(40, 8, 6, 6), Color("345c40"))
	for y in 32:                                           # slope tile: wall below the diagonal
		for x in 32:
			if x >= 31 - y:
				img.set_pixel(64 + x, y, Color("363046"))
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	var src := TileSetAtlasSource.new()
	src.texture = ImageTexture.create_from_image(img)
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	for x in 3:
		src.create_tile(Vector2i(x, 0))
	var h := TILE / 2.0
	var box := PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	var ramp := PackedVector2Array([Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	for pair in [[Vector2i(0, 0), box], [Vector2i(2, 0), ramp]]:
		var td := src.get_tile_data(pair[0], 0)
		td.add_collision_polygon(0)
		td.set_collision_polygon_points(0, 0, pair[1])
	return ts


func build(which: String) -> void:
	scene = which
	t = 0.0
	if world:
		world.queue_free()
	world = Node2D.new()
	add_child(world)
	var rows := top_level() if which == "top" else side_level()
	var map := TileMapLayer.new()
	map.tile_set = make_tileset()
	for r in rows.size():
		for c in rows[r].length():
			var ch := rows[r][c]
			var atlas := Vector2i(0, 0) if ch == "#" else (Vector2i(2, 0) if ch == "/" else Vector2i(1, 0))
			if which == "side" and ch == ".":
				continue
			map.set_cell(Vector2i(c, r), 0, atlas)
	world.add_child(map)
	hero = Hero.new()
	hero.side = which == "side"
	hero.robot = bench
	hero.motion_mode = CharacterBody2D.MOTION_MODE_GROUNDED if hero.side else CharacterBody2D.MOTION_MODE_FLOATING
	hero.position = Vector2(90, 94) if which == "top" else Vector2(90, 314)
	world.add_child(hero)
	var cam := Camera2D.new()
	cam.process_callback = Camera2D.CAMERA2D_PROCESS_PHYSICS
	cam.position_smoothing_enabled = true
	cam.position_smoothing_speed = 10.0
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = rows[0].length() * TILE
	cam.limit_bottom = rows.size() * TILE
	hero.add_child(cam)
	# the dark: everything is tinted down, and a soft light follows the hero
	var dark := CanvasModulate.new()
	dark.color = Color(1 - GLOOM, 1 - GLOOM, (1 - GLOOM) * 1.2)
	world.add_child(dark)
	var light := PointLight2D.new()
	var g := GradientTexture2D.new()
	g.fill = GradientTexture2D.FILL_RADIAL
	g.fill_from = Vector2(0.5, 0.5)
	g.fill_to = Vector2(1.0, 0.5)
	g.width = 256
	g.height = 256
	g.gradient = Gradient.new()
	g.gradient.set_color(0, Color.WHITE)
	g.gradient.set_color(1, Color(1, 1, 1, 0))
	light.texture = g
	light.texture_scale = 1.4
	light.energy = 1.0
	hero.add_child(light)


func _ready() -> void:
	if "--fps60" in args:
		Engine.max_fps = 60
	if "--novsync" in args:
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	if "--test" in args:
		_run_tests()
		return
	build("top")
	if "--shots" in args:
		_shots()
		return
	label = Label.new()
	label.position = Vector2(4, 4)
	label.add_theme_font_size_override("font_size", 20)
	var ui := CanvasLayer.new()
	ui.add_child(label)
	add_child(ui)


func _unhandled_key_input(e: InputEvent) -> void:
	if e.is_pressed() and e is InputEventKey:
		if e.keycode == KEY_ESCAPE:
			get_tree().quit()
		elif e.keycode == KEY_TAB:
			build("side" if scene == "top" else "top")


func _process(delta: float) -> void:
	if "--test" in args or not bench or times.has("done"):
		return
	var now := Time.get_ticks_usec()
	if last_us:
		times[scene].append((now - last_us) / 1000.0)
	last_us = now
	t += delta
	if t > SECONDS:
		if scene == "top":
			build("side")
		else:
			_finish()


func _stats(ms: Array) -> Dictionary:
	ms = ms.slice(30)
	ms.sort()
	var n := ms.size()
	var mean := 0.0
	for x in ms:
		mean += x
	mean /= n
	var v := 0.0
	var late := 0
	for x in ms:
		v += (x - mean) * (x - mean)
		late += int(x > 20.0)
	var hist := {"<7": 0, "7-10": 0, "10-15": 0, "15-18": 0, "18-25": 0, ">25": 0}
	for x in ms:
		var k := "<7" if x < 7 else ("7-10" if x < 10 else ("10-15" if x < 15 else ("15-18" if x < 18 else ("18-25" if x < 25 else ">25"))))
		hist[k] += 1
	return {"hist_ms": hist, "frames": n, "mean_ms": snappedf(mean, 0.001), "stdev_ms": snappedf(sqrt(v / n), 0.001),
		"p99_ms": snappedf(ms[int(n * 0.99)], 0.001), "max_ms": snappedf(ms[n - 1], 0.001), "late_over_20ms": late}


func _finish() -> void:
	var out := {"engine": "godot " + Engine.get_version_info().string, "web": OS.has_feature("web"),
		"top": _stats(times["top"]), "side": _stats(times["side"])}
	times["done"] = true
	var text := JSON.stringify(out, " ")
	print(text)
	label.text = "%s web=%s\ntop: mean %.2f stdev %.2f p99 %.2f late %d\nside: mean %.2f stdev %.2f p99 %.2f late %d" % [
		out.engine, out.web, out.top.mean_ms, out.top.stdev_ms, out.top.p99_ms, out.top.late_over_20ms,
		out.side.mean_ms, out.side.stdev_ms, out.side.p99_ms, out.side.late_over_20ms]
	if not OS.has_feature("web"):
		var f := FileAccess.open("res://bench_godot%s.json" % ("_fps60" if "--fps60" in args else ""), FileAccess.WRITE)
		f.store_string(text)
		f.close()
		get_tree().quit()


func _shots() -> void:
	## godot --path spikes/engine/godot -- --shots : a picture of each scene (needs a window)
	hero.robot = true
	for which in ["top", "side"]:
		build(which)
		hero.robot = true
		for i in 90:
			await get_tree().process_frame
		get_viewport().get_texture().get_image().save_png("res://shot_%s.png" % which)
	get_tree().quit()


# ---------------------------------------------------------------- tests (headless)

func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _coyote_jump(delay_ticks: int) -> bool:
	## Run right off the ledge at column 10, press jump some ticks after leaving it.
	build("side")
	var rows := PackedStringArray()
	rows.append("#".repeat(20))
	for i in 8:
		rows.append("#" + ".".repeat(18) + "#")
	rows.append("#".repeat(10) + ".".repeat(10))
	rows.append("#".repeat(10) + ".".repeat(10))
	var map: TileMapLayer = world.get_child(0)
	map.clear()
	for r in rows.size():
		for c in rows[r].length():
			if rows[r][c] == "#":
				map.set_cell(Vector2i(c, r), 0, Vector2i(0, 0))
	hero.set_meta("test", true)
	hero.position = Vector2(280, 240)
	await _ticks(60)
	if not hero.is_on_floor():
		return false
	hero.ix = 1.0
	for i in 300:
		await _ticks(1)
		if not hero.is_on_floor():
			break
	await _ticks(delay_ticks)
	var before: int = hero.jumps
	hero.jump_pressed = true
	hero.jump_held = true
	await _ticks(1)
	return hero.jumps == before + 1


func _run_tests() -> void:
	var fails := []
	if not await _coyote_jump(3):           # 0.05 s after leaving: still jumps
		fails.append("coyote jump inside the window")
	if await _coyote_jump(9):               # 0.15 s after: too late
		fails.append("no jump after the window")
	build("side")                           # slope: the robot walks up the ramp onto the step
	hero.set_meta("test", true)
	await _ticks(60)
	hero.ix = 1.0
	var y0 := hero.position.y
	await _ticks(90)
	if not (hero.position.y < y0 - 20 and hero.position.x > 352):
		fails.append("walks up the slope (y %.1f -> %.1f, x %.1f)" % [y0, hero.position.y, hero.position.x])
	print("FAIL: " + ", ".join(fails) if fails else "ALL PASSED (3 checks)")
	get_tree().quit(1 if fails else 0)
