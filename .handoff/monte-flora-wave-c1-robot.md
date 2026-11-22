# Handoff: Wave C1 caves (task_47cbb8938c97), 2026-11-22

User's words: "I'll be much more interested in playing once all the new graphics are in place and the
gameplay is more polished. I had some issues navigating the caves because things like the steam blasting
you up is not quite in place." Goals: 1 letters like pygame + test per letter; 2 real-physics Godot cave
robot beating stone 1-3 + a few classic caves, in CI; 3 cave art (shadowfall/art tilesets, parallax,
monster sheets via ArtSheet); 4 juice (hit-stop, shake, dust/spark, hurt flash; docs/teen/gameplay §4 table).

## Done
- PR #39 (branch monte-flora/wave-c1-caves -> phase-2): goal 1. Table in shadowfall/caves/README.md.
  Geyser steam drawn + 0.4 s fizzle; A/J/M on one pygame clock (78 off/54 on); geyser 7.2 t, mushroom 6 t;
  ladder tops standable (tile "h", physics layer bit 4; climber drops mask); DOWN from ladder top; UP on %;
  * s solid (bump/strike/dig takes); J own block + 2; lava waits 2 s, 1 t/s, stops below E; springs 60 s;
  crumble 54 f; platforms 2 t/s. godot-test 153/153, pytest green locally. Check it merged.

## In flight: branch monte-flora/wave-c1-robot (stacked on #39), WIP, NOT a PR yet
- shadowfall/caves/robot/cave_robot.gd (CaveRobot): BFS over stand-cells (walk/drop/jump/climb/launch),
  presses only h.ix/iy/jump_pressed/held/attack/interact, replans after every move.
- shadowfall/caves/tests/test_cave_robot.gd: stone 1 only so far. FAILS now: it climbs the zigzag "---"
  shaft at x 91-97 to (93,8), then plans "jump (95,10)" (back down) instead of up to (9x,6) on the "==="
  row 7 -> debug moves()/route() from (93,8) (probe: print bot.moves(Vector2i(93,8))). Crumbled ledges:
  it waits 60 f and replans (works).
- Next: fix that, beat stone 1 (lever L opens G near diamond? diamond is B*B at row 6 col 50: _use strikes),
  then stone 3, classic 05/07/10 (no P/U/R). Stone 2 needs ropes R + dash: maybe skip and say so.
  Keep the test runtime small (CI). Then PR into phase-2.
- Goals 3 (art) and 4 (juice) not started. Art asks go to C2 (owns art/).
