extends Node
## Music and sound (autoload `Audio`). Owned by B6. Spec: docs/teen/audio/README.md.
##   Audio.play_sfx("jump")          a sound effect (names in audio/sfx.gd)
##   Audio.play_music("cave")        a tune (audio/tunes.gd); each screen picks its own (SCENE_MUSIC)
##   Audio.intensity = 1.0           push the dark stem in by hand (boss phase 2, Nightfall); 0 = off
##   Audio.duck(true)                music down to 30% under dialogue
##   Audio.set_volume("Music", 0.5)  0..1 for "Master", "Music", "SFX"; saved in user://audio.cfg
##   Audio.toggle_mute()
## Every tune plays as one AudioStreamSynchronized with 2 stems, base and dark, started together.
## The dark stem fades in with Game.gloom: dark = smoothstep(0.3, 0.9, gloom). As it does, the base
## stem drops to 75% and the Music bus low-pass closes from 8 kHz to 1.8 kHz. The gains change at
## most 10 times a second, ramped (a full swing takes 2 s). Every sound is made in code at first
## use and kept (nothing is downloaded or sampled; see CREDITS-audio.md).

const Synth := preload("res://audio/synth.gd")
const Tunes := preload("res://audio/tunes.gd")
const Sfx := preload("res://audio/sfx.gd")

const SCENE_MUSIC := {"title": "overworld", "overworld": "overworld", "cave": "cave", "boss": "boss"}
const BUSES := ["Music", "SFX"]
const VOLUME_DEFAULTS := {"Master": 1.0, "Music": 0.35, "SFX": 0.8}
const SETTINGS_PATH := "user://audio.cfg"
const UPDATE_EVERY := 0.1        # seconds between gain updates
const RAMP := 0.05               # the most the dark gain moves per update
const BASE_AT_FULL_DARK := 0.75
const CUTOFF_BRIGHT := 8000.0
const CUTOFF_DARK := 1800.0
const CROSSFADE := 0.9
const DUCK := 0.3
const SFX_VOICES := 8
const SILENT_DB := -80.0

var track := ""                  # the tune playing now ("" = none)
var intensity := 0.0             # extra darkness from the game, 0..1 (the dark stem follows the larger)
var dark := 0.0                  # the dark stem's gain now, 0..1
var volumes := VOLUME_DEFAULTS.duplicate()
var muted := false
var ducked := false

var _streams := {}               # tune -> AudioStreamSynchronized
var _sounds := {}                # sfx name -> AudioStreamWAV
var _music: AudioStreamPlayer    # the tune playing now
var _fading: AudioStreamPlayer   # the one fading out
var _voices: Array[AudioStreamPlayer] = []
var _next_voice := 0
var _lowpass := AudioEffectLowPassFilter.new()
var _clock := 0.0
var _tweens := {}                # player -> its fade


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	_make_buses()
	_load_settings()
	_music = _player("Music")
	_fading = _player("Music")
	for i in SFX_VOICES:
		_voices.append(_player("SFX"))
	Scenes.switched.connect(_on_screen)


func _process(delta: float) -> void:
	_clock += delta
	if _clock >= UPDATE_EVERY:
		_clock = 0.0
		update()


## The dark stem's target gain, 0..1.
func dark_target() -> float:
	return maxf(smoothstep(0.3, 0.9, Game.gloom), clampf(intensity, 0.0, 1.0))


## One gain update: moves `dark` a ramp step towards its target (snap = jump there).
func update(snap := false) -> void:
	var want := dark_target()
	dark = want if snap else move_toward(dark, want, RAMP)
	_lowpass.cutoff_hz = lerpf(CUTOFF_BRIGHT, CUTOFF_DARK, dark)
	if _streams.has(track):
		var s: AudioStreamSynchronized = _streams[track]
		s.set_sync_stream_volume(0, _db(lerpf(1.0, BASE_AT_FULL_DARK, dark)))
		s.set_sync_stream_volume(1, _db(dark))


## Plays a tune (see Tunes.TUNES), crossfading from the one before. The same tune keeps going.
func play_music(tune: String) -> void:
	if tune == track or not Tunes.TUNES.has(tune):
		return
	var stream := music_stream(tune)
	track = tune
	update(true)
	_swap_players(CROSSFADE)
	_music.stream = stream
	_music.volume_linear = 0.0
	_music.play()
	_fade(_music, 1.0, CROSSFADE)


func stop_music(fade := 0.4) -> void:
	track = ""
	_swap_players(fade)


## A tune's stream (made on first use): stem 0 = base, stem 1 = dark.
func music_stream(tune: String) -> AudioStreamSynchronized:
	if not _streams.has(tune):
		var t := Tunes.make(tune)
		var s := AudioStreamSynchronized.new()
		s.stream_count = 2
		s.set_sync_stream(0, Synth.to_stream(t["base"], true))
		s.set_sync_stream(1, Synth.to_stream(t["dark"], true))
		_streams[tune] = s
	return _streams[tune]


func play_sfx(sound: String, pitch := 1.0) -> void:
	var s := sfx_stream(sound)
	if s == null:
		return
	var p := _voices[_next_voice]
	_next_voice = (_next_voice + 1) % _voices.size()
	p.stream = s
	p.pitch_scale = pitch
	p.play()


func sfx_stream(sound: String) -> AudioStreamWAV:
	if sound not in Sfx.NAMES:
		push_warning("Audio: no sound called " + sound)
		return null
	if not _sounds.has(sound):
		_sounds[sound] = Synth.to_stream(Sfx.make(sound))
	return _sounds[sound]


func duck(on: bool) -> void:
	ducked = on
	_apply_volumes()


func set_volume(bus: String, value: float, save := true) -> void:
	if not volumes.has(bus):
		return
	volumes[bus] = clampf(snappedf(value, 0.1), 0.0, 1.0)
	_apply_volumes()
	if save:
		_save_settings()


func get_volume(bus: String) -> float:
	return volumes.get(bus, 0.0)


func toggle_mute() -> void:
	muted = not muted
	_apply_volumes()
	_save_settings()


func _on_screen(screen: String) -> void:
	if SCENE_MUSIC.has(screen):
		play_music(SCENE_MUSIC[screen])


func _swap_players(fade: float) -> void:
	var old := _music
	_music = _fading
	_fading = old
	if old.playing:
		_fade(old, 0.0, fade)


## Fades a player to `to` (0..1) over `seconds`; at 0 it stops. A new fade replaces the old one.
func _fade(p: AudioStreamPlayer, to: float, seconds: float) -> void:
	var old: Tween = _tweens.get(p)
	if old and old.is_valid():
		old.kill()
	var tw := create_tween()
	tw.tween_property(p, "volume_linear", to, seconds)
	if to <= 0.0:
		tw.tween_callback(p.stop)
	_tweens[p] = tw


func _player(bus: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.bus = bus
	add_child(p)
	return p


func _make_buses() -> void:
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")
	AudioServer.add_bus_effect(AudioServer.get_bus_index("Music"), _lowpass)
	_lowpass.cutoff_hz = CUTOFF_BRIGHT


func _apply_volumes() -> void:
	for bus in volumes:
		var v: float = volumes[bus]
		if bus == "Music" and ducked:
			v *= DUCK
		AudioServer.set_bus_volume_db(AudioServer.get_bus_index(bus), _db(v))
	AudioServer.set_bus_mute(0, muted)


func _load_settings() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SETTINGS_PATH) == OK:
		for bus in volumes:
			volumes[bus] = clampf(float(cfg.get_value("volume", bus, volumes[bus])), 0.0, 1.0)
		muted = bool(cfg.get_value("volume", "muted", false))
	_apply_volumes()


func _save_settings() -> void:
	var cfg := ConfigFile.new()
	for bus in volumes:
		cfg.set_value("volume", bus, volumes[bus])
	cfg.set_value("volume", "muted", muted)
	cfg.save(SETTINGS_PATH)


static func _db(linear: float) -> float:
	return SILENT_DB if linear <= 0.0001 else maxf(SILENT_DB, linear_to_db(linear))
