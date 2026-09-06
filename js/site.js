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

  // 2. back to top
  var toTop = document.querySelector('.to-top');
  if (toTop) {
    var onScroll = function () {
      toTop.classList.toggle('show', window.scrollY > 600);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    toTop.addEventListener('click', function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // 3. scroll reveal (skipped under reduced motion; CSS shows everything)
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var items = document.querySelectorAll('.reveal');
  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('in'); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
    });
  }, { rootMargin: '0px 0px -10% 0px', threshold: 0.1 });
  items.forEach(function (el) { io.observe(el); });
})();

/* 4. lightbox for case-study screenshots (.shot img) */
(function () {
  'use strict';
  var imgs = document.querySelectorAll('.shot img');
  if (!imgs.length) return;
  var box = document.createElement('div');
  box.className = 'lightbox';
  box.setAttribute('role', 'dialog');
  box.setAttribute('aria-label', 'Enlarged screenshot');
  box.innerHTML = '<img alt=""><button type="button" aria-label="Close">×</button>';
  document.body.appendChild(box);
  var big = box.querySelector('img');
  function close() { box.classList.remove('open'); big.src = ''; document.body.style.overflow = ''; }
  imgs.forEach(function (im) {
    im.addEventListener('click', function () {
      big.src = im.currentSrc || im.src; big.alt = im.alt;
      box.classList.add('open'); document.body.style.overflow = 'hidden';
    });
  });
  box.addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
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
