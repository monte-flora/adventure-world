# shadowfall/art

All Shadowfall art: sprite sheets, tilesets, cave parallax, the Shadowfall 32 palette, the gloom LUT and the pixel fonts. Owned by B-Art (see ../WAVE_B.md). Code draws every asset, and all of it is original. Spec: `docs/teen/art/README.md`. Every size there is **doubled** for the 32-px tile pick.

| What | Command |
|---|---|
| Rebuild everything | `.pixi/envs/default/bin/python shadowfall/art/src/make_all.py` (pygame; about 25 s) |
| Rebuild some monsters | `python shadowfall/art/src/make_monsters.py frost_wolf shade` |
| Check every sheet (palette + cell size) and load each as `SpriteFrames` | `sh shadowfall/tools/run_tests.sh --only=art` (part of `pixi run godot-test`) |

## Use it in Godot
```gdscript
var spr := AnimatedSprite2D.new()
spr.sprite_frames = ArtSheet.frames("hero_side")   # cached, one per sheet
spr.offset = ArtSheet.offset("hero_side")          # puts the feet (JSON origin) on the node
spr.flip_h = facing_left                            # every sheet faces right
spr.play("run")
var t: AtlasTexture = ArtSheet.tile("tiles_moss", "solid_5")   # one tile
var font: Font = load("res://art/font/body.fnt")
```

## Sheet format (`sheets/<name>.png` + `.json`)
`{"image", "kind": "sprite"|"tileset", "cell": [w, h], "origin": [x, y], "anims": {name: {row, col, frames, fps, loop}}}`. Frames run left to right from `col` on `row`. Sprites get one row per animation. A tileset packs tiles 16 to a row. Only Shadowfall 32 colours are used, with alpha 0 or 255. Touchable sprites have a 1-px `ink0` outline. Tiles have no outline.

| Sheet | Cell | Animations |
|---|---|---|
| `hero_side` (hooded wanderer, lantern) | 48×64 | idle 4, run 6, jump 3 (rise/apex/fall), fall 2, land 2, attack 4, air_attack 3, pogo 2, climb 4, wall_slide 1, dash 3, swim 4, lantern_raise 3, hurt 2, death 6 (ends in smoke) |
| `hero_top` | 32×48 | idle/walk/roll/attack × `_down` `_up` `_side`, hurt 2, lantern_raise 3 |
| `shadow_king` (spiked black plate, iron crown, violet eyes, crystal heart, torn rune cloak, greatsword) | 192×256 | idle 4, float 4, cast 6, summon 6, blade 4, hurt 2, fade_out 8 |
| `monster_<id>` (18) | 32, 64 or 96 | move 4, attack 3, hurt 2, poof 4. Realm: thornling, barrow_wight, mere_lurker, frost_wolf, ash_scarab, bog_wisp, umbral_hound. Cave: cave_bat, gloom_slime, bone_crawler, ember_imp, ice_mite, sand_wyrm, mire_toad, shade. Mini-bosses 96: stone_warden, frost_matriarch, cinder_drake |
| `tiles_<theme>` (stone, moss, crystal, lava, frost, sand, swamp, shadow, castle) | 32×32 | `solid_0`–`solid_15` (bits N1 E2 S4 W8 = that neighbour is solid), cracked `B`, ore_diamond `*`, ore_sun `s`, ledge `=`, ledge_crumbly `-`, spikes `^`, spike_trap `A`, fire `!`, lava `~`, chest `T` (closed, open), gem `$`, door `E`, mushroom `o`, ladder `H`, vine `V`, rope `R`, climb_wall `%`, ice `I`, spring `u`, lever `L`, gate `G` (shut, open), flame_jet `J` + flame, geyser `M`, platform `P` `U`, checkpoint / checkpoint_lit `C`, crystal, torch `i`, window `w`, banner `f`, key `K`, light_shard `+`, back_wall, stalactite, tuft, skull |
| `realm_<land>` (emberhold, weepingwold, hollowcrown, drowned_mere, wintermarch, cinder_wastes, mirefen, shadowgate, umbral_reach) | 32×32 | ground_0–2, path_0–2, water + `shore_0`–`shore_14` (same bits; set = water there), tree_top + tree `F`, rock `X`, cliff_face, reeds `B`, bush, house `H`, mine `M`, portal `P`, castle `C`, sign `+`, chest `T`, vent `V`, waystone / waystone_lit `L`, bridge `#`, bridge_broken `=`, gate_ivy `Y`, gate_rubble `O`, gate_thorns `K` |

## Other files
- `palette.png` (32×1, in index order) and `palette.json` (names `ink0`…`shadow2` → hex): Shadowfall 32. Nothing may use a colour outside it.
- `ui/hero_portrait.png` (128×160): the Lanternbearer bust from the concept; the title screen (2×) and the pause JOURNEY tab (1×) show it. `make_hero.py` draws it.
- `ui/shadow_king_portrait.png` (160×200): his bust; the boss intro card (boss/boss.gd, first 4 s). `make_king.py` draws it.
- `gloom_lut.png` (32×4): row = gloom stage 0–3, column = source palette index, and the pixel is the colour it turns into. B3's palette-swap shader reads it. Accents never change.
- `parallax/<theme>_{far,back,mid,front}.png` (960×540): `far` is opaque and scrolls 0×, `back` 0.25× (`ink1`), `mid` 0.5× (`ink2`), `front` 1.4× (`ink0`, ≤15 % of the screen).
- `font/body` (5×7 glyphs, 6×10 cell, ASCII 32–126) and `font/num` (3×5 digits and `+ - / : x %`): each is a PNG grid, a JSON and a BMFont `.fnt` that Godot loads as a `Font`. Draw them at a whole-number scale.
- `src/` (ignored by Godot): the generators. `sfart.py` holds the palette, the sheet packer and the drawing helpers.
