class G:
    def __init__(s, W, H):
        s.W, s.H = W, H
        s.g = [['#'] * W for _ in range(H)]
    def rect(s, r1, c1, r2, c2, ch='.'):
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                s.g[r][c] = ch
    def set(s, r, c, ch):
        s.g[r][c] = ch
    def many(s, r, cols, ch):
        for c in cols: s.g[r][c] = ch
    def text(s, head):
        return head.strip('\n') + '\n' + '\n'.join(''.join(r) for r in s.g) + '\n'
    def save(s, head, path):
        open(path, 'w').write(s.text(head))
