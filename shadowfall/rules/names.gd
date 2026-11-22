class_name Names
## The names players see, by id. The one place for display names: code keeps ids, screens read here.
## Decided by main 2026-11-21 (user may still rename). B4 (rules/) owns this folder.

const STONE := {
	"dawn": "Dawnstone", "leaf": "Thornheart", "crown": "Crown of Ash", "tide": "Drowned Pearl",
	"frost": "Wintermark", "sun": "Sunforge Ember", "moon": "Ravenmoon",
}
const ABILITY := {
	"dash": "Wraithstep", "climb": "Ironclaw", "pound": "Kingsfall", "swim": "Tidebinder",
	"double_jump": "Stormwing", "flare": "Dawnbrand", "truesight": "Veilsight",
}
## Lands by id (the old pygame land ids). Home is Emberhold; Nightfall's place is the Umbral Reach.
const LAND := {
	"home": "Emberhold", "woods": "the Weepingwold", "ruins": "Hollowcrown", "lake": "the Drowned Mere",
	"frost": "the Wintermarch", "desert": "the Cinder Wastes", "swamp": "the Mirefen",
	"portal": "the Shadowgate", "nightfall": "the Umbral Reach",
	# the same lands by their realm ids (overworld/world_map.gd REALM_ID, MapMonster.OF_LAND)
	"emberhold": "Emberhold", "weepingwold": "the Weepingwold", "hollowcrown": "Hollowcrown",
	"drowned_mere": "the Drowned Mere", "wintermarch": "the Wintermarch", "cinder_wastes": "the Cinder Wastes",
	"mirefen": "the Mirefen", "shadowgate": "the Shadowgate", "umbral_reach": "the Umbral Reach",
}
## The name a world file still has (levels/world/*.txt `name:`) -> land id, until B-L renames them.
const LAND_OF_OLD_NAME := {
	"Home Meadow": "home", "Hearthvale": "home", "Whispering Woods": "woods", "Old Ruins": "ruins",
	"The Great Lake": "lake", "Great Lake": "lake", "Frost Peaks": "frost", "Sunscorch Desert": "desert",
	"Murk Swamp": "swamp", "Portal Island": "portal", "Nightfall Hollow": "nightfall",
}
const HOME := "Emberhold"
const NIGHTFALL_PLACE := "the Umbral Reach"
const NIGHTFALL_EVENT := "Nightfall"
const BOSS := "the Shadow King"
## The blade the 7 Light Stones forge at the castle gate.
const SUNFANG := "Sunfang"
## The Shadow King's 7 lieutenants (one guards each Stone); he calls their echoes in the Eclipse.
const LIEUTENANT := {
	"thornwarden": "Vargoth the Thornwarden", "loom_widow": "Ysmera, the Loom Widow",
	"bellwarden": "Old Dunmoor, the Bellwarden", "rust_regent": "Kael Rustcrown, the Rust Regent",
	"rime_matriarch": "Skaldra, the Rime Matriarch", "glass_wyrm": "Sarkhaal, the Glass Wyrm",
	"mire_lantern": "Gloamwick, the Mire Lantern",
}
const GAME_TITLE := "Shadowfall"


static func stone(id: String) -> String:
	return STONE.get(id, id)


static func ability(id: String) -> String:
	return ABILITY.get(id, id)


static func land(id: String) -> String:
	return LAND.get(id, id)


## A land's display name from either its id or the old name in a world file.
static func land_named(old_or_id: String) -> String:
	return land(LAND_OF_OLD_NAME.get(old_or_id, old_or_id))
