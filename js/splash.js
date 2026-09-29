/* Splash: plays on the first page of a visit and on every refresh, and is
   skipped when moving from page to page inside the site. Loaded synchronously
   in <head> so the class is on <html> before first paint — otherwise a skipped
   splash would flash for a frame. The splash itself is pure CSS (css/site.css)
   and lifts on its own; this file only skips it and handles click/key to skip.
   If this file fails, the splash still plays and still ends. */
(function () {
  'use strict';
  var root = document.documentElement;
  var reload = false;
  try {
    var nav = performance.getEntriesByType && performance.getEntriesByType('navigation')[0];
    reload = nav ? nav.type === 'reload' : (performance.navigation && performance.navigation.type === 1);
  } catch (e) { /* no Navigation Timing: treat as a normal load */ }
  try {
    if (sessionStorage.getItem('mw-splash') && !reload) root.classList.add('splash-seen');
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
    window.setTimeout(off, 4000);
  }
})();
