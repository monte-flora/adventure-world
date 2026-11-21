extends TestCase
## Cut on purpose (user, 2026-11-21): XP, lives, food, sword wear. None of them anywhere in rules/.

const BANNED := ["xp", "level_up", "lives", "life", "food", "berries", "durability", "repair", "hits_left", "armor"]
const REWARDS := ["gold", "arrows", "sun_ore", "shard", "sigil"]


func _words(text: String) -> PackedStringArray:
	var re := RegEx.new()
	re.compile("[a-z_]+")
	var out := PackedStringArray()
	for m in re.search_all(text.to_lower()):
		out.append(m.get_string())
	return out


func test_no_cut_system_in_rules_code_or_data() -> void:
	for f in DirAccess.get_files_at("res://rules"):
		if f.ends_with(".gd"):
			var code := ""
			for line in FileAccess.get_file_as_string("res://rules/" + f).split("\n"):
				code += line.split("#")[0] + "\n"      # comments may say what was cut
			for w in _words(code):
				check(w not in BANNED, "%s uses %s" % [f, w])
	for f in DirAccess.get_files_at("res://rules/data"):
		var text := FileAccess.get_file_as_string("res://rules/data/" + f)
		var about := str(JSON.parse_string(text).get("about", ""))
		for w in _words(text.replace(about, "")):
			check(w not in BANNED, "%s says %s" % [f, w])


func test_rewards_are_only_allowed_kinds() -> void:
	var qs: Dictionary = RulesData.get_file("main_quest")["quests"].duplicate()
	qs.merge(RulesData.get_file("quests")["quests"])
	for id in qs:
		for k in qs[id].get("reward", {}):
			check(k in REWARDS, "%s reward %s" % [id, k])
	for it in RulesData.get_file("shop")["buy"]:
		for k in it["gives"]:
			check(k in REWARDS, "shop %s gives %s" % [it["id"], k])
