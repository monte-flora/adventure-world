extends TestCase
## Every cave the game plays loads, uses only known letters, and the Hero lands in it.

const FOLDERS := ["caves", "secret", "shadow", "stone"]


func _files() -> PackedStringArray:
	var out := PackedStringArray()
	for f in FOLDERS:
		if DirAccess.dir_exists_absolute(Paths.level(f)):
			out.append_array(Paths.level_files(f))
	return out


func test_every_cave_has_only_known_letters() -> void:
	var files := _files()
	check(files.size() >= 21, "17 caves + secret + 3 shadow found (%d)" % files.size())
	for f in files:
		var lf := LevelFile.load_file(Paths.level(f))
		check(lf.error == "", f + ": " + lf.error)
		var bad := CaveTiles.unknown(lf)
		check(bad.is_empty(), "%s: unknown letters %s" % [f, ",".join(bad)])


func test_teen_letters_are_known() -> void:
	var lf := LevelFile.from_text("stone: dawn\n#######\n#S.C<>n#\n#######")
	check(CaveTiles.unknown(lf).is_empty(), "C < > n are known: " + ",".join(CaveTiles.unknown(lf)))
	check(not CaveTiles.unknown(LevelFile.from_text("#Q#")).is_empty(), "Q is not a cave letter")


func test_every_cave_builds_and_the_hero_lands() -> void:
	for f in _files():
		if is_instance_valid(Scenes.screen):
			Scenes.screen.free()          # no overlap with the last cave's rock (goto frees it a frame late)
		Scenes.goto("cave", {"file": f})
		await physics_frames(45)
		var cave = Scenes.screen
		check(cave.map.get_used_cells().size() > 50, f + ": rock placed")
		check(cave.hero.is_on_floor(), f + ": the Hero stands on the floor")
