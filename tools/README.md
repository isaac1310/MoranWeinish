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
