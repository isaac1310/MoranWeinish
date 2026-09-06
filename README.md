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

## Deploy
Push to `main` → Vercel (project `MoranWeinish`, personal Hobby scope) deploys automatically.
