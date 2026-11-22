extends TestCase
## Names: every stone, ability and land has a display name.


func test_every_stone_and_ability_has_a_name() -> void:
	for s in Game.STONES:
		check(Names.STONE.has(s), "stone " + s)
		check(Names.ABILITY.has(Game.ABILITY_OF[s]), "ability " + Game.ABILITY_OF[s])
	check_eq(Names.stone("dawn"), "Dawnstone", "dawn")
	check_eq(Names.ability("double_jump"), "Stormwing", "double jump")
	check_eq(Names.HOME, "Emberhold", "home")
	check_eq(Names.land("nightfall"), "the Umbral Reach", "Nightfall's place")
	check_eq(Names.land_named("Murk Swamp"), "the Mirefen", "old world-file name")
	check_eq(Names.land_named("woods"), "the Weepingwold", "id")
