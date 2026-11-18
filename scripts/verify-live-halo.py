#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end live verification for https://blog.mycampusmail.com & https://qa.mycampusmail.com:
  1. HTTP 200 across homepage, /my-reviews, /tools, /about, /privacy-policy, /user-agreement,
     uploaded favicon & dual-volume cover PNGs, category/tag pages, all 6 published VPS posts,
     and all 7 /rx-skins/* static assets on BOTH subdomains (with Cache-Control: max-age=604800)
  2. Homepage pinned order (#1 Vol. 1, #2 Vol. 2), favicon=/upload/favicon.png, dual-volume cover cards,
     /my-reviews & /tools in primary menu, and 0 placeholder welcome stubs
  3. /privacy-policy & /user-agreement legal SinglePages (zero default placeholder text, Light/Dark card styles)
  4. Halo Lucene Search API hits for colloquial vendor nicknames (大妈, 瓦工, 御坂, 丽萨, 小秘书)
  5. Flarum qa.mycampusmail.com sticky official VPS guide thread under Tag 1 (VPS 科普)
  6. Zero broken #anchors, zero stale /vps/ links, denoised sidebar TOC (.toc a <= 280),
     #vps-vendor-wall (61 / 56 vendor jump pills), slang filter expansion, and zero blurred <pre> blocks
  7. CC 4-Skin System (pop, ink, luxe, plain) × Light/Dark across BOTH sites, pre.vps-raw-report dark high-contrast
     protection in all 8 modes, cross-subdomain .mycampusmail.com Cookie sync (blog -> qa), Flarum SPA remount,
     /console & /admin zero-injection isolation, and zero horizontal overflow on 1280px & 390px viewports
"""
import itertools, json, re, shutil, subprocess, tempfile, time, urllib.error, urllib.request
import websocket

PORT = 9242
BASE = "https://blog.mycampusmail.com"
QA_BASE = "https://qa.mycampusmail.com"

SKIN_STATIC_FILES = [
    "rx-tokens.css",
    "rx-halo.css",
    "rx-flarum.css",
    "rx-switcher.js",
    "ink-landscape.svg",
    "ink-mountains.svg",
    "ink-stroke.svg",
]

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


def _rgb_luminance(rgb_str: str) -> float:
    nums = [int(x) for x in re.findall(r"\d+", rgb_str or "")[:3]]
    if len(nums) < 3:
        return 0.0
    vals = []
    for c in nums:
        v = c / 255.0
        vals.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def http_fetch(req, timeout=20, retries=3):
    last_err = None
    for att in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read(), dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise
            last_err = e
            time.sleep(0.8 * (att + 1))
        except Exception as e:
            last_err = e
            time.sleep(0.8 * (att + 1))
    raise last_err


def check_rx_skins_static_endpoints():
    print("\n=== RX-SKINS SAME-ORIGIN STATIC ENDPOINTS AUDIT ===")
    for origin in (BASE, QA_BASE):
        for fname in SKIN_STATIC_FILES:
            url = f"{origin}/rx-skins/{fname}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
            status, body, hdrs = http_fetch(req, timeout=15)
            cc = hdrs.get("Cache-Control", hdrs.get("cache-control", ""))
            print(f"  [HTTP {status}] {len(body):7,d} bytes | cache={cc} | {url}")
            assert status == 200 and len(body) > 50, f"Bad response on {url}: status={status}, len={len(body)}"
            assert "max-age=604800" in cc, f"Missing Cache-Control max-age=604800 on {url}: {cc}"


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
    assert "/rx-skins/rx-flarum.css" in qa_html, "Flarum HTML missing /rx-skins/rx-flarum.css"
    assert "/vps/first-post/" not in qa_html, "Flarum header still has legacy /vps/first-post/ link"
    print("  Flarum HTML Head & Top Banner : favicon.png=True | /my-reviews=True | /tools=True | rx-flarum.css=True")
    try:
        urllib.request.urlopen(urllib.request.Request(f"{QA_BASE}/sync-admin.php", headers={"User-Agent": "Mozilla/5.0"}), timeout=10)
        raise AssertionError("sync-admin.php should return 404 after archiving!")
    except urllib.error.HTTPError as e:
        assert e.code == 404, f"Expected 404 for archived sync-admin.php, got {e.code}"
        print("  Legacy sync-admin.php         : HTTP 404 (archived safely outside webroot)")
    return str(g["id"])


def check_dual_site_cc_skins(call, guide_id: str):
    print("\n=== CC 4-SKIN DUAL-SITE & CROSS-COOKIE E2E AUDIT ===")
    call("Network.clearBrowserCookies")
    call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
    call("Page.navigate", url=f"{BASE}/?_skin_audit={int(time.time())}")
    time.sleep(2.5)

    halo_home_skins = json.loads(call("Runtime.evaluate", expression=r"""
    (() => {
      const initialSkin = document.documentElement.dataset.rxSkin || '';
      const hasBtn = !!document.getElementById('rx-skin-toggle');
      const hasProgress = !!document.getElementById('rx-read-progress');
      const bgs = {};
      for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
        window.RXSkins.setSkin(sk);
        document.documentElement.dataset.rxSkin = sk;
        document.documentElement.classList.remove('rx-dark', 'dark');
        bgs[sk + ':light'] = getComputedStyle(document.body).backgroundColor;
        document.documentElement.classList.add('rx-dark', 'dark');
        bgs[sk + ':dark'] = getComputedStyle(document.body).backgroundColor;
      }
      document.documentElement.classList.remove('rx-dark', 'dark');
      window.RXSkins.setSkin('pop');
      return JSON.stringify({ initialSkin, hasBtn, hasProgress, bgs });
    })()
    """, returnByValue=True)["result"]["value"])

    print(f"  Halo Default Boot             : skin={halo_home_skins['initialSkin']} | toggle={halo_home_skins['hasBtn']} | progress={halo_home_skins['hasProgress']}")
    print(f"  Halo 4-Skin Light Bgs         : pop={halo_home_skins['bgs']['pop:light']} | ink={halo_home_skins['bgs']['ink:light']} | luxe={halo_home_skins['bgs']['luxe:light']} | plain={halo_home_skins['bgs']['plain:light']}")
    assert halo_home_skins["initialSkin"] == "pop", halo_home_skins
    assert halo_home_skins["hasBtn"] is True and halo_home_skins["hasProgress"] is True
    assert halo_home_skins["bgs"]["pop:light"] == "rgb(255, 247, 232)", halo_home_skins["bgs"]
    assert halo_home_skins["bgs"]["ink:light"] == "rgb(239, 231, 214)", halo_home_skins["bgs"]
    assert halo_home_skins["bgs"]["luxe:light"] == "rgb(246, 241, 233)", halo_home_skins["bgs"]
    assert halo_home_skins["bgs"]["plain:light"] == "rgb(255, 255, 255)", halo_home_skins["bgs"]
    for sk in ("pop", "ink", "luxe", "plain"):
        assert halo_home_skins["bgs"][f"{sk}:light"] != halo_home_skins["bgs"][f"{sk}:dark"]

    # Check Halo 390px mobile across all 4 skins
    call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    time.sleep(0.5)
    halo_mob = json.loads(call("Runtime.evaluate", expression=r"""
    (() => {
      const out = {};
      for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
        document.documentElement.dataset.rxSkin = sk;
        out[sk] = { sw: document.documentElement.scrollWidth, iw: window.innerWidth };
      }
      document.documentElement.dataset.rxSkin = 'pop';
      return JSON.stringify(out);
    })()
    """, returnByValue=True)["result"]["value"])
    for sk, dims in halo_mob.items():
        assert dims["sw"] <= dims["iw"], f"Halo homepage 390px overflow in {sk}: {dims}"

    # Check pre.vps-raw-report across all 8 skin × theme combinations on Vol.1
    call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
    call("Page.navigate", url=f"{BASE}/archives/nodeseek-merchant-reviews-2026h2?_skin_pre={int(time.time())}")
    time.sleep(3.0)
    pre_matrix = json.loads(call("Runtime.evaluate", expression=r"""
    (() => {
      const d = document.querySelector('details:not(#vps-vendor-wall)');
      if (d) d.open = true;
      const pre = document.querySelector('pre.vps-raw-report');
      const out = {};
      for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
        for (const dk of [false, true]) {
          document.documentElement.dataset.rxSkin = sk;
          document.documentElement.classList.toggle('rx-dark', dk);
          document.documentElement.classList.toggle('dark', dk);
          const cs = getComputedStyle(pre);
          out[sk + ':' + (dk ? 'dark' : 'light')] = { filter: cs.filter, bg: cs.backgroundColor, fg: cs.color };
        }
      }
      if (d) d.open = false;
      return JSON.stringify(out);
    })()
    """, returnByValue=True)["result"]["value"])
    for key, st in pre_matrix.items():
        assert st["filter"] == "none", f"Blurred pre in {key}: {st}"
        assert _rgb_luminance(st["bg"]) < 0.12, f"Raw pre bg not dark in {key}: {st}"
        assert _rgb_luminance(st["fg"]) > 0.65, f"Raw pre fg not readable in {key}: {st}"
    print(f"  Halo Raw <pre> 8-Mode Matrix  : plain:light bg={pre_matrix['plain:light']['bg']} fg={pre_matrix['plain:light']['fg']} (ALL 8 unblurred & dark)")

    # Cross-subdomain Cookie sync: set 'ink' + 'dark' on blog.mycampusmail.com -> navigate to qa.mycampusmail.com
    call("Runtime.evaluate", expression="window.RXSkins.setSkin('ink'); window.RXSkins.setTheme('dark', null, true);")
    time.sleep(0.3)
    call("Page.navigate", url=f"{QA_BASE}/?_sync={int(time.time())}")
    time.sleep(3.0)
    qa_boot = call("Runtime.evaluate", expression=r"""
    (() => ({
      rxSkin: document.documentElement.dataset.rxSkin || '',
      dataTheme: document.documentElement.getAttribute('data-theme') || '',
      rxDark: document.documentElement.classList.contains('rx-dark'),
      skinBtnCount: document.querySelectorAll('#rx-skin-toggle').length,
      themeBtnCount: document.querySelectorAll('#rx-theme-toggle').length,
      hasCheckin: !!document.getElementById('rx-checkin-btn'),
      hasCaptcha: !!document.getElementById('rx-captcha-float'),
      fnCheckin: typeof window.__rxCheckin,
      fnEmail: typeof window.__rxSendEmailCode,
    }))()
    """, returnByValue=True)["result"]["value"]
    print(f"  Cross-Subdomain Sync (blog->qa): rxSkin={qa_boot['rxSkin']} | data-theme={qa_boot['dataTheme']} | rxDark={qa_boot['rxDark']}")
    assert qa_boot["rxSkin"] == "ink", f"Cross-subdomain skin cookie failed: {qa_boot}"
    assert qa_boot["dataTheme"].startswith("dark") and qa_boot["rxDark"] is True, f"Cross-subdomain theme cookie failed: {qa_boot}"
    assert qa_boot["skinBtnCount"] == 1 and qa_boot["themeBtnCount"] == 1, qa_boot
    assert qa_boot["hasCheckin"] is True and qa_boot["hasCaptcha"] is True
    assert qa_boot["fnCheckin"] == "function" and qa_boot["fnEmail"] == "function"

    # Flarum 4-skin × Light/Dark matrix + SPA navigation to discussion thread
    qa_matrix = json.loads(call("Runtime.evaluate", expression=r"""
    (() => {
      const out = {};
      const cross = document.querySelector('.rx-qa-crossbar');
      for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
        for (const dk of [false, true]) {
          document.documentElement.dataset.rxSkin = sk;
          document.documentElement.classList.toggle('rx-dark', dk);
          document.documentElement.setAttribute('data-theme', dk ? 'dark' : 'light');
          out[sk + ':' + (dk ? 'dark' : 'light')] = {
            primary: getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim().toLowerCase(),
            bodyBg: getComputedStyle(document.body).backgroundColor,
            crossBg: cross ? getComputedStyle(cross).backgroundColor : ''
          };
        }
      }
      return JSON.stringify(out);
    })()
    """, returnByValue=True)["result"]["value"])
    for key, st in qa_matrix.items():
        assert st["primary"] != "#4d698e", f"Flarum --primary-color still cold blue in {key}: {st}"
    assert qa_matrix["pop:light"]["bodyBg"] == "rgb(255, 247, 232)", qa_matrix["pop:light"]
    assert qa_matrix["ink:light"]["bodyBg"] == "rgb(239, 231, 214)", qa_matrix["ink:light"]

    # SPA navigate inside Flarum (`m.route.set` / clicking a discussion link) and verify buttons persist
    call("Runtime.evaluate", expression=r"""
    (() => {
      const link = document.querySelector('.DiscussionListItem-main');
      if (link) link.click();
    })()
    """)
    time.sleep(2.0)
    qa_spa = call("Runtime.evaluate", expression=r"""
    ({
      path: location.pathname,
      skinBtns: document.querySelectorAll('#rx-skin-toggle').length,
      themeBtns: document.querySelectorAll('#rx-theme-toggle').length,
      sw: document.documentElement.scrollWidth,
      iw: window.innerWidth
    })
    """, returnByValue=True)["result"]["value"]
    print(f"  Flarum SPA Discussion Nav     : path={qa_spa['path']} | skinBtns={qa_spa['skinBtns']} | themeBtns={qa_spa['themeBtns']} | {qa_spa['sw']}<={qa_spa['iw']}")
    assert qa_spa["skinBtns"] == 1 and qa_spa["themeBtns"] == 1, qa_spa
    assert qa_spa["sw"] <= qa_spa["iw"]

    # Flarum 390px mobile zero-overflow check across all 4 skins
    call("Page.navigate", url=f"{QA_BASE}/d/{guide_id}?_mob={int(time.time())}")
    time.sleep(2.5)
    call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
    time.sleep(0.6)
    qa_mob = json.loads(call("Runtime.evaluate", expression=r"""
    (() => {
      const out = {};
      for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
        document.documentElement.dataset.rxSkin = sk;
        out[sk] = {
          sw: document.documentElement.scrollWidth,
          iw: window.innerWidth,
          hasMobileSkinBtn: !!document.getElementById('rx-skin-toggle-m')
        };
      }
      return JSON.stringify(out);
    })()
    """, returnByValue=True)["result"]["value"])
    for sk, dims in qa_mob.items():
        assert dims["hasMobileSkinBtn"] is True, f"Missing #rx-skin-toggle-m on Flarum mobile: {dims}"
        assert dims["sw"] <= dims["iw"], f"Flarum 390px overflow in {sk}: {dims}"
    print("  Flarum 390px Mobile Matrix    : pop/ink/luxe/plain all <= 390px with mobile skin switcher")

    # Admin isolation check (/console on Halo & /admin on Flarum) while rx_skin=ink cookie is set
    call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
    for admin_url in (f"{BASE}/console", f"{QA_BASE}/admin"):
        call("Page.navigate", url=admin_url)
        time.sleep(2.0)
        adm = call("Runtime.evaluate", expression=r"""
        ({
          url: location.href,
          rxSkin: document.documentElement.dataset.rxSkin || null,
          btnCount: document.querySelectorAll('#rx-skin-toggle').length
        })
        """, returnByValue=True)["result"]["value"]
        print(f"  Admin Isolation Check         : {admin_url} -> rxSkin={adm['rxSkin']} | btnCount={adm['btnCount']}")
        assert adm["rxSkin"] is None, f"Admin route leaked data-rx-skin: {adm}"
        assert adm["btnCount"] == 0, f"Admin route leaked #rx-skin-toggle: {adm}"

    # Reset cookies to clean default ('pop' + 'light') for subsequent checks
    call("Network.clearBrowserCookies")


def main():
    for u in PAGE_URLS + POST_URLS:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
        status, b, hdrs = http_fetch(req, timeout=20)
        print(f"[HTTP {status}] {len(b):9,d} bytes | {u}")
        assert status == 200
        assert hdrs.get("X-Content-Type-Options") == "nosniff", f"Missing nosniff on {u}: {hdrs}"
        if "/upload/" in u:
            assert "max-age=604800" in hdrs.get("Cache-Control", ""), f"Missing immutable cache on {u}: {hdrs}"

    check_rx_skins_static_endpoints()
    check_halo_nickname_search()
    guide_id = check_flarum_vps_guide()

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

        check_dual_site_cc_skins(call, guide_id)

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
          document.documentElement.classList.remove('dark', 'rx-dark');
          const box = document.getElementById('rx-reviews');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark', 'rx-dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark', 'rx-dark');
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
        assert reviews_res["lightCardBg"] != reviews_res["darkCardBg"]
        assert _rgb_luminance(reviews_res["lightCardBg"]) > 0.75 and _rgb_luminance(reviews_res["darkCardBg"]) < 0.12
        assert reviews_res["hasCheckPlace"] is True
        assert reviews_res["sw"] <= reviews_res["iw"] and reviews_mob["sw"] <= reviews_mob["iw"]

        # 2. Audit /tools Interactive SinglePage
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/tools?_t={int(time.time())}")
        time.sleep(2.5)
        tools_js = r"""
        (() => {
          document.documentElement.classList.remove('dark', 'rx-dark');
          const box = document.getElementById('rx-toolbox');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark', 'rx-dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark', 'rx-dark');
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
        assert tools_res["lightCardBg"] != tools_res["darkCardBg"]
        assert _rgb_luminance(tools_res["lightCardBg"]) > 0.75 and _rgb_luminance(tools_res["darkCardBg"]) < 0.12
        assert "剩余天数" in tools_res["vpsTxt"] and "6S1P" in tools_res["batTxt"]
        assert tools_res["blurredPres"] == 0
        assert tools_res["sw"] <= tools_res["iw"] and tools_mob["sw"] <= tools_mob["iw"]

        # 2a. Audit /about SinglePage (Zero Default Placeholder Meta Description + Light/Dark Cards)
        call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
        call("Page.navigate", url=f"{BASE}/about?_t={int(time.time())}")
        time.sleep(2.0)
        about_js = r"""
        (() => {
          document.documentElement.classList.remove('dark', 'rx-dark');
          const box = document.getElementById('rx-about');
          const card = box ? box.querySelector('.rx-card') : null;
          const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.add('dark', 'rx-dark');
          const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
          document.documentElement.classList.remove('dark', 'rx-dark');
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
        assert about_res["lightCardBg"] != about_res["darkCardBg"]
        assert _rgb_luminance(about_res["lightCardBg"]) > 0.75 and _rgb_luminance(about_res["darkCardBg"]) < 0.12
        assert about_res["sw"] <= about_res["iw"] and about_mob["sw"] <= about_mob["iw"]

        # 2b. Audit /privacy-policy & /user-agreement Legal SinglePages
        for slug in ["privacy-policy", "user-agreement"]:
            call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            call("Page.navigate", url=f"{BASE}/{slug}?_t={int(time.time())}")
            time.sleep(2.0)
            legal_js = r"""
            (() => {
              document.documentElement.classList.remove('dark', 'rx-dark');
              const box = document.querySelector('.rx-legal');
              const card = box ? box.querySelector('.rx-legal-meta') : null;
              const lightCardBg = card ? getComputedStyle(card).backgroundColor : '';
              document.documentElement.classList.add('dark', 'rx-dark');
              const darkCardBg = card ? getComputedStyle(card).backgroundColor : '';
              document.documentElement.classList.remove('dark', 'rx-dark');
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
            assert legal_res["lightCardBg"] != legal_res["darkCardBg"]
            assert _rgb_luminance(legal_res["lightCardBg"]) > 0.75 and _rgb_luminance(legal_res["darkCardBg"]) < 0.12
            assert legal_res["sw"] <= legal_res["iw"] and legal_mob["sw"] <= legal_mob["iw"]

        # 3. Audit All 6 VPS Posts + Vendor Wall + Slang Filter + Zero Blurred Pre Blocks + Light/Dark Styles
        JS_POST_AUDIT = r"""
        (() => {
          document.documentElement.classList.remove('dark', 'rx-dark');
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

          detailsAll.slice(0, 5).forEach(d => { d.open = true; });
          const visibleBlurredPres = Array.from(md.querySelectorAll('pre')).filter(p => {
            const cs = getComputedStyle(p);
            return cs.display !== 'none' && cs.filter && cs.filter.includes('blur');
          }).length;
          const rawPre = md.querySelector('pre.vps-raw-report');
          const rawPreLightBg = rawPre ? getComputedStyle(rawPre).backgroundColor : '';
          document.documentElement.classList.add('dark', 'rx-dark');
          const rawPreDarkBg = rawPre ? getComputedStyle(rawPre).backgroundColor : '';
          document.documentElement.classList.remove('dark', 'rx-dark');
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

            document.documentElement.classList.add('dark', 'rx-dark');
            const darkBg = getComputedStyle(tb).backgroundColor;
            const darkInputBg = getComputedStyle(input).backgroundColor;
            const darkChipBg = activeChip ? getComputedStyle(activeChip).backgroundColor : '';
            const subHead = md.querySelector('.vps-review-subheading');
            const darkSubHeadColor = subHead ? getComputedStyle(subHead).color : '';
            document.documentElement.classList.remove('dark', 'rx-dark');
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
                assert _rgb_luminance(res["rawPreLightBg"]) < 0.12, res["rawPreLightBg"]
                assert _rgb_luminance(res["rawPreDarkBg"]) < 0.12, res["rawPreDarkBg"]
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
                assert tc["lightBg"] != tc["darkBg"], tc
                assert _rgb_luminance(tc["lightBg"]) > 0.75 and _rgb_luminance(tc["darkBg"]) < 0.12, tc
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
        print("\nALL HOMEPAGE PINNING, FAVICON, COVERS, LEGAL PAGES, VENDOR WALL, NICKNAME SEARCH, FLARUM GUIDE, CC 4-SKINS DUAL-SITE, CROSS-COOKIE SYNC, ZERO-BLUR PRE & MOBILE CHECKS PASSED 100%!")
    finally:
        chrome_proc.terminate()
        shutil.rmtree(tmp_prof, ignore_errors=True)


if __name__ == "__main__":
    main()
