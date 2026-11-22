class_name Person
extends Node2D
## One person from rules/data/people.json standing in the realm (top-down, art/sheets/people_<look>).
## 'move': idle stands and breathes; pace walks a few squares to and fro, waiting at each end. A person
## stops while the hero is close, and turns to face the hero to talk. B1 owns this folder.

const TILE := LevelFile.TILE
const PACE := 2                             # squares each way from home
const SPEED := 1.2 * TILE                   # px/s, an unhurried walk
const WAIT := 1.5                           # s at each end of a pace
const NEAR := 1.6 * TILE                    # the hero this close: stand still

var id := ""
var data: Dictionary = {}
var cell := Vector2i.ZERO                   # home square on the realm map
var facing := Vector2.DOWN
var hero: Node2D
var sprite: AnimatedSprite2D
var _span := Vector2.ZERO                   # pace: min and max x (px)
var _dir := 1.0
var _wait := 0.0


func setup(person: Dictionary, at: Vector2i, world: WorldMap) -> void:
	data = person
	id = person.get("id", "")
	cell = at
	position = Vector2(at) * TILE + Vector2.ONE * TILE / 2.0
	_span = Vector2(position.x, position.x)
	if person.get("move", "idle") == "pace":
		for side in [-1, 1]:
			for k in range(1, PACE + 1):
				var q := at + Vector2i(side * k, 0)
				if not world.walkable(q) or world.at(q) in "MSPL":
					break
				if side < 0:
					_span.x = position.x - k * TILE
				else:
					_span.y = position.x + k * TILE
	_wait = fmod(float(at.x * 7 + at.y * 3) / 10.0, WAIT)     # so pacers don't move in step
	var sheet := "people_" + str(person.get("look", "peasant"))
	if ArtSheet.meta(sheet).is_empty():
		sheet = "people_peasant"
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = ArtSheet.frames(sheet)
	sprite.offset = ArtSheet.offset(sheet)
	sprite.position = Vector2(0, 12)        # feet on the bottom of the square, like the hero
	add_child(sprite)
	sprite.play("idle_down")


func paces() -> bool:
	return _span.x < _span.y


## Turns to look at `at` (the hero) and stands still.
func face(at: Vector2) -> void:
	var d := at - position
	if d != Vector2.ZERO:
		facing = Vector2(signf(d.x), 0) if absf(d.x) > absf(d.y) else Vector2(0, signf(d.y))
	_animate(false)


func _physics_process(dt: float) -> void:
	if not paces() or (hero != null and hero.position.distance_to(position) < NEAR):
		_animate(false)
		return
	if _wait > 0.0:
		_wait -= dt
		_animate(false)
		return
	var goal := _span.y if _dir > 0 else _span.x
	position.x = move_toward(position.x, goal, SPEED * dt)
	facing = Vector2(_dir, 0)
	if is_equal_approx(position.x, goal):
		_dir = -_dir
		_wait = WAIT
	_animate(true)


func _animate(walking: bool) -> void:
	var dir := "_side" if absf(facing.x) > absf(facing.y) else ("_up" if facing.y < 0 else "_down")
	var anim := ("walk" if walking else "idle") + dir
	if sprite.animation != anim:
		sprite.play(anim)
	sprite.flip_h = facing.x < 0 and dir == "_side"
