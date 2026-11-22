class_name LumenHeal
extends RefCounted
## The Lumen heal in progress: hold Q, standing still, for HOLD_FRAMES physics frames to heal
## 1 heart. Starting spends a charge; letting go early gives it back; a hit wastes it.
## Use: var h := LumenHeal.new(); each physics frame h.step(holding, standing_still); on a hit h.hit().

const HOLD_FRAMES := 54

var frames := 0
var active := false


## One physics frame. Returns true on the frame the heart is healed.
func step(holding: bool, standing_still: bool) -> bool:
	if not active:
		if holding and standing_still and Vitals.spend_lumen_charge():
			active = true
			frames = 0
		return false
	if not holding or not standing_still:
		Vitals.refund_lumen_charge()
		active = false
		return false
	frames += 1
	if frames >= HOLD_FRAMES:
		active = false
		Vitals.heal(1)
		return true
	return false


## You were hit while healing: the heal stops and the charge is lost.
func hit() -> void:
	active = false
	frames = 0


func progress() -> float:
	return float(frames) / HOLD_FRAMES if active else 0.0
