extends RefCounted
## The music, as text: every tune is original and you can rewrite it here. Owned by B6.
## Each tune has 2 stems of the same length that loop together: "base" (always on) and "dark"
## (fades in as the gloom rises, see Audio). Steps are eighth notes, 8 per bar.
##
## The two leitmotifs (docs/teen/audio/README.md):
##   Shadowfall (the land, the hero):  A3 C4 E4 D4 | B3     rises, ends unresolved
##   The Shadow King:                  A3 G#3 F3 D#3 | E3   same rhythm, falls, tritone A-D#

const Synth := preload("res://audio/synth.gd")
const STEPS_PER_BAR := 8

## tune id -> beats per minute. Every tune here has base + dark.
const TUNES := {"overworld": 96, "cave": 70, "boss": 140}


static func step_of(tune: String) -> float:
	return 60.0 / TUNES[tune] / 2.0


## Makes one tune: {"base": samples, "dark": samples, "bars": n}.
static func make(tune: String) -> Dictionary:
	match tune:
		"overworld":
			return _overworld()
		"cave":
			return _cave()
		"boss":
			return _boss()
	push_error("no such tune: " + tune)
	return {}


## The map under a darkening sky. The dark stem: a drone a tritone under the key, and a far bell
## playing the Shadow King's motif. Alone it is just unease.
static func _overworld() -> Dictionary:
	var step := step_of("overworld")
	var melody := ("A4 - C5 - E5 - D5 C5 | B4 - - - G4 - - - | A4 - C5 - E5 - G5 - | F5 - E5 - D5 - - - |"
		+ "C5 - D5 - E5 - A5 - | G5 - F5 - E5 - C5 - | D5 - C5 - B4 - G#4 - | A4 - - - . . . . |")
	var harmony := ("E4 - - - A4 - - - | G4 - - - D4 - - - | E4 - - - C5 - - - | A4 - - - F4 - - - |"
		+ "A4 - - - C5 - - - | C5 - - - G4 - - - | F4 - - - E4 - - - | E4 - - - . . . . |")
	var bass := "A2 . A3 . A2 . E3 . | G2 . G3 . G2 . D3 . | F2 . F3 . F2 . C3 . | D2 . D3 . E2 . E3 . |".repeat(2)
	var beat := "k . h . s . h h | k . h k s . h . |".repeat(4)
	var n := Synth.length_of(melody, step)
	var base := Synth.mix([
		Synth.voice(melody, step, "pulse", 0.22, n, 0.25, [0.005, 0.08, 0.7, 0.03], 0.004),
		Synth.voice(harmony, step, "pulse", 0.10, n, 0.125, [0.02, 0.2, 0.5, 0.1]),
		Synth.voice(bass, step, "triangle", 0.45, n, 0.5, [0.002, 0.05, 0.8, 0.02]),
		Synth.drums(beat, step, 0.30, n),
	])
	base = Synth.echo(base, step * 3, 0.25, 0.25)
	var drone := "A1 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |".repeat(2)
	var bell := (". . . . . . . . A5 - G#5 - F5 - D#5 - | E5 - - - - - - - . . . . . . . . |"
		+ ". . . . . . . . . . . . . . . . | . . . . . . . . D#5 - - - E5 - - - |")
	var wind := ". . . . . . . . . . . . . . . . | c - - - - - - - . . . . . . . . |".repeat(2)
	var dark := Synth.mix([
		Synth.voice(drone, step, "pulse", 0.25, n, 0.5, [0.6, 0.5, 0.8, 0.6]),
		Synth.voice(bell, step, "sine", 0.30, n, 0.5, [0.003, 0.6, 0.0, 0.05]),
		Synth.drums(wind, step, 0.25, n),
	])
	dark = Synth.echo(Synth.lowpass(dark, 900.0), step * 4, 0.45, 0.5)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## Caves: ambient first. A slow pad, the Shadowfall motif low on a soft triangle, water drips, a
## heartbeat thud, a long echo. The dark stem: the heartbeat doubles, a tritone drone, the King's
## motif far below.
static func _cave() -> Dictionary:
	var step := step_of("cave")
	var pad := ("A2 - - - - - - - - - - - - - - - | F2 - - - - - - - - - - - - - - - |"
		+ "D2 - - - - - - - - - - - - - - - | E2 - - - - - - - - - - - - - - - |")
	var motif := (". . . . A3 - C4 - E4 - - - D4 - - - | B3 - - - - - - - . . . . . . . . |"
		+ ". . . . . . . . . . . . . . . . | . . . . G#3 - - - - - - - A3 - - - |")
	var drip := (". . . . . . . . . . . E6 . . . . | . . . . . . . . . . . . . . B5 . |"
		+ ". . . . . . A6 . . . . . . . . . | . . . . . . . . . . . . . . . . |")
	var beat := "k . . . . . . . k . . . . . . . |".repeat(4)
	var n := Synth.length_of(pad, step)
	var base := Synth.mix([
		Synth.voice(pad, step, "pulse", 0.20, n, 0.125, [0.8, 0.5, 0.7, 0.8]),
		Synth.voice(motif, step, "triangle", 0.45, n, 0.5, [0.05, 0.3, 0.6, 0.2], 0.006),
		Synth.voice(drip, step, "sine", 0.25, n, 0.5, [0.001, 0.25, 0.0, 0.01]),
		Synth.drums(beat, step, 0.35, n),
	])
	base = Synth.echo(Synth.lowpass(base, 2200.0), 0.37, 0.5, 0.45)
	var drone := "A1 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |".repeat(2)
	var king := (". . . . . . . . . . . . . . . . | A2 - - - G#2 - - - F2 - - - D#2 - - - |"
		+ "E2 - - - - - - - - - - - - - - - | . . . . . . . . . . . . . . . . |")
	var pulse := "k . . . k . . . . . . . . . . . |".repeat(4)
	var dark := Synth.mix([
		Synth.voice(drone, step, "pulse", 0.22, n, 0.5, [1.0, 0.5, 0.8, 1.0]),
		Synth.voice(king, step, "triangle", 0.5, n, 0.5, [0.1, 0.4, 0.7, 0.4]),
		Synth.drums(pulse, step, 0.45, n, 11),
	])
	dark = Synth.echo(Synth.lowpass(dark, 700.0), 0.37, 0.55, 0.5)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## The Shadow King: intense but sad. A driving ostinato under his falling motif, answered by the
## Shadowfall motif. The dark stem (phase 2 of the fight, or deep gloom): a shrieking tritone
## arpeggio and crashes.
static func _boss() -> Dictionary:
	var step := step_of("boss")
	var melody := ("A4 - G#4 - F4 - D#4 - | E4 - - - - - - - | A4 - C5 - E5 - D5 - | B4 - - - - - - - |"
		+ "A5 - G#5 - F5 - D#5 - | E5 - - - D5 - C5 - | B4 - C5 - D5 - D#5 - | E5 - - - . . . . |")
	var bass := ("A2 A2 A3 A2 D#3 A2 G#2 A2 |".repeat(4)
		+ "F2 F2 F3 F2 B2 F2 E2 F2 | E2 E2 E3 E2 A#2 E2 D#2 E2 |".repeat(2))
	var low := "A1 - - - - - - - | E1 - - - - - - - |".repeat(4)
	var beat := "k h s h k k s h |".repeat(7) + "k s s s s s c . |"
	var n := Synth.length_of(melody, step)
	var base := Synth.mix([
		Synth.voice(melody, step, "pulse", 0.22, n, 0.25, [0.005, 0.1, 0.75, 0.04], 0.008),
		Synth.voice(bass, step, "pulse", 0.14, n, 0.5, [0.002, 0.05, 0.6, 0.02]),
		Synth.voice(low, step, "triangle", 0.45, n, 0.5, [0.01, 0.2, 0.8, 0.1]),
		Synth.drums(beat, step, 0.32, n, 3),
	])
	base = Synth.echo(base, step * 3, 0.2, 0.2)
	var arp := "A5 D#6 A6 D#6 ".repeat(8) + "F5 B5 F6 B5 ".repeat(4) + "E5 A#5 E6 A#5 ".repeat(4)
	var crash := "c . . . . . . . | . . . . . . . . |".repeat(4)
	var dark := Synth.mix([
		Synth.voice(arp, step, "pulse", 0.14, n, 0.125, [0.002, 0.04, 0.5, 0.02]),
		Synth.drums(crash, step, 0.35, n, 5),
	])
	dark = Synth.echo(Synth.lowpass(dark, 3000.0), step * 3, 0.4, 0.4)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## The Shadow King's motif as a short sting (boss intro; he appears on the map). Not a loop.
static func king_sting() -> PackedFloat32Array:
	var step := 60.0 / 80.0 / 2.0
	var top := "A4 - G#4 - F4 - D#4 - | E4 - - - - - - - | . . . . . . . ."
	var low := "A2 - G#2 - F2 - D#2 - | E2 - - - - - - - | . . . . . . . ."
	var hit := "c . . . . . . . | k . . . . . . . | . . . . . . . ."
	var n := Synth.length_of(top, step)
	var sting := Synth.mix([
		Synth.voice(top, step, "pulse", 0.25, n, 0.25, [0.01, 0.2, 0.7, 0.4], 0.01),
		Synth.voice(low, step, "pulse", 0.25, n, 0.5, [0.01, 0.2, 0.8, 0.4]),
		Synth.voice(low.replace("2", "1"), step, "triangle", 0.5, n),
		Synth.drums(hit, step, 0.4, n),
	])
	return Synth.normalise(Synth.echo(sting, 0.3, 0.4, 0.4, false))
