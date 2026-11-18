(function () {
  var p = String(window.__RX_TEST_PATH || location.pathname || '');
  if (/^\/(console|uc|admin)(\/|$)/.test(p)) return;
  var VALID = { pop: 1, ink: 1, luxe: 1, plain: 1 };
  function rc(k) {
    var m = document.cookie.match(new RegExp('(?:^|;\\s*)' + k + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }
  var skin = rc('rx_skin');
  if (!VALID[skin]) {
    try { skin = localStorage.getItem('rx_skin') || localStorage.getItem('rx-skin') || ''; } catch (e) {}
  }
  if (!VALID[skin]) skin = 'pop';

  var th = rc('rx_theme');
  if (th !== 'dark' && th !== 'light') {
    try {
      var hs = localStorage.getItem('rx_theme') || localStorage.getItem('rx-theme') || localStorage.getItem('color-scheme') || '';
      if (hs === 'dark' || hs === 'light') th = hs;
    } catch (e) {}
  }
  var root = document.documentElement;
  var dt = root.getAttribute('data-theme') || '';
  var isDark = th === 'dark'
    ? true
    : th === 'light'
      ? false
      : dt.indexOf('dark') === 0
        ? true
        : dt.indexOf('light') === 0
          ? false
          : root.classList.contains('dark') || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);

  root.setAttribute('data-rx-skin', skin);
  root.classList.toggle('rx-dark', !!isDark);
  if (dt) {
    root.setAttribute('data-theme', isDark ? 'dark' : 'light');
  } else if (th === 'dark' || th === 'light') {
    root.classList.toggle('dark', isDark);
    try { localStorage.setItem('color-scheme', isDark ? 'dark' : 'light'); } catch (e) {}
  }
})();
