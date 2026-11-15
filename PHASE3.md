# Phase 3: a 3D Adventure World (Godot prototype)

Branch `phase-3`. Asked 2026-11-13. A 3D take on the game in **Godot 4.7** (installed with `brew install --cask godot`; the command is `godot`). It lives in `godot/`, apart from the pygame game, so Classic and Phase 2 are untouched.

## The look
Cartoony, chunky, low-poly, like late-90s 3D platformers: bright flat colors, big simple shapes, a bouncy hero, a friendly follow camera. **Not polished, and not a copy of any existing game**: original characters (the Hero, a young knight, Zombies, Spiders, the Ember Skull, the Shadow King), original places and music.
- Art from code: Godot primitives (boxes, capsules, spheres, cylinders, prisms) with flat or vertex-colored materials, slightly exaggerated proportions. No downloaded asset packs unless the user OKs one.
- Simple shading: Godot's Compatibility or Forward+ renderer, a sun, soft ambient light, no post-processing beyond a little fog for distance.

## First prototype (about one session)
1. The Hero: a chunky character built from primitives. Run with a little momentum, jump, a double jump or long jump, a sword swing. Camera orbits behind him (mouse or arrow keys / Q E).
2. A small hub world: Home Meadow with a house, trees, a pond, hills and a Mine entrance; a few floating platforms and collectible diamonds.
3. One monster you can see: a Zombie that patrols, chases when close, and takes 3 sword hits (or one jump on its head).
4. The Mine leads to a tiny cave level: a few jumps over lava, a lever and a gate, and a diamond at the end.
5. A simple HUD: hearts and diamonds.

## Rules
- PRs target `phase-3`, never `main`. Never open `phase-3` → `main` (a merge to main publishes the pygame game to itch.io).
- Tests: Godot scripts must load headless with no errors (`godot --headless --path godot --quit`), plus a few headless logic tests. 3D screenshots need a window (headless has no renderer).
- Commands go in `pixi.toml` (e.g. `pixi run game3d`) and `godot/README.md`.
