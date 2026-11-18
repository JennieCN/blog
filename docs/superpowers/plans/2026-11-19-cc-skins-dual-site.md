# CC Dual-Site 4-Skin Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port CC's 4 switchable skins (`pop`, `ink`, `luxe`, `plain`), Light/Dark modes, top-bar skin switcher, View Transition reveal, and confetti/toast micro-interactions onto both live Halo (`https://blog.mycampusmail.com`) and live Flarum (`https://qa.mycampusmail.com`) with cross-subdomain `.mycampusmail.com` state sync and zero container source modifications.

**Architecture:** Serve a versioned `/rx-skins/*` static asset bundle same-origin from Caddy (`site-proxy`) on both subdomains so SVG `mask-image` assets (`ink-stroke.svg`, `ink-mountains.svg`, `ink-landscape.svg`), shared CSS tokens (`rx-tokens.css`), and the cross-site controller (`rx-switcher.js`) load with zero CORS issues. Inject lightweight Zero-FOUC bootstrap + site-specific visual adapters via Halo `codeInjection.globalHead` (`rx-halo.css`) and Flarum `flarum_settings.custom_header` (`rx-flarum.css`), synchronizing active skin and theme via `.mycampusmail.com` cookies while strictly excluding `/console`, `/uc`, and `/admin`.

**Tech Stack:** CSS Custom Properties, CSS `mask-image` / View Transitions API, Vanilla ES5/ES6 JavaScript (`MutationObserver`), Caddy 2 static `handle_path`, Halo `v2.27.3` (`theme-earth`), Flarum `v2.0.2`, Python 3 (`unittest` + Headless Chrome CDP verification).

**Spec:** `docs/superpowers/specs/2026-11-19-cc-skins-dual-site-design.md`

## Global Constraints

- Live production stack runs on `vps8` (`/opt/site-stack/docker-compose.yml`): `site-proxy` (Caddy 2), `site-halo` (`halo:8090`), and `site-flarum` (`flarum:8000`); never modify internal container images or unpack `theme-earth` templates.
- Skin rotation order MUST be `['pop', 'ink', 'luxe', 'plain']` with first-visit default `'pop'` when no valid cookie/storage value is present.
- Cross-site cookies MUST use `rx_skin=pop|ink|luxe|plain` and `rx_theme=light|dark` with attributes `Domain=.mycampusmail.com; Path=/; Max-Age=31536000; SameSite=Lax; Secure` (falling back to host-only cookie + `localStorage` on `localhost` / `file://` during tests).
- Admin routes (`/console`, `/uc` on Halo; `/admin` on Flarum) MUST remain 100% untouched even when `rx_skin` / `rx_theme` cookies are present on `.mycampusmail.com`.
- Code blocks (`<pre class="vps-raw-report">` and Shiki `<pre>`) MUST never have `filter: blur(...)` and MUST preserve high-contrast readable foreground/background across all 8 skin × theme combinations (including `plain` light mode).
- `390px` mobile and `1280px` desktop viewports MUST exhibit zero horizontal overflow (`documentElement.scrollWidth <= window.innerWidth`) across all 4 skins.
- Honor `prefers-reduced-motion: reduce` and `prefers-reduced-transparency: reduce` by disabling animations, View Transitions, confetti particles, and `backdrop-filter`.

## Review Focus

- Unknown, corrupted, or legacy cookie/storage values (`rx_skin=bogus`, `color-scheme=system`) must fall back cleanly to `'pop'` and OS `prefers-color-scheme` without blanking CSS variables or throwing JS exceptions.
- Clicking Halo's built-in `theme-earth` color-scheme menu (`亮色 / 暗色 / 跟随系统`) mutates `<html class="dark">` outside our button handler; `rx-switcher.js` must observe `<html>` class changes and keep `html.rx-dark` + `rx_theme` cookie synchronized.
- Flarum Mithril SPA navigation (e.g., `/d/7` -> `/`) re-renders `.Header-controls`; `rx-switcher.js` must re-mount `#rx-skin-toggle` and `#rx-theme-toggle` idempotently without creating duplicate buttons.
- `plain` light mode sets `--rx-code-bg: #f6f8fa` (light gray), which would break terminal-dark `<pre class="vps-raw-report">` or Shiki blocks if inherited blindly; `.vps-raw-report` must retain dark terminal background (`#0f172a` / `#151b23`) and light text (`#e2e8f0`) in every skin.
- Visiting `/console`, `/uc`, or `/admin` while `rx_skin=ink` cookie is set on `.mycampusmail.com` must leave `document.documentElement.dataset.rxSkin` undefined and inject zero toolbar buttons.

---

### Task 1: Shared Skin Token Bundle, Ink SVGs & Cross-Site Controller (`scripts/rx-skins/`)

**Files:**
- Create: `scripts/rx-skins/ink-landscape.svg` (copy from `public/skins/ink-landscape.svg`)
- Create: `scripts/rx-skins/ink-mountains.svg` (copy from `public/skins/ink-mountains.svg`)
- Create: `scripts/rx-skins/ink-stroke.svg` (copy from `public/skins/ink-stroke.svg`)
- Create: `scripts/rx-skins/rx-tokens.css`
- Create: `scripts/rx-skins/rx-switcher.js`
- Create: `scripts/rx-skins/bootstrap-snippet.js`
- Test: `scripts/tests/test_rx_skins.py`

**Interfaces:**
- Produces:
  - HTML root attributes managed by bootstrap & `rx-switcher.js`: `html[data-rx-skin="pop|ink|luxe|plain"]` and unified dark class `html.rx-dark` (kept in lockstep with `html.dark` on Halo and `html[data-theme="dark"|"light"]` on Flarum).
  - CSS variables in `rx-tokens.css` defined for all 4 skins × `:not(.rx-dark)` / `.rx-dark`: `--rx-bg`, `--rx-surface`, `--rx-surface-2`, `--rx-surface-3`, `--rx-line`, `--rx-line-strong`, `--rx-text`, `--rx-text-2`, `--rx-text-3`, `--rx-accent`, `--rx-accent-hover`, `--rx-accent-ink`, `--rx-accent-soft`, `--rx-ok`, `--rx-ok-bg`, `--rx-warn`, `--rx-warn-bg`, `--rx-danger`, `--rx-code-bg`, `--rx-code-text`, `--rx-radius`, `--rx-radius-sm`, `--rx-bw`, `--rx-shadow`, `--rx-shadow-lg`, `--rx-glass`, `--rx-glass-strong`, `--rx-hairline`, `--rx-dusk`, `--rx-font-sans`, `--rx-font-serif`, `--rx-font-brush`, `--rx-font-display`, `--rx-stroke`.
  - Shared chrome classes in `rx-tokens.css`: `#rx-read-progress`, `.rx-toast-wrap`, `.rx-toast`, `.rx-icon-btn`, `.fx-layer`, `.fx-bit`.
  - Global JS API in `rx-switcher.js`: `window.RXSkins = { SKINS: ['pop','ink','luxe','plain'], getSkin(): string, setSkin(id: string, originEl?: Element): void, nextSkin(): string, getTheme(): 'light'|'dark', setTheme(mode: 'light'|'dark', originEl?: Element, persist?: boolean): void, toggleTheme(originEl?: Element): void, toast(msg: string): void, confetti(originEl?: Element): void, mountButtons(): void }` plus `window.RXFX` compatibility alias (`{ toast, confetti, setSkin, currentSkin: getSkin }`).

- [ ] **Step 1: Write failing Headless Chrome unit/DOM tests in `scripts/tests/test_rx_skins.py`**

Write `TestRxSkinsCore` in `scripts/tests/test_rx_skins.py` launching headless Chrome on local HTML fixtures to assert:
1. `test_svg_assets_and_token_selectors`: all 3 SVG files exist and are valid `<svg>`, and `rx-tokens.css` defines `--rx-bg`, `--rx-surface`, `--rx-text`, `--rx-accent` for `pop`, `ink`, `luxe`, `plain` in both light and `.rx-dark`.
2. `test_corrupted_cookie_fallback_and_cycle`: loading fixture with `rx_skin=bogus` sets `documentElement.dataset.rxSkin === 'pop'`; clicking `#rx-skin-toggle` 4 times cycles `'pop' -> 'ink' -> 'luxe' -> 'plain' -> 'pop'` and renders `#rx-toast` with `已切换至「水墨」风格` on first click.
3. `test_admin_path_exclusion`: running `bootstrap-snippet.js` + `rx-switcher.js` when `window.__RX_TEST_PATH = '/console/dashboard'` or `'/admin'` leaves `dataset.rxSkin` undefined and mounts `0` `#rx-skin-toggle` buttons even when `localStorage.getItem('rx_skin') === 'ink'`.
4. `test_halo_native_dark_mutation_sync`: on a Halo-shaped DOM (`#header-menu`), toggling `documentElement.classList.add('dark')` externally triggers `MutationObserver` so `documentElement.classList.contains('rx-dark') === true`.
5. `test_flarum_spa_header_remount_idempotent`: on a Flarum-shaped DOM (`.Header-secondary .Header-controls`), wiping `.Header-controls.innerHTML = ''` and re-inserting child `<li>` nodes causes `rx-switcher.js` to re-mount exactly `1` `#rx-skin-toggle` and `1` `#rx-theme-toggle`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v`
Expected: FAIL (`FileNotFoundError` / missing `scripts/rx-skins/*`).

- [ ] **Step 3: Copy ink SVGs and implement `rx-tokens.css`, `bootstrap-snippet.js`, and `rx-switcher.js`**

- Copy `ink-landscape.svg`, `ink-mountains.svg`, `ink-stroke.svg` from `public/skins/` into `scripts/rx-skins/`.
- In `scripts/rx-skins/rx-tokens.css`, port CC's exact color, typography, shadow, glass, and radius palettes from `public/skins/{pop,ink,luxe,plain}.css` and `src/styles/global.css` into `:root[data-rx-skin="pop"]`, `:root[data-rx-skin="ink"]`, `:root[data-rx-skin="luxe"]`, `:root[data-rx-skin="plain"]` and their `html.rx-dark[data-rx-skin="..."]` dark counterparts, using relative `url("ink-stroke.svg")` for `--rx-stroke`, plus shared `#rx-read-progress`, `.rx-toast`, `.rx-icon-btn`, View Transition rules, and `prefers-reduced-motion` / `prefers-reduced-transparency` guards.
- In `scripts/rx-skins/bootstrap-snippet.js`, write the compact synchronous `<head>` IIFE (supporting optional `window.__RX_TEST_PATH` override for testing) that exits immediately on `/console`, `/uc`, `/admin`, reads `rx_skin` / `rx_theme` from cookie then `localStorage`, validates `rx_skin` against `['pop','ink','luxe','plain']` (default `'pop'`), computes initial dark state (cookie `rx_theme` -> Halo `localStorage['color-scheme']` -> Flarum `data-theme` -> `matchMedia('(prefers-color-scheme: dark)')`), and applies `data-rx-skin`, `rx-dark`, Halo `dark`, and Flarum `data-theme` synchronously before first paint.
- In `scripts/rx-skins/rx-switcher.js`, implement `window.RXSkins` + `window.RXFX`, `.mycampusmail.com` cookie writer (with host-only fallback when domain is not `*.mycampusmail.com`), View Transition circular reveal, toast, confetti, `#rx-read-progress` rAF scroll listener, Halo `#header-menu` + mobile drawer button mount & `html.dark` `MutationObserver`, and Flarum `.Header-controls` `#rx-skin-toggle` + `#rx-theme-toggle` mount & SPA `MutationObserver`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v`
Expected: PASS (5/5 tests OK).

- [ ] **Step 5: Commit**

```bash
git add scripts/rx-skins/ink-landscape.svg scripts/rx-skins/ink-mountains.svg scripts/rx-skins/ink-stroke.svg scripts/rx-skins/rx-tokens.css scripts/rx-skins/bootstrap-snippet.js scripts/rx-skins/rx-switcher.js scripts/tests/test_rx_skins.py
git commit -m "feat(skins): add shared CC 4-skin tokens, ink SVGs, and cross-site switcher"
```

---

### Task 2: Halo Main Site Visual Adapter & Head Injection Template (`rx-halo.css`)

**Files:**
- Create: `scripts/rx-skins/rx-halo.css`
- Create: `scripts/rx-skins/halo-global-head.html`
- Modify: `scripts/tests/test_rx_skins.py`

**Interfaces:**
- Consumes: `html[data-rx-skin]`, `html.rx-dark`, `--rx-*` tokens from `rx-tokens.css`, `bootstrap-snippet.js`, and `window.RXSkins` from Task 1.
- Produces:
  - `scripts/rx-skins/rx-halo.css`: Full visual adapter for Halo `theme-earth` + custom Halo pages/posts.
  - `scripts/rx-skins/halo-global-head.html`: Ready-to-inject HTML snippet for Halo `/registry/configmaps/system` -> `data.codeInjection.globalHead`.

- [ ] **Step 1: Add failing Halo DOM & visual regression tests in `scripts/tests/test_rx_skins.py`**

Add `TestRxHaloAdapter` in `scripts/tests/test_rx_skins.py` loading a representative Halo `theme-earth` HTML fixture (containing `#header-menu`, homepage hero `<div class="bg-cover bg-center bg-no-repeat h-96">`, `#filters`, post card `.group.flex.flex-col.overflow-hidden.rounded-xl.bg-white`, `#post-content`, `.vps-summary-panel`, `#vps-vendor-wall`, `<pre class="vps-raw-report">`, and `.rx-legal-meta`) with `rx-tokens.css` + `rx-halo.css` + `rx-switcher.js` in Headless Chrome:
1. `test_halo_four_skins_distinct_backgrounds_and_cards`: verify `getComputedStyle(document.body).backgroundColor` and post card `borderRadius` / `boxShadow` / `borderTopWidth` match each skin (`pop` cream `#fff7e8` + `>=2px` border + hard shadow; `ink` Xuan paper `#efe7d6` + `0px`/`3px` radius; `luxe` warm `#f6f1e9` + blurred glass card; `plain` `#ffffff` + `1px` border + `boxShadow: none`).
2. `test_halo_raw_report_never_blurred_and_high_contrast_in_plain`: across all 8 combinations (`pop/ink/luxe/plain` × `light/dark`), `<pre class="vps-raw-report">` has `filter === 'none'` and dark background luminance `< 0.12` with light foreground luminance `> 0.65` (specifically pinning `plain` light mode).
3. `test_halo_mobile_390px_zero_overflow`: at `390x844` viewport across all 4 skins, `document.documentElement.scrollWidth <= 390` and `#rx-skin-toggle` is visible and clickable.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v`
Expected: FAIL (`rx-halo.css` missing).

- [ ] **Step 3: Implement `scripts/rx-skins/rx-halo.css` and `scripts/rx-skins/halo-global-head.html`**

- Build `scripts/rx-skins/rx-halo.css` scoped under `html[data-rx-skin]`:
  - **Page backdrop layers**: `pop` radial polka-dot grid; `ink` Xuan paper vignette + `body::before` `url("ink-mountains.svg")` + paper noise `body::after`; `luxe` animated sunset aurora `body::before` + subtle grain `body::after`; `plain` clean solid `--rx-bg`.
  - **Header (`#header-menu`) & dropdowns**: map background, border, nav link colors, mobile menu panel, and skin-specific header signatures (`ink` bottom `ink-stroke.svg` brush bar; `luxe` frosted `backdrop-filter` + sunset hairline; `pop` `2.5px` solid border; `plain` Primer `surface-2` bar).
  - **Homepage Hero (`section > div.bg-cover.h-96`)**: `ink` replaces dark photo banner look with Xuan paper + right-aligned `url("ink-landscape.svg")` + brush calligraphy title + vertical「融夕」cinnabar seal (`::after`); `pop` renders bordered cream/night sticker card with yellow geometric sun badge & hard shadow; `luxe` blends warm dusk gradient overlay with glowing title; `plain` renders crisp bordered surface card.
  - **Category `#filters`, Post Cards, Sidebar Widgets, Pagination, Footer**: override `theme-earth` hardcoded `.bg-white` / `.dark\:bg-slate-800` / `.bg-slate-50` inside main layout containers cleanly using `--rx-surface`, `--rx-line`, `--rx-shadow`, `--rx-radius`, hover states, and `ink` serif/brush / `pop` display typography.
  - **Post Prose & Custom Components**: style `.markdown-body` / `#post-content` (including `ink` H2 brush underline & `「` blockquote mark; `pop` rotated yellow square before H2 & thick-bordered blockquote; `luxe` dusk-bordered blockquote), map `.vps-summary-panel`, `.vps-sticky-bar`, `#vps-vendor-wall`, `.vps-pill`, `.vps-toc-table`, `.rx-about-*`, `.rx-legal-*`, and `/my-reviews` + `/tools` cards to `--rx-*` tokens, and explicitly lock `pre.vps-raw-report` + Shiki `pre` to `filter: none !important; background: #0f172a; color: #e2e8f0` (with skin-appropriate border/shadow accents).
- Assemble `scripts/rx-skins/halo-global-head.html` embedding the minified/inlined `bootstrap-snippet.js`, `<link rel="stylesheet" href="/rx-skins/rx-tokens.css?v=20261119a">`, `<link rel="stylesheet" href="/rx-skins/rx-halo.css?v=20261119a">`, and `<script defer src="/rx-skins/rx-switcher.js?v=20261119a"></script>`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v`
Expected: PASS (all `TestRxSkinsCore` + `TestRxHaloAdapter` tests OK).

- [ ] **Step 5: Commit**

```bash
git add scripts/rx-skins/rx-halo.css scripts/rx-skins/halo-global-head.html scripts/tests/test_rx_skins.py
git commit -m "feat(skins): add Halo theme-earth 4-skin visual adapter and head template"
```

---

### Task 3: Flarum 2.0 Visual Adapter & Custom Header Template (`rx-flarum.css`)

**Files:**
- Create: `scripts/rx-skins/rx-flarum.css`
- Create: `scripts/rx-skins/flarum-custom-header.html`
- Modify: `scripts/tests/test_rx_skins.py`

**Interfaces:**
- Consumes: `html[data-rx-skin]`, `html.rx-dark`, `html[data-theme]`, `--rx-*` tokens from Task 1, and existing Flarum `me.php` / captcha endpoints on `qa.mycampusmail.com`.
- Produces:
  - `scripts/rx-skins/rx-flarum.css`: Complete Flarum 2.0 variable & component adapter across all 4 skins × Light/Dark.
  - `scripts/rx-skins/flarum-custom-header.html`: Complete `flarum_settings.custom_header` payload preserving `#rx-points`, `#rx-checkin-btn`, `window.__rxCheckin` (with `RXFX.confetti`), `#rx-captcha-float`, and `window.__rxSendEmailCode`.

- [ ] **Step 1: Add failing Flarum DOM, variable mapping & mobile overflow tests in `scripts/tests/test_rx_skins.py`**

Add `TestRxFlarumAdapter` in `scripts/tests/test_rx_skins.py` loading a Flarum 2.0 HTML fixture (including `flarum-custom-header.html`, `.App-header`, `.Header-secondary .Header-controls`, `.Hero.WelcomeHero`, `.IndexPage-nav`, `.DiscussionListItem`, `.DiscussionListItem--sticky`, `.TagLabel`, `.CommentPost`, and `.Button--primary`) in Headless Chrome:
1. `test_flarum_four_skins_override_cold_blue_and_style_crossbar`: assert `--primary-color` and `.Button--primary` background are no longer `#4d698e`, and `.rx-qa-crossbar` + `.rx-qa-strip` dynamically change computed background/border across `pop`, `ink`, `luxe`, `plain` in both `data-theme="light"` and `data-theme="dark"`.
2. `test_flarum_preserved_checkin_and_captcha_hooks`: assert `#rx-checkin-btn`, `#rx-points`, `#rx-captcha-float`, `typeof window.__rxCheckin === 'function'`, and `typeof window.__rxSendEmailCode === 'function'` all exist, and links to `https://blog.mycampusmail.com/my-reviews` and `https://blog.mycampusmail.com/tools` are present.
3. `test_flarum_mobile_390px_zero_overflow`: at `390x844` viewport across all 4 skins, `document.documentElement.scrollWidth <= 390` and both `#rx-skin-toggle` and `#rx-theme-toggle` fit without overflowing `.App-header`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v`
Expected: FAIL (`rx-flarum.css` / `flarum-custom-header.html` missing).

- [ ] **Step 3: Implement `scripts/rx-skins/rx-flarum.css` and `scripts/rx-skins/flarum-custom-header.html`**

- First fetch the exact current `custom_header` script tail from `vps8` (`flarum_settings` where `key='custom_header'`) so zero existing check-in (`me.php`) or registration/composer email-captcha (`#rx-captcha-float` / `__rxSendEmailCode`) logic is lost; refactor only the hardcoded `#18181b` / `#eff6ff` inline styles into semantic classes `.rx-qa-crossbar`, `.rx-qa-strip`, and `.rx-checkin-pill`, and hook `window.RXFX && window.RXFX.confetti(btn)` on newly completed check-in inside `flarum-custom-header.html`.
- Prepend the Zero-FOUC inline `bootstrap-snippet.js`, `<link rel="stylesheet" href="/rx-skins/rx-tokens.css?v=20261119a">`, `<link rel="stylesheet" href="/rx-skins/rx-flarum.css?v=20261119a">`, and `<script defer src="/rx-skins/rx-switcher.js?v=20261119a"></script>` at the top of `flarum-custom-header.html`.
- In `scripts/rx-skins/rx-flarum.css`:
  - Map `--rx-*` tokens to Flarum 2.0's `:root`, `[data-theme^=light]`, and `[data-theme^=dark]` custom properties (`--body-bg`, `--body-bg-shaded`, `--body-bg-light`, `--body-bg-faded`, `--text-color`, `--heading-color`, `--muted-color`, `--control-bg`, `--control-bg-light`, `--control-bg-shaded`, `--control-color`, `--header-bg`, `--header-color`, `--header-control-bg`, `--header-control-color`, `--primary-color`, `--secondary-color`, `--link-color`, `--button-color`, `--button-bg`, `--button-primary-bg`, `--button-primary-color`, `--hero-bg`, `--hero-color`, `--discussion-title-color`, `--code-bg`, `--code-color`, `--border-radius`).
  - Style page backgrounds (`pop` dot-grid, `ink` Xuan paper + `ink-mountains.svg`, `luxe` sunset aurora + grain, `plain` solid), `.rx-qa-crossbar` & `.rx-qa-strip`, `.App-header` (including `ink` brush bottom edge, `luxe` glass blur, `pop` thick border), `.WelcomeHero` / `.Hero` (`ink` `ink-landscape.svg` +「融夕」cinnabar seal on `.Hero-title::after`; `pop` yellow sticker card + hard shadow; `luxe` dusk radial glass card; `plain` clean bordered card), `.DiscussionListItem` (cards/dividers, sticky highlight, serif/display titles), `.IndexPage-nav .item-nav` side links, `.TagLabel` & `.TagTile`, `.PostStream-item` / `.CommentPost`, `.Composer`, `.Modal-content`, `.Dropdown-menu`, and `#rx-captcha-float`, plus `@media (max-width: 640px)` compact rules.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v && npm run build`
Expected: PASS (all unit/DOM tests pass; Astro repo build remains `0 Warning, 0 Error`).

- [ ] **Step 5: Commit**

```bash
git add scripts/rx-skins/rx-flarum.css scripts/rx-skins/flarum-custom-header.html scripts/tests/test_rx_skins.py
git commit -m "feat(skins): add Flarum 2.0 4-skin visual adapter and custom_header template"
```

---

### Task 4: Live Deployment, End-to-End Dual-Site Verification & Backup (`vps8`)

**Files:**
- Create: `scripts/deploy-rx-skins.py`
- Modify: `scripts/verify-live-halo.py`
- Modify: `scripts/README.md`

**Interfaces:**
- Consumes: `scripts/rx-skins/*` (`ink-*.svg`, `rx-tokens.css`, `rx-halo.css`, `rx-flarum.css`, `rx-switcher.js`, `halo-global-head.html`, `flarum-custom-header.html`) from Tasks 1–3.
- Produces:
  - Live `/rx-skins/*` endpoints on both `https://blog.mycampusmail.com/rx-skins/*` and `https://qa.mycampusmail.com/rx-skins/*` via Caddy `site-proxy`.
  - Updated Halo `codeInjection.globalHead` and Flarum `custom_header` + `theme_primary_color` on `vps8`, verified end-to-end by `scripts/verify-live-halo.py`, backed up via `/opt/site-stack/backup.sh`, and pushed to `origin/main`.

- [ ] **Step 1: Extend `scripts/verify-live-halo.py` with failing live dual-site skin assertions**

Add `check_dual_site_cc_skins(browser_ws)` and static asset checks to `scripts/verify-live-halo.py`:
1. HTTP `200` + `Cache-Control` check on `/rx-skins/{rx-tokens.css,rx-halo.css,rx-flarum.css,rx-switcher.js,ink-landscape.svg,ink-mountains.svg,ink-stroke.svg}` across BOTH `https://blog.mycampusmail.com` and `https://qa.mycampusmail.com`.
2. Headless Chrome live check on `https://blog.mycampusmail.com/` and `https://blog.mycampusmail.com/archives/nodeseek-merchant-reviews-2026h2`:
   - Default first-paint `dataset.rxSkin === 'pop'`; `#rx-skin-toggle` present;
   - Cycle through all 4 skins (`pop`, `ink`, `luxe`, `plain`) in both Light and Dark modes: verify distinct computed `body` backgrounds, zero horizontal overflow at `1280px` and `390px`, `<pre class="vps-raw-report">` `filter === 'none'` and dark contrast preserved even in `plain` light mode.
   - Set skin to `'ink'` and theme to `'dark'` on `blog.mycampusmail.com`, then navigate the same browser context to `https://qa.mycampusmail.com/` and assert cross-subdomain `.mycampusmail.com` Cookie automatically boots `qa` in `dataset.rxSkin === 'ink'` and `dataset.theme === 'dark'`!
3. Headless Chrome live check on `https://qa.mycampusmail.com/` and `https://qa.mycampusmail.com/d/7`:
   - Cycle all 4 skins × Light/Dark, verify `#rx-skin-toggle` & `#rx-theme-toggle` survive SPA navigation (`/` -> `/d/7`), `.rx-qa-crossbar` & `.DiscussionListItem` reflect skin styles, and `390px` mobile has zero horizontal overflow.
4. Admin isolation check: navigate to `https://blog.mycampusmail.com/console` and `https://qa.mycampusmail.com/admin` while `rx_skin=ink` cookie is set and assert `documentElement.dataset.rxSkin` is undefined on both admin routes.

- [ ] **Step 2: Run live verification to confirm it fails before deployment**

Run: `python3 scripts/verify-live-halo.py`
Expected: FAIL (`HTTPError: HTTP Error 404: Not Found` on `/rx-skins/rx-tokens.css`).

- [ ] **Step 3: Implement and run idempotent `scripts/deploy-rx-skins.py` against `vps8`**

Write `scripts/deploy-rx-skins.py` (never hardcoding credentials; using SSH `vps8` and server-side `/opt/site-stack/.env`) to:
1. Upload `scripts/rx-skins/{*.css,*.js,*.svg}` to `vps8:/opt/site-stack/rx-skins/`.
2. Idempotently add `./rx-skins:/srv/rx-skins:ro` to `site-proxy.volumes` in `/opt/site-stack/docker-compose.yml`, add `handle_path /rx-skins/*` (with `Cache-Control: public, max-age=604800` and `file_server`) in both `blog.mycampusmail.com` and `qa.mycampusmail.com` blocks of `/opt/site-stack/Caddyfile`, include `rx-skins` in `/opt/site-stack/backup.sh`, and recreate/reload `site-proxy` (`docker compose up -d proxy && docker exec site-proxy caddy reload --config /etc/caddy/Caddyfile`).
3. Update Halo `/registry/configmaps/system` -> `data.codeInjection.globalHead` with `halo-global-head.html` via Halo's authenticated Console API (reading admin credentials from local keychain/env or updating via Halo REST API so Halo's in-memory ConfigMap cache refreshes immediately).
4. Update Flarum `flarum_settings` (`custom_header` = `flarum-custom-header.html`, `theme_primary_color` = `#b8461f`, `theme_secondary_color` = `#9a5b00`) and run `docker exec site-flarum php /opt/flarum/flarum cache:clear`.
5. Document `rx-skins/` and `deploy-rx-skins.py` in `scripts/README.md`.

- [ ] **Step 4: Run full live verification and server backup**

Run: `python3 -m unittest scripts/tests/test_rx_skins.py -v && python3 scripts/verify-live-halo.py && ssh vps8 '/opt/site-stack/backup.sh'`
Expected: PASS (`exit code 0` across all URLs, search, Flarum guide, 4 skins × Light/Dark on both domains, cross-site Cookie sync, admin isolation, `1280px`/`390px` zero overflow, plus fresh backup archive created).

- [ ] **Step 5: Commit and push to `origin/main`**

```bash
git add scripts/deploy-rx-skins.py scripts/verify-live-halo.py scripts/README.md
git commit -m "feat(live): deploy CC 4-skin system across Halo and Flarum with e2e verification"
git push origin main
```
