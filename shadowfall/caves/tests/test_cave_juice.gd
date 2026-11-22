extends TestCase
## Cave juice (docs/teen/gameplay §4): hit-stop, screen shake and its off switch, the hurt edge,
## the kill poof, landing dust and the art in place.

const ROOM := "theme: stone\n##############\n#............#\n#S..z........#\n##############"


func _open(text: String) -> CaveScene:
	Scenes.goto("cave", {"text": text})
	await physics_frames(20)
	Scenes.screen.hero.set_meta("test", true)
	return Scenes.screen


func _swing_at_zombie(cave: CaveScene) -> CaveMonster:
	var z: CaveMonster = cave.monsters.get_child(0)
	cave.hero.position.x = z.position.x - 40
	cave.hero.facing = 1
	await physics_frames(2)
	cave.hero.attack_pressed = true
	for i in 10:
		await physics_frames(1)
		if cave.juice.stopped():
			break
	return z


func test_a_sword_hit_stops_the_cave_for_3_frames() -> void:
	var cave := await _open(ROOM)
	var z := await _swing_at_zombie(cave)
	check(cave.juice.stopped(), "the hit stops the game")
	check(not z.is_physics_processing() and not cave.hero.is_physics_processing(), "hero and monster freeze")
	check_eq(z.sprite.modulate, Color(4, 4, 4), "the monster flashes white")
	await physics_frames(CaveJuice.STOP_HIT + 1)
	check(not cave.juice.stopped() and z.is_physics_processing() and cave.hero.is_physics_processing(), "then play goes on")


func test_a_kill_leaves_a_poof() -> void:
	var cave := await _open("theme: stone\n##############\n#............#\n#S..c........#\n##############")
	var skull: CaveMonster = cave.monsters.get_child(0)
	skull.set_physics_process(false)
	cave.hero.position = skull.position - Vector2(36, 0)
	cave.hero.facing = 1
	cave.hero.attack_pressed = true
	await physics_frames(8)
	check(not is_instance_valid(skull), "one hit kills an Ember Skull")
	var poofs := cave.get_children().filter(func(n): return n is AnimatedSprite2D and n.animation == "poof")
	check_eq(poofs.size(), 1, "its poof plays")


func test_getting_hurt_shakes_and_pulses_red() -> void:
	var cave := await _open(ROOM)
	cave.monsters.get_child(0).queue_free()
	UiSettings.screen_shake = true
	cave.hurt_hero(cave.hero.position + Vector2(20, 0))
	check(cave.juice.edge.modulate.a > 0.9, "the screen edge goes red")
	await physics_frames(2)
	check(cave.cam.offset.length() > 0.0, "the camera shakes")
	check(cave.juice.stopped(), "a hurt stops the game for a moment")


func test_screen_shake_off_never_moves_the_camera() -> void:
	var cave := await _open(ROOM)
	cave.monsters.get_child(0).queue_free()
	UiSettings.screen_shake = false
	cave.hurt_hero(cave.hero.position + Vector2(20, 0))
	var most := 0.0
	for i in 12:
		await physics_frames(1)
		most = maxf(most, cave.cam.offset.length())
	UiSettings.screen_shake = true
	check_eq(most, 0.0, "no shake with screen shake off")


func test_a_hard_landing_kicks_up_dust() -> void:
	var cave := await _open("theme: stone\n######\n#.S..#\n#....#\n#....#\n#....#\n#....#\n#....#\n######")
	await physics_frames(25)                             # landed from the start, its dust gone
	cave.hero.position = Vector2(2.5 * 32, 1.5 * 32)
	cave.hero.velocity = Vector2.ZERO
	var dust := false
	for i in 60:
		await physics_frames(1)
		if cave.get_children().any(func(n): return n is CPUParticles2D):
			dust = true
			break
	check(dust, "dust when the Hero lands from high up")


func test_the_cave_is_drawn_from_the_art_sheets() -> void:
	var cave := await _open("theme: moss\n#####\n#S.E#\n#####")
	check_eq(cave.art_sheet, "tiles_moss", "the theme's tile sheet")
	check_eq(cave.parallax.size(), 4, "four parallax layers")
	check_eq(cave.hero.sprite.sprite_frames, ArtSheet.frames("hero_side"), "the Hero uses hero_side")
	check_eq(cave.map.get_cell_atlas_coords(Vector2i(2, 2)), Vector2i(2 | 4 | 8, 1), "floor rock: rock east, south and west")
