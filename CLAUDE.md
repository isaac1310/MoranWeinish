# Moran Weinish portfolio — working notes

Static site, no build step. Read `README.md` first for structure and the
checks; this file is about *how to work on it without breaking it*.

Every rule below was written after something went wrong. None of it is
theoretical.

---

## 1. Measure the Figma file. Do not eyeball it.

`Portfolio.fig` is in the repo root (gitignored, 67 MB). It is a zip containing
a kiwi-encoded document, and `tools/figdecode/` decodes it:

```bash
brew install zstd                                   # once
python3 tools/figdecode/decode.py Portfolio.fig /tmp/figx
cd tools/figdecode && python3 -c "
import nodes; nodes.load('/tmp/figx')
print(nodes.frames())            # main page 18:457 · kkl 46:121 · travel hub 18:666 · bara · suzuki
nodes.tree('46:121', maxd=3)     # exact x/y/w/h, fills, strokes, radii, text
print(nodes.find_text('Next trip'))
"
```

This gives exact colours, sizes, spacings, fonts and vector geometry. **Use it
before changing any number.** A whole round of this project was spent guessing
values off screenshots and getting them wrong — including reading a cropped
screenshot backwards and moving a column 80px the wrong way.

`gensvg.py` renders any frame as inline SVG. That is how the seven TravelHub
screens and the Suzuki icon row were built: they are drawn components in Figma,
not images, so there was never a file to export.

### Two traps in the geometry

- **Case-study frames are 1934 wide at x = −7.** So on those pages the gutter is
  **123** and the content column **1674** — not the 130 / 1660 of the home page
  frame, which is a true 1920. Mixing the two put every case page 7px out.
- **Image crops live in the paint transform**, not the image. `m00/m11` are the
  crop's width/height fraction, `m02/m12` its offset. Resizing the source
  without applying that produces squashed rubbish.

---

## 2. The .fig in this repo goes stale

Moran edits the live Figma; the file here is a point-in-time export. If a
screenshot disagrees with the decode, **the screenshot is newer** — say so and
ask for a fresh export rather than quietly trusting either one.

State clearly in the commit when a value came from a screenshot instead of the
file, and mark it in `tools/expected-*.json`, so the next person knows which
numbers are verified and which are inferred.

---

## 3. Run the checks before pushing. Not after.

```bash
python3 -m http.server 8787 &
tools/smoke.sh                       # content is visible on every page
tools/measure.sh work/kkl 1920       # geometry matches the .fig
tools/measure.sh work/kkl 1440       # ...and at any other width
```

Both must pass **before** `git push`, in a separate command. A commit, a push
and a failing smoke test once ran in one chained command and the broken build
shipped.

`measure.sh <page> <width>` scales the expected values by width/1920. All four
case pages should read clean at 1920, 1440 and 1024.

---

## 4. Scaling: `--k`

Gutters and type scale with the viewport. Spacing, padding, radii and fixed grid
tracks must too, or at 1440 they are 33% too large relative to everything else —
which is what produced round after round of "the spacing is off".

```css
--k: clamp(0.5333px, 100vw / 1920, 1px);   /* the size of one design pixel */
```

Used as `calc(310 * var(--k))` — the number stays unitless and traceable to the
frame, because `--k` carries the unit. **`--k` has to be a length.** A unitless
`clamp(0.5333, 100vw / 1920, 1)` is invalid CSS and the browser silently drops
every declaration that uses it.

Rule: a Figma-derived px inside a `≥1024` rule gets `* var(--k)`. Exceptions:
1px hairlines and focus outlines.

---

## 5. CSS ordering — this bit three times

`case.css` is mobile-first, so a media query placed **before** the base rule it
overrides loses. It happened with `.swatches span`, `.chips li` and
`.dark .chips li` — each time the declaration was correct and simply never
applied. If a change appears to do nothing, check the order before rewriting it.

Watch for higher-specificity variants too: `.dark .chips li` sets its own
`font-size` and outranks `.chips li`.

---

## 6. Content must never depend on JavaScript

`.reveal` is visible by default. The animation only exists once `js/site.js` has
put `.reveal-ready` on `<html>`, and the setup is wrapped in try/catch with a
per-element failsafe.

This is not a preference. A bad regex once deleted the block of `site.js` that
adds `.in`, and because the CSS hid `.reveal` at `opacity: 0` by default, four of
the five pages shipped **completely blank**. `node --check` passed. Lighthouse
scored the blank pages 100 for accessibility. `tools/smoke.sh` exists to catch
exactly this and its static check must keep passing.

The failsafe is per element. An earlier version asked "has anything revealed?"
and one revealed element switched the net off for every other one.

---

## 7. Editing traps specific to this repo

- **Nav and footer are copy-pasted into all five `.html` files.** Change them in
  all five. Same for the version marker.
- **Never revert with a greedy regex.** `.*?` up to a closing `})();` matched the
  end of the wrong IIFE and took 60 lines with it. Prefer `git show <sha>:path`.
- **A hidden `<br>` eats the space around it.** `before<br class="wide">designing`
  renders as "beforedesigning" below the breakpoint. Put the space in.
- **Force a line break with `&nbsp;`, not a width.** Tuning a `max-width` to make
  text wrap in a particular place is fragile at other viewports.
- **There is a CSP** in `vercel.json` (`script-src 'self'`). Inline event
  handlers are blocked. `python3 -m http.server` sends no CSP, so anything that
  depends on one will pass locally and fail live — an async font-loading change
  shipped this way and the live site ran in fallback fonts.

---

## 8. Verifying animation

Headless Chrome with `--virtual-time-budget` does **not** advance CSS
transitions or animations, and a hidden browser tab throttles them to a crawl.
Both read as "nothing is animating" when the CSS is fine. Use the Web Animations
API instead — it is immune to both:

```js
const a = el.getAnimations()[0];
a.currentTime = 200;                 // force a point in the timeline
getComputedStyle(el).opacity;
```

### Parent opacity multiplies

A child cannot animate out of a fading ancestor. Section 04's chips looked
static because `.cs-content.reveal` faded the whole block while the chips
staggered inside it — opting the `<ul>` out of its own fade does not escape a
wrapping one. Put `.reveal` on the individual children instead of the wrapper.

---

## 9. Deploying

Push to `main` → Vercel. **Bump the patch version in all five footers on every
push that changes what ships** (see README). Docs-only commits do not bump.

Pushes go through Itzik's personal GitHub account, not the work one.
