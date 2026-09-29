/* Splash: once per browser session. Loaded synchronously in <head> so the
   class is on <html> before first paint — otherwise a repeat visit would flash
   the splash for a frame. The splash itself is pure CSS (css/site.css) and
   lifts on its own; this file only skips it on repeat visits and on a
   click/key. If this file fails, the splash still plays and still ends. */
(function () {
  'use strict';
  var root = document.documentElement;
  try {
    if (sessionStorage.getItem('mw-splash')) root.classList.add('splash-seen');
    else sessionStorage.setItem('mw-splash', '1');
  } catch (e) { /* storage blocked: the splash just plays every time */ }

  function skip() { root.classList.add('splash-skip'); off(); }
  function off() {
    document.removeEventListener('click', skip, true);
    document.removeEventListener('keydown', skip, true);
  }
  if (!root.classList.contains('splash-seen')) {
    document.addEventListener('click', skip, true);
    document.addEventListener('keydown', skip, true);
    // after the splash has lifted, clicks belong to the page again
    window.setTimeout(off, 2700);
  }
})();
