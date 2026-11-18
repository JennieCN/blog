#!/usr/bin/env node
/**
 * Render templated VPS Markdown ({{ANCHOR:...}} / {{ANCHOR_SELF:...}}) into:
 *   1. Clean final Markdown (--out-md) for Astro / Git repository
 *   2. Frontmatter-stripped Markdown body (--out-body) for Halo raw content
 *   3. Halo HTML (--out-html) with:
 *      - Heading IDs emitted ONLY on h1/h2/h3 (converting h4..h6 to div[role="heading"] so Halo tocbot stays concise)
 *      - Styled <details>/<summary> collapsible benchmark blocks
 *      - Optional progressive interactive filter + expand/collapse toolbar (--inject-toolbar) with Light & Dark (html.dark) support
 *      - Strict 0-broken-anchor & <details> balance verification
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const nm = path.resolve(__dirname, '..', 'node_modules');

const { unified } = await import(path.join(nm, 'unified/index.js'));
const { default: remarkParse } = await import(path.join(nm, 'remark-parse/index.js'));
const { default: remarkGfm } = await import(path.join(nm, 'remark-gfm/index.js'));
const { default: remarkRehype } = await import(path.join(nm, 'remark-rehype/index.js'));
const { default: rehypeStringify } = await import(path.join(nm, 'rehype-stringify/index.js'));
const { default: GithubSlugger } = await import(path.join(nm, 'github-slugger/index.js'));

function parseArgs(argv) {
  const opts = {
    input: '',
    outMd: '',
    outBody: '',
    outHtml: '',
    expectedDetails: null,
    injectToolbar: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--') && !opts.input) opts.input = a;
    else if (a === '--out-md') opts.outMd = argv[++i];
    else if (a === '--out-body') opts.outBody = argv[++i];
    else if (a === '--out-html') opts.outHtml = argv[++i];
    else if (a === '--expected-details') opts.expectedDetails = Number(argv[++i]);
    else if (a === '--inject-toolbar') opts.injectToolbar = true;
    else throw new Error(`Unknown argument: ${a}`);
  }
  if (!opts.input || !opts.outHtml) {
    throw new Error('Usage: node scripts/render-halo-markdown.mjs <input.md> --out-html <out.html> [--out-md <final.md>] [--out-body <body.md>] [--expected-details N] [--inject-toolbar]');
  }
  return opts;
}

// Emit IDs only on h1..h3 so Halo theme-earth's tocbot sidebar doesn't index 450+ h4 review sub-items!
const HEADING_TAGS_WITH_ID = new Set(['h1', 'h2', 'h3']);

function textOf(node) {
  if (!node) return '';
  if (node.type === 'text') return node.value || '';
  if (Array.isArray(node.children)) return node.children.map(textOf).join('');
  return '';
}

function walk(node, fn) {
  fn(node);
  if (Array.isArray(node.children)) {
    for (const child of node.children) walk(child, fn);
  }
}

function splitFrontmatter(md) {
  const m = md.match(/^(---\n[\s\S]*?\n---\n)/);
  if (!m) return { frontmatter: '', body: md };
  return { frontmatter: m[1], body: md.slice(m[1].length) };
}

function buildInteractiveToolbarHtml(detailsCount) {
  const chips = [
    ['全部', ''],
    ['👑 皇冠/推荐', '皇冠'],
    ['9929 / CN2 / CMIN2', '9929|CN2|CMIN2|CTGGIA|专线'],
    ['4837 / 软银 / CMI', '4837|SoftBank|软银|CMI|IIJ|Lumen'],
    ['真家宽 / 商宽', 'Hinet|Seednet|HKT|AT&T|Verizon|Frontier|KDDI|夏威夷|家宽|商宽'],
    ['NAT 共享', 'NAT'],
    ['双 ISP 伪家宽', '双 ISP|伪家宽'],
    ['9950X / EPYC 性能', '9950X|7950X|EPYC|Turin|Genoa|RS 1000'],
    ['香港', '香港|HK'],
    ['日本', '日本|东京|大阪|JP'],
    ['台湾', '台湾|台北|彰化|Hinet|Seednet'],
    ['美国', '美国|洛杉矶|圣何塞|夏威夷|西雅图|达拉斯'],
    ['欧洲', '德国|法兰克福|英国|伦敦|荷兰|西班牙'],
  ];
  const chipBtns = chips
    .map(
      ([label, pat], idx) =>
        `<button type="button" class="vps-tb-chip${idx === 0 ? ' is-active' : ''}" data-vps-chip="${pat}">${label}</button>`
    )
    .join('');

  return `
<style>
#vps-quick-toolbar {
  margin: 16px 0 20px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8fafc;
  color: #0f172a;
}
#vps-quick-toolbar .vps-tb-input {
  width: 100%;
  padding: 7px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
  background: #ffffff;
  color: #0f172a;
}
#vps-quick-toolbar .vps-tb-input::placeholder {
  color: #64748b;
}
#vps-quick-toolbar .vps-tb-btn {
  padding: 7px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #475569;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
#vps-quick-toolbar .vps-tb-btn-primary {
  color: #0f172a;
  font-weight: 500;
}
#vps-quick-toolbar .vps-tb-btn:hover,
#vps-quick-toolbar .vps-tb-chip:hover {
  border-color: #94a3b8;
}
#vps-quick-toolbar .vps-tb-chip {
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #ffffff;
  color: #334155;
  font-size: 12px;
  line-height: 1.5;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
#vps-quick-toolbar .vps-tb-chip.is-active {
  background: #0f172a;
  border-color: #0f172a;
  color: #ffffff;
  font-weight: 600;
}
#vps-quick-toolbar #vps-filter-status {
  margin-top: 8px;
  font-size: 12.5px;
  color: #64748b;
}
.vps-review-subheading {
  margin: 1.25em 0 0.5em;
  font-size: 1.05em;
  font-weight: 700;
  line-height: 1.4;
  color: #0f172a;
}
html.dark #vps-quick-toolbar {
  background: #1e293b;
  border-color: #334155;
  color: #f1f5f9;
}
html.dark #vps-quick-toolbar .vps-tb-input {
  background: #0f172a;
  border-color: #475569;
  color: #f8fafc;
}
html.dark #vps-quick-toolbar .vps-tb-input::placeholder {
  color: #94a3b8;
}
html.dark #vps-quick-toolbar .vps-tb-btn {
  background: #0f172a;
  border-color: #475569;
  color: #cbd5e1;
}
html.dark #vps-quick-toolbar .vps-tb-btn-primary {
  color: #f8fafc;
}
html.dark #vps-quick-toolbar .vps-tb-btn:hover,
html.dark #vps-quick-toolbar .vps-tb-chip:hover {
  border-color: #64748b;
}
html.dark #vps-quick-toolbar .vps-tb-chip {
  background: #0f172a;
  border-color: #475569;
  color: #cbd5e1;
}
html.dark #vps-quick-toolbar .vps-tb-chip.is-active {
  background: #38bdf8;
  border-color: #38bdf8;
  color: #0f172a;
}
html.dark #vps-quick-toolbar #vps-filter-status {
  color: #94a3b8;
}
html.dark .vps-review-subheading {
  color: #f8fafc;
}
</style>
<div id="vps-quick-toolbar">
  <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;">
    <div style="flex:1 1 260px;display:flex;gap:8px;align-items:center;">
      <input id="vps-filter-input" class="vps-tb-input" type="search" placeholder="快速筛选分类表机型（如：9929、AT&T、台湾、9950X、NAT、DMIT…）" />
      <button id="vps-filter-clear" class="vps-tb-btn" type="button">清空</button>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
      <button id="vps-expand-all" class="vps-tb-btn vps-tb-btn-primary" type="button">展开全部报告原文（${detailsCount} 份）</button>
      <button id="vps-collapse-all" class="vps-tb-btn" type="button">全部收起</button>
    </div>
  </div>
  <div id="vps-chip-bar" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">${chipBtns}</div>
  <div id="vps-filter-status">当前显示全部分类机型条目（支持多关键词空格组合筛选，点击商家或机型直接跳转测评）</div>
</div>
<script>
(function(){
  var toolbar = document.getElementById('vps-quick-toolbar');
  if (!toolbar) return;
  var root = toolbar.parentElement;
  var input = document.getElementById('vps-filter-input');
  var clearBtn = document.getElementById('vps-filter-clear');
  var statusEl = document.getElementById('vps-filter-status');
  var expandBtn = document.getElementById('vps-expand-all');
  var collapseBtn = document.getElementById('vps-collapse-all');
  var chips = Array.prototype.slice.call(toolbar.querySelectorAll('[data-vps-chip]'));

  function getTaxonomyTables() {
    var tables = [];
    var started = false;
    var children = Array.prototype.slice.call(root.children);
    for (var i = 0; i < children.length; i++) {
      var el = children[i];
      if (el.tagName === 'H2') {
        var t = (el.textContent || '').trim();
        if (t.indexOf('一、') === 0 || t.indexOf('二、') === 0 || t.indexOf('三、') === 0 || t.indexOf('四、') === 0) {
          started = true;
        } else if (started) {
          break;
        }
      }
      if (started && el.tagName === 'TABLE') {
        var prev = el.previousElementSibling;
        var regionLabel = (prev && prev.tagName === 'P') ? (prev.textContent || '').trim() : '';
        tables.push({ table: el, regionP: (prev && prev.tagName === 'P' && prev.children.length === 1 && prev.children[0].tagName === 'STRONG') ? prev : null, regionText: regionLabel });
      }
    }
    return tables;
  }

  function applyFilter(rawQuery, regexMode) {
    var items = getTaxonomyTables();
    var q = (rawQuery || '').trim();
    var matched = 0, total = 0;
    var rx = null;
    var terms = [];
    if (q) {
      if (regexMode) {
        try { rx = new RegExp(q, 'i'); } catch (e) { rx = null; }
      } else {
        terms = q.toLowerCase().split(/\\s+/).filter(Boolean);
      }
    }
    items.forEach(function(item) {
      var rows = Array.prototype.slice.call(item.table.querySelectorAll('tbody tr'));
      var visibleInTable = 0;
      rows.forEach(function(tr) {
        total += 1;
        var hay = (item.regionText + ' ' + (tr.textContent || '')).toLowerCase();
        var ok = true;
        if (q) {
          if (rx) ok = rx.test(item.regionText + ' ' + (tr.textContent || ''));
          else ok = terms.every(function(term) { return hay.indexOf(term) !== -1; });
        }
        tr.style.display = ok ? '' : 'none';
        if (ok) { visibleInTable += 1; matched += 1; }
      });
      var showTbl = (!q || visibleInTable > 0);
      item.table.style.display = showTbl ? '' : 'none';
      if (item.regionP) item.regionP.style.display = showTbl ? '' : 'none';
    });
    if (!q) {
      statusEl.textContent = '当前显示全部分类表共 ' + total + ' 条机型记录（支持空格多词组合筛选，如：美国 家宽、香港 9929）';
    } else {
      statusEl.textContent = '筛选「' + q.replace(/\\|/g, ' / ') + '」：匹配 ' + matched + ' / ' + total + ' 条分类机型记录';
    }
  }

  function highlightChip(activeBtn) {
    chips.forEach(function(btn) {
      btn.classList.toggle('is-active', btn === activeBtn);
    });
  }

  input.addEventListener('input', function() {
    highlightChip(input.value.trim() ? null : chips[0]);
    applyFilter(input.value, false);
  });
  clearBtn.addEventListener('click', function() {
    input.value = '';
    highlightChip(chips[0]);
    applyFilter('', false);
  });
  chips.forEach(function(btn) {
    btn.addEventListener('click', function() {
      var pat = btn.getAttribute('data-vps-chip') || '';
      highlightChip(btn);
      if (!pat) {
        input.value = '';
        applyFilter('', false);
      } else {
        input.value = pat.indexOf('|') === -1 ? pat : '';
        applyFilter(pat, pat.indexOf('|') !== -1);
      }
    });
  });
  expandBtn.addEventListener('click', function() {
    var ds = root.querySelectorAll('details');
    for (var i = 0; i < ds.length; i++) ds[i].open = true;
    statusEl.textContent = '已展开全部 ' + ds.length + ' 份终端测评报告原文';
  });
  collapseBtn.addEventListener('click', function() {
    var ds = root.querySelectorAll('details');
    for (var i = 0; i < ds.length; i++) ds[i].open = false;
    statusEl.textContent = '已收起全部 ' + ds.length + ' 份终端测评报告原文';
  });
})();
</script>`.trim();
}

const opts = parseArgs(process.argv);
const templatedMd = fs.readFileSync(opts.input, 'utf8');
const { frontmatter, body: templatedBody } = splitFrontmatter(templatedMd);

const h2Map = new Map();
const h3SelfMap = new Map();
const pairMap = new Map();

function collectSlugsPlugin() {
  return (tree) => {
    const slugger = new GithubSlugger();
    let curH2 = null;
    walk(tree, (node) => {
      if (node.type === 'element' && HEADING_TAGS_WITH_ID.has(node.tagName)) {
        const txt = textOf(node).trim();
        const id = slugger.slug(txt);
        if (node.tagName === 'h2') {
          curH2 = txt;
          if (!h2Map.has(txt)) h2Map.set(txt, id);
        } else if (node.tagName === 'h3') {
          if (!h3SelfMap.has(txt)) h3SelfMap.set(txt, id);
          if (curH2) pairMap.set(`${curH2}||${txt}`, id);
        }
      }
    });
  };
}

await unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkRehype, { allowDangerousHtml: true })
  .use(collectSlugsPlugin)
  .use(rehypeStringify, { allowDangerousHtml: true })
  .process(templatedBody);

let resolvedBody = templatedBody.replace(/\{\{ANCHOR:([^}]+)\}\}/g, (_, key) => {
  if (key.includes('||')) {
    const id = pairMap.get(key);
    if (!id) throw new Error(`Unresolved ANCHOR pair: ${key}`);
    return `#${id}`;
  }
  const id = h2Map.get(key);
  if (!id) throw new Error(`Unresolved ANCHOR h2: ${key}`);
  return `#${id}`;
});

resolvedBody = resolvedBody.replace(/\{\{ANCHOR_SELF:([^}]+)\}\}/g, (_, key) => {
  const id = h3SelfMap.get(key);
  if (!id) throw new Error(`Unresolved ANCHOR_SELF: ${key}`);
  return `#${id}`;
});

if (resolvedBody.includes('{{ANCHOR')) {
  throw new Error('Residual {{ANCHOR token found after replacement!');
}

const finalMd = frontmatter + resolvedBody;
if (opts.outMd) fs.writeFileSync(opts.outMd, finalMd, 'utf8');
if (opts.outBody) fs.writeFileSync(opts.outBody, resolvedBody.replace(/^\n+/, ''), 'utf8');

const emittedIds = new Set();
const internalHrefs = [];
let rawDetailsOpen = 0;
let rawDetailsClose = 0;

function rehypeAddSlugsAndVerify() {
  return (tree) => {
    const slugger = new GithubSlugger();
    walk(tree, (node) => {
      if (node.type === 'raw') {
        const val = (node.value || '').trim();
        if (val.startsWith('<details>\n<summary>')) {
          rawDetailsOpen += 1;
          node.value = node.value.replace(
            '<summary>',
            '<summary style="cursor:pointer;font-weight:600;user-select:none;">'
          );
        } else if (val === '</details>') {
          rawDetailsClose += 1;
        } else {
          throw new Error(`Unexpected raw HTML node encountered: ${val.slice(0, 120)}`);
        }
      } else if (node.type === 'element' && HEADING_TAGS_WITH_ID.has(node.tagName)) {
        const txt = textOf(node).trim();
        const id = slugger.slug(txt);
        node.properties = node.properties || {};
        node.properties.id = id;
        emittedIds.add(id);
      } else if (node.type === 'element' && (node.tagName === 'h4' || node.tagName === 'h5' || node.tagName === 'h6')) {
        // Convert h4..h6 to accessible styled div[role="heading"] so Halo theme-earth's tocbot
        // never auto-indexes 450+ forum review sub-cards into the sidebar TOC!
        const lvl = node.tagName.slice(1);
        node.tagName = 'div';
        node.properties = {
          role: 'heading',
          'aria-level': lvl,
          className: ['vps-review-subheading'],
        };
      } else if (node.type === 'element' && node.tagName === 'a') {
        const href = node.properties?.href;
        if (typeof href === 'string' && href.startsWith('#')) {
          internalHrefs.push(href);
        }
      }
    });
  };
}

const htmlResult = await unified()
  .use(remarkParse)
  .use(remarkGfm)
  .use(remarkRehype, { allowDangerousHtml: true })
  .use(rehypeAddSlugsAndVerify)
  .use(rehypeStringify, { allowDangerousHtml: true })
  .process(resolvedBody);

let htmlStr = String(htmlResult);
const brokenHrefs = internalHrefs.filter((href) => {
  const targetId = decodeURIComponent(href.slice(1));
  return !emittedIds.has(targetId);
});

if (brokenHrefs.length > 0) {
  throw new Error(`Broken internal #anchor links (${brokenHrefs.length}): ${brokenHrefs.slice(0, 5).join(', ')}`);
}
if (rawDetailsOpen !== rawDetailsClose) {
  throw new Error(`Mismatched <details> tags: open=${rawDetailsOpen}, close=${rawDetailsClose}`);
}
if (opts.expectedDetails !== null && rawDetailsOpen !== opts.expectedDetails) {
  throw new Error(`Expected ${opts.expectedDetails} <details> pairs, got ${rawDetailsOpen}`);
}

if (opts.injectToolbar) {
  const markerRx = /(<h2 id="[^"]*">选机分类体系总览（猫猫博客口径）<\/h2>)/;
  if (!markerRx.test(htmlStr)) {
    throw new Error('Could not find 选机分类体系总览 heading to inject interactive toolbar!');
  }
  const toolbarHtml = buildInteractiveToolbarHtml(rawDetailsOpen);
  htmlStr = htmlStr.replace(markerRx, `$1\n${toolbarHtml}`);
}

fs.writeFileSync(opts.outHtml, htmlStr, 'utf8');

console.log(
  `[render-halo-markdown] OK: headingIDs=${emittedIds.size} (h1-h3 only), anchors=${internalHrefs.length} (0 broken), details=${rawDetailsOpen}, toolbar=${opts.injectToolbar}, mdBytes=${Buffer.byteLength(finalMd, 'utf8').toLocaleString()}, htmlBytes=${Buffer.byteLength(htmlStr, 'utf8').toLocaleString()}`
);
