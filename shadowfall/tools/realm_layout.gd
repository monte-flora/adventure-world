extends Node
## Writes one realm screen's Gemini map (gemini_realm.py export runs this; it's a scene so the
## autoloads load):
##   godot --headless --path shadowfall res://tools/realm_layout.tscn -- <screen, e.g. B3> <out dir>
## out/layout.png (2752 × 1536, PaintedRealmScreen.layout, stretched, blocky) and out/layout.json (the land,
## the props and gates on it, the legend's colours).

const OUT_SIZE := Vector2i(2752, 1536)        # polish.py SIZE: Gemini's 16:9


func _ready() -> void:
	var a := OS.get_cmdline_user_args()
	var sc := WorldMap.screen_named(a[0]) if a.size() == 2 else Vector2i(-1, -1)
	if sc.x < 0:
		printerr("realm_layout: want <screen like B3> <out dir>")
		get_tree().quit(1)
		return
	var w := WorldMap.load_realm()
	var got := PaintedRealmScreen.layout(w, sc)
	var img: Image = got.image
	img.resize(OUT_SIZE.x, OUT_SIZE.y, Image.INTERPOLATE_NEAREST)
	DirAccess.make_dir_recursive_absolute(a[1])
	img.save_png(a[1].path_join("layout.png"))
	var mid := sc * WorldMap.SCREEN + WorldMap.SCREEN / 2
	var legend := []
	for k in PaintedRealmScreen.LAYOUT:
		var c: Color = PaintedRealmScreen.LAYOUT[k]
		legend.append([k, [c.r8, c.g8, c.b8]])
	var info := {"screen": WorldMap.screen_name(sc), "land": WorldMap.realm_id(w.land(mid)),
		"land_name": w.land_name(w.land(mid)), "props": got.props, "gates": got.gates, "roles": got.roles, "legend": legend,
		"painted_screen": w.painted_screens.has(sc)}
	var f := FileAccess.open(a[1].path_join("layout.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(info, " "))
	f.close()
	print("realm_layout: %s -> %s" % [info.screen, a[1]])
	get_tree().quit(0)
