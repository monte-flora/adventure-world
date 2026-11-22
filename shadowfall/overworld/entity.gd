class_name Entity
extends Node2D
## The base of everyone who walks the realm (HeroTop, Person): a body sprite plus equipment you can
## switch on and off. Each item is a Sprite2D laid over the body from its own sheet, art/sheets/gear_<item>
## (same cell, origin and animations as the body sheet), so one body sheet makes many different people:
##   equip("shield")   equip("shield", false)   toggle("lantern")   has_gear("pack")   gear() -> names
## The overlays follow the body's animation, frame and flip every frame. An item hides while the body
## plays an animation its sheet lacks (a roll, say). Slot (the sheet JSON's "slot"): "back" items go
## behind the body when it faces you, hand items ("main", "off") go behind when it faces away.
## `gear_set` picks sheets for another body size: "tall" -> gear_tall_<item>.

var sprite: AnimatedSprite2D
var gear_set := ""
var _gear := {}                              # item -> its Sprite2D


func gear_sheet(item: String) -> String:
	return "gear_" + (gear_set + "_" if gear_set != "" else "") + item


## Shows (or hides) an item. False if there is no body sprite yet or no art for the item.
func equip(item: String, on := true) -> bool:
	if not on:
		if _gear.has(item):
			_gear[item].queue_free()
			_gear.erase(item)
		return true
	if _gear.has(item):
		return true
	var sheet := gear_sheet(item)
	if sprite == null or ArtSheet.meta(sheet).is_empty():
		return false
	var s := Sprite2D.new()
	s.name = "Gear_" + item
	s.texture = ArtSheet.texture(sheet)
	s.region_enabled = true
	s.offset = ArtSheet.offset(sheet)
	s.set_meta("sheet", sheet)
	sprite.add_child(s)
	_gear[item] = s
	_sync_gear()
	return true


func toggle(item: String) -> bool:
	return equip(item, not has_gear(item))


func has_gear(item: String) -> bool:
	return _gear.has(item)


func gear() -> Array:
	return _gear.keys()


## Where an item's flame is, from this node's origin (Vector2.INF if the item gives no light).
func gear_light_at(item: String) -> Vector2:
	var meta := ArtSheet.meta(gear_sheet(item))
	var at: Dictionary = meta.get("light", {})
	var dir := _gear_dir()
	if sprite == null or not at.has(dir):
		return Vector2.INF
	var p := Vector2(float(at[dir][0]), float(at[dir][1])) - Vector2(ArtSheet.cell(gear_sheet(item))) / 2.0
	p += ArtSheet.offset(gear_sheet(item))
	if sprite.flip_h:
		p.x = -p.x
	return sprite.position + p


func _gear_dir() -> String:
	return str(sprite.animation).trim_suffix("_sunfang").get_slice("_", 1) if sprite else "down"


func _sync_gear() -> void:
	if _gear.is_empty():
		return
	var anim := str(sprite.animation).trim_suffix("_sunfang")
	var dir := _gear_dir()
	for item in _gear:
		var s: Sprite2D = _gear[item]
		var sheet: String = s.get_meta("sheet")
		var meta := ArtSheet.meta(sheet)
		var has: bool = meta["anims"].has(anim)
		s.visible = has
		if not has:
			continue
		var n := int(meta["anims"][anim]["frames"])
		s.region_rect = Rect2(ArtSheet.region(sheet, anim, sprite.frame % n))
		s.flip_h = sprite.flip_h
		var back: bool = meta.get("slot", "main") == "back"
		s.show_behind_parent = (dir == "down") if back else (dir == "up")


func _process(_dt: float) -> void:
	_sync_gear()
