#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Volume 1 companion post:
  src/content/vps/nodeseek-merchant-reviews-2026h2.md (templated -> /tmp/article_templated.md)

Covers all 61 MeowVPS newly-collected / recently-promoted merchants, 457 NodeSeek community reviews,
64 official MeowVPS vendor review links, 2 horizontal shootouts, 2 standalone home-broadband archives,
and 319 collapsible terminal benchmark reports.
"""
import argparse, json, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from part_rem29 import emit_rem29
from taxonomy_guide import render_taxonomy_markdown
from parse_vol2_all import parse_blog_article

DEFAULT_DATA = os.path.abspath(os.path.join(HERE, "..", "..", "..", "data", "vps-reviews-202611"))
DATA_ROOT = os.environ.get("VPS_DATA_DIR") or (DEFAULT_DATA if os.path.isdir(DEFAULT_DATA) else "/tmp")
POSTS_DIR = os.path.join(DATA_ROOT, "posts") if os.path.isdir(os.path.join(DATA_ROOT, "posts")) else "/tmp"
NQ_DIR = os.path.join(DATA_ROOT, "nqfull") if os.path.isdir(os.path.join(DATA_ROOT, "nqfull")) else "/tmp/nqfull"


# ---------- Helpers ----------
def dec(u):
    return urllib.parse.unquote(u.split('jump?to=')[1]) if 'jump?to=' in u else u


def load(k):
    base = k[:-2] if k.endswith('-1') else k
    for p in (os.path.join(POSTS_DIR, f'post_post-{k}.json'), os.path.join(POSTS_DIR, f'post_post-{base}.json')):
        if os.path.exists(p):
            return json.load(open(p, encoding='utf-8'))
    raise FileNotFoundError(k)


def nq_of(k):
    d = load(k)
    for l in d.get('links', []):
        l = dec(l)
        if 'nodequality.com/r/' in l:
            tok = l.rstrip('/').split('/')[-1]
            return tok, 'https://nodequality.com/r/' + tok
    return None, None


def tq_of(k):
    d = load(k)
    out = []
    for l in d.get('links', []):
        l = dec(l)
        for tok in re.findall(r'tcpquality\.ibsgss\.uk/r/([A-Za-z0-9_\-]+)', l):
            u = 'https://tcpquality.ibsgss.uk/r/' + tok
            if u not in out:
                out.append(u)
    return out


def _headers(t):
    lines = t.split('\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(('####', '++++', '****'))]
    if not idx:
        return [t.strip()]
    segs = []
    for n, i in enumerate(idx):
        j = idx[n + 1] if n + 1 < len(idx) else len(lines)
        seg = '\n'.join(lines[i:j]).strip()
        if seg:
            segs.append(seg)
    return segs


def report(tok):
    p = os.path.join(NQ_DIR, f'nq_{tok}.txt')
    if not os.path.exists(p):
        return None
    segs = _headers(open(p, encoding='utf-8').read())
    out = []
    for s in segs:
        if len(s) < 200:
            continue
        if s in out:
            continue
        out.append(s)
    body = '\n\n'.join(out).strip()
    if '未检测基本信息' in body and len(body) < 1600:
        return None
    return body or None


def date_of(k):
    return load(k)['date'][:10]


def author_of(k):
    t = load(k)['text']
    return t.split('楼主')[0].strip()


def memo_of(k):
    t = load(k)['text']
    head = t
    for marker in [
        '💻基本信息', 'IPv4回程', '🎬IP质量', '配置：',
        '########################################################################',
        '++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++',
        '-------------------------------------VPS融合怪',
        '---------------------基础信息查询',
    ]:
        i = head.find(marker)
        if i > 0:
            head = head[:i]
    lines = [l.strip() for l in head.split('\n')]
    keep = []
    for l in lines:
        if not l or l == '#0':
            continue
        if re.match(r'^.+楼主(博主|临时禁言|违规禁止|管理员|\s)*$', l):
            continue
        if re.match(r'^\d+\s*(day|days|h|min|hour|hours|month|months|year|s)\b.*\bin\s+\S+', l):
            continue
        if re.match(r'^(\d+\s*)+$', l) and len(l) <= 12:
            continue
        keep.append(l)
    return ' '.join(keep)


def safe_truncate_cell(s, max_len=280):
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > max_len:
        cut = s[:max_len]
        cut = re.sub(r'https?://\S*$', '', cut).rstrip()
        s = cut + '…'
    s = s.rstrip('\\').replace('|', '\\|')
    return s


def plink(k):
    return 'https://www.nodeseek.com/post-%s-1' % k.replace('post-', '').replace('-1', '')


def _wrap(body):
    body = body.replace('```', "'''")
    out = []
    for line in body.split('\n'):
        while len(line) > 100:
            out.append(line[:100])
            line = line[100:]
        out.append(line)
    return '\n'.join(out).strip()


def _tabs(k):
    tabs = load(k).get('tabs') or []
    segs = []
    for t in tabs:
        t = (t or '').strip()
        if len(t) < 200 or t in segs:
            continue
        segs.append(t)
    return _wrap('\n\n'.join(segs))


def _inline(k):
    t = load(k).get('text') or ''
    lines = t.split('\n')
    idx = []
    for i, l in enumerate(lines):
        ls = l.lstrip()
        if ls.startswith(('+' * 20, '#' * 20, '*' * 20)):
            if '体检报告' in ls or (i + 1 < len(lines) and '体检报告' in lines[i + 1]):
                idx.append(i)
    if not idx:
        return ''
    segs = []
    for n, i in enumerate(idx):
        j = idx[n + 1] if n + 1 < len(idx) else len(lines)
        chunk_lines = [cl for cl in lines[i:j] if not re.match(r'^\s*0\s*$', cl)]
        seg = '\n'.join(chunk_lines).strip()
        if len(seg) > 200 and seg not in segs:
            segs.append(seg)
    return _wrap('\n\n'.join(segs))


def _has_net(t):
    return '网络质量体检报告' in t or t.lstrip().startswith('****')


def _tq_links(k):
    t = load(k).get('text') or ''
    out = []
    for tok in re.findall(r'tcpquality\.ibsgss\.uk/r/([A-Za-z0-9_\-]+)', t):
        u = 'https://tcpquality.ibsgss.uk/r/' + tok
        if u not in out:
            out.append(u)
    return out


def format_meow_official_block(slug, summary_bullets):
    art = parse_blog_article(slug)
    lines = [
        f"- **猫猫官方专测原文**：[{art['title']}]({art['url']})（发布日期：`{art['date']}`）",
    ]
    for b in summary_bullets:
        lines.append(f"  - {b}")
    lines.append("")
    assert art["combined_pre"], f"Expected terminal <pre> block in {slug}"
    pre_clean = _wrap(art["combined_pre"])
    n_lines = len(pre_clean.splitlines())
    lines.extend([
        "<details>",
        f"<summary>展开查看猫猫专测终端报告原文（摘录 {art['pre_kept_count']}/{art['pre_total_count']} 段 · 共 {n_lines} 行）</summary>",
        "",
        "```text",
        pre_clean,
        "```",
        "",
        "</details>",
        "",
    ])
    return "\n".join(lines) + "\n"


def build_vol1(out_path='/tmp/article_templated.md'):
    BODY_OUT = []

    def w(s=''):
        BODY_OUT.append(s)

    def tq_block(k, note=None):
        tqs = _tq_links(k) or tq_of(k)
        if not tqs:
            return
        links = '、'.join('[%s](%s)' % (t.rsplit('/r/', 1)[1], t) for t in tqs)
        if note:
            w('TcpQuality 报告：%s。%s' % (links, note))
        else:
            w('TcpQuality 报告：%s。报告页只渲染回程、大包、UDP、教育网、国际互联和单线程测速的图片，没有可复制的文本，具体数据请看原帖贴图。' % links)
        w()

    def review(k, product, note='', extra='', tq_note=None):
        d = load(k)
        tok, url = nq_of(k)
        memo = safe_truncate_cell(memo_of(k), 280)
        w('#### %s · %s' % (d['title'], author_of(k)))
        w()
        w('| 项 | 内容 |')
        w('| --- | --- |')
        w('| 产品 | %s |' % product)
        w('| 发帖时间 | %s |' % date_of(k))
        w('| 作者 | %s |' % author_of(k))
        if memo:
            w('| 作者说明 | %s |' % memo)
        if extra:
            w('| 补充 | %s |' % extra.rstrip('\\').replace('|', '\\|'))
        w('| 原帖 | [%s](%s) |' % (d['title'].rstrip('\\').replace('|', '\\|'), plink(k)))
        w()
        body = report(tok) if tok else None
        tabs = _tabs(k)
        inline = _inline(k)
        if body and not _has_net(body):
            if tabs and _has_net(tabs):
                body = tabs
            elif inline and _has_net(inline):
                body = inline
        elif not body:
            body = tabs or inline or None
        if body and not _has_net(body):
            note = (note + ' ' if note else '') + '原报告只包含硬件与 IP 质量两项，没有网络质量与回程路由数据。'
        if body:
            n_lines = len(body.splitlines())
            if tok:
                w('NodeQuality 报告（[在线报告页](%s)）：' % url)
            else:
                w('NodeQuality 报告（帖子正文内嵌，无单独报告页链接）：')
            w()
            w('<details>')
            w(f'<summary>展开查看 NodeQuality 报告原文（共 {n_lines} 行）</summary>')
            w()
            w('```text')
            w(body)
            w('```')
            w()
            w('</details>')
            w()
        elif tok:
            w('NodeQuality 报告（[%s](%s)）：报告页只显示“未检测基本信息”占位，没有硬件与网络数据。' % (tok, url))
            w()
        else:
            w('这条帖子没有 NodeQuality 报告。')
            w()
        tq_block(k, tq_note)
        if note:
            w(note)
            w()

    # ---------- 1. Execute Round 1 merchant body sections ----------
    orig_lines = open(os.path.join(HERE, 'round1_build_article.py'), encoding='utf-8').read().splitlines()
    start_idx = next(i for i, l in enumerate(orig_lines) if l.startswith('# ---------- 1 六六云'))
    end_idx = next(i for i, l in enumerate(orig_lines) if l.startswith('# ---------- 30 无帖商家'))
    round1_code = '\n'.join(orig_lines[start_idx:end_idx])
    exec(compile(round1_code, 'round1_sections.py', 'exec'), {
        'w': w, 'review': review, 'load': load, 'date_of': date_of,
        'author_of': author_of, 'memo_of': memo_of, 're': re
    })

    # ---------- 2. Execute Round 2 remaining 29 merchants ----------
    emit_rem29(w, review)

    # ---------- 2.5 Standalone MeowVPS Non-Directory Home-Broadband Archives (2 Articles) ----------
    w('## 猫猫博客非目录特殊家宽留档（2 篇）')
    w()
    w('> 🧭 [↑ 返回顶部分类导览]({{ANCHOR:选机分类体系总览（猫猫博客口径）}}) ｜ 📌 说明：以下 2 篇为猫猫博客专栏发布的非公开售卖/非标特殊真家宽留档，因不对应常驻商家目录而单独归档于此，从而实现 `meowvps.com/blog/` 全站测评博文 **100% 完整索引**。')
    w()
    w('### 留档一：AWS Wavelength 日本 KDDI 5Gbps 家宽测评（2026-02-11）')
    w()
    w(format_meow_official_block('wavelength', [
        '**架构与带宽**：极其罕见的 AWS Wavelength 边缘节点方案，采用“AWS 前置入站 IP + 纯正日本 KDDI 5Gbps 家宽出站 IP”双 IP 结构（分普通入口与精品入口），日本线路机（DMIT JP Pro / RFC JP CO / BageVM JP 等）拉取可跑出千兆级家宽吞吐。',
        '**风险与定位**：非 AWS 官方正价常驻品，偶有掉线需联系渠道重开实例（重开会丢失盘内数据，切勿存放生产数据）；晚高峰电信/移动直连丢包重，推荐纯落地中转使用。',
    ]))
    w('### 留档二：神秘美国 AT&T 1Gbps 双栈家宽小鸡留档（2026-04-23）')
    w()
    w(format_meow_official_block('4brw6mgm4w', [
        '**网络与 IP 纯净度**：双栈完美美国 AT&T 真家宽，上行高达 **1Gbps**、下行约 **700Mbps**，距洛杉矶仅约 **38ms**，常见美西优化线路机中转即可轻松拉满 500~700Mbps。',
        '**怪兽级宿主机硬件**：搭载桌面旗舰 **i9-13900K** + 100GB 高速 NVMe（`fio` 4K 随机读写近 **1GB/s**、IOPS 近 **25 万**），属猫猫博客留档过的硬件天花板级非标私家宽样本（未公开购买渠道）。',
    ]))

    # ---------- 3. Zero-post merchants section ----------
    w('## 测评区没有对应帖子的商家')
    w()
    w(f'> 🧭 [↑ 返回顶部分类导览]({{{{ANCHOR:选机分类体系总览（猫猫博客口径）}}}})')
    w()
    w('MeowVPS 商家目录里标记“收集中”的 57 家商家中，以下 **2 家**在 NodeSeek 测评区（review 版块）及猫猫博客专栏中均暂未检索到公开测评帖：')
    w()
    w('- **CoffeeHost**：按 `coffeehost`、`coffee host` 检索，测评区与猫猫专栏均无公开测评帖。')
    w('- **筋斗云**：按 `jindouyun`、`筋斗云` 检索，测评区与猫猫专栏均无公开测评帖。')
    w()
    w('这两家可能只在讨论区零星提及或尚未开放测评，暂列索引供后续追踪（注：同样在 NodeSeek 测评区无第三方帖的 **[NexKr]({{ANCHOR:NexKr}})** 已在上方补入猫猫博客 11 月 11 日发布的韩国 SKB 官方专测摘要）。')
    w()

    # ---------- 4. Methodology & internal links ----------
    w('## 收录方法与口径')
    w()
    w('- 检索路径：先在 NodeSeek 测评区按商家名、中文名与代表产品名定位帖子，再解析帖子里的 NodeQuality / TcpQuality 链接与折叠分区，最后从报告页逐项抓取原文；对猫猫博客已发布独立专测的 39 家商家（共 **64 篇**商家专测 + **2 篇**横评 + **2 篇**特殊家宽留档），同步附上全部 `meowvps.com/blog/...` 官方评测链接。')
    w('- NQ 原文来自 `nodequality.com/r/<token>` 报告页，按“基本信息 / IP 质量 / 网络质量 / 回程路由”四个分区逐个复制后拼接，保留报告页上的分隔线与原始排版，并统一收入可展开折叠块（点击即可展开复制全文）。')
    w('- 少数帖子把 NQ 报告直接嵌在正文的折叠分区或代码块里（没有单独的报告页链接），这类条目按正文分区顺序提取原文并注明。')
    w('- 报告时间取脚本输出的“报告时间”，与发帖时间可能相差几分钟到几小时。')
    w('- TQ 报告页（`tcpquality.ibsgss.uk/r/<token>`）按 `section` 渲染图片，没有文本层，因此保留在线报告链接并说明看原帖贴图。')
    w('- 部分 NQ 报告本身只有“未检测基本信息”占位，说明当时脚本未采到硬件信息，已如实注明，不贴空代码块。')
    w('- 对近半年（5 月中旬至今）无公开新帖的 5 家“收集中”商家（DataOnline、LightNode、Langya、HostBlazer、VMVM），已附上 2026 年 3—4 月的历史公开测评并标注停运/跑路警示，确保 MeowVPS 57 家“收集中”目录无遗漏。')
    w()
    w('相关阅读：[VPS 测评怎么读](/archives/reading-vps-reviews)、[VPS 线路与落地怎么搭](/archives/relay-and-egress-guide)、[Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback)。')

    # ---------- 4.5 Post-process BODY_OUT: inject 5 newly extracted regional lines, upgrade NexKr, fold PPFlight TQ, inject full multi-review MeowVPS nav ----------
    def _m(slugs_labels, status):
        return ([(lbl, f'https://meowvps.com/blog/{sl}/') for lbl, sl in slugs_labels], status)

    MEOWVPS_VENDOR_META = {
        '六六云 666Clouds': _m([('菲律宾双ISP', '666cloudsph'), ('韩国双ISP', '666cloudskr1'), ('英国原生IP', '666cloudsuk1')], '收集中'),
        '干杯云 USVPS24': _m([('AT&T家宽初测', 'usvps243'), ('AT&T商宽PRO', 'usvps24pro'), ('商宽PRO升级复测', 'usvps24proup')], '已正式收录'),
        'Tamago Network': _m([('香港WTT商宽', 'tamagowtt'), ('香港HKT新品', 'tamagohkt')], '已正式收录'),
        'JCloudHosting（西班牙家宽）': _m([('西班牙家宽专测', 'jcloudhosting')], '已正式收录'),
        'PanstarCloud': _m([('美西DC2三网优化', 'panstarusdc2'), ('德国三网9929', 'panstarde')], '收集中'),
        'VPS.TAXI': _m([('新加坡专测', 'vpstaxisg')], '收集中'),
        'FlawlessNode': _m([('洛杉矶优化初测', 'flawlessnode'), ('优化复测', 'flawlessnodere'), ('PRO 9929初测', 'flawlessnode9929'), ('PRO 9929复测', 'flawlessnode9929re'), ('Basic 4837', 'flawlessnodebasic')], '已正式收录'),
        'Bocchi': _m([('达拉斯高性能', 'bocchi'), ('东京9950X', 'bocchijp')], '已正式收录'),
        'ATTVPS': _m([('AT&T家宽初测', 'attvps'), ('AT&T家宽复测', 'attvpsre')], '已正式收录'),
        'NexKr': _m([('韩国SKB家宽', 'nexkrskb')], '已正式收录'),
        'RackNerd': ([], '收集中'),
        'BuyVM': ([], '收集中'),
        'HostHatch': ([], '收集中'),
        'JTTI': ([], '收集中'),
        'wawo（哇沃主机）': ([], '收集中'),
        'PPFlight': ([], '收集中'),
        'HostDzire': ([], '收集中'),
        'JDIDC': ([], '收集中'),
        'NOSLA': ([], '收集中'),
        'Peekabo Networks': ([], '收集中'),
        'BreadCloud（面包云）': ([], '收集中'),
        'DediRock': ([], '收集中'),
        'HaloCloud': ([], '收集中'),
        'HHost': ([], '收集中'),
        'HighEndNetwork': ([], '收集中'),
        'HKCloudX': ([], '收集中'),
        'KFCHost': ([], '收集中'),
        'LamHosting': ([], '收集中'),
        'NoBrand': ([], '收集中'),
        'VmShell': ([], '收集中'),
        'BeroHost': _m([('德国性能机专测', 'berohost')], '已正式收录'),
        'BlossomHost': _m([('得州NetWest家宽', 'blossomhostnetwest'), ('华盛顿Verizon家宽', 'blossomhostverizon'), ('西雅图Wave ISP', 'blossomhoswave')], '收集中'),
        'CloudSilk（白丝云）': _m([('全线专测', 'cloudsilk')], '收集中'),
        'FXTRANSIT': _m([('美西NOVA优化', 'fxtransitusnova'), ('日本Tier1国际', 'fxtransitjpt1')], '收集中'),
        'GatewaySentry': _m([('全线专测', 'gatewaysentry')], '收集中'),
        'GoldCloud': _m([('美西4837专测', 'goldcloudus')], '收集中'),
        'GoodlyCloud（吉云）': _m([('英国伦敦9929', 'goodlyclouduk'), ('美西4837双ISP', 'goodlycloudus')], '收集中'),
        'IPMELA': _m([('北卡Spectrum商宽', 'ipmelaspectrum')], '收集中'),
        'LazyCatCloud（懒猫云）': _m([('家宽与线路专测', 'lazycat')], '收集中'),
        'LegendVPS': _m([('新加坡专测', 'legendvpssg')], '收集中'),
        'LisaHost（丽萨主机）': _m([('双ISP住宅专测', 'lisahost')], '收集中'),
        'Misaka': _m([('德国柏林CN2 GIA', 'misakade'), ('俄罗斯莫斯科CN2 GIA', 'misakaru')], '收集中'),
        'OrangeVPS': _m([('新加坡专测', 'orangesg')], '收集中'),
        'RadoNet': _m([('日本SoftBank NAT', 'radonet'), ('日本So-net家宽', 'radonetsonet')], '收集中'),
        'ResidentialVPS': _m([('AT&T 1Gbps初测', 'residentialvps'), ('路易斯安那AT&T复测', 'residentialvpslouisiana')], '收集中'),
        'ShanDun Network': _m([('德国9929专测', 'shandunde9929')], '收集中'),
        'Terabix': _m([('大马柔佛Genoa专测', 'terabix')], '收集中'),
        'TOTHOST': _m([('越南VNPT家宽专测', 'tot')], '收集中'),
        'WebHorizon': _m([('新加坡Ryzen专测', 'webhorizon')], '收集中'),
        'WePC（车库云）': _m([('马来西亚家宽', 'wepc'), ('菲律宾原生IP', 'wepcph'), ('澳洲Exetel家宽', 'wepcau')], '收集中'),
        'WLX': _m([('香港9955HX独服', 'wlxhk9955hx')], '收集中'),
        'ZgoCloud': _m([('洛杉矶三网优化', 'zgo'), ('洛杉矶双ISP优化', 'zgocloudispvps')], '收集中'),
        'Zouter': _m([('香港BGP Global', 'zouterhk'), ('日本Global&大盘', 'zouterjp'), ('德国法兰克福Global', 'zouterde')], '收集中'),
        '艾云 iaClouds（破云 / Brea.cloud）': _m([('美国GGBOOM优化', 'iacloudsusenterprise'), ('德国三网9929', 'iacloudsde9929')], '收集中'),
        'DataOnline（近半年公开帖为 0 · 附 2026 年 4 月底测评）': _m([('越南专测', 'dataonline')], '收集中'),
        'LightNode（近半年公开帖为 0 · 附 2026 年 4 月测评）': _m([('菲律宾节点专测', 'lightnodeph')], '收集中'),
        'Langya（近半年公开帖为 0 · 附 2026 年 3 月测评）': _m([('落地机专测', 'langya')], '收集中'),
        'HostBlazer（已于 2026 年 4 月停运 · 附 3 月历史留档）': _m([('停运前历史专测', 'hostblazer')], '收集中·已停运'),
        'VMVM（已被标记违规跑路 · 附 2026 年 3 月历史留档）': _m([('跑路前历史专测', 'vmvm')], '收集中·已跑路'),
    }

    raw_body = '\n'.join(BODY_OUT)

    # 1) Inject 5 newly extracted regional official product lines into 六六云, WePC, and Zouter
    extra_666 = (
        "### 产品线五：韩国 SEJONG 双 ISP 与英国 GTT 原生 IP（猫猫官方专测）\n\n"
        + format_meow_official_block('666cloudskr1', [
            '**IP 与解锁表现**：上游直属韩国 **SEJONG**，原生静态家宽/商宽属性，韩国本土及国际流媒体完整解锁、滥用标记极少（注：韩国段存在被邻居波及触发 Google“送中”的通病风险，重度 Gemini/YouTube 用户需知悉）。',
            '**组网建议**：三网直连丢包严重不可用，定位纯落地；推荐用香港或日本线路机中转（延迟 30~60ms，可稳定拉起 200Mbps 端口）。1C1G 硬件仅适合做轻量代理出口。',
        ])
        + format_meow_official_block('666cloudsuk1', [
            '**带宽与中转**：上游直属 **GTT** 英国原生 IP（带部分家宽库标记），三网直连波动大，用德国法兰克福线路机中转延迟仅 **10~15ms**，可轻松跑满 **1Gbps** 大端口。',
            '**避坑提示**：受测段已出现 Google“送中”情况，且官网无统一退款条款（下单前请按不退款预期评估，优先月付试水）。',
        ])
    )
    assert '\n## 干杯云 USVPS24\n' in raw_body
    raw_body = raw_body.replace('\n## 干杯云 USVPS24\n', '\n' + extra_666 + '\n## 干杯云 USVPS24\n', 1)

    extra_wepc = (
        "### 产品线二：马来西亚家宽与菲律宾原生 IP 伪家宽（猫猫官方专测）\n\n"
        + format_meow_official_block('wepc', [
            '**定位与中转质量**：极少见的马来西亚本土纯落地家宽，三网不可直连；用新加坡或马来西亚前置（如 Evoxt MY / RFC SG）中转延迟低、重传极少，晚高峰可稳跑满 **90~95Mbps** 标称带宽，Claude / Gemini / 本土流媒体解锁全绿。',
        ])
        + format_meow_official_block('wepcph', [
            '**移动 Lumen 快乐 + BBIX 低延迟**：极其稀缺的菲律宾多库家宽标原生 IP。电信联通不可直连，但**中国移动走 Lumen 直连单线程即可跑满 50Mbps**；若用接入 BBIX 的香港线路机（如 DMIT / ISIF）中转，港菲延迟低至 **17ms**。1C0.5G 羸弱硬件仅作纯组网出口。',
        ])
    )
    assert '\n## WLX\n' in raw_body
    raw_body = raw_body.replace('\n## WLX\n', '\n' + extra_wepc + '\n## WLX\n', 1)

    extra_zouter = (
        "### 产品线三：德国法兰克福 Global 落地新品（猫猫官方专测）\n\n"
        + format_meow_official_block('zouterde', [
            '**网络与硬件**：定位欧洲大流量国际落地机（首发翻倍至 4TB），大陆直连丢包严重不可直连，用德国法兰克福优化机中转可轻松跑满 **1Gbps**；搭载 **EPYC 7K62** + 干净德国原生机房 IP，常规流媒体解锁齐全。',
            '**退款规则提醒**：24 小时内且双向流量 ≤30GB 支持无条件退（每月限 2 次；USDT 不支持原路提现，余额提现收 5% 手续费且最低 2 元）。',
        ])
    )
    assert '\n## 艾云 iaClouds（破云 / Brea.cloud）\n' in raw_body
    raw_body = raw_body.replace('\n## 艾云 iaClouds（破云 / Brea.cloud）\n', '\n' + extra_zouter + '\n## 艾云 iaClouds（破云 / Brea.cloud）\n', 1)

    # 2) Upgrade NexKr section with MeowVPS 2026-11-11 SKB review summary
    old_nexkr = (
        "## NexKr\n\n"
        "NexKr（韩国 SKB）也是 MeowVPS 新收录的商家。按商家名、产品名和“SKB”在 NodeSeek 测评区检索，没有找到对应帖子，因此本篇没有 NexKr 的条目。"
    )
    new_nexkr = (
        "## NexKr\n\n"
        "NexKr 是运营两年半的老牌韩国家宽商 `koreaisbest` 上线的新站（`nexkr.sh`），主营韩国 SK Broadband（SKB）大带宽真家宽落地机。NodeSeek 测评区暂未检索到第三方坛友帖，但猫猫博客已于 **2026-11-11** 发布完整专测（[商家NexKr 韩国SKB家宽产品 测评](https://meowvps.com/blog/nexkrskb/)，附 [Check.Place 网络体检报告](https://Report.Check.Place/net/3KMUA0CJ8.svg)），核心实测结论整理如下：\n\n"
        "- **IP 质量**：上游直属韩国 **SK Broadband（AS9318）** 原生真家宽 IP，常规流媒体与 AI 全家桶完整解锁，滥用标记极低，属韩国家宽顶端 IP 质量。（提醒：韩国段易因不当代理行为触发 Google“送中”，开机后请第一时间检查，商家支持 **7 天最多 2 次、30 天最多 4 次免费换 IP**，并附赠 **5 个自定义 DDNS 域名**。）\n"
        "- **带宽与组网路由**：给足 **2000Mbps 超大端口 + 60TB/月单向出站计费**；大陆直连为三网骨干半优化（电信 163 全天高丢包个位数速率，联通 `4837` / 移动 `CMI` 视省份可跑 200~300Mbps 或丢包，比较看脸），**定位应作为纯落地机配合日本或香港前置中转**——实测东京中转延迟 30~40ms、单线程约 700Mbps，香港中转 30~60ms、单线程 300~400Mbps，两地多线程均可跑满约 **1800Mbps**。\n"
        "- **硬件与政策**：Intel Xeon Platinum 8272CL（4C4G 够用级，不适合重度编译）+ 高速磁盘（可发工单免费扩容硬盘）；注册需验证手机号。"
    )
    assert old_nexkr in raw_body, "Could not locate old NexKr section!"
    raw_body = raw_body.replace(old_nexkr, new_nexkr, 1)

    # 3) Fold the single standalone TQ text block in PPFlight (post-978647)
    tq_marker = "这条帖子把 TQ 报告以文本形式贴了出来（报告时间 2026-10-12 16:42:32 CST），原文如下：\n\n```text\n"
    assert tq_marker in raw_body, "Could not locate PPFlight standalone TQ block!"
    idx_tq = raw_body.index(tq_marker) + len(tq_marker)
    idx_tq_end = raw_body.index("\n```\n", idx_tq)
    tq_content = raw_body[idx_tq:idx_tq_end]
    tq_lines = len(tq_content.splitlines())
    raw_body = (
        raw_body[:raw_body.index(tq_marker)]
        + "这条帖子把 TQ 报告以文本形式贴了出来（报告时间 2026-10-12 16:42:32 CST）：\n\n"
        + f"<details>\n<summary>展开查看 TcpQuality 文本报告原文（共 {tq_lines} 行）</summary>\n\n```text\n"
        + tq_content
        + "\n```\n\n</details>\n"
        + raw_body[idx_tq_end + len("\n```\n"):]
    )

    # 4) Inject top navigation & ALL MeowVPS official review links right below each merchant H2
    def inject_merchant_nav(match):
        h2_title = match.group(1).strip()
        if h2_title not in MEOWVPS_VENDOR_META:
            return match.group(0)
        links, st_label = MEOWVPS_VENDOR_META[h2_title]
        nav = "{{ANCHOR:选机分类体系总览（猫猫博客口径）}}"
        if links:
            links_md = " / ".join(f"[{lbl}]({u})" for lbl, u in links)
            bar = f"> 🧭 [↑ 返回顶部分类导览]({nav}) ｜ 📖 猫猫博客专测（{len(links)} 篇）：{links_md}（目录状态：{st_label}）"
        else:
            bar = f"> 🧭 [↑ 返回顶部分类导览]({nav}) ｜ 📌 MeowVPS 目录状态：{st_label}（暂无猫猫独立专测，以下为 NodeSeek 社区实测）"
        return f"## {h2_title}\n\n{bar}\n"

    body_text = re.sub(r'(?m)^## ([^\n]+)\n', inject_merchant_nav, raw_body)

    # ---------- 5. Parse body_text to build 100% accurate Summary Table ----------
    PRODUCT_SUMMARY = {
        '六六云 666Clouds': '美国 CN2 GIA、美西 4837/NTT 双 ISP、德国 9929、香港优化、菲律宾/韩国双 ISP、英国原生 IP',
        '干杯云 USVPS24': 'AT&T 商业宽带 PRO、二号线、加州 AT&T 静态家宽、Frontier（已正式收录）',
        'Tamago Network': '香港 WTT 商宽独立 IP、HKT NAT（500M/2500M）、WTT NAT（已正式收录）',
        'JCloudHosting（西班牙家宽）': '西班牙 KVM ECO / HIGH / RYZEN（已正式收录）',
        'PanstarCloud': 'LAX Premium DC2、德国 DEPro、香港 HK Pro / HKP / HKS、英国 UK Lite',
        'VPS.TAXI': '洛杉矶（512M/24 刀）、东京软银、新加坡、30 刀年付',
        'FlawlessNode': 'LAX Pro（9929 初测/复测）、LAX Basic Special（4837）（已正式收录）',
        'Bocchi': '东京 TYO-Pulse（9950X）、达拉斯 Pulse（已正式收录）',
        'ATTVPS': 'AT&T 美国静态家宽（猫猫初测与复测长文，已正式收录）',
        'NexKr': '韩国 SKB 2000Mbps 大带宽真家宽（猫猫官方专测，已正式收录）',
        'RackNerd': '黑五 1GB/2.5GB KVM、2023 黑五闪购、Buffalo NY、NL-Amsterdam、圣何塞、达拉斯',
        'BuyVM': '瑞士（卢森堡）KVM、拉斯维加斯 KVM + 存储块、存储块读写',
        'HostHatch': '香港 HK FLASH / 6C24G / 3C3G、韩国、洛杉矶大鸡、东京 4C16G',
        'JTTI': '香港 HK（$49/年）、日本东京 JP-1C-1G-50G',
        'wawo（哇沃主机）': '香港 HK-Simple / HK-One、香港 IPv6-only、台湾 IPv6、美国 US-Simple',
        'PPFlight': 'LIFT S1 / S2、Glide S、Plus-s、洛杉矶 CN2-GIA',
        'HostDzire': 'LAX 4C6G 24 刀年付、ColoCrossing、SFO 4C6G',
        'JDIDC': '美国 3 区 9929（4H8G）',
        'NOSLA': '圣何塞 SJC、圣何塞精品优化、洛杉矶 LAX、东京',
        'Peekabo Networks': '香港 HK（龙系三网精品）',
        'BreadCloud（面包云）': '美国 Slice、日本 Bite、新加坡 Crumb',
        'DediRock': '洛杉矶低价年付、纽约、Storage Promo 大盘鸡',
        'HaloCloud': '香港 Lite、新加坡、日本 Standard、台湾、洛杉矶 Akari',
        'HHost': '洛杉矶 LA China Optimized（换 IP 前后）',
        'HighEndNetwork': 'SeedNet Home Broadband、Seednet Lavender / Matcha、Hinet Sencha',
        'HKCloudX': '香港 BGP 优化（老 200M / 迁移 AMD）、MiniV6',
        'KFCHost': '日本 Tier1 Global RouteFlex、RouteFlex',
        'LamHosting': '德国 DE 9929、日本 JPCR-Zero / Japan、美国 USCR、台湾 HiNet-A、DECR-Zero',
        'NoBrand': '日本 Super Chicken / COGENT TYO / JP-TYO-1 / Super KFC / NewNB、沪日专线',
        'VmShell': '香港 CMIN2-WEBAPP / CMIN2.HK-Classic、澳门 CMIN2-IP.MO-Lite',
        'BeroHost': '德国十周年（12 欧 / 49 欧 / 89 欧）、XMAS 2025 69 欧、1 欧款（已正式收录）',
        'BlossomHost': '得州 Odessa NetWest 家宽、西雅图 Wave 10Gbps ISP、华盛顿 Verizon FiOS',
        'CloudSilk（白丝云）': '圣何塞大陆优化 BGP（4837）、圣何塞精品 9929、德国精品 9929、香港 CMI',
        'FXTRANSIT': '美西 US NOVA（CN2 GIA）、美国 T1、日本 T1 10G、香港 AXIS / Nova、新加坡 T1',
        'GatewaySentry': '洛杉矶 VPS-4 / CN2、荷兰 Ryzen 9 9950X',
        'GoldCloud': '香港三网优化 7K62 / CMI、香港 HK-DC2、洛杉矶 US-DC1（4837）',
        'GoodlyCloud（吉云）': '英国伦敦原生 IP（9929+CMIN2）、美国洛杉矶 NTT 双 ISP（4837）',
        'IPMELA': '美国北卡罗来纳州 Charter Spectrum 商宽 VPS/RDP',
        'LazyCatCloud（懒猫云）': '香港双栈 Lumen、新加坡狗妈、美西 4837 / 德国 9929、日韩新菲动态家宽 NAT',
        'LegendVPS': '新加坡 SG-Evo / SG-Lite、日本 JP-Spark、美国 US-LAX（注：11 月换老板开放退款）',
        'LisaHost（丽萨主机）': '美国 9929 双 ISP 住宅 IP、英国双 ISP、香港小鸡',
        'Misaka': '德国柏林 CN2 / PREM-Pro、莫斯科 CN2 GIA、新加坡 / 香港 / 台湾、西雅图 / 洛杉矶',
        'OrangeVPS': '新加坡促销款 / BASIC-AP-1、8C16G 活动鸡、香港 HK、日本 BASIC-AP-1',
        'RadoNet': '日本 KDDI / Rakuten / SoftBank 共享 NAT、So-net 家宽、Starlink 家宽、BIGLOBE',
        'ResidentialVPS': '美国加州/路易斯安那 Pro AT&T 家宽（$40/月，Windows RDP）',
        'ShanDun Network': '德国 DE 9929、英国 UK 9929 ISP、美国 Premium / 4837 ISP / NTT、香港 Standard',
        'Terabix': '马来西亚柔佛新山 Cloud VM Premium（AMD Genoa）',
        'TOTHOST': '越南河内 VNPT ISP · TOT K11、越南双 ISP 家宽 TOT GT',
        'WebHorizon': '新加坡 Ryzen-KVM-1GB（1C1G/15G）',
        'WePC（车库云）': '澳大利亚墨尔本 Exetel 家宽、马来西亚家宽、菲律宾原生 IP 伪家宽',
        'WLX': '香港荃湾 Ryzen 9 9955HX 与 Core Ultra 9 285HX + RTX 4070 独立服务器',
        'ZgoCloud': '洛杉矶 AMD 三网精品 / 双 ISP / Global / 黑五新段、香港 AMD Specials、大阪 IIJ',
        'Zouter': '香港 HK BGP Global（103 段）、日本东京 JP BGP Global、德国法兰克福 Global',
        '艾云 iaClouds（破云 / Brea.cloud）': '德国法兰克福三网 9929、洛杉矶 GGBOOM CN2 GIA、美西 GGBOOM 4837',
        'DataOnline（近半年公开帖为 0 · 附 2026 年 4 月底测评）': '越南河内 Cheap Cloud VPS 1（4 月底归档；11 月新帖仅登录可见）',
        'LightNode（近半年公开帖为 0 · 附 2026 年 4 月测评）': '沙特利雅得 / 菲律宾节点（4 月归档）',
        'Langya（近半年公开帖为 0 · 附 2026 年 3 月测评）': '美国芝加哥 GSL 落地机、香港落地机（3 月归档）',
        'HostBlazer（已于 2026 年 4 月停运 · 附 3 月历史留档）': '美国达拉斯 DAL Standard、免费 IPv6（4 月已失联停运）',
        'VMVM（已被标记违规跑路 · 附 2026 年 3 月历史留档）': '日本东京春季特别款、美国盐湖城 9950X（已标记违规跑路）',
    }

    h2_chunks = re.split(r'(?m)^## ', body_text)
    table_rows = []
    total_reviews = 0
    merchant_sections = 0

    for chunk in h2_chunks[1:]:
        h2_title = chunk.split('\n', 1)[0].strip()
        if h2_title in ('猫猫博客非目录特殊家宽留档（2 篇）', '测评区没有对应帖子的商家', '收录方法与口径'):
            continue
        merchant_sections += 1
        cnt = len(re.findall(r'(?m)^#### ', chunk))
        dates = sorted(re.findall(r'\| 发帖时间 \| (\d{4}-\d{2}-\d{2}) \|', chunk))
        total_reviews += cnt
        if cnt == 0:
            if h2_title == 'ATTVPS':
                cnt_str = '2（猫猫初测+复测）'
                dt_str = '08-31 ~ 11-09'
            elif h2_title == 'NexKr':
                cnt_str = '1（猫猫官方专测）'
                dt_str = '11-11'
            else:
                cnt_str = '0（测评区无帖）'
                dt_str = '—'
        else:
            d_min, d_max = dates[0][5:], dates[-1][5:]
            dt_str = d_min if d_min == d_max else f'{d_min} ~ {d_max}'
            if '近半年公开帖为 0' in h2_title or '停运' in h2_title or '跑路' in h2_title:
                cnt_str = f'0（附春季归档 {cnt} 篇）'
            else:
                cnt_str = str(cnt)
        prod = PRODUCT_SUMMARY.get(h2_title)
        assert prod, f'Missing PRODUCT_SUMMARY for {h2_title}'
        disp_name = h2_title.split('（近半年')[0].split('（已于')[0].split('（已被')[0]
        links, _ = MEOWVPS_VENDOR_META.get(h2_title, ([], ''))
        name_cell = f'[{disp_name}]({{{{ANCHOR:{h2_title}}}}})'
        if len(links) == 1:
            name_cell += f'（[猫猫专测]({links[0][1]})）'
        elif len(links) > 1:
            short_links = ' / '.join(f'[{lbl}]({u})' for lbl, u in links)
            name_cell += f'（猫猫专测：{short_links}）'
        table_rows.append(f'| {name_cell} | {prod} | {cnt_str} | {dt_str} |')

    table_rows.append('| [CoffeeHost]({{ANCHOR:测评区没有对应帖子的商家}}) | — | 0（暂无公开帖） | — |')
    table_rows.append('| [筋斗云]({{ANCHOR:测评区没有对应帖子的商家}}) | — | 0（暂无公开帖） | — |')

    taxonomy_md = render_taxonomy_markdown()
    total_meow_vendor_articles = sum(len(v[0]) for v in MEOWVPS_VENDOR_META.values())

    HEADER = [
        '---',
        'title: NodeSeek 商家测评汇总：MeowVPS 61 家新收录与转正商家的产品线与 NQ/TQ 原文（上卷）',
        f'description: 按猫猫博客（MeowVPS）选机分类体系（线路机 / 落地机 / 性能·存储·独服 → 细分小类 → 地区）全景梳理 61 家商家 193 项产品线，附三网与组网配对速查、{total_meow_vendor_articles} 篇猫猫官方专测（外加横评与特殊家宽留档）及 {total_reviews} 条可折叠 NodeSeek 实测原文。',
        'pubDate: 2026-11-18',
        'tags: [VPS, 测评, NodeSeek, NodeQuality, TcpQuality, 线路机, 落地机, 家宽]',
        '---',
        '',
        '> 📚 **MeowVPS 全库 117 家商家 + 全站 205 篇测评博文 100% 完整双卷索引**：',
        '> - **本篇（上卷）· 61 家新收录与转正潜力商家 + 457 条 NodeSeek 社区实测**：聚焦近期新晋黑马商家、全部 64 篇猫猫新商专测 + 2 篇特殊家宽留档，以及 **319 份**可展开终端报告原文。',
        '> - **[下卷 · MeowVPS 正式收录 56 家主力商家与皇冠标杆汇总](/archives/meowvps-official-merchants-2026h2)**：覆盖全部 56 家正式老牌主力商家（含 **DMIT、搬瓦工、netcup、DigitalFyre、港仔 Boil、夏威夷 qqpw** 六大皇冠标杆）与 137 篇猫猫官方深度专测；上下两卷 `61 + 56 = 117` 家 **零重叠、零遗漏**。',
        '> - **配套选型与实操方法论**：[VPS 测评怎么读](/archives/reading-vps-reviews) ｜ [VPS 线路与落地怎么搭](/archives/relay-and-egress-guide) ｜ [Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback)',
        '',
        f'MeowVPS 近期陆续收录并扩充了一批商家目录（含 57 家初始标记“收集中”的商家及 4 家同期关联商家，其中 Tamago、JCloudHosting、Bocchi、BeroHost、NexKr 等已陆续转正，合计 **61 家**、共 **{total_reviews} 条** NodeSeek 测评条目 + **{total_meow_vendor_articles} 篇**猫猫商家专测 + **2 篇**横评与 **2 篇**非目录特殊家宽留档）。为方便按需查机与组网，本文分为上下两部分：',
        '',
        '1. **前半部分 · 猫猫博客分类体系 × 地区选机与组网导览**：先按 **大类（线路机 / 落地机 / 性能·存储·独服 / 归档避雷）→ 细分小类 → 地区** 逐级归类全部 193 项产品线，附上**三网宽带选机速查、前置×落地组网配对表、跨商家横评与大牌标杆参照**，点击任意机型即可直达实测。',
        '2. **后半部分 · 61 家商家完整测评档案库**：按 **商家 → 产品线 → 测评** 完整保留发帖时间、原帖链接、全部猫猫官方评测链接及 TcpQuality 报告链接；全部 **319 份百行级 NodeQuality / TQ / 猫猫终端报告原文已做默认折叠**（点击折叠栏即可展开查看与复制全文，兼顾快速浏览与原始数据留档）。',
        '',
        '先说明几条阅读规则：',
        '',
        '- 主体时间范围为 **2026 年 5 月中旬至 2026 年 11 月 18 日**（近半年）；对 5 家近半年无公开新帖的商家（DataOnline、LightNode、Langya、HostBlazer、VMVM），在文末单独附上其 2026 年 3—4 月的历史公开测评并标注停运/跑路等经营风险，确保目录 100% 完整可查。',
        '- 同一条产品线可能有多人测同一款或不同配置，配置以帖子标题和作者说明为准；配置不明的会写“未注明”。',
        '- 商家自营或独立评测机构（如 MeowVPS、VPStarter）发的长文帖会标出，并提炼核心路由、硬件与避坑结论。',
        '- 报告里的 IP 是测评机当时的出口，不代表现在买到的 IP 段；磁盘、内存等数字是脚本实测值。',
        '- 论坛帖子可能被作者编辑、设为仅登录可见或删除，数据以原帖为准。',
        '',
        taxonomy_md,
        '## 商家与产品线总览',
        '',
        '> 🧭 [↑ 返回顶部分类导览]({{ANCHOR:选机分类体系总览（猫猫博客口径）}}) ｜ 📎 另附：[猫猫博客非目录特殊家宽留档（AWS Wavelength 日本 KDDI / 神秘美国 AT&T）]({{ANCHOR:猫猫博客非目录特殊家宽留档（2 篇）}})',
        '',
        '| 商家（附猫猫官方专测） | 产品线 | 本次收录测评数 | 主要测评时间 |',
        '| --- | --- | --- | --- |',
        *table_rows,
        '',
    ]

    FOOTER = [
        '',
        '## 上下卷联动与选机延伸阅读',
        '',
        '- **想查一线老牌大厂与 6 大皇冠推荐标杆（DMIT / 搬瓦工 / netcup / DigitalFyre / 港仔 Boil / 夏威夷 qqpw）？** 请继续阅读 **[下卷：MeowVPS 正式收录 56 家主力商家与皇冠标杆汇总](/archives/meowvps-official-merchants-2026h2)**（汇总全部 56 家正式主力商家与 137 篇猫猫专测原文）。',
        '- **想看猫猫博客跨商家横向对比跑分？** 请参考 [**《热门机器横评系列(1)：美西优化线路》**](https://meowvps.com/blog/benchboxus/) 与 [**《热门机器横评系列(2)：欧洲线路机器》**](https://meowvps.com/blog/benchboxeu/)。',
        '- **配套方法论与配置防坑**：[VPS 测评怎么读：带宽、IP 标签与流量成本](/archives/reading-vps-reviews) ｜ [VPS 线路与落地怎么搭：链式代理、反向隧道与 Po0](/archives/relay-and-egress-guide) ｜ [Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback)',
        '',
    ]
    full_md = '\n'.join(HEADER) + '\n' + body_text + '\n' + '\n'.join(FOOTER)

    # ---------- 6. Strict Validation ----------
    assert '```\n```' not in full_md and '```text\n```' not in full_md, 'Empty code block detected!'
    assert full_md.count('```') % 2 == 0, 'Unbalanced code fences!'
    assert full_md.count('<details>') == 319 and full_md.count('</details>') == 319, (
        f"Expected 319 <details> blocks, got open={full_md.count('<details>')} close={full_md.count('</details>')}"
    )
    assert '/vps/reading-vps-reviews/' not in full_md and '/vps/relay-and-egress-guide/' not in full_md, 'Stale Astro links remain!'
    bad_h4 = [l for l in full_md.splitlines() if l.startswith('#### ') and (' · ' not in l or len(l.rsplit(' · ', 1)[1].strip()) == 0)]
    assert not bad_h4, f'Malformed H4 author lines: {bad_h4[:3]}'
    bad_tbl = [l for l in full_md.splitlines() if l.startswith('| ') and l.endswith('\\|')]
    assert not bad_tbl, f'Malformed table row ending with escaped pipe: {bad_tbl[:3]}'

    open(out_path, 'w', encoding='utf-8').write(full_md)

    print(f'TEMPLATED SUCCESS! Merchant H2 sections={merchant_sections} (+2 zero-post = {merchant_sections+2} total merchants)')
    print(f'Total #### review entries={total_reviews}, MeowVPS vendor review links={total_meow_vendor_articles}')
    print(f'Total collapsible <details> blocks={full_md.count("<details>")} (```text={full_md.count("```text")})')
    print(f'Templated Markdown size={len(full_md):,} chars ({len(full_md.splitlines()):,} lines) -> {out_path}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='/tmp/article_templated.md')
    args = ap.parse_args()
    build_vol1(args.out)
