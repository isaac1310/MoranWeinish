/* Moran Weinish portfolio — the only JavaScript on the site.
   1. mobile nav drawer   2. back-to-top button   3. scroll reveal
   Everything degrades: with JS off the page is fully readable. */

/* 4. lightbox for case-study screenshots (.shot img)
      Click the image once to zoom to full resolution, then drag to pan.
      Click again (or Esc / the X / the backdrop) to zoom out and close. */
(function () {
  'use strict';
  var imgs = document.querySelectorAll('.shot img');
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

/* 6. simple gallery (Suzuki): prev/next, dots, plays the video only on its slide */
(function () {
  'use strict';
  document.querySelectorAll('.gallery').forEach(function (g) {
    var slides = g.querySelectorAll('.slide'), cap = g.querySelector('.cap'), dots = g.querySelector('.dots'), i = 0;
    if (!slides.length) return;
    slides.forEach(function (_, k) { var d = document.createElement('i'); if (!k) d.className = 'on'; dots.appendChild(d); });
    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) {
        s.classList.toggle('on', k === i);
        var v = s.querySelector('video'); if (v) { if (k === i) { v.play().catch(function () {}); } else { v.pause(); } }
      });
      dots.querySelectorAll('i').forEach(function (d, k) { d.classList.toggle('on', k === i); });
      cap.innerHTML = slides[i].getAttribute('data-cap') || '';
    }
    g.querySelector('.prev').addEventListener('click', function () { show(i - 1); });
    g.querySelector('.next').addEventListener('click', function () { show(i + 1); });
    show(0);
  });
})();
