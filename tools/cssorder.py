#!/usr/bin/env python3
"""CLAUDE.md §5, as a check: a declaration inside @media (min-width: …) that a LATER
unconditional rule with the same selector overrides never applies. It bit this repo
at least eight times (.swatches span, .chips li, .ds, .stats li, .reflect, .summary,
.panel, .banner img) — each time the value was right and simply lost.

    python3 tools/cssorder.py            # css/*.css and every page's <style> block
Exit 1 if anything is shadowed. Same-selector matches only; specificity is not modelled.
"""
import re, sys, glob

def rules(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    out, media = [], None
    for m in re.finditer(r'(@media[^{]+)\{|([^{}]+)\{([^{}]*)\}|\}', css):
        if m.group(1): media = m.group(1).strip(); continue
        if m.group(2) is None: media = None; continue
        props = {}
        for d in m.group(3).split(';'):
            if ':' in d:
                k, v = d.split(':', 1); props[k.strip()] = v.strip()
        out.append((media, [s.strip() for s in m.group(2).split(',')], props))
    return out

def family(p):  # margin-top is overridden by a later margin shorthand, etc.
    return p.split('-')[0] if p.split('-')[0] in ('margin', 'padding', 'border', 'gap', 'inset') else p

def check(name, css):
    rs, bad = rules(css), 0
    for i, (media, sels, props) in enumerate(rs):
        if not media or 'min-width' not in media or 'max-width' in media: continue
        for sel in sels:
            for m2, sels2, props2 in rs[i + 1:]:
                if m2 is None and sel in sels2:
                    fam2 = {family(k) for k in props2} | set(props2)
                    lost = [k for k in props if k in props2 or family(k) in props2 or
                            (k in ('margin', 'padding') and any(x.startswith(k) for x in props2))]
                    if lost:
                        print('   FAIL  %s: %s { %s } in %s is overridden by a later base rule'
                              % (name, sel, ', '.join(lost), media)); bad += 1
    return bad

bad = 0
for f in sorted(glob.glob('css/*.css')):
    bad += check(f, open(f).read())
for f in ['index.html'] + sorted(glob.glob('work/*.html')):
    for j, block in enumerate(re.findall(r'<style>(.*?)</style>', open(f).read(), re.S)):
        bad += check('%s <style>' % f, block)
if not bad: print('   ok    no desktop rule is shadowed by a later base rule')
sys.exit(1 if bad else 0)
