/* 动效层、皮肤与主题切换、Ctrl/⌘ + K 命令面板（适配 Astro 多页应用） */
(function () {
  'use strict';

  var SKINS = [
    { id: 'pop', name: '撞色', icon: 'square' },
    { id: 'ink', name: '水墨', icon: 'brush' },
    { id: 'plain', name: '素色', icon: 'palette' },
  ];

  var DEFAULT_SECTIONS = [
    { key: 'vps', name: 'VPS 科普', description: '服务器选购、链路测速、网络代理与搭建避坑指南', url: '/vps/', icon: 'server' },
    { key: 'fsae', name: '大学生方程式赛车', description: 'FSAE 规则解析、设计报告、电控与机械调试记录', url: '/fsae/', icon: 'flag' },
    { key: 'rm', name: 'RoboMaster', description: 'RoboMaster 视觉、电控、机械结构与赛季经验总结', url: '/rm/', icon: 'cpu' },
    { key: 'ai', name: 'AI 工程实践', description: '大模型微调、Agent、RAG 与本地部署实战手记', url: '/ai/', icon: 'code' },
    { key: 'resources', name: '精选资源', description: '学习资料、开源工具整理与常用脚本索引', url: '/resources/', icon: 'book' },
  ];

  var ICONS = {
    home: '<path d="M3 10.5L12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/>',
    chat: '<path d="M21 12a8 8 0 0 1-8 8H4l2-4.2A8 8 0 1 1 21 12z"/>',
    book: '<path d="M4 5a2 2 0 0 1 2-2h5v17H6a2 2 0 0 0-2 1z"/><path d="M20 5a2 2 0 0 0-2-2h-5v17h5a2 2 0 0 1 2 1z"/>',
    server: '<rect x="3" y="4" width="18" height="7" rx="2"/><rect x="3" y="13" width="18" height="7" rx="2"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    cpu: '<rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 2v4M15 2v4M9 18v4M15 18v4M2 9h4M2 15h4M18 9h4M18 15h4"/>',
    code: '<path d="M8 7l-5 5 5 5M16 7l5 5-5 5"/>',
    feather: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    flag: '<path d="M5 21V4"/><path d="M5 4h12l-2.5 4L17 12H5"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    keyboard: '<rect x="2" y="6" width="20" height="12" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 14h10"/>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4l-5.6 5.6a1.5 1.5 0 0 0 2.1 2.1l5.6-5.6a4 4 0 0 0 5.4-5.4l-2.3 2.3-2.1-2.1z"/>',
    brush: '<path d="M20 4c-3.5 1.2-7.6 5-9.6 7.9l1.7 1.7C15 11.6 18.8 7.5 20 4z"/><path d="M10.4 11.9c-2 .2-3.4 1.6-3.6 3.6-.2 1.8-1 2.8-2.8 3.5 3.6 1.3 7.6.4 8.1-3.4z"/>',
    square: '<rect x="4" y="4" width="16" height="16" rx="2.5"/><path d="M4 9h16"/>',
    palette: '<path d="M12 3a9 9 0 0 0 0 18c1.2 0 1.8-.8 1.8-1.7 0-1.3-1-1.6-1-2.6 0-.9.7-1.6 1.6-1.6H16a5 5 0 0 0 5-5C21 6.4 17 3 12 3z"/><circle cx="7.5" cy="11" r="1"/><circle cx="10" cy="7" r="1"/><circle cx="14.5" cy="7" r="1"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    x: '<path d="M18 6L6 18M6 6l12 12"/>',
  };

  function svg(name) {
    return '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + (ICONS[name] || '') + '</svg>';
  }

  function esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  var root = document.documentElement;
  var reduced = function () { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; };
  var fine = function () { return window.matchMedia('(hover: hover) and (pointer: fine)').matches; };

  /* ---------- Toast 提示条 ---------- */
  var toastTimer = null;
  function toast(msg) {
    var el = document.getElementById('toast');
    if (!el) return;
    clearTimeout(toastTimer);
    el.innerHTML = '<span>' + esc(msg) + '</span>' +
      '<button type="button" class="toast-close" aria-label="关闭提示">' + svg('x') + '</button>';
    el.hidden = false;
    var closeBtn = el.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        clearTimeout(toastTimer);
        el.hidden = true;
      });
    }
    toastTimer = setTimeout(function () { el.hidden = true; }, 3200);
  }

  /* ---------- 主题与皮肤圆形切换 ---------- */
  function themeReveal(update, origin) {
    if (!document.startViewTransition || reduced()) { update(); return; }
    var r = origin && origin.getBoundingClientRect
      ? origin.getBoundingClientRect()
      : { left: window.innerWidth - 60, top: 30, width: 0, height: 0 };
    var x = r.left + r.width / 2;
    var y = r.top + r.height / 2;
    var end = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    root.classList.add('fx-theme-vt');
    try {
      var vt = document.startViewTransition(update);
      vt.ready.then(function () {
        document.documentElement.animate(
          { clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + end + 'px at ' + x + 'px ' + y + 'px)'] },
          { duration: 480, easing: 'cubic-bezier(.22, 1, .36, 1)', pseudoElement: '::view-transition-new(root)' }
        );
      }).catch(function () {});
      vt.finished.finally(function () { root.classList.remove('fx-theme-vt'); });
    } catch (e) {
      root.classList.remove('fx-theme-vt');
      update();
    }
  }

  function currentSkin() {
    return root.dataset.skin || 'pop';
  }

  function nextSkin() {
    var cur = currentSkin();
    for (var i = 0; i < SKINS.length; i++) {
      if (SKINS[i].id === cur) return SKINS[(i + 1) % SKINS.length];
    }
    return SKINS[0];
  }

  function syncSkinButtons() {
    var nxt = nextSkin();
    var activeSkin = SKINS.find(function (s) { return s.id === currentSkin(); }) || SKINS[0];
    ['skin-toggle', 'skin-toggle-m'].forEach(function (id) {
      var btn = document.getElementById(id);
      if (!btn) return;
      var iconWrap = btn.querySelector('.skin-ic');
      var labelWrap = btn.querySelector('.skin-label');
      if (iconWrap) iconWrap.innerHTML = svg(nxt.icon);
      else if (!labelWrap) btn.innerHTML = svg(nxt.icon);
      if (labelWrap) labelWrap.textContent = '风格：' + activeSkin.name;
      btn.setAttribute('aria-label', '切换到' + nxt.name + '风格');
      btn.title = '当前「' + activeSkin.name + '」风格，点击切换到「' + nxt.name + '」';
    });
  }

  function syncThemeButtons() {
    var isDark = root.classList.contains('dark');
    ['theme-toggle', 'theme-toggle-m'].forEach(function (id) {
      var btn = document.getElementById(id);
      if (!btn) return;
      var iconWrap = btn.querySelector('.theme-ic');
      if (iconWrap) iconWrap.innerHTML = svg(isDark ? 'sun' : 'moon');
      else btn.innerHTML = svg(isDark ? 'sun' : 'moon');
      btn.setAttribute('aria-label', isDark ? '切换到浅色' : '切换到深色');
      btn.title = isDark ? '切换到浅色' : '切换到深色';
    });
  }

  function setSkin(id, origin) {
    themeReveal(function () {
      root.dataset.skin = id;
      SKINS.forEach(function (s) {
        var link = document.getElementById('skin-' + s.id);
        if (link) link.disabled = s.id !== id;
      });
      try { localStorage.setItem('rx-skin', id); } catch (e) {}
      syncSkinButtons();
    }, origin);
    var skinObj = SKINS.find(function (s) { return s.id === id; });
    if (skinObj) toast('已切换至「' + skinObj.name + '」风格');
  }

  function toggleTheme(origin) {
    themeReveal(function () {
      var isDark = root.classList.toggle('dark');
      var val = isDark ? 'dark' : 'light';
      try {
        localStorage.setItem('rx-theme', val);
        localStorage.setItem('theme', val);
      } catch (e) {}
      syncThemeButtons();
    }, origin);
  }

  syncSkinButtons();
  syncThemeButtons();

  document.addEventListener('click', function (e) {
    var themeBtn = e.target.closest('#theme-toggle, #theme-toggle-m');
    if (themeBtn) { toggleTheme(themeBtn); return; }
    var skinBtn = e.target.closest('#skin-toggle, #skin-toggle-m');
    if (skinBtn) { setSkin(nextSkin().id, skinBtn); return; }
  });

  /* ---------- 粒子动画（签到彩纸） ---------- */
  var layer = null;
  function fxLayer() {
    if (layer) return layer;
    layer = document.createElement('div');
    layer.className = 'fx-layer';
    layer.setAttribute('aria-hidden', 'true');
    document.body.appendChild(layer);
    return layer;
  }

  function confetti(origin) {
    if (reduced() || !origin || !origin.getBoundingClientRect) return;
    var r = origin.getBoundingClientRect();
    var ox = r.left + r.width / 2;
    var oy = r.top + r.height / 2;
    var colors = ['#ffd23f', '#f2894f', '#c2456b', '#2a7444', '#60a5fa'];
    var host = fxLayer();
    for (var i = 0; i < 24; i++) {
      var bit = document.createElement('span');
      bit.className = 'fx-bit';
      bit.style.background = colors[i % colors.length];
      bit.style.left = ox + 'px';
      bit.style.top = oy + 'px';
      host.appendChild(bit);
      var angle = (-Math.PI / 2) + (Math.random() - 0.5) * 1.9;
      var dist = 55 + Math.random() * 110;
      var dx = Math.cos(angle) * dist;
      var dy = Math.sin(angle) * dist + 45;
      bit.animate(
        [
          { transform: 'translate(0, 0) rotate(0deg) scale(1)', opacity: 1 },
          { transform: 'translate(' + dx.toFixed(1) + 'px, ' + dy.toFixed(1) + 'px) rotate(' + Math.round(Math.random() * 360) + 'deg) scale(.4)', opacity: 0 },
        ],
        { duration: 750 + Math.random() * 350, easing: 'cubic-bezier(.16, 1, .3, 1)' }
      ).onfinish = function () { this.effect.target.remove(); };
    }
  }

  /* ---------- 光标光晕、磁吸按钮与 Hero 视差 ---------- */
  var SPOT = '.card, .stream-item, .section-card, .post-nav a';
  var RIM = '.card, .thread';
  var magnet = null;

  function decorate() {
    document.querySelectorAll(SPOT).forEach(function (el) {
      el.classList.add('fx-spot');
      if (el.matches(RIM)) el.classList.add('fx-rim');
    });
  }
  decorate();

  if (fine() && !reduced()) {
    var pending = null;
    document.addEventListener('pointermove', function (e) {
      if (pending) return;
      pending = requestAnimationFrame(function () {
        pending = null;
        var card = e.target.closest && e.target.closest('.fx-spot');
        if (card) {
          var r = card.getBoundingClientRect();
          card.style.setProperty('--mx', (e.clientX - r.left).toFixed(1) + 'px');
          card.style.setProperty('--my', (e.clientY - r.top).toFixed(1) + 'px');
        }
        var btn = e.target.closest && e.target.closest('.btn-primary');
        if (magnet && magnet !== btn) { magnet.style.translate = ''; magnet = null; }
        if (btn) {
          var b = btn.getBoundingClientRect();
          var dx = e.clientX - (b.left + b.width / 2);
          var dy = e.clientY - (b.top + b.height / 2);
          btn.style.translate = (dx * 0.16).toFixed(1) + 'px ' + (dy * 0.24).toFixed(1) + 'px';
          magnet = btn;
        }
        var hero = e.target.closest && e.target.closest('.hall-head');
        var currentHero = document.querySelector('.hall-head');
        if (currentHero) {
          if (hero) {
            var h = hero.getBoundingClientRect();
            hero.style.setProperty('--px', (((e.clientX - h.left) / h.width - 0.5) * -22).toFixed(1) + 'px');
            hero.style.setProperty('--py', (((e.clientY - h.top) / h.height - 0.5) * -16).toFixed(1) + 'px');
          } else {
            currentHero.style.removeProperty('--px');
            currentHero.style.removeProperty('--py');
          }
        }
      });
    }, { passive: true });
    document.addEventListener('pointerleave', function () {
      if (magnet) { magnet.style.translate = ''; magnet = null; }
    });
  }

  /* ---------- 移动端侧栏抽屉（含焦点管理） ---------- */
  var drawerBtn = document.getElementById('drawer-btn');
  var sidebarEl = document.getElementById('sidebar');
  var scrim = document.getElementById('scrim');
  var lastDrawerFocus = null;

  function setDrawer(open, restoreFocus) {
    var wasOpen = document.body.classList.contains('drawer-open');
    if (open === wasOpen) return;
    document.body.classList.toggle('drawer-open', open);
    if (scrim) scrim.hidden = !open;
    if (drawerBtn) drawerBtn.setAttribute('aria-expanded', String(open));

    if (open && sidebarEl) {
      lastDrawerFocus = document.activeElement;
      requestAnimationFrame(function () {
        var first = sidebarEl.querySelector('.side-link[aria-current="page"], a.side-link, button.side-link');
        if (first && typeof first.focus === 'function') first.focus();
      });
    } else if (!open && restoreFocus) {
      var target = (lastDrawerFocus && document.contains(lastDrawerFocus) && lastDrawerFocus) || drawerBtn;
      if (target && typeof target.focus === 'function') target.focus();
      lastDrawerFocus = null;
    }
  }

  if (drawerBtn) {
    drawerBtn.addEventListener('click', function () {
      var open = !document.body.classList.contains('drawer-open');
      setDrawer(open, !open);
    });
  }
  if (scrim) scrim.addEventListener('click', function () { setDrawer(false, true); });
  if (sidebarEl) {
    sidebarEl.addEventListener('click', function (e) {
      if (document.body.classList.contains('drawer-open') && e.target.closest('a.side-link, a.btn')) {
        setDrawer(false, false);
      }
    });
  }

  /* ---------- Ctrl/⌘ + K 命令面板 ---------- */
  var indexData = null;
  var indexPromise = null;

  function loadIndex() {
    if (indexData) return Promise.resolve(indexData);
    if (!indexPromise) {
      indexPromise = fetch('/posts-index.json')
        .then(function (r) { return r.json(); })
        .then(function (d) { indexData = d; return d; })
        .catch(function () { return { sections: [], posts: [] }; });
    }
    return indexPromise;
  }

  var dlg = document.createElement('dialog');
  dlg.id = 'cmdk';
  dlg.className = 'cmdk';
  dlg.setAttribute('aria-label', '快捷跳转与命令');
  dlg.innerHTML =
    '<div class="cmdk-input">' + svg('search') +
    '<input id="cmdk-input" type="search" placeholder="搜索文章、板块、工具或切换风格…" autocomplete="off" role="combobox" aria-expanded="true" aria-controls="cmdk-list">' +
    '<kbd>Esc</kbd></div>' +
    '<ul id="cmdk-list" class="cmdk-list" role="listbox"></ul>' +
    '<div class="cmdk-foot"><span><kbd>↑</kbd><kbd>↓</kbd> 选择</span><span><kbd>Enter</kbd> 打开</span><span><kbd>Esc</kbd> 关闭</span></div>';
  document.body.appendChild(dlg);

  var input = document.getElementById('cmdk-input');
  var listEl = document.getElementById('cmdk-list');
  var results = [];
  var active = 0;

  function buildCommands() {
    var out = [
      { group: '前往', icon: 'home', label: '首页（双流动态）', hint: '/', run: function () { location.href = '/'; } },
      { group: '前往', icon: 'book', label: '全部专栏（按月归档）', hint: '/blog/', run: function () { location.href = '/blog/'; } },
      { group: '前往', icon: 'chat', label: '社区大厅（qa.mycampusmail.com）', hint: '/qa/', run: function () { location.href = '/qa/'; } },
      { group: '前往', icon: 'wrench', label: '实用工具箱（测速 / IP / 计算器）', hint: '/tools/', run: function () { location.href = '/tools/'; } },
      { group: '前往', icon: 'calendar', label: '建站日志', hint: '/timeline/', run: function () { location.href = '/timeline/'; } },
      { group: '前往', icon: 'info', label: '关于「融夕的书」', hint: '/about/', run: function () { location.href = '/about/'; } },
      { group: '前往', icon: 'search', label: '全站全文搜索（Pagefind）', hint: '/search/', run: function () { location.href = '/search/'; } },
      { group: '操作', icon: 'plus', label: '去社区登录 / 发帖提问', hint: 'qa.mycampusmail.com', run: function () { location.href = 'https://qa.mycampusmail.com/'; } },
      { group: '操作', icon: root.classList.contains('dark') ? 'sun' : 'moon', label: root.classList.contains('dark') ? '切换到浅色模式' : '切换到深色模式', run: function () { toggleTheme(document.getElementById('theme-toggle')); } },
      { group: '操作', icon: 'keyboard', label: '查看键盘快捷键', hint: '?', run: function () { var s = document.getElementById('shortcuts'); if (s && s.showModal) s.showModal(); } },
    ];
    SKINS.forEach(function (sk) {
      if (sk.id === currentSkin()) return;
      out.push({ group: '操作', icon: sk.icon, label: '切换到「' + sk.name + '」风格', run: function () { setSkin(sk.id, document.getElementById('skin-toggle')); } });
    });
    var sections = (indexData && Array.isArray(indexData.sections) && indexData.sections.length)
      ? indexData.sections
      : DEFAULT_SECTIONS;
    sections.forEach(function (s) {
      out.push({ group: '板块', icon: s.icon || 'book', label: s.name, hint: s.description, text: s.key, run: function () { location.href = s.url; } });
    });
    if (indexData && Array.isArray(indexData.posts)) {
      indexData.posts.forEach(function (p) {
        out.push({
          group: '专栏文章',
          icon: 'book',
          label: p.title,
          hint: p.sectionName + ' · ' + p.dateStr,
          text: (p.tags || []).join(' ') + ' ' + (p.description || ''),
          run: function () { location.href = p.url; },
        });
      });
    }
    return out;
  }

  function score(q, item) {
    var label = item.label.toLowerCase();
    var hay = label + ' ' + (item.text || '').toLowerCase() + ' ' + (item.hint || '').toLowerCase();
    var idx = label.indexOf(q);
    if (idx >= 0) return { s: 1000 - idx * 2 - label.length * 0.1, at: idx, len: q.length };
    if (hay.indexOf(q) >= 0) return { s: 500 };
    var pos = -1, gaps = 0;
    for (var i = 0; i < q.length; i++) {
      var next = label.indexOf(q[i], pos + 1);
      if (next < 0) return null;
      if (pos >= 0) gaps += next - pos - 1;
      pos = next;
    }
    return { s: 200 - gaps };
  }

  function labelHTML(r) {
    var l = r.item.label;
    if (r.m && r.m.at != null) {
      return esc(l.slice(0, r.m.at)) + '<mark>' + esc(l.slice(r.m.at, r.m.at + r.m.len)) + '</mark>' + esc(l.slice(r.m.at + r.m.len));
    }
    return esc(l);
  }

  function paint() {
    if (!results.length) {
      listEl.innerHTML = '<li class="cmdk-empty" role="presentation">没有直接命中。按 Enter 用 Pagefind 全文搜索「' + esc(input.value.trim()) + '」</li>';
      input.removeAttribute('aria-activedescendant');
      return;
    }
    var html = '';
    var group = '';
    results.forEach(function (r, i) {
      if (r.item.group !== group) {
        group = r.item.group;
        html += '<li class="cmdk-group" role="presentation">' + esc(group) + '</li>';
      }
      var hint = r.item.hint || '';
      if (hint.length > 22) hint = hint.slice(0, 22) + '…';
      html += '<li class="cmdk-item" role="option" id="cmdk-opt-' + i + '" data-i="' + i + '" aria-selected="' + (i === active) + '">' +
        svg(r.item.icon) +
        '<span class="cmdk-item-label">' + labelHTML(r) + '</span>' +
        (hint ? '<span class="cmdk-item-hint">' + esc(hint) + '</span>' : '') +
        '</li>';
    });
    listEl.innerHTML = html;
    input.setAttribute('aria-activedescendant', 'cmdk-opt-' + active);
  }

  function update() {
    var q = input.value.trim().toLowerCase();
    var all = buildCommands();
    if (!q) {
      var postCount = 0;
      results = all.filter(function (it) {
        if (it.group === '前往' || it.group === '操作' || it.group === '板块') return true;
        if (it.group === '专栏文章' && postCount++ < 5) return true;
        return false;
      }).map(function (it) { return { item: it, m: null }; });
    } else {
      results = all.map(function (it) { var m = score(q, it); return m ? { item: it, m: m } : null; })
        .filter(Boolean)
        .sort(function (a, b) { return b.m.s - a.m.s; })
        .slice(0, 28);
      var order = [];
      results.forEach(function (r) { if (order.indexOf(r.item.group) < 0) order.push(r.item.group); });
      results.sort(function (a, b) { return order.indexOf(a.item.group) - order.indexOf(b.item.group); });
    }
    active = 0;
    paint();
  }

  function setActive(i) {
    if (!results.length) return;
    active = (i + results.length) % results.length;
    listEl.querySelectorAll('.cmdk-item').forEach(function (li) {
      li.setAttribute('aria-selected', String(+li.dataset.i === active));
    });
    input.setAttribute('aria-activedescendant', 'cmdk-opt-' + active);
    var el = document.getElementById('cmdk-opt-' + active);
    if (el) el.scrollIntoView({ block: 'nearest' });
  }

  function runActive() {
    var r = results[active];
    var q = input.value.trim();
    dlg.close();
    if (r) r.item.run();
    else if (q) location.href = '/search/?q=' + encodeURIComponent(q);
  }

  function openPalette() {
    if (dlg.open) return;
    setDrawer(false, false);
    document.querySelectorAll('dialog[open]').forEach(function (d) { d.close(); });
    input.value = '';
    update();
    dlg.showModal();
    input.focus();
    loadIndex().then(function () { if (dlg.open) update(); });
  }

  input.addEventListener('input', update);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive(active + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive(active - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); runActive(); }
    else if (e.key === 'Escape') { e.preventDefault(); dlg.close(); }
  });
  listEl.addEventListener('pointermove', function (e) {
    var li = e.target.closest && e.target.closest('.cmdk-item');
    if (li && +li.dataset.i !== active) setActive(+li.dataset.i);
  });
  listEl.addEventListener('click', function (e) {
    var li = e.target.closest && e.target.closest('.cmdk-item');
    if (li) { active = +li.dataset.i; runActive(); }
  });
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });

  var searchTrigger = document.getElementById('nav-search-input');
  if (searchTrigger) {
    searchTrigger.addEventListener('focus', function () {
      searchTrigger.blur();
      openPalette();
    });
    searchTrigger.addEventListener('click', function (e) {
      e.preventDefault();
      openPalette();
    });
  }
  var cmdkTrigger = document.getElementById('cmdk-trigger');
  if (cmdkTrigger) cmdkTrigger.addEventListener('click', openPalette);

  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      if (dlg.open) dlg.close(); else openPalette();
      return;
    }
    if (e.key === 'Escape' && document.body.classList.contains('drawer-open')) {
      e.preventDefault();
      setDrawer(false, true);
      return;
    }
    var tag = document.activeElement && document.activeElement.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || (document.activeElement && document.activeElement.isContentEditable)) return;
    if (document.querySelector('dialog[open]')) return;
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      e.preventDefault();
      openPalette();
    } else if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
      var s = document.getElementById('shortcuts');
      if (s && s.showModal) { e.preventDefault(); s.showModal(); }
    }
  });

  window.RXFX = {
    toast: toast,
    confetti: confetti,
    themeReveal: themeReveal,
    openPalette: openPalette,
    setSkin: setSkin,
    currentSkin: currentSkin,
  };
})();
