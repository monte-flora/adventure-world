from lib import G
W, H = 100, 27
g = G(W, H)
g.rect(2, 1, 9, 97)          # upper corridor
g.rect(12, 1, 21, 90)        # lower tier
g.rect(10, 88, 11, 90)       # shaft through the rock
g.rect(10, 4, 11, 6)         # drop hole upper -> start
# shaft walls
g.rect(10, 87, 11, 87, '#')
g.rect(12, 87, 18, 87, '%')
g.rect(10, 91, 21, 91, '%')
# trapdoor to exit
g.rect(23, 7, 24, 9)
g.set(22, 8, 'G'); g.set(24, 8, 'E')
g.set(21, 2, 'S')
# --- lower section 1: teach vine
g.rect(12, 23, 20, 23, 'V')
g.rect(15, 24, 21, 27, '#')
g.many(13, range(24, 28), '$')
g.many(20, [10, 12, 14], '$'); g.many(18, [17, 19, 21], '$')
g.set(21, 40, 'C')
# --- section 2: pits with swing vines
g.rect(21, 44, 21, 51, '^'); g.rect(12, 46, 18, 46, 'R')
# secret chamber
g.set(22, 32, 'B'); g.rect(23, 29, 24, 35); g.rect(23, 32, 24, 32, 'H'); g.set(24, 34, 'T')
for r, c in [(18, 29), (19, 30), (20, 31), (18, 35), (19, 34), (20, 33)]: g.set(r, c, '$')
g.rect(21, 59, 21, 63, '^'); g.rect(21, 64, 21, 66, '#'); g.rect(21, 67, 21, 72, '^')
g.rect(12, 61, 18, 61, 'R'); g.rect(12, 69, 18, 69, 'R')
g.set(19, 65, '$'); g.many(19, [75, 77], '$')
g.set(21, 80, 'C'); g.many(20, [82, 84], '$')
# --- upper: twist
g.many(7, [92, 94, 96], '$')
g.rect(9, 70, 9, 76, '^'); g.rect(2, 73, 7, 73, 'R')
g.many(8, [71, 75], '$')
g.rect(6, 63, 9, 64, '#'); g.rect(2, 65, 8, 65, 'V'); g.many(4, [63, 64], '$')
g.set(9, 57, 'C'); g.many(8, [60, 59], '$')
# --- finale
g.rect(9, 44, 9, 51, '^'); g.rect(2, 48, 7, 48, 'R'); g.many(7, [45, 47, 50], '$')
g.rect(8, 38, 8, 40, 'B'); g.set(9, 38, 'B'); g.set(9, 39, '*'); g.set(9, 40, 'B')
g.rect(9, 30, 9, 31, '^'); g.many(6, [30, 31], '$')
g.set(9, 17, 'L'); g.many(8, [12, 14], '$')
head = """theme: moss
name: The Weeping Deep
stone: leaf
land: weepingwold
needs: dash
dark: yes
about: Teach: a vine up over a rock wall on safe floor. Test: swinging vines over two spike pits. Twist: wall-jump the % shaft, then swing and climb the upper road. Finale: cross the spikes, dig out the Leaf Stone, pull the lever and drop through the gate home. Secret: a gem arrow points to a cracked floor stone and a chest room below."""
g.save(head, 'out2.txt')
