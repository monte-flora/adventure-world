# Handoff: Wave C1 caves, 2026-11-22 (restart 2)

User's words: "I'll be much more interested in playing once all the new graphics are in place and the
gameplay is more polished. I had some issues navigating the caves because things like the steam blasting
you up is not quite in place."

## Done
- PR #39: goal 1 (cave letters like pygame, one test per letter). Merged.
- PR #45 (branch monte-flora/wave-c1-robot): goal 2. CaveRobot (shadowfall/caves/robot/cave_robot.gd)
  beats stone 1, stone 3, classic 05/07/12 in CI (test_cave_robot.gd, ~15 s). Green; auto-merge.
  Not covered: stone 2 (ropes R + dash), % wall climbs; classic 01/02/03/06/08-11 "no route" from start,
  04 loops at a ladder jump (72 s: keep out of CI). Section in shadowfall/caves/README.md.

## Next (this branch monte-flora/wave-c1-juice, from #45's head; merge origin/phase-2 first)
- Goal 3: cave art in place: art/ cave tilesets, parallax, monster sheets via ArtSheet. art/ is C2's:
  read it, don't edit it; asks go in the report.
- Goal 4: juice: hit-stop, screen shake, dust/spark particles, hurt flash (docs/teen/gameplay §4 table).
- Debug tips: after merging phase-2 run `godot --headless --path shadowfall --import` (new class_names).
  Single test: `--only=<file part>`. Never `cat >` without a heredoc (it hangs on stdin).
