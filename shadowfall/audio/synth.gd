extends RefCounted
## The sound maker: every note in Shadowfall is made here, from maths (no samples, nothing
## downloaded). "NES rules, modern room": pulse, triangle, sine and noise voices, then echo and
## a low-pass. A port of spikes/audio/make_audio.py (docs/teen/audio/README.md). Owned by B6.
##
## Tune text: one token per step, "A4" plays a note, "-" holds it, "." rests, "|" is decoration.
## Drum text: k = low thud, s = snare, h = hat, c = long crash (wind).

const RATE := 22050
const NOTE_STEPS := {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3,
	"G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}


static func freq(note: String) -> float:
	var octave := int(note.right(1))
	return 440.0 * pow(2.0, (NOTE_STEPS[note.left(-1)] + 12 * (octave - 4)) / 12.0)


static func tokens(text: String) -> PackedStringArray:
	return text.replace("|", " ").split(" ", false)


## How many samples a tune of this text lasts at this step (seconds per token).
static func length_of(text: String, step: float) -> int:
	return tokens(text).size() * int(RATE * step)


static func _osc(wave: String, phase: float, duty: float) -> float:
	match wave:
		"pulse":
			return 1.0 if phase < duty else -1.0
		"triangle":  # NES-like: 16 steps, a little gritty
			return roundf((4.0 * absf(phase - 0.5) - 1.0) * 7.5) / 7.5
		_:
			return sin(TAU * phase)


## One voice. adsr = [attack s, decay s, sustain level, release s]; the release is inside the note.
static func voice(text: String, step: float, wave: String, vol: float, length: int, duty := 0.5,
		adsr := [0.005, 0.08, 0.7, 0.03], vibrato := 0.0) -> PackedFloat32Array:
	var buf := PackedFloat32Array()
	buf.resize(length)
	var seq := tokens(text)
	var n_step := int(RATE * step)
	var a := maxi(1, int(RATE * adsr[0]))
	var d := maxi(1, int(RATE * adsr[1]))
	var s: float = adsr[2]
	var r := maxi(1, int(RATE * adsr[3]))
	var pulse := wave == "pulse"
	var tri := wave == "triangle"
	var i := 0
	while i < seq.size():
		var note := seq[i]
		var hold := 1
		while i + hold < seq.size() and seq[i + hold] == "-":
			hold += 1
		if note != "." and note != "-":
			var f := freq(note)
			var n := hold * n_step
			var start := i * n_step
			var inc := f / RATE
			var phase := 0.0
			var ramp := RATE * 0.25
			var a_d := a + d
			var rel := n - r
			for j in mini(n, length - start):
				if vibrato > 0.0:
					phase += inc * (1.0 + vibrato * sin(TAU * 5.5 * j / RATE) * minf(1.0, j / ramp))
				else:
					phase += inc
				if phase >= 1.0:
					phase -= 1.0
				var env := s
				if j < a:
					env = float(j) / a
				elif j < a_d:
					env = 1.0 - (1.0 - s) * (j - a) / d
				if j > rel:
					env = minf(env, s) * float(n - j) / r
				var v: float
				if pulse:
					v = 1.0 if phase < duty else -1.0
				elif tri:
					v = roundf((4.0 * absf(phase - 0.5) - 1.0) * 7.5) / 7.5
				else:
					v = sin(TAU * phase)
				buf[start + j] += v * env * vol
		i += hold
	return buf


## Noise-channel drums (see the letters at the top).
static func drums(text: String, step: float, vol: float, length: int, seed := 7) -> PackedFloat32Array:
	var buf := PackedFloat32Array()
	buf.resize(length)
	var seq := tokens(text)
	var n_step := int(RATE * step)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var durs := {"k": 0.14, "s": 0.10, "h": 0.03, "c": 0.9}
	var gains := {"s": 0.8, "h": 0.35, "c": 0.3}
	for i in seq.size():
		var hit := seq[i]
		if not durs.has(hit):
			continue
		var n := int(RATE * durs[hit])
		var start := i * n_step
		var held := 0.0
		for j in mini(n, length - start):
			var fade := pow(1.0 - float(j) / n, 2.0)
			var v: float
			if hit == "k":  # a falling sine thump
				v = sin(TAU * (90.0 - 50.0 * j / n) * j / RATE) * 1.4
			else:
				if hit == "s" or j % 2 == 0:  # sample-and-hold: "metallic" noise
					held = rng.randf_range(-1.0, 1.0)
				v = held * gains[hit]
			buf[start + j] += v * fade * vol
	return buf


static func mix(bufs: Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	var n := 0
	for b in bufs:
		n = maxi(n, b.size())
	out.resize(n)
	for b: PackedFloat32Array in bufs:
		for i in b.size():
			out[i] += b[i]
	return out


## One-pole low-pass. Lower cutoff = duller, further away, darker. Loops: the filter runs twice
## round so the start matches the end.
static func lowpass(buf: PackedFloat32Array, cutoff: float) -> PackedFloat32Array:
	var a := 1.0 - exp(-TAU * cutoff / RATE)
	var y := 0.0
	var out := PackedFloat32Array()
	out.resize(buf.size())
	for _round in 2:
		for i in buf.size():
			y += a * (buf[i] - y)
			out[i] = y
	return out


## A room echo. loop = true wraps the tail to the start so a loop stays seamless.
static func echo(buf: PackedFloat32Array, delay: float, feedback: float, wet: float, loop := true) -> PackedFloat32Array:
	var d := int(RATE * delay)
	var n := buf.size()
	var out := buf.duplicate()
	for _round in 2:  # two passes so the wrapped tail settles
		for i in n:
			var src := i - d
			if src < 0 and not loop:
				continue
			out[i] = buf[i] + out[posmod(src, n)] * feedback
	for i in n:
		out[i] = buf[i] * (1.0 - wet) + out[i] * wet
	return out


## A sound effect: the pitch slides f0 -> f1 over dur seconds, fading out.
static func sweep(f0: float, f1: float, dur: float, wave := "pulse", duty := 0.5, vol := 0.6,
		curve := 1.0, noise := 0.0, seed := 1) -> PackedFloat32Array:
	var n := int(RATE * dur)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var phase := 0.0
	var out := PackedFloat32Array()
	out.resize(n)
	for j in n:
		var t := pow(float(j) / n, curve)
		phase = fmod(phase + (f0 + (f1 - f0) * t) / RATE, 1.0)
		var v := _osc(wave, phase, duty) * (1.0 - noise) + rng.randf_range(-1.0, 1.0) * noise
		out[j] = v * vol * (1.0 - float(j) / n) * minf(1.0, j / 40.0)
	return out


static func silence(seconds: float) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	out.resize(int(RATE * seconds))
	return out


static func join(bufs: Array) -> PackedFloat32Array:
	var out := PackedFloat32Array()
	for b in bufs:
		out.append_array(b)
	return out


static func peak(buf: PackedFloat32Array) -> float:
	var m := 0.0
	for v in buf:
		m = maxf(m, absf(v))
	return m


## Scales so the loudest sample is `to`.
static func normalise(buf: PackedFloat32Array, to := 0.85) -> PackedFloat32Array:
	var m := maxf(1e-9, peak(buf))
	var out := buf.duplicate()
	for i in out.size():
		out[i] *= to / m
	return out


## Turns samples into a playable 16-bit mono stream; loop = true repeats the whole buffer.
static func to_stream(buf: PackedFloat32Array, loop := false) -> AudioStreamWAV:
	var data := PackedByteArray()
	data.resize(buf.size() * 2)
	for i in buf.size():
		data.encode_s16(i * 2, int(clampf(buf[i], -1.0, 1.0) * 32767.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	if loop:
		w.loop_mode = AudioStreamWAV.LOOP_FORWARD
		w.loop_begin = 0
		w.loop_end = buf.size()
	return w
