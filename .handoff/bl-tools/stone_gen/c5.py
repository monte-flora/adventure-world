from lib import G
W, H = 100, 39
g = G(W, H)
g.rect(4, 1, 9, 94)      # L3
g.rect(12, 9, 17, 94)    # L2
g.rect(20, 9, 25, 94)    # L1
g.rect(28, 1, 33, 94)    # L0
g.rect(10, 4, 27, 6)     # drop shaft
g.rect(35, 8, 36, 10); g.set(34, 9, 'G'); g.set(36, 9, 'E')
g.set(33, 2, 'S')
# S1 right shaft L0 -> L1
g.rect(26, 92, 27, 94)
g.rect(26, 95, 33, 95, '%')
g.rect(26, 91, 27, 91, '#'); g.rect(28, 91, 30, 91, '%')
# S3 right shaft L2 -> L3
g.rect(10, 92, 11, 94)
g.rect(10, 95, 17, 95, '%')
g.rect(10, 91, 11, 91, '#'); g.rect(12, 91, 14, 91, '%')
# S2 left shaft L1 -> L2
g.rect(18, 9, 19, 11)
g.rect(18, 8, 25, 8, '%')
g.rect(18, 12, 19, 12, '#'); g.rect(20, 12, 22, 12, '%')
# ---- L0 teach: ice
g.rect(34, 18, 34, 42, 'I')
g.many(32, [20, 24, 28, 32, 36], '$'); g.many(31, [22, 26, 30, 34], '$')
# secret chamber under flat
g.set(34, 50, 'B'); g.rect(35, 47, 36, 53); g.rect(35, 50, 36, 50, 'H'); g.set(36, 52, 'T')
for r, c in [(29, 47), (30, 48), (31, 49), (29, 53), (30, 52), (31, 51)]: g.set(r, c, '$')
g.set(33, 60, 'C')
g.rect(34, 64, 34, 80, 'I')
g.rect(30, 70, 33, 72, '#'); g.rect(30, 69, 33, 69, '%'); g.rect(30, 73, 33, 73, '%')
g.many(29, [70, 71, 72], '$')
# ---- L1 test (going left): ice with spikes
g.rect(26, 62, 26, 88, 'I')
g.rect(25, 79, 25, 80, '^'); g.rect(25, 70, 25, 72, '^')
g.many(23, [84, 75, 66], '$')
g.rect(26, 28, 26, 58, 'I')
g.rect(25, 48, 25, 50, '^'); g.rect(25, 38, 25, 39, '^')
g.many(23, [54, 43, 33], '$')
g.set(25, 20, 'C')
# ---- L2 twist (going right): ice + climb barriers
g.rect(18, 14, 18, 30, 'I'); g.rect(17, 24, 17, 25, '^')
g.rect(14, 34, 17, 35, '#'); g.rect(14, 34, 17, 34, '%')
g.rect(18, 38, 18, 56, 'I'); g.rect(17, 46, 17, 48, '^')
g.rect(14, 60, 17, 61, '#'); g.rect(14, 60, 17, 60, '%'); g.rect(14, 61, 14, 61, '#')
g.many(13, [34, 35, 60, 61], '$'); g.many(15, [40, 52], '$')
g.set(17, 80, 'C')
# ---- L3 finale (going left)
g.many(7, [90, 86], '$')
g.rect(10, 56, 10, 82, 'I'); g.rect(9, 74, 9, 75, '^')
g.rect(8, 64, 8, 66, 'B'); g.set(9, 64, 'B'); g.set(9, 65, '*'); g.set(9, 66, 'B')
g.rect(10, 24, 10, 50, 'I'); g.rect(9, 44, 9, 46, '^'); g.rect(9, 32, 9, 33, '^')
g.many(7, [45, 33], '$')
g.set(9, 16, 'L')
head = """theme: crystal
name: The Wintermarch Climb
stone: frost
land: wintermarch
needs: dash, climb, pound, swim
about: Teach: an icy floor with nothing to hurt you, then a wall-jump shaft up. Test: sliding ice between spikes. Twist: icy road with rock walls to climb. Finale: slide the top road, dig out the Frost Stone, pull the lever and drop the long shaft past the gate home. Secret: a gem arrow points to a cracked floor stone and a chest room below."""
g.save(head, 'out5.txt')
