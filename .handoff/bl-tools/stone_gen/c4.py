from lib import G
W, H = 132, 29
g = G(W, H)
g.rect(2, 1, 9, 128)
g.rect(14, 1, 23, 128)
g.rect(10, 4, 13, 6)
g.rect(25, 7, 26, 9); g.set(24, 8, 'G'); g.set(26, 8, 'E')
g.set(23, 2, 'S')
g.rect(10, 121, 23, 121, 'H')
# teach: shallow dry pit
g.rect(24, 14, 25, 22); g.rect(24, 13, 24, 23, 'P')
g.many(21, [11, 13, 15], '$'); g.many(21, [18, 20], '$')
g.many(22, [38, 40], '$')
# secret chamber under teach flat
g.set(24, 30, 'B'); g.rect(25, 27, 26, 33); g.rect(25, 30, 26, 30, 'H'); g.set(26, 32, 'T')
for r, c in [(21, 27), (22, 28), (23, 29), (21, 33), (22, 32), (23, 31)]: g.set(r, c, '$')
g.set(23, 36, 'C')
# test: spike pit with platform
g.rect(24, 44, 25, 51); g.rect(25, 44, 25, 51, '^'); g.rect(24, 43, 24, 52, 'P')
g.many(21, [46, 48, 50], '$')
# lift to shelf
g.rect(20, 70, 24, 84, '#')
g.rect(19, 67, 22, 68, 'U')
g.many(18, [70, 72, 74], '$'); g.set(19, 78, 'C')
# twist: lava, two rides, island
g.rect(24, 96, 25, 101); g.rect(25, 96, 25, 101, '~'); g.rect(24, 95, 24, 102, 'P')
g.rect(24, 103, 25, 105, '#')
g.rect(24, 106, 25, 111); g.rect(25, 106, 25, 111, '~'); g.rect(24, 105, 24, 112, 'P')
g.many(21, [98, 100], '$'); g.set(22, 104, '$'); g.many(21, [108, 110], '$')
# upper lane (right to left)
g.many(8, [124, 119], '$')
g.set(9, 112, 'C')
g.rect(10, 96, 11, 103, '~'); g.rect(10, 95, 10, 104, 'P')
g.many(7, [98, 100, 102], '$')
g.rect(6, 70, 9, 81, '#'); g.rect(5, 82, 8, 83, 'U')
g.many(4, [72, 74, 76], '$')
g.rect(8, 62, 8, 64, 'B'); g.set(9, 62, 'B'); g.set(9, 63, '*'); g.set(9, 64, 'B')
g.rect(9, 44, 9, 45, '^'); g.many(6, [44, 45], '$')
g.set(9, 24, 'L'); g.many(8, [30, 34], '$')
head = """theme: crystal
name: The Drowned Bell Road
stone: tide
land: drowned_mere
needs: dash, climb, pound
about: Teach: a sliding stone over a shallow dry pit. Test: a ride over spikes, then a lift up to a shelf. Twist: two rides over a lava pool with an island between, then the ladder up. Finale: ride over lava, lift up the ledge, dig out the Tide Stone, pull the lever and drop through the gate home. Secret: a gem arrow points to a cracked floor stone and a chest room below."""
g.save(head, 'out4.txt')
