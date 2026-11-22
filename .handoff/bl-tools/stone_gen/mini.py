import sys, time
sys.path.insert(0, "/Users/montgomeryflora/orca/workspaces/noah-adventure/wave-bl-levels")
import cave_solver
from lib import G
def run(g, tl=100):
    t = g.text("theme: crystal\nname: t\nabout: x")
    t0=time.time()
    r = cave_solver.check(t, time_limit=tl)
    print({k: r[k] for k in ("exit","stuck_at","gave_up","seconds","tries")}, round(time.time()-t0))
if __name__ == "__main__":
    pw = int(sys.argv[1]); 
    g = G(40+pw, 12)
    g.rect(2, 1, 7, 38+pw)
    g.set(7, 2, 'S'); g.set(7, 36+pw, 'E')
    g.rect(8, 10, 9, 10+pw-1); g.rect(9, 10, 9, 10+pw-1, '^'); g.rect(8, 9, 8, 10+pw, 'P')
    run(g)
