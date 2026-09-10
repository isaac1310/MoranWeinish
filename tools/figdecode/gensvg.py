"""Emit a Figma frame subtree as one self-contained inline SVG.

The seven TravelHub screens are drawn in Figma, not exported images, so there
was nothing to copy into assets/. Every node's position, size, fill, radius,
text and vector geometry is in the decoded file, so the frame can be rebuilt
exactly. SVG (rather than positioned divs) means it scales to any size with a
viewBox and stays crisp.
"""
import os, sys, html, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nodes as _n
from nodes import kids, gid, name, size, pos

def BY_(i):
    return _n.BY.get(i)
from path import parse as parse_path

IMAGES = {}   # figma image hash -> site path

def hexa(c, extra_op=1.0):
    if not c: return None, 1.0
    f = lambda v: format(max(0, min(255, round(v * 255))), '02x')
    a = c.get('a', 1) * extra_op
    return '#' + f(c.get('r', 0)) + f(c.get('g', 0)) + f(c.get('b', 0)), round(a, 3)

def solid(paints):
    """First visible solid/gradient paint -> (css-ish fill, opacity, gradient-def or None)."""
    for p in (paints or []):
        if p.get('visible') is False: continue
        op = p.get('opacity', 1)
        if op == 0: continue
        if p.get('type') == 'SOLID':
            col, a = hexa(p.get('color'), op)
            return col, a, None
        if p.get('type', '').startswith('GRADIENT'):
            return None, 1.0, p
        if p.get('type') == 'IMAGE':
            h = ''.join(format(b, '02x') for b in (p.get('image') or {}).get('hash', []))
            if h in IMAGES: return ('IMG:' + IMAGES[h]), op, None
    return None, 1.0, None

FW = {'Thin':100,'ExtraLight':200,'Light':300,'Regular':400,'Medium':500,
      'SemiBold':600,'Bold':700,'ExtraBold':800,'Black':900}

class Ctx:
    def __init__(self): self.defs = []; self.n = 0
    def grad(self, p, x, y, w, h):
        self.n += 1
        gid_ = 'g%d' % self.n
        stops = []
        for s in (p.get('stops') or []):
            col, a = hexa(s.get('color'), p.get('opacity', 1))
            stops.append('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>'
                         % (round(s.get('position', 0), 3), col, a))
        m = p.get('transform') or {}
        if p.get('type') == 'GRADIENT_RADIAL':
            self.defs.append('<radialGradient id="%s">%s</radialGradient>' % (gid_, ''.join(stops)))
        else:
            dx, dy = m.get('m00', 1), m.get('m10', 0)
            ang = math.atan2(-dy, dx)
            x1, y1 = 0.5 - math.cos(ang) / 2, 0.5 + math.sin(ang) / 2
            x2, y2 = 0.5 + math.cos(ang) / 2, 0.5 - math.sin(ang) / 2
            self.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                             % (gid_, round(x1,3), round(y1,3), round(x2,3), round(y2,3), ''.join(stops)))
        return 'url(#%s)' % gid_

def rr(n):
    ks = ['rectangleTopLeftCornerRadius','rectangleTopRightCornerRadius',
          'rectangleBottomRightCornerRadius','rectangleBottomLeftCornerRadius']
    vs = [n.get(k) for k in ks]
    if any(v is not None for v in vs): return max(v or 0 for v in vs)
    return n.get('cornerRadius') or 0

def to_d(cmds, dx=0, dy=0):
    p = []
    for op, v in cmds:
        if op == 'Z': p.append('Z'); continue
        nums = [round(v[i] + (dx if i % 2 == 0 else dy), 2) for i in range(len(v))]
        p.append(op + ' '.join(str(x) for x in nums))
    return ''.join(p)

def emit(nid, ox, oy, out, ctx, depth=0, maxd=15):
    n = BY_(nid)
    if not n or n.get('visible') is False or depth > maxd: return
    x, y = pos(n); w, h = size(n)
    ax, ay = round(ox + x, 2), round(oy + y, 2)
    typ = n.get('type')
    op = n.get('opacity', 1)
    gop = ' opacity="%g"' % round(op, 3) if op < 1 else ''

    if typ == 'TEXT':
        td = n.get('textData') or {}
        chars = (td.get('characters') or '')
        if not chars.strip(): return
        fn = n.get('fontName') or {}
        fs = n.get('fontSize') or 14
        col, a, _ = solid(n.get('fillPaints'))
        fam = 'var(--mono)' if 'Mono' in (fn.get('family') or '') else 'var(--sans)'
        lh = n.get('lineHeight') or {}
        step = lh['value'] if lh.get('units') == 'PIXELS' and lh.get('value') else fs * 1.3
        ls = n.get('letterSpacing') or {}
        lsv = ls.get('value') if ls.get('units') == 'PIXELS' else 0
        anchor = {'CENTER': 'middle', 'RIGHT': 'end'}.get(n.get('textAlignHorizontal'), 'start')
        tx = ax + (w / 2 if anchor == 'middle' else (w if anchor == 'end' else 0))
        if n.get('textCase') == 'UPPER': chars = chars.upper()
        lines = chars.split('\n')
        tspans = ''.join('<tspan x="%s" dy="%s">%s</tspan>'
                         % (round(tx, 2), 0 if i == 0 else round(step, 2), html.escape(l))
                         for i, l in enumerate(lines))
        out.append('<text x="%s" y="%s" fill="%s"%s font-family="%s" font-size="%s" font-weight="%d"%s%s '
                   'dominant-baseline="text-before-edge" text-anchor="%s">%s</text>'
                   % (round(tx, 2), round(ay, 2), col or '#000',
                      ' fill-opacity="%s"' % a if a < 1 else '', fam, round(fs, 2),
                      FW.get(fn.get('style', 'Regular'), 400),
                      ' letter-spacing="%s"' % round(lsv, 2) if lsv else '', gop, anchor, tspans))
        return

    geo = n.get('fillGeometry') or []
    sgeo = n.get('strokeGeometry') or []
    if typ in ('VECTOR', 'LINE', 'ELLIPSE', 'REGULAR_POLYGON', 'STAR') and (geo or sgeo):
        fcol, fa, _ = solid(n.get('fillPaints'))
        scol, sa, _ = solid(n.get('strokePaints'))
        for g in geo:
            out.append('<path d="%s" fill="%s"%s%s/>' % (to_d(parse_path(g['commandsBlob']), ax, ay),
                       fcol or 'none', ' fill-opacity="%s"' % fa if fa < 1 else '', gop))
        for g in sgeo:
            out.append('<path d="%s" fill="%s"%s%s/>' % (to_d(parse_path(g['commandsBlob']), ax, ay),
                       scol or fcol or 'none', ' fill-opacity="%s"' % sa if sa < 1 else '', gop))
        return

    fill, fa, grad = solid(n.get('fillPaints'))
    r = rr(n)
    if grad is not None:
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s/>'
                   % (ax, ay, round(w,2), round(h,2), round(r,2), ctx.grad(grad, ax, ay, w, h), gop))
    elif fill and fill.startswith('IMG:'):
        src = fill[4:]
        clip = ''
        if r:
            ctx.n += 1; cid = 'c%d' % ctx.n
            ctx.defs.append('<clipPath id="%s"><rect x="%s" y="%s" width="%s" height="%s" rx="%s"/></clipPath>'
                            % (cid, ax, ay, round(w,2), round(h,2), round(r,2)))
            clip = ' clip-path="url(#%s)"' % cid
        out.append('<image href="%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="xMidYMid slice"%s%s/>'
                   % (src, ax, ay, round(w,2), round(h,2), clip, gop))
    elif fill:
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"%s%s/>'
                   % (ax, ay, round(w,2), round(h,2), round(r,2), fill,
                      ' fill-opacity="%s"' % fa if fa < 1 else '', gop))
    scol, sa, _ = solid(n.get('strokePaints'))
    if scol and not scol.startswith('IMG:') and typ not in ('VECTOR',):
        sw = n.get('strokeWeight') or 1
        out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="%s" stroke-width="%s"%s/>'
                   % (round(ax + sw/2, 2), round(ay + sw/2, 2), round(w - sw, 2), round(h - sw, 2),
                      max(round(r - sw/2, 2), 0), scol, round(sw, 2), gop))
    # an INSTANCE has no children of its own — draw the symbol it points at
    sd = n.get('symbolData') or {}
    sid = sd.get('symbolID')
    if typ == 'INSTANCE' and sid:
        sym = '%s:%s' % (sid['sessionID'], sid['localID'])
        if BY_(sym):
            # a symbol's children are positioned relative to the symbol frame,
            # so the instance's own origin is the offset — not the symbol's
            # position out on the canvas
            for k in kids(sym):
                emit(gid(k['guid']), ax, ay, out, ctx, depth + 1, maxd)
            return
    for k in kids(nid):
        emit(gid(k['guid']), ax, ay, out, ctx, depth + 1, maxd)

def svg(root_id, cls='fig'):
    n = BY_(root_id); w, h = size(n); x, y = pos(n)
    ctx = Ctx(); out = []
    emit(root_id, -x, -y, out, ctx)
    defs = '<defs>%s</defs>' % ''.join(ctx.defs) if ctx.defs else ''
    return ('<svg class="%s" viewBox="0 0 %g %g" xmlns="http://www.w3.org/2000/svg" '
            'role="img">%s%s</svg>' % (cls, w, h, defs, ''.join(out)))
