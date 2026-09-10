/* injected by tools/smoke.sh
   The failure this guards against: js/site.js loses its reveal block, nothing
   ever gets .in, and every .reveal element stays at opacity 0 forever — the
   page ships blank. So the check is "did the script reveal what is on screen",
   not "what is the opacity right now": CSS transitions do not advance under
   headless virtual time, so a freshly revealed element still reads as opacity 0.

   Elements below the fold are meant to stay hidden until scrolled to. */
window.addEventListener('load', function () {
  setTimeout(function () {
    var inView = 0, unrevealed = 0, offenders = [];
    document.querySelectorAll('.reveal').forEach(function (e) {
      var r = e.getBoundingClientRect();
      var vis = Math.min(r.bottom, window.innerHeight) - Math.max(r.top, 0);
      if (r.height <= 0 || vis / r.height < 0.15) return;   // not meaningfully on screen
      inView++;
      var shown = e.classList.contains('in') || +getComputedStyle(e).opacity > 0.05;
      if (!shown) { unrevealed++; offenders.push(e.className); }
    });
    document.title = 'SMOKE' + JSON.stringify({
      total: inView, hidden: unrevealed,
      all: document.querySelectorAll('.reveal').length,
      cls: document.documentElement.className, offenders: offenders
    }) + 'SMOKE';
  }, 4000);
});
