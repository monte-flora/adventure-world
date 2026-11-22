import sys
from mini import *
p = int(sys.argv[1]); pw = int(sys.argv[2])
g = G(p+pw+30, 12)
g.rect(2, 1, 7, p+pw+28)
g.set(7, 2, 'S'); g.set(7, p+pw+20, 'E')
g.rect(8, p, 9, p+pw-1); g.rect(9, p, 9, p+pw-1, '^'); g.rect(8, p-1, 8, p+pw, 'P')
print(p,pw,end=' '); run(g, 100)
