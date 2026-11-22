extends Node
## Runs every test in the project, headless:
##   godot --headless --fixed-fps 60 --path shadowfall res://tests/run_tests.tscn [-- --only=caves]
## Finds every tests/test_*.gd under res://, runs each func test_*(), prints one line per test,
## and quits with exit code 1 if any failed. A test that prints an error (SCRIPT ERROR, push_error) fails. Owned by core (B0).

const SKIP_DIRS := [".godot", "build", "levels", "addons"]

var passed := 0
var failed := 0
var _errors := _ErrorLog.new()


## Catches every engine/script error (SCRIPT ERROR, push_error) so a test that hits one fails.
class _ErrorLog extends Logger:
	var lines: PackedStringArray = []
	var _lock := Mutex.new()

	func _log_error(function: String, file: String, line: int, code: String, rationale: String,
			_editor_notify: bool, error_type: int, _backtraces: Array[ScriptBacktrace]) -> void:
		if error_type == ERROR_TYPE_WARNING:
			return
		_lock.lock()
		lines.append("%s (%s:%d %s)" % [rationale if rationale else code, file, line, function])
		_lock.unlock()

	func take() -> PackedStringArray:
		_lock.lock()
		var out := lines.duplicate()
		lines.clear()
		_lock.unlock()
		return out


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	OS.add_logger(_errors)
	Game.save_path = Game.TEST_SAVE_PATH          # tests never touch the player's save
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
		DirAccess.remove_absolute(Game.TEST_SAVE_PATH)
		Scenes.resume()
		var t: TestCase = script.new()
		add_child(t)
		Scenes.host = t
		_errors.take()
		await t.call(name)
		for e in _errors.take():
			t.failures.append("error: " + e)
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
