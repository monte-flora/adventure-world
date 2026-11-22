import sys, time
sys.path.insert(0, "/Users/montgomeryflora/orca/workspaces/noah-adventure/wave-bl-levels")
import cave_solver
def probe(path, r, c, tl=150):
    lines = open(path).read().split('\n')
    i = next(k for k,l in enumerate(lines) if not ':' in l[:14] and l.startswith('#'))
    rows = [list(l) for l in lines[i:] if l]
    for row in rows:
        for k,ch in enumerate(row):
            if ch in '*LE': row[k]='.'
            if ch=='G': row[k]='#'
            if ch=='T': row[k]='.'
    rows[r][c]='E'
    t = "theme: crystal\nname: t\nabout: x\n" + '\n'.join(''.join(x) for x in rows) + '\n'
    t0=time.time()
    res = cave_solver.check(t, time_limit=tl)
    print(path, (r,c), {k: res[k] for k in ("exit","stuck_at","gave_up","seconds","tries")}, round(time.time()-t0), flush=True)
if __name__ == "__main__":
    probe(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv)>4 else 150)
