# GAPS — things the Figma file does not contain (for Moran)

Generated 2026-09-06 from `Portfolio.fig` (decoded directly; no Dev Mode).
Each item blocks or degrades a part of the site until answered.

## Blocking for launch

| # | Gap | Where it shows | What I need |
|---|-----|----------------|-------------|
| 1 | **LinkedIn URL** | Footer "Elsewhere → LinkedIn" (currently points at linkedin.com) | The profile URL |
| 2 | **Resume PDF** | Footer "Resume (PDF)" — the file is not in Figma | The PDF, saved as `assets/Moran-Weinish-CV.pdf`. Consider removing phone/address from the web copy: anyone with the link can download it and search engines index PDFs. |
| 3 | **Hero accent colour** | "feel *simple.*" | The colour comes from a shared Figma style I can't read from the file. I used `#8a2c46` (same as the "Selected work" label). Confirm or give the hex. |

## Quality / decide together

| # | Gap | Detail |
|---|-----|--------|
| 4 | **Bara card image is low-res** | Source is 600×320 (7 KB after compression). On a retina screen it will look soft. Export at 1200×640 from the source design, or pick another frame. |
| 5 | **TravelHub card has no image** | In Figma the card thumbnail is a phone mockup built from layers, not a picture. I rebuilt a simplified version in CSS. If you prefer, export the card art from Figma as a 750×460 PNG and I'll swap it. |
| 6 | **KKL card image is 2.6 MB JPEG (1920×1024)** | Compressed to 39 KB WebP at 750px wide. Check it still reads well; the original is much larger than the card. |
| 7 | **Suzuki card image** (1931×1090) | Compressed to 78 KB WebP. Fine, just confirm the crop (cover, centred). |
| 8 | **Headshot** (1536×2040 JPEG) | Used at 340×420 with a 2× version. Good quality. Confirm this is the photo you want public. |
| 9 | **Open Graph image** | Nothing in Figma. I will render a 1200×630 `assets/og.png` from the hero (name + tagline on the cream background). Confirm or supply your own. |
| 10 | **"What I do" strip on mobile** | Six items + slashes don't fit one line on a phone. Plan: wrap to two centred rows. Alternative: horizontal scroll. Your call when you see it. |
| 11 | **Card text differences** | TravelHub card body text in Figma is 12 px (others 17 px) — looks like a leftover. I used 17 px everywhere. "Site system · 2024" is lowercase "site" in Figma; labels are uppercase on the site anyway. |

## Case-study pages (next phase) — will need

- **Video** (Suzuki gallery): 2.5 MB mp4 found in the file. Ships as muted looping video with a poster frame. Confirm it belongs to the Suzuki page.
- **Image budgets**: KKL has 18 images (8.3 MB raw), Suzuki 12 + video (14 MB raw). Both will be cut to ≤ 2.5 MB per page. Some 4096-px-tall screenshots will be shown at ~1000 px; if you want a zoom/lightbox on them, say so (the Figma prototype has overlays on KKL images).
- **Interactive tab components** appear in TravelHub, Bara and Suzuki (Figma "swap state" interactions). I'll build them as real tabs. Confirm which ones matter.
- **Hebrew screenshots** inside Suzuki mockups (RTL UI): stay as images, no RTL work needed.

## Not gaps, just FYI

- Fonts: Assistant (400/600/700/800) and Space Mono (400) — both on Google Fonts, loaded with `display=swap`.
- The "contact" frame in Figma is a copy of the About + Footer sections and is not linked from anywhere; the site uses `/#about` and `/#contact` anchors instead.
- 105 of the 155 images in the `.fig` are not used by any of the six final frames (drafts/components) and are ignored.
