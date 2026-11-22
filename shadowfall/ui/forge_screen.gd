class_name ForgeScreen
extends CanvasLayer
## The blacksmith's forge (rules/forge.gd): your blade, the next tier and its price; then 3 hammer
## strikes on the timing bar (a marker sweeps to and fro; strike as it crosses the glowing middle).
##   var f := ForgeScreen.new(); add_child(f); await f.closed
## JUMP/INTERACT/ATTACK: start, then strike. ESC: leave. Any Miss and the metal cools (nothing spent).

signal closed

const BOX := Rect2(200, 90, 560, 360)
const BAR := Rect2(260, 300, 440, 24)
const SWEEP := 1.1                      # s for the marker to cross the bar once

var hammering := false
var strikes: Array = []                 # where each strike stopped (0..1)
var marker := 0.0
var result := ""                        # the last forge's result: done, perfect, cooled, can't
var _t := 0.0
var _info: Label
var _note: Label
var _bar: Control


func _ready() -> void:
	layer = GloomLight.HUD_LAYER + 15
	process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(UiStyle.INK0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var panel := Panel.new()
	panel.theme = UiStyle.theme()
	panel.position = BOX.position
	panel.size = BOX.size
	add_child(panel)
	var title := UiStyle.label("THE FORGE", "body", UiStyle.LIGHT0, UiStyle.BODY * 2)
	title.position = BOX.position + Vector2(20, 12)
	add_child(title)
	_info = UiStyle.label("", "body", UiStyle.INK6)
	_info.position = BOX.position + Vector2(24, 70)
	add_child(_info)
	_note = UiStyle.label("", "body", UiStyle.EMBER3)
	_note.position = BOX.position + Vector2(24, 250)
	add_child(_note)
	_bar = Control.new()
	_bar.draw.connect(_draw_bar)
	add_child(_bar)
	var hint := UiStyle.label("SPACE start / strike   ESC leave", "small", UiStyle.INK4)
	hint.position = BOX.position + Vector2(16, BOX.size.y - 20)
	add_child(hint)
	refresh()


func refresh() -> void:
	var t := Forge.tier()
	var lines := ["Your blade: %s (%d damage)" % [Forge.blade_name(), Forge.sword_damage()]]
	if t < Forge.SUNFANG_TIER:
		var next := "Next: %s (%d damage)" % [Forge.TIER_NAME[t + 1], Forge.DAMAGE[t + 1]]
		if t < Forge.SUNFANG_TIER - 1:
			next += ", for %d sun ore and %d gold" % [Forge.ORE_COST[t], Forge.GOLD_COST[t]]
		else:
			next += ", from the seven Light Stones"
		lines.append(next)
	lines.append("You carry %d sun ore and %d gold." % [Vitals.count("sun_ore"), Game.gold])
	if Forge.crit_chance() > 0.0:
		lines.append("A perfect temper: %d%% to strike true." % roundi(Forge.crit_chance() * 100))
	_info.text = "\n".join(lines)
	var why := Forge.problem()
	if hammering:
		_note.text = "Strike %d of %d!" % [strikes.size() + 1, Forge.STRIKES]
	elif result == "perfect":
		_note.text = "Perfect! The steel sings. Your strikes land truer."
	elif result == "done":
		_note.text = "The steel takes the temper. %s." % Forge.blade_name()
	elif result == "cooled":
		_note.text = "A miss. The metal cools; nothing is lost. Try again."
	else:
		_note.text = why if why != "" else "Press SPACE to heat the steel."
	_bar.queue_redraw()


## Start hammering (if the forge can take your blade). Returns false if it can't.
func begin() -> bool:
	if Forge.problem() != "":
		Audio.play_sfx("menu")
		refresh()
		return false
	hammering = true
	strikes = []
	_t = 0.0
	result = ""
	refresh()
	return true


## One hammer blow with the marker at pos (0..1). The 3rd blow forges.
func strike(pos := -1.0) -> String:
	if not hammering:
		return ""
	strikes.append(marker if pos < 0.0 else pos)
	Audio.play_sfx("hit")
	var g := Forge.grade(strikes[-1])
	if strikes.size() >= Forge.STRIKES or g == "miss":
		hammering = false
		while strikes.size() < Forge.STRIKES:
			strikes.append(0.0)                 # a miss ends it at once
		result = Forge.forge(strikes)
		Audio.play_sfx("stone" if result == "perfect" else ("select" if result == "done" else "menu"))
	refresh()
	return g


func _process(delta: float) -> void:
	if hammering:
		_t += delta
		marker = pingpong(_t / SWEEP, 1.0)
		_bar.queue_redraw()


func _draw_bar() -> void:
	_bar.draw_rect(BAR, UiStyle.INK2)
	var mid := BAR.position.x + BAR.size.x * 0.5
	var good := BAR.size.x * Forge.GOOD_WINDOW
	var perfect := BAR.size.x * Forge.PERFECT_WINDOW
	_bar.draw_rect(Rect2(mid - good, BAR.position.y, good * 2, BAR.size.y), Color("7a1c2e"))
	_bar.draw_rect(Rect2(mid - perfect, BAR.position.y, perfect * 2, BAR.size.y), UiStyle.LIGHT0)
	_bar.draw_rect(BAR, UiStyle.INK4, false)
	for i in strikes.size():                    # where each blow landed
		var x := BAR.position.x + BAR.size.x * float(strikes[i])
		_bar.draw_line(Vector2(x, BAR.position.y - 4), Vector2(x, BAR.end.y + 4), UiStyle.INK6, 2)
	if hammering:
		var x := BAR.position.x + BAR.size.x * marker
		_bar.draw_rect(Rect2(x - 2, BAR.position.y - 8, 4, BAR.size.y + 16), UiStyle.LIGHT1)


func close() -> void:
	closed.emit()
	queue_free()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		close()
	elif event.is_action_pressed("jump") or event.is_action_pressed("interact") or event.is_action_pressed("attack"):
		if hammering:
			strike()
		else:
			begin()
	get_viewport().set_input_as_handled()
