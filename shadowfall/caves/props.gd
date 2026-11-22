class_name CaveProps
## The moving parts of a cave: platforms on P and U tracks, and swinging vines (R).

const T := LevelFile.TILE
const PLATFORM_SPEED := 2.5 * T                  # tiles a second


## A platform riding its track to one end and back (P: side to side, 2 wide; U: up and down).
class Platform extends AnimatableBody2D:
	var a := Vector2.ZERO                         # one end of the track (top-left of the platform)
	var b := Vector2.ZERO
	var size := Vector2.ZERO
	var t := 0.0
	var dir := 1.0
	var color := Color("a8703f")

	func setup(from: Vector2, to: Vector2, sz: Vector2, col: Color) -> void:
		a = from
		b = to
		size = sz
		color = col
		position = a
		sync_to_physics = true
		collision_layer = 1
		var shape := CollisionShape2D.new()
		var r := RectangleShape2D.new()
		r.size = size
		shape.shape = r
		shape.position = size / 2.0
		add_child(shape)

	func _physics_process(dt: float) -> void:
		var length := a.distance_to(b)
		if length < 1.0:
			return
		t += dir * CaveProps.PLATFORM_SPEED * dt / length
		if t >= 1.0 or t <= 0.0:
			t = clampf(t, 0.0, 1.0)
			dir = -dir
		position = a.lerp(b, t)

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), color)
		draw_rect(Rect2(Vector2.ZERO, Vector2(size.x, 3)), color.lightened(0.3))


## A swinging vine hanging from rock: grab it, LEFT and RIGHT pump the swing, jump lets go.
class Rope extends Node2D:
	const GRAVITY := 1507.0                       # the Hero's own gravity, so swings feel the same
	const PUMP := 3.5                             # radians/s² from LEFT and RIGHT
	const DAMP := 0.15
	var length := 64.0
	var angle := 0.0
	var spin := 0.0                               # radians a second
	var hero: Node2D = null
	var grip := 64.0                              # how far down the vine the Hero holds on

	func setup(pivot: Vector2, len_px: float) -> void:
		position = pivot
		length = len_px

	## Is this point on the vine?
	func touches(p: Vector2) -> bool:
		var local := (p - position).rotated(-angle)
		return absf(local.x) < 12.0 and local.y > 8.0 and local.y < length + 8.0

	func grab(h: Node2D) -> void:
		hero = h
		grip = clampf((h.position - position).length(), 24.0, length)
		spin = h.velocity.x / grip * 0.5
		h.velocity = Vector2.ZERO

	func pump(dir: float) -> void:
		if absf(dir) > 0.1:
			spin += dir * PUMP * get_physics_process_delta_time()

	func release() -> Vector2:
		var v := Vector2(cos(angle), -sin(angle)) * spin * grip
		hero = null
		return Vector2(v.x, minf(v.y, 0.0) * 1.0)

	func _physics_process(dt: float) -> void:
		spin += -(GRAVITY / maxf(grip, 24.0)) * sin(angle) * dt * (1.0 if hero else 0.6)
		spin *= 1.0 - DAMP * dt
		angle = clampf(angle + spin * dt, -1.3, 1.3)
		if hero and is_instance_valid(hero):
			hero.position = position + Vector2(sin(angle), cos(angle)) * grip
			hero.velocity = Vector2.ZERO
		queue_redraw()

	func _draw() -> void:
		var tip := Vector2(sin(angle), cos(angle)) * length
		draw_line(Vector2.ZERO, tip, Color("5d7a3a"), 3.0)
		for i in range(1, int(length / 16.0)):
			draw_circle(tip * (i * 16.0 / length), 3.0, Color("7fa35a"))
