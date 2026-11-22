extends TestCase
## P1 prototype: the painted Emberhold screen loads, and the hero can't walk through a house.


func _screen() -> PaintedScreen:
	var s: PaintedScreen = load("res://painted/painted.tscn").instantiate()
	add_child(s)
	return s


func test_loads() -> void:
	var s := _screen()
	await physics_frames(2)
	check(s.hero != null and s.hero.is_inside_tree(), "the hero is on the screen")
	check_eq(s.people.size(), 6, "people standing where the painting had them")
	check(s.sorted.y_sort_enabled and s.sorted.get_node_or_null("house_blue") != null, "y-sorted roof piece")
	s.queue_free()
	await frames(1)


func test_house_blocks() -> void:
	var s := _screen()
	check(s.blocked(Rect2(590, 140, 20, 20)), "the blue house is solid")
	check(not s.blocked(Rect2(470, 330, 20, 20)), "the open ground by the fire is not")
	s.hero.position = Vector2(596, 200)     # just below the blue house's door
	s.hero.drive = Vector2.UP
	await physics_frames(60)
	check(s.hero.position.y >= 184.0 + PaintedHero.HALF.y - 0.5, "stopped at the house wall, y=%f" % s.hero.position.y)
	s.hero.drive = Vector2.LEFT
	await physics_frames(20)
	check(s.hero.position.x < 590.0, "still walks along the wall")
	s.queue_free()
	await frames(1)
