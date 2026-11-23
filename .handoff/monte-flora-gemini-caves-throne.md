# gemini-caves throne (step 3), WIP: paused at 50% usage

Task: task_375b9cb3ad8a (gemini-caves). Steps 1 and 3 only (step 2 went to the lands worker; don't touch shadowfall/realm/ or levels/realm/).

## Done
- PR #79 (branch monte-flora/gemini-caves-1, into phase-2): `pixi run gemini-caves`. Local pytest 758 passed (2 local test_web ffmpeg errors), Godot 223 passed. CI was pending at pause; auto-merge runs on green. If green but not merged after a minute: gh run rerun <pull_request Tests run id>.

## In flight (this branch, monte-flora/gemini-caves-throne, stacked on gemini-caves-1)
- levels/polish/throne_room/throne_room.txt (30x17 hall map: ceiling, walls, floor rows 14-16) + prompt.txt (hand-written throne-hall words; gemini-caves keeps it).
- gemini_caves.py: throne_room comes last; export(name, path, levels, run_cmd). tests/test_gemini_caves.py: 7 pass.
- boss/boss.gd: THRONE_ROOM painting (CaveArt.painting) as a Sprite2D at z -2 behind `stage`, painted_material from GloomLight; _draw_hall skipped when painted; painting hidden in phase 3 (the void). NOT yet run in Godot.

## Next
1. Godot test in shadowfall/boss/tests/test_boss.gd: fake painting via CaveArt.polish_root (see caves/tests/test_cave_painting.gd _fake_painting, folder "throne_room"): painting shown, behind stage, material == light.painted_material, hidden once fight.phase = 3; no painting -> null. And a test that throne_room.txt '#' cells == ThroneFight solids (cell centres) for phases 1-2.
2. sh shadowfall/tools/run_tests.sh + full pytest; add a line to levels/polish/README.txt (throne room last).
3. After #79 merges: merge origin/phase-2 into this branch, push, PR into phase-2, gh pr checks N --watch.
4. worker_done: PRs #79 + new; not verified: real Gemini paste/download, osascript clipboard.
