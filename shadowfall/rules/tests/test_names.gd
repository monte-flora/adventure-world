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


func test_realms_boss_and_lieutenants_have_names() -> void:
	for id in WorldMap.REALM_ID:
		check_eq(Names.land(WorldMap.REALM_ID[id]), Names.land(id), "realm id " + WorldMap.REALM_ID[id])
	for id in ThroneFight.LIEUTENANTS:
		check(Names.LIEUTENANT.has(id), "lieutenant " + id)
	check(Names.SUNFANG != "" and Names.BOSS != "", "boss and blade")
