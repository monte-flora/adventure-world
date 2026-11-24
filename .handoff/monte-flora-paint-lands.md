# Handoff: paint every land (task_eefd0707008b), 2026-11-23 ~7:15 pm ET

User's words: "Can we finish the rest of Emberhold too like the weepingwillow land or whatever and any other places on the main overworld map?"

## PRs into phase-2
- #78 merged: gemini-next `is_ground()` (`<land>_ground_<x>`).
- #81 merged: painted crags/gates/water (RealmProps.scatter, ground roles, `paint:`/`forest:`/`crags:` lines, ripple). 8 prompts: crag ivy_cliff rubble_heap shadow_thorns riven_boulder ground_cliff ground_deep_water ground_forest_floor.
- #82 open (monte-flora/paint-lands-1): Weepingwold + Hollowcrown, 17 prompts (8 + 9, listed in the PR body), plus the reachability test, placeholder `like`/ground_colors, painted sea.

## PAUSED by the user, 2026-11-23 (evening ET). Do not resume until the coordinator says so.
- Merged: #78 #81 #82. #83 open (Mere + Wintermarch, 20 prompts). It may auto-merge on its own.
- Branch monte-flora/paint-lands-3 (off paint-lands-2): Cinder Wastes + Mirefen. A sonnet subagent was stopped mid-way; its partial WIP is in the WIP commit.
  On resume: check `git show --stat HEAD`, finish it (the same brief as Mere/Wintermarch: prompts cinder_wastes_*/mirefen_*, assets.json, placeholders, level props, before/after pairs cinder_e4 135,59 / cinder_f3 165,42 / cinder_e5 135,76 / mirefen_a4 15,59 / mirefen_b5 45,76 / mirefen_c5 75,76).
  Then move the test_props "stays on tiles" sample to the Shadowgate, run both suites and open the PR.
  The before shots may be partial: retake them from origin/phase-2 in a temp worktree if needed.

## Earlier plan
- Branch monte-flora/paint-lands-2 (off paint-lands-1): Mere + Wintermarch, done by a sonnet subagent (same brief as #82).
  Mere: the test_props "sea stays on tiles" check must move to an unpainted land.
- Then: Cinder + Mirefen, then Shadowgate + Umbral Reach. Umbral: nightfall is mirror() of the light realm, and lands["nightfall"] has no file.
  To paint it: add ground/paint/forest/crags/props from 9_umbral_reach.txt in mirror(). RealmGround is built only when realm == "light", and scatter/painted() skip world.nightfall.
  When every light land is painted, test_realm_art_per_land's "forest square outside painted lands" check must change.
- Pair images: scratchpad pair.py (before | after, 400 px each) into docs/teen/art/lands/<land>_<screen>.png.
- Final: worker_done with the PR numbers and the prompt list per land.
