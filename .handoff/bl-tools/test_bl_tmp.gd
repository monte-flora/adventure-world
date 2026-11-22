extends TestCase
func test_bl_every_new_level_loads() -> void:
	var n := 0
	for folder in ["caves", "secret", "shadow", "castle", "stone", "realm"]:
		for f in Paths.level_files(folder):
			var lf := LevelFile.load_file(Paths.level(f))
			check(lf.error == "", f + ": " + lf.error)
			n += 1
	check(n >= 40, "found the levels (%d)" % n)
