class_name MapMonster
extends Node2D
## A monster on the map: roams near where it was born, chases the hero when it sees them, gives up
## when they get away (as phase2/monsters.py), and hurts on touch. HP in sword hits at forge tier 1
## (docs/teen/gameplay §6). Placeholder art. B1 owns this file.

const TILE := LevelFile.TILE
const KINDS := {
	# hp (in damage points, sword = 2), speed (squares/s), sees (squares), colour
	"slime": {"hp": 2, "speed": 2.5, "sees": 5.0, "color": "5fa35a"},
	"zombie": {"hp": 6, "speed": 1.8, "sees": 6.0, "color": "6f7f5a"},
	"shade": {"hp": 8, "speed": 3.0, "sees": 7.0, "color": "4a3a6e"},   # Nightfall
}
const GIVE_UP := 9.0                         # squares
const TOUCH := 20.0                          # px
const ROAM := 3                              # squares from home

signal died(monster: MapMonster)

var world: WorldMap
var hero: HeroTop
var kind := "slime"
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
	queue_redraw()


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


func _draw() -> void:
	var c := Color.WHITE if flash > 8 else Color(KINDS[kind].color)
	draw_circle(Vector2.ZERO, 10, c)
	draw_circle(Vector2(-4, -3), 2, Color("f0e6c8"))
	draw_circle(Vector2(4, -3), 2, Color("f0e6c8"))
