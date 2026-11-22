extends TestCase
## The forge in caves: the sword hits harder each tier (cave hp counts Wanderer's-Blade hits), and
## Sunfang swings with its glowing runes.

const ROOM := "theme: stone\n##############\n#............#\n#S..z........#\n##############"


func _open() -> CaveScene:
	Scenes.goto("cave", {"text": ROOM})
	await physics_frames(20)
	Scenes.screen.hero.set_meta("test", true)
	return Scenes.screen


func test_forged_tiers_hit_harder() -> void:
	check_eq(CaveScene.sword_damage(), 1, "Wanderer's Blade: 1")
	Game.flags["forge_tier"] = 1
	check_eq(CaveScene.sword_damage(), 2, "Tempered Blade: 2")
	Game.flags["forge_tier"] = Forge.SUNFANG_TIER
	check_eq(CaveScene.sword_damage(), 6, "Sunfang: 6")


func test_sunfang_kills_a_zombie_in_one_swing_with_runes() -> void:
	Game.flags["forge_tier"] = Forge.SUNFANG_TIER
	var cave := await _open()
	var z: CaveMonster = cave.monsters.get_child(0)
	cave.hero.position.x = z.position.x - 40
	cave.hero.facing = 1
	await physics_frames(2)
	cave.hero.attack_pressed = true
	var anim := ""
	for i in 12:
		await physics_frames(1)
		if cave.hero.sprite.animation.ends_with("_sunfang"):
			anim = cave.hero.sprite.animation
	check_eq(anim, "attack_sunfang", "the swing shows Sunfang's runes")
	check(not is_instance_valid(z), "a 3-hp zombie falls to one blow")
