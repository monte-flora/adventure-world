extends Node
## Runs every test in the project, headless:
##   godot --headless --fixed-fps 60 --path shadowfall res://tests/run_tests.tscn [-- --only=caves]
## Finds every tests/test_*.gd under res://, runs each func test_*(), prints one line per test,
## and quits with exit code 1 if any failed. Owned by core (B0).

const SKIP_DIRS := [".godot", "build", "levels", "addons"]

var passed := 0
var failed := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var want := Engine.get_version_info()
	var pinned := FileAccess.get_file_as_string("res://GODOT_VERSION").strip_edges()
	print("Godot %s (pinned %s)" % [want.string, pinned])
	var only: String = Paths.cmdline().get("only", "")
	var files := PackedStringArray()
	_find("res://", files)
	files.sort()
	for f in files:
		if only != "" and only not in f:
			continue
		await _run_file(f)
	print("%d passed, %d failed" % [passed, failed])
	get_tree().quit(0 if failed == 0 and passed > 0 else 1)


func _find(dir: String, out: PackedStringArray) -> void:
	for d in DirAccess.get_directories_at(dir):
		if d not in SKIP_DIRS:
			_find(dir.path_join(d), out)
	if dir.get_file() == "tests":
		for f in DirAccess.get_files_at(dir):
			if f.begins_with("test_") and f.ends_with(".gd"):
				out.append(dir.path_join(f))


func _run_file(path: String) -> void:
	print(path)
	var script: GDScript = load(path)
	if script == null or not script.can_instantiate():
		failed += 1
		print("  FAIL  can't load this file (a script error?)")
		return
	for m in script.get_script_method_list():
		var name: String = m["name"]
		if not name.begins_with("test_"):
			continue
		Game.reset()
		Scenes.resume()
		var t: TestCase = script.new()
		add_child(t)
		Scenes.host = t
		await t.call(name)
		if t.failures.is_empty():
			passed += 1
			print("  ok    ", name)
		else:
			failed += 1
			print("  FAIL  ", name, "\n          ", "\n          ".join(t.failures))
		Scenes.host = null
		Scenes.current = ""
		t.queue_free()
		await get_tree().process_frame
