class_name Juice
## Game feel shared by the realm and the throne room (docs/teen/gameplay §4): screen shake that
## fades out (off when the player turns it off in the settings) and one-shot bursts of motes.

## How much to shake: 0 when the player switched screen shake off.
static func shake_scale() -> float:
	return 1.0 if UiSettings.screen_shake else 0.0


## A shake that fades out. add(px, frames); step(dt) gives the camera offset this frame.
class Shake:
	var px := 0.0
	var t := 0.0
	var length := 0.0

	func add(p: float, frames: int) -> void:
		if p >= px * now():                     # a bigger shake wins; a small one never cuts a big one short
			px = p
			t = frames / 60.0
			length = t

	func now() -> float:
		return t / length if length > 0.0 else 0.0

	func step(dt: float) -> Vector2:
		t = maxf(0.0, t - dt)
		return Vector2(randf_range(-1, 1), randf_range(-1, 1)) * px * now() * Juice.shake_scale()


## n square motes fly out of `at` and fade; the node frees itself when they are gone.
static func burst(parent: Node, at: Vector2, color: Color, n: int, speed := 80.0, life := 0.5,
		size := 2.0, gravity := 0.0) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.position = at
	p.one_shot = true
	p.explosiveness = 1.0
	p.amount = n
	p.lifetime = life
	p.spread = 180.0
	p.initial_velocity_min = speed * 0.4
	p.initial_velocity_max = speed
	p.damping_min = speed * 0.8
	p.damping_max = speed * 1.6
	p.gravity = Vector2(0, gravity)
	p.scale_amount_min = size
	p.scale_amount_max = size
	var fade := Gradient.new()
	fade.set_color(0, color)
	fade.set_color(1, Color(color, 0.0))
	p.color_ramp = fade
	p.z_index = 10
	parent.add_child(p)
	p.emitting = true
	p.finished.connect(p.queue_free)
	return p
