extends TestCase
## Hearts, heart shards, hits, gold, the Lost Light.


func test_four_shards_make_a_full_heart() -> void:
	check_eq(Game.max_hearts, 5, "start with 5")
	Vitals.give("shard", 3)
	check_eq(Game.max_hearts, 5, "3 shards: still 5")
	check_eq(Vitals.shards_toward_next_heart(), 3, "3 toward the next")
	Vitals.hurt()
	Vitals.give("shard", 1)
	check_eq(Game.max_hearts, 6, "4 shards: 6 hearts")
	check_eq(Game.hearts, 5, "the new heart comes full")
	Vitals.give("shard", 40)
	check_eq(Game.max_hearts, Game.MAX_HEARTS, "never past 10")
	check(not Vitals.take("shard", 1), "shards can't be taken")


func test_hits_and_heals() -> void:
	check(not Vitals.hurt(), "1 hit")
	check_eq(Game.hearts, 4, "4 left")
	Vitals.hurt(true)
	check_eq(Game.hearts, 2, "a boss hits for 2")
	check(Vitals.hurt(true), "the last heart: dead")
	check_eq(Game.hearts, 0, "never below 0")
	Vitals.heal_full()
	check_eq(Game.hearts, 5, "a lantern heals all")


func test_items_and_gold() -> void:
	Vitals.give("arrows", 5)
	check_eq(Vitals.count("arrows"), 5, "arrows")
	check(not Vitals.take("sun_ore", 1), "no ore to take")
	check_eq(Vitals.pick_up_gold(10), 10, "gold")
	Sigils.gain("fortune")
	Sigils.wear("fortune")
	check_eq(Vitals.pick_up_gold(10), 15, "Fortune: +50%")
	check_eq(Game.gold, 25, "total")


func test_lost_light() -> void:
	Game.gold = 40
	Vitals.hurt(true); Vitals.hurt(true); Vitals.hurt(true)
	Vitals.die({"scene": "cave", "x": 3})
	check_eq(Game.gold, 0, "the gold stays where you fell")
	check_eq(Game.hearts, Game.max_hearts, "you wake with every heart")
	check_eq(Vitals.lost_light().get("gold"), 40, "a Lost Light holds it")
	check_eq(Vitals.recover_lost_light(), 40, "touch it: it comes back")
	check_eq(Game.gold, 40, "gold back")
	check(Vitals.lost_light().is_empty(), "the light is gone")
	Vitals.die({})
	Game.gold = 5
	Vitals.die({})
	check_eq(Vitals.lost_light().get("gold"), 5, "die again first: the old gold is gone")
	Game.flags["assist_keep_gold"] = true
	Game.gold = 9
	Vitals.die({})
	check_eq(Game.gold, 9, "Assist: keep your gold")
	check(Vitals.lost_light().is_empty(), "and no Lost Light")


func test_rules_state_saves() -> void:
	var path := "user://test_rules_save.json"
	Vitals.give("shard", 4)
	Vitals.give("sun_ore", 2)
	Sigils.gain("hardy")
	Sigils.wear("hardy")
	Game.gold = 7
	Vitals.die({"x": 1})
	Game.save(path)
	Game.reset()
	Game.load_save(path)
	DirAccess.remove_absolute(path)
	check_eq(Vitals.count("sun_ore"), 2, "ore comes back")
	check_eq(Vitals.count("shard"), 4, "shards come back")
	check(Sigils.is_on("hardy"), "worn sigils come back")
	check_eq(Vitals.recover_lost_light(), 7, "the Lost Light comes back")
	Vitals.refresh_max_hearts()
	check_eq(Game.max_hearts, 7, "5 + shard heart + Hardy")
