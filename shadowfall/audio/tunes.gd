extends RefCounted
## The music, as text: every tune is original and you can rewrite it here. Owned by B6.
## Each tune has 2 stems of the same length that loop together: "base" (always on) and "dark"
## (fades in as the gloom rises, see Audio). Steps are sixteenth notes, 16 per bar, so a line can
## mix held notes, dotted rhythms, syncopation, rests and 16th fills (4 steps = 1 beat).
##
## The two leitmotifs (docs/teen/audio/README.md):
##   Shadowfall (the land, the hero):  A3 C4 E4 D4 | B3     rises, ends unresolved
##   The Shadow King:                  A3 G#3 F3 D#3 | E3   same rhythm, falls, tritone A-D#

const Synth := preload("res://audio/synth.gd")
const STEPS_PER_BAR := 16

## tune id -> beats per minute. Every tune here has base + dark.
## The Shadow King's fight has a tune per phase: "boss" (the Blade), "boss_eclipse", "boss_fall".
const TUNES := {"overworld": 96, "cave": 70, "boss": 140, "boss_eclipse": 140, "boss_fall": 140}


static func step_of(tune: String) -> float:
	return 60.0 / TUNES[tune] / 4.0


## Makes one tune: {"base": samples, "dark": samples, "bars": n}.
static func make(tune: String) -> Dictionary:
	match tune:
		"overworld":
			return _overworld()
		"cave":
			return _cave()
		"boss":
			return _boss()
		"boss_eclipse", "boss_fall":
			return _battle(tune)
	push_error("no such tune: " + tune)
	return {}


## Eighth-note text to sixteenth steps: each token lasts twice as long ("A4" -> "A4 -", "k" -> "k .").
static func x2(text: String) -> String:
	var out := PackedStringArray()
	for t in text.replace("|", " | ").split(" ", false):
		if t == "|":
			out.append(t)
		elif t == "-":
			out.append("- -")
		elif t == "." or t in ["k", "s", "h", "c"]:
			out.append(t + " .")
		else:
			out.append(t + " -")
	return " ".join(out)


## Every line of every tune, as text (8 bars of 16 steps each). "lead" and "beat" are the base
## stem's tune and drums; "dark_lead" and "dark_beat" are the dark stem's.
static func parts(tune: String) -> Dictionary:
	match tune:
		"overworld":
			return {
				"lead": ("A4 - - - - - C5 - E5 - - - D5 - C5 - | B4 - - - - - - - . . G4 - A4 B4 C5 D5 |"
					+ "A4 - - - C5 - - E5 - - - - G5 - - - | F5 - - E5 D5 - - - - - - - . . . . |"
					+ "C5 - D5 - E5 - - - A5 - - - - - G5 - | F5 - - - E5 - - - . . C5 - E5 - D5 C5 |"
					+ "D5 - - - C5 - B4 - - - G#4 - - - . . | A4 - - - - - - - - - - - . . . . |"),
				"harmony": x2("E4 - - - A4 - - - | G4 - - - D4 - - - | E4 - - - C5 - - - | A4 - - - F4 - - - |"
					+ "A4 - - - C5 - - - | C5 - - - G4 - - - | F4 - - - E4 - - - | E4 - - - . . . . |"),
				"bass": ("A2 - - A2 - - A3 - A2 - - - E3 - - - | G2 - - G2 - - G3 - G2 - - - D3 - - - |"
					+ "F2 - - F2 - - F3 - F2 - - - C3 - - - | D2 - - - - - D3 - E2 - - - E3 - E2 E2 |"
					+ "A2 - - - - - - - A2 - - A2 - - E3 - | C3 - - - - - - - G2 - - G2 - - G2 - |"
					+ "D3 - - D3 - - D3 - E2 - - E2 - - E2 - | A2 - - - - - - - . . . . E2 . E2 . |"),
				"beat": ("k . . . h . . . s . . . h . h . | k . . k h . . . s . . . h . . . |"
					+ "k . . . h . . . s . . . h . h . | k . . k h . k . s . s . s s s s |"
					+ "k . . . . . k . s . . . . . h . | k . . . . . k . s . . . h . . . |"
					+ "k . . k . . k . s . . k s . . . | k . . . h . . . s . s s s s s s |"),
				"drone": x2("A1 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |".repeat(2)),
				"dark_lead": (". . . . . . . . . . . . . . . . | A5 - - G#5 F5 - - - D#5 - - - - - - - |"
					+ "E5 - - - - - - - - - - - - - - - | . . . . . . . . . . . . . . . . |"
					+ ". . . . . . . . . . . . . . . . | . . . . . . . . . . . . . . . . |"
					+ ". . . . . . . . D#5 - - - - - E5 - | - - - - - - - - . . . . . . . . |"),
				"wind": x2(". . . . . . . . . . . . . . . . | c - - - - - - - . . . . . . . . |".repeat(2)),
				"dark_beat": (". . . . . . . . . . . . . . . . |".repeat(4)
					+ "k . . k . . k . . . . . . . . . | k . . k . . k . . . . . k . k . |"
					+ "k . . k . . k . . . . . . . . . | k . . k . . k . k . k . k k k k |"),
			}
		"cave":
			return {
				"pad": x2("A2 - - - - - - - - - - - - - - - | F2 - - - - - - - - - - - - - - - |"
					+ "D2 - - - - - - - - - - - - - - - | E2 - - - - - - - - - - - - - - - |"),
				"lead": (". . . . . . . . A3 - - - - - C4 - | E4 - D4 E4 - - - - - - D4 - - - - - |"
					+ "B3 - - - - - - - - - - - - - - - | . . . . . . . . . . . . . . . . |"
					+ ". . . . . . . . . . . . . . . . | . . . . . . . . . . . . . . . . |"
					+ ". . . . . . . . G#3 - - - - - - - | - - - - A3 - - - - - - - - - . . |"),
				"drip": (". . . . . . . . . . . . . . . . | . . . . . . E6 . . . . . . . . . |"
					+ ". . . . . . . . . . . . . . . . | . . . . . . . . . . . . B5 . . . |"
					+ ". . . . A6 . . . . . . . . . . . | . . . . . . . . . . E6 B5 . . . . |"
					+ ". . . . . . . . . . . . . . . . | . . . . . . . . . . . . . . . . |"),
				"beat": ("k . . . . . . . . . . . . . . . |".repeat(3)
					+ "k . . . . . . . . . . . h . h h |"
					+ "k . . . . . . . . . k . . . . . |".repeat(3)
					+ "k . . . . . . . . . . . . . . . |"),
				"drone": x2("A1 - - - - - - - - - - - - - - - | D#2 - - - - - - - - - - - - - - - |".repeat(2)),
				"dark_lead": (". . . . . . . . . . . . . . . . | . . . . . . . . . . . . . . . . |"
					+ "A2 - - - - - - - - - - - G#2 - - - | F2 - - - - - - - - - - - D#2 - - - |"
					+ "- - - - - - - - E2 - - - - - - - | - - - - - - - - - - - - - - - - |"
					+ ". . . . . . . . . . . . . . . . | . . . . . . . . . . . . . . . . |"),
				"dark_beat": ("k . . k . . . . . . . . . . . . |".repeat(6)
					+ "k . . k . . . . k . . k . . . . |".repeat(2)),
			}
		"boss":
			return {
				"lead": ("A4 - - - - - G#4 - F4 - - - - - D#4 - | E4 - - - - - - - - - . . A3 B3 C4 D4 |"
					+ "A4 - - - C5 - - - E5 - - D5 - - - - | B4 - - - - - - - - - - - B4 C5 B4 A4 |"
					+ "A5 - - - - - G#5 - F5 - - - - - D#5 - | E5 - - - - - D5 - - - C5 - - - - - |"
					+ "B4 - C5 - D5 - - - D#5 - - - - - - - | E5 - - - - - - - . . . . . . . . |"),
				"bass": ("A2 - A2 A2 A3 - A2 - D#3 - A2 A2 G#2 - A2 - |".repeat(4)
					+ "F2 - - F2 - - F3 - B2 - - F2 - - E2 - | E2 - - E2 - - E3 - A#2 - - E2 - - D#2 - |"
					+ "F2 - F2 F2 F3 - F2 - B2 - F2 F2 E2 - F2 - | E2 - E2 E2 E3 - E2 - A#2 - E2 E2 D#2 - E2 - |"),
				"low": x2("A1 - - - - - - - | E1 - - - - - - - |".repeat(4)),
				"beat": ("k . h . s . h . k . k . s . h . | k . h . s . h . k . . k s . h h |"
					+ "k . h . s . h . k . k . s . h . | k . h . s . h . k . k . s s s s |"
					+ "k . . . s . . k . . k . s . . . | k . . . s . . k . . k . s . h h |"
					+ "k . h . s . h . k . k . s . s . | k . s s s s s s k . s s c . . . |"),
				"dark_lead": ("A5 - D#6 A6 - D#6 A6 - A5 - D#6 A6 - D#6 A6 - |".repeat(3)
					+ "A5 D#6 A6 D#6 A5 D#6 A6 D#6 A6 - - - - - . . |"
					+ "F5 - B5 F6 - B5 F6 - F5 - B5 F6 - B5 F6 - | F5 B5 F6 B5 F5 B5 F6 B5 F6 - - - - - . . |"
					+ "E5 - A#5 E6 - A#5 E6 - E5 - A#5 E6 - A#5 E6 - | E5 A#5 E6 A#5 E5 A#5 E6 A#5 E6 - - - - - . . |"),
				"dark_beat": ("c . . . . . . . . . . . . . . . | . . . . . . . . . . . . k . k . |".repeat(3)
					+ "c . . . . . . . . . . . . . . . | . . . . . . . . k . k . k k k k |"),
			}
		"boss_eclipse":  # phase 2: he drowns the hall in night and hunts you through it
			return {
				"lead": ("A3 - - - - - - - G#3 - - - F3 - - - | D#3 - - - - - - - - - - - . . E3 - |"
					+ "A3 - - - C4 - - - B3 - - - A3 - G#3 - | F3 - - - - - - - E3 - - - - - . . |"
					+ "A3 - . A3 C4 - . C4 D#4 - - - - - - - | E4 - - - D4 - - - C4 - - - B3 - - - |"
					+ "C4 - B3 - A3 - G#3 - F3 - - - D#3 - - - | E3 - - - - - - - - - - - . . . . |"),
				"bass": ("A1 - A2 - A1 - A2 - A#1 - A#2 - A1 - A2 - |".repeat(2)
					+ "F1 - F2 - F1 - F2 - E1 - E2 - E1 - E2 - | D1 - D2 - D1 - D2 - E1 - E2 - E1 - E2 - |"
					+ "A1 - A2 - A1 - A2 - A#1 - A#2 - A1 - A2 - |".repeat(2)
					+ "F1 - F2 - F1 - F2 - D#1 - D#2 - D#1 - D#2 - | E1 - E2 - E1 - E2 - E1 - E2 - E1 E1 E1 E1 |"),
				"pad": x2("A3 - - - - - - - | A3 - - - - - - - | F3 - - - - - - - | E3 - - - - - - - |".repeat(2)),
				"beat": ("k . . . . . . . s . . . . . . . | k . . . . . k . s . . . . . h h |"
					+ "k . . . . . . . s . . . . . . . | k . . . . . k . s . . k s . s s |"
					+ "k . . k . . . . s . . . . . . . | k . . k . . k . s . . . k . . . |"
					+ "k . . k . . . . s . . . . . . . | k . k . k . k . s s s s s s c . |"),
				"dark_lead": (". . . . . . . . . . . . . . . . | A5 - - - - - - - D#6 - - - - - - - |"
					+ ". . . . . . . . . . . . . . . . | F5 - - - E5 - - - - - - - . . . . |"
					+ "A5 - D#6 - A6 - - - - - - - . . . . | G#6 - - - F6 - - - D#6 - - - - - - - |"
					+ "E6 - - - - - - - - - - - . . D#6 E6 | A5 - - - - - - - - - - - - - . . |"),
				"dark_beat": ("c . . . . . . . . . . . . . . . | . . . . . . . . . . . . k . k . |".repeat(3)
					+ "c . . . . . . . . . . . . . . . | . . . . . . . . k . k . k k k k |"),
			}
		"boss_fall":  # phase 3: the floor is gone, the crown is cracked; the land's motif fights back
			return {
				"lead": ("A4 - - - C5 - - - E5 - - - D5 - - - | B4 - - - - - - - - - . . A4 B4 C5 D5 |"
					+ "E5 - - - - - D5 - C5 - - - B4 - A4 - | G#4 - - - - - - - E4 - - - - - - - |"
					+ "A4 - C5 - E5 - A5 - - - G#5 - F5 - - - | D#5 - - - - - - - E5 - - - - - . . |"
					+ "C5 - D5 - E5 - - - D5 - C5 - B4 - G#4 - | A4 - - - - - - - - - - - . . . . |"),
				"bass": ("A1 A1 A2 A1 A1 A1 A2 A1 F1 F1 F2 F1 G1 G1 G2 G1 | E1 E1 E2 E1 E1 E1 E2 E1 E1 E1 E2 E1 G#1 G#1 G#2 G#1 |"
					+ "A1 A1 A2 A1 A1 A1 A2 A1 F1 F1 F2 F1 G1 G1 G2 G1 | E1 E1 E2 E1 E1 E1 E2 E1 D#1 D#1 D#2 D#1 E1 E1 E2 E1 |"
					+ "A1 A1 A2 A1 C2 C2 C3 C2 F1 F1 F2 F1 D#1 D#1 D#2 D#1 | E1 E1 E2 E1 E1 E1 E2 E1 E1 - - - E2 - - - |"
					+ "F1 F1 F2 F1 G1 G1 G2 G1 E1 E1 E2 E1 E1 E1 E2 E1 | A1 A1 A2 A1 A1 A1 A2 A1 E1 - - - E1 E1 E1 E1 |"),
				"harmony": x2("A3 - - - F3 - G3 - | E3 - - - - - - - | A3 - - - F3 - G3 - | E3 - - - D#3 - E3 - |"
					+ "A3 - C4 - F3 - D#3 - | E3 - - - - - - - | F3 - G3 - E3 - - - | A3 - - - - - - - |"),
				"beat": ("k . h k s . h . k . k . s . h h | k . h k s . h . k k . k s . s s |"
					+ "k . h k s . h . k . k . s . h h | k . h k s . h . k . k . s s s s |"
					+ "k k s . k k s . k k s . k k s . | k . s s k . s s k . s s s s s s |"
					+ "k . h k s . h . k . k . s . h h | k . s s s s s s k . s s c . . . |"),
				"dark_lead": (". . . . . . . . E6 - - - D#6 - E6 - | F6 - - - - - - - E6 - - - - - - - |"
					+ ". . . . . . . . E6 - - - D#6 - E6 - | B5 - - - - - - - - - - - . . . . |"
					+ "A6 - G#6 - F6 - D#6 - E6 - - - - - - - | A5 - D#6 A6 - D#6 A6 - . . . . . . . . |"
					+ "C6 - - - B5 - - - A5 - - - G#5 - - - | A5 - - - - - - - - - - - . . . . |"),
				"dark_beat": ("c . . . . . . . . . . . . . . . | . . . . . . . . k . k . k . k . |".repeat(3)
					+ "c . . . . . . . k . . . c . . . | k k k k k k k k c . . . . . . . |"),
			}
	return {}


## The map under a darkening sky. The dark stem: a drone a tritone under the key, a far bell
## playing the Shadow King's motif, and war drums in the second half. Alone it is just unease.
static func _overworld() -> Dictionary:
	var step := step_of("overworld")
	var p := parts("overworld")
	var n := Synth.length_of(p.lead, step)
	var base := Synth.mix([
		Synth.voice(p.lead, step, "pulse", 0.22, n, 0.25, [0.005, 0.08, 0.7, 0.03], 0.004),
		Synth.voice(p.harmony, step, "pulse", 0.10, n, 0.125, [0.02, 0.2, 0.5, 0.1]),
		Synth.voice(p.bass, step, "triangle", 0.45, n, 0.5, [0.002, 0.05, 0.8, 0.02]),
		Synth.drums(p.beat, step, 0.30, n),
	])
	base = Synth.echo(base, step * 6, 0.25, 0.25)
	var dark := Synth.mix([
		Synth.voice(p.drone, step, "pulse", 0.25, n, 0.5, [0.6, 0.5, 0.8, 0.6]),
		Synth.voice(p.dark_lead, step, "sine", 0.30, n, 0.5, [0.003, 0.6, 0.0, 0.05]),
		Synth.drums(p.wind, step, 0.25, n),
		Synth.drums(p.dark_beat, step, 0.30, n, 13),
	])
	dark = Synth.echo(Synth.lowpass(dark, 900.0), step * 8, 0.45, 0.5)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## Caves: ambient first. A slow pad, the Shadowfall motif low on a soft triangle, water drips, a
## heartbeat thud, a long echo. The dark stem: the heartbeat doubles, a tritone drone, the King's
## motif far below.
static func _cave() -> Dictionary:
	var step := step_of("cave")
	var p := parts("cave")
	var n := Synth.length_of(p.pad, step)
	var base := Synth.mix([
		Synth.voice(p.pad, step, "pulse", 0.20, n, 0.125, [0.8, 0.5, 0.7, 0.8]),
		Synth.voice(p.lead, step, "triangle", 0.45, n, 0.5, [0.05, 0.3, 0.6, 0.2], 0.006),
		Synth.voice(p.drip, step, "sine", 0.25, n, 0.5, [0.001, 0.25, 0.0, 0.01]),
		Synth.drums(p.beat, step, 0.35, n),
	])
	base = Synth.echo(Synth.lowpass(base, 2200.0), 0.37, 0.5, 0.45)
	var dark := Synth.mix([
		Synth.voice(p.drone, step, "pulse", 0.22, n, 0.5, [1.0, 0.5, 0.8, 1.0]),
		Synth.voice(p.dark_lead, step, "triangle", 0.5, n, 0.5, [0.1, 0.4, 0.7, 0.4]),
		Synth.drums(p.dark_beat, step, 0.45, n, 11),
	])
	dark = Synth.echo(Synth.lowpass(dark, 700.0), 0.37, 0.55, 0.5)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## The Shadow King: intense but sad. A galloping ostinato under his falling motif, answered by the
## Shadowfall motif. The dark stem (phase 2 of the fight, or deep gloom): a shrieking tritone
## arpeggio, crashes and tom fills.
static func _boss() -> Dictionary:
	var step := step_of("boss")
	var p := parts("boss")
	var n := Synth.length_of(p.lead, step)
	var base := Synth.mix([
		Synth.voice(p.lead, step, "pulse", 0.22, n, 0.25, [0.005, 0.1, 0.75, 0.04], 0.008),
		Synth.voice(p.bass, step, "pulse", 0.14, n, 0.5, [0.002, 0.05, 0.6, 0.02]),
		Synth.voice(p.low, step, "triangle", 0.45, n, 0.5, [0.01, 0.2, 0.8, 0.1]),
		Synth.drums(p.beat, step, 0.32, n, 3),
	])
	base = Synth.echo(base, step * 6, 0.2, 0.2)
	var dark := Synth.mix([
		Synth.voice(p.dark_lead, step, "pulse", 0.14, n, 0.125, [0.002, 0.04, 0.5, 0.02]),
		Synth.drums(p.dark_beat, step, 0.35, n, 5),
	])
	dark = Synth.echo(Synth.lowpass(dark, 3000.0), step * 6, 0.4, 0.4)
	return {"base": Synth.normalise(base), "dark": Synth.normalise(dark, 0.6), "bars": 8}


## The fight's later phases on the code synth (only when a stem file is missing): the lead,
## the bass, the pad or harmony and the drums; the dark stem is the high line and the crashes.
static func _battle(tune: String) -> Dictionary:
	var step := step_of(tune)
	var p := parts(tune)
	var n := Synth.length_of(p.lead, step)
	var chords: String = p.get("pad", p.get("harmony", ""))
	var base := Synth.mix([
		Synth.voice(p.lead, step, "pulse", 0.22, n, 0.25, [0.005, 0.1, 0.75, 0.04], 0.008),
		Synth.voice(p.bass, step, "triangle", 0.40, n, 0.5, [0.002, 0.05, 0.7, 0.02]),
		Synth.voice(chords, step, "pulse", 0.10, n, 0.125, [0.05, 0.2, 0.6, 0.1]),
		Synth.drums(p.beat, step, 0.32, n, 3),
	])
	base = Synth.echo(base, step * 6, 0.2, 0.2)
	var dark := Synth.mix([
		Synth.voice(p.dark_lead, step, "pulse", 0.14, n, 0.125, [0.002, 0.04, 0.5, 0.02]),
		Synth.drums(p.dark_beat, step, 0.35, n, 5),
	])
	dark = Synth.echo(Synth.lowpass(dark, 3000.0), step * 6, 0.4, 0.4)
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
