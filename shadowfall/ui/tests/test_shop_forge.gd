extends TestCase
## The shop screen (buy, sell, can't overspend, sold out) and the forge screen (timing bar, tiers),
## and what you buy takes effect.


func _shop(trader := "tamsin") -> ShopScreen:
	var s := ShopScreen.new()
	s.trader = trader
	Engine.get_main_loop().root.add_child(s)
	await frames(1)
	return s


func _row(s: ShopScreen, id: String) -> int:
	var rs := s.rows()
	for i in rs.size():
		if rs[i].id == id:
			return i
	return -1


func test_buy_with_gold_and_never_overspend() -> void:
	var s := await _shop()
	Game.gold = 20
	s.cursor = _row(s, "sun_ore")
	check(not s.confirm(), "25 gold of ore with 20: no")
	check_eq(s.message, "Not enough gold.", "and says why")
	check_eq(Game.gold, 20, "no gold spent")
	s.cursor = _row(s, "arrows")
	check(s.confirm(), "arrows for 6")
	check_eq(Game.gold, 14, "6 gold spent")
	check_eq(Vitals.count("arrows"), 5, "+5 arrows")
	check_eq(s._about.text, "+5 arrows", "the description shows")
	s.close()


func test_stock_runs_out_and_sigils_are_owned() -> void:
	var s := await _shop()
	Game.gold = 500
	s.cursor = _row(s, "shard")
	var hearts := Game.max_hearts
	check(s.confirm(), "a heart shard")
	check(not s.confirm(), "only one")
	check_eq(s.message, "Sold out.", "sold out")
	s.cursor = _row(s, "fortune")
	check(s.confirm(), "the Sigil of Fortune")
	check("fortune" in Sigils.owned(), "is yours")
	check_eq(Vitals.count("shard"), 1, "the shard counts toward a heart")
	check_eq(Game.max_hearts, hearts, "one shard isn't a heart yet")
	s.close()


func test_tonic_mends_and_phial_fills_lumen() -> void:
	var s := await _shop()
	Game.gold = 100
	Game.hearts = 1
	s.cursor = _row(s, "tonic")
	s.confirm()
	check_eq(Game.hearts, 3, "a tonic mends 2 hearts")
	s.cursor = _row(s, "lumen")
	s.confirm()
	check_eq(Vitals.lumen_charges(), 1, "a phial fills a heal charge")
	s.close()


func test_sell_sun_ore() -> void:
	var s := await _shop()
	Vitals.give("sun_ore", 1)
	s.press("move_right")
	check(s.selling, "RIGHT: the SELL side")
	s.cursor = _row(s, "sun_ore")
	check(s.confirm(), "sell a piece")
	check_eq(Game.gold, 10, "for 10 gold")
	check(not s.confirm(), "none left to sell")
	s.press("move_up")
	s.cursor = s.rows().size() - 1
	s.confirm()
	check(not is_instance_valid(s) or s.is_queued_for_deletion(), "Leave closes it")


func test_forge_tiers_and_timing_bar() -> void:
	var f := ForgeScreen.new()
	Engine.get_main_loop().root.add_child(f)
	await frames(1)
	check(not f.begin(), "no ore, no gold: can't")
	check(f._note.text.contains("sun ore"), "says what it needs")
	Vitals.give("sun_ore", 2)
	Vitals.give("gold", 30)
	check(f.begin(), "now the steel heats")
	check_eq(f.strike(0.9), "miss", "a wild blow")
	check_eq(f.result, "cooled", "the metal cools")
	check_eq(Vitals.count("sun_ore"), 2, "nothing spent")
	f.begin()
	for i in 3:
		f.strike(0.5)
	check_eq(f.result, "perfect", "three true blows")
	check_eq(Forge.tier(), 1, "Tempered Blade")
	check_eq(Forge.sword_damage(), 3, "hits for 3")
	check(Forge.crit_chance() > 0.0, "a perfect temper adds crit")
	check_eq(Game.gold, 0, "gold spent")
	await frames(2)
	f.begin()
	check(not f.hammering, "tier 2 needs more ore")
	f.close()


func test_sunfang_swings_with_runes() -> void:
	Scenes.goto("overworld")
	await physics_frames(2)
	var h: HeroTop = Scenes.screen.hero
	Game.flags["forge_tier"] = Forge.SUNFANG_TIER
	h.attack()
	await physics_frames(2)
	check(h.sprite.animation.ends_with("_sunfang"), "Sunfang's swing shows its runes")
	check_eq(Forge.sword_damage(), 7, "and hits for 7")
