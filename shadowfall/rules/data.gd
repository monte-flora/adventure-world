class_name RulesData
## Reads the rules' JSON files in rules/data/ once and keeps them. (The teen rewrite of
## phase2/data/*.json, same format; no XP, lives, food or sword wear.)

const DIR := "res://rules/data/"
static var _cache := {}


static func get_file(name: String) -> Dictionary:
	if not _cache.has(name):
		var d = JSON.parse_string(FileAccess.get_file_as_string(DIR + name + ".json"))
		_cache[name] = d if typeof(d) == TYPE_DICTIONARY else {}
	return _cache[name]


static func person(id: String) -> Dictionary:
	for p in get_file("people").get("people", []):
		if p["id"] == id:
			return p
	return {}
