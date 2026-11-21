extends Node
## The first screen: checks the levels can be found, then goes to the title.
## `-- --scene=cave --file=caves/03_blue_lvl_1.txt` jumps straight to a screen (play-testing).

func _ready() -> void:
	var dir := Paths.levels_dir()
	if not DirAccess.dir_exists_absolute(dir):
		push_error("Shadowfall: can't find the levels folder at " + dir)
	print("Shadowfall boot: Godot %s, levels at %s" % [Engine.get_version_info().string, dir])
	var opts := Paths.cmdline()
	var target: String = opts.get("scene", "title")
	Scenes.goto.call_deferred(target, opts)
