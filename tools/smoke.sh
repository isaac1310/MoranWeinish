#!/usr/bin/env bash
# Is the content actually visible?
#
# This exists because of a real bug: a bad edit to js/site.js removed the block
# that adds .in to .reveal elements, and because the CSS hid them at opacity 0
# by default, four of the five pages shipped completely blank. Nothing in the
# HTML, the CSS, or a Lighthouse run caught it.
#
# Two checks:
#   1. static  — no CSS rule may hide .reveal unless it is behind .reveal-ready,
#                which is the class js/site.js adds. This is what guarantees the
#                page is readable with JavaScript off or broken.
#   2. rendered — every .reveal element that is in the viewport after load must
#                have a computed opacity above 0. Elements below the fold are
#                meant to stay hidden until scrolled to; content you can see
#                must never be invisible.
#
#   python3 -m http.server 8787 &
#   tools/smoke.sh
set -uo pipefail
BASE="${1:-http://localhost:8787}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
FAIL=0

echo "1. static: nothing hides .reveal without .reveal-ready"
if grep -nE '(^|[^-])\.reveal[^-a-z]*\{[^}]*opacity:\s*0' css/*.css | grep -v 'reveal-ready' | grep -q .; then
  grep -nE '(^|[^-])\.reveal[^-a-z]*\{[^}]*opacity:\s*0' css/*.css | grep -v 'reveal-ready' | sed 's/^/   FAIL /'
  FAIL=1
else
  echo "   ok    .reveal is visible by default"
fi

echo "2. rendered: every .reveal element ends up visible"
WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"; lsof -ti:8798 | xargs kill 2>/dev/null || true' EXIT
lsof -ti:8798 | xargs kill 2>/dev/null || true
rsync -a --exclude Portfolio.fig --exclude .git ./ "$WORK/"
cp tools/probe.js "$WORK/probe.js"
for f in "$WORK"/index.html "$WORK"/work/*.html; do
  python3 - "$f" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
open(p, 'w').write(s.replace('</body>', '<script src="/probe.js"></script></body>'))
PY
done
(cd "$WORK" && python3 -m http.server 8798 >/dev/null 2>&1 &) ; sleep 1.5
for PAGE in /index.html /work/kkl.html /work/travelhub.html /work/bara.html /work/suzuki.html; do
  R=$("$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=20000 \
      --window-size=1500,1000 --dump-dom "http://localhost:8798$PAGE" 2>/dev/null \
      | grep -o 'SMOKE{[^}]*}SMOKE' | head -1 | sed 's/SMOKE//g')
  T=$(sed -n 's/.*"total":\([0-9]*\).*/\1/p' <<<"$R"); H=$(sed -n 's/.*"hidden":\([0-9]*\).*/\1/p' <<<"$R")
  if [[ -z "${T:-}" ]]; then printf '   %-22s ?     could not read the page\n' "$PAGE"; FAIL=1
  elif [[ "$H" -gt 0 ]]; then printf '   %-22s FAIL  %s of %s in view are invisible\n' "$PAGE" "$H" "$T"; FAIL=1
  else printf '   %-22s ok    %s in view, all visible\n' "$PAGE" "$T"; fi
done

[[ "$FAIL" -eq 0 ]] && echo "content is visible on every page" || echo "SMOKE TEST FAILED"
exit "$FAIL"
