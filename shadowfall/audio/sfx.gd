extends RefCounted
## The sound effects, one recipe each, all made by audio/synth.gd. Owned by B6.
## Other areas play them with Audio.play_sfx("jump"). Add a name to NAMES and a branch in make().

const Synth := preload("res://audio/synth.gd")

const NAMES := ["swing", "hit", "hurt", "jump", "land", "dash", "pound", "stone", "coin",
	"checkpoint", "die", "menu", "select", "king"]


## A sound's samples, never louder than 0.9.
static func make(sound: String) -> PackedFloat32Array:
	var buf := _recipe(sound)
	return Synth.normalise(buf, 0.9) if Synth.peak(buf) > 0.9 else buf


static func _recipe(sound: String) -> PackedFloat32Array:
	match sound:
		"swing":  # the sword (R): a quick bright swish
			return Synth.sweep(1800, 300, 0.12, "pulse", 0.125, 0.6, 0.6, 0.55, 2)
		"hit":  # you hit a monster: a thud and a crunch
			return Synth.mix([Synth.sweep(220, 50, 0.14, "triangle", 0.5, 0.9),
				Synth.sweep(900, 200, 0.07, "pulse", 0.5, 0.5, 1.0, 0.8, 4)])
		"hurt":  # a monster hits you: low, falling, buzzy
			return Synth.sweep(330, 140, 0.25, "pulse", 0.5, 0.6, 0.5, 0.15, 5)
		"jump":
			return Synth.sweep(260, 620, 0.11, "pulse", 0.25, 0.6, 0.7)
		"land":
			return Synth.sweep(160, 60, 0.06, "triangle", 0.5, 0.8, 1.0, 0.2, 6)
		"dash":  # Wraithstep: a rushing breath of noise
			return Synth.sweep(600, 2400, 0.18, "pulse", 0.125, 0.5, 0.4, 0.85, 8)
		"pound":  # Kingsfall: a heavy slam, then grit
			return Synth.mix([Synth.sweep(120, 30, 0.35, "triangle", 0.5, 1.0, 0.6),
				Synth.sweep(500, 80, 0.25, "pulse", 0.5, 0.5, 1.0, 0.9, 9)])
		"stone":  # a Light Stone: the Shadowfall motif's first notes, two octaves up, with echo
			return _arp(["A5", "C6", "E6", "A6"], 0.07, 0.45, 0.5)
		"coin":
			return _arp(["E6", "B6"], 0.05, 0.4, 0.1)
		"checkpoint":  # a waystone wakes
			return _arp(["A4", "E5", "A5"], 0.09, 0.4, 0.4)
		"die":  # the motif falls apart
			return _arp(["E4", "D#4", "D4", "A3"], 0.14, 0.45, 0.4)
		"menu":
			return Synth.sweep(880, 880, 0.04, "pulse", 0.25, 0.35)
		"select":
			return _arp(["A5", "E6"], 0.05, 0.35, 0.0)
		"king":  # the Shadow King's motif (boss intro, or he appears on the map)
			return preload("res://audio/tunes.gd").king_sting()
	push_error("no such sound: " + sound)
	return PackedFloat32Array()


## Notes one after another, then an echo tail of `tail` seconds.
static func _arp(notes: Array, each: float, vol: float, tail: float) -> PackedFloat32Array:
	var parts := []
	for note in notes:
		var f := Synth.freq(note)
		parts.append(Synth.sweep(f, f, each, "pulse", 0.25, vol))
	parts.append(Synth.silence(tail))
	return Synth.echo(Synth.join(parts), 0.09, 0.45, 0.4, false)
