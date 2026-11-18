#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse all 56 MeowVPS official vendor dossier cards (meow_vol2/vps_cards/<id>.html)
and all matching /blog/... review pages (meow_vol2/pages/<slug>.html) into a clean
structured JSON dataset (meow_vol2/structured_56.json).

Also exposes `parse_blog_article(slug)` for Volume 1's generator to extract official
terminal benchmark <pre> blocks for newly covered regional lines.
"""
import html, json, os, re, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.abspath(os.path.join(HERE, "..", "..", "..", "data", "vps-reviews-202611"))
DATA_ROOT = os.environ.get("VPS_DATA_DIR") or (DEFAULT_DATA if os.path.isdir(DEFAULT_DATA) else "/tmp")
MEOW_DIR = os.path.join(DATA_ROOT, "meow_vol2")

# Explicit slug mapping for all 56 Vol. 2 vendors -> all their /blog/<slug>/ review pages
EXTRA_BLOG_SLUGS = {
    "digitalfyre": ["digitalfyre", "digitalfyresg"],
    "datawave": ["datawave"],
    "pqs": ["pqsvnfpt", "pqstwpro", "pqstwhinet2", "pqshkt"],
    "leikwanhost": ["leikwanhost"],
    "lightlayer": ["lightlayersjc", "lightlayersg"],
    "xuezhangvps": ["学长网络", "xuezhangvpskddi", "xuezhangvpshinet"],
    "quicksrv": ["quicksrvams", "quicksrvuk"],
    "VPS": ["vpssj", "vpssg", "vpsnl", "vpsde"],
    "greencloud": ["greencloud", "greencloudjp"],
    "tokyonline": ["tokyonline"],
    "saltyfish": ["saltyfish", "saltyfishfrelite"],
    "bestvm": ["bestvmuspro", "bestvmtw", "bestvmjpbgp"],
    "moonvm": ["moonvm"],
    "sixtynet": ["sixtynet", "sixtynetpro"],
    "netcup": [],
    "vmrack": ["vmrack"],
    "residentialservice": ["residentialservice", "residentialservicetk", "residentialserviceuk"],
    "rivencloud": ["rivensg", "rivenjp"],
    "yunyoo": ["yunyoo", "yunyoohk4", "yunyoohk5", "yunyooiij", "yunyootw", "yunyoocstd", "yunyoode9929"],
    "taipei101": ["taipei101", "taipei101tw", "taipei101sg", "taipei101jp", "taipei101laxspe"],
    "synexvm": ["synexvm"],
    "aethercloud": ["aethercloud"],
    "hostdare": ["hostdare"],
    "geelinx": ["geelinx", "geelinxuk", "geelinxhk"],
    "100tb": ["100tb", "100tbjp", "100tbkrpro", "100tbsgco"],
    "tcs": ["tcs"],
    "kaze": ["kaze", "kazecmhk", "kazehkbnnat", "kazehkt", "kazewttnat"],
    "dpnet": ["dpnet"],
    "miraigrid": ["miraigrid"],
    "nmcloud": ["nmcloud", "nmcseednet"],
    "isif": ["isif", "isifcop", "isifuscop"],
    "bwh": ["bwh", "bwhdc6", "bwhdc9"],
    "vircs": ["vircs"],
    "ipraft": ["ipraft", "ipraftindia"],
    "rfc": ["rfc", "rfchkco"],
    "evoxt": ["evoxt", "evoxtmy", "evoxthk"],
    "taphip": ["taphip"],
    "nube": ["nube", "nubethai"],
    "bage": ["bage"],
    "akko": ["akkocloud"],
    "neburst": ["neburst", "nebursttw"],
    "boil": ["boil", "boilcpe", "boilusfrontier"],
    "gomami": ["gomami", "gomamijp", "gomamius", "gomamisg", "gomamide"],
    "vmiss": ["vmiss", "vmisstridc1"],
    "skyline": ["skyline"],
    "wirecat": ["wirecat", "wirecattest"],
    "dmit": ["dmit", "dmithkeb"],
    "fachost": ["fachost", "fachosttbc", "fachosthinetnat", "fachostsonet"],
    "qqpw": ["hawaii"],
    "yinnet": ["yinnet", "yinnetuk", "yinnetfr"],
    "aaitr": ["aaitr", "aaitrfrontier", "aaitrverizon", "aaitrverizonnat"],
    "zorocloud": ["zorocloudglbb", "zorocloudin", "zorocloudmy", "zorocloudsg", "zorocloudkr", "zorocloudde", "zorocloudatt"],
    "bugnet": ["bugnet", "bugnetjp", "bugnetper", "bugnetjp2"],
    "ciallonetworks": ["ciallojp", "ciallous", "ciallohk", "ciallohkepyc", "ciallode9929"],
    "novixlink": ["novixntt", "novixcox", "novixcg"],
    "mondoze": ["mondozelinuxvps", "mondozetmnet"],
}


def clean_site_url(u):
    if not u:
        return ""
    p = urllib.parse.urlsplit(u)
    if not p.scheme or not p.netloc:
        return ""
    path = p.path
    if path.rstrip("/").endswith("aff.php"):
        path = "/"
    return f"{p.scheme}://{p.netloc}{path}" if path != "/" else f"{p.scheme}://{p.netloc}/"


def parse_card(vid):
    raw = open(os.path.join(MEOW_DIR, "vps_cards", f"{vid}.html"), encoding="utf-8", errors="ignore").read()
    m = re.search(r"<main[^>]*>([\s\S]*?)</main>", raw)
    chunk = m.group(1) if m else raw
    site_m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*官网\s*</a>', chunk)
    site_url = clean_site_url(site_m.group(1)) if site_m else ""

    body = re.sub(r"<(script|style|svg)[^>]*>[\s\S]*?</\1>", "", chunk)
    lines = [l.strip() for l in html.unescape(re.sub(r"<[^>]+>", "\n", body)).splitlines() if l.strip()]

    def idx_of(label):
        for i, l in enumerate(lines):
            if l == label:
                return i
        return -1

    rating = ""
    updated = ""
    intro = ""
    for i, l in enumerate(lines[:18]):
        if l in ("好评如潮", "特别好评", "多半好评", "褒贬不一", "多半差评", "差评如潮", "暂无评分", "谨慎购买"):
            rating = l
        if l.startswith("更新："):
            updated = l.replace("更新：", "").strip()
            if i + 1 < len(lines) and lines[i + 1] != "基础信息":
                intro = lines[i + 1]

    def field_after(key, stop_keys):
        k = idx_of(key)
        if k < 0:
            return ""
        vals = []
        for j in range(k + 1, min(k + 5, len(lines))):
            if lines[j] in stop_keys:
                break
            if lines[j] not in vals:
                vals.append(lines[j])
        return "；".join(vals)

    stops = {
        "官方 Looking glass", "TOS", "AUP", "退款策略", "实名要求",
        "支付方式", "工单响应", "本站探针", "测评时间线", "特点",
        "代表产品线", "猫猫评价", "MJJ评价", "商家活动", "频道公告"
    }
    refund = field_after("退款策略", stops)
    kyc = field_after("实名要求", stops)
    pay = field_after("支付方式", stops)
    ticket = field_after("工单响应", stops)

    feats = []
    i_feat = idx_of("特点")
    if i_feat >= 0:
        for j in range(i_feat + 1, len(lines)):
            if lines[j] in stops:
                break
            feats.append(lines[j])

    rep_lines = []
    i_rep = idx_of("代表产品线")
    if i_rep >= 0:
        buf = []
        for j in range(i_rep + 1, len(lines)):
            if lines[j] in stops:
                break
            buf.append(lines[j])
        k = 0
        while k < len(buf):
            name = buf[k]
            desc = ""
            spec = ""
            if k + 1 < len(buf) and buf[k + 1].startswith("："):
                desc = buf[k + 1].lstrip("：").strip()
                k += 1
            if k + 1 < len(buf) and (buf[k + 1].startswith("（") or buf[k + 1].startswith("(")):
                spec = buf[k + 1].strip("（）() ")
                k += 1
            rep_lines.append({"name": name, "desc": desc, "spec": spec})
            k += 1

    meow_comment = ""
    i_mc = idx_of("猫猫评价")
    if i_mc >= 0:
        mc_parts = []
        for j in range(i_mc + 1, len(lines)):
            if lines[j] in stops:
                break
            mc_parts.append(lines[j])
        meow_comment = " ".join(mc_parts).strip()

    mjj_comments = []
    i_mjj = idx_of("MJJ评价")
    if i_mjj >= 0:
        for j in range(i_mjj + 1, len(lines)):
            if lines[j] in stops:
                break
            if " · 202" in lines[j] and j + 1 < len(lines) and lines[j + 1] not in stops:
                mjj_comments.append(f"{lines[j]}：{lines[j + 1]}")

    return {
        "site_url": site_url,
        "rating": rating,
        "updated": updated,
        "intro": intro,
        "refund": refund,
        "kyc": kyc,
        "pay": pay,
        "ticket": ticket,
        "features": feats,
        "rep_lines": rep_lines,
        "meow_comment": meow_comment,
        "mjj_comments": mjj_comments[:4],
    }


def parse_blog_article(slug, parsed_index=None):
    if parsed_index is None:
        parsed_index = json.load(open(os.path.join(MEOW_DIR, "parsed_index.json"), encoding="utf-8"))
    safe = urllib.parse.quote(slug, safe="")
    fp = os.path.join(MEOW_DIR, "pages", f"{safe}.html")
    if not os.path.exists(fp):
        fp_raw = os.path.join(MEOW_DIR, "pages", f"{slug}.html")
        if os.path.exists(fp_raw):
            fp = fp_raw
        else:
            raise FileNotFoundError(fp)
    raw = open(fp, encoding="utf-8", errors="ignore").read()
    m = re.search(r"<article[^>]*>([\s\S]*?)</article>", raw)
    art = m.group(1) if m else raw
    art_no_script = re.sub(r"<(script|style|svg)[^>]*>[\s\S]*?</\1>", "", art)

    art_no_pre = re.sub(r"<pre[^>]*>[\s\S]*?</pre>", "\n", art_no_script)
    blocks = []
    for tag, inner in re.findall(r"<(h[2-4]|p|blockquote|li)[^>]*>([\s\S]*?)</\1>", art_no_pre):
        txt = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        txt = re.sub(r"\s+", " ", txt)
        if not txt or txt in ("目录", "前言", "写在前面"):
            continue
        if len(txt) < 4:
            continue
        txt = re.sub(r"https?://\S*aff\S*", "", txt).strip()
        blocks.append((tag, txt))

    pres_raw = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<pre[^>]*>([\s\S]*?)</pre>", art_no_script)]
    good_pres = []
    for p in pres_raw:
        if len(p) < 220:
            continue
        if p in good_pres:
            continue
        good_pres.append(p)

    kept_pres = []
    total_chars = 0
    for p in good_pres:
        if total_chars + len(p) > 16000 and len(kept_pres) >= 3:
            break
        kept_pres.append(p)
        total_chars += len(p)

    meta = parsed_index[slug]
    url_slug = urllib.parse.quote(slug, safe="")
    return {
        "slug": slug,
        "url": f"https://meowvps.com/blog/{url_slug}/",
        "title": meta["title"],
        "date": meta["date"],
        "blocks": blocks[:45],
        "pre_total_count": len(good_pres),
        "pre_kept_count": len(kept_pres),
        "combined_pre": "\n\n".join(kept_pres),
    }


def main():
    vendors = json.load(open(os.path.join(MEOW_DIR, "vol2_vendors.json"), encoding="utf-8"))
    parsed_index = json.load(open(os.path.join(MEOW_DIR, "parsed_index.json"), encoding="utf-8"))
    out = []
    total_articles = 0
    total_pre_blocks = 0
    for v in vendors:
        vid = v["id"]
        assert vid in EXTRA_BLOG_SLUGS, f"Missing slug mapping for {vid}"
        card = parse_card(vid)
        slugs = list(EXTRA_BLOG_SLUGS[vid])
        if v.get("detailReview"):
            dr_slug = urllib.parse.unquote(v["detailReview"].strip("/").split("/", 1)[1])
            if dr_slug not in slugs:
                slugs = [dr_slug] + slugs
        arts = [parse_blog_article(s, parsed_index) for s in slugs]
        arts.sort(key=lambda x: x["date"] or "")
        total_articles += len(arts)
        total_pre_blocks += sum(1 for a in arts if a["combined_pre"])
        out.append({
            "id": vid,
            "name": v["name"],
            "recommended": bool(v.get("recommended")),
            "tags": v.get("tags", {}),
            "card_url": f"https://meowvps.com/vps/{vid}/",
            "card": card,
            "articles": arts,
        })

    out_path = os.path.join(MEOW_DIR, "structured_56.json")
    open(out_path, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"SUCCESS: Parsed {len(out)}/56 vendors, {total_articles} official blog review articles, {total_pre_blocks} combined terminal <details> blocks -> {out_path}")


if __name__ == "__main__":
    main()
