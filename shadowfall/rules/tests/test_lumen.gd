extends TestCase
## The Lumen heal: hits fill it, holding still heals, a hit wastes the charge.


func _fill_one_charge() -> void:
	for i in 3:
		Vitals.lumen_hit()


func test_three_sword_hits_fill_a_charge() -> void:
	Vitals.lumen_hit()
	Vitals.lumen_hit()
	check_eq(Vitals.lumen_charges(), 0, "2 hits: not yet")
	Vitals.lumen_hit()
	check_eq(Vitals.lumen_charges(), 1, "3 hits: 1 charge")
	for i in 9:
		Vitals.lumen_hit(true)
	check_eq(Vitals.lumen_charges(), 2, "9 arrow hits: 1 more")
	for i in 30:
		Vitals.lumen_hit()
	check_eq(Vitals.lumen_charges(), 3, "the meter holds 3")


func test_hold_54_frames_heals_one_heart() -> void:
	_fill_one_charge()
	Vitals.hurt()
	var h := LumenHeal.new()
	var healed_at := -1
	for f in 60:
		if h.step(true, true):
			healed_at = f
	check_eq(healed_at, LumenHeal.HOLD_FRAMES, "healed after 54 frames held")
	check_eq(Game.hearts, 5, "+1 heart")
	check_eq(Vitals.lumen_charges(), 0, "the charge is spent")


func test_letting_go_keeps_the_charge_and_a_hit_wastes_it() -> void:
	_fill_one_charge()
	Vitals.hurt()
	var h := LumenHeal.new()
	for f in 20:
		h.step(true, true)
	h.step(false, true)
	check_eq(Vitals.lumen_charges(), 1, "let go: charge back")
	for f in 20:
		h.step(true, true)
	h.hit()
	check_eq(Vitals.lumen_charges(), 0, "hit: charge wasted")
	check_eq(Game.hearts, 4, "and no heal")


func test_no_heal_at_full_hearts() -> void:
	_fill_one_charge()
	var h := LumenHeal.new()
	h.step(true, true)
	check(not h.active, "full hearts: nothing to heal")
	check_eq(Vitals.lumen_charges(), 1, "charge kept")
