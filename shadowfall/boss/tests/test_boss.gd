extends TestCase
## The castle road and the Shadow King: every phase can be reached, and a scripted player
## (ThroneBot) beats him.

const DT := 1.0 / 60.0


## Runs a fight with the bot until it ends or `seconds` pass. Returns the fight.
func _bot_fight(seed_value: int, seconds := 240.0) -> ThroneFight:
	var f := ThroneFight.new(seed_value)
	var bot := ThroneBot.new()
	for i in int(seconds * 60.0):
		bot.drive(f)
		f.tick(DT)
		if f.won or f.lost:
			break
	return f


func test_castle_has_five_levels() -> void:
	var files := Castle.files()
	check_eq(files.size(), 5, "castle levels")
	for i in files.size():
		var lf := LevelFile.load_file(Paths.level(files[i]))
		check(lf.error == "", "%s loads: %s" % [files[i], lf.error])
		check(lf.find("S").size() == 1 and lf.find("D").size() == 1, files[i] + " has a start and a door")
	check(Castle.file(1).begins_with("castle/1_"), "the gate is first")
	check_eq(Castle.next(1), {"castle": 2}, "the gate leads to level 2")
	check_eq(Castle.next(5), {}, "the battlements lead to the throne")


func test_sunfang_forged_at_the_gate() -> void:
	for s in Game.STONES:
		Game.take_stone(s)
	Scenes.goto("boss", {"castle": 1})
	await physics_frames(2)
	check(Game.flags.get("sunfang", false), "Sunfang is forged at the gate")
	check_eq(Castle.sword_damage(), 7, "Sunfang hits for 7")
	Game.flags["light_shards"] = 2
	check_eq(Castle.sword_damage(), 9, "each light shard adds 1")
	check(Scenes.screen.cave != null, "the gate plays as a cave")


func test_castle_door_leads_on() -> void:
	Scenes.goto("boss", {"castle": 5})
	await physics_frames(2)
	var screen = Scenes.screen
	var door: Vector2i = screen.cave.level.find("D")[0]
	var key: Vector2i = screen.cave.level.find("K")[0]
	screen.cave.hero.position = (Vector2(door) + Vector2(0.5, 0.5)) * LevelFile.TILE
	await physics_frames(3)
	check(Scenes.screen == screen and screen.door_open_t < 0.0, "without the key the great door holds")
	check_eq(screen.caption, screen.locked_line(), "and says why, grimly")
	screen.cave.hero.position = (Vector2(key) + Vector2(0.5, 0.5)) * LevelFile.TILE
	await physics_frames(2)
	check(screen.has_key, "the key is taken")
	screen.cave.hero.position = (Vector2(door) + Vector2(0.5, 0.5)) * LevelFile.TILE
	await physics_frames(3)
	check(screen.door_open_t >= 0.0, "with the key the door opens")
	await physics_frames(int(screen.DOOR_OPEN_TIME * 60) + 6)
	check(Scenes.screen != screen and Scenes.screen.fight != null, "the last door opens the throne room")


## Every castle door is shut until you find its key (K) or pull its lever (L).
func test_every_castle_door_is_locked() -> void:
	for i in range(1, Castle.LEVELS + 1):
		var lf := LevelFile.load_file(Paths.level(Castle.file(i)))
		check(lf.find("K").size() + lf.find("L").size() > 0, "castle %d has a key or a lever" % i)
	Scenes.goto("boss", {"castle": 2})
	await physics_frames(2)
	var screen = Scenes.screen
	check(not screen.has_key, "level 2's door starts shut")
	var lever: Vector2i = screen.cave.level.find("L")[0]
	screen.cave.hero.attack_hits.append(lever)   # as if the sword struck it
	await physics_frames(2)
	check(screen.has_key, "the lever unbars the door")


func test_blade_phase() -> void:
	var f := ThroneFight.new(1)
	for i in 300:
		f.tick(DT)
	check(f.state != "intro", "the intro ends")
	check_eq(f.phase, 1, "phase 1: Blade")
	f.state = "stuck"                            # his sword is stuck: cut him
	f.hero.pos = Vector2(f.king.x - 60, f.hero.pos.y)
	f.hero.facing = 1
	f.hero.attack_pressed = true
	for i in 12:
		f.tick(DT)
	check_eq(f.hp, ThroneFight.MAX_HP - 7, "a Sunfang cut takes 7")


func test_eclipse_phase() -> void:
	var f := ThroneFight.new(2)
	f.state = "idle"
	f.hp = ThroneFight.PHASE_2_AT + 1
	f._hurt_king(7)
	check_eq(f.phase, 2, "60%: phase 2, Eclipse")
	Game.hearts = 999                            # nobody dodges here
	for i in 150:
		f.tick(DT)
	check(f.dark, "the room goes dark")
	var seen := {}
	for i in 600:
		f.tick(DT)
		seen[f.state] = true
	for s in ["vanish", "shimmer", "rise", "exposed", "echo", "cast"]:
		check(seen.has(s), "he does " + s)
	check(f.echoes.size() == 2 and f.echoes[0] != f.echoes[1], "he calls 2 lieutenants")


func test_fall_phase() -> void:
	var f := ThroneFight.new(3)
	f.phase = 2
	f.state = "exposed"
	f.hp = ThroneFight.PHASE_3_AT + 3
	f._hurt_king(7)
	check_eq(f.phase, 3, "30%: phase 3, Fall")
	check_eq(f.platforms().size(), 5, "the floor breaks into 5 platforms")
	check(not f.ground_at(ThroneFight.WALL_L + ThroneFight.PLATFORM_W + 20), "a gap over the void")
	check(not f.hittable(), "only his crown can be hurt now")
	f.hitstop = 0.0
	f.hero.pos.y = 700                           # into the void
	var hearts := Game.hearts
	f.tick(DT)
	check_eq(Game.hearts, hearts - 1, "the void costs 1 heart")
	check(f.hero.pos.y < ThroneFight.FLOOR_Y, "and puts you back on a platform")


func test_sunfang_finale() -> void:
	var f := ThroneFight.new(4)
	f.phase = 3
	f.hp = ThroneFight.PHASE_3_AT
	f.state = "watch"
	for i in 3:
		f._hit_crown()
	check_eq(f.state, "finale", "3 crown blows: the Sunfang strike")
	for i in 300:
		f.tick(DT)
	check(f.won, "he falls")
	check(Game.flags.get("shadow_king_beaten", false), "the game remembers")
	check_eq(Game.gloom, 0.0, "the gloom lifts")


func test_bot_beats_the_shadow_king() -> void:
	for seed_value in [1, 2, 3]:
		Game.reset()
		var f := _bot_fight(seed_value)
		check(f.won, "seed %d: the bot wins (phase %d, hp %d, hearts %d, %s)" % [seed_value, f.phase, f.hp, Game.hearts, f.state])
		check_eq(f.phases_seen, [1, 2, 3], "seed %d: through all 3 phases" % seed_value)


func test_throne_screen_runs() -> void:
	Scenes.goto("boss")
	await physics_frames(2)
	var screen = Scenes.screen
	check(screen.fight != null, "the throne room opens")
	screen.set_meta("test", true)
	var bot := ThroneBot.new()
	for i in 200:
		bot.drive(screen.fight)
		await get_tree().physics_frame
	check(screen.fight.time > 1.0, "the fight runs on the screen")


func test_throne_art_in_place() -> void:
	Scenes.goto("boss")
	await physics_frames(2)
	var screen = Scenes.screen
	screen.set_meta("test", true)
	check(screen.hero_spr.sprite_frames == ArtSheet.frames("hero_side"), "the hero uses the side sheet")
	check(screen.king_spr.sprite_frames == ArtSheet.frames("shadow_king"), "the king uses his sheet")
	check(screen.light is GloomLight and screen.stage.material == screen.light.world_material,
		"GloomLight darkens the hall with the gloom")
	check(screen.castle_tex != null, "castle tiles are loaded before drawing")
	var before: int = screen.get_child_count()
	screen._echo_ghost("rime_matriarch")
	check(screen.get_child_count() == before + 1, "a lieutenant's echo shows its ghost")
	for id in ThroneFight.LIEUTENANTS:
		check(FileAccess.file_exists(ArtSheet.DIR + screen.ECHO_SHEET[id] + ".json"), id + " has a ghost sheet")
