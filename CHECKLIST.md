# Launch checklist — moran-weinish.vercel.app

## A. Moran supplies (Figma exports → drop into the folder, tell Itzik)
- [x] ~~TravelHub screens~~ — not needed; rebuilt from the `.fig` as inline SVG. Was:
      `screen-01-trips-home.png` · `screen-02-trip-detail.png` · `screen-03-itinerary-day.png` ·
      `screen-04-itinerary-map.png` · `screen-05-budget.png` · `screen-06-bookings.png` · `screen-07-group.png`
      (Figma: select the phone "Background" frame inside each Container component → Export → PNG 2x)
- [x] ~~Suzuki icon row~~ — not needed; rendered from the `.fig` to `assets/img/suzuki/icons.png`
- [ ] Hero accent colour: select "simple." in Figma, read the Fill hex. `8A2C46` = OK, otherwise send the hex
- [ ] Suzuki gallery captions, slides 2–8: read and correct wording (`work/suzuki.html`, the `data-cap` texts)
- [ ] Bara logo at 2x -> `assets/img/bara/logo.webp` 438x140 (currently 219x70, soft on retina)
- [ ] (Optional) Bara card thumbnail at higher resolution (source is 600×320) → `assets/img/card-bara.webp` 750×400

## B. Review together — phone (Moran's) and desktop
Home
- [ ] Hero: text wraps well on phone, cards animation OK, buttons reachable
- [ ] "What I do" strip: two rows on phone is acceptable
- [ ] Four cards: images, order (KKL · TravelHub · Bara · Suzuki), hover on desktop
- [ ] About photo and text; skills grid; footer email opens mail app; LinkedIn opens; CV downloads
Case studies (each of the four)
- [ ] Reads top to bottom on phone without horizontal scroll
- [ ] Screenshots crop sensibly (top of image shown); tap → lightbox opens and closes
- [ ] Suzuki video autoplays muted on iPhone; prev/next gallery works
- [ ] "Back to portfolio" and "Next case study" go to the right place
- [ ] Copy: any typo or wording Moran wants changed → note page + section number

## C. Itzik, after A and B
- [ ] Wire in the exports, apply the review notes, push
- [x] Add `robots.txt` + `sitemap.xml`
- [x] Lighthouse (mobile) on the live URL → recorded in README. Home and all four case studies clear Accessibility and SEO; TravelHub (88) and Suzuki (89) sit just under the performance target — see the README note.
- [ ] Link preview: paste the URL into LinkedIn's post composer (don't post) → card shows title + og image
- [x] Final `diff` of nav/footer across all five files: footer byte-identical; nav differs only where it must — home links to `#work`/`#about`, case pages to `/#work`/`/#about` — plus whitespace.

## D. Parked (decided, not now)
- CV PDF: "Portfolio" link inside it points to the old Wix site; phone number is public. Replace the file when ready.
- Custom domain, analytics, contact form: out of scope.

## Go-live
- [ ] Moran puts `https://moran-weinish.vercel.app` in the CV as a link **and** as plain text
