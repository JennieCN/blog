#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Idempotently deploy CC's 4-skin system (pop, ink, luxe, plain) across BOTH live sites on vps8:
  - https://blog.mycampusmail.com (Halo 2.27 + theme-earth)
  - https://qa.mycampusmail.com   (Flarum 2.0)

Zero hardcoded & zero temp-file credentials:
  - Halo admin credentials are read strictly from ../private/gatewave-halo-admin.txt
    or HALO_USER / HALO_PASS environment variables and streamed in-memory over SSH stdin
    (never written to local or remote /tmp files).
  - Flarum database credentials are read inside vps8's site-flarum-db container environment.

Usage:
  python3 scripts/deploy-rx-skins.py
  python3 scripts/deploy-rx-skins.py --ssh-host vps8
"""
import argparse
import base64
import json
import os
import shlex
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKINS_DIR = REPO_ROOT / "scripts" / "rx-skins"
DEFAULT_CRED_PATH = REPO_ROOT.parent / "private" / "gatewave-halo-admin.txt"

STATIC_ASSETS = [
    "rx-tokens.css",
    "rx-halo.css",
    "rx-flarum.css",
    "rx-switcher.js",
    "ink-landscape.svg",
    "ink-mountains.svg",
    "ink-stroke.svg",
]


def read_halo_credentials(cred_path: Path):
    user = os.environ.get("HALO_USER", "")
    pw = os.environ.get("HALO_PASS", "")
    if user and pw:
        return user, pw
    if not cred_path.is_file():
        raise FileNotFoundError(f"Halo credentials file not found: {cred_path}")
    for line in cred_path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k == "username":
                user = v
            elif k == "password":
                pw = v
    if not user or not pw:
        raise ValueError(f"Missing Username or Password in {cred_path}")
    return user, pw


REMOTE_DEPLOY_SCRIPT = r"""
import base64
import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

cfg = json.loads(sys.stdin.read())

STACK_DIR = Path("/opt/site-stack")
RX_DIR = STACK_DIR / "rx-skins"
TS = time.strftime("%Y%m%d_%H%M%S")
SNAP_DIR = STACK_DIR / "backups" / f"pre-rx-skins-{TS}"
SNAP_DIR.mkdir(parents=True, exist_ok=True)

# 1. Backup existing configs before mutation
for fn in ("docker-compose.yml", "Caddyfile", "backup.sh"):
    src = STACK_DIR / fn
    if src.is_file():
        shutil.copy2(src, SNAP_DIR / fn)

# 2. Write static /rx-skins/* assets
RX_DIR.mkdir(parents=True, exist_ok=True)
for name, b64_data in cfg["static_files"].items():
    out = RX_DIR / name
    out.write_bytes(base64.b64decode(b64_data))
    os.chmod(out, 0o644)
print(f"[deploy-rx-skins] Synced {len(cfg['static_files'])} static files to {RX_DIR}")

# 3. Idempotently mount ./rx-skins:/srv/rx-skins:ro in docker-compose.yml (site-proxy)
compose_path = STACK_DIR / "docker-compose.yml"
compose_txt = compose_path.read_text(encoding="utf-8")
if "./rx-skins:/srv/rx-skins:ro" not in compose_txt:
    anchor = "      - ./Caddyfile:/etc/caddy/Caddyfile:ro\n"
    if anchor not in compose_txt:
        raise RuntimeError("Could not find Caddyfile volume anchor in docker-compose.yml")
    compose_txt = compose_txt.replace(
        anchor,
        anchor + "      - ./rx-skins:/srv/rx-skins:ro\n",
        1,
    )
    compose_path.write_text(compose_txt, encoding="utf-8")
    print("[deploy-rx-skins] Patched docker-compose.yml with ./rx-skins:/srv/rx-skins:ro")
else:
    print("[deploy-rx-skins] docker-compose.yml already mounts ./rx-skins:/srv/rx-skins:ro")

# 4. Idempotently add handle_path /rx-skins/* & handle /favicon.ico to both subdomains in Caddyfile
caddy_path = STACK_DIR / "Caddyfile"
caddy_txt = caddy_path.read_text(encoding="utf-8")
RX_CADDY_SNIPPET = (
    "\thandle_path /rx-skins/* {\n"
    "\t\troot * /srv/rx-skins\n"
    "\t\theader Cache-Control \"public, max-age=604800\"\n"
    "\t\tfile_server\n"
    "\t}\n\n"
)
BLOG_FAVICON_SNIPPET = (
    "\thandle /favicon.ico {\n"
    "\t\theader Cache-Control \"public, max-age=604800\"\n"
    "\t\trewrite * /upload/favicon.png\n"
    "\t\treverse_proxy halo:8090\n"
    "\t}\n\n"
)
QA_FAVICON_SNIPPET = (
    "\thandle /favicon.ico {\n"
    "\t\theader Cache-Control \"public, max-age=604800\"\n"
    "\t\trewrite * /assets/favicon.png\n"
    "\t\treverse_proxy flarum:8000\n"
    "\t}\n\n"
)

updated_caddy = False
if "handle_path /rx-skins/*" not in caddy_txt:
    for target in ("\treverse_proxy halo:8090", "\treverse_proxy flarum:8000"):
        if target not in caddy_txt:
            raise RuntimeError(f"Missing target in Caddyfile: {target}")
        caddy_txt = caddy_txt.replace(target, RX_CADDY_SNIPPET + target, 1)
    updated_caddy = True
elif caddy_txt.count("handle_path /rx-skins/*") < 2:
    if "\treverse_proxy flarum:8000" in caddy_txt and "\nqa.mycampusmail.com {" in caddy_txt:
        parts = caddy_txt.split("\nqa.mycampusmail.com {", 1)
        if "handle_path /rx-skins/*" not in parts[1]:
            parts[1] = parts[1].replace("\treverse_proxy flarum:8000", RX_CADDY_SNIPPET + "\treverse_proxy flarum:8000", 1)
            caddy_txt = "\nqa.mycampusmail.com {".join(parts)
            updated_caddy = True

if "\nqa.mycampusmail.com {" in caddy_txt:
    blog_part, qa_part = caddy_txt.split("\nqa.mycampusmail.com {", 1)
    if "handle /favicon.ico" not in blog_part and "\treverse_proxy halo:8090" in blog_part:
        blog_part = blog_part.replace("\treverse_proxy halo:8090", BLOG_FAVICON_SNIPPET + "\treverse_proxy halo:8090", 1)
        updated_caddy = True
    if "handle /favicon.ico" not in qa_part and "\treverse_proxy flarum:8000" in qa_part:
        qa_part = qa_part.replace("\treverse_proxy flarum:8000", QA_FAVICON_SNIPPET + "\treverse_proxy flarum:8000", 1)
        updated_caddy = True
    caddy_txt = blog_part + "\nqa.mycampusmail.com {" + qa_part

if updated_caddy:
    caddy_path.write_text(caddy_txt, encoding="utf-8")
    print("[deploy-rx-skins] Updated Caddyfile with /rx-skins/* and /favicon.ico handlers on both subdomains")
else:
    print("[deploy-rx-skins] Caddyfile already serves /rx-skins/* and /favicon.ico on both subdomains")

# 5. Idempotently include rx-skins & configs + expired empty dir cleanup in backup.sh
backup_sh = STACK_DIR / "backup.sh"
if backup_sh.is_file():
    btxt = backup_sh.read_text(encoding="utf-8")
    changed_backup = False
    if "site-configs_" not in btxt:
        line_to_add = 'tar czf "$DIR/site-configs_${TS}.tar.gz" -C /opt/site-stack docker-compose.yml Caddyfile backup.sh rx-skins\n'
        if "find \"$DIR\"" in btxt:
            btxt = btxt.replace('find "$DIR"', line_to_add + 'find "$DIR"', 1)
        else:
            btxt = btxt.rstrip() + "\n" + line_to_add
        changed_backup = True
    if "-type d -empty -delete" not in btxt:
        old_find = 'find "$DIR" -type f -mtime +7 -delete'
        new_find = old_find + '\nfind "$DIR" -mindepth 1 -type d -empty -delete'
        if old_find in btxt:
            btxt = btxt.replace(old_find, new_find, 1)
        else:
            btxt = btxt.rstrip() + '\nfind "$DIR" -mindepth 1 -type d -empty -delete\n'
        changed_backup = True
    if changed_backup:
        backup_sh.write_text(btxt, encoding="utf-8")
        os.chmod(backup_sh, 0o755)
        print("[deploy-rx-skins] Updated backup.sh (site-configs archive + empty dir cleanup)")

# 6. Recreate site-proxy if needed & reload Caddy
subprocess.check_call(["docker", "compose", "up", "-d", "site-proxy"], cwd=str(STACK_DIR))
subprocess.check_call(["docker", "exec", "site-proxy", "caddy", "reload", "--config", "/etc/caddy/Caddyfile"])
print("[deploy-rx-skins] Reloaded site-proxy (Caddy)")

# 7. Update Halo /api/v1alpha1/configmaps/system -> data.codeInjection.globalHead
HALO_BASE = cfg["halo_base_url"]
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

login_html = opener.open(HALO_BASE + "/login", timeout=20).read().decode("utf-8")
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', login_html).group(1)
pub = re.search(r'const\s+publicKey\s*=\s*"([^"]+)"', login_html).group(1).replace("\\/", "/")
pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(pub[i:i+64] for i in range(0, len(pub), 64)) + "\n-----END PUBLIC KEY-----\n"

with tempfile.NamedTemporaryFile("w", delete=False) as tf:
    tf.write(pem)
    pem_path = tf.name
try:
    enc = subprocess.check_output(
        ["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", pem_path],
        input=cfg["halo_password"].encode("utf-8"),
    )
finally:
    try:
        os.unlink(pem_path)
    except Exception:
        pass

pw_b64 = base64.b64encode(enc).decode("ascii")
form_data = urllib.parse.urlencode({"_csrf": csrf, "username": cfg["halo_username"], "password": pw_b64}).encode("utf-8")
opener.open(urllib.request.Request(HALO_BASE + "/login", data=form_data, headers={"Content-Type": "application/x-www-form-urlencoded"}), timeout=20)

xsrf = ""
for c in cj:
    if c.name == "XSRF-TOKEN":
        xsrf = urllib.parse.unquote(c.value)

def halo_api(method: str, path: str, obj=None):
    headers = {"Accept": "application/json"}
    if xsrf:
        headers["X-XSRF-TOKEN"] = xsrf
    body = None
    if obj is not None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(HALO_BASE + path, data=body, headers=headers, method=method)
    try:
        resp = opener.open(req, timeout=30)
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode("utf-8", errors="replace")[:500]}

for att in range(5):
    st, sys_cm = halo_api("GET", "/api/v1alpha1/configmaps/system")
    if st != 200:
        raise RuntimeError(f"GET /api/v1alpha1/configmaps/system failed ({st}): {sys_cm}")
    data_map = sys_cm.setdefault("data", {})
    prev_ci_raw = data_map.get("codeInjection", "{}")
    if att == 0:
        (SNAP_DIR / "halo-codeInjection.json").write_text(prev_ci_raw, encoding="utf-8")
    try:
        ci_obj = json.loads(prev_ci_raw) if prev_ci_raw else {}
    except Exception:
        ci_obj = {}
    ci_obj["globalHead"] = cfg["halo_global_head"]
    ci_obj.setdefault("contentHead", "")
    ci_obj.setdefault("footer", "")
    data_map["codeInjection"] = json.dumps(ci_obj, ensure_ascii=False)
    st_put, res_put = halo_api("PUT", "/api/v1alpha1/configmaps/system", sys_cm)
    if st_put == 200:
        print(f"[deploy-rx-skins] Updated Halo system ConfigMap codeInjection.globalHead ({len(cfg['halo_global_head'])} chars)")
        break
    if st_put != 409:
        raise RuntimeError(f"PUT /api/v1alpha1/configmaps/system failed ({st_put}): {res_put}")
    time.sleep(0.3 * (att + 1))
else:
    raise RuntimeError("409 conflict persisted updating Halo configmaps/system")

# 8. Backup & update Flarum settings + clear Flarum cache
select_sql = (
    "SELECT `key`, TO_BASE64(`value`) FROM flarum_settings "
    "WHERE `key` IN ('custom_header','theme_primary_color','theme_secondary_color');\n"
)
prev_flarum = subprocess.check_output(
    [
        "docker", "exec", "-i", "site-flarum-db", "sh", "-c",
        'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -N -B --raw'
    ],
    input=select_sql.encode("utf-8"),
).decode("utf-8", errors="replace")
(SNAP_DIR / "flarum-settings.tsv").write_text(prev_flarum, encoding="utf-8")

header_hex = cfg["flarum_custom_header"].encode("utf-8").hex()
sql = (
    f"INSERT INTO flarum_settings (`key`, `value`) VALUES ('custom_header', UNHEX('{header_hex}')) "
    f"ON DUPLICATE KEY UPDATE `value` = VALUES(`value`); "
    f"INSERT INTO flarum_settings (`key`, `value`) VALUES ('theme_primary_color', '#b8461f') "
    f"ON DUPLICATE KEY UPDATE `value` = VALUES(`value`); "
    f"INSERT INTO flarum_settings (`key`, `value`) VALUES ('theme_secondary_color', '#9a5b00') "
    f"ON DUPLICATE KEY UPDATE `value` = VALUES(`value`);"
)
subprocess.run(
    [
        "docker", "exec", "-i", "site-flarum-db", "sh", "-c",
        'mariadb -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
    ],
    input=sql.encode("utf-8"),
    check=True,
)
subprocess.check_call(["docker", "exec", "site-flarum", "php", "/opt/flarum/flarum", "cache:clear"])
print(f"[deploy-rx-skins] Updated Flarum custom_header ({len(cfg['flarum_custom_header'])} chars), warm theme colors & cleared cache")
print(f"[deploy-rx-skins] Pre-change snapshot saved at {SNAP_DIR}")
"""


def main():
    ap = argparse.ArgumentParser(description="Deploy CC 4-skin system to Halo & Flarum on vps8")
    ap.add_argument("--ssh-host", default="vps8", help="SSH host alias for live server")
    ap.add_argument("--halo-base-url", default="http://127.0.0.1:8091", help="Halo loopback URL on remote host")
    ap.add_argument("--cred-file", default=str(DEFAULT_CRED_PATH), help="Path to Halo admin credentials file")
    args = ap.parse_args()

    halo_user, halo_pw = read_halo_credentials(Path(args.cred_file))

    static_files = {}
    for fname in STATIC_ASSETS:
        fpath = SKINS_DIR / fname
        if not fpath.is_file():
            raise FileNotFoundError(f"Missing static skin file: {fpath}")
        static_files[fname] = base64.b64encode(fpath.read_bytes()).decode("ascii")

    halo_head = (SKINS_DIR / "halo-global-head.html").read_text(encoding="utf-8")
    flarum_header = (SKINS_DIR / "flarum-custom-header.html").read_text(encoding="utf-8")

    payload = {
        "halo_base_url": args.halo_base_url,
        "halo_username": halo_user,
        "halo_password": halo_pw,
        "static_files": static_files,
        "halo_global_head": halo_head,
        "flarum_custom_header": flarum_header,
    }

    subprocess.run(
        ["ssh", args.ssh_host, f"python3 -c {shlex.quote(REMOTE_DEPLOY_SCRIPT)}"],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        check=True,
    )


if __name__ == "__main__":
    main()
