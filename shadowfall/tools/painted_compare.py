"""Today's realm screen next to its painting, at gloom 0 and 3 (docs/teen/art/painted_screen/):

    python shadowfall/tools/painted_compare.py B3 [--placeholder] [--out FILE]

Takes 4 shots of the real overworld (a silent Godot window, a few seconds each): today's look
(-- --painted=off) and the painted one, at gloom 0 and 3, with the hero in the screen's middle, and
puts them in a 2 x 2 sheet. --placeholder paints with a fake painting (the layout, blurred and
stamped PLACEHOLDER) instead of levels/polish/realm_<screen>/painted.*: the docs use that one, since
the real painting (made by hand in Gemini) is never committed.
"""

import os
import subprocess
import sys
import tempfile

import gemini_realm as gr
import polish

pygame = polish.pygame
DOCS = os.path.join(gr.ROOT, "docs", "teen", "art", "painted_screen")
VIEW = (960, 540)


def placeholder(screen, root):
    """root/realm_<screen>/painted.png: the screen's layout, blurred, stamped PLACEHOLDER."""
    out = os.path.join(root, "realm_" + screen)
    os.makedirs(out, exist_ok=True)
    subprocess.run([os.environ.get("GODOT", "godot"), "--headless", "--audio-driver", "Dummy", "--path",
                    polish.SHADOWFALL, "res://tools/realm_layout.tscn", "--", screen, out], check=True)
    pic = pygame.image.load(os.path.join(out, "layout.png"))
    pic = pygame.transform.smoothscale(pygame.transform.smoothscale(pic, (120, 68)), gr.SCREEN_PX)
    pygame.font.init()
    stamp = pygame.font.Font(None, 140).render("PLACEHOLDER", True, (255, 255, 255))
    stamp.set_alpha(110)
    pic.blit(stamp, stamp.get_rect(center=(gr.SCREEN_PX[0] // 2, gr.SCREEN_PX[1] // 2)))
    pygame.image.save(pic, os.path.join(out, "painted.png"))


def shot(path, cell, gloom, extra):
    subprocess.run([os.environ.get("GODOT", "godot"), "--audio-driver", "Dummy", "--path", polish.SHADOWFALL,
                    "--", "--scene=overworld", "--shot=" + path, "--cell=%d,%d" % cell, "--gloom=%d" % gloom]
                   + extra, check=True, capture_output=True, timeout=120)


def main(argv):
    screens = [a for a in argv if not a.startswith("--")]
    if len(screens) != 1:
        print(__doc__)
        return 1
    screen = screens[0].upper()
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(DOCS, "compare_%s.jpg" % screen)
    col, row = ord(screen[0]) - 65, int(screen[1:]) - 1
    cell = (col * 30 + 14, row * 17 + 8)                  # the screen's middle square
    tmp = tempfile.mkdtemp(prefix="painted_compare_")
    painted = []
    if "--placeholder" in argv:
        placeholder(screen, tmp)
        painted = ["--polish-root=" + tmp]
    pygame.font.init()
    font = pygame.font.Font(None, 44)
    sheet = pygame.Surface((VIEW[0] * 2, (VIEW[1] + 50) * 2))
    sheet.fill((20, 18, 24))
    for y, gloom in enumerate((0, 3)):
        for x, (label, extra) in enumerate((("today", ["--painted=off"]),
                                            ("painted" + (" (PLACEHOLDER)" if painted else ""), painted))):
            png = os.path.join(tmp, "shot_%d_%d.png" % (x, gloom))
            shot(png, cell, gloom, extra)
            top = y * (VIEW[1] + 50)
            sheet.blit(font.render("%s %s, gloom %d" % (screen, label, gloom), True, (240, 236, 224)),
                       (x * VIEW[0] + 16, top + 12))
            pic = pygame.image.load(png)              # a HiDPI window shoots at 2x
            sheet.blit(pygame.transform.smoothscale(pic, VIEW) if pic.get_size() != VIEW else pic,
                       (x * VIEW[0], top + 50))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    pygame.image.save(pygame.transform.smoothscale(sheet, (sheet.get_width() * 3 // 4, sheet.get_height() * 3 // 4)), out)
    print("Made", os.path.relpath(out, gr.ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
