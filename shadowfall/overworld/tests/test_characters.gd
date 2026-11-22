extends TestCase
## Wave E2 characters: the Lanternbearer's light rig (the strongest light, embers, follows his facing).


func _open() -> Node:
	Scenes.goto("overworld")
	await physics_frames(2)
	return Scenes.screen


func test_hero_carries_the_strongest_light() -> void:
	var ow = await _open()
	var hero: HeroTop = ow.hero
	check(hero.light is PointLight2D and hero.light.texture != null, "the hero has a PointLight2D")
	check(hero.light.color.r > hero.light.color.b * 2.0, "the light is warm gold")
	var lights := hero.get_children().filter(func(c): return c is PointLight2D)
	check_eq(lights.size(), 1, "his own rig is his only light")
	check(hero.light.get_children().any(func(c): return c is Flicker), "it flickers (light/flicker.gd)")
	check(hero.embers is CPUParticles2D and hero.embers.emitting, "embers rise from the lantern")
	check(hero.embers.gravity.y < 0, "embers drift up")
	check(LanternLight.NPC.energy < LanternLight.HERO.energy * 0.6, "a person's torch is far weaker")
	check(LanternLight.NPC.radius < LanternLight.HERO.radius * 0.6, "and far smaller")


func test_light_follows_the_lantern_and_the_dusk() -> void:
	var ow = await _open()
	var hero: HeroTop = ow.hero
	hero.drive = Vector2.RIGHT
	await physics_frames(4)
	var right := hero.light.position.x
	hero.drive = Vector2.LEFT
	await physics_frames(12)
	check(hero.light.position.x == -right and right != 0.0, "the light swaps sides when he turns")
	hero.drive = Vector2.ZERO
	hero.light.dusk = CanvasModulate.new()
	hero.light.dusk.color = Color.WHITE
	var day := hero.light.steady_energy()
	hero.light.dusk.color = Color("3a4068")
	check(hero.light.steady_energy() > day * 1.5, "the lantern burns brighter at dusk (%.2f > %.2f)" % [hero.light.steady_energy(), day])
	hero.light.dusk.free()


func test_sunfang_runes_show_while_walking() -> void:
	for a in ["idle_down", "walk_side", "attack_up"]:
		check(ArtSheet.frames("hero_top").has_animation(a + "_sunfang"), "hero_top has %s_sunfang" % a)


func _person(ow, id: String) -> Person:
	for p in ow.people:
		if p.id == id:
			return p
	return null


func test_people_do_not_all_look_alike() -> void:
	var all: Array = RulesData.get_file("people").get("people", [])
	var looks := {}
	var kits := {}
	for d in all:
		looks[d.look] = true
		kits[str(d.look) + str(d.get("gear", []))] = true
		for item in d.get("gear", []):
			var sheet := "gear_" + str(item)
			check(not ArtSheet.meta(sheet).is_empty(), "%s's %s has art (%s)" % [d.id, item, sheet])
	check(looks.size() >= 16, "%d different looks among %d people" % [looks.size(), all.size()])
	check_eq(kits.size(), all.size(), "no two people share a look and the same gear")


func test_gear_sheets_match_the_people_sheets() -> void:
	var body: Dictionary = ArtSheet.meta("people_peasant")
	for n in ArtSheet.names():
		if not n.begins_with("gear_"):
			continue
		var m: Dictionary = ArtSheet.meta(n)
		check_eq(ArtSheet.cell(n), ArtSheet.cell("people_peasant"), n + " cell")
		check_eq(m.origin, body.origin, n + " origin")
		check(m.get("slot", "") in ["main", "off", "back"], n + " has a slot")
		for a in body.anims:
			check(m.anims.has(a) and m.anims[a].frames == body.anims[a].frames, "%s/%s frames" % [n, a])


func test_entity_toggles_equipment() -> void:
	var ow = await _open()
	var bram := _person(ow, "bram")
	check(bram is Entity and ow.hero is Entity, "people and the hero are Entities")
	check(bram.has_gear("spear") and bram.has_gear("torch"), "Bram carries his spear and torch from people.json")
	var spear: Sprite2D = bram.sprite.get_node("Gear_spear")
	check(spear.visible and spear.region_enabled, "the spear is a Sprite2D over the body")
	check(bram.equip("shield") and bram.has_gear("shield"), "a shield can be switched on")
	check(bram.toggle("shield") and not bram.has_gear("shield"), "and off again")
	check(not bram.equip("no_such_thing"), "an item with no art is refused")
	bram.equip("pack")
	bram.face(bram.position + Vector2(0, 40))
	bram.sprite.frame = 2
	bram._sync_gear()
	var pack: Sprite2D = bram.sprite.get_node("Gear_pack")
	check_eq(Rect2i(spear.region_rect), ArtSheet.region("gear_spear", "idle_down", 2), "gear follows the body's frame")
	check(pack.show_behind_parent and not spear.show_behind_parent, "facing you: the pack is behind, the spear in front")
	bram.face(bram.position + Vector2(0, -40))
	bram._sync_gear()
	check(not pack.show_behind_parent and spear.show_behind_parent, "facing away: the pack is on top")
	bram.face(bram.position + Vector2(-40, 0))
	bram._sync_gear()
	check(spear.flip_h, "gear flips with the body")
	check(not ow.hero.equip("shield"), "the hero's sheet is taller: no gear art for him yet")
