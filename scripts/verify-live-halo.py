#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end live verification for https://blog.mycampusmail.com & https://qa.mycampusmail.com:
  1. HTTP 200 across homepage, /my-reviews, /tools, /about, /privacy-policy, /user-agreement,
     uploaded favicon & dual-volume cover PNGs, category/tag pages, and all 6 published VPS posts
  2. Homepage pinned order (#1 Vol. 1, #2 Vol. 2), favicon=/upload/favicon.png, dual-volume cover cards,
     /my-reviews & /tools in primary menu, and 0 placeholder welcome stubs
  3. /privacy-policy & /user-agreement legal SinglePages (zero default placeholder text, Light/Dark card styles)
  4. Halo Lucene Search API hits for colloquial vendor nicknames (大妈, 瓦工, 御坂, 丽萨, 小秘书)
  5. Flarum qa.mycampusmail.com sticky official VPS guide thread under Tag 1 (VPS 科普)
  6. Zero broken #anchors, zero stale /vps/ links, denoised sidebar TOC (.toc a <= 280),
     #vps-vendor-wall (61 / 56 vendor jump pills), slang filter expansion, and zero blurred <pre> blocks
  7. Light Mode vs Dark Mode (html.dark) computed styles and zero horizontal overflow on 1280px & 390px viewports
"""
import itertools, json, shutil, subprocess, tempfile, time, urllib.request
import websocket

PORT = 9242
BASE = "https://blog.mycampusmail.com"
QA_BASE = "https://qa.mycampusmail.com"

POST_URLS = [
    f"{BASE}/archives/nodeseek-merchant-reviews-2026h2",
    f"{BASE}/archives/meowvps-official-merchants-2026h2",
    f"{BASE}/archives/reading-vps-reviews",
    f"{BASE}/archives/relay-and-egress-guide",
    f"{BASE}/archives/mihomo-chain-and-fallback",
    f"{BASE}/archives/first-post",
]
PAGE_URLS = [
    f"{BASE}/",
    f"{BASE}/my-reviews",
    f"{BASE}/tools",
    f"{BASE}/about",
    f"{BASE}/privacy-policy",
    f"{BASE}/user-agreement",
    f"{BASE}/upload/favicon.png",
    f"{BASE}/upload/vps-vol1-cover.png",
    f"{BASE}/upload/vps-vol2-cover.png",
    f"{BASE}/upload/reading-vps-reviews-cover.png",
    f"{BASE}/upload/relay-and-egress-guide-cover.png",
    f"{BASE}/upload/mihomo-chain-and-fallback-cover.png",
    f"{BASE}/upload/first-post-cover.png",
    f"{BASE}/upload/site-hero-banner.png",
    f"{QA_BASE}/assets/favicon.png",
    f"{QA_BASE}/sitemap.xml",
    f"{QA_BASE}/feed.rss",
    f"{BASE}/categories/vps",
    f"{BASE}/categories/ai",
    f"{BASE}/categories/fsae",
    f"{BASE}/categories/rm",
    f"{BASE}/categories/resources",
    f"{BASE}/tags/isp",
]


def http_fetch(req, timeout=20, retries=3):
    last_err = None
    for att in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), dict(r.headers)
        except Exception as e:
            last_err = e
            time.sleep(0.8 * (att + 1))
    raise last_err


def check_halo_nickname_search():
    print("\n=== HALO LUCENE NICKNAME SEARCH AUDIT ===")
    for kw in ["大妈", "瓦工", "御坂", "丽萨", "小秘书"]:
        payload = json.dumps({"keyword": kw, "limit": 5, "includeTypes": ["post.content.halo.run"]}, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{BASE}/apis/api.halo.run/v1alpha1/indices/-/search",
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "Mozilla/5.0"},
            method="POST",
        )
        _, raw, _ = http_fetch(req, timeout=15)
        res = json.loads(raw.decode("utf-8"))
        hits = res.get("hits") or []
        titles = [h.get("title", "") for h in hits]
        print(f"  keyword={kw:4s} -> hits={len(hits)} | {titles[:2]}")
        assert len(hits) >= 1, f"Halo search returned 0 hits for colloquial nickname: {kw}"


def check_flarum_vps_guide():
    print("\n=== FLARUM QA COMMUNITY AUDIT ===")
    req = urllib.request.Request(
        f"{QA_BASE}/api/discussions?include=tags",
        headers={"Accept": "application/vnd.api+json", "User-Agent": "Mozilla/5.0"},
    )
    _, raw, _ = http_fetch(req, timeout=15)
    data = json.loads(raw.decode("utf-8"))
    vps_guides = [
        d for d in data.get("data", [])
        if "【VPS 交流】" in d.get("attributes", {}).get("title", "")
    ]
    assert len(vps_guides) >= 1, "Missing 【VPS 交流】 official guide thread on qa.mycampusmail.com"
    g = vps_guides[0]
    print(f"  Found Flarum VPS Guide ID={g['id']} | sticky={g['attributes'].get('isSticky')} | title={g['attributes']['title']}")
    assert g["attributes"].get("isSticky") is True
    _, qa_raw, _ = http_fetch(urllib.request.Request(f"{QA_BASE}/", headers={"User-Agent": "Mozilla/5.0"}), timeout=15)
    qa_html = qa_raw.decode("utf-8", errors="replace")
    assert "assets/favicon.png" in qa_html, "Flarum missing favicon.png link"
    assert "117 家商家测评" in qa_html, "Flarum missing updated forum_description / header"
    assert "https://blog.mycampusmail.com/tools" in qa_html, "Flarum header missing /tools direct link"
    assert "https://blog.mycampusmail.com/my-reviews" in qa_html, "Flarum header missing /my-reviews direct link"
    assert "/vps/first-post/" not in qa_html, "Flarum header still has legacy /vps/first-post/ link"
    print("  Flarum HTML Head & Top Banner : favicon.png=True | /my-reviews=True | /tools=True | legacy_links=0")
    try:
        urllib.request.urlopen(urllib.request.Request(f"{QA_BASE}/sync-admin.php", headers={"User-Agent": "Mozilla/5.0"}), timeout=10)
        raise AssertionError("sync-admin.php should return 404 after archiving!")
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404 for archived sync-admin.php, got {e.code}"
        print("  Legacy sync-admin.php         : HTTP 404 (archived safely outside webroot)")


def main():
    for u in PAGE_URLS + POST_URLS:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
        status, b, hdrs = http_fetch(req, timeout=20)
        print(f"[HTTP {status}] {len(b):9,d} bytes | {u}")
        assert status == 200
        assert hdrs.get("X-Content-Type-Options") == "nosniff", f"Missing nosniff on {u}: {hdrs}"
        if "/upload/" in u:
            assert "max-age=604800" in hdrs.get("Cache-Control", ""), f"Missing immutable cache on {u}: {hdrs}"

    check_halo_nickname_search()
    check_flarum_vps_guide()

    tmp_prof = tempfile.mkdtemp(prefix="cdp-verify-")
    chrome_proc = subprocess.Popen(
        [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            f"--remote-debugging-port={PORT}",
            f"--user-data-dir={tmp_prof}",
            "--no-first-run",
            "--no-default-browser-check",
            "--headless=new",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(15):
            time.sleep(1)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=2)
                break
            except Exception:
                pass
        else:
            raise RuntimeError("Chrome CDP failed to start")

        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list").read().decode())
        ws_u = [t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page"][0]
        ws = websocket.create_connection(ws_u, timeout=45, suppress_origin=True)
        _id = itertools.count(1)

        def call(method, **params):
            i = next(_id)
            ws.send(json.dumps({"id": i, "method": method, "params": params}))
            while True:
                m = json.loads(ws.recv())
                if m.get("id") == i:
                    return m.get("result", {})

        call("Page.enable")
        call("Network.enable")
        call("Network.setCacheDisabled", cacheDisabled=True)

        # 1. Verify Homepage Pinned Order, Favicon, Cover Images, /my-reviews & /tools Nav Items & Zero Stub Posts
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/?_t={int(time.time())}")
        time.sleep(2.5)
        home_js = r"""
        (() => {
          const links = Array.from(document.querySelectorAll('a[href*="/archives/"]'))
            .map(a => ({ href: a.getAttribute('href'), text: (a.textContent || '').trim() }))
            .filter(x => x.text.length > 4);
          const seen = [];
          for (const l of links) {
            if (!seen.some(s => s.href === l.href)) seen.push(l);
          }
          const iconHref = document.querySelector('link[rel*="icon"]')?.getAttribute('href') || '';
          const imgs = Array.from(document.querySelectorAll('img')).map(i => i.getAttribute('src') || '');
          const expectedCovers = [
            'vps-vol1-cover.png', 'vps-vol2-cover.png',
            'reading-vps-reviews-cover.png', 'relay-and-egress-guide-cover.png',
            'mihomo-chain-and-fallback-cover.png', 'first-post-cover.png'
          ];
          const coversFound = expectedCovers.filter(c => imgs.some(s => s.includes(c))).length;
          const hasVol1Cover = coversFound === 6;
          const hasVol2Cover = coversFound === 6;
          const hasMyReviewsNav = Array.from(document.querySelectorAll('header a[href="/my-reviews"]')).length > 0;
          const hasToolsNav = Array.from(document.querySelectorAll('header a[href="/tools"]')).length > 0;
          const htmlSrc = document.documentElement.outerHTML;
          const hasHeroBanner = htmlSrc.includes('site-hero-banner.png') && !htmlSrc.includes('default-background-2023-10-12.jpeg');
          const footerHrefs = Array.from(document.querySelectorAll('footer a')).map(a => a.getAttribute('href') || '');
          const hasFooterLinks = ['/privacy-policy', '/user-agreement', '/rss.xml', '/sitemap.xml'].every(p => footerHrefs.some(h => h.includes(p)));
          const bodyTxt = document.body.innerText;
          const stubsPresent = ['AI 分区开篇', '资源分区开篇', 'RoboMaster 分区开篇', '车队的第一篇记录'].filter(t => bodyTxt.includes(t));
          return JSON.stringify({
            archiveCards: seen,
            iconHref,
            hasVol1Cover,
            hasVol2Cover,
            hasMyReviewsNav,
            hasToolsNav,
            stubsPresent, hasHeroBanner, hasFooterLinks,
            sw: document.documentElement.scrollWidth,
            iw: window.innerWidth
          });
        })()
        """
        home_res = json.loads(call("Runtime.evaluate", expression=home_js, returnByValue=True)["result"]["value"])
        print("\n=== HOMEPAGE AUDIT ===")
        for idx, c in enumerate(home_res["archiveCards"]):
            print(f"  #{idx+1}: {c['href']} -> {c['text']}")
        print(f"  Favicon={home_res['iconHref']} | Covers: vol1={home_res['hasVol1Cover']}, vol2={home_res['hasVol2Cover']}")
        print(f"  Header has /my-reviews={home_res['hasMyReviewsNav']}, /tools={home_res['hasToolsNav']} | Stubs: {home_res['stubsPresent']} | Width: {home_res['sw']}<={home_res['iw']}")
        assert len(home_res["archiveCards"]) >= 6
        assert home_res["archiveCards"][0]["href"].endswith("/archives/nodeseek-merchant-reviews-2026h2")
        assert home_res["archiveCards"][1]["href"].endswith("/archives/meowvps-official-merchants-2026h2")
        assert "favicon.png" in home_res["iconHref"]
        assert home_res["hasVol1Cover"] is True and home_res["hasVol2Cover"] is True
        assert home_res["hasMyReviewsNav"] is True
        assert home_res["hasToolsNav"] is True
        assert home_res["hasHeroBanner"] is True, "Homepage still using default landscape hero background"
        assert home_res["hasFooterLinks"] is True, "Footer missing legal/RSS/sitemap menu links"
        print(f"  Hero Banner & Footer Menu     : customHero={home_res['hasHeroBanner']}, footerMenu={home_res['hasFooterLinks']}")
        assert home_res["stubsPresent"] == [], f"Welcome stubs still visible: {home_res['stubsPresent']}"
        assert home_res["sw"] <= home_res["iw"]

        # 1b. Audit /my-reviews SinglePage
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/my-reviews?_t={int(time.time())}")
        time.sleep(2.5)
        reviews_js = r"""
        (() => {
          document.documentElement.classList.remove('dark');
          const box = document.getElementById('rx-reviews');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark');
          const hasCheckPlace = Array.from(document.querySelectorAll('a[href*="1PBAA6I6S.svg"], img[src*="1PBAA6I6S.svg"]')).length >= 2;
          return JSON.stringify({
            exists: !!box, lightCardBg, darkCardBg, hasCheckPlace,
            sw: document.documentElement.scrollWidth, iw: window.innerWidth
          });
        })()
        """
        reviews_res = json.loads(call("Runtime.evaluate", expression=reviews_js, returnByValue=True)["result"]["value"])
        call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        time.sleep(0.5)
        reviews_mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])
        print("\n=== /my-reviews SINGLEPAGE AUDIT ===")
        print(f"  Cards Light/Dark : {reviews_res['lightCardBg']} -> {reviews_res['darkCardBg']} | CheckPlace={reviews_res['hasCheckPlace']}")
        print(f"  Responsive       : 1280px ({reviews_res['sw']}<={reviews_res['iw']}), 390px ({reviews_mob['sw']}<={reviews_mob['iw']})")
        assert reviews_res["exists"] is True
        assert reviews_res["lightCardBg"] == "rgb(255, 255, 255)"
        assert reviews_res["darkCardBg"] == "rgb(30, 41, 59)"
        assert reviews_res["hasCheckPlace"] is True
        assert reviews_res["sw"] <= reviews_res["iw"] and reviews_mob["sw"] <= reviews_mob["iw"]

        # 2. Audit /tools Interactive SinglePage
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/tools?_t={int(time.time())}")
        time.sleep(2.5)
        tools_js = r"""
        (() => {
          document.documentElement.classList.remove('dark');
          const box = document.getElementById('rx-toolbox');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark');
          const vpsTxt = (document.getElementById('vps-result')?.textContent || '').trim();
          const batTxt = (document.getElementById('bat-result')?.textContent || '').trim();
          const blurredPres = Array.from(document.querySelectorAll('pre')).filter(p => {
            const cs = getComputedStyle(p);
            return cs.display !== 'none' && cs.filter && cs.filter.includes('blur');
          }).length;
          return JSON.stringify({
            exists: !!box, lightCardBg, darkCardBg, vpsTxt, batTxt, blurredPres,
            sw: document.documentElement.scrollWidth, iw: window.innerWidth
          });
        })()
        """
        tools_res = json.loads(call("Runtime.evaluate", expression=tools_js, returnByValue=True)["result"]["value"])
        call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        time.sleep(0.5)
        tools_mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])
        print("\n=== /tools SINGLEPAGE AUDIT ===")
        print(f"  Cards Light/Dark : {tools_res['lightCardBg']} -> {tools_res['darkCardBg']} | blurredPre={tools_res['blurredPres']}")
        print(f"  Calc Outputs     : VPS=[{tools_res['vpsTxt']}] | BAT=[{tools_res['batTxt']}]")
        print(f"  Responsive       : 1280px ({tools_res['sw']}<={tools_res['iw']}), 390px ({tools_mob['sw']}<={tools_mob['iw']})")
        assert tools_res["exists"] is True
        assert tools_res["lightCardBg"] == "rgb(255, 255, 255)"
        assert tools_res["darkCardBg"] == "rgb(30, 41, 59)"
        assert "剩余天数" in tools_res["vpsTxt"] and "6S1P" in tools_res["batTxt"]
        assert tools_res["blurredPres"] == 0
        assert tools_res["sw"] <= tools_res["iw"] and tools_mob["sw"] <= tools_mob["iw"]

        # 2a. Audit /about SinglePage (Zero Default Placeholder Meta Description + Light/Dark Cards)
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/about?_t={int(time.time())}")
        time.sleep(2.0)
        about_js = r"""
        (() => {
          document.documentElement.classList.remove('dark');
          const box = document.getElementById('rx-about');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark');
          const metaDesc = document.querySelector('meta[name="description"]')?.getAttribute('content') || '';
          return JSON.stringify({
            exists: !!box, lightCardBg, darkCardBg, metaDesc,
            sw: document.documentElement.scrollWidth, iw: window.innerWidth
          });
        })()
        """
        about_res = json.loads(call("Runtime.evaluate", expression=about_js, returnByValue=True)["result"]["value"])
        call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
        time.sleep(0.4)
        about_mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])
        print("\n=== /about SINGLEPAGE AUDIT ===")
        print(f"  Cards Light/Dark : {about_res['lightCardBg']} -> {about_res['darkCardBg']} | desc={about_res['metaDesc'][:42]}...")
        print(f"  Responsive       : 1280px ({about_res['sw']}<={about_res['iw']}), 390px ({about_mob['sw']}<={about_mob['iw']})")
        assert about_res["exists"] is True
        assert "这是一个自定义页面" not in about_res["metaDesc"], about_res["metaDesc"]
        assert "117 家" in about_res["metaDesc"], about_res["metaDesc"]
        assert about_res["lightCardBg"] == "rgb(255, 255, 255)"
        assert about_res["darkCardBg"] == "rgb(30, 41, 59)"
        assert about_res["sw"] <= about_res["iw"] and about_mob["sw"] <= about_mob["iw"]

        # 2b. Audit /privacy-policy & /user-agreement Legal SinglePages
        for slug in ["privacy-policy", "user-agreement"]:
            call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            call("Page.navigate", url=f"{BASE}/{slug}?_t={int(time.time())}")
            time.sleep(2.0)
            legal_js = r"""
            (() => {
              document.documentElement.classList.remove('dark');
              const box = document.querySelector('.rx-legal');
              const card = box ? box.querySelector('.rx-legal-meta') : null;
              const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
              document.documentElement.classList.add('dark');
              const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
              document.documentElement.classList.remove('dark');
              const hasPlaceholder = document.body.innerText.includes('请在此处添加');
              return JSON.stringify({
                exists: !!box, lightCardBg, darkCardBg, hasPlaceholder,
                sw: document.documentElement.scrollWidth, iw: window.innerWidth
              });
            })()
            """
            legal_res = json.loads(call("Runtime.evaluate", expression=legal_js, returnByValue=True)["result"]["value"])
            call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
            time.sleep(0.4)
            legal_mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])
            print(f"\n=== /{slug} LEGAL SINGLEPAGE AUDIT ===")
            print(f"  Cards Light/Dark : {legal_res['lightCardBg']} -> {legal_res['darkCardBg']} | hasPlaceholder={legal_res['hasPlaceholder']}")
            print(f"  Responsive       : 1280px ({legal_res['sw']}<={legal_res['iw']}), 390px ({legal_mob['sw']}<={legal_mob['iw']})")
            assert legal_res["exists"] is True
            assert legal_res["hasPlaceholder"] is False
            assert legal_res["lightCardBg"] == "rgb(248, 250, 252)"
            assert legal_res["darkCardBg"] == "rgb(30, 41, 59)"
            assert legal_res["sw"] <= legal_res["iw"] and legal_mob["sw"] <= legal_mob["iw"]

        # 3. Audit All 6 VPS Posts + Vendor Wall + Slang Filter + Zero Blurred Pre Blocks + Light/Dark Styles
        JS_POST_AUDIT = r"""
        (() => {
          document.documentElement.classList.remove('dark');
          const md = document.querySelector('.markdown-body') || document.body;
          const hashLinks = Array.from(md.querySelectorAll('a[href^="#"]'));
          const brokenAnchors = hashLinks
            .map(a => a.getAttribute('href'))
            .filter(h => h.length > 1 && !document.getElementById(decodeURIComponent(h.slice(1))));
          const staleVpsLinks = Array.from(md.querySelectorAll('a[href]'))
            .map(a => a.getAttribute('href'))
            .filter(h => h && h.startsWith('/vps/'));
          const tocLinks = document.querySelectorAll('.toc a').length;
          const detailsAll = Array.from(md.querySelectorAll('details:not(#vps-vendor-wall)'));
          const defaultOpen = detailsAll.filter(d => d.open).length;
          const vendorWall = document.getElementById('vps-vendor-wall');
          const vendorPillCount = vendorWall ? vendorWall.querySelectorAll('.vps-vendor-pill').length : 0;

          // Temporarily open first 5 details to verify zero blurred <pre>!
          detailsAll.slice(0, 5).forEach(d => { d.open = true; });
          const visibleBlurredPres = Array.from(md.querySelectorAll('pre')).filter(p => {
            const cs = getComputedStyle(p);
            return cs.display !== 'none' && cs.filter && cs.filter.includes('blur');
          }).length;
          const rawPre = md.querySelector('pre.vps-raw-report');
          const rawPreLightBg = rawPre ? getComputedStyle(rawPre).backgroundColor : '';
          document.documentElement.classList.add('dark');
          const rawPreDarkBg = rawPre ? getComputedStyle(rawPre).backgroundColor : '';
          document.documentElement.classList.remove('dark');
          detailsAll.slice(0, 5).forEach(d => { d.open = false; });

          let toolbarCheck = null;
          const tb = document.getElementById('vps-quick-toolbar');
          const input = document.getElementById('vps-filter-input');
          const expandBtn = document.getElementById('vps-expand-all');
          const collapseBtn = document.getElementById('vps-collapse-all');
          const clearBtn = document.getElementById('vps-filter-clear');
          const statusEl = document.getElementById('vps-filter-status');

          if (tb && input && expandBtn && collapseBtn) {
            const activeChip = tb.querySelector('.vps-tb-chip.is-active');
            if (activeChip) activeChip.style.transition = 'none';
            const lightBg = getComputedStyle(tb).backgroundColor;
            const lightChipBg = activeChip ? getComputedStyle(activeChip).backgroundColor : '';

            document.documentElement.classList.add('dark');
            const darkBg = getComputedStyle(tb).backgroundColor;
            const darkInputBg = getComputedStyle(input).backgroundColor;
            const darkChipBg = activeChip ? getComputedStyle(activeChip).backgroundColor : '';
            const subHead = md.querySelector('.vps-review-subheading');
            const darkSubHeadColor = subHead ? getComputedStyle(subHead).color : '';
            document.documentElement.classList.remove('dark');
            if (activeChip) activeChip.style.transition = '';

            const slangTerm = location.pathname.includes('meowvps-official-merchants') ? '大妈' : '御坂';
            input.value = slangTerm;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            const statusAfterSlang = statusEl ? statusEl.textContent : '';
            clearBtn.click();

            input.value = '9929';
            input.dispatchEvent(new Event('input', { bubbles: true }));
            const statusAfterFilter = statusEl ? statusEl.textContent : '';
            clearBtn.click();
            expandBtn.click();
            const openAfterExpand = detailsAll.filter(d => d.open).length;
            collapseBtn.click();
            const openAfterCollapse = detailsAll.filter(d => d.open).length;

            toolbarCheck = {
              lightBg, lightChipBg, darkBg, darkInputBg, darkChipBg, darkSubHeadColor,
              slangTerm, statusAfterSlang, statusAfterFilter, openAfterExpand, openAfterCollapse
            };
          }

          return JSON.stringify({
            hashLinkCount: hashLinks.length,
            brokenAnchorCount: brokenAnchors.length,
            staleVpsLinkCount: staleVpsLinks.length,
            tocLinks,
            detailsTotal: detailsAll.length,
            defaultOpen,
            vendorPillCount,
            visibleBlurredPres,
            rawPreLightBg,
            rawPreDarkBg,
            toolbarCheck,
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth
          });
        })()
        """

        for u in POST_URLS:
            call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            call("Page.navigate", url=u + f"?_t={int(time.time())}")
            time.sleep(3.5)
            res = json.loads(call("Runtime.evaluate", expression=JS_POST_AUDIT, returnByValue=True)["result"]["value"])

            call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
            time.sleep(0.7)
            mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])

            print(f"\n=== POST AUDIT: {u} ===")
            print(f"  Anchors={res['hashLinkCount']} (broken={res['brokenAnchorCount']}), stale=/vps/={res['staleVpsLinkCount']}, TOC={res['tocLinks']}, vendorPills={res['vendorPillCount']}, details={res['detailsTotal']}, blurredPre={res['visibleBlurredPres']}")
            if res["rawPreLightBg"]:
                print(f"  Raw <pre> Bg     : light={res['rawPreLightBg']} -> dark={res['rawPreDarkBg']}")
                assert res["rawPreLightBg"] == "rgb(248, 250, 252)", res["rawPreLightBg"]
                assert res["rawPreDarkBg"] == "rgb(15, 23, 42)", res["rawPreDarkBg"]
            if u.endswith("nodeseek-merchant-reviews-2026h2"):
                assert res["vendorPillCount"] == 61, res["vendorPillCount"]
                assert res["detailsTotal"] == 319, res["detailsTotal"]
            elif u.endswith("meowvps-official-merchants-2026h2"):
                assert res["vendorPillCount"] == 56, res["vendorPillCount"]
                assert res["detailsTotal"] == 137, res["detailsTotal"]
            if res["toolbarCheck"]:
                tc = res["toolbarCheck"]
                print(f"  Light vs Dark TB : light={tc['lightBg']} / chip={tc['lightChipBg']} -> dark={tc['darkBg']} / input={tc['darkInputBg']} / chip={tc['darkChipBg']}")
                print(f"  Slang & Filter   : [{tc['slangTerm']}] -> {tc['statusAfterSlang']} | [9929] -> {tc['statusAfterFilter']}")
                print(f"  Details Toggle   : expand={tc['openAfterExpand']} -> collapse={tc['openAfterCollapse']}")
                assert tc["lightBg"] == "rgb(248, 250, 252)", tc
                assert tc["darkBg"] == "rgb(30, 41, 59)", tc
                assert tc["darkInputBg"] == "rgb(15, 23, 42)", tc
                assert tc["darkChipBg"] == "rgb(56, 189, 248)", tc
                assert "匹配 0" not in tc["statusAfterSlang"], tc["statusAfterSlang"]
                assert tc["openAfterExpand"] == res["detailsTotal"] and tc["openAfterCollapse"] == 0
            print(f"  Responsive       : 1280px ({res['scrollWidth']}<={res['innerWidth']}), 390px ({mob['sw']}<={mob['iw']})")
            assert res["brokenAnchorCount"] == 0
            assert res["staleVpsLinkCount"] == 0
            assert res["visibleBlurredPres"] == 0, f"Blurred <pre> still present on {u}: {res['visibleBlurredPres']}"
            assert res["tocLinks"] <= 280
            assert res["scrollWidth"] <= res["innerWidth"]
            assert mob["sw"] <= mob["iw"]

        ws.close()
        print("\nALL HOMEPAGE PINNING, FAVICON, COVERS, LEGAL PAGES, VENDOR WALL, NICKNAME SEARCH, FLARUM GUIDE, ZERO-BLUR PRE, DARK MODE & MOBILE CHECKS PASSED 100%!")
    finally:
        chrome_proc.terminate()
        shutil.rmtree(tmp_prof, ignore_errors=True)


if __name__ == "__main__":
    main()
