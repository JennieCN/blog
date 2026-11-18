#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Headless Chrome unit & DOM integration tests for scripts/rx-skins/."""
import http.server
import itertools
import json
import os
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
          // Also verify synchronous rapid bursts advance state without race
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


if __name__ == "__main__":
    unittest.main()
