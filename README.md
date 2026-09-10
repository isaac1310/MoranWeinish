# Moran Weinish — portfolio

Static site, no build step. Live: https://moran-weinish.vercel.app

- `index.html` — home (hero · what I do · case studies · about · contact)
- `work/<slug>.html` — one file per case study (kkl, travelhub, bara, suzuki)
- `css/tokens.css` — colours/type/spacing from the Figma file; `css/site.css` — layout
- `js/site.js` — mobile nav, back-to-top, scroll reveal (only JS on the site)
- `assets/` — WebP images, video, `og.png`, CV PDF

## Editing
- **Nav/footer are copy-pasted in every `.html`** (no build step). Change them everywhere.
- Swap the CV: replace `assets/Moran-Weinish-CV.pdf`, keep the name.
- New image: convert to WebP ≤1600px wide (`sharp` or squoosh.app), put in `assets/img/`.
- The Figma file is frozen; this repo is the source of truth.

## Local preview
```bash
python3 -m http.server 8787
```
Open http://127.0.0.1:8787/. Note: `/work/kkl` clean URLs only work on Vercel; locally use `/work/kkl.html`.

## Lighthouse

Mobile, run against the live URL on 2026-09-10 (`npx lighthouse@12 <url>`, default
mobile preset, headless Chrome). Targets: Performance ≥ 90, Accessibility ≥ 95, SEO ≥ 95.

| Page | Performance | Accessibility | Best practices | SEO |
|---|---|---|---|---|
| `/` | 97 | 100 | 100 | 100 |
| `/work/kkl` | 98 | 100 | 96 | 100 |
| `/work/travelhub` | 88 | 98 | 100 | 100 |
| `/work/bara` | 98 | 95 | 96 | 100 |
| `/work/suzuki` | 89 | 100 | 100 | 100 |

TravelHub and Suzuki miss the performance target by a couple of points. Both are
image-heavy and both are held up by the same thing: the Google Fonts stylesheet is
render-blocking (~1.6 s and ~0.6 s of the LCP), and the LCP element on each is a
paragraph waiting on it. Loading it asynchronously
(`media="print" onload="this.media='all'"` plus a `<noscript>` fallback, in all five
files) would clear it, at the cost of a more visible fallback-font flash on a slow
connection. Not done — it is a visual trade-off, so it is a decision, not a fix.

Best practices sits at 96 on Bara: `assets/img/bara/logo.webp` is 219x70 and is shown
at that size, so it is soft on a retina screen. It needs a 2x export from Moran
(tracked in GAPS.md); nothing in the code can fix it.

(KKL was also at 96 — the challenge banner's watermark had a fixed `height` attribute
that `max-width` then squashed. Fixed with `height: auto`.)

## Deploy
Push to `main` → Vercel (project `MoranWeinish`, personal Hobby scope) deploys automatically.
