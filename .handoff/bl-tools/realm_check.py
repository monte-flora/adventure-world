"""Check levels/realm: every land file stitches into 180x85 with no overlap, and the ability order holds:
with the stones of lands 1..k-1 you reach land k's stone Mine (and its waystone), but not land k+1's.
Reads the files themselves (not the generator's json)."""
import os, sys, glob
from collections import deque

SW, SH = 30, 17
ORDER = ["emberhold", "weepingwold", "hollowcrown", "drowned_mere", "wintermarch", "cinder_wastes", "mirefen"]
ABILITY = dict(emberhold="dash", weepingwold="climb", hollowcrown="pound", drowned_mere="swim",
               wintermarch="double_jump", cinder_wastes="flare", mirefen="truesight")
LETTER_NEEDS = {"Y": "climb", "O": "pound", "W": "swim", "K": "flare"}
BLOCK = set("X")
LETTERS = set("GFXIBLTSMR+HWPV#YOKC")

def read(path):
    head, rows = {}, []
    for line in open(path).read().splitlines():
        if not rows and ":" in line:
            k, v = line.split(":", 1)
            head.setdefault(k.strip(), []).append(v.strip())
        elif line:
            rows.append(line)
    return head, rows

grid = [[None] * 180 for _ in range(85)]
owner = [[None] * 180 for _ in range(85)]
gates, mines, way, home, errors = {}, {}, {}, None, []
for path in sorted(glob.glob("levels/realm/[1-8]_*.txt")):
    head, rows = read(path)
    land = head["land"][0]
    top, left = map(int, head["at"][0].split())
    if len({len(r) for r in rows}) != 1:
        errors.append(path + ": rows differ in length")
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            if ch not in LETTERS:
                errors.append("%s: unknown letter %r" % (path, ch))
            R, C = top + r, left + c
            if owner[R][C]:
                errors.append("%s overlaps %s at %d %d" % (land, owner[R][C], R, C))
            grid[R][C], owner[R][C] = ch, land
            if ch == "L":
                way.setdefault(land, []).append((R, C))
    for m in head.get("mine", []):
        f, r, c = m.rsplit(" ", 2)
        R, C = top + int(r), left + int(c)
        if grid[R][C] not in "MS":
            errors.append("%s: mine %s not on M/S" % (land, f))
        if not os.path.exists(os.path.join("levels", f)):
            errors.append("%s: no file %s" % (land, f))
        mines[f] = (R, C, land)
    for g in head.get("gate", []):
        name_r_c, ab = g.rsplit(" ", 1)
        _, r, c = name_r_c.rsplit(" ", 2)
        gates[(top + int(r), left + int(c))] = ab
    if "home" in head:
        r, c = map(int, head["home"][0].split())
        home = (top + r, left + c)
        if grid[home[0]][home[1]] != "H":
            errors.append("home not on H")
holes = [(r, c) for r in range(85) for c in range(180) if grid[r][c] is None]
if holes:
    errors.append("%d squares no land draws, e.g. %s" % (len(holes), holes[:3]))

def reach(abilities):
    seen, q = {home}, deque([home])
    while q:
        r, c = q.popleft()
        for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            R, C = r + dr, c + dc
            if not (0 <= R < 85 and 0 <= C < 180) or (R, C) in seen:
                continue
            ch = grid[R][C]
            if (R, C) in gates:
                if gates[(R, C)] not in abilities:
                    continue
            elif ch in BLOCK or (ch in LETTER_NEEDS and LETTER_NEEDS[ch] not in abilities):
                continue
            seen.add((R, C)); q.append((R, C))
    return seen

def scr(p):
    return p[1] // SW, p[0] // SH

stone = {land: next(p for f, p in mines.items() if f.startswith("stone/") and p[2] == land) for land in ORDER}
have = set()
for i, land in enumerate(ORDER):
    seen = reach(have)
    s = stone[land][:2]
    if s not in seen:
        errors.append("with %s: can't reach the %s stone Mine" % (sorted(have), land))
    if not any(w in seen for w in way.get(land, [])):
        errors.append("with %s: can't reach the %s waystone" % (sorted(have), land))
    if len(way.get(land, [])) != 1:
        errors.append("%s: %d waystones (want 1)" % (land, len(way.get(land, []))))
    else:
        (a, b), (x, y) = scr(way[land][0]), scr(s)
        if abs(a - x) + abs(b - y) < 2:
            errors.append("%s: stone Mine only %d screen from the waystone" % (land, abs(a - x) + abs(b - y)))
    if i + 1 < len(ORDER) and stone[ORDER[i + 1]][:2] in seen:
        errors.append("with %s: the %s stone Mine is reachable too early" % (sorted(have), ORDER[i + 1]))
    have.add(ABILITY[land])
seen = reach(have)
for f, (r, c, land) in mines.items():
    if (r, c) not in seen:
        errors.append("with every ability: can't reach mine %s" % f)
portal = [(r, c) for r in range(85) for c in range(180) if grid[r][c] == "P"]
if len(portal) != 1 or portal[0] not in seen or portal[0] in reach(have - {"truesight"}):
    errors.append("Portal: want 1, reachable only with truesight: %s" % portal)
side = sorted(f for f in mines if f.startswith("caves/"))
print("%d mines (%d side caves), %d gates" % (len(mines), len(side), len(gates)))
# the Umbral Reach
head, rows = read("levels/realm/9_umbral_reach.txt")
if len({len(r) for r in rows}) != 1 or (len(rows), len(rows[0])) != (3 * SH, 3 * SW):
    errors.append("umbral: want 51 x 90")
start = next((r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == "P")
seen, q = {start}, deque([start])
while q:
    r, c = q.popleft()
    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        R, C = r + dr, c + dc
        if 0 <= R < len(rows) and 0 <= C < len(rows[0]) and (R, C) not in seen and rows[R][C] not in "XW":
            seen.add((R, C)); q.append((R, C))
for m in head["mine"] + head["castle"]:
    f, r, c = m.rsplit(" ", 2)
    if (int(r), int(c)) not in seen or not os.path.exists(os.path.join("levels", f)):
        errors.append("umbral: can't reach %s" % f)
print("\n".join(errors) or "realm OK")
sys.exit(1 if errors else 0)
