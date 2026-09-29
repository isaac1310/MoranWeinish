# tools/ — dev only, not shipped

## measure.sh — check the rendered page against Portfolio.fig

The bugs in this project have almost all been the same kind: a number in the CSS
that did not match the Figma frame, found by eye one viewport at a time. This
script removes the eye.

It renders a page at 1920 in headless Chrome, reads the real geometry of the
elements that matter, and diffs them against numbers taken out of `Portfolio.fig`.

```bash
python3 -m http.server 8787 &
tools/measure.sh work/kkl
```

Output is one line per element: rendered `[x, width, height]`, the expected
values, and OK / DIFF. Anything marked DIFF is a real mismatch with the design.

Expected values live in `tools/expected-kkl.json`, keyed by CSS selector. They
were read from the decoded `.fig` (frame `kkl`, node 46:121), not measured off a
screenshot — the node ids are in the comments beside each entry in `css/case.css`.

Note the case-study frames in the `.fig` are 1934 wide at x=-7, so on these pages
the gutter is 123 and the content column 1674 (`body.case` in `css/case.css`).
The home-page frame is a true 1920, which is where the 130/1660 in `tokens.css`
comes from. Mixing the two was the cause of a whole round of misalignments.

## figcompare.sh — the Figma frame next to the page, by eye

```bash
python3 tools/figdecode/decode.py Portfolio.fig /tmp/figx      # once
tools/figcompare.sh /tmp/figx 46:121 work/kkl /tmp/cmp          # open /tmp/cmp/compare.html
```

Renders the frame with `tools/figdecode/refpage.py` (rotated nodes, resized instances, image
crops, per-side borders, gradients and paint opacity all handled — see its docstring), takes a
1920 screenshot of the page from a copy with animations and the splash off, and puts the two
side by side, Figma on the left. measure.sh checks numbers; this is for everything measure.sh
doesn't have a selector for. The export can be older than the live Figma file — when they
disagree, look at the live prototype before changing anything.

Frames: home 18:457 · kkl 46:121 · travelhub 18:666 · bara 133:8706 · suzuki 174:1060.

## cssorder.py — desktop rules shadowed by a later base rule

Run by smoke.sh. See CLAUDE.md §5.
