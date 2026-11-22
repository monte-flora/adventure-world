class_name MapMonster
extends Node2D
## A monster on the map: roams near where it was born, chases the hero when it sees them, gives up
## when they get away (as phase2/monsters.py), and hurts on touch. HP in sword hits at forge tier 1
## (docs/teen/gameplay §6). Art: art/sheets/monster_<kind>. B1 owns this file.

const TILE := LevelFile.TILE
const KINDS := {
	# hp (in damage points, sword = 2), speed (squares/s), sees (squares); the sheet is monster_<kind>
	"thornling": {"hp": 2, "speed": 2.5, "sees": 5.0},
	"barrow_wight": {"hp": 6, "speed": 1.8, "sees": 6.0},
	"mere_lurker": {"hp": 4, "speed": 2.2, "sees": 5.0},
	"frost_wolf": {"hp": 4, "speed": 3.4, "sees": 7.0},
	"ash_scarab": {"hp": 4, "speed": 2.6, "sees": 5.0},
	"bog_wisp": {"hp": 2, "speed": 3.0, "sees": 6.0},
	"umbral_hound": {"hp": 8, "speed": 3.0, "sees": 7.0},     # the Umbral Reach (Nightfall)
}
## Who haunts each land (levels/realm ids); the rest get thornlings.
const OF_LAND := {
	"emberhold": ["thornling"], "weepingwold": ["thornling", "bog_wisp"],
	"hollowcrown": ["barrow_wight", "thornling"], "drowned_mere": ["mere_lurker"],
	"wintermarch": ["frost_wolf"], "cinder_wastes": ["ash_scarab"], "mirefen": ["bog_wisp", "mere_lurker"],
	"shadowgate": ["umbral_hound"], "umbral_reach": ["umbral_hound"],
}
const GIVE_UP := 9.0                         # squares
const TOUCH := 20.0                          # px
const ROAM := 3                              # squares from home

signal died(monster: MapMonster)

var world: WorldMap
var hero: HeroTop
var kind := "thornling"
var sprite: AnimatedSprite2D
var hp := 2
var born := Vector2i.ZERO
var chasing := false
var target := Vector2.ZERO
var flash := 0
var knock := Vector2.ZERO
var rng := RandomNumberGenerator.new()


func setup(w: WorldMap, h: HeroTop, k: String, at_cell: Vector2i, seed_value: int) -> void:
	world = w
	hero = h
	kind = k
	hp = KINDS[k].hp
	born = at_cell
	position = Vector2(at_cell) * TILE + Vector2.ONE * TILE / 2.0
	target = position
	rng.seed = seed_value
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = ArtSheet.frames("monster_" + k)
	sprite.offset = ArtSheet.offset("monster_" + k)
	sprite.position = Vector2(0, ArtSheet.cell("monster_" + k).y * 0.3)
	add_child(sprite)
	sprite.play("move")


## The kind for the i-th monster of a land.
static func kind_for(land_id: String, i: int) -> String:
	var list: Array = OF_LAND.get(WorldMap.realm_id(land_id), ["thornling"])
	return list[i % list.size()]


func _physics_process(dt: float) -> void:
	flash = maxi(0, flash - 1)
	var k: Dictionary = KINDS[kind]
	var to_hero := hero.position - position
	var dist := to_hero.length() / TILE
	chasing = dist <= k.sees or (chasing and dist <= GIVE_UP)
	if chasing:
		target = hero.position
	elif position.distance_to(target) < 4.0 or rng.randf() < 0.005:
		var c := born + Vector2i(rng.randi_range(-ROAM, ROAM), rng.randi_range(-ROAM, ROAM))
		target = Vector2(c) * TILE + Vector2.ONE * TILE / 2.0 if world.walkable(c) else position
	var step: Vector2 = position.direction_to(target) * k.speed * TILE * dt + knock * dt
	knock = knock.move_toward(Vector2.ZERO, 900.0 * dt)
	var next: Vector2 = position + step
	if world.walkable(Vector2i(floor(next.x / TILE), floor(next.y / TILE))):
		position = next
	if to_hero.length() < TOUCH:
		hero.take_hit(position)
	if absf(step.x) > 0.05:
		sprite.flip_h = step.x < 0.0
	var anim := "hurt" if flash > 0 else ("attack" if chasing and dist < 1.5 else "move")
	if sprite.animation != anim:
		sprite.play(anim)
	sprite.modulate = Color(4, 4, 4) if flash > 8 else Color.WHITE


## A sword hit. Returns true if this killed it.
func hit(damage: int, from: Vector2) -> bool:
	if flash > 0:
		return false
	hp -= damage
	flash = 12
	knock = (position - from).normalized() * 1.5 * TILE / (6.0 / 60.0)
	if hp <= 0:
		died.emit(self)
		queue_free()
		return true
	return false
