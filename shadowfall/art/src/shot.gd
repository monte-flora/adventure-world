extends SceneTree
## Screenshot any screen (silent window): godot --path shadowfall --audio-driver Dummy -s art/src/shot.gd -- --scene=overworld --out=/abs/x.png [--frames=40] [--dusk=3a4068] [--realm=nightfall] [--at=c,r] [--eval='scene.hero.place(Vector2i(5,5))'] (eval: calls only, no assignment)
func _initialize() -> void:
	_run.call_deferred()

func _run() -> void:
	var opts := {}
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=", true, 1)
		opts[kv[0]] = kv[1] if kv.size() > 1 else "1"
	await process_frame
	var root_game = root.get_node("Game")
	for ab in opts.get("abilities", "").split(",", false):
		root_game.abilities[ab] = true if root_game.abilities is Dictionary else null
	var args := {}
	if opts.has("realm"): args["realm"] = opts.realm
	if opts.has("file"): args["file"] = opts.file
	if opts.has("at"):
		var p: PackedStringArray = opts.at.split(",")
		args["at"] = Vector2i(int(p[0]), int(p[1]))
	root.get_node("Scenes").goto(opts.get("scene", "overworld"), args)
	for i in int(opts.get("frames", "40")):
		await process_frame
	if opts.has("dusk"):                       # --dusk=3a4068: tint the world to check lights at night
		var cm := CanvasModulate.new()
		cm.color = Color(opts.dusk)
		current_scene.add_child(cm)
		for i in 90:
			await process_frame
	if opts.has("eval"):
		var e := Expression.new()
		e.parse(opts.eval, ["scene"])
		e.execute([current_scene], self)
		for i in 20:
			await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(opts.get("out", "/tmp/shot.png"))
	quit()
