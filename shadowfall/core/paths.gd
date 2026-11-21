class_name Paths
## Where things live. The levels stay in the repo's levels/ folder (the kid's text files and the
## pygame game share them). The editor and tests read ../levels directly; an export copies them
## into res://levels first (tools/export_web.sh). Owned by core (B0).


static func levels_dir() -> String:
	if DirAccess.dir_exists_absolute("res://levels"):
		return "res://levels"
	return ProjectSettings.globalize_path("res://").path_join("../levels").simplify_path()


## A level file by its path inside levels/, e.g. "caves/01_the_easy_moss_cave.txt".
static func level(rel: String) -> String:
	return levels_dir().path_join(rel)


## Every .txt file in one levels/ folder, sorted, as paths inside levels/ ("caves/01_....txt").
static func level_files(folder: String) -> PackedStringArray:
	var out := PackedStringArray()
	for f in DirAccess.get_files_at(levels_dir().path_join(folder)):
		if f.ends_with(".txt"):
			out.append(folder.path_join(f))
	out.sort()
	return out


## User args after `--`, as a dictionary: --scene=cave gives {"scene": "cave"}, --test gives {"test": true}.
static func cmdline() -> Dictionary:
	var d := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--"):
			var kv := a.substr(2).split("=", true, 1)
			d[kv[0]] = kv[1] if kv.size() > 1 else true
	return d
