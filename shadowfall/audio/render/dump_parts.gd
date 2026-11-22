extends SceneTree
## Writes every tune's note text (Tunes.parts) and tempo to JSON for render_music.py.
##   godot --headless --path shadowfall --script res://audio/render/dump_parts.gd -- <out.json>

const Tunes := preload("res://audio/tunes.gd")


func _init() -> void:
	var out := {"steps_per_bar": Tunes.STEPS_PER_BAR, "tunes": {}}
	for tune in Tunes.TUNES:
		out.tunes[tune] = {"bpm": Tunes.TUNES[tune], "parts": Tunes.parts(tune)}
	var args := OS.get_cmdline_user_args()
	var f := FileAccess.open(args[0], FileAccess.WRITE)
	f.store_string(JSON.stringify(out, "\t"))
	f.close()
	quit()
