#!/usr/bin/env bash
# Is the content actually visible?
#
# This exists because of a real bug: a bad edit to js/site.js removed the block
# that adds .in to .reveal elements, and because the CSS hid them at opacity 0
# by default, four of the five pages shipped completely blank. Nothing in the
# HTML, the CSS, or a Lighthouse run caught it.
#
# Three checks:
#   1. static  — no CSS rule may hide .reveal unless it is behind .reveal-ready,
#                which is the class js/site.js adds. This is what guarantees the
#                page is readable with JavaScript off or broken.
#   2. rendered — every .reveal element that is in the viewport after load must
#                have a computed opacity above 0. Elements below the fold are
#                meant to stay hidden until scrolled to; content you can see
#                must never be invisible.
#   1b. order  — tools/cssorder.py: no @media rule lost to a later base rule.
#   3. overflow — no page scrolls sideways at 375, 390 or 1024.
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

echo "1b. static: no desktop rule is shadowed by a later base rule (CLAUDE.md §5)"
python3 tools/cssorder.py || FAIL=1

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

echo "3. no sideways scroll at 375, 390 and 1024"
# Headless Chrome will not open a window narrower than 500, so each page is
# loaded in a same-origin iframe of the target width and measured from outside.
# This is what caught KKL (411) and Bara (601) scrolling sideways on a phone.
cat > "$WORK/_overflow.html" <<'HTML'
<!doctype html><body style="margin:0"><script>
var pages = ['/index.html','/work/kkl.html','/work/travelhub.html','/work/bara.html','/work/suzuki.html'];
var widths = [375, 390, 1024], out = [], left = pages.length * widths.length;
pages.forEach(function (p) { widths.forEach(function (w) {
  var f = document.createElement('iframe');
  f.style.cssText = 'width:' + w + 'px;height:800px;border:0;display:block';
  // measure after the web fonts land: the fallback font is narrower and hides it
  f.onload = function () { f.contentDocument.fonts.ready.then(function () { setTimeout(function () {
    var d = f.contentDocument.documentElement;
    out.push(p + '@' + w + '=' + d.scrollWidth);
    if (--left === 0) document.title = 'OVF' + out.join(',') + 'OVF';
  }, 1500); }); };
  f.src = p; document.body.appendChild(f);
}); });
</script></body>
HTML
R=$("$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=30000 \
    --window-size=1100,1000 --dump-dom "http://localhost:8798/_overflow.html" 2>/dev/null \
    | grep -o 'OVF[^<]*OVF' | head -1 | sed 's/OVF//g')
if [[ -z "$R" ]]; then echo "   ?     could not measure"; FAIL=1; fi
for item in ${R//,/ }; do
  pg=${item%@*}; rest=${item#*@}; w=${rest%=*}; sw=${rest#*=}
  if [[ "$sw" -gt "$w" ]]; then printf '   %-22s FAIL  %s wide at %s\n' "$pg" "$sw" "$w"; FAIL=1
  else printf '   %-22s ok    %s\n' "$pg" "$w"; fi
done

[[ "$FAIL" -eq 0 ]] && echo "content is visible on every page" || echo "SMOKE TEST FAILED"
exit "$FAIL"
