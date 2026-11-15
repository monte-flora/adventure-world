extends Node
## The game's memory (an autoload called `Game`): hearts, diamonds, and travel between levels.

signal changed                       # hearts or diamonds changed
signal message(text: String)         # a short line for the HUD
signal travel_requested(level: String, spawn: String)

const MAX_HEARTS := 3
const TOTAL_DIAMONDS := 10

var hearts := MAX_HEARTS
var diamonds := 0
var collected := {}   # diamond id -> true, so a diamond stays collected when you come back


func reset() -> void:
	hearts = MAX_HEARTS
	diamonds = 0
	collected.clear()
	changed.emit()


func has_collected(id: String) -> bool:
	return collected.has(id)


## Returns true if this diamond was new.
func collect_diamond(id: String) -> bool:
	if collected.has(id):
		return false
	collected[id] = true
	diamonds += 1
	changed.emit()
	if diamonds == TOTAL_DIAMONDS:
		say("All %d diamonds! Hooray!" % TOTAL_DIAMONDS)
	return true


## Takes away a heart. Returns true when the hearts ran out (they fill up again).
func lose_heart() -> bool:
	hearts -= 1
	var ran_out := hearts <= 0
	if ran_out:
		hearts = MAX_HEARTS
	changed.emit()
	return ran_out


func say(text: String) -> void:
	message.emit(text)


func travel(level: String, spawn: String) -> void:
	travel_requested.emit(level, spawn)
