from lib import G
W, H = 128, 29
g = G(W, H)
g.rect(2, 1, 9, 124)
g.rect(14, 1, 23, 124)
g.rect(10, 4, 13, 6)
g.rect(25, 7, 26, 9); g.set(24, 8, 'G'); g.set(26, 8, 'E')
g.set(23, 2, 'S')
g.rect(10, 121, 23, 121, 'H')
# teach: crumbly ledges over a safe pit
g.rect(24, 14, 25, 24); g.many(24, [15, 16, 18, 19, 21, 22], '-')
g.many(21, [15, 18, 21], '$'); g.many(22, [6, 8, 10], '$'); 
g.set(23, 38, 'C')
# test: geysers on islands in lava pools
g.rect(24, 40, 24, 43, '~'); g.rect(24, 44, 24, 47, '#'); g.set(24, 46, 'M')
g.rect(24, 48, 24, 52, '~'); g.rect(24, 53, 24, 56, '#'); g.set(24, 55, 'M')
g.rect(24, 57, 24, 61, '~')
g.many(20, [49, 51], '$'); g.many(20, [58, 60], '$')
g.set(23, 64, 'C')
# secret
g.set(24, 32, 'B'); g.rect(25, 29, 26, 35); g.rect(25, 32, 26, 32, 'H'); g.set(26, 34, 'T')
for r, c in [(20, 29), (21, 30), (22, 31), (20, 35), (21, 34), (22, 33)]: g.set(r, c, '$')
# twist: cracked door, swing vine, platform
g.rect(14, 86, 23, 86, '#'); g.rect(22, 86, 23, 86, 'B')
g.rect(24, 91, 25, 98); g.rect(25, 91, 25, 98, '^'); g.rect(14, 93, 20, 93, 'R')
g.rect(24, 106, 25, 113); g.rect(25, 106, 25, 113, '^'); g.rect(24, 105, 24, 114, 'P')
g.many(22, [88, 89], '$'); g.many(22, [102, 103], '$')
# upper lane
g.many(8, [123, 119], '$')
g.set(9, 112, 'C')
g.rect(10, 94, 11, 105); g.rect(11, 94, 11, 105, '^'); g.many(10, [95, 96, 99, 100, 103, 104], '-')
g.set(10, 83, 'M'); g.rect(5, 70, 9, 80, '#'); g.many(3, [72, 75, 78], '$')
g.rect(8, 62, 8, 64, 'B'); g.set(9, 62, 'B'); g.set(9, 63, '*'); g.set(9, 64, 'B')
g.rect(10, 47, 11, 54); g.rect(11, 47, 11, 54, '^'); g.rect(10, 46, 10, 55, 'P')
g.rect(10, 28, 11, 35); g.rect(11, 28, 11, 35, '^'); g.rect(2, 33, 7, 33, 'R')
g.set(9, 18, 'L'); g.many(8, [12, 14], '$')
head = """theme: shadow
name: The Mirefen Maw
stone: moon
land: mirefen
needs: dash, climb, pound, swim, double_jump, flare
dark: yes
about: Finale of the road: every idea once more. Teach: crumbly ledges over a safe pit. Test: geysers across lava pools. Twist: dig the cracked door, swing a vine, ride a stone over spikes. Finale: crumbly ledges over spikes, a geyser to a high ledge, dig out the Moon Stone, ride and swing, then pull the lever and drop through the gate home. Secret: a gem arrow points to a cracked floor stone and a chest room below."""
g.save(head, 'out7.txt')
