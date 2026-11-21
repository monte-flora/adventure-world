class_name TestCase
extends Node
## Base for a test file (class TestCase). Put files named test_*.gd in a tests/ folder inside your own area
## (caves/tests/test_ledges.gd). Each func test_*() is one test; it may await.

var failures: PackedStringArray = []


func check(ok: bool, what: String) -> void:
	if not ok:
		failures.append(what)


func check_eq(got, want, what: String) -> void:
	if got != want:
		failures.append("%s: got %s, want %s" % [what, str(got), str(want)])


func physics_frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame
