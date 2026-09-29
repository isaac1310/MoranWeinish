/* Moran Weinish portfolio — the only JavaScript on the site.
   1. mobile nav drawer   2. back-to-top button   3. scroll reveal
   Everything degrades: with JS off the page is fully readable. */

(function () {
  'use strict';

  // 1. mobile nav
  var nav = document.querySelector('.nav');
  var toggle = document.querySelector('.nav-toggle');
  if (nav && toggle) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.querySelectorAll('.nav-drawer a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // 2. back to top.
  //    It takes the case study's own accent, except while it is sitting over
  //    the footer, where it takes the footer's — otherwise the green ring on
  //    KKL lands on the plum block and reads as a mistake.
  var toTop = document.querySelector('.to-top');
  if (toTop) {
    var footer = document.querySelector('.footer');
    // On a phone the button floats over the text you are reading, so there it
    // only appears while you scroll back up (or at the very end of the page)
    // and gets out of the way again as soon as you scroll down.
    var phone = window.matchMedia('(max-width: 767px)');
    var lastY = window.scrollY;
    var onScroll = function () {
      var y = window.scrollY, up = y < lastY - 2, down = y > lastY + 2;
      if (up || down) lastY = y;
      if (!phone.matches) {
        toTop.classList.toggle('show', y > 600);
      } else {
        var atEnd = y + window.innerHeight >= document.documentElement.scrollHeight - 40;
        if (y <= 600) toTop.classList.remove('show');
        else if (up || atEnd) toTop.classList.add('show');
        else if (down) toTop.classList.remove('show');
      }
      if (!footer) return;
      var b = toTop.getBoundingClientRect();
      toTop.classList.toggle('on-footer', footer.getBoundingClientRect().top < b.bottom);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    toTop.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // 3. scroll reveal.
  //    The CSS only hides .reveal once <html> has .reveal-ready, so the class
  //    goes on at the last possible moment and comes straight back off if
  //    anything here fails. A blank page is never an acceptable failure mode.
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = document.querySelectorAll('.reveal:not(.chips)');
  var chipRows = document.querySelectorAll('.chips.reveal');
  var root = document.documentElement;
  if (reduce || !('IntersectionObserver' in window)) return;

  function playChips(el) {
    el.classList.remove('in');
    void el.offsetWidth;
    el.classList.add('in');
  }

  root.classList.add('reveal-ready');

  if (chipRows.length) {
    // Chip rows are ~40px tall. threshold: 0.6 plus a shrunk root meant they
    // could scroll through the viewport without ever intersecting "enough",
    // so .in never landed and the stagger never ran. Fire once the row sits
    // in the middle band, and restart the animation each time it does.
    var chipIO = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        playChips(en.target);
        chipIO.unobserve(en.target);
      });
    }, { rootMargin: '-8% 0px -22% 0px', threshold: 0 });
    chipRows.forEach(function (ul) { chipIO.observe(ul); });

    // The CSS hides the chips until .in lands, so if this observer ever fails
    // to fire the row is invisible rather than merely unanimated — the same
    // failure mode that once shipped four blank pages. Play any row that is on
    // screen and has not played yet, on scroll and shortly after load.
    var chipFailsafe = function () {
      chipRows.forEach(function (ul) {
        if (ul.classList.contains('in')) return;
        var r = ul.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) { playChips(ul); }
      });
    };
    window.addEventListener('scroll', chipFailsafe, { passive: true });
    window.setTimeout(chipFailsafe, 2000);
  }

  if (!items.length) return;

  function showAll() {
    items.forEach(function (el) { el.classList.add('in'); });
  }
  try {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
    items.forEach(function (el) { io.observe(el); });
    // Failsafe. The observer can miss an element when the layout settles after
    // load (images and inline SVG changing heights), and it only ever fires
    // once per element — so shortly after load, reveal anything that is on
    // screen but still hidden. Checking per element rather than "did anything
    // reveal at all" matters: one revealed element used to switch this off for
    // every other one.
    window.setTimeout(function () {
      items.forEach(function (el) {
        if (el.classList.contains('in')) return;
        var r = el.getBoundingClientRect();
        if (r.bottom > 0 && r.top < (window.innerHeight || 0)) { el.classList.add('in'); }
      });
    }, 2500);
  } catch (e) {
    root.classList.remove('reveal-ready');
    showAll();
  }
})();

/* 4. lightbox for case-study screenshots (.shot img)
      Click the image once to zoom to full resolution, then drag to pan.
      Click again (or Esc / the X / the backdrop) to zoom out and close. */
(function () {
  'use strict';
  // Suzuki's carousel and before/after images are photos too (Itzik: tapping one did nothing)
  var imgs = document.querySelectorAll('.shot img, .cs-hero-shot img, .gallery .slide img, .ba img');
  if (!imgs.length) return;
  var box = document.createElement('div');
  box.className = 'lightbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-label', 'Enlarged screenshot');
  box.innerHTML = '<div class="stage"><img alt=""><button type="button" aria-label="Close">\u00d7</button></div><span class="zoom-hint"></span>';
  document.body.appendChild(box);
  var big = box.querySelector('img');
  var hint = box.querySelector('.zoom-hint');
  var closeBtn = box.querySelector('button');

  function setHint() {
    hint.textContent = box.classList.contains('zoomed') ? 'Drag to pan · click to zoom out' : 'Click to zoom in';
  }
  function unzoom() {
    box.classList.remove('zoomed');
    box.scrollTop = 0; box.scrollLeft = 0;
    setHint();
  }
  function close() {
    box.classList.remove('open');
    unzoom();
    big.src = '';
    document.body.style.overflow = '';
  }
  function zoomAt(e) {
    // keep the clicked point under the cursor when zooming in
    var r = big.getBoundingClientRect();
    var fx = (e.clientX - r.left) / r.width;
    var fy = (e.clientY - r.top) / r.height;
    box.classList.add('zoomed');
    setHint();
    box.scrollLeft = fx * big.scrollWidth - box.clientWidth / 2;
    box.scrollTop = fy * big.scrollHeight - box.clientHeight / 2;
  }

  imgs.forEach(function (im) {
    im.addEventListener('click', function () {
      // a swipe on the carousel ends in a click too — that one changes slide, it doesn't open
      var st = im.closest('.stage');
      if (st && Date.now() - (+st.getAttribute('data-swiped') || 0) < 500) return;
      big.src = im.currentSrc || im.src; big.alt = im.alt;
      box.classList.add('open'); unzoom();
      document.body.style.overflow = 'hidden';
    });
  });

  big.addEventListener('click', function (e) {
    e.stopPropagation();
    if (box.classList.contains('zoomed')) unzoom(); else zoomAt(e);
  });

  // drag to pan while zoomed
  var down = false, sx = 0, sy = 0, sl = 0, st = 0, moved = 0;
  box.addEventListener('pointerdown', function (e) {
    if (!box.classList.contains('zoomed')) return;
    down = true; moved = 0;
    sx = e.clientX; sy = e.clientY; sl = box.scrollLeft; st = box.scrollTop;
    box.classList.add('dragging');
    box.setPointerCapture(e.pointerId);
  });
  box.addEventListener('pointermove', function (e) {
    if (!down) return;
    var dx = e.clientX - sx, dy = e.clientY - sy;
    moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
    box.scrollLeft = sl - dx; box.scrollTop = st - dy;
  });
  box.addEventListener('pointerup', function (e) {
    if (!down) return;
    down = false;
    box.classList.remove('dragging');
    if (box.hasPointerCapture && box.hasPointerCapture(e.pointerId)) box.releasePointerCapture(e.pointerId);
    if (moved > 6) e.stopPropagation();
  }, true);

  closeBtn.addEventListener('click', function (e) { e.stopPropagation(); close(); });
  box.addEventListener('click', function () { if (moved <= 6) close(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' || !box.classList.contains('open')) return;
    if (box.classList.contains('zoomed')) unzoom(); else close();
  });
})();

/* 5. screen placeholders: if an exported screen PNG is missing, show a labelled frame instead of a broken image */
(function () {
  'use strict';
  document.querySelectorAll('.screen .ph img').forEach(function (im) {
    function fallback() {
      var d = document.createElement('div');
      d.className = 'missing';
      d.textContent = 'Export from Figma → ' + im.getAttribute('src').split('/').pop();
      im.replaceWith(d);
    }
    if (im.complete && im.naturalWidth === 0) fallback(); else im.addEventListener('error', fallback);
  });
})();

/* 6. simple gallery (Suzuki): arrows on the image, swipe, ←/→, dots; loops.
      Plays the video only on its slide. Without JS the first slide and its
      caption are already in the markup (.on) and the arrows stay hidden. */
(function () {
  'use strict';
  document.querySelectorAll('.gallery').forEach(function (g) {
    var slides = g.querySelectorAll('.slide'), dots = g.querySelector('.dots'), i = 0;
    var stage = g.querySelector('.stage'), cap = g.querySelector('.cap');
    var caps = cap ? cap.querySelectorAll(':scope > span') : [];
    if (!slides.length) return;
    if (dots) slides.forEach(function (_, k) { var d = document.createElement('i'); if (!k) d.className = 'on'; dots.appendChild(d); });
    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        s.classList.toggle('on', k === i);
        var v = s.querySelector('video'); if (v) { if (k === i) { v.play().catch(function () {}); } else { v.pause(); } }
      });
      if (dots) dots.querySelectorAll('i').forEach(function (d, k) { d.classList.toggle('on', k === i); });
      if (caps.length) caps.forEach(function (c, k) { c.classList.toggle('on', k === i); });
      else if (cap) cap.innerHTML = slides[i].getAttribute('data-cap') || '';
    }
    var prev = g.querySelector('.prev'), next = g.querySelector('.next');
    if (prev) prev.addEventListener('click', function () { show(i - 1); });
    if (next) next.addEventListener('click', function () { show(i + 1); });

    // ←/→ while the carousel (or one of its arrows) has focus
    if (!g.hasAttribute('tabindex')) g.setAttribute('tabindex', '0');
    g.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { e.preventDefault(); show(i - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); show(i + 1); }
    });

    // swipe. The stage has touch-action: pan-y, so a vertical drag still scrolls
    // the page; only a mostly-horizontal move past the threshold changes slide.
    if (stage && window.PointerEvent) {
      var sx = 0, sy = 0, id = null;
      stage.addEventListener('pointerdown', function (e) {
        if (e.button > 0 || e.target.closest('button')) return;
        id = e.pointerId; sx = e.clientX; sy = e.clientY;
      });
      stage.addEventListener('pointerup', function (e) {
        if (e.pointerId !== id) return;
        id = null;
        var dx = e.clientX - sx, dy = e.clientY - sy;
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) {
          stage.setAttribute('data-swiped', Date.now());
          show(dx < 0 ? i + 1 : i - 1);
        }
      });
      stage.addEventListener('pointercancel', function () { id = null; });
    }

    g.classList.add('ready');
    show(0);
  });
})();
