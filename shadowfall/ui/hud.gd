extends CanvasLayer
## The HUD, inside the play view (docs/teen/art/README.md): top-left hearts and the Light Stone
## count, top-right gold. It sits above the light layer, so it is never darkened.
## A screen adds it with  add_child(preload("res://ui/hud.tscn").instantiate()).

const LAYER := GloomLight.HUD_LAYER   # above the dark (light/ draws on 50)
const MARGIN := 8
const SIZE := UiStyle.SMALL * 2   # small font at 2×: hearts read clearly

var hearts: Label      # full hearts (ember)
var lost: Label        # emptied hearts (ink3), right after the full ones
var stones: Label
var gold: Label
var _shown := []


func _ready() -> void:
	layer = LAYER
	hearts = _add(UiStyle.EMBER2, Vector2(MARGIN, MARGIN))
	lost = _add(UiStyle.INK3, Vector2(MARGIN, MARGIN))
	stones = _add(UiStyle.LIGHT0, Vector2(MARGIN, MARGIN + SIZE + 4))
	gold = _add(UiStyle.LIGHT0, Vector2.ZERO)
	gold.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	gold.position = Vector2(UiStyle.VIEW.x - MARGIN - 200, MARGIN)
	gold.size.x = 200
	refresh()


func _add(color: Color, pos: Vector2) -> Label:
	var l := UiStyle.label("", "small", color, SIZE)
	l.position = pos
	add_child(l)
	return l


func _process(_delta: float) -> void:
	if _shown != _state():
		refresh()


func _state() -> Array:
	return [Game.hearts, Game.max_hearts, Game.stones.size(), Game.gold]


func refresh() -> void:
	_shown = _state()
	hearts.text = UiStyle.HEART.repeat(maxi(Game.hearts, 0))
	lost.text = UiStyle.HEART.repeat(maxi(Game.max_hearts - Game.hearts, 0))
	hearts.size = Vector2.ZERO
	lost.position.x = MARGIN + (hearts.get_minimum_size().x if Game.hearts > 0 else 0.0)
	stones.text = "%s %d/%d" % [UiStyle.STONE, Game.stones.size(), Game.STONES.size()]
	gold.text = "%s %d" % [UiStyle.COIN, Game.gold]
