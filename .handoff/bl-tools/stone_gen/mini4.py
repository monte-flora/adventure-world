import sys
from mini import *
pw, rc, ln = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
W = 60
g = G(W, 14)
g.rect(2, 1, 9, W-2)
p = 20
g.rect(10, p, 11, p+pw-1); g.rect(11, p, 11, p+pw-1, '^')
g.rect(2, rc, 1+ln, rc, 'R')
g.set(9, 50, 'S'); g.set(9, 6, 'E')
print(sys.argv[1:], end=' '); run(g, 60)
