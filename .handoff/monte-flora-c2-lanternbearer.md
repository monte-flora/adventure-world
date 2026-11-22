# Handoff: Lanternbearer + Shadow King redraws, 2026-11-22

## Done
- PR #46 merged (task_d6243cc65949): pause SOUND tab "Screen shake" row + ui test; rules/names.gd realm ids in LAND,
  SUNFANG, LIEUTENANT (Vargoth the Thornwarden, Ysmera the Loom Widow, ...); boss/ reads Names directly
  (Castle.display removed); frost_matriarch redrawn (crowned ice spider, frost-breath attack).
- This branch (monte-flora/c2-lanternbearer, WIP, no PR yet): concepts committed to docs/teen/art/ref/;
  art/src/make_hero.py side() rewritten to the concept (midnight hood water0-2, ink0 face + ink6/7 eyes, long torn
  cloak streaming with `sway`, leather earth0-2 + mail ink2/3 checker, steel pauldron + vambrace, ember sash with tail,
  caged lantern on the belt swinging; `lamp_hand=True` puts it in the hand, used by lantern_raise). sheets/hero_side.png
  rebuilt. sword() has a `runes=` flag (Sunfang ember runes) not yet used anywhere.

## Next (coordinator msgs msg_dc2babfb850b, msg_b832550a8c75; user: "as close to this as we can get")
1. Polish side: pauldron reads as a grey ball on the chest; make it a shoulder plate (flatter, over the arm top).
2. Rewrite top() (32x48, down/up/side) in the same style; rebuild: `cd shadowfall/art/src && SDL_VIDEODRIVER=dummy <py> -c "import make_hero as m; m.main()"`.
3. Large portrait ~128x160 from the concept (new art/sheets or art/ui png, Shadowfall 32 only), wire into ui/title.gd and ui/pause.gd (small).
4. Screenshots 1x and 2x beside the concept (scratch zoom: pygame scale of sheet crops). `sh shadowfall/tools/run_tests.sh` (ArtCheck) + pytest. PR into phase-2.
5. Then a separate PR: Shadow King (art/src/make_king.py, 192x256 all phase anims) to docs/teen/art/ref/shadow_king_concept.jpg
   (spiked black plate, jagged iron crown + violet gem, faceless helm with violet eyes, violet crystal heart + belt gem, torn
   violet/black rune-trim cloak, jagged black greatsword w/ violet gem, gauntlet with violet wisps, soft aura; shadow ramp + ink;
   violet the brightest) + portrait ~160x200 for boss intro/title card.
6. worker_done (task_d6243cc65949, dispatch ctx_e26f7203c01c) with all PR numbers.
- py = /Users/montgomeryflora/noah-adventure/.pixi/envs/default/bin/python. Sunfang runes: not wired (no Sunfang hero sheet yet); note as ask.
