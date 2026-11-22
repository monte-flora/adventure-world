extends SceneTree
## Shrinks a painting from Gemini into painted.webp for one cave (polish.py import runs this):
##   godot --headless --path shadowfall --script res://tools/polish_import.gd -- <src> <dst.webp> <w> <h> <max bytes>
## w x h is the cave in game pixels (32 a block): the painting is stretched to it, so it lines up
## with the blocks 1:1. The WebP quality steps down until the file is under max bytes.


func _init() -> void:
	var a := OS.get_cmdline_user_args()
	if a.size() != 5:
		printerr("polish_import: want <src> <dst.webp> <w> <h> <max bytes>")
		quit(1)
		return
	var img := Image.load_from_file(a[0])
	if img == null or img.is_empty():
		printerr("polish_import: can't read " + a[0])
		quit(1)
		return
	img.convert(Image.FORMAT_RGB8)
	img.resize(int(a[2]), int(a[3]), Image.INTERPOLATE_LANCZOS)
	var quality := 0.85
	while true:
		var bytes := img.save_webp_to_buffer(true, quality)
		if bytes.size() <= int(a[4]) or quality <= 0.3:
			var f := FileAccess.open(a[1], FileAccess.WRITE)
			if f == null:
				printerr("polish_import: can't write " + a[1])
				quit(1)
				return
			f.store_buffer(bytes)
			f.close()
			# The web export copies levels/ into the game: "keep" ships the small WebP as it is
			# (Godot would otherwise re-encode it as a much bigger texture).
			var imp := FileAccess.open(a[1] + ".import", FileAccess.WRITE)
			imp.store_string("[remap]\n\nimporter=\"keep\"\n")
			imp.close()
			print("polish_import: %s %dx%d %d bytes (quality %.2f)" % [a[1], img.get_width(), img.get_height(), bytes.size(), quality])
			quit(0)
			return
		quality -= 0.1
