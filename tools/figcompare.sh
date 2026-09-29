#!/usr/bin/env bash
# Figma frame next to the site, for a review by eye.
#
#   tools/figcompare.sh <figx> <frame-id> <page> [out-dir]
#   tools/figcompare.sh /tmp/figx 46:121 work/kkl /tmp/cmp      # then open /tmp/cmp/compare.html
#
# <figx> is a decode made with tools/figdecode/decode.py. The frame is rendered with
# tools/figdecode/refpage.py, the page is served from a copy of the working tree with
# animations and the splash switched off (so nothing is caught mid-fade), both are
# screenshotted at 1920 in headless Chrome, and compare.html shows them side by side,
# Figma on the left. The export in the repo can be older than the live Figma file: when
# the two disagree, check the live prototype before changing anything (CLAUDE.md §2).
set -euo pipefail
FIGX="$1"; FRAME="$2"; PAGE="$3"; OUT="${4:-$(mktemp -d)}"
PORT="${PORT:-8797}"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$HERE")"
mkdir -p "$OUT"; WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"; lsof -ti:'"$PORT"' | xargs kill 2>/dev/null || true' EXIT

# 1. the Figma frame
H=$(python3 "$HERE/figdecode/refpage.py" "$FIGX" "$FRAME" "$OUT/figma.html" | awk '{print int($3)}')
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --virtual-time-budget=20000 --window-size=1920,"$H" --screenshot="$OUT/figma.png" "file://$OUT/figma.html" >/dev/null 2>&1

# 2. the page, static
rsync -a --exclude Portfolio.fig --exclude .git "$ROOT/" "$WORK/"
python3 - "$WORK/$PAGE.html" <<'PY'
import sys
p = sys.argv[1]; s = open(p).read()
s = s.replace('</head>', '<style>*,*::before,*::after{animation:none!important;transition:none!important}'
              '.reveal{opacity:1!important;transform:none!important}.splash{display:none!important}</style></head>')
open(p, 'w').write(s)
PY
lsof -ti:"$PORT" | xargs kill 2>/dev/null || true
(cd "$WORK" && python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1 &); sleep 1.5
"$CHROME" --headless=new --disable-gpu --hide-scrollbars --virtual-time-budget=15000 \
  --window-size=1920,$((H + 2500)) --screenshot="$OUT/site.png" "http://127.0.0.1:$PORT/$PAGE.html" >/dev/null 2>&1

# 3. side by side
cat > "$OUT/compare.html" <<HTML
<!doctype html><meta charset="utf-8"><title>$PAGE — Figma vs site</title>
<style>body{margin:0;font:13px system-ui;background:#888}header{position:sticky;top:0;display:grid;grid-template-columns:1fr 1fr;background:#222;color:#fff}
header b{padding:6px 10px}main{display:grid;grid-template-columns:1fr 1fr;gap:4px;align-items:start}img{width:100%;display:block;background:#fff}</style>
<header><b>Figma $FRAME (repo export)</b><b>site: $PAGE at 1920</b></header>
<main><img src="figma.png" alt="Figma render"><img src="site.png" alt="Site screenshot"></main>
HTML
echo "$OUT/compare.html"
