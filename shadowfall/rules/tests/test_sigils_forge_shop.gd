extends TestCase
## Sigils (slots and effects), the forge (tiers, timing bar, Sunfang), the shop.


func test_sigil_slots_grow_with_stones() -> void:
	check_eq(Sigils.slots(), 3, "3 slots at the start")
	for s in ["dawn", "leaf"]:
		Game.take_stone(s)
	check_eq(Sigils.slots(), 4, "+1 at 2 stones")
	for s in Game.STONES:
		Game.take_stone(s)
	check_eq(Sigils.slots(), 6, "6 at most")


func test_sigils_cost_slots() -> void:
	check(not Sigils.wear("keen_edge"), "can't wear one you don't own")
	for id in ["keen_edge", "swiftfoot", "hardy"]:
		check(Sigils.gain(id), "gain " + id)
	check(not Sigils.gain("hardy"), "only once")
	check(Sigils.wear("keen_edge"), "Keen Edge: 3 slots")
	check(not Sigils.wear("swiftfoot"), "no room left")
	check_eq(Forge.sword_damage(), 3, "Keen Edge: +1 damage")
	Sigils.remove("keen_edge")
	check(Sigils.wear("swiftfoot") and Sigils.wear("hardy"), "1 + 2 slots fit")
	check_eq(Sigils.run_speed(), 8.5, "Swiftfoot")
	check_eq(Game.max_hearts, 6, "Hardy: +1 heart")
	Sigils.remove("hardy")
	check_eq(Game.max_hearts, 5, "take it off: back to 5")
	check(Game.hearts <= Game.max_hearts, "hearts never above max")
	for id in Sigils.ALL:
		check(Sigils.cost(id) >= 1 and Sigils.cost(id) <= 3, id + " costs 1-3")


func test_forge_timing_bar() -> void:
	check_eq(Forge.grade(0.5), "perfect", "centre")
	check_eq(Forge.grade(0.62), "good", "near")
	check_eq(Forge.grade(0.95), "miss", "far")


func test_forge_tiers_and_sunfang() -> void:
	check_eq(Forge.sword_damage(), 2, "start: 2")
	check(Forge.problem() != "", "no ore: can't")
	Vitals.give("sun_ore", 20)
	Game.gold = 500
	check_eq(Forge.forge([0.5, 0.5, 0.99]), "cooled", "a Miss cools the metal")
	check_eq(Vitals.count("sun_ore"), 20, "nothing spent")
	check_eq(Forge.forge([0.5, 0.5, 0.5]), "perfect", "3 Perfect strikes")
	check_eq(Forge.sword_damage(), 3, "tier 1: 3")
	check(is_equal_approx(Forge.crit_chance(), 0.05), "+5% crit")
	check_eq(Vitals.count("sun_ore"), 18, "2 ore spent")
	check_eq(Game.gold, 470, "30 gold spent")
	Forge.forge([0.6, 0.5, 0.5])
	Forge.forge([0.6, 0.5, 0.5])
	check_eq(Forge.sword_damage(), 5, "tier 3: 5")
	check(is_equal_approx(Forge.crit_chance(), 0.05), "Good strikes add no crit")
	check_eq(Forge.forge([0.5, 0.5, 0.5]), "can't", "Sunfang needs 7 stones")
	for s in Game.STONES:
		Game.take_stone(s)
	check_eq(Forge.forge([0.5, 0.52, 0.5]), "perfect", "forge Sunfang")
	check_eq(Forge.blade_name(), "Sunfang", "named")
	check_eq(Forge.sword_damage(), 7, "Sunfang: 7")
	check_eq(Forge.forge([0.5, 0.5, 0.5]), "can't", "the last tier")


func test_shop() -> void:
	check(Shop.buy_problem("tamsin", "arrows") == "Not enough gold.", "no gold")
	Game.gold = 200
	check(Shop.buy("tamsin", "arrows"), "buy arrows")
	check_eq(Vitals.count("arrows"), 5, "+5 arrows")
	check_eq(Shop.stock("tamsin", "arrows"), -1, "arrows never run out")
	check(Shop.buy("tamsin", "shard"), "buy a heart shard")
	check_eq(Shop.buy_problem("tamsin", "shard"), "Sold out.", "only 1")
	check(Shop.buy("tamsin", "fortune"), "buy a sigil")
	check(Sigils.owned().has("fortune"), "you own it")
	check_eq(Shop.buy_problem("tamsin", "swiftfoot"), "Not for sale here.", "Tamsin doesn't sell it")
	check_eq(Game.gold, 200 - 6 - 60 - 80, "gold spent")
	check(Shop.buy("tamsin", "sun_ore") and Shop.sell("sun_ore"), "buy and sell ore")
	check(not Shop.sell("sun_ore"), "none left to sell")
	check(not Shop.sell("sword"), "the sword is never sold or mended")
	check_eq(Shop.start_gold(), 10, "start gold")
