#!/usr/bin/env bash
# Render a page at 1920 and diff its geometry against the Figma numbers.
# Usage: tools/measure.sh work/kkl [width]   (needs python3 -m http.server 8787 running)
#
# The .fig numbers are for the 1920 design frame. At any other width the page is
# a straight scale of it, so the expected values are multiplied by width/1920.
# With the --k factor in tokens.css in place, 1920 and 1440 both come back clean.
set -euo pipefail
PAGE="${1:-work/kkl}"
WIDTH="${2:-1920}"
PORT="${PORT:-8787}"
EXPECTED="tools/expected-$(basename "$PAGE").json"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

lsof -ti:8799 | xargs kill 2>/dev/null || true   # a stale run holding the port
rsync -a --exclude Portfolio.fig --exclude .git ./ "$WORK/"
python3 - "$WORK/$PAGE.html" "$EXPECTED" <<'PY'
import json, sys
page, expected = sys.argv[1], sys.argv[2]
sels = [k for k in json.load(open(expected)) if not k.startswith('_')]
probe = """
<script>window.addEventListener('load', function () {
  document.querySelectorAll('.reveal').forEach(function (e) { e.classList.add('in'); });
  var sels = %s, out = {};
  sels.forEach(function (s) {
    var el = document.querySelector(s);
    if (!el) { out[s] = null; return; }
    var r = el.getBoundingClientRect();
    out[s] = [Math.round(r.left), Math.round(r.width), Math.round(r.height)];
  });
  document.title = 'MEASURE' + JSON.stringify(out) + 'END';
});</script>
""" % json.dumps(sels)
s = open(page).read()
open(page, 'w').write(s.replace('</body>', probe + '</body>'))
PY

(cd "$WORK" && python3 -m http.server 8799 >/dev/null 2>&1 & echo $! > "$WORK/.pid"); sleep 1.5
RAW=$("$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=9000 \
      --window-size=$WIDTH,1200 --dump-dom "http://localhost:8799/$PAGE.html" 2>/dev/null \
      | grep -o 'MEASURE.*END' | head -1 | sed 's/MEASURE//;s/END//')
kill "$(cat "$WORK/.pid")" 2>/dev/null || true

EXPECTED="$EXPECTED" WIDTH="$WIDTH" python3 - "$RAW" <<'PY'
import json, os, sys
m = json.loads(sys.argv[1])
exp = json.load(open(os.environ['EXPECTED']))
k = int(os.environ.get('WIDTH', 1920)) / 1920.0
tol = max(3, round(4 * k))
bad = 0
print(f"{'selector':<26}{'rendered':<24}{'expected @%d':<20}" % int(os.environ.get('WIDTH', 1920)))
for sel, spec in exp.items():
    if sel.startswith('_'): continue
    r = m.get(sel)
    f = [None if v is None else round(v * k) for v in spec['fig']]
    if r is None:
        print(f"{sel:<26}{'NOT FOUND':<24}{str(f):<20}<-- MISSING"); bad += 1; continue
    ok = all(abs(r[i] - v) <= tol for i, v in enumerate(f) if v is not None)
    bad += 0 if ok else 1
    print(f"{sel:<26}{str(r):<24}{str(f):<20}{'OK' if ok else '<-- DIFF'}")
n = len([k for k in exp if not k.startswith('_')])
print(f"\n{n - bad}/{n} match the .fig within {tol}px at {int(os.environ.get('WIDTH', 1920))}")
sys.exit(1 if bad else 0)
PY
