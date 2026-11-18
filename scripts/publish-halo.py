#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish, update, pin, unpublish Posts or SinglePages (with optional Menu registration) on Halo CMS on vps8 (127.0.0.1:8091).
Credentials are read strictly from private/gatewave-halo-admin.txt or environment variables
(NEVER hardcoded in repository scripts).

Usage (publish/update a Post + optional pin):
  python3 scripts/publish-halo.py \
    --post-name post-meowvps-official-merchants-2026h2 \
    --slug meowvps-official-merchants-2026h2 \
    --md src/content/vps/meowvps-official-merchants-2026h2.md \
    --html /tmp/vol2.html \
    --pinned --priority 15 \
    --categories cat-vps \
    --tags "VPS:tag-vps,测评:tag-review"

Usage (publish/update a SinglePage + add to primary menu):
  python3 scripts/publish-halo.py \
    --single-page \
    --post-name page-tools \
    --slug tools \
    --title "实用工具箱" \
    --description "本机分流出口 IP 检测、多节点 HTTP 延迟测速、VPS 剩余价值计算器、电池组速算与术语脚本库" \
    --html scripts/halo-pages/tools.html \
    --menu-item-name menu-tools \
    --menu-display-name "工具箱" \
    --menu-after menu-res

Usage (batch publish multiple items in one session):
  python3 scripts/publish-halo.py --batch-json /tmp/batch.json

Usage (unpublish placeholder stub):
  python3 scripts/publish-halo.py --post-name post-ai-welcome --unpublish-only
"""
import argparse, json, os, re, subprocess, tempfile


def read_credentials(cred_path):
    user = os.environ.get("HALO_USER", "")
    pw = os.environ.get("HALO_PASS", "")
    if user and pw:
        return user, pw
    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Credentials file not found: {cred_path}")
    for line in open(cred_path, encoding="utf-8").read().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip().lower(), v.strip()
            if k == "username":
                user = v
            elif k == "password":
                pw = v
    if not user or not pw:
        raise ValueError("Missing Username or Password in credentials file")
    return user, pw


def parse_frontmatter(md_text):
    m = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", md_text)
    if not m:
        raise ValueError("Markdown file missing YAML frontmatter")
    fm_raw, body = m.group(1), m.group(2).lstrip("\n")
    meta = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def parse_tag_specs(tags_str):
    tag_specs = []
    for item in (tags_str or "").split(","):
        item = item.strip()
        if not item:
            continue
        if ":" in item:
            disp, tname = item.split(":", 1)
            tag_specs.append([disp.strip(), tname.strip()])
        else:
            tag_specs.append([item, f"tag-{item.lower()}"])
    return tag_specs


REMOTE_RUNNER = r"""
import os, sys, subprocess, re, json, base64, time, urllib.request, urllib.parse, urllib.error, http.cookiejar

cfg = json.load(open("/tmp/halo_pub_job.json", encoding="utf-8"))
BASE = cfg["base_url"]

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

html = opener.open(BASE + "/login").read().decode("utf-8")
csrf = re.search(r'name="_csrf"\s+value="([^"]+)"', html).group(1)
pub = re.search(r'const\s+publicKey\s*=\s*"([^"]+)"', html).group(1).replace("\\/", "/")
pem = "-----BEGIN PUBLIC KEY-----\n" + "\n".join(pub[i:i+64] for i in range(0, len(pub), 64)) + "\n-----END PUBLIC KEY-----\n"
open("/tmp/hp_pub.pem", "w").write(pem)
enc = subprocess.check_output(["openssl", "pkeyutl", "-encrypt", "-pubin", "-inkey", "/tmp/hp_pub.pem"], input=cfg["password"].encode("utf-8"))
try: os.unlink("/tmp/hp_pub.pem")
except Exception: pass
pw_b64 = base64.b64encode(enc).decode("ascii")
data = urllib.parse.urlencode({"_csrf": csrf, "username": cfg["username"], "password": pw_b64}).encode("utf-8")
opener.open(urllib.request.Request(BASE + "/login", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"}))

xsrf = ""
for c in cj:
    if c.name == "XSRF-TOKEN":
        xsrf = urllib.parse.unquote(c.value)

def api_req(method, path, obj=None):
    headers = {"Accept": "application/json"}
    if xsrf:
        headers["X-XSRF-TOKEN"] = xsrf
    body = None
    if obj is not None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        resp = opener.open(req, timeout=90)
        raw = resp.read().decode("utf-8")
        return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode("utf-8", errors="replace")[:600]}

def publish_post_item(item):
    POST_NAME = item["post_name"]
    SLUG = item["slug"]
    TITLE = item["title"]
    EXCERPT = item["description"]
    CATS = item.get("categories", [])
    TAG_SPECS = item.get("tag_specs", [])
    PINNED = item.get("pinned")
    PRIORITY = item.get("priority")
    COVER = item.get("cover")

    tag_names = []
    for disp, tname in TAG_SPECS:
        st, _ = api_req("GET", f"/apis/content.halo.run/v1alpha1/tags/{tname}")
        if st == 404:
            tslug = tname.replace("tag-", "")
            st_c, _ = api_req("POST", "/apis/content.halo.run/v1alpha1/tags", {
                "apiVersion": "content.halo.run/v1alpha1",
                "kind": "Tag",
                "metadata": {"name": tname},
                "spec": {"displayName": disp, "slug": tslug}
            })
            if st_c not in (200, 201):
                raise RuntimeError(f"Failed creating tag {tname}: {st_c}")
        tag_names.append(tname)

    content_payload = {
        "raw": item["raw_md"],
        "content": item["html"],
        "rawType": "markdown"
    }

    st_get, cur_post = api_req("GET", f"/apis/content.halo.run/v1alpha1/posts/{POST_NAME}")
    if st_get == 404:
        create_body = {
            "post": {
                "apiVersion": "content.halo.run/v1alpha1",
                "kind": "Post",
                "metadata": {"name": POST_NAME, "annotations": {}},
                "spec": {
                    "title": TITLE,
                    "slug": SLUG,
                    "template": "",
                    "cover": COVER or "",
                    "deleted": False,
                    "publish": False,
                    "pinned": bool(PINNED) if PINNED is not None else False,
                    "allowComment": True,
                    "visible": "PUBLIC",
                    "priority": int(PRIORITY) if PRIORITY is not None else 0,
                    "excerpt": {"autoGenerate": False, "raw": EXCERPT},
                    "categories": CATS,
                    "tags": tag_names,
                    "htmlMetas": []
                }
            },
            "content": content_payload
        }
        st_c, res_c = api_req("POST", "/apis/api.console.halo.run/v1alpha1/posts", create_body)
        if st_c not in (200, 201):
            raise RuntimeError(f"Create post failed ({st_c}): {res_c}")
        action = "CREATED"
    else:
        st_u1, res_u1 = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/posts/{POST_NAME}/content", content_payload)
        if st_u1 != 200:
            raise RuntimeError(f"Update content failed ({st_u1}): {res_u1}")
        for _att in range(5):
            time.sleep(0.25 * (_att + 1))
            st_g2, cur_post = api_req("GET", f"/apis/content.halo.run/v1alpha1/posts/{POST_NAME}")
            cur_post["spec"]["title"] = TITLE
            cur_post["spec"]["slug"] = SLUG
            cur_post["spec"]["excerpt"] = {"autoGenerate": False, "raw": EXCERPT}
            if COVER is not None:
                cur_post["spec"]["cover"] = COVER
            if PINNED is not None:
                cur_post["spec"]["pinned"] = bool(PINNED)
            if PRIORITY is not None:
                cur_post["spec"]["priority"] = int(PRIORITY)
            if CATS:
                cur_post["spec"]["categories"] = CATS
            if tag_names:
                cur_post["spec"]["tags"] = tag_names
            st_u2, res_u2 = api_req("PUT", f"/apis/content.halo.run/v1alpha1/posts/{POST_NAME}", cur_post)
            if st_u2 == 200:
                break
            if st_u2 != 409:
                raise RuntimeError(f"Update metadata failed ({st_u2}): {res_u2}")
        else:
            raise RuntimeError(f"Update metadata 409 conflict persisted: {res_u2}")
        action = "UPDATED"

    st_pub, res_pub = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/posts/{POST_NAME}/publish")
    if st_pub != 200:
        raise RuntimeError(f"Publish failed ({st_pub}): {res_pub}")
    sp_out = res_pub.get("spec", {})
    print(f"[publish-halo] {action} & PUBLISHED Post {POST_NAME} (/archives/{SLUG}) -> pinned={sp_out.get('pinned')}, priority={sp_out.get('priority')}, releaseSnapshot={sp_out.get('releaseSnapshot')}")

def publish_single_page_item(item):
    PAGE_NAME = item["post_name"]
    SLUG = item["slug"]
    TITLE = item["title"]
    EXCERPT = item["description"]
    content_payload = {
        "raw": item["html"],
        "content": item["html"],
        "rawType": "HTML"
    }
    st_get, cur_page = api_req("GET", f"/apis/content.halo.run/v1alpha1/singlepages/{PAGE_NAME}")
    if st_get == 404:
        create_body = {
            "page": {
                "apiVersion": "content.halo.run/v1alpha1",
                "kind": "SinglePage",
                "metadata": {"name": PAGE_NAME, "annotations": {}},
                "spec": {
                    "title": TITLE,
                    "slug": SLUG,
                    "template": "",
                    "cover": "",
                    "deleted": False,
                    "publish": False,
                    "pinned": False,
                    "allowComment": False,
                    "visible": "PUBLIC",
                    "priority": 0,
                    "excerpt": {"autoGenerate": False, "raw": EXCERPT},
                    "htmlMetas": []
                }
            },
            "content": content_payload
        }
        st_c, res_c = api_req("POST", "/apis/api.console.halo.run/v1alpha1/singlepages", create_body)
        if st_c not in (200, 201):
            raise RuntimeError(f"Create singlepage failed ({st_c}): {res_c}")
        action = "CREATED"
    else:
        st_u1, res_u1 = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/singlepages/{PAGE_NAME}/content", content_payload)
        if st_u1 != 200:
            raise RuntimeError(f"Update singlepage content failed ({st_u1}): {res_u1}")
        for _att in range(5):
            time.sleep(0.25 * (_att + 1))
            st_g2, cur_page = api_req("GET", f"/apis/content.halo.run/v1alpha1/singlepages/{PAGE_NAME}")
            cur_page["spec"]["title"] = TITLE
            cur_page["spec"]["slug"] = SLUG
            cur_page["spec"]["excerpt"] = {"autoGenerate": False, "raw": EXCERPT}
            st_u2, res_u2 = api_req("PUT", f"/apis/content.halo.run/v1alpha1/singlepages/{PAGE_NAME}", cur_page)
            if st_u2 == 200:
                break
            if st_u2 != 409:
                raise RuntimeError(f"Update singlepage metadata failed ({st_u2}): {res_u2}")
        else:
            raise RuntimeError(f"Singlepage 409 conflict persisted: {res_u2}")
        action = "UPDATED"

    st_pub, res_pub = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/singlepages/{PAGE_NAME}/publish")
    if st_pub != 200:
        raise RuntimeError(f"Publish singlepage failed ({st_pub}): {res_pub}")
    print(f"[publish-halo] {action} & PUBLISHED SinglePage {PAGE_NAME} (/{SLUG})")

    menu_item_name = item.get("menu_item_name")
    menu_display = item.get("menu_display_name")
    menu_after = item.get("menu_after", "menu-res")
    if menu_item_name and menu_display:
        st_mi, cur_mi = api_req("GET", f"/api/v1alpha1/menuitems/{menu_item_name}")
        target_ref = {"group": "content.halo.run", "kind": "SinglePage", "name": PAGE_NAME, "version": "v1alpha1"}
        if st_mi == 404:
            st_mc, res_mc = api_req("POST", "/api/v1alpha1/menuitems", {
                "apiVersion": "v1alpha1",
                "kind": "MenuItem",
                "metadata": {"name": menu_item_name},
                "spec": {
                    "children": [],
                    "displayName": menu_display,
                    "menuName": "primary",
                    "priority": 6,
                    "targetRef": target_ref
                }
            })
            if st_mc not in (200, 201):
                raise RuntimeError(f"Create MenuItem failed ({st_mc}): {res_mc}")
        else:
            cur_mi["spec"]["displayName"] = menu_display
            cur_mi["spec"]["targetRef"] = target_ref
            api_req("PUT", f"/api/v1alpha1/menuitems/{menu_item_name}", cur_mi)

        st_m, menu_obj = api_req("GET", "/api/v1alpha1/menus/primary")
        if st_m == 200:
            items_list = list(menu_obj.get("spec", {}).get("menuItems", []))
            if menu_item_name not in items_list:
                if menu_after in items_list:
                    idx = items_list.index(menu_after) + 1
                    items_list.insert(idx, menu_item_name)
                else:
                    items_list.append(menu_item_name)
                menu_obj["spec"]["menuItems"] = items_list
                st_mu, res_mu = api_req("PUT", "/api/v1alpha1/menus/primary", menu_obj)
                if st_mu != 200:
                    raise RuntimeError(f"Update primary Menu failed ({st_mu}): {res_mu}")
            for prio, mname in enumerate(items_list):
                st_i, mi_obj = api_req("GET", f"/api/v1alpha1/menuitems/{mname}")
                if st_i == 200 and mi_obj.get("spec", {}).get("priority") != prio:
                    mi_obj["spec"]["priority"] = prio
                    api_req("PUT", f"/api/v1alpha1/menuitems/{mname}", mi_obj)
            print(f"[publish-halo] ENSURED MenuItem {menu_item_name} ({menu_display}) in primary menu -> {items_list}")

try:
    if cfg.get("list_posts"):
        st_l, res_l = api_req("GET", "/apis/content.halo.run/v1alpha1/posts?size=100")
        for it in res_l.get("items", []):
            sp = it.get("spec", {})
            print(f"  {it['metadata']['name']:38s} | slug={sp.get('slug',''):36s} | pub={str(sp.get('publish')):5s} | pinned={str(sp.get('pinned')):5s} | prio={sp.get('priority',0):2d} | {sp.get('title','')}")
        sys.exit(0)

    if cfg.get("unpublish_only"):
        for pname in [x.strip() for x in cfg["post_name"].split(",") if x.strip()]:
            st_u, res_u = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/posts/{pname}/unpublish")
            if st_u != 200:
                raise RuntimeError(f"Unpublish {pname} failed ({st_u}): {res_u}")
            print(f"[publish-halo] UNPUBLISHED {pname}")
        sys.exit(0)

    for item in cfg.get("items", []):
        if item.get("single_page"):
            publish_single_page_item(item)
        else:
            publish_post_item(item)
finally:
    try: os.unlink("/tmp/halo_pub_job.json")
    except Exception: pass
"""


def build_item_from_spec(spec):
    if spec.get("single_page"):
        html_text = open(spec["html"], encoding="utf-8").read()
        return {
            "single_page": True,
            "post_name": spec["post_name"],
            "slug": spec["slug"],
            "title": spec["title"],
            "description": spec.get("description", ""),
            "html": html_text,
            "menu_item_name": spec.get("menu_item_name", ""),
            "menu_display_name": spec.get("menu_display_name", ""),
            "menu_after": spec.get("menu_after", "menu-res"),
        }
    md_text = open(spec["md"], encoding="utf-8").read()
    html_text = open(spec["html"], encoding="utf-8").read()
    meta, body = parse_frontmatter(md_text)
    cats = [c.strip() for c in (spec.get("categories") or "cat-vps").split(",") if c.strip()]
    return {
        "single_page": False,
        "post_name": spec["post_name"],
        "slug": spec["slug"],
        "title": meta["title"],
        "description": meta["description"],
        "categories": cats,
        "tag_specs": parse_tag_specs(spec.get("tags", "")),
        "cover": spec.get("cover"),
        "pinned": spec.get("pinned"),
        "priority": spec.get("priority"),
        "raw_md": body,
        "html": html_text,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-name", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--html", default="")
    ap.add_argument("--categories", default="cat-vps")
    ap.add_argument("--tags", default="")
    ap.add_argument("--cover", default=None)
    ap.add_argument("--pinned", action=argparse.BooleanOptionalAction, default=None)
    ap.add_argument("--priority", type=int, default=None)
    ap.add_argument("--single-page", action="store_true")
    ap.add_argument("--menu-item-name", default="")
    ap.add_argument("--menu-display-name", default="")
    ap.add_argument("--menu-after", default="menu-res")
    ap.add_argument("--batch-json", default="")
    ap.add_argument("--unpublish-only", action="store_true")
    ap.add_argument("--list-posts", action="store_true")
    ap.add_argument("--ssh-host", default="vps8")
    ap.add_argument("--base-url", default="http://127.0.0.1:8091")
    ap.add_argument(
        "--cred-file",
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "private", "gatewave-halo-admin.txt")),
    )
    args = ap.parse_args()

    user, pw = read_credentials(args.cred_file)

    if args.list_posts:
        job = {"base_url": args.base_url, "username": user, "password": pw, "list_posts": True}
    elif args.unpublish_only:
        if not args.post_name:
            raise ValueError("--post-name is required with --unpublish-only")
        job = {"base_url": args.base_url, "username": user, "password": pw, "post_name": args.post_name, "unpublish_only": True}
    elif args.batch_json:
        raw_specs = json.load(open(args.batch_json, encoding="utf-8"))
        items = [build_item_from_spec(s) for s in raw_specs]
        job = {"base_url": args.base_url, "username": user, "password": pw, "items": items}
    elif args.single_page:
        if not (args.post_name and args.slug and args.title and args.html):
            raise ValueError("--post-name, --slug, --title, and --html are required with --single-page")
        item = build_item_from_spec({
            "single_page": True,
            "post_name": args.post_name,
            "slug": args.slug,
            "title": args.title,
            "description": args.description,
            "html": args.html,
            "menu_item_name": args.menu_item_name,
            "menu_display_name": args.menu_display_name,
            "menu_after": args.menu_after,
        })
        job = {"base_url": args.base_url, "username": user, "password": pw, "items": [item]}
    else:
        if not (args.post_name and args.slug and args.md and args.html):
            raise ValueError("--post-name, --slug, --md, and --html are required for publishing")
        item = build_item_from_spec({
            "single_page": False,
            "post_name": args.post_name,
            "slug": args.slug,
            "md": args.md,
            "html": args.html,
            "categories": args.categories,
            "tags": args.tags,
            "cover": args.cover,
            "pinned": args.pinned,
            "priority": args.priority,
        })
        job = {"base_url": args.base_url, "username": user, "password": pw, "items": [item]}

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(job, tf, ensure_ascii=False)
        local_job = tf.name

    try:
        subprocess.check_call(["scp", "-q", local_job, f"{args.ssh_host}:/tmp/halo_pub_job.json"])
        subprocess.run(["ssh", "-o", "BatchMode=yes", args.ssh_host, "python3", "-"], input=REMOTE_RUNNER.encode("utf-8"), check=True)
    finally:
        if os.path.exists(local_job):
            os.unlink(local_job)


if __name__ == "__main__":
    main()
