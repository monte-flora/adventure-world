import sys
sys.path.insert(0,'.')
from lib import G
exec(open('c4.py').read().split("head =")[0].replace("from lib import G",""))
mode = sys.argv[1]
if mode == 'nopit1':
    g.rect(24,13,25,23,'#')
if mode == 'shortpit2':
    g.rect(24,40,25,53,'#'); g.rect(24,44,25,50); g.rect(25,44,25,50,'^'); g.rect(24,43,24,51,'P')
open('v4_%s.txt'%mode,'w').write(g.text("theme: crystal\nname: t\nabout: x"))
