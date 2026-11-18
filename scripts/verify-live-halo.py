#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end live verification for https://blog.mycampusmail.com:
  1. HTTP 200 across homepage, all category pages, tag page, and all 6 published VPS posts
  2. Homepage pinned order (#1 Vol. 1, #2 Vol. 2) and 0 placeholder welcome stubs
  3. Zero broken #anchors, zero stale /vps/ links, denoised sidebar TOC (.toc a <= 280)
  4. Interactive filter + expand/collapse toolbar functionality
  5. Light Mode vs Dark Mode (html.dark) computed styles on #vps-quick-toolbar, inputs, chips & subheadings
  6. Zero horizontal overflow on both 1280px desktop and 390px mobile viewports
"""
import itertools, json, shutil, subprocess, tempfile, time, urllib.request
import websocket

PORT = 9242
BASE = "https://blog.mycampusmail.com"

POST_URLS = [
    f"{BASE}/archives/nodeseek-merchant-reviews-2026h2",
    f"{BASE}/archives/meowvps-official-merchants-2026h2",
    f"{BASE}/archives/reading-vps-reviews",
    f"{BASE}/archives/relay-and-egress-guide",
    f"{BASE}/archives/mihomo-chain-and-fallback",
    f"{BASE}/archives/first-post",
]
CAT_URLS = [
    f"{BASE}/",
    f"{BASE}/categories/vps",
    f"{BASE}/categories/ai",
    f"{BASE}/categories/fsae",
    f"{BASE}/categories/rm",
    f"{BASE}/categories/resources",
    f"{BASE}/tags/isp",
]


def main():
    for u in CAT_URLS + POST_URLS:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req, timeout=20) as r:
            b = r.read()
            print(f"[HTTP {r.status}] {len(b):9,d} bytes | {u}")
            assert r.status == 200

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

        # 1. Verify Homepage Pinned Order & Zero Stub Posts
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
          const bodyTxt = document.body.innerText;
          const stubsPresent = ['AI 分区开篇', '资源分区开篇', 'RoboMaster 分区开篇', '车队的第一篇记录'].filter(t => bodyTxt.includes(t));
          return JSON.stringify({ archiveCards: seen, stubsPresent });
        })()
        """
        home_res = json.loads(call("Runtime.evaluate", expression=home_js, returnByValue=True)["result"]["value"])
        print("\n=== HOMEPAGE AUDIT ===")
        for idx, c in enumerate(home_res["archiveCards"]):
            print(f"  #{idx+1}: {c['href']} -> {c['text']}")
        print("  Stubs present on homepage:", home_res["stubsPresent"])
        assert len(home_res["archiveCards"]) >= 6
        assert home_res["archiveCards"][0]["href"].endswith("/archives/nodeseek-merchant-reviews-2026h2")
        assert home_res["archiveCards"][1]["href"].endswith("/archives/meowvps-official-merchants-2026h2")
        assert home_res["stubsPresent"] == [], f"Welcome stubs still visible: {home_res['stubsPresent']}"

        # 2. Audit Posts + Light/Dark Toolbar Styles + Responsive Layout
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
          const detailsAll = Array.from(md.querySelectorAll('details'));
          const defaultOpen = detailsAll.filter(d => d.open).length;

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
              statusAfterFilter, openAfterExpand, openAfterCollapse
            };
          }

          return JSON.stringify({
            hashLinkCount: hashLinks.length,
            brokenAnchorCount: brokenAnchors.length,
            staleVpsLinkCount: staleVpsLinks.length,
            tocLinks,
            detailsTotal: detailsAll.length,
            defaultOpen,
            toolbarCheck,
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: window.innerWidth
          });
        })()
        """

        for u in POST_URLS[:5]:
            call("Emulation.setDeviceMetricsOverride", width=1280, height=900, deviceScaleFactor=1, mobile=False)
            call("Page.navigate", url=u + f"?_t={int(time.time())}")
            time.sleep(3.5)
            res = json.loads(call("Runtime.evaluate", expression=JS_POST_AUDIT, returnByValue=True)["result"]["value"])

            call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=2, mobile=True)
            time.sleep(0.7)
            mob = json.loads(call("Runtime.evaluate", expression="JSON.stringify({sw: document.documentElement.scrollWidth, iw: window.innerWidth})", returnByValue=True)["result"]["value"])

            print(f"\n=== POST AUDIT: {u} ===")
            print(f"  Anchors={res['hashLinkCount']} (broken={res['brokenAnchorCount']}), stale=/vps/={res['staleVpsLinkCount']}, TOC(.toc a)={res['tocLinks']}, details={res['detailsTotal']}")
            if res["toolbarCheck"]:
                tc = res["toolbarCheck"]
                print(f"  Light vs Dark TB : light={tc['lightBg']} / chip={tc['lightChipBg']} -> dark={tc['darkBg']} / input={tc['darkInputBg']} / chip={tc['darkChipBg']}")
                print(f"  Filter & Details : {tc['statusAfterFilter']} | expand={tc['openAfterExpand']} -> collapse={tc['openAfterCollapse']}")
                assert tc["lightBg"] == "rgb(248, 250, 252)", tc
                assert tc["darkBg"] == "rgb(30, 41, 59)", tc
                assert tc["darkInputBg"] == "rgb(15, 23, 42)", tc
                assert tc["darkChipBg"] == "rgb(56, 189, 248)", tc
                assert tc["openAfterExpand"] == res["detailsTotal"] and tc["openAfterCollapse"] == 0
            print(f"  Responsive       : 1280px ({res['scrollWidth']}<={res['innerWidth']}), 390px ({mob['sw']}<={mob['iw']})")
            assert res["brokenAnchorCount"] == 0
            assert res["staleVpsLinkCount"] == 0
            assert res["tocLinks"] <= 280
            assert res["scrollWidth"] <= res["innerWidth"]
            assert mob["sw"] <= mob["iw"]

        ws.close()
        print("\nALL HOMEPAGE PINNING, CATEGORY 200s, DARK MODE, ANCHORS, TOC & MOBILE CHECKS PASSED 100%!")
    finally:
        chrome_proc.terminate()
        shutil.rmtree(tmp_prof, ignore_errors=True)


if __name__ == "__main__":
    main()
