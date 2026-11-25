extends SceneTree
## pixi run import-characters [-- portrait_hero people_smith]: art/gemini/in/ -> art/ui/, art/sheets/ (CharImport).
## --hero (pixi run import-hero): only the hero_* pictures, into the live hero_top sheet.


func _init() -> void:
	var only := PackedStringArray()
	for a in OS.get_cmdline_user_args():
		if a == "--hero":
			for f in DirAccess.get_files_at(CharImport.GEMINI + "prompts"):
				if f.begins_with("hero_"):
					only.append(f.get_basename())
		elif not a.begins_with("--"):
			only.append(a)
	var log := CharImport.run(only)
	for l in log:
		print(l)
	if log.is_empty():
		print("import-characters: nothing in art/gemini/in/ yet (see art/gemini/README.txt)")
	var bad := false
	for l in log:
		bad = bad or l.begins_with("!")
	quit(1 if bad else 0)
