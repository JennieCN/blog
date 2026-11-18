#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Publish, update, pin, or unpublish a post on Halo CMS on vps8 (127.0.0.1:8091).
Credentials are read strictly from private/gatewave-halo-admin.txt or environment variables
(NEVER hardcoded in repository scripts).

Usage (publish/update + optional pin):
  python3 scripts/publish-halo.py \
    --post-name post-meowvps-official-merchants-2026h2 \
    --slug meowvps-official-merchants-2026h2 \
    --md src/content/vps/meowvps-official-merchants-2026h2.md \
    --html /tmp/vol2.html \
    --pinned --priority 20 \
    --categories cat-vps \
    --tags "VPS:tag-vps,测评:tag-review,线路:tag-route,落地:tag-egress,家宽:tag-isp,组网:tag-networking,NodeQuality:tag-nodequality"

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


REMOTE_RUNNER = r"""
import os, sys, subprocess, re, json, base64, time, urllib.request, urllib.parse, urllib.error, http.cookiejar

cfg = json.load(open("/tmp/halo_pub_job.json", encoding="utf-8"))
BASE = cfg["base_url"]
POST_NAME = cfg["post_name"]

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

try:
    if cfg.get("list_posts"):
        st_l, res_l = api_req("GET", "/apis/content.halo.run/v1alpha1/posts?size=100")
        for it in res_l.get("items", []):
            sp = it.get("spec", {})
            print(f"  {it['metadata']['name']:38s} | slug={sp.get('slug',''):36s} | pub={str(sp.get('publish')):5s} | pinned={str(sp.get('pinned')):5s} | prio={sp.get('priority',0):2d} | {sp.get('title','')}")
        sys.exit(0)

    if cfg.get("unpublish_only"):
        for pname in [x.strip() for x in POST_NAME.split(",") if x.strip()]:
            st_u, res_u = api_req("PUT", f"/apis/api.console.halo.run/v1alpha1/posts/{pname}/unpublish")
            if st_u != 200:
                raise RuntimeError(f"Unpublish {pname} failed ({st_u}): {res_u}")
            print(f"[publish-halo] UNPUBLISHED {pname}")
        sys.exit(0)

    SLUG = cfg["slug"]
    TITLE = cfg["title"]
    EXCERPT = cfg["description"]
    CATS = cfg["categories"]
    TAG_SPECS = cfg["tag_specs"]
    PINNED = cfg.get("pinned")
    PRIORITY = cfg.get("priority")

    # Ensure tags exist
    tag_names = []
    for disp, tname in TAG_SPECS:
        st, existing = api_req("GET", f"/apis/content.halo.run/v1alpha1/tags/{tname}")
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
        "raw": cfg["raw_md"],
        "content": cfg["html"],
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
                    "cover": "",
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
    print(f"[publish-halo] {action} & PUBLISHED {POST_NAME} (/archives/{SLUG}) -> pinned={sp_out.get('pinned')}, priority={sp_out.get('priority')}, releaseSnapshot={sp_out.get('releaseSnapshot')}")
finally:
    try: os.unlink("/tmp/halo_pub_job.json")
    except Exception: pass
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-name", default="")
    ap.add_argument("--slug", default="")
    ap.add_argument("--md", default="")
    ap.add_argument("--html", default="")
    ap.add_argument("--categories", default="cat-vps")
    ap.add_argument("--tags", default="")
    ap.add_argument("--pinned", action=argparse.BooleanOptionalAction, default=None)
    ap.add_argument("--priority", type=int, default=None)
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
        job = {"base_url": args.base_url, "username": user, "password": pw, "post_name": "", "list_posts": True}
    elif args.unpublish_only:
        if not args.post_name:
            raise ValueError("--post-name is required with --unpublish-only")
        job = {"base_url": args.base_url, "username": user, "password": pw, "post_name": args.post_name, "unpublish_only": True}
    else:
        if not (args.post_name and args.slug and args.md and args.html):
            raise ValueError("--post-name, --slug, --md, and --html are required for publishing")
        md_text = open(args.md, encoding="utf-8").read()
        html_text = open(args.html, encoding="utf-8").read()
        meta, body = parse_frontmatter(md_text)

        cats = [c.strip() for c in args.categories.split(",") if c.strip()]
        tag_specs = []
        for item in args.tags.split(","):
            item = item.strip()
            if not item:
                continue
            if ":" in item:
                disp, tname = item.split(":", 1)
                tag_specs.append([disp.strip(), tname.strip()])
            else:
                tag_specs.append([item, f"tag-{item.lower()}"])

        job = {
            "base_url": args.base_url,
            "username": user,
            "password": pw,
            "post_name": args.post_name,
            "slug": args.slug,
            "title": meta["title"],
            "description": meta["description"],
            "categories": cats,
            "tag_specs": tag_specs,
            "pinned": args.pinned,
            "priority": args.priority,
            "raw_md": body,
            "html": html_text,
        }

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
