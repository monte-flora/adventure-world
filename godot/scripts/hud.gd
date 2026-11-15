extends CanvasLayer
## Hearts and diamonds in the corner, a big message in the middle, and the controls at first.

var panel: Control
var msg: Label
var help: Label
var msg_time := 0.0
var help_time := 10.0
var pop := 0.0
var last_diamonds := 0


func _ready() -> void:
	panel = Control.new()
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.draw.connect(_draw_panel)
	add_child(panel)
	msg = _label(46, Color("fff3c4"))
	msg.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	msg.offset_top = 100
	msg.offset_bottom = 170
	help = _label(22, Color.WHITE)
	help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	help.offset_top = -60
	help.offset_bottom = -20
	help.text = "Arrows: run   SPACE: jump (twice: double jump)   A or J: sword   Q / E or right-drag: camera"
	Game.changed.connect(panel.queue_redraw)
	Game.message.connect(show_message)
	last_diamonds = Game.diamonds


func _label(size: int, color: Color) -> Label:
	var l := Label.new()
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color("3b2412"))
	l.add_theme_constant_override("outline_size", 12)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l


func show_message(text: String) -> void:
	msg.text = text
	msg_time = 2.2


func _process(delta: float) -> void:
	msg_time -= delta
	msg.modulate.a = clampf(msg_time * 2.0, 0.0, 1.0)
	help_time -= delta
	help.modulate.a = clampf(help_time, 0.0, 1.0)
	if Game.diamonds != last_diamonds:
		last_diamonds = Game.diamonds
		pop = 1.0
	if pop > 0.0:
		pop = maxf(0.0, pop - delta * 3.0)
		panel.queue_redraw()


func _draw_panel() -> void:
	var font := ThemeDB.fallback_font
	# a soft rounded backing
	panel.draw_rect(Rect2(14, 14, 64 * Game.MAX_HEARTS + 24, 72), Color(0, 0, 0, 0.25))
	for i in Game.MAX_HEARTS:
		var full := i < Game.hearts
		_heart(Vector2(50 + i * 64, 50), 26.0, Color("ff3b4a") if full else Color(0.25, 0.2, 0.22, 0.8))
	var w := panel.size.x
	var s := 1.0 + pop * 0.4
	panel.draw_rect(Rect2(w - 250, 14, 236, 72), Color(0, 0, 0, 0.25))
	_diamond(Vector2(w - 210, 50), 24.0 * s)
	var text := "%d / %d" % [Game.diamonds, Game.TOTAL_DIAMONDS]
	panel.draw_string_outline(font, Vector2(w - 170, 64), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, 10, Color("3b2412"))
	panel.draw_string(font, Vector2(w - 170, 64), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, Color.WHITE)


func _heart(c: Vector2, r: float, color: Color) -> void:
	var pts := PackedVector2Array()
	for i in 40:
		var t := TAU * i / 40.0
		# the classic heart curve, flipped so the point is at the bottom
		var x := 16.0 * pow(sin(t), 3)
		var y := -(13.0 * cos(t) - 5.0 * cos(2 * t) - 2.0 * cos(3 * t) - cos(4 * t))
		pts.append(c + Vector2(x, y) * r / 16.0)
	var outline := PackedVector2Array()
	for p in pts:
		outline.append(c + (p - c) * 1.18)
	panel.draw_colored_polygon(outline, Color("3b2412"))
	panel.draw_colored_polygon(pts, color)
	panel.draw_circle(c + Vector2(-r * 0.4, -r * 0.35), r * 0.18, Color(1, 1, 1, 0.6))


func _diamond(c: Vector2, r: float) -> void:
	var outer := PackedVector2Array([c + Vector2(0, -r), c + Vector2(r, -r * 0.2), c + Vector2(0, r), c + Vector2(-r, -r * 0.2)])
	var big := PackedVector2Array()
	for p in outer:
		big.append(c + (p - c) * 1.2)
	panel.draw_colored_polygon(big, Color("3b2412"))
	panel.draw_colored_polygon(outer, Color("4fe3ff"))
	panel.draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r), c + Vector2(r, -r * 0.2), c + Vector2(0, -r * 0.2)]), Color("b8f6ff"))
