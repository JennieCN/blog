#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless Chrome unit & DOM integration tests for scripts/rx-skins/."""
import http.server
import itertools
import json
import os
import re
import shutil
import socket
import socketserver
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path

import websocket

REPO_ROOT = Path(__file__).resolve().parents[2]
SKINS_DIR = REPO_ROOT / "scripts" / "rx-skins"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _rgb_luminance(rgb_str: str) -> float:
    nums = [int(x) for x in re.findall(r"\d+", rgb_str)[:3]]
    if len(nums) < 3:
        return 0.0
    vals = []
    for c in nums:
        v = c / 255.0
        vals.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


class _SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class ChromeHarnessMixin:
    @classmethod
    def setUpClass(cls):
        cls.serve_dir = Path(tempfile.mkdtemp(prefix="rx-skins-srv-"))
        cls.http_port = _free_port()
        cls.cdp_port = _free_port()

        handler = lambda *a, **kw: _SilentHandler(*a, directory=str(cls.serve_dir), **kw)
        socketserver.TCPServer.allow_reuse_address = True
        cls.httpd = socketserver.TCPServer(("127.0.0.1", cls.http_port), handler)
        cls.http_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.http_thread.start()

        cls.profile_dir = tempfile.mkdtemp(prefix="rx-skins-cdp-")
        cls.chrome_proc = subprocess.Popen(
            [
                CHROME_BIN,
                f"--remote-debugging-port={cls.cdp_port}",
                f"--user-data-dir={cls.profile_dir}",
                "--no-first-run",
                "--no-default-browser-check",
                "--headless=new",
                "about:blank",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(25):
            time.sleep(0.3)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{cls.cdp_port}/json/version", timeout=1)
                break
            except Exception:
                pass
        else:
            raise RuntimeError("Headless Chrome failed to start")

        tabs = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{cls.cdp_port}/json/list").read().decode())
        ws_url = [t["webSocketDebuggerUrl"] for t in tabs if t.get("type") == "page"][0]
        cls.ws = websocket.create_connection(ws_url, timeout=20, suppress_origin=True)
        cls._id = itertools.count(1)
        cls.cdp("Page.enable")
        cls.cdp("Network.enable")
        cls.cdp("Network.setCacheDisabled", cacheDisabled=True)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.ws.close()
        except Exception:
            pass
        cls.chrome_proc.terminate()
        try:
            cls.chrome_proc.wait(timeout=5)
        except Exception:
            cls.chrome_proc.kill()
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.serve_dir, ignore_errors=True)
        shutil.rmtree(cls.profile_dir, ignore_errors=True)

    @classmethod
    def cdp(cls, method: str, **params):
        i = next(cls._id)
        cls.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        while True:
            msg = json.loads(cls.ws.recv())
            if msg.get("id") == i:
                if "error" in msg:
                    raise RuntimeError(f"CDP error on {method}: {msg['error']}")
                return msg.get("result", {})

    def sync_skin_files(self):
        target = self.serve_dir / "rx-skins"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(SKINS_DIR, target)

    def eval_js(self, expr: str):
        res = self.cdp("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in res:
            raise AssertionError(f"JS exception: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")

    def open_fixture(self, name: str, html: str, width: int = 1280, height: int = 900, clear_storage: bool = True):
        self.sync_skin_files()
        out = self.serve_dir / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html, encoding="utf-8")
        self.cdp("Emulation.setDeviceMetricsOverride", width=width, height=height, deviceScaleFactor=1, mobile=width < 640)
        if clear_storage:
            self.cdp("Network.clearBrowserCookies")
        self.cdp("Page.navigate", url=f"http://127.0.0.1:{self.http_port}/{name}?_={time.time_ns()}")
        time.sleep(0.35)


class TestRxSkinsCore(ChromeHarnessMixin, unittest.TestCase):
    def test_svg_assets_and_token_selectors(self):
        for svg_name in ("ink-landscape.svg", "ink-mountains.svg", "ink-stroke.svg"):
            p = SKINS_DIR / svg_name
            self.assertTrue(p.is_file(), f"Missing SVG asset: {p}")
            txt = p.read_text(encoding="utf-8")
            self.assertIn("<svg", txt)

        tokens_path = SKINS_DIR / "rx-tokens.css"
        self.assertTrue(tokens_path.is_file(), "Missing rx-tokens.css")
        boot = (SKINS_DIR / "bootstrap-snippet.js").read_text(encoding="utf-8")
        html = f"""<!doctype html><html><head>
        <meta charset="utf-8"><script>{boot}</script>
        <link rel="stylesheet" href="/rx-skins/rx-tokens.css">
        <script defer src="/rx-skins/rx-switcher.js"></script>
        </head><body><header id="header-menu"><div class="mx-auto"><div class="flex"><ul class="sm:flex"></ul></div></div></header></body></html>"""
        self.open_fixture("core-tokens.html", html)

        data = self.eval_js("""
        (() => {
          const out = {};
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            for (const dk of [false, true]) {
              document.documentElement.dataset.rxSkin = sk;
              document.documentElement.classList.toggle('rx-dark', dk);
              const cs = getComputedStyle(document.documentElement);
              out[sk + ':' + (dk ? 'dark' : 'light')] = {
                bg: cs.getPropertyValue('--rx-bg').trim(),
                surface: cs.getPropertyValue('--rx-surface').trim(),
                text: cs.getPropertyValue('--rx-text').trim(),
                accent: cs.getPropertyValue('--rx-accent').trim(),
              };
            }
          }
          return out;
        })()
        """)
        for key, vals in data.items():
            for prop, v in vals.items():
                self.assertTrue(v, f"Empty token {prop} for {key}")
        self.assertNotEqual(data["pop:light"]["bg"], data["ink:light"]["bg"])
        self.assertNotEqual(data["ink:light"]["bg"], data["luxe:light"]["bg"])
        self.assertNotEqual(data["luxe:light"]["bg"], data["plain:light"]["bg"])
        self.assertNotEqual(data["pop:light"]["bg"], data["pop:dark"]["bg"])

    def test_corrupted_cookie_fallback_and_cycle(self):
        boot = (SKINS_DIR / "bootstrap-snippet.js").read_text(encoding="utf-8")
        html = f"""<!doctype html><html><head><meta charset="utf-8">
        <script>document.cookie = 'rx_skin=bogus; path=/'; localStorage.setItem('rx_skin', 'invalid_skin');</script>
        <script>{boot}</script>
        <link rel="stylesheet" href="/rx-skins/rx-tokens.css">
        <script defer src="/rx-skins/rx-switcher.js"></script>
        </head><body>
        <header id="header-menu"><div class="mx-auto flex justify-between"><div class="flex"></div><div class="flex items-center gap-4"><ul class="flex items-center gap-4"><li class="search-slot"><a href="#">S</a></li></ul></div></div></header>
        </body></html>"""
        self.open_fixture("core-cycle.html", html)

        res = self.eval_js("""
        (async () => {
          const initial = document.documentElement.dataset.rxSkin;
          const btn = document.getElementById('rx-skin-toggle');
          if (!btn) return { error: 'missing #rx-skin-toggle' };
          const seq = [initial];
          let firstToast = '';
          for (let i = 0; i < 4; i++) {
            btn.click();
            await new Promise(r => setTimeout(r, 50));
            seq.push(document.documentElement.dataset.rxSkin);
            if (i === 0) {
              const t = document.getElementById('rx-toast');
              firstToast = t ? t.textContent : '';
            }
          }
          const burst = [window.RXSkins.getSkin()];
          for (let j = 0; j < 4; j++) {
            btn.click();
            burst.push(window.RXSkins.getSkin());
          }
          await new Promise(r => setTimeout(r, 50));
          return { seq, burst, finalDom: document.documentElement.dataset.rxSkin, firstToast };
        })()
        """)
        self.assertEqual(res.get("seq"), ["pop", "ink", "luxe", "plain", "pop"])
        self.assertEqual(res.get("burst"), ["pop", "ink", "luxe", "plain", "pop"])
        self.assertEqual(res.get("finalDom"), "pop")
        self.assertIn("已切换至「水墨」风格", res.get("firstToast", ""))

    def test_admin_path_exclusion(self):
        boot = (SKINS_DIR / "bootstrap-snippet.js").read_text(encoding="utf-8")
        for admin_path in ("/console/dashboard", "/uc/profile", "/admin"):
            html = f"""<!doctype html><html><head><meta charset="utf-8">
            <script>
              localStorage.setItem('rx_skin', 'ink');
              document.cookie = 'rx_skin=ink; path=/';
              window.__RX_TEST_PATH = {json.dumps(admin_path)};
            </script>
            <script>{boot}</script>
            <script defer src="/rx-skins/rx-switcher.js"></script>
            </head><body><header id="header-menu"><ul class="flex"><li>A</li></ul></header></body></html>"""
            self.open_fixture("core-admin.html", html, clear_storage=False)
            state = self.eval_js("""
            ({
              skin: document.documentElement.dataset.rxSkin || null,
              btnCount: document.querySelectorAll('#rx-skin-toggle').length
            })
            """)
            self.assertIsNone(state["skin"], f"Admin route {admin_path} should not set data-rx-skin")
            self.assertEqual(state["btnCount"], 0, f"Admin route {admin_path} should mount 0 skin buttons")

    def test_halo_native_dark_mutation_sync(self):
        boot = (SKINS_DIR / "bootstrap-snippet.js").read_text(encoding="utf-8")
        html = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
        <script>{boot}</script>
        <link rel="stylesheet" href="/rx-skins/rx-tokens.css">
        <script defer src="/rx-skins/rx-switcher.js"></script>
        </head><body><header id="header-menu"><ul class="flex"><li>A</li></ul></header></body></html>"""
        self.open_fixture("core-halo-dark.html", html)
        synced = self.eval_js("""
        new Promise((resolve) => {
          document.documentElement.classList.remove('dark', 'rx-dark');
          setTimeout(() => {
            document.documentElement.classList.add('dark');
            setTimeout(() => {
              resolve({
                rxDarkAfterAdd: document.documentElement.classList.contains('rx-dark'),
                cookieAfterAdd: document.cookie
              });
            }, 60);
          }, 30);
        })
        """)
        self.assertTrue(synced["rxDarkAfterAdd"])
        self.assertIn("rx_theme=dark", synced["cookieAfterAdd"])

    def test_flarum_spa_header_remount_idempotent(self):
        boot = (SKINS_DIR / "bootstrap-snippet.js").read_text(encoding="utf-8")
        html = f"""<!doctype html><html data-theme="light"><head><meta charset="utf-8">
        <script>{boot}</script>
        <link rel="stylesheet" href="/rx-skins/rx-tokens.css">
        <script defer src="/rx-skins/rx-switcher.js"></script>
        </head><body>
        <header class="App-header"><div class="Header-secondary"><ul class="Header-controls"><li class="item-search">Search</li></ul></div></header>
        </body></html>"""
        self.open_fixture("core-flarum-spa.html", html)
        remount = self.eval_js("""
        new Promise((resolve) => {
          const ul = document.querySelector('.Header-controls');
          const beforeSkin = document.querySelectorAll('#rx-skin-toggle').length;
          const beforeTheme = document.querySelectorAll('#rx-theme-toggle').length;
          ul.innerHTML = '<li class="item-search">Search Redrawn</li><li class="item-logIn">Log In</li>';
          setTimeout(() => {
            window.RXSkins.mountButtons();
            resolve({
              beforeSkin,
              beforeTheme,
              afterSkin: document.querySelectorAll('#rx-skin-toggle').length,
              afterTheme: document.querySelectorAll('#rx-theme-toggle').length,
            });
          }, 80);
        })
        """)
        self.assertEqual(remount["beforeSkin"], 1)
        self.assertEqual(remount["beforeTheme"], 1)
        self.assertEqual(remount["afterSkin"], 1)
        self.assertEqual(remount["afterTheme"], 1)


HALO_FIXTURE_BODY = """
<header id="header-menu" class="sticky top-0 z-10 flex h-16 bg-white py-3 shadow-sm dark:bg-gray-800" style="display:flex;justify-content:space-between;align-items:center;padding:0 16px">
  <div style="display:flex;align-items:center;gap:12px">
    <a href="/"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Logo" style="width:28px;height:28px"></a>
    <ul style="display:flex;gap:12px;list-style:none;margin:0;padding:0"><li><a href="/">首页</a></li></ul>
  </div>
  <div>
    <ul style="display:flex;gap:8px;list-style:none;margin:0;padding:0;align-items:center">
      <li><a href="#">Search</a></li>
    </ul>
  </div>
  <nav style="display:none"><ul><li><a href="/">首页</a></li></ul></nav>
</header>
<section class="rx-hero-wrap">
  <div class="bg-cover bg-center bg-no-repeat h-96" style="height:240px;display:flex;align-items:center;justify-content:center">
    <div style="display:flex;flex-direction:column;align-items:center;gap:8px">
      <span class="text-5xl" style="color:#ffffff">融夕的书</span>
      <span class="text-sm font-light" style="color:#ffffff">VPS、赛车、机器人、AI 与资源笔记</span>
    </div>
  </div>
</section>
<section style="max-width:1200px;margin:16px auto;padding:0 12px">
  <ul id="filters" style="display:flex;gap:8px;list-style:none;padding:0"><li><a href="/" class="rounded px-3">全部</a></li></ul>
  <article id="sample-card" class="group flex flex-col overflow-hidden rounded-xl bg-white shadow-md dark:bg-slate-800" style="padding:16px;margin-top:12px">
    <h2><a href="/archives/test">117 家 VPS 测评归档</a></h2>
    <p>路线与网络质量汇总</p>
  </article>
  <div class="rounded-xl bg-white p-4 dark:bg-slate-800" style="margin-top:16px">
    <article id="post-content" class="markdown-body">
      <h2>水墨与贴纸二级标题</h2>
      <blockquote>这是一段引用说明</blockquote>
      <div class="vps-summary-panel">摘要面板</div>
      <div id="vps-vendor-wall"><a class="vps-vendor-pill" href="#v1">DMIT</a></div>
      <pre class="vps-raw-report">========== NodeQuality Benchmark Raw Output ==========
ASN: AS54574 | Route: CN2 GIA | Loss: 0.0%</pre>
      <div class="rx-legal-meta">隐私条款摘要卡片</div>
    </article>
  </div>
</section>
<footer class="mt-10 bg-white py-8 dark:bg-slate-800" style="padding:16px">Footer</footer>
"""


class TestRxHaloAdapter(ChromeHarnessMixin, unittest.TestCase):
    def _load_halo(self, width: int = 1280):
        head_path = SKINS_DIR / "halo-global-head.html"
        self.assertTrue(head_path.is_file(), f"Missing {head_path}")
        self.assertTrue((SKINS_DIR / "rx-halo.css").is_file(), "Missing rx-halo.css")
        head_html = re.sub(r"\?v=[^\"']+", "", head_path.read_text(encoding="utf-8"))
        doc = f"<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>{head_html}</head><body style='margin:0'>{HALO_FIXTURE_BODY}</body></html>"
        self.open_fixture("halo-fixture.html", doc, width=width)

    def test_halo_four_skins_distinct_backgrounds_and_cards(self):
        self._load_halo(1280)
        snaps = self.eval_js("""
        (() => {
          const out = {};
          const card = document.getElementById('sample-card');
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            window.RXSkins.setSkin(sk);
            document.documentElement.dataset.rxSkin = sk;
            const bcs = getComputedStyle(document.body);
            const ccs = getComputedStyle(card);
            out[sk] = {
              bodyBg: bcs.backgroundColor,
              cardRadius: parseFloat(ccs.borderTopLeftRadius || '0'),
              cardBorderW: parseFloat(ccs.borderTopWidth || '0'),
              cardShadow: ccs.boxShadow,
              cardFilter: ccs.backdropFilter || ccs.webkitBackdropFilter || 'none'
            };
          }
          return out;
        })()
        """)
        self.assertEqual(snaps["pop"]["bodyBg"], "rgb(255, 247, 232)")
        self.assertGreaterEqual(snaps["pop"]["cardBorderW"], 2.0)
        self.assertNotEqual(snaps["pop"]["cardShadow"], "none")

        self.assertEqual(snaps["ink"]["bodyBg"], "rgb(239, 231, 214)")
        self.assertLessEqual(snaps["ink"]["cardRadius"], 4.0)

        self.assertEqual(snaps["luxe"]["bodyBg"], "rgb(246, 241, 233)")
        self.assertIn("blur", snaps["luxe"]["cardFilter"])

        self.assertEqual(snaps["plain"]["bodyBg"], "rgb(255, 255, 255)")
        self.assertEqual(snaps["plain"]["cardBorderW"], 1.0)

    def test_halo_raw_report_never_blurred_and_high_contrast_in_plain(self):
        self._load_halo(1280)
        matrix = self.eval_js("""
        (() => {
          const pre = document.querySelector('pre.vps-raw-report');
          const out = {};
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            for (const dk of [false, true]) {
              document.documentElement.dataset.rxSkin = sk;
              document.documentElement.classList.toggle('rx-dark', dk);
              document.documentElement.classList.toggle('dark', dk);
              const cs = getComputedStyle(pre);
              out[sk + ':' + (dk ? 'dark' : 'light')] = {
                filter: cs.filter,
                bg: cs.backgroundColor,
                fg: cs.color
              };
            }
          }
          return out;
        })()
        """)
        for key, st in matrix.items():
            self.assertEqual(st["filter"], "none", f"pre.vps-raw-report blurred in {key}: {st}")
            bg_lum = _rgb_luminance(st["bg"])
            fg_lum = _rgb_luminance(st["fg"])
            self.assertLess(bg_lum, 0.12, f"Expected dark code bg in {key}, got {st['bg']} (lum={bg_lum:.3f})")
            self.assertGreater(fg_lum, 0.65, f"Expected bright code fg in {key}, got {st['fg']} (lum={fg_lum:.3f})")

    def test_halo_mobile_390px_zero_overflow(self):
        self._load_halo(390)
        overflow = self.eval_js("""
        (() => {
          const res = {};
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            document.documentElement.dataset.rxSkin = sk;
            res[sk] = {
              scrollW: document.documentElement.scrollWidth,
              innerW: window.innerWidth,
              hasBtn: !!document.getElementById('rx-skin-toggle')
            };
          }
          return res;
        })()
        """)
        for sk, info in overflow.items():
            self.assertTrue(info["hasBtn"], f"Missing #rx-skin-toggle on 390px in {sk}")
            self.assertLessEqual(info["scrollW"], info["innerW"], f"Horizontal overflow on Halo 390px in {sk}: {info}")


FLARUM_NATIVE_STYLE = """
:root, [data-theme^=light] {
  --primary-color: #4d698e;
  --secondary-color: #4d698e;
  --body-bg: #ffffff;
  --text-color: #111111;
  --header-bg: #ffffff;
  --header-color: #4d698e;
  --button-primary-bg: #4d698e;
  --button-primary-color: #ffffff;
  --hero-bg: #e8ecf3;
  --hero-color: #4d698e;
}
[data-theme^=dark] {
  --primary-color: #4d698e;
  --body-bg: #1b2028;
  --text-color: #dddddd;
  --header-bg: #14191f;
  --button-primary-bg: #4d698e;
}
body { margin: 0; background: var(--body-bg); color: var(--text-color); }
.App-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 14px; background: var(--header-bg); box-sizing: border-box; }
.Header-controls { display: flex; align-items: center; gap: 6px; list-style: none; margin: 0; padding: 0; }
.Button--primary { background: var(--button-primary-bg); color: var(--button-primary-color); border: 0; padding: 6px 12px; }
"""

FLARUM_APP_BODY = """
<div id="app" class="App">
  <header class="App-header">
    <div class="Header-primary"><a class="Header-title" href="/">融夕问答社区</a></div>
    <div class="Header-secondary">
      <ul class="Header-controls">
        <li class="item-search"><button class="Button" type="button">搜索</button></li>
        <li class="item-logIn"><button class="Button" type="button">登录</button></li>
      </ul>
    </div>
  </header>
  <main class="App-content">
    <header class="Hero WelcomeHero">
      <div class="container">
        <h1 class="Hero-title">融夕问答社区</h1>
        <div class="Hero-subtitle">VPS 线路实测、赛车电控、机器人与 AI 交流</div>
      </div>
    </header>
    <div class="container" style="max-width:1150px;margin:16px auto;padding:0 12px;box-sizing:border-box">
      <nav class="IndexPage-nav sideNav">
        <ul><li class="item-newDiscussion"><button class="Button Button--primary" type="button">发布主题</button></li></ul>
      </nav>
      <div class="DiscussionList">
        <ul class="DiscussionList-discussions" style="list-style:none;padding:0;margin:12px 0">
          <li class="DiscussionListItem DiscussionListItem--sticky" style="padding:12px">
            <a class="DiscussionListItem-main" href="/d/1"><h2 class="DiscussionListItem-title">【置顶】117 家 VPS 测评索引</h2></a>
            <span class="TagLabel">VPS 交流</span>
          </li>
          <li class="DiscussionListItem" style="padding:12px;margin-top:8px">
            <a class="DiscussionListItem-main" href="/d/2"><h2 class="DiscussionListItem-title">CN2 GIA 晚高峰延迟对比</h2></a>
          </li>
        </ul>
      </div>
      <article class="CommentPost Post" style="padding:16px">
        <div class="Post-body"><p>社区讨论正文段落</p><pre><code>ping -c 4 1.1.1.1</code></pre></div>
      </article>
    </div>
  </main>
</div>
"""


class TestRxFlarumAdapter(ChromeHarnessMixin, unittest.TestCase):
    def _load_flarum(self, width: int = 1280):
        header_path = SKINS_DIR / "flarum-custom-header.html"
        self.assertTrue(header_path.is_file(), f"Missing {header_path}")
        self.assertTrue((SKINS_DIR / "rx-flarum.css").is_file(), "Missing rx-flarum.css")
        custom_header = re.sub(r"\?v=[^\"']+", "", header_path.read_text(encoding="utf-8"))
        doc = (
            "<!doctype html><html lang='zh-CN' data-theme='light'><head>"
            "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<style>{FLARUM_NATIVE_STYLE}</style></head><body>{custom_header}{FLARUM_APP_BODY}</body></html>"
        )
        self.open_fixture("flarum-fixture.html", doc, width=width)

    def test_flarum_four_skins_override_cold_blue_and_style_crossbar(self):
        self._load_flarum(1280)
        snaps = self.eval_js("""
        (() => {
          const out = {};
          const btn = document.querySelector('.Button--primary');
          const cross = document.querySelector('.rx-qa-crossbar');
          const strip = document.querySelector('.rx-qa-strip');
          if (!cross || !strip) return { error: 'missing .rx-qa-crossbar or .rx-qa-strip' };
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            for (const dk of [false, true]) {
              document.documentElement.dataset.rxSkin = sk;
              document.documentElement.classList.toggle('rx-dark', dk);
              document.documentElement.setAttribute('data-theme', dk ? 'dark' : 'light');
              const rcs = getComputedStyle(document.documentElement);
              const bcs = getComputedStyle(btn);
              const xcs = getComputedStyle(cross);
              const scs = getComputedStyle(strip);
              out[sk + ':' + (dk ? 'dark' : 'light')] = {
                primaryVar: rcs.getPropertyValue('--primary-color').trim().toLowerCase(),
                btnBg: bcs.backgroundColor,
                crossBg: xcs.backgroundColor,
                stripBg: scs.backgroundColor,
                bodyBg: getComputedStyle(document.body).backgroundColor
              };
            }
          }
          return out;
        })()
        """)
        self.assertNotIn("error", snaps, f"Missing crossbar/strip elements: {snaps}")
        for key, st in snaps.items():
            self.assertNotEqual(st["primaryVar"], "#4d698e", f"--primary-color still cold blue in {key}")
            self.assertNotEqual(st["btnBg"], "rgb(77, 105, 142)", f".Button--primary still cold blue in {key}")
        self.assertNotEqual(snaps["pop:light"]["crossBg"], snaps["ink:light"]["crossBg"])
        self.assertNotEqual(snaps["pop:light"]["stripBg"], snaps["plain:light"]["stripBg"])
        self.assertNotEqual(snaps["pop:light"]["bodyBg"], snaps["pop:dark"]["bodyBg"])

    def test_flarum_preserved_checkin_and_captcha_hooks(self):
        self._load_flarum(1280)
        hooks = self.eval_js("""
        ({
          hasCheckinBtn: !!document.getElementById('rx-checkin-btn'),
          hasPoints: !!document.getElementById('rx-points'),
          hasCaptchaFloat: !!document.getElementById('rx-captcha-float'),
          hasCaptchaInput: !!document.getElementById('rx-captcha-input'),
          hasSendMailBtn: !!document.getElementById('rx-send-mail-code'),
          fnCheckin: typeof window.__rxCheckin,
          fnSendEmail: typeof window.__rxSendEmailCode,
          fnRefresh: typeof window.__rxRefreshCaptcha,
          hasReviewsLink: !!document.querySelector('a[href="https://blog.mycampusmail.com/my-reviews"]'),
          hasToolsLink: !!document.querySelector('a[href="https://blog.mycampusmail.com/tools"]'),
        })
        """)
        self.assertTrue(hooks["hasCheckinBtn"])
        self.assertTrue(hooks["hasPoints"])
        self.assertTrue(hooks["hasCaptchaFloat"])
        self.assertTrue(hooks["hasCaptchaInput"])
        self.assertTrue(hooks["hasSendMailBtn"])
        self.assertEqual(hooks["fnCheckin"], "function")
        self.assertEqual(hooks["fnSendEmail"], "function")
        self.assertEqual(hooks["fnRefresh"], "function")
        self.assertTrue(hooks["hasReviewsLink"])
        self.assertTrue(hooks["hasToolsLink"])

    def test_flarum_mobile_390px_zero_overflow(self):
        self._load_flarum(390)
        overflow = self.eval_js("""
        (() => {
          const res = {};
          for (const sk of ['pop', 'ink', 'luxe', 'plain']) {
            document.documentElement.dataset.rxSkin = sk;
            const sb = document.getElementById('rx-skin-toggle');
            const tb = document.getElementById('rx-theme-toggle');
            res[sk] = {
              scrollW: document.documentElement.scrollWidth,
              innerW: window.innerWidth,
              hasSkinBtn: !!sb,
              hasThemeBtn: !!tb,
              skinRight: sb ? sb.getBoundingClientRect().right : 9999,
              themeRight: tb ? tb.getBoundingClientRect().right : 9999,
            };
          }
          return res;
        })()
        """)
        for sk, info in overflow.items():
            self.assertTrue(info["hasSkinBtn"], f"Missing #rx-skin-toggle on Flarum 390px in {sk}")
            self.assertTrue(info["hasThemeBtn"], f"Missing #rx-theme-toggle on Flarum 390px in {sk}")
            self.assertLessEqual(info["scrollW"], info["innerW"], f"Horizontal overflow on Flarum 390px in {sk}: {info}")
            self.assertLessEqual(info["skinRight"], info["innerW"], f"#rx-skin-toggle overflows 390px in {sk}: {info}")
            self.assertLessEqual(info["themeRight"], info["innerW"], f"#rx-theme-toggle overflows 390px in {sk}: {info}")


if __name__ == "__main__":
    unittest.main()
