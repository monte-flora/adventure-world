import sys
from mini import *
# floor row 12; stand row 11; air rows 2..11 ; ceiling row 1
floor = sys.argv[1]
W = 12 + len(floor) + 12
g = G(W, 14)
g.rect(2, 1, 11, W-2)
for i,ch in enumerate(floor): g.set(12, 12+i, ch)
g.set(11, 2, 'S'); g.set(11, W-4, 'E')
print(floor, end=' '); run(g, 80)
