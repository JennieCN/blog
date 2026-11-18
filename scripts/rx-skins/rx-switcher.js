/* ==========================================================================
   融夕的书 · CC 四套皮肤跨站切换器与动效控制器 (rx-switcher.js)
   兼容 Halo (blog.mycampusmail.com) 与 Flarum 2.0 (qa.mycampusmail.com)
   ========================================================================== */
(function () {
  'use strict';

  var pathname = String(window.__RX_TEST_PATH || location.pathname || '');
  if (/^\/(console|uc|admin)(\/|$)/.test(pathname)) return;

  var SKIN_META = [
    { id: 'pop', name: '撞色', icon: 'square' },
    { id: 'ink', name: '水墨', icon: 'brush' },
    { id: 'luxe', name: '夕照', icon: 'sparkles' },
    { id: 'plain', name: '素色', icon: 'palette' }
  ];
  var SKIN_IDS = SKIN_META.map(function (s) { return s.id; });

  var ICONS = {
    square: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="2.5"/><path d="M4 9h16"/></svg>',
    brush: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 4c-3.5 1.2-7.6 5-9.6 7.9l1.7 1.7C15 11.6 18.8 7.5 20 4z"/><path d="M10.4 11.9c-2 .2-3.4 1.6-3.6 3.6-.2 1.8-1 2.8-2.8 3.5 3.6 1.3 7.6.4 8.1-3.4z"/></svg>',
    sparkles: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"/><path d="M19 16l.9 2.1L22 19l-2.1.9L19 22l-.9-2.1L16 19l2.1-.9L19 16z"/></svg>',
    palette: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 0 0 0 18c1.2 0 1.8-.8 1.8-1.7 0-1.3-1-1.6-1-2.6 0-.9.7-1.6 1.6-1.6H16a5 5 0 0 0 5-5C21 6.4 17 3 12 3z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="14.5" cy="7" r="1"/></svg>',
    sun: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    moon: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>',
    x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12"/></svg>'
  };

  var root = document.documentElement;
  var syncingAttr = false;
  var activeVt = null;
  var initialAttr = root.getAttribute('data-rx-skin') || '';
  var currentSkinState = SKIN_IDS.indexOf(initialAttr) >= 0 ? initialAttr : 'pop';
  var currentThemeState = root.classList.contains('rx-dark') ? 'dark' : 'light';

  function reducedMotion() {
    return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  }

  function esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function writeCrossCookie(name, value) {
    var encoded = encodeURIComponent(value);
    var base = name + '=' + encoded + '; Path=/; Max-Age=31536000; SameSite=Lax';
    var host = String(location.hostname || '');
    if (host === 'mycampusmail.com' || /\.mycampusmail\.com$/i.test(host)) {
      document.cookie = base + '; Domain=.mycampusmail.com; Secure';
    } else {
      document.cookie = base;
    }
    try { localStorage.setItem(name, value); } catch (e) {}
  }

  function readCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|;\\s*)' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  function isFlarumPage() {
    return !!(root.hasAttribute('data-theme') || document.querySelector('.App-header, #app.App'));
  }

  function getSkin() {
    var attr = root.getAttribute('data-rx-skin') || '';
    if (!activeVt && SKIN_IDS.indexOf(attr) >= 0) {
      currentSkinState = attr;
    }
    return currentSkinState;
  }

  function getSkinMeta(id) {
    for (var i = 0; i < SKIN_META.length; i++) {
      if (SKIN_META[i].id === id) return SKIN_META[i];
    }
    return SKIN_META[0];
  }

  function nextSkin() {
    var cur = getSkin();
    var idx = SKIN_IDS.indexOf(cur);
    return SKIN_IDS[(idx + 1) % SKIN_IDS.length];
  }

  function getTheme() {
    if (!activeVt) {
      currentThemeState = root.classList.contains('rx-dark') ? 'dark' : 'light';
    }
    return currentThemeState;
  }

  function themeReveal(updateFn, originEl) {
    if (!document.startViewTransition || reducedMotion() || !originEl || document.visibilityState === 'hidden') {
      updateFn();
      return;
    }
    if (activeVt && typeof activeVt.skipTransition === 'function') {
      try { activeVt.skipTransition(); } catch (e) {}
      activeVt = null;
      root.classList.remove('fx-theme-vt');
      updateFn();
      return;
    }
    var r = originEl.getBoundingClientRect
      ? originEl.getBoundingClientRect()
      : { left: window.innerWidth - 60, top: 30, width: 0, height: 0 };
    var x = r.left + r.width / 2;
    var y = r.top + r.height / 2;
    var end = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    root.classList.add('fx-theme-vt');
    try {
      var vt = document.startViewTransition(updateFn);
      activeVt = vt;
      vt.ready.then(function () {
        root.animate(
          { clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + end + 'px at ' + x + 'px ' + y + 'px)'] },
          { duration: 440, easing: 'cubic-bezier(.22, 1, .36, 1)', pseudoElement: '::view-transition-new(root)' }
        );
      }).catch(function () {});
      vt.finished.finally(function () {
        if (activeVt === vt) activeVt = null;
        root.classList.remove('fx-theme-vt');
      });
    } catch (e) {
      activeVt = null;
      root.classList.remove('fx-theme-vt');
      updateFn();
    }
  }

  /* ---------------- Toast 提示条 ---------------- */
  var toastTimer = null;
  function ensureToastEl() {
    var el = document.getElementById('rx-toast');
    if (el) return el;
    var wrap = document.createElement('div');
    wrap.className = 'rx-toast-wrap';
    wrap.setAttribute('aria-live', 'polite');
    el = document.createElement('div');
    el.id = 'rx-toast';
    el.className = 'rx-toast';
    el.hidden = true;
    wrap.appendChild(el);
    document.body.appendChild(wrap);
    return el;
  }

  function toast(msg) {
    if (!document.body) return;
    var el = ensureToastEl();
    clearTimeout(toastTimer);
    el.innerHTML = '<span>' + esc(msg) + '</span>' +
      '<button type="button" class="rx-toast-close" aria-label="关闭提示">' + ICONS.x + '</button>';
    el.hidden = false;
    var closeBtn = el.querySelector('.rx-toast-close');
    if (closeBtn) {
      closeBtn.onclick = function () {
        clearTimeout(toastTimer);
        el.hidden = true;
      };
    }
    toastTimer = setTimeout(function () { el.hidden = true; }, 3000);
  }

  /* ---------------- 彩纸粒子 (签到庆贺) ---------------- */
  var particleLayer = null;
  function confetti(originEl) {
    if (reducedMotion() || !document.body) return;
    var r = originEl && originEl.getBoundingClientRect
      ? originEl.getBoundingClientRect()
      : { left: window.innerWidth / 2, top: 60, width: 0, height: 0 };
    var ox = r.left + r.width / 2;
    var oy = r.top + r.height / 2;
    if (!particleLayer) {
      particleLayer = document.createElement('div');
      particleLayer.className = 'fx-layer';
      particleLayer.setAttribute('aria-hidden', 'true');
      document.body.appendChild(particleLayer);
    }
    var colors = ['#ffd23f', '#f2894f', '#b5291c', '#2a7444', '#4493f8'];
    for (var i = 0; i < 24; i++) {
      var bit = document.createElement('span');
      bit.className = 'fx-bit';
      bit.style.background = colors[i % colors.length];
      bit.style.left = ox + 'px';
      bit.style.top = oy + 'px';
      particleLayer.appendChild(bit);
      var angle = (-Math.PI / 2) + (Math.random() - 0.5) * 1.9;
      var dist = 55 + Math.random() * 110;
      var dx = Math.cos(angle) * dist;
      var dy = Math.sin(angle) * dist + 45;
      if (bit.animate) {
        bit.animate(
          [
            { transform: 'translate(0, 0) rotate(0deg) scale(1)', opacity: 1 },
            { transform: 'translate(' + dx.toFixed(1) + 'px, ' + dy.toFixed(1) + 'px) rotate(' + Math.round(Math.random() * 360) + 'deg) scale(.4)', opacity: 0 }
          ],
          { duration: 750 + Math.random() * 350, easing: 'cubic-bezier(.16, 1, .3, 1)' }
        ).onfinish = function () {
          if (this.effect && this.effect.target) this.effect.target.remove();
        };
      } else {
        bit.remove();
      }
    }
  }

  /* ---------------- 按钮文案与图标同步 ---------------- */
  function syncButtonLabels() {
    var curMeta = getSkinMeta(currentSkinState);
    var nxtIdx = (SKIN_IDS.indexOf(currentSkinState) + 1) % SKIN_IDS.length;
    var nxtMeta = getSkinMeta(SKIN_IDS[nxtIdx]);
    var isDark = currentThemeState === 'dark';

    ['rx-skin-toggle', 'rx-skin-toggle-m'].forEach(function (id) {
      var btn = document.getElementById(id);
      if (!btn) return;
      btn.innerHTML = ICONS[curMeta.icon] + '<span class="rx-btn-label">' + curMeta.name + '</span>';
      btn.title = '当前「' + curMeta.name + '」风格，点击切换到「' + nxtMeta.name + '」';
      btn.setAttribute('aria-label', '切换到' + nxtMeta.name + '风格');
    });

    ['rx-theme-toggle', 'rx-theme-toggle-m'].forEach(function (id) {
      var btn = document.getElementById(id);
      if (!btn) return;
      btn.innerHTML = ICONS[isDark ? 'sun' : 'moon'];
      btn.title = isDark ? '切换到浅色模式' : '切换到深色模式';
      btn.setAttribute('aria-label', btn.title);
    });
  }

  function applySkinNow() {
    syncingAttr = true;
    root.setAttribute('data-rx-skin', currentSkinState);
    writeCrossCookie('rx_skin', currentSkinState);
    try { localStorage.setItem('rx-skin', currentSkinState); } catch (e) {}
    syncButtonLabels();
    syncingAttr = false;
  }

  function setSkin(id, originEl) {
    if (SKIN_IDS.indexOf(id) < 0) id = 'pop';
    currentSkinState = id;
    writeCrossCookie('rx_skin', id);
    try { localStorage.setItem('rx-skin', id); } catch (e) {}
    themeReveal(applySkinNow, originEl);
    toast('已切换至「' + getSkinMeta(id).name + '」风格');
  }

  function applyThemeNow(persist) {
    var isDark = currentThemeState === 'dark';
    syncingAttr = true;
    root.classList.toggle('rx-dark', isDark);
    if (isFlarumPage()) {
      root.setAttribute('data-theme', isDark ? 'dark' : 'light');
    } else {
      root.classList.toggle('dark', isDark);
      try { localStorage.setItem('color-scheme', isDark ? 'dark' : 'light'); } catch (e) {}
    }
    if (persist !== false) {
      writeCrossCookie('rx_theme', isDark ? 'dark' : 'light');
      try { localStorage.setItem('rx-theme', isDark ? 'dark' : 'light'); } catch (e) {}
    }
    syncButtonLabels();
    syncingAttr = false;
  }

  function setTheme(mode, originEl, persist) {
    currentThemeState = mode === 'dark' ? 'dark' : 'light';
    themeReveal(function () {
      applyThemeNow(persist);
    }, originEl);
  }

  function toggleTheme(originEl) {
    var next = getTheme() === 'dark' ? 'light' : 'dark';
    setTheme(next, originEl, true);
    toast(next === 'dark' ? '已切换至深色模式' : '已切换至浅色模式');
  }

  /* ---------------- 挂载阅读进度条与两站顶栏按钮 ---------------- */
  function ensureReadProgress() {
    if (!document.body || document.getElementById('rx-read-progress')) return;
    var bar = document.createElement('div');
    bar.id = 'rx-read-progress';
    bar.setAttribute('aria-hidden', 'true');
    document.body.insertBefore(bar, document.body.firstChild);

    var raf = 0;
    function paint() {
      raf = 0;
      var h = document.documentElement.scrollHeight - window.innerHeight;
      var p = h > 0 ? Math.min(1, Math.max(0, window.scrollY / h)) : 0;
      bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
    }
    function queue() {
      if (!raf) raf = requestAnimationFrame(paint);
    }
    window.addEventListener('scroll', queue, { passive: true });
    window.addEventListener('resize', queue, { passive: true });
    paint();
  }

  function mountHaloButtons() {
    var header = document.getElementById('header-menu');
    if (!header) return;
    if (!document.getElementById('rx-skin-toggle')) {
      var uls = header.querySelectorAll('ul');
      var actionUl = uls.length > 1 ? uls[1] : uls[0];
      if (actionUl && !actionUl.closest('nav')) {
        var li = document.createElement('li');
        li.className = 'rx-halo-skin-item flex items-center';
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.id = 'rx-skin-toggle';
        btn.className = 'rx-icon-btn';
        btn.addEventListener('click', function () {
          setSkin(nextSkin(), btn);
        });
        li.appendChild(btn);
        actionUl.insertBefore(li, actionUl.firstChild);
      } else {
        var bar = header.firstElementChild || header;
        var fallbackBtn = document.createElement('button');
        fallbackBtn.type = 'button';
        fallbackBtn.id = 'rx-skin-toggle';
        fallbackBtn.className = 'rx-icon-btn';
        fallbackBtn.addEventListener('click', function () {
          setSkin(nextSkin(), fallbackBtn);
        });
        bar.appendChild(fallbackBtn);
      }
    }

    var mobileNavUl = header.querySelector('nav ul');
    if (mobileNavUl && !document.getElementById('rx-skin-toggle-m')) {
      var mli = document.createElement('li');
      mli.className = 'py-2 flex items-center justify-between';
      var mSpan = document.createElement('span');
      mSpan.textContent = '界面皮肤风格';
      var mBtn = document.createElement('button');
      mBtn.type = 'button';
      mBtn.id = 'rx-skin-toggle-m';
      mBtn.className = 'rx-icon-btn';
      mBtn.addEventListener('click', function () {
        setSkin(nextSkin(), mBtn);
      });
      mli.appendChild(mSpan);
      mli.appendChild(mBtn);
      mobileNavUl.appendChild(mli);
    }
  }

  function mountFlarumButtons() {
    var controls = document.querySelector('.Header-secondary .Header-controls') || document.querySelector('.Header-controls');
    if (!controls) return;

    if (!document.getElementById('rx-skin-toggle')) {
      var skinLi = document.createElement('li');
      skinLi.className = 'item-rxSkin';
      var skinBtn = document.createElement('button');
      skinBtn.type = 'button';
      skinBtn.id = 'rx-skin-toggle';
      skinBtn.className = 'rx-icon-btn';
      skinBtn.addEventListener('click', function () {
        setSkin(nextSkin(), skinBtn);
      });
      skinLi.appendChild(skinBtn);
      controls.insertBefore(skinLi, controls.firstChild);
    }

    if (!document.getElementById('rx-theme-toggle')) {
      var themeLi = document.createElement('li');
      themeLi.className = 'item-rxTheme';
      var themeBtn = document.createElement('button');
      themeBtn.type = 'button';
      themeBtn.id = 'rx-theme-toggle';
      themeBtn.className = 'rx-icon-btn';
      themeBtn.addEventListener('click', function () {
        toggleTheme(themeBtn);
      });
      themeLi.appendChild(themeBtn);
      var skinItem = controls.querySelector('.item-rxSkin');
      if (skinItem && skinItem.nextSibling) {
        controls.insertBefore(themeLi, skinItem.nextSibling);
      } else {
        controls.appendChild(themeLi);
      }
    }
  }

  function mountButtons() {
    ensureReadProgress();
    mountHaloButtons();
    mountFlarumButtons();
    syncButtonLabels();
  }

  /* ---------------- 监听 Halo 原生暗色切换与 Flarum SPA 重绘 ---------------- */
  var rootObserver = new MutationObserver(function (mutations) {
    if (syncingAttr) return;
    for (var i = 0; i < mutations.length; i++) {
      var attr = mutations[i].attributeName;
      if (attr === 'class' && !isFlarumPage()) {
        var haloDark = root.classList.contains('dark');
        if (haloDark !== root.classList.contains('rx-dark')) {
          syncingAttr = true;
          currentThemeState = haloDark ? 'dark' : 'light';
          root.classList.toggle('rx-dark', haloDark);
          writeCrossCookie('rx_theme', haloDark ? 'dark' : 'light');
          syncButtonLabels();
          syncingAttr = false;
        }
      } else if (attr === 'data-theme' && isFlarumPage()) {
        var saved = readCookie('rx_theme');
        var dt = root.getAttribute('data-theme') || '';
        if ((saved === 'dark' || saved === 'light') && dt !== saved) {
          syncingAttr = true;
          currentThemeState = saved;
          root.setAttribute('data-theme', saved);
          root.classList.toggle('rx-dark', saved === 'dark');
          syncButtonLabels();
          syncingAttr = false;
        } else {
          var flarumDark = dt.indexOf('dark') === 0;
          if (flarumDark !== root.classList.contains('rx-dark')) {
            syncingAttr = true;
            currentThemeState = flarumDark ? 'dark' : 'light';
            root.classList.toggle('rx-dark', flarumDark);
            syncButtonLabels();
            syncingAttr = false;
          }
        }
      }
    }
  });
  rootObserver.observe(root, { attributes: true, attributeFilter: ['class', 'data-theme'] });

  var bodyObserverStarted = false;
  function startBodyObserver() {
    if (bodyObserverStarted || !document.body) return;
    bodyObserverStarted = true;
    var remountPending = false;
    var bodyObs = new MutationObserver(function () {
      if (remountPending) return;
      if (isFlarumPage() && (!document.getElementById('rx-skin-toggle') || !document.getElementById('rx-theme-toggle'))) {
        remountPending = true;
        requestAnimationFrame(function () {
          remountPending = false;
          mountButtons();
        });
      }
    });
    bodyObs.observe(document.body, { childList: true, subtree: true });
  }

  function boot() {
    if (!SKIN_IDS.includes(root.getAttribute('data-rx-skin') || '')) {
      currentSkinState = 'pop';
      root.setAttribute('data-rx-skin', 'pop');
    } else {
      currentSkinState = root.getAttribute('data-rx-skin');
    }
    var savedTheme = readCookie('rx_theme');
    if (isFlarumPage() && (savedTheme === 'dark' || savedTheme === 'light')) {
      currentThemeState = savedTheme;
      applyThemeNow(false);
    } else {
      currentThemeState = root.classList.contains('rx-dark') ? 'dark' : 'light';
    }
    mountButtons();
    startBodyObserver();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  window.RXSkins = {
    SKINS: SKIN_IDS.slice(),
    getSkin: getSkin,
    setSkin: setSkin,
    nextSkin: nextSkin,
    getTheme: getTheme,
    setTheme: setTheme,
    toggleTheme: toggleTheme,
    toast: toast,
    confetti: confetti,
    mountButtons: mountButtons
  };

  window.RXFX = {
    toast: toast,
    confetti: confetti,
    themeReveal: themeReveal,
    setSkin: setSkin,
    currentSkin: getSkin
  };
})();
