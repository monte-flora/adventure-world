extends SceneTree
## pixi run import-art [-- --placeholders] [-- oak pine]: realm/gemini/in/ -> realm/props/, realm/ground/.


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var only := PackedStringArray()
	for a in args:
		if not a.begins_with("--"):
			only.append(a)
	var log := ArtImport.run("--placeholders" in args, only)
	for l in log:
		print(l)
	if log.is_empty():
		print("import-art: nothing in realm/gemini/in/ yet (see realm/gemini/README.txt)")
	quit(1 if log.size() > 0 and log[0].begins_with("!") else 0)
