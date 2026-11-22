class_name CaveMonster
extends CharacterBody2D
## A cave monster (docs/teen/gameplay/README.md section 6). HP is in sword hits. Every attack has a
## telegraph. z Zombie, k Skeleton, c Ember Skull, x Spider.

const T := 32.0
const KINDS := {
	#        hp  size (px)          colour
	"z": [3, Vector2(22, 30), Color("6b8a5a")],    # Zombie: slow walk, arms up 30 f, grab lunge
	"k": [2, Vector2(20, 30), Color("d8d0c0")],    # Skeleton: keeps 4-7 tiles off, bow glow 1.2 s, arrow
	"c": [1, Vector2(20, 20), Color("e0753a")],    # Ember Skull: floats in, flares 1.5 s, blast 2.2 tiles
	"x": [2, Vector2(24, 16), Color("4a3658")],    # Spider: rear-up 24 f, drops on a thread
}
const SEE := 9.0 * T                             # how far they notice you
const ZOMBIE_WALK := 1.5 * T
const ZOMBIE_LUNGE := 7.0 * T
const ZOMBIE_TELL := 30
const SKELETON_WALK := 2.0 * T
const SKELETON_TELL := 72                        # 1.2 s bow glow
const SKELETON_RELOAD := 132                     # an arrow every 2.2 s
const ARROW_SPEED := 9.0 * T
const SKULL_FLOAT := 2.2 * T
const SKULL_FLARE := 90                          # 1.5 s
const SKULL_BLAST := 2.2 * T
const SPIDER_TELL := 24
const SPIDER_DROP := 14.0 * T
const KNOCKBACK := 1.5 * T                       # pushed this far when hit (over 6 frames)
const GRAVITY := 1507.0

var kind := "z"
var hp := 1
var size := Vector2(20, 20)
var color := Color.WHITE
var cave                                          # CaveScene
var home := Vector2.ZERO
var tell := 0                                     # frames left in the telegraph
var cool := 0
var act := 0                                      # frames left of the attack itself
var flash := 0
var knock := 0.0
var dropping := false
var sprite: AnimatedSprite2D


func setup(letter: String, at: Vector2, c) -> void:
	kind = letter
	hp = KINDS[kind][0]
	size = KINDS[kind][1]
	color = KINDS[kind][2]
	cave = c
	position = at
	home = at
	collision_layer = 4
	collision_mask = 1
	var shape := CollisionShape2D.new()
	var r := RectangleShape2D.new()
	r.size = size
	shape.shape = r
	add_child(shape)
	var sheet: String = CaveArt.MONSTER[kind]
	sprite = AnimatedSprite2D.new()
	sprite.sprite_frames = ArtSheet.frames(sheet)
	sprite.offset = ArtSheet.offset(sheet)
	sprite.position = Vector2(0, size.y / 2.0)       # feet on the bottom of the box
	add_child(sprite)
	sprite.play("move")
	if kind == "x":                               # a spider hangs from the roof above its letter
		position = c.roof_above(at) + Vector2(0, size.y / 2.0)
		home = position


func rect() -> Rect2:
	return Rect2(position - size / 2.0, size)


func flying() -> bool:
	return kind == "c" or (kind == "x" and not dropping)


func _physics_process(dt: float) -> void:
	if cave == null or cave.hero == null:
		return
	flash = maxi(0, flash - 1)
	cool = maxi(0, cool - 1)
	var h: Node2D = cave.hero
	var to := h.position - position
	var side := 1.0 if to.x > 0 else -1.0
	match kind:
		"z":
			_zombie(to, side)
		"k":
			_skeleton(to, side)
		"c":
			_skull(to)
		"x":
			_spider(to)
	if knock != 0.0:
		velocity.x = knock
		knock = move_toward(knock, 0.0, KNOCKBACK * 10.0 / 6.0)
	if not flying():
		velocity.y = minf(velocity.y + GRAVITY * dt, 640.0)
	move_and_slide()
	_animate(side)
	queue_redraw()


## Hurt flash (white), the telegraph (attack pose, pulsing red), else moving; faces the Hero.
func _animate(side: float) -> void:
	sprite.flip_h = side < 0.0
	var anim := "hurt" if flash > 0 else ("attack" if tell > 0 or act > 0 else "move")
	if sprite.animation != anim:
		sprite.play(anim)
	if flash > 0:
		sprite.modulate = Color(4, 4, 4)
	elif tell > 0:
		sprite.modulate = Color.WHITE.lerp(Color(2.0, 0.5, 0.5), 0.8 if (tell / 4) % 2 == 0 else 0.3)
	else:
		sprite.modulate = Color.WHITE


func _zombie(to: Vector2, side: float) -> void:
	if act > 0:
		act -= 1
		velocity.x = side * ZOMBIE_LUNGE if act > 0 else 0.0
		return
	if tell > 0:
		tell -= 1
		velocity.x = 0.0
		if tell == 0:
			act = 12
		return
	if to.length() > SEE:
		velocity.x = 0.0
	elif absf(to.x) < 2.0 * T and absf(to.y) < T and cool == 0:
		tell = ZOMBIE_TELL
		cool = 90
	else:
		velocity.x = side * ZOMBIE_WALK


func _skeleton(to: Vector2, side: float) -> void:
	velocity.x = 0.0
	if to.length() > SEE:
		return
	var d := absf(to.x)
	if d < 4.0 * T:
		velocity.x = -side * SKELETON_WALK
	elif d > 7.0 * T:
		velocity.x = side * SKELETON_WALK
	if is_on_floor() and velocity.x != 0.0 and not cave.ground_ahead(self, signf(velocity.x)):
		velocity.x = 0.0
	if tell > 0:
		tell -= 1
		if tell == 0:
			cave.shoot(position, Vector2(side * ARROW_SPEED, 0), self)
			cool = SKELETON_RELOAD - SKELETON_TELL
	elif cool == 0 and absf(to.y) < 3.0 * T:
		tell = SKELETON_TELL


func _skull(to: Vector2) -> void:
	if tell > 0:
		velocity = Vector2.ZERO
		tell -= 1
		if tell == 0:
			if to.length() < SKULL_BLAST:
				cave.hurt_hero(position, 1)
			cool = 120
		return
	if to.length() > SEE or cool > 0:
		velocity = velocity.move_toward((home - position).limit_length(SKULL_FLOAT * 0.5), 8.0)
	elif to.length() < 1.8 * T:
		tell = SKULL_FLARE
	else:
		velocity = to.normalized() * SKULL_FLOAT


func _spider(to: Vector2) -> void:
	if dropping:
		if is_on_floor():
			act += 1
			if act > 90:                                # climb back up its thread
				dropping = false
				act = 0
		return
	velocity = (home - position) * 6.0                  # back up the thread to its spot
	if tell > 0:
		tell -= 1
		if tell == 0:
			dropping = true
			act = 0
			velocity = Vector2(0, SPIDER_DROP)
	elif to.y > 0 and absf(to.x) < 1.5 * T and to.y < 10.0 * T and cool == 0:
		tell = SPIDER_TELL
		cool = 150


## Hit by the sword (or a reflected arrow: 1). Returns true if it died.
func hit(from: Vector2, damage := 1) -> bool:
	hp -= damage
	flash = 4
	if sprite:                                        # show it now: the hit-stop holds this frame
		sprite.modulate = Color(4, 4, 4)
		sprite.play("hurt")
	knock = (1.0 if position.x > from.x else -1.0) * KNOCKBACK * 10.0     # 1.5 tiles over 6 frames
	if kind == "c":
		tell = 0                                      # a hit skull doesn't blow up
	if hp <= 0:
		queue_free()
		return true
	return false


func _draw() -> void:
	if kind == "x":                                  # the spider's thread
		draw_line(Vector2(0, home.y - position.y - size.y / 2.0), Vector2(0, -size.y / 2.0), Color(1, 1, 1, 0.4), 1.0)
	if kind == "c" and tell > 0:                     # how far the Ember Skull's blast will reach
		draw_arc(Vector2.ZERO, SKULL_BLAST * (1.0 - tell / float(SKULL_FLARE)), 0, TAU, 32, Color(1, 0.6, 0.2, 0.5), 2.0)


## A skeleton's arrow. R reflects it: then it flies back and hurts monsters.
class Arrow extends Node2D:
	var velocity := Vector2.ZERO
	var cave
	var reflected := false
	var life := 300

	func _physics_process(dt: float) -> void:
		position += velocity * dt
		life -= 1
		if life <= 0 or CaveTiles.is_solid(cave.letter_at(position)):
			queue_free()
			return
		cave.arrow_moved(self)
		queue_redraw()

	func rect() -> Rect2:
		return Rect2(position - Vector2(8, 2), Vector2(16, 4))

	func _draw() -> void:
		draw_line(Vector2(-8, 0), Vector2(8, 0), Color("f7c64a") if reflected else Color("d8d0c0"), 2.0)
