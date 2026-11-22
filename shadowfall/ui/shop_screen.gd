class_name ShopScreen
extends CanvasLayer
## A trader's wares (rules/shop.gd, rules/data/shop.json): BUY and SELL, paid in gold.
##   var s := ShopScreen.new(); s.trader = "tamsin"; add_child(s); await s.closed
## LEFT/RIGHT: buy or sell. UP/DOWN: pick. JUMP/INTERACT: buy or sell it. ESC (or Leave): go.
## The line under the list says what the thing does, or why you can't have it.

signal closed

const BOX := Rect2(200, 70, 560, 400)

var trader := ""
var selling := false
var cursor := 0
var message := ""
var _title: Label
var _gold: Label
var _list: VBoxContainer
var _about: Label
var _note: Label


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
	_title = UiStyle.label("", "body", UiStyle.LIGHT0, UiStyle.BODY * 2)
	_title.position = BOX.position + Vector2(20, 12)
	add_child(_title)
	_gold = UiStyle.label("", "body", UiStyle.LIGHT0)
	_gold.position = BOX.position + Vector2(BOX.size.x - 140, 20)
	add_child(_gold)
	_list = VBoxContainer.new()
	_list.position = BOX.position + Vector2(24, 76)
	_list.add_theme_constant_override("separation", 4)
	add_child(_list)
	_about = UiStyle.label("", "body", UiStyle.INK6)
	_about.position = BOX.position + Vector2(24, BOX.size.y - 76)
	add_child(_about)
	_note = UiStyle.label("", "body", UiStyle.EMBER3)
	_note.position = BOX.position + Vector2(24, BOX.size.y - 52)
	add_child(_note)
	var hint := UiStyle.label("LEFT/RIGHT buy or sell   UP/DOWN choose   SPACE ok   ESC leave", "small", UiStyle.INK4)
	hint.position = BOX.position + Vector2(16, BOX.size.y - 20)
	add_child(hint)
	refresh()


## The rows on show: [{id, name, price, says, left}], then Leave.
func rows() -> Array:
	var out := []
	if selling:
		for it in RulesData.get_file("shop").get("sell", []):
			out.append({"id": it.id, "name": it.name, "price": int(it.price), "says": "%s (you have %d)" % [it.says, Vitals.count(it.id)], "left": -1})
	else:
		for it in Shop.wares(trader):
			out.append({"id": it.id, "name": it.name, "price": int(it.price), "says": it.says, "left": Shop.stock(trader, it.id)})
	out.append({"id": "", "name": "Leave", "price": 0, "says": "", "left": -1})
	return out


func refresh() -> void:
	var name: String = RulesData.person(trader).get("name", "Trader")
	_title.text = "%s  ·  %s" % [name, "SELL" if selling else "BUY"]
	_gold.text = "%s %d gold" % [UiStyle.COIN, Game.gold]
	for c in _list.get_children():
		c.queue_free()
	var rs := rows()
	cursor = clampi(cursor, 0, rs.size() - 1)
	for i in rs.size():
		var r: Dictionary = rs[i]
		var can: bool = r.id == "" or (Vitals.count(r.id) > 0 if selling else Shop.buy_problem(trader, r.id) == "")
		var text: String = ("> " if i == cursor else "  ") + r.name
		if r.id != "":
			text += "   %d gold" % r.price
			if r.left == 0:
				text += "   sold out"
			elif r.left > 0:
				text += "   (%d left)" % r.left
		_list.add_child(UiStyle.label(text, "body", UiStyle.LIGHT0 if i == cursor else (UiStyle.INK6 if can else UiStyle.INK4)))
	_about.text = rs[cursor].says
	_note.text = message


## Buy (or sell) the thing under the cursor; Leave closes. Returns true if gold changed hands.
func confirm() -> bool:
	var r: Dictionary = rows()[cursor]
	if r.id == "":
		close()
		return false
	var ok: bool
	if selling:
		ok = Shop.sell(r.id)
		message = "Sold." if ok else "You have none to sell."
	else:
		message = Shop.buy_problem(trader, r.id)
		ok = Shop.buy(trader, r.id)
		if ok:
			message = "Yours: %s." % r.name
	Audio.play_sfx("coin" if ok else "menu")
	refresh()
	return ok


func close() -> void:
	closed.emit()
	queue_free()


func press(action: String) -> void:
	match action:
		"move_up", "move_down":
			cursor = posmod(cursor + (1 if action == "move_down" else -1), rows().size())
			message = ""
		"move_left", "move_right":
			selling = not selling
			cursor = 0
			message = ""
		"jump", "interact", "attack":
			confirm()
			return
		"pause":
			close()
			return
	refresh()


func _unhandled_input(event: InputEvent) -> void:
	for a in ["move_up", "move_down", "move_left", "move_right", "jump", "interact", "attack", "pause"]:
		if event.is_action_pressed(a):
			press(a)
			break
	get_viewport().set_input_as_handled()
