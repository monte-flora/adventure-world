extends Node
## Tiny made-up sound effects (an autoload called `Sfx`). Every sound is generated here
## as a beep, sweep or crunch: nothing is downloaded.

const RATE := 22050

var sounds := {}
var _players: Array[AudioStreamPlayer] = []
var _next := 0


func _ready() -> void:
	sounds["jump"] = _tone([[330.0, 620.0, 0.12]], "square", 0.18)
	sounds["double"] = _tone([[440.0, 990.0, 0.16]], "square", 0.18)
	sounds["swing"] = _tone([[900.0, 300.0, 0.10]], "noise", 0.15)
	sounds["hit"] = _tone([[220.0, 110.0, 0.12]], "square", 0.25)
	sounds["stomp"] = _tone([[300.0, 70.0, 0.18]], "square", 0.28)
	sounds["diamond"] = _tone([[988.0, 988.0, 0.07], [1319.0, 1319.0, 0.16]], "square", 0.15)
	sounds["hurt"] = _tone([[520.0, 140.0, 0.3]], "square", 0.25)
	sounds["lever"] = _tone([[140.0, 90.0, 0.25]], "noise", 0.3)
	sounds["gate"] = _tone([[80.0, 60.0, 0.6]], "square", 0.2)
	sounds["portal"] = _tone([[200.0, 800.0, 0.35]], "sine", 0.3)
	sounds["zombie"] = _tone([[110.0, 95.0, 0.4]], "square", 0.12)
	for i in 6:
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)


func play(name: String) -> void:
	if not sounds.has(name) or _players.is_empty():
		return
	var p := _players[_next]
	_next = (_next + 1) % _players.size()
	p.stream = sounds[name]
	p.play()


## Builds a sound from notes [from_hz, to_hz, seconds], one after the other.
func _tone(notes: Array, wave: String, volume: float) -> AudioStreamWAV:
	var samples := PackedFloat32Array()
	var phase := 0.0
	for note in notes:
		var n := int(RATE * float(note[2]))
		for i in n:
			var p := float(i) / n
			var f: float = lerpf(note[0], note[1], p)
			phase = fmod(phase + f / RATE, 1.0)
			var s := 0.0
			match wave:
				"square":
					s = 1.0 if phase < 0.5 else -1.0
				"sine":
					s = sin(phase * TAU)
				_:
					s = randf_range(-1.0, 1.0) * (1.0 if phase < 0.5 else 0.6)
			var env := minf(1.0, i / 200.0) * (1.0 - p)
			samples.append(s * env * volume)
	var data := PackedByteArray()
	data.resize(samples.size() * 2)
	for i in samples.size():
		data.encode_s16(i * 2, int(clampf(samples[i], -1.0, 1.0) * 32767.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = RATE
	w.stereo = false
	w.data = data
	return w
