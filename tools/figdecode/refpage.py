"""Render a whole .fig frame as a reference page (HTML + one SVG) to compare the site against.

    python3 tools/figdecode/refpage.py /tmp/figx 46:121 /tmp/ref/kkl.html

This is the renderer the 2026-09-29 review was done with, with the bugs that review found
fixed. Differences from gensvg.py (which emits small inline SVGs for the site itself):

- Every node is nested in its own <g transform="matrix(...)">, so rotated and flipped nodes
  (the TravelHub hero phone, Suzuki's arrows, the Bara flower) render the way Figma draws them.
- An INSTANCE whose size differs from its symbol uses Figma's own resized geometry
  (derivedSymbolData) when the file has it, and otherwise scales the symbol by the size ratio.
  Drawing the unresized symbol is what clipped the Suzuki icon row.
- Text is laid out line by line from derivedTextData baselines, so line breaks match Figma.
- Image fills apply their crop (the paint transform: m00/m11 = visible fraction, m02/m12 =
  offset) whenever it isn't the identity — top/bottom-only crops included.
- Linear gradients take their direction from the paint transform's inverse, so a vertical
  wash reads top-to-bottom (the old code read the wrong matrix row and drew it sideways).
- Paint opacity is applied on top of the colour's alpha. The v1.0.14 Bara bug came from
  dropping it: #5889a8 at 11% is a pale grey-green, not blue.
- Per-side borders (borderStrokeWeightsIndependent) are drawn side by side, so a section
  label is a top rule, not a box.
- Frames with clipping on (frameMaskDisabled False) clip their children.

Known limits: no shadows or blurs, no gradient strokes, no blend modes, fonts come from Google
Fonts (Assistant, Space Mono, Open Sans, Inter, Poppins). Good enough to compare layout,
spacing, colour and copy — confirm exact numbers from the decode.
"""
import sys, os, html, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nodes as N
from path import parse as parse_path

FW = {'Thin': 100, 'ExtraLight': 200, 'Light': 300, 'Regular': 400, 'Medium': 500,
      'SemiBold': 600, 'Bold': 700, 'ExtraBold': 800, 'Black': 900}


def f(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') or '0'


def rgba(c, op=1.0):
    if not c:
        return None, 1.0
    h = lambda v: format(max(0, min(255, round(v * 255))), '02x')
    return '#' + h(c.get('r', 0)) + h(c.get('g', 0)) + h(c.get('b', 0)), round(c.get('a', 1) * op, 4)


def inv(m):
    """Inverse of the 2x3 affine [a b c; d e f] given as (m00, m01, m02, m10, m11, m12)."""
    a, b, c, d, e, g = m
    det = a * e - b * d or 1e-9
    return (e / det, -b / det, (b * g - c * e) / det, -d / det, a / det, (c * d - a * g) / det)


def apply(m, x, y):
    return m[0] * x + m[1] * y + m[2], m[3] * x + m[4] * y + m[5]


class Page:
    def __init__(self, figx, outdir):
        self.figx, self.outdir = figx, outdir
        self.defs, self.n = [], 0
        os.makedirs(os.path.join(outdir, 'img'), exist_ok=True)

    def uid(self, p):
        self.n += 1
        return '%s%d' % (p, self.n)

    def image(self, h):
        """figx/images/<hash> has no extension and Chrome won't sniff it inside SVG: link one in."""
        src = os.path.join(self.figx, 'images', h)
        if not os.path.exists(src):
            return None
        head = open(src, 'rb').read(4)
        ext = 'png' if head.startswith(b'\x89PNG') else 'jpg' if head.startswith(b'\xff\xd8') else 'gif' if head.startswith(b'GIF') else 'bin'
        dst = os.path.join(self.outdir, 'img', h + '.' + ext)
        if not os.path.exists(dst):
            os.symlink(os.path.abspath(src), dst)
        return 'img/%s.%s' % (h, ext)

    def paint(self, p, w, h):
        """One visible paint -> (fill attr value, opacity) or (None, 0)."""
        if p.get('visible') is False:
            return None, 0
        op = p.get('opacity', 1)
        if op == 0:
            return None, 0
        t = p.get('type', '')
        if t == 'SOLID':
            return rgba(p.get('color'), op)
        if t.startswith('GRADIENT'):
            gid = self.uid('g')
            stops = ''.join('<stop offset="%s" stop-color="%s" stop-opacity="%s"/>'
                            % (f(s.get('position', 0)), *rgba(s.get('color')))
                            for s in (p.get('stops') or []))
            tm = p.get('transform') or {}
            m = (tm.get('m00', 1), tm.get('m01', 0), tm.get('m02', 0), tm.get('m10', 0), tm.get('m11', 1), tm.get('m12', 0))
            im = inv(m)
            if t == 'GRADIENT_LINEAR':
                # the paint transform maps the shape's unit box to gradient space, where the
                # gradient runs along x from 0 to 1 at y = .5 — so its ends are T^-1(0,.5), T^-1(1,.5)
                (x1, y1), (x2, y2) = apply(im, 0, .5), apply(im, 1, .5)
                self.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                                 % (gid, f(x1), f(y1), f(x2), f(y2), stops))
            else:
                cx, cy = apply(im, .5, .5)
                self.defs.append('<radialGradient id="%s" cx="%s" cy="%s" r=".5">%s</radialGradient>'
                                 % (gid, f(cx), f(cy), stops))
            return 'url(#%s)' % gid, op
        if t == 'IMAGE':
            hsh = ''.join(format(b, '02x') for b in (p.get('image') or {}).get('hash', []))
            return ('IMG', self.image(hsh), p), op
        return None, 0

    def box(self, n, w, h, out):
        r = _radius(n)
        for p in (n.get('fillPaints') or []):
            val, op = self.paint(p, w, h)
            if val is None:
                continue
            if isinstance(val, tuple):
                _, src, ip = val
                if not src:
                    continue
                cid = self.uid('c')
                self.defs.append('<clipPath id="%s"><rect width="%s" height="%s" rx="%s"/></clipPath>' % (cid, f(w), f(h), f(r)))
                tm = ip.get('transform') or {}
                sw, sh = tm.get('m00', 1) or 1, tm.get('m11', 1) or 1
                ox, oy = tm.get('m02', 0), tm.get('m12', 0)
                mode = ip.get('imageScaleMode', 'FILL')
                if (sw, sh, ox, oy) != (1, 1, 0, 0):
                    iw, ih = w / sw, h / sh
                    out.append('<image href="%s" x="%s" y="%s" width="%s" height="%s" preserveAspectRatio="none" clip-path="url(#%s)" opacity="%s"/>'
                               % (src, f(-ox * iw), f(-oy * ih), f(iw), f(ih), cid, f(op)))
                else:
                    par = 'xMidYMid meet' if mode == 'FIT' else 'xMidYMid slice'
                    out.append('<image href="%s" width="%s" height="%s" preserveAspectRatio="%s" clip-path="url(#%s)" opacity="%s"/>'
                               % (src, f(w), f(h), par, cid, f(op)))
            else:
                out.append('<rect width="%s" height="%s" rx="%s" fill="%s"%s/>'
                           % (f(w), f(h), f(r), val, ' fill-opacity="%s"' % f(op) if op < 1 else ''))
        for p in (n.get('strokePaints') or []):
            val, op = self.paint(p, w, h)
            if val is None or isinstance(val, tuple):
                continue
            sw = n.get('strokeWeight') or 1
            so = ' stroke-opacity="%s"' % f(op) if op < 1 else ''
            if n.get('strokeGeometry'):
                # Figma ships the exact stroke outline (per-side weights, radius, alignment) — use it
                for geo in n['strokeGeometry']:
                    out.append('<path d="%s" fill="%s"%s/>' % (_d(geo), val, ' fill-opacity="%s"' % f(op) if op < 1 else ''))
                continue
            if n.get('borderStrokeWeightsIndependent'):
                # per-side borders (a section label's top rule, a card's thick left edge): draw each side
                sides = [('borderTopWeight', 0, 0, w, 0), ('borderBottomWeight', 0, h, w, h),
                         ('borderLeftWeight', 0, 0, 0, h), ('borderRightWeight', w, 0, w, h)]
                for key, x1, y1, x2, y2 in sides:
                    bw = n.get(key, 0) or 0  # a side the file doesn't list has no border
                    if bw:
                        dx = bw / 2 if key == 'borderLeftWeight' else -bw / 2 if key == 'borderRightWeight' else 0
                        dy = bw / 2 if key == 'borderTopWeight' else -bw / 2 if key == 'borderBottomWeight' else 0
                        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"%s/>'
                                   % (f(x1 + dx), f(y1 + dy), f(x2 + dx), f(y2 + dy), val, f(bw), so))
                continue
            out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="none" stroke="%s" stroke-width="%s"%s/>'
                       % (f(sw / 2), f(sw / 2), f(w - sw), f(h - sw), f(max(r - sw / 2, 0)), val, f(sw), so))

    def text(self, n, out):
        chars = (n.get('textData') or {}).get('characters') or ''
        if not chars.strip():
            return
        fn = n.get('fontName') or {}
        fs = n.get('fontSize') or 14
        fam = "'Space Mono',monospace" if 'Mono' in (fn.get('family') or '') else "'%s',sans-serif" % (fn.get('family') or 'Assistant').replace(' Hebrew', '')
        col, a = (None, 1)
        for p in (n.get('fillPaints') or []):
            v, op = self.paint(p, 0, 0)
            if v and not isinstance(v, tuple):
                col, a = v, op
                break
        ls = n.get('letterSpacing') or {}
        lsv = ls.get('value', 0) if ls.get('units') == 'PIXELS' else ls.get('value', 0) * fs / 100 if ls.get('units') == 'PERCENT' else 0
        if n.get('textCase') == 'UPPER':
            chars = chars.upper()
        style = (fn.get('style') or 'Regular').replace(' Italic', '').replace('Italic', 'Regular')
        attrs = 'fill="%s"%s font-family="%s" font-size="%s" font-weight="%d"%s' % (
            col or '#000', ' fill-opacity="%s"' % f(a) if a < 1 else '', html.escape(fam), f(fs),
            FW.get(style, 400), ' letter-spacing="%s"' % f(lsv) if lsv else '')
        bl = (n.get('derivedTextData') or {}).get('baselines') or []
        if not bl:
            out.append('<text %s dominant-baseline="text-before-edge">%s</text>' % (attrs, html.escape(chars)))
            return
        for b in bl:
            s = chars[b['firstCharacter']:b['endCharacter']].rstrip('\n')
            if s.strip():
                out.append('<text x="%s" y="%s" %s>%s</text>' % (f(b['position']['x']), f(b['position']['y']), attrs, html.escape(s)))

    def emit(self, nid, out, root=False, derived=None, scale=None):
        n = N.BY.get(nid)
        if not n or n.get('visible') is False or n.get('opacity', 1) == 0:
            return
        d = None
        if derived and n.get('overrideKey'):
            ok = n['overrideKey']
            d = derived.get((ok['sessionID'], ok['localID']))
        t = (d or {}).get('transform') or n.get('transform') or {}
        m = [t.get('m00', 1), t.get('m10', 0), t.get('m01', 0), t.get('m11', 1), t.get('m02', 0), t.get('m12', 0)]
        if scale and not d:
            m[4] *= scale[0]; m[5] *= scale[1]
        if root:
            m = [1, 0, 0, 1, 0, 0]
        w, h = N.size(n)
        if d and d.get('size'):
            w, h = d['size'].get('x', w), d['size'].get('y', h)
        op = n.get('opacity', 1)
        g = ['<g']
        if m != [1, 0, 0, 1, 0, 0]:
            g.append(' transform="matrix(%s)"' % ' '.join(f(v) for v in m))
        if op < 1:
            g.append(' opacity="%s"' % f(op))
        out.append(''.join(g) + '>')
        typ = n.get('type')
        if typ == 'TEXT':
            self.text(n, out)
        else:
            fg = (d or {}).get('fillGeometry') or n.get('fillGeometry') or []
            sg = (d or {}).get('strokeGeometry') or n.get('strokeGeometry') or []
            if typ in ('VECTOR', 'LINE', 'ELLIPSE', 'REGULAR_POLYGON', 'STAR', 'BOOLEAN_OPERATION') and (fg or sg):
                for p, geos in ((n.get('fillPaints'), fg), (n.get('strokePaints'), sg)):
                    for pp in (p or []):
                        val, pop = self.paint(pp, w, h)
                        if val is None or isinstance(val, tuple):
                            continue
                        for geo in geos:
                            out.append('<path d="%s" fill="%s"%s/>' % (_d(geo), val, ' fill-opacity="%s"' % f(pop) if pop < 1 else ''))
                        break
            else:
                self.box(n, w, h, out)
                inner = []
                sd = n.get('symbolData') or {}
                sid = sd.get('symbolID')
                if typ == 'INSTANCE' and sid and N.BY.get(N.gid(sid)):
                    sym = N.gid(sid)
                    der = {(x['guidPath']['guids'][-1]['sessionID'], x['guidPath']['guids'][-1]['localID']): x
                           for x in (n.get('derivedSymbolData') or []) if x.get('guidPath', {}).get('guids')}
                    sw, sh = N.size(N.BY[sym])
                    sc = (w / sw if sw else 1, h / sh if sh else 1)
                    for k in N.kids(sym):
                        self.emit(N.gid(k['guid']), inner, derived=der or None, scale=None if der else sc)
                else:
                    for k in N.kids(nid):
                        self.emit(N.gid(k['guid']), inner, derived=derived, scale=scale)
                if inner and typ in ('FRAME', 'INSTANCE', 'SYMBOL') and n.get('frameMaskDisabled') is False:
                    cid = self.uid('k')
                    self.defs.append('<clipPath id="%s"><rect width="%s" height="%s" rx="%s"/></clipPath>' % (cid, f(w), f(h), f(_radius(n))))
                    out.append('<g clip-path="url(#%s)">' % cid); out.extend(inner); out.append('</g>')
                else:
                    out.extend(inner)
        out.append('</g>')


def _radius(n):
    ks = ['rectangleTopLeftCornerRadius', 'rectangleTopRightCornerRadius',
          'rectangleBottomRightCornerRadius', 'rectangleBottomLeftCornerRadius']
    vs = [n.get(k) for k in ks]
    return max(v or 0 for v in vs) if any(v is not None for v in vs) else (n.get('cornerRadius') or 0)


def _d(geo):
    p = []
    for op, v in parse_path(geo['commandsBlob']):
        p.append('Z' if op == 'Z' else op + ' '.join(f(x) for x in v))
    return ''.join(p)


def main(figx, root, out_html):
    N.load(figx)
    page = Page(figx, os.path.dirname(os.path.abspath(out_html)))
    n = N.BY[root]
    w, h = N.size(n)
    body = []
    page.emit(root, body, root=True)
    svg = ('<svg viewBox="0 0 %s %s" width="%s" height="%s" xmlns="http://www.w3.org/2000/svg"><defs>%s</defs>%s</svg>'
           % (f(w), f(h), f(w), f(h), ''.join(page.defs), ''.join(body)))
    open(out_html, 'w').write(
        '<!doctype html><meta charset="utf-8"><title>%s — Figma reference</title>'
        '<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;500;600;700;800&family=Space+Mono'
        '&family=Open+Sans:wght@400;600;700&family=Inter:wght@400;500;600;700&family=Poppins:wght@400;500;600;700&display=block" rel="stylesheet">'
        '<style>body{margin:0}svg{display:block}</style>%s' % (html.escape(N.name(n)), svg))
    print(out_html, w, h)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
