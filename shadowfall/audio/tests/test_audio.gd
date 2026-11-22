extends TestCase
## Audio: the stems follow the gloom, the tunes loop on whole bars, every sound is made and fits.

const Synth := preload("res://audio/synth.gd")
const Tunes := preload("res://audio/tunes.gd")
const Sfx := preload("res://audio/sfx.gd")


func test_buses() -> void:
	for bus in ["Master", "Music", "SFX"]:
		check(AudioServer.get_bus_index(bus) != -1, "bus " + bus)
	check_eq(AudioServer.get_bus_send(AudioServer.get_bus_index("Music")), &"Master", "Music goes to Master")


func test_stems_switch_with_gloom() -> void:
	Audio.play_music("overworld")
	var s: AudioStreamSynchronized = Audio.music_stream("overworld")
	Audio.update(true)
	check_eq(Audio.dark, 0.0, "bright world: no dark stem")
	check(s.get_sync_stream_volume(1) <= Audio.SILENT_DB, "dark stem silent at gloom 0")
	check(is_equal_approx(s.get_sync_stream_volume(0), 0.0), "base stem full at gloom 0")
	Game.tick(Game.GLOOM_MINUTES * 60.0)  # all the way dark
	check_eq(Game.gloom, 1.0, "gloom reached 1")
	Audio.update()
	check(Audio.dark > 0.0 and Audio.dark < 1.0, "the dark stem ramps in, not a jump")
	for i in 30:
		Audio.update()
	check_eq(Audio.dark, 1.0, "full dark after the ramp")
	check(is_equal_approx(s.get_sync_stream_volume(1), 0.0), "dark stem at full volume")
	check(s.get_sync_stream_volume(0) < -1.0, "base stem drops under the dark")
	Game.take_stone("dawn")  # pushes the gloom back to 0.75
	Audio.update(true)
	check(Audio.dark > 0.5 and Audio.dark < 1.0, "a Light Stone pulls the dark stem back")
	Game.reset()
	Audio.intensity = 1.0
	Audio.update(true)
	check_eq(Audio.dark, 1.0, "intensity pushes the dark stem in by hand")
	Audio.intensity = 0.0
	Audio.update(true)


func test_each_screen_picks_its_tune() -> void:
	for screen in Audio.SCENE_MUSIC:
		Scenes.goto(screen)
		await frames(1)
		check_eq(Audio.track, Audio.SCENE_MUSIC[screen], screen + " plays its tune")
		check(Audio._music.playing, screen + ": the music player runs")


func test_tunes_loop_on_whole_bars() -> void:
	for tune in Tunes.TUNES:
		var s: AudioStreamSynchronized = Audio.music_stream(tune)
		var base: AudioStreamWAV = s.get_sync_stream(0)
		var dark: AudioStreamWAV = s.get_sync_stream(1)
		check_eq(base.data.size(), dark.data.size(), tune + ": stems the same length")
		check_eq(base.loop_mode, AudioStreamWAV.LOOP_FORWARD, tune + ": base loops")
		check_eq(dark.loop_mode, AudioStreamWAV.LOOP_FORWARD, tune + ": dark loops")
		var bar := int(Synth.RATE * Tunes.step_of(tune)) * Tunes.STEPS_PER_BAR
		check_eq(base.loop_end % bar, 0, tune + ": whole bars")
		check(base.loop_end / bar >= 4, tune + ": at least 4 bars")


## The tunes aren't steady eighths: every lead mixes note lengths and rests, every beat varies its bars.
func test_tunes_have_varied_rhythm() -> void:
	for tune in Tunes.TUNES:
		var parts := Tunes.parts(tune)
		for part in parts:
			check_eq(Synth.tokens(parts[part]).size(), 8 * Tunes.STEPS_PER_BAR, "%s %s: 8 whole bars" % [tune, part])
		for part in ["lead", "dark_lead"]:
			var seq := Synth.tokens(parts[part])
			var lengths := {}
			var i := 0
			while i < seq.size():
				var hold := 1
				while i + hold < seq.size() and seq[i + hold] == "-":
					hold += 1
				if seq[i] != "." and seq[i] != "-":
					lengths[hold] = true
				i += hold
			check(lengths.size() >= 3, "%s %s: %d note lengths, want 3+" % [tune, part, lengths.size()])
			check("." in seq, "%s %s: has rests" % [tune, part])
		var bars := {}
		var beat := Synth.tokens(parts.beat)
		for b in 8:
			bars[" ".join(beat.slice(b * Tunes.STEPS_PER_BAR, (b + 1) * Tunes.STEPS_PER_BAR))] = true
		check(bars.size() >= 3, "%s beat: %d different bars, want 3+" % [tune, bars.size()])


func test_peaks_and_size_budget() -> void:
	var music_bytes := 0
	for tune in Tunes.TUNES:
		var t := Tunes.make(tune)
		for stem in ["base", "dark"]:
			var p := Synth.peak(t[stem])
			check(p > 0.1 and p <= 0.9, "%s %s peak %.2f in (0.1, 0.9]" % [tune, stem, p])
			music_bytes += t[stem].size() * 2
	check(music_bytes < 16 * 1024 * 1024, "music in memory under 16 MB")
	var sfx_bytes := 0
	for sound in Sfx.NAMES:
		var w := Audio.sfx_stream(sound)
		check(w != null and w.data.size() > 0, sound + " is made")
		var buf := Sfx.make(sound)
		check(Synth.peak(buf) <= 1.0, sound + " doesn't clip")
		sfx_bytes += w.data.size()
	check(sfx_bytes < 1024 * 1024, "sound effects under 1 MB")


func test_play_sfx_and_volumes() -> void:
	Audio.play_sfx("jump")
	Audio.play_sfx("no_such_sound")  # a warning, not a crash
	check(Audio._voices.any(func(p): return p.playing and p.stream == Audio.sfx_stream("jump")), "jump plays")
	var was: float = Audio.get_volume("Music")
	Audio.set_volume("Music", 0.53, false)
	check(is_equal_approx(Audio.get_volume("Music"), 0.5), "volumes go in steps of 10%")
	Audio.duck(true)
	var db := AudioServer.get_bus_volume_db(AudioServer.get_bus_index("Music"))
	check(is_equal_approx(db, linear_to_db(0.5 * Audio.DUCK)), "duck: music to 30%")
	Audio.duck(false)
	Audio.set_volume("Music", was, false)


func test_freq() -> void:
	check(is_equal_approx(Synth.freq("A4"), 440.0), "A4 is 440 Hz")
	check(is_equal_approx(Synth.freq("A3"), 220.0), "A3 is 220 Hz")
	check(absf(Synth.freq("C4") - 261.63) < 0.01, "C4")
