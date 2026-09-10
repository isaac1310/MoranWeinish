"""Query helpers over a decoded Portfolio.fig node tree.

    import nodes; nodes.load('/tmp/figx')       # dir produced by decode.py
    nodes.tree('46:121')                        # print a subtree
"""
import json, os

N = []; BY = {}; KIDS = {}; BLOBS = []

def load(d):
    global N, BY, KIDS, BLOBS
    N = json.load(open(os.path.join(d, 'nodes.json')))
    BY = {gid(n['guid']): n for n in N if n.get('guid')}
    KIDS = {}
    for n in N:
        p = n.get('parentIndex')
        if p: KIDS.setdefault(gid(p['guid']), []).append(n)
    bp = os.path.join(d, 'blobs.json')
    if os.path.exists(bp): BLOBS = [bytes.fromhex(h) for h in json.load(open(bp))]
    return len(N)

def gid(g): return '%s:%s' % (g['sessionID'], g['localID']) if g else None
def name(n): return n.get('name', '')
def pos(n):
    t = n.get('transform') or {}
    return (t.get('m02', 0), t.get('m12', 0))
def size(n):
    s = n.get('size') or {}
    return (round(s.get('x', 0), 1), round(s.get('y', 0), 1))
def kids(i):
    return sorted(KIDS.get(i, []), key=lambda n: n.get('parentIndex', {}).get('position', ''))

def hexc(c):
    if not c: return None
    f = lambda v: format(max(0, min(255, round(v * 255))), '02x')
    s = '#' + f(c.get('r', 0)) + f(c.get('g', 0)) + f(c.get('b', 0))
    a = c.get('a', 1)
    return s if a >= 0.999 else s + ' @%s' % round(a, 2)

def _paints(n, key):
    out = []
    for p in (n.get(key) or []):
        if p.get('visible') is False or p.get('opacity', 1) == 0: continue
        out.append(hexc(p.get('color')) if p.get('type') == 'SOLID' else p.get('type'))
    return out
def fills(n): return _paints(n, 'fillPaints')
def strokes(n): return _paints(n, 'strokePaints')

def text(n): return (n.get('textData') or {}).get('characters')

def tree(i, d=0, maxd=4):
    n = BY.get(i)
    if not n: return
    x, y = pos(n); w, h = size(n)
    t = text(n)
    print('  ' * d + '%r [%s] %s @(%d,%d) %sx%s fill=%s stroke=%s%s'
          % (name(n), n.get('type'), i, round(x), round(y), w, h, fills(n), strokes(n),
             ' ' + repr(t[:40]) if t else ''))
    if d < maxd:
        for k in kids(i): tree(gid(k['guid']), d + 1, maxd)

def find_text(needle, limit=20):
    """Every node whose text contains `needle` (case-insensitive)."""
    out = []
    for n in N:
        t = text(n)
        if t and needle.lower() in t.lower():
            out.append((gid(n['guid']), t[:60]))
            if len(out) >= limit: break
    return out

def frames():
    """Top-level page frames, e.g. 'kkl' 46:121."""
    return [(gid(n['guid']), name(n), size(n)) for n in N
            if n.get('type') == 'FRAME' and name(n) in
            ('main page', 'kkl', 'travel hub', 'bara', 'suzuki', 'contact')]
