#!/usr/bin/env node
/**
 * Render templated VPS Markdown ({{ANCHOR:...}} / {{ANCHOR_SELF:...}}) into:
 *   1. Clean final Markdown (--out-md) for Astro / Git repository
 *   2. Frontmatter-stripped Markdown body (--out-body) for Halo raw content
 *   3. Halo HTML (--out-html) with:
 *      - Heading IDs emitted ONLY on h1/h2/h3 (converting h4..h6 to div[role="heading"] so Halo tocbot stays concise)
 *      - Plaintext / language-text <pre><code> unwrapped to <pre class="vps-raw-report"> so Halo plugin-shiki
 *        neither blurs them (pre:has(code) { filter: blur(10px) }) nor mounts 300+ Shadow DOM Web Components
 *      - Styled <details>/<summary> collapsible benchmark blocks
 *      - Optional progressive interactive filter + A-Z vendor jump wall + expand/collapse toolbar (--inject-toolbar)
 *        with Light & Dark (html.dark) support, colloquial nickname expansion, instant cross-page #hash landing,
 *        and contextual return pill when arriving from /my-reviews
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

const HEADING_TAGS_WITH_ID = new Set(['h1', 'h2', 'h3']);

const STRUCTURAL_H2_PREFIXES = [
  '👑 猫猫钦点',
  '选机分类体系总览',
  '一、',
  '二、',
  '三、',
  '四、',
  '商家与产品线总览',
  '56 家正式商家与产品线总览',
  '猫猫博客非目录特殊家宽留档',
  '测评区没有对应帖子的商家',
  '收录方法与口径',
  '上下卷联动与选机延伸阅读',
];

const CROWN_VENDORS = new Set([
  'DMIT',
  '搬瓦工(BWH)',
  'Boil の家裡雲(港仔)',
  'qqpw(夏威夷家宽)',
  'netcup',
  'DigitalFyre',
]);

// Colloquial community nicknames -> canonical search keywords
const VENDOR_ALIASES = {
  'DMIT': '大妈 dmit coronado lax.pro',
  '搬瓦工(BWH)': '瓦工 bandwagon bandwagonhost bwh megabox the plan',
  'Boil の家裡雲(港仔)': '港仔 家里云 家裡雲 boil network',
  'qqpw(夏威夷家宽)': '夏威夷 qqpw drr hawaii',
  'netcup': 'nc 德鸡 rs1000 vps1000',
  'DigitalFyre': 'df digitalfyre',
  'GreenCloud(绿云)': '绿云 greencloud gc',
  'V.PS(小秘书)': '小秘书 xtom vps',
  'RFCHOST(花卷科技)': '花卷 rfchost rfc',
  'SaltyFish(咸鱼云)': '咸鱼 咸鱼云 saltyfish',
  'BageVM': '八哥 bage',
  'BestVM(富婆)': '富婆 bestvm',
  'BUG NET(虫网)': '虫网 bugnet',
  'Evoxt(益沃斯)': '益沃斯 evoxt',
  'FacHost(工厂云)': '工厂云 fachost',
  'Gomami(狗妈咪)': '狗妈咪 gomami',
  'HostDare': 'hd hostdare',
  'LeiKwan Host(利群主机)': '利群 leikwan',
  'Neburst(奶爸)': '奶爸 neburst',
  'NMCloud(牛马云)': '牛马 牛马云 nmcloud',
  'NovixLink(诺联主机)': '诺联 novixlink',
  'PittQiao(PQS)': '彼得巧 pqs pittqiao',
  'RivenCloud(极云)': '极云 rivencloud',
  'VIRCS(威尔克斯)': '威尔克斯 vircs',
  'WireCat(维猫)': '维猫 wirecat',
  'Yinnet(荫云)': '荫云 yinnet',
  'YUNYOO(云悠)': '云悠 yunyoo',
  'ZoroCloud(索隆云)': '索隆 索隆云 zorocloud',
  '六六云 666Clouds': '666 666clouds 六六云',
  '干杯云 USVPS24': '干杯 usvps24',
  'wawo（哇沃主机）': '哇沃 wawo',
  'BreadCloud（面包云）': '面包 面包云 breadcloud',
  'CloudSilk（白丝云）': '白丝 白丝云 cloudsilk',
  'GoodlyCloud（吉云）': '吉云 goodlycloud',
  'LazyCatCloud（懒猫云）': '懒猫 懒猫云 lazycat',
  'LisaHost（丽萨主机）': '丽萨 丽萨主机 lisahost',
  'Misaka': '御坂 御坂网络 misaka',
  'BuyVM': '卢森堡 frantech buyvm',
  'RackNerd': 'rn racknerd',
  'WePC（车库云）': '车库 车库云 wepc',
  '艾云 iaClouds（破云 / Brea.cloud）': '艾云 破云 iaclouds brea',
};

function escapeAttr(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function shortVendorLabel(h2Txt) {
  return h2Txt
    .replace(/（近半年公开帖为.*$/, '')
    .replace(/（已于.*$/, ' ⚠️停运')
    .replace(/（已被标记.*$/, ' ⚠️跑路')
    .replace(/（破云 \/ Brea\.cloud）/, '');
}

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

// Wrap <style> inside a <div> so Halo's server-side Jsoup.parseBodyFragment enters InBody state
// instead of hoisting a leading <style> into discarded <head>.
function buildScopedStyleBlock(includeToolbar) {
  const baseCss = `
.markdown-body h2[id],
.markdown-body h3[id] {
  scroll-margin-top: 88px;
}
.markdown-body h2.vps-hash-target,
.markdown-body h3.vps-hash-target {
  padding: 4px 10px;
  border-left: 4px solid var(--rx-accent, #b8461f);
  border-radius: 4px;
  background: var(--rx-accent-soft, #fbe7dc);
  transition: background-color 1.2s ease;
}
html.dark .markdown-body h2.vps-hash-target,
html.rx-dark .markdown-body h2.vps-hash-target,
html.dark .markdown-body h3.vps-hash-target,
html.rx-dark .markdown-body h3.vps-hash-target {
  border-left-color: var(--rx-accent, #ff8577);
  background: var(--rx-accent-soft, rgba(255, 133, 119, 0.18));
}
.vps-back-reviews-bar {
  margin: 8px 0 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.vps-back-reviews-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  max-width: 100%;
  box-sizing: border-box;
  padding: 6px 13px;
  border: 1.5px solid var(--rx-accent, #b8461f);
  border-radius: 999px;
  background: var(--rx-accent-soft, #fbe7dc);
  color: var(--rx-text, #1f2328) !important;
  font-size: 12.5px;
  font-weight: 700;
  text-decoration: none !important;
  box-shadow: var(--rx-shadow-sm, 0 1px 2px rgba(15, 23, 42, 0.08));
}
.vps-back-reviews-link:hover {
  background: var(--rx-accent, #b8461f);
  color: var(--rx-accent-ink, #ffffff) !important;
}
html.dark .vps-back-reviews-link,
html.rx-dark .vps-back-reviews-link {
  border-color: var(--rx-accent, #ff8577);
  background: var(--rx-accent-soft, rgba(255, 133, 119, 0.18));
  color: var(--rx-text, #fbf5ec) !important;
}
html.dark .vps-back-reviews-link:hover,
html.rx-dark .vps-back-reviews-link:hover {
  background: var(--rx-accent, #ff8577);
  color: var(--rx-accent-ink, #1c1726) !important;
}
.markdown-body pre.vps-raw-report,
pre.vps-raw-report {
  margin: 10px 0 14px;
  padding: 12px 14px !important;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #f8fafc;
  color: #1e293b;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 12.5px;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
  filter: none !important;
}
html.dark .markdown-body pre.vps-raw-report,
html.dark pre.vps-raw-report {
  background: #0f172a;
  border-color: #334155;
  color: #e2e8f0;
}
.vps-review-subheading {
  margin: 1.25em 0 0.5em;
  font-size: 1.05em;
  font-weight: 700;
  line-height: 1.4;
  color: #0f172a;
}
html.dark .vps-review-subheading {
  color: #f8fafc;
}`.trim();

  if (!includeToolbar) {
    return `<div class="vps-style-carrier"><style>\n${baseCss}\n</style></div>`;
  }

  const toolbarCss = `
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
#vps-quick-toolbar .vps-tb-chip:hover,
#vps-quick-toolbar .vps-vendor-pill:hover {
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
  background: var(--rx-accent, #0f172a);
  border-color: var(--rx-accent, #0f172a);
  color: var(--rx-accent-ink, #ffffff);
  font-weight: 600;
}
#vps-quick-toolbar #vps-filter-status {
  margin-top: 8px;
  font-size: 12.5px;
  color: #64748b;
}
#vps-quick-toolbar #vps-vendor-wall {
  margin: 10px 0 0 !important;
  padding: 8px 12px;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
}
#vps-quick-toolbar #vps-vendor-wall > summary {
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  user-select: none;
}
#vps-quick-toolbar .vps-vendor-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}
#vps-quick-toolbar .vps-vendor-pill {
  display: inline-block;
  padding: 3px 9px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #f8fafc;
  color: #1e293b !important;
  font-size: 12px;
  line-height: 1.45;
  text-decoration: none !important;
}
#vps-quick-toolbar .vps-vendor-pill.is-crown {
  border-color: #f59e0b;
  background: #fffbeb;
  color: #92400e !important;
  font-weight: 600;
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
html.dark #vps-quick-toolbar .vps-tb-chip:hover,
html.dark #vps-quick-toolbar .vps-vendor-pill:hover {
  border-color: #64748b;
}
html.dark #vps-quick-toolbar .vps-tb-chip {
  background: #0f172a;
  border-color: #475569;
  color: #cbd5e1;
}
html.dark #vps-quick-toolbar .vps-tb-chip.is-active {
  background: var(--rx-accent, #f59e0b);
  border-color: var(--rx-accent, #f59e0b);
  color: var(--rx-accent-ink, #0f172a);
}
html.dark #vps-quick-toolbar #vps-filter-status {
  color: #94a3b8;
}
html.dark #vps-quick-toolbar #vps-vendor-wall {
  background: #0f172a;
  border-color: #334155;
}
html.dark #vps-quick-toolbar #vps-vendor-wall > summary {
  color: #e2e8f0;
}
html.dark #vps-quick-toolbar .vps-vendor-pill {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0 !important;
}
html.dark #vps-quick-toolbar .vps-vendor-pill.is-crown {
  background: #451a03;
  border-color: #b45309;
  color: #fde68a !important;
}`.trim();

  return `<div class="vps-style-carrier"><style>\n${baseCss}\n${toolbarCss}\n</style></div>`;
}

function collectVendorEntries(h2Map) {
  const list = [];
  for (const [txt, id] of h2Map.entries()) {
    if (STRUCTURAL_H2_PREFIXES.some((p) => txt.startsWith(p))) continue;
    const isCrown = CROWN_VENDORS.has(txt);
    const label = (isCrown ? '👑 ' : '') + shortVendorLabel(txt);
    const alias = VENDOR_ALIASES[txt] || '';
    const canon = txt.split(/[（(]/)[0].trim();
    list.push({
      sortKey: txt.replace(/^[^A-Za-z0-9\u4e00-\u9fa5]+/, ''),
      label,
      href: `#${id}`,
      canon,
      searchHay: `${txt} ${label} ${alias}`.toLowerCase(),
      isCrown,
    });
  }
  if (h2Map.has('测评区没有对应帖子的商家')) {
    const noPostId = h2Map.get('测评区没有对应帖子的商家');
    for (const np of ['CoffeeHost', '筋斗云']) {
      list.push({
        sortKey: np,
        label: `${np} (暂无帖)`,
        href: `#${noPostId}`,
        canon: np,
        searchHay: `${np} 暂无帖`.toLowerCase(),
        isCrown: false,
      });
    }
  }
  list.sort((a, b) => {
    if (a.isCrown !== b.isCrown) return a.isCrown ? -1 : 1;
    return a.sortKey.localeCompare(b.sortKey, 'en', { sensitivity: 'base' });
  });
  return list;
}

function buildInteractiveToolbarHtml(detailsCount, vendorEntries) {
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

  const vendorPills = vendorEntries
    .map(
      (v) =>
        `<a href="${v.href}" class="vps-vendor-pill${v.isCrown ? ' is-crown' : ''}" data-vendor-hay="${escapeAttr(v.searchHay)}" data-vendor-canon="${escapeAttr(v.canon.toLowerCase())}">${escapeAttr(v.label)}</a>`
    )
    .join('');

  return `
<div id="vps-quick-toolbar">
  <div style="display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;">
    <div style="flex:1 1 260px;display:flex;gap:8px;align-items:center;">
      <input id="vps-filter-input" class="vps-tb-input" type="search" placeholder="筛选机型或搜俗称（如：9929、AT&T、大妈、瓦工、御坂、PQS、RN…）" />
      <button id="vps-filter-clear" class="vps-tb-btn" type="button">清空</button>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
      <button id="vps-expand-all" class="vps-tb-btn vps-tb-btn-primary" type="button">展开全部报告原文（${detailsCount} 份）</button>
      <button id="vps-collapse-all" class="vps-tb-btn" type="button">全部收起</button>
    </div>
  </div>
  <div id="vps-chip-bar" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:10px;">${chipBtns}</div>
  <details id="vps-vendor-wall">
    <summary id="vps-vendor-wall-summary">🏪 按商家名 A–Z 速查直达墙（本卷共 ${vendorEntries.length} 家，支持上方输入框按店名或俗称联动检索）</summary>
    <div class="vps-vendor-grid">${vendorPills}</div>
  </details>
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
  var vendorWall = document.getElementById('vps-vendor-wall');
  var vendorPills = Array.prototype.slice.call(toolbar.querySelectorAll('.vps-vendor-pill'));
  var chips = Array.prototype.slice.call(toolbar.querySelectorAll('[data-vps-chip]'));

  var SLANG_MAP = {
    '大妈': 'dmit', '瓦工': '搬瓦工', 'bwh': '搬瓦工', 'bandwagon': '搬瓦工',
    '港仔': 'boil', '家里云': 'boil', '绿云': 'greencloud', '小秘书': 'v.ps', 'xtom': 'v.ps',
    '花卷': 'rfchost', '咸鱼': 'saltyfish', '八哥': 'bagevm', '富婆': 'bestvm',
    '奶爸': 'neburst', 'pqs': 'pittqiao', '彼得巧': 'pittqiao', '御坂': 'misaka',
    '卢森堡': 'buyvm', 'frantech': 'buyvm', 'rn': 'racknerd', 'hd': 'hostdare',
    '丽萨': 'lisahost', '白丝': 'cloudsilk', '车库': 'wepc', '破云': '艾云', '云悠': 'yunyoo'
  };

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
        terms = q.toLowerCase().split(/\\s+/).filter(Boolean).map(function(t) {
          return SLANG_MAP[t] || t;
        });
      }
    }
    var matchedVendors = 0;
    vendorPills.forEach(function(pill) {
      var vhay = pill.getAttribute('data-vendor-hay') || '';
      var vok = true;
      if (q && !regexMode) {
        var rawTerms = q.toLowerCase().split(/\\s+/).filter(Boolean);
        vok = rawTerms.every(function(rt) {
          return vhay.indexOf(rt) !== -1 || (SLANG_MAP[rt] && vhay.indexOf(SLANG_MAP[rt]) !== -1);
        });
      }
      pill.style.display = vok ? '' : 'none';
      if (vok) matchedVendors += 1;
    });
    if (vendorWall && !regexMode) {
      if (q && matchedVendors > 0 && matchedVendors <= 12) vendorWall.open = true;
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
      statusEl.textContent = '当前显示全部分类表共 ' + total + ' 条机型记录（支持空格多词组合或俗称筛选，如：大妈、美国 家宽、香港 9929）';
    } else {
      statusEl.textContent = '筛选「' + q.replace(/\\|/g, ' / ') + '」：匹配 ' + matched + ' / ' + total + ' 条分类机型记录' + (!regexMode ? ('（匹配商家直达卡 ' + matchedVendors + ' 家）') : '');
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
    if (vendorWall) vendorWall.open = false;
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
    var ds = Array.prototype.slice.call(root.querySelectorAll('details')).filter(function(d) { return d.id !== 'vps-vendor-wall'; });
    for (var i = 0; i < ds.length; i++) ds[i].open = true;
    statusEl.textContent = '已展开全部 ' + ds.length + ' 份终端测评报告原文';
  });
  collapseBtn.addEventListener('click', function() {
    var ds = Array.prototype.slice.call(root.querySelectorAll('details')).filter(function(d) { return d.id !== 'vps-vendor-wall'; });
    for (var i = 0; i < ds.length; i++) ds[i].open = false;
    statusEl.textContent = '已收起全部 ' + ds.length + ' 份终端测评报告原文';
  });

  // Instant cross-page #hash jump, visual highlight & contextual back-to-my-reviews bar
  var userInteractedAfterJump = false;
  var jumpedAtLeastOnce = false;
  function markUserScroll() {
    if (jumpedAtLeastOnce) userInteractedAfterJump = true;
  }
  window.addEventListener('wheel', markUserScroll, { passive: true });
  window.addEventListener('touchmove', markUserScroll, { passive: true });

  var CARD_LABELS = {
    'dc9-gia': '① 搬瓦工 · 洛杉矶 DC9 CN2 GIA',
    'ppf-lax': '② PPFlight · 洛杉矶三网精品优化',
    'flawless-9929': '③ 完美节点 · 洛杉矶三网 9929',
    'attvps-standard': '④ ATTVPS · 洛杉矶 AT&T 静态家宽',
    'usvps24-att-pro9': '⑤ 干杯Cloud · AT&T 宽带 PRO-9线',
    'nmcloud-hinet': '⑥ NMCloud · 台湾 HiNet 家宽',
    'zorocloud-sg': '⑦ ZoroCloud · 新加坡 SPTel 家宽',
    'novix-lax': '⑧ NovixLink · 洛杉矶 LAX-BGP Lite',
    'yunyou-4837': '⑨ 云悠 · 洛杉矶 US4 Mini',
    'taipei101-tex1': '⑩ Taipei101 · 得州 TEX1 双栈'
  };

  function ensureBackToReviewsBar(target) {
    try {
      var sp = new URLSearchParams(location.search);
      if (sp.get('from') !== 'my-reviews') return;
      var cardId = sp.get('card') || '';
      var safeCard = /^[a-z0-9-]+$/i.test(cardId) ? ('#' + cardId) : '';
      var label = CARD_LABELS[cardId] || '';
      var existing = document.getElementById('vps-back-reviews-bar');
      if (existing) existing.remove();
      var bar = document.createElement('div');
      bar.id = 'vps-back-reviews-bar';
      bar.className = 'vps-back-reviews-bar';
      var a = document.createElement('a');
      a.className = 'vps-back-reviews-link';
      a.href = '/my-reviews' + safeCard;
      a.textContent = label
        ? ('← 返回「我的测评」：' + label)
        : '← 返回「我的测评」刚才查看的真机实测卡片';
      bar.appendChild(a);
      target.insertAdjacentElement('afterend', bar);
    } catch (e) {}
  }

  function jumpToHashTarget(forceInstant) {
    if (!location.hash || location.hash.length <= 1) return false;
    var raw = location.hash.slice(1);
    var decoded = raw;
    try { decoded = decodeURIComponent(raw); } catch (e) {}
    var target = document.getElementById(decoded) || document.getElementById(raw);
    if (!target) return false;
    var cur = target.parentElement;
    while (cur && cur !== document.body) {
      if (cur.tagName === 'DETAILS') cur.open = true;
      cur = cur.parentElement;
    }
    var old = root.querySelectorAll('.vps-hash-target');
    for (var i = 0; i < old.length; i++) old[i].classList.remove('vps-hash-target');
    target.classList.add('vps-hash-target');
    ensureBackToReviewsBar(target);
    if (document.documentElement.scrollHeight < 1200) return false;
    var rect = target.getBoundingClientRect();
    var desiredY = Math.max(0, window.pageYOffset + rect.top - 88);
    if (forceInstant) {
      var htmlEl = document.documentElement;
      var prev = htmlEl.style.scrollBehavior;
      htmlEl.style.scrollBehavior = 'auto';
      window.scrollTo(0, desiredY);
      htmlEl.style.scrollBehavior = prev;
    } else {
      target.scrollIntoView({ block: 'start' });
    }
    jumpedAtLeastOnce = true;
    return true;
  }

  function scheduleInitialHashJump() {
    if (!location.hash || location.hash.length <= 1) return;
    jumpToHashTarget(true);
    setTimeout(function() {
      if (!userInteractedAfterJump) jumpToHashTarget(true);
    }, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleInitialHashJump);
  } else {
    scheduleInitialHashJump();
  }
  window.addEventListener('load', function() {
    if (!userInteractedAfterJump) scheduleInitialHashJump();
  });
  window.addEventListener('hashchange', function() {
    userInteractedAfterJump = false;
    jumpToHashTarget(true);
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
let rawReportPreCount = 0;
let subheadingCount = 0;

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
      } else if (node.type === 'element' && node.tagName === 'pre') {
        const onlyChild = node.children?.length === 1 ? node.children[0] : null;
        if (onlyChild && onlyChild.type === 'element' && onlyChild.tagName === 'code') {
          const classes = Array.isArray(onlyChild.properties?.className) ? onlyChild.properties.className : [];
          if (classes.length === 0 || classes.includes('language-text') || classes.includes('language-plaintext')) {
            node.children = onlyChild.children || [];
            node.properties = { ...(node.properties || {}), className: ['vps-raw-report'] };
            rawReportPreCount += 1;
          }
        }
      } else if (node.type === 'element' && HEADING_TAGS_WITH_ID.has(node.tagName)) {
        const txt = textOf(node).trim();
        const id = slugger.slug(txt);
        node.properties = node.properties || {};
        node.properties.id = id;
        emittedIds.add(id);
      } else if (node.type === 'element' && (node.tagName === 'h4' || node.tagName === 'h5' || node.tagName === 'h6')) {
        const lvl = node.tagName.slice(1);
        node.tagName = 'div';
        node.properties = {
          role: 'heading',
          'aria-level': lvl,
          className: ['vps-review-subheading'],
        };
        subheadingCount += 1;
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

const vendorEntries = collectVendorEntries(h2Map);

if (opts.injectToolbar) {
  const markerRx = /(<h2 id="[^"]*">选机分类体系总览（猫猫博客口径）<\/h2>)/;
  if (!markerRx.test(htmlStr)) {
    throw new Error('Could not find 选机分类体系总览 heading to inject interactive toolbar!');
  }
  const toolbarHtml = buildInteractiveToolbarHtml(rawDetailsOpen, vendorEntries);
  htmlStr = htmlStr.replace(markerRx, `$1\n${toolbarHtml}`);
}

if (opts.injectToolbar || rawReportPreCount > 0 || subheadingCount > 0) {
  htmlStr = `${buildScopedStyleBlock(opts.injectToolbar)}\n${htmlStr}`;
}

fs.writeFileSync(opts.outHtml, htmlStr, 'utf8');

console.log(
  `[render-halo-markdown] OK: headingIDs=${emittedIds.size} (h1-h3 only), anchors=${internalHrefs.length} (0 broken), vendors=${vendorEntries.length}, details=${rawDetailsOpen}, rawPre=${rawReportPreCount}, toolbar=${opts.injectToolbar}, mdBytes=${Buffer.byteLength(finalMd, 'utf8').toLocaleString()}, htmlBytes=${Buffer.byteLength(htmlStr, 'utf8').toLocaleString()}`
);
