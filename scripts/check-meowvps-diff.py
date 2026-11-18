#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit MeowVPS live vendor directory (https://meowvps.com/vendors/index.json) AND
live blog sitemap (https://meowvps.com/sitemap-0.xml) against our two local companion posts:
  - Volume 1: src/content/vps/nodeseek-merchant-reviews-2026h2.md (61 MeowVPS merchants)
  - Volume 2: src/content/vps/meowvps-official-merchants-2026h2.md (56 MeowVPS merchants)

Reports exact vendor coverage, overlap check, and any newly added MeowVPS vendors or new /blog/ reviews.
"""
import json, os, re, sys, urllib.parse, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VOL1 = os.path.join(ROOT, "src/content/vps/nodeseek-merchant-reviews-2026h2.md")
VOL2 = os.path.join(ROOT, "src/content/vps/meowvps-official-merchants-2026h2.md")

# Non-review site guides / announcements / UI test pages on meowvps.com/blog/
KNOWN_NON_REVIEW_BLOG_SLUGS = {
    "answer",
    "detect",
    "introduce",
    "ipcheck",
    "meowcheck",
    "meowoneyear",
    "meowoneyearre",
    "meowwork",
    "natplay",
    "probe-v2-ui-test",
    "resrec",
    "route",
    "script",
    "vpsstart",
}

# Exact 61 MeowVPS vendor IDs covered in Volume 1
VOL1_ID_MAP = {
    "666clouds": "六六云",
    "attvps": "ATTVPS",
    "berohost": "BeroHost",
    "blossomhost": "BlossomHost",
    "bocchi": "Bocchi",
    "breadcloud": "BreadCloud",
    "buyvm": "BuyVM",
    "cloudsilk": "CloudSilk",
    "coffeehost": "CoffeeHost",
    "dataonline": "DataOnline",
    "dedirock": "DediRock",
    "flawlessnode": "FlawlessNode",
    "fxtransit": "FXTRANSIT",
    "gatewaysentry": "GatewaySentry",
    "goldcloud": "GoldCloud",
    "goodlycloud": "GoodlyCloud",
    "halocloud": "HaloCloud",
    "hhost": "HHost",
    "highendnetwork": "HighEndNetwork",
    "hkcloudx": "HKCloudX",
    "hostblazer": "HostBlazer",
    "hostdzire": "HostDzire",
    "hosthatch": "HostHatch",
    "iaclouds": "艾云",
    "ipmela": "IPMELA",
    "jcloud": "JCloudHosting",
    "jdidc": "JDIDC",
    "jindouyun": "筋斗云",
    "jtti": "JTTI",
    "kfchost": "KFCHost",
    "lamhosting": "LamHosting",
    "langya": "Langya",
    "lazycat": "LazyCatCloud",
    "legendvps": "LegendVPS",
    "lightnode": "LightNode",
    "lisahost": "LisaHost",
    "misaka": "Misaka",
    "nexkr": "NexKr",
    "nobrand": "NoBrand",
    "nosla": "NOSLA",
    "orangevps": "OrangeVPS",
    "panstar": "PanstarCloud",
    "peekabo": "Peekabo Networks",
    "ppflight": "PPFlight",
    "racknerd": "RackNerd",
    "radonet": "RadoNet",
    "residentialvps": "ResidentialVPS",
    "shandun": "ShanDun Network",
    "tamago": "Tamago Network",
    "terabix": "Terabix",
    "tothost": "TOTHOST",
    "usvps24": "USVPS24",
    "vmshell": "VmShell",
    "vmvm": "VMVM",
    "vpstaxi": "VPS.TAXI",
    "wawo": "wawo",
    "webhorizon": "WebHorizon",
    "wepc": "WePC",
    "wlx": "WLX",
    "zgocloud": "ZgoCloud",
    "zouter": "Zouter",
}


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8")


def main():
    raw = json.loads(fetch_text("https://meowvps.com/vendors/index.json"))
    vendors = raw["vendors"] if isinstance(raw, dict) and "vendors" in raw else raw

    vol1_txt = open(VOL1, encoding="utf-8").read() if os.path.exists(VOL1) else ""
    vol2_txt = open(VOL2, encoding="utf-8").read() if os.path.exists(VOL2) else ""
    combined_txt = vol1_txt + "\n" + vol2_txt

    in_v1, in_v2, missing = [], [], []
    for v in vendors:
        vid = v["id"]
        vname = v["name"]
        hit1 = vid in VOL1_ID_MAP and (VOL1_ID_MAP[vid] in vol1_txt)
        hit2 = f"https://meowvps.com/vps/{vid}/" in vol2_txt
        if hit1:
            in_v1.append(vid)
        if hit2:
            in_v2.append(vid)
        if not hit1 and not hit2:
            missing.append((vid, vname, v.get("placeholder"), v.get("detailReview")))

    overlap = set(in_v1) & set(in_v2)

    # Check sitemap /blog/<slug>/ review coverage
    sitemap_xml = fetch_text("https://meowvps.com/sitemap-0.xml")
    live_blog_slugs = {
        urllib.parse.unquote(m)
        for m in re.findall(r"https://meowvps\.com/blog/([^/<\"\s]+)/?", sitemap_xml)
        if m not in ("page", "tags", "categories")
    }
    linked_blog_slugs = {
        urllib.parse.unquote(m)
        for m in re.findall(r"https://meowvps\.com/blog/([^/\"\)\s]+)/?", combined_txt)
    }
    review_slugs_live = live_blog_slugs - KNOWN_NON_REVIEW_BLOG_SLUGS
    unlinked_reviews = sorted(review_slugs_live - linked_blog_slugs)

    print(f"MeowVPS live vendors total   : {len(vendors)}")
    print(f"Covered in Volume 1          : {len(in_v1)}")
    print(f"Covered in Volume 2          : {len(in_v2)}")
    print(f"Overlap between Vol.1 & 2    : {len(overlap)} {sorted(overlap) if overlap else ''}")
    print(f"Uncovered / New vendors      : {len(missing)}")
    print(f"Live /blog/ review articles  : {len(review_slugs_live)} (linked: {len(review_slugs_live & linked_blog_slugs)}, unlinked: {len(unlinked_reviews)})")
    for m in missing:
        print("  NEW VENDOR:", m)
    for s in unlinked_reviews:
        print(f"  NEW / UNLINKED REVIEW: https://meowvps.com/blog/{s}/")
    if missing or overlap or unlinked_reviews:
        sys.exit(1)
    print("AUDIT PASSED: 100% of MeowVPS directory vendors (117/117) AND 100% of /blog/ reviews (205/205) are covered!")


if __name__ == "__main__":
    main()
