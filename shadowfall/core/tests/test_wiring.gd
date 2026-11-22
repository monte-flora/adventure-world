extends TestCase
## B9 wiring: every play screen has the HUD above the dark, and the gloom light.


func _layers(screen: Node) -> Dictionary:
	var out := {}
	for c in screen.get_children():
		if c is GloomLight:
			out["light"] = c
		elif c is CanvasLayer and c.get_script() == preload("res://ui/hud.gd"):
			out["hud"] = c
	return out


func test_play_screens_have_hud_and_light() -> void:
	for s in ["overworld", "cave"]:
		Scenes.goto(s)
		await physics_frames(2)
		var l := _layers(Scenes.screen)
		check(l.has("light"), s + " has the gloom light")
		check(l.has("hud"), s + " has the HUD")
		if l.has("light") and l.has("hud"):
			check(l.hud.layer >= GloomLight.HUD_LAYER and l.hud.layer > l.light.layer, s + ": HUD above the dark")
			check(l.light.lantern != null, s + ": the hero carries the lantern")


func test_dark_cave_is_dark() -> void:
	Scenes.goto("cave", {"text": "theme: stone\ndark: yes\n#####\n#S.E#\n#####"})
	await physics_frames(2)
	check(_layers(Scenes.screen).light.dark, "dark: yes makes the cave dark")


func test_hud_shows_a_taken_stone() -> void:
	Scenes.goto("overworld")
	await physics_frames(1)
	var hud = _layers(Scenes.screen).hud
	Game.take_stone("dawn")
	await frames(3)
	check("1/" in hud.stones.text, "the HUD counts the stone: " + hud.stones.text)


func test_checkpoint_and_stone_save() -> void:
	Scenes.goto("cave", {"text": "theme: stone\nstone: dawn\n########\n#S.C.*E#\n########"})
	await physics_frames(2)
	var cave: CaveScene = Scenes.screen
	check(not Game.has_save(), "no save yet")
	cave.hero.position = cave._cell_spot(Vector2i(3, 1))
	await physics_frames(2)
	check(Game.has_save(), "a checkpoint saves")
	cave.hero.position = cave._cell_spot(Vector2i(5, 1))
	await physics_frames(2)
	Game.reset()
	check(Game.load_save() and Game.has_ability("dash"), "the Stone is in the save")


func test_m_mutes() -> void:
	var was: bool = Audio.muted
	var m := InputEventKey.new()
	m.physical_keycode = KEY_M
	m.pressed = true
	check(InputMap.action_has_event("mute", m), "M is the mute key")
	Scenes._unhandled_input(m)
	check(Audio.muted != was, "M flips the sound")
	Audio.toggle_mute()
	check_eq(Audio.muted, was, "and back")


## The MVP path can be lost: the last heart drops your gold as a Lost Light, you wake at the
## lantern shrine, and touching the Light gives the gold back.
func test_you_can_lose_in_a_cave() -> void:
	Scenes.goto("cave", {"text": "theme: stone\n##########\n#S.C....E#\n##########"})
	await physics_frames(2)
	var cave: CaveScene = Scenes.screen
	cave.hero.position = cave._cell_spot(Vector2i(3, 1))     # light the shrine
	await physics_frames(2)
	var shrine := cave.checkpoint
	cave.hero.position = cave._cell_spot(Vector2i(6, 1))
	await physics_frames(2)
	Game.gold = 7
	Game.hearts = 1
	cave.hurt_hero(cave.hero.position + Vector2(20, 0))
	check_eq(Game.hearts, Game.max_hearts, "hearts come back")
	check_eq(Game.gold, 0, "the gold is dropped")
	check_eq(cave.hero.position, shrine, "you wake at the shrine")
	check(cave.lost_light_spot().x < INF, "a Lost Light waits in this cave")
	cave.hero.iframes = 0
	cave.hero.position = cave.lost_light_spot()
	await physics_frames(2)
	check_eq(Game.gold, 7, "the Lost Light gives the gold back")
	check(Vitals.lost_light().is_empty(), "and is gone")


func test_you_can_lose_in_the_realm() -> void:
	Scenes.goto("overworld")
	await physics_frames(2)
	var ow = Scenes.screen
	var spot: Vector2i = ow.world.home
	for d in [Vector2i.RIGHT, Vector2i.LEFT, Vector2i.DOWN, Vector2i.UP]:
		if ow.world.walkable(ow.world.home + d * 2) and ow.world.at(ow.world.home + d * 2) not in "MSPL":
			spot = ow.world.home + d * 2
			break
	check(spot != ow.world.home, "a square near home")
	ow.hero.place(spot)
	await physics_frames(2)
	Game.gold = 5
	Game.hearts = 1
	check(ow.hero.take_hit(ow.hero.position + Vector2(10, 0)), "the hit lands")
	check_eq(Game.gold, 0, "the gold is dropped")
	check_eq(Game.hearts, Game.max_hearts, "hearts come back")
	check_eq(ow.hero.cell(), ow.respawn, "you wake at the last lantern")
	check_eq(ow.lost_light_cell(), spot, "the Lost Light is where you fell")
	ow.hero.place(spot)
	await physics_frames(2)
	check_eq(Game.gold, 5, "the Lost Light gives the gold back")


func test_lumen_heals_a_heart() -> void:
	Scenes.goto("cave", {"text": "theme: stone\n########\n#S....E#\n########"})
	await physics_frames(20)
	for i in 3:
		Vitals.lumen_hit()
	check_eq(Vitals.lumen_charges(), 1, "3 sword hits fill a charge")
	Game.hearts = Game.max_hearts - 1
	Input.action_press("heal")
	await physics_frames(LumenHeal.HOLD_FRAMES + 5)
	Input.action_release("heal")
	check_eq(Game.hearts, Game.max_hearts, "holding Q heals a heart")
	check_eq(Vitals.lumen_charges(), 0, "and spends the charge")


func test_a_sword_hit_fills_lumen() -> void:
	Scenes.goto("cave", {"text": "theme: stone\n########\n#S.z..E#\n########"})
	await physics_frames(2)
	var cave: CaveScene = Scenes.screen
	var m: CaveMonster = null
	for c in cave.monsters.get_children():
		if c is CaveMonster:
			m = c
	check(m != null, "a monster")
	cave.hero.position = m.position - Vector2(30, 0)
	cave.hero.facing = 1
	Input.action_press("attack")
	await physics_frames(6)
	Input.action_release("attack")
	check(Vitals.lumen() > 0.0, "the hit fills the Lumen meter: %s" % Vitals.lumen())
