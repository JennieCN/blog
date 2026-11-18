#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Server-side weekly watcher for MeowVPS newly listed vendors & /blog/ review articles.
Designed to run via cron on vps8 (/opt/site-stack/watch-meowvps.py):
  - Compares live https://meowvps.com/vendors/index.json and https://meowvps.com/sitemap-0.xml
    against our live Halo Vol. 1 & Vol. 2 pages (via local 127.0.0.1:8091).
  - Deduplicates state in /opt/site-stack/.meowvps-watch-state.json so identical diffs only email once.
  - Reads SMTP credentials dynamically from site-flarum-db (flarum_settings) when --notify-email is passed;
    ZERO credentials are hardcoded in this script.
"""
import argparse, datetime, email.message, hashlib, json, os, re, smtplib, ssl, subprocess, urllib.parse, urllib.request

LOCAL_HALO = "http://127.0.0.1:8091"
STATE_FILE = "/opt/site-stack/.meowvps-watch-state.json"

KNOWN_NON_REVIEW_BLOG_SLUGS = {
    "answer", "detect", "introduce", "ipcheck", "meowcheck",
    "meowoneyear", "meowoneyearre", "meowwork", "natplay",
    "probe-v2-ui-test", "resrec", "route", "script", "vpsstart",
}

VOL1_ID_MAP = {
    "666clouds": "六六云", "attvps": "ATTVPS", "berohost": "BeroHost", "blossomhost": "BlossomHost",
    "bocchi": "Bocchi", "breadcloud": "BreadCloud", "buyvm": "BuyVM", "cloudsilk": "CloudSilk",
    "coffeehost": "CoffeeHost", "dataonline": "DataOnline", "dedirock": "DediRock", "flawlessnode": "FlawlessNode",
    "fxtransit": "FXTRANSIT", "gatewaysentry": "GatewaySentry", "goldcloud": "GoldCloud", "goodlycloud": "GoodlyCloud",
    "halocloud": "HaloCloud", "hhost": "HHost", "highendnetwork": "HighEndNetwork", "hkcloudx": "HKCloudX",
    "hostblazer": "HostBlazer", "hostdzire": "HostDzire", "hosthatch": "HostHatch", "iaclouds": "艾云",
    "ipmela": "IPMELA", "jcloud": "JCloudHosting", "jdidc": "JDIDC", "jindouyun": "筋斗云",
    "jtti": "JTTI", "kfchost": "KFCHost", "lamhosting": "LamHosting", "langya": "Langya",
    "lazycat": "LazyCatCloud", "legendvps": "LegendVPS", "lightnode": "LightNode", "lisahost": "LisaHost",
    "misaka": "Misaka", "nexkr": "NexKr", "nobrand": "NoBrand", "nosla": "NOSLA",
    "orangevps": "OrangeVPS", "panstar": "PanstarCloud", "peekabo": "Peekabo Networks", "ppflight": "PPFlight",
    "racknerd": "RackNerd", "radonet": "RadoNet", "residentialvps": "ResidentialVPS", "shandun": "ShanDun Network",
    "tamago": "Tamago Network", "terabix": "Terabix", "tothost": "TOTHOST", "usvps24": "USVPS24",
    "vmshell": "VmShell", "vmvm": "VMVM", "vpstaxi": "VPS.TAXI", "wawo": "wawo",
    "webhorizon": "WebHorizon", "wepc": "WePC", "wlx": "WLX", "zgocloud": "ZgoCloud", "zouter": "Zouter",
}


def fetch_text(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MeowVPS-Diff-Watch/1.0)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def read_flarum_smtp_and_admin():
    env_raw = subprocess.check_output(["docker", "inspect", "site-flarum-db", "--format", "{{json .Config.Env}}"]).decode("utf-8")
    envs = dict(kv.split("=", 1) for kv in json.loads(env_raw) if "=" in kv)
    pw = envs.get("MARIADB_PASSWORD") or envs.get("MYSQL_PASSWORD")
    out = subprocess.check_output([
        "docker", "exec", "-i", "site-flarum-db", "mariadb", "-uflarum", f"-p{pw}", "flarum", "-N", "-e",
        "SELECT `key`, `value` FROM flarum_settings WHERE `key` IN ('mail_host','mail_port','mail_username','mail_password','mail_from');"
    ]).decode("utf-8")
    cfg = dict(line.split("\t", 1) for line in out.strip().splitlines() if "\t" in line)
    to_addr = subprocess.check_output([
        "docker", "exec", "-i", "site-flarum-db", "mariadb", "-uflarum", f"-p{pw}", "flarum", "-N", "-e",
        "SELECT email FROM flarum_users WHERE id=1;"
    ]).decode("utf-8").strip()
    cfg["to_addr"] = to_addr
    return cfg


def send_alert_email(subject, body_txt):
    cfg = read_flarum_smtp_and_admin()
    if not (cfg.get("mail_host") and cfg.get("mail_password") and cfg.get("to_addr")):
        print("[watch-meowvps] SMTP config incomplete, skipping email alert")
        return
    msg = email.message.EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"融夕的书巡检 <{cfg.get('mail_from', 'noreply@qa.mycampusmail.com')}>"
    msg["To"] = cfg["to_addr"]
    msg.set_content(body_txt)
    ctx = ssl.create_default_context()
    port = int(cfg.get("mail_port", "465"))
    with smtplib.SMTP_SSL(cfg["mail_host"], port, context=ctx, timeout=20) as s:
        s.login(cfg.get("mail_username", "resend"), cfg["mail_password"])
        s.send_message(msg)
    print(f"[watch-meowvps] Sent alert email to {cfg['to_addr']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--notify-email", action="store_true", help="Send email alert via Flarum Resend SMTP when new items are found")
    args = ap.parse_args()

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw = json.loads(fetch_text("https://meowvps.com/vendors/index.json"))
    vendors = raw["vendors"] if isinstance(raw, dict) and "vendors" in raw else raw

    vol1_html = fetch_text(f"{LOCAL_HALO}/archives/nodeseek-merchant-reviews-2026h2")
    vol2_html = fetch_text(f"{LOCAL_HALO}/archives/meowvps-official-merchants-2026h2")
    combined = vol1_html + "\n" + vol2_html

    missing_vendors = []
    for v in vendors:
        vid = v["id"]
        hit1 = vid in VOL1_ID_MAP and (VOL1_ID_MAP[vid] in vol1_html)
        hit2 = f"https://meowvps.com/vps/{vid}/" in vol2_html
        if not hit1 and not hit2:
            missing_vendors.append({"id": vid, "name": v.get("name", ""), "detailReview": v.get("detailReview", "")})

    sitemap_xml = fetch_text("https://meowvps.com/sitemap-0.xml")
    live_blog_slugs = {
        urllib.parse.unquote(m)
        for m in re.findall(r"https://meowvps\.com/blog/([^/<\"\s]+)/?", sitemap_xml)
        if m not in ("page", "tags", "categories")
    }
    linked_blog_slugs = {
        urllib.parse.unquote(m)
        for m in re.findall(r"https://meowvps\.com/blog/([^/\"'\)\s<]+)/?", combined)
    }
    review_slugs_live = live_blog_slugs - KNOWN_NON_REVIEW_BLOG_SLUGS
    unlinked_reviews = sorted(review_slugs_live - linked_blog_slugs)

    if not missing_vendors and not unlinked_reviews:
        print(f"[{ts}] OK: 100% covered (vendors={len(vendors)}, blog_reviews={len(review_slugs_live)}, diff=0)")
        return

    report_lines = [
        f"[{ts}] MeowVPS 增量巡检发现新条目：",
        f"- 当前猫猫商家总数：{len(vendors)}（未收录新增：{len(missing_vendors)}）",
        f"- 当前猫猫专测总数：{len(review_slugs_live)}（未收录新专测：{len(unlinked_reviews)}）",
        "",
    ]
    for mv in missing_vendors:
        report_lines.append(f"  [新商家] {mv['name']} (id={mv['id']}) -> https://meowvps.com/vps/{mv['id']}/")
    for slug in unlinked_reviews:
        report_lines.append(f"  [新专测] https://meowvps.com/blog/{slug}/")
    report_lines.append("\n可在本地仓库运行 `python3 scripts/check-meowvps-diff.py` 增量合入上下卷并发布。")
    report_txt = "\n".join(report_lines)
    print(report_txt)

    if args.notify_email:
        sig = hashlib.sha256(json.dumps({"v": missing_vendors, "b": unlinked_reviews}, sort_keys=True).encode("utf-8")).hexdigest()[:16]
        prev_sig = ""
        if os.path.exists(STATE_FILE):
            try:
                prev_sig = json.load(open(STATE_FILE)).get("last_sig", "")
            except Exception:
                pass
        if sig != prev_sig:
            send_alert_email(
                f"【融夕的书】MeowVPS 发现新收录变动（+{len(missing_vendors)} 商家 / +{len(unlinked_reviews)} 专测）",
                report_txt,
            )
            os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
            json.dump({"last_sig": sig, "updated_at": ts}, open(STATE_FILE, "w"))


if __name__ == "__main__":
    main()
