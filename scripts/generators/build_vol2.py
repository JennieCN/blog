#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Volume 2 companion post:
  src/content/vps/meowvps-official-merchants-2026h2.md (templated -> /tmp/vol2_templated.md)

Covers all 56 formally rated main MeowVPS vendors (6 Crown Flagships + 50 established/featured vendors),
137 official MeowVPS in-depth product reviews + 2 horizontal shootouts, and 137 collapsible terminal benchmark blocks,
classified under the exact same MeowVPS taxonomy (大类 -> 细分小类 -> 地区 -> 具体机型).
"""
import argparse, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DATA = os.path.abspath(os.path.join(HERE, "..", "..", "..", "data", "vps-reviews-202611"))
DATA_ROOT = os.environ.get("VPS_DATA_DIR") or (DEFAULT_DATA if os.path.isdir(DEFAULT_DATA) else "/tmp")
STRUCTURED_JSON = os.path.join(DATA_ROOT, "meow_vol2", "structured_56.json")

DATA = json.load(open(STRUCTURED_JSON, encoding="utf-8"))
BY_ID = {v["id"]: v for v in DATA}
assert len(BY_ID) == 56, f"Expected 56 vendors, got {len(BY_ID)}"


def H2_OF(vid):
    return BY_ID[vid]["name"]


def A_VID(vid, label, art_idx=None):
    h2 = H2_OF(vid)
    if art_idx is not None:
        art = BY_ID[vid]["articles"][art_idx]
        h3 = f"专测 {art_idx + 1}：{art['title']}（{art['date']}）"
        return f"[{label}]({{{{ANCHOR:{h2}||{h3}}}}})"
    return f"[{label}]({{{{ANCHOR:{h2}}}}})"


def A_ART_SLUG(vid, slug, label):
    h2 = H2_OF(vid)
    arts = BY_ID[vid]["articles"]
    for idx, a in enumerate(arts):
        if a["slug"] == slug:
            h3 = f"专测 {idx + 1}：{a['title']}（{a['date']}）"
            return f"[{label}]({{{{ANCHOR:{h2}||{h3}}}}})"
    raise KeyError(f"Slug {slug} not found under vendor {vid}")


def esc_cell(s, max_len=360):
    s = re.sub(r"\s+", " ", (s or "")).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip() + "…"
    return s.rstrip("\\").replace("|", "\\|")


# ---------- Taxonomy Mapping (Every single one of the 56 vendors mapped by product line & region) ----------
VOL2_TAXONOMY = [
    {
        "cat_h2": "一、线路机（CN 大陆优化线路 / 前置中转机）",
        "cat_desc": (
            "按猫猫博客《热门地区服务器 VPS 推荐》与《常见线路科普》口径，**线路机**指具备中国大陆方向直连路由优化、低延迟且抗晚高峰拥塞的机器，"
            "既可单机直连日常使用，也是拉取下方海外真家宽/纯落地机的**核心前置跳板**。下分**精品优化与专线**、**普通骨干优化与单网快乐机**、**优化线路 + 家宽/双 ISP 复合机**三小类。"
        ),
        "subcats": [
            {
                "sub_h3": "1.1 精品优化与专线（CN2 GIA / CTGNet / 9929 / CMIN2 / 沪港台入口）",
                "sub_desc": (
                    "三网各自顶级优化（电信 CN2 GIA / CTGNet、联通 9929/10099、移动 CMIN2）、三网 CN2 GIA 及国内双出口/IPLC 专线，主打晚高峰稳速与极致单线程，**中国电信用户与高要求前置中转必看此档**。\n\n"
                    "> 📊 **猫猫博客官方同场横评对照**：挑美西或欧洲精品线拿不定主意时，可直接对照猫猫博客横向对比实测——[**《热门机器横评系列(1)：美西优化线路》**](https://meowvps.com/blog/benchboxus/)（同场横评搬瓦工 MegaBOX、DMIT Corona/Malibu、VMISS TRI、VMRack L3）与 [**《热门机器横评系列(2)：欧洲线路机器》**](https://meowvps.com/blog/benchboxeu/)（同场横评德/荷/英/俄 15 台线路机：搬瓦工 EU1、咸鱼云、AkkoCloud、V.PS、白丝云、Misaka、Geelinx、NOSLA、Nube 等）。"
                ),
                "regions": [
                    ("中国大陆入口与跨境专线（上海 / 深港·广台·沪日）", [
                        ("leikwanhost", A_ART_SLUG("leikwanhost", "leikwanhost", "上海 CN2&9929 双出口（239 元/半年）"), "`[需实名·进阶向]` 上海本地入口按对端智能切换 CN2 / 9929 / IXP，把普通海外落地秒变精品线"),
                        ("pqs", A_VID("pqs", "深港 / 广台 / 沪日 IPLC 专线与定制网"), "`[需实名·大户向]` 台湾彼得巧自营多方向内网专线，物理低抖动过境"),
                    ]),
                    ("中国香港（HK）", [
                        ("dmit", " / ".join([
                            A_ART_SLUG("dmit", "dmit", "HKG.Pro 维多利亚（三网 CN2 GIA）"),
                            A_ART_SLUG("dmit", "dmithkeb", "HKG.EB 新品（9929 + CMIN2）"),
                        ]), "`[👑 皇冠推荐]` 香港顶级优化行业标杆，Pro 档电信极致、EB 档联通移动性价比拉满（每 15 天可免费换 IP）"),
                        ("gomami", A_ART_SLUG("gomami", "gomami", "HKG.Turin.Mini（EPYC + 三网各自顶级）"), "Sharon 旗下高端旗舰站，亚太单线程轻松 500Mbps+，被猫猫评为“亚太六边形战士”"),
                        ("neburst", A_ART_SLUG("neburst", "neburst", "Hong Kong HKG（龙系三网精品）"), "Sakura 龙系上游（与狗妈同源）+ 强劲性能 + 免费 DNS 解锁与 Emby，折后门槛更亲民"),
                        ("bwh", A_ART_SLUG("bwh", "bwh", "香港 HKG CN2 GIA（多机房通切）"), "`[👑 皇冠推荐]` 搬瓦工顶级香港三网 CN2 GIA，极稳但正价昂贵，适合不差钱求省心用户"),
                    ]),
                    ("日本（JP · 东京 / 大阪）", [
                        ("dmit", A_ART_SLUG("dmit", "dmit", "TYO.Pro 品川 Shinagawa / TYO.EB"), "`[👑 皇冠推荐]` DMIT 自营东京三网 CTGGIA（Pro）与 9929+CMIN2（EB），日本直连稳度天花板"),
                        ("gomami", A_ART_SLUG("gomami", "gomamijp", "JPN.Pulse 系列（Ryzen 9950X + 三网精品）"), "东京三网各自顶级优化 + 9950X 单核怪兽性能，兼顾极速代理与低延迟建站"),
                        ("neburst", A_ART_SLUG("neburst", "neburst", "Tokyo NRT（三网优化 + 性能）"), "龙系东京三网精品优化，单向流量计费，附带 DNS 解锁与 Emby"),
                        ("VPS", A_VID("VPS", "Tokyo Gen 2（xTom 亲儿子精品线）"), "xTom 官方直营高端东京优化线（47.95 欧/月起），线路硬核但偏 ToB 少活动"),
                        ("rivencloud", A_ART_SLUG("rivencloud", "rivenjp", "日本东京 Premium VPS（9950X + 每日备份）"), "Equinix 机房 xTom 巅峰旗舰线 + Ryzen 9950X + 保留 4 周每日自动备份（$49/月）"),
                        ("greencloud", A_ART_SLUG("greencloud", "greencloudjp", "Tokyo CN Premium Optimized（内网免流）"), "绿云东京电信联通精品优化款（$25/月），支持同机房内网免计费拉普通大流量出口机"),
                        ("bwh", A_ART_SLUG("bwh", "bwh", "日本大阪 JPOS_6（三网 CTGGIA）"), "`[👑 皇冠推荐]` 搬瓦工大阪三网 CTGGIA 精品机房，支持后台一键无损切换机房"),
                    ]),
                    ("新加坡 & 中国台湾（SG / TW）", [
                        ("gomami", A_ART_SLUG("gomami", "gomamisg", "SIN.Pulse 系列（新加坡三网精品复测）"), "新加坡三网各自顶级优化 + 高频 AMD 硬件，拉东南亚家宽与直连双优"),
                        ("VPS", A_ART_SLUG("VPS", "vpssg", "Singapore EPYC Explorer"), "xTom 新加坡顶级大陆优化线，适合预算充足的亚太核心跳板"),
                        ("rivencloud", A_ART_SLUG("rivencloud", "rivensg", "新加坡 Premium VPS（9950X）"), "新加坡 Equinix 机房三网极致优化 + 9950X 高性能旗舰（$49/月）"),
                        ("lightlayer", A_ART_SLUG("lightlayer", "lightlayersg", "Singapore Premium（10M 无限流量，$24.99/年）"), "`[仅退余额·锁IO]` 特色小带宽无限流量新加坡中国优化机，适合轻量 API 与跳板"),
                        ("neburst", A_ART_SLUG("neburst", "nebursttw", "台湾优化尝鲜新品"), "极少见的台湾方向大陆直连优化新品"),
                    ]),
                    ("美国（US · 洛杉矶 LAX / 圣何塞 SJC）", [
                        ("dmit", A_ART_SLUG("dmit", "dmit", "LAX.Pro（Malibu 等三网 CN2 GIA）/ LAX.EB（Corona 等 9929+CMIN2）"), "`[👑 皇冠推荐]` 美西优化双绝：Pro 电信毕业级稳度，EB 联通移动极致且带优化 IPv6，被墙满 15 天免费换"),
                        ("bwh", " / ".join([
                            A_ART_SLUG("bwh", "bwh", "DC1 MEGABOX-PRO（$49/年三网各自顶级）"),
                            A_ART_SLUG("bwh", "bwhdc6", "DC6 CN2 GIA-E"),
                            A_ART_SLUG("bwh", "bwhdc9", "DC9 / DC99 MINIBOX（$29/年）"),
                        ]), "`[👑 皇冠推荐]` 美西性价比断层标杆（29~49 刀/年优惠箱），独享一键切机房绝技"),
                        ("gomami", A_ART_SLUG("gomami", "gomamius", "美国洛杉矶 LAX 优化新品"), "GoMami 美西高端三网优化 + 旗舰 AMD 性能线"),
                        ("VPS", A_ART_SLUG("VPS", "vpssj", "San Jose Starter（圣何塞优化，8.95 欧/月起）"), "xTom 美西圣何塞精品大陆优化入门档"),
                        ("saltyfish", A_ART_SLUG("saltyfish", "saltyfish", "圣何塞 San Jose Premium"), "Kirino 上游平价稳定的美西 CN2 GIA / 9929 线路机"),
                        ("lightlayer", A_ART_SLUG("lightlayer", "lightlayersjc", "圣何塞 SJC Premium（CN2 / CMIN2）"), "电信 CN2、移动 CMIN2 回程表现优秀（注意磁盘 IO 限制与仅退账户余额）"),
                        ("vmiss", A_ART_SLUG("vmiss", "vmisstridc1", "US.LA.TRI 三网优化（折后约 21 元/月）"), "`[补货秒空]` 5 CAD/月高人气平价洛杉矶三网各自顶级优化个人机"),
                        ("vmrack", A_ART_SLUG("vmrack", "vmrack", "L3-VPS-1C1G-Base（$35/年三网各自顶级）"), "`[曾改计费争议]` Easylink 旗下美西三网精品线，机器素质均衡但需留意历史口碑争议"),
                        ("isif", A_ART_SLUG("isif", "isifuscop", "洛杉矶 COP 三网优化新品"), "ISIF 美西大陆优化线 + 免费 DNS 解锁"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyoocstd", "洛杉矶优化 CSTD（9929 & CMIN2）"), "云悠亲民低门槛美西 9929 + CMIN2 优化小鸡"),
                        ("taphip", A_ART_SLUG("taphip", "taphip", "US China Optimized（20 元/月）"), "`[OneMan灵车]` 20 元/月超低门槛美西三网优化小带宽尝鲜机"),
                        ("hostdare", A_ART_SLUG("hostdare", "hostdare", "洛杉矶 CN2 GIA（21.59 欧/年）"), "`[超售严重·慎入]` 延迟好看但晚高峰实测常跌至 10Mbps 且多段送中，仅作避坑对照"),
                    ]),
                    ("欧洲（EU · 德国 DE / 荷兰 NL / 英国 UK）", [
                        ("bwh", A_ART_SLUG("bwh", "bwh", "EU1 荷兰阿姆斯特丹（The Amsterdam Plan，$39/年）"), "`[👑 皇冠推荐]` 欧洲唯一平价大厂三网各自顶级优化（CN2 GIA / 9929 / CMIN2），拉全欧神级前置"),
                        ("gomami", A_ART_SLUG("gomami", "gomamide", "德国法兰克福 FRA Pulse 新品"), "GoMami 2026 年 11 月最新法兰克福三网精品 + 高频 AMD 旗舰"),
                        ("VPS", " / ".join([
                            A_ART_SLUG("VPS", "vpsde", "德国法兰克福 Performance"),
                            A_ART_SLUG("VPS", "vpsnl", "荷兰阿姆斯特丹 Amsterdam"),
                        ]), "xTom 欧洲核心大机房精品大陆优化线"),
                        ("saltyfish", A_ART_SLUG("saltyfish", "saltyfishfrelite", "德国 Frankfurt 9929 / 荷兰 Amsterdam CN2 GIA"), "欧洲线路老牌口碑之选（Kirino 上游），2.5Gbps 大端口季付平价稳健"),
                        ("akko", A_ART_SLUG("akko", "akkocloud", "德国法兰克福 / 英国伦敦 KVM-CN2-A1 mini（299 元/年）"), "稀缺英德双程电联 CN2 GIA + 移动 CMIN2 年付小鸡（部分时段偶有断流）"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyoode9929", "德国法兰克福三网 9929 新品"), "云悠低门槛法兰克福三网 9929 欧洲前置"),
                        ("ciallonetworks", A_ART_SLUG("ciallonetworks", "ciallode9929", "德国法兰克福中国优化 9929"), "二次元商家推出的法兰克福 9929 大陆优化新品"),
                    ]),
                ],
            },
            {
                "sub_h3": "1.2 普通骨干优化与单网快乐机（4837 / 10099 / CMI / 软银 SoftBank / IIJ / 弹性按量）",
                "sub_desc": "以亚太 CMI / 10099 / 高 Q163、日本 SoftBank / IIJ、美西 4837 及按量弹性优化为主，带宽流量充足、起步价低，非常适合联通/移动单网快乐或追求性价比的用户。",
                "regions": [
                    ("中国香港（HK）", [
                        ("rfc", A_ART_SLUG("rfc", "rfchkco", "香港 HK-CO 优化复测（高 Q163 / 10099 / CMI）"), "花卷老牌均衡香港优化机，附赠免费 DNS 解锁 + Emby（偶受同段机场 DDoS 波及）"),
                        ("isif", A_ART_SLUG("isif", "isifcop", "香港 HKCOP 优化系列（低至 6 欧/月）"), "支持特色流量池与免费 DNS 解锁的香港中端优化线（200Mbps 口，偶挨打）"),
                        ("evoxt", A_ART_SLUG("evoxt", "evoxthk", "香港电信移动优化线路机"), "6.0GHz 超高主频 CPU + 香港直连优化，适合轻量低延迟微站与代理"),
                        ("yunyoo", " / ".join([
                            A_ART_SLUG("yunyoo", "yunyoohk4", "香港九龙四区优化"),
                            A_ART_SLUG("yunyoo", "yunyoohk5", "香港荃湾三网优化"),
                        ]), "云悠“丐帮高性价比”香港多可用区入门优化小鸡"),
                        ("vmiss", A_ART_SLUG("vmiss", "vmiss", "香港 HK.BGP 移动快乐线"), "加拿大商家平价香港直连款，移动用户体验尤佳"),
                        ("100tb", A_ART_SLUG("100tb", "100tb", "香港 HK SC 512M（Sakura/Zenlayer 系）"), "`[无路由保证]` 5 刀/月国际互联兼直连可用新品，新商建议月付观察"),
                    ]),
                    ("日本 & 韩国（JP / KR）", [
                        ("greencloud", A_ART_SLUG("greencloud", "greencloud", "日本 2222 JP SoftBank（$22/年，三年翻倍）"), "`[活动不退]` 绿云最出圈的 10Gbps 软银年付神机（联通快乐，电信晚高峰勿盲冲）"),
                        ("rfc", A_ART_SLUG("rfc", "rfc", "日本 JP2-CO / JP2-CO-Lite"), "花卷东京去回程双优（CO）与回程单优（CO-Lite）双档选择 + 免费 DNS 解锁/Emby"),
                        ("nube", A_ART_SLUG("nube", "nube", "东京 TYO 国际优化（IIJ + SoftBank 按时按量）"), "`[按小时+单向流量计费]` 牛肉佬自研弹性云，1 刀/月起三网 IIJ+软银小流量神器"),
                        ("geelinx", A_ART_SLUG("geelinx", "geelinx", "东京 JP-TYO-BGP-A（16.88 欧/年单向计费）"), "`[联通快乐·风波较多]` 国产兆芯 CPU，联通直连真香但曾历 DDoS 与限速争议"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyooiij", "日本东京 IIJ TCVM"), "云悠低价东京 IIJ 入门直连机"),
                        ("isif", A_ART_SLUG("isif", "isif", "韩国 KRCOM 系列（24 欧/月）"), "猫猫实测评价“目前独一档水平”的稀缺韩国大陆优化线路机"),
                        ("vmiss", A_ART_SLUG("vmiss", "vmiss", "韩国 KR.SEL.TRI（5 CAD/月）"), "低门槛韩国首尔三网直连优化个人机"),
                        ("100tb", " / ".join([
                            A_ART_SLUG("100tb", "100tbjp", "日本普通+优质双线"),
                            A_ART_SLUG("100tb", "100tbkrpro", "韩国优质线路"),
                        ]), "Sakura 下游日韩直连与国际互联新品"),
                    ]),
                    ("新加坡 & 马来西亚 & 中国台湾（SG / MY / TW）", [
                        ("evoxt", " / ".join([
                            A_ART_SLUG("evoxt", "evoxt", "全产品测评（主打大马）"),
                            A_ART_SLUG("evoxt", "evoxtmy", "马来西亚三网优化（$2.99/月起）"),
                        ]), "`[亚太电信扶贫神机]` 几乎唯一的平价马来西亚三网优化 + 6GHz 高频机器"),
                        ("isif", A_ART_SLUG("isif", "isif", "新加坡 SGCOP 系列（72 欧/年）"), "高性价比新加坡大陆优化 + 流量池共享方案"),
                        ("pqs", A_ART_SLUG("pqs", "pqstwpro", "台湾台北 PRO 双栈原生 IP"), "`[需实名]` 台湾双栈原生 IP + 极佳国际互联，电信与移动方向带一定回国优化"),
                        ("100tb", A_ART_SLUG("100tb", "100tbsgco", "新加坡普通优化线"), "100TB 新加坡直连与区域互联款"),
                    ]),
                    ("美国 & 欧洲（US / DE / UK）", [
                        ("vmrack", A_ART_SLUG("vmrack", "vmrack", "美西 L2-VPS-1C1G-Base（$26/年，5Gbps）"), "4837/半优化大口高流量平价美西年付机"),
                        ("bestvm", A_ART_SLUG("bestvm", "bestvmuspro", "美国 USPRO（5 元/月三网 4837 + Akari 内网）"), "白菜价三网 4837 回程小鸡，还能组富婆家 Akari 港美内网"),
                        ("nube", A_ART_SLUG("nube", "nube", "圣何塞 SJC 中国优化 / 法兰克福 FRA 中国优化"), "`[按小时计费]` SJC 同款 DMIT 路由（小流量移动首选），FRA 欧洲移动联通快乐"),
                        ("geelinx", A_ART_SLUG("geelinx", "geelinxuk", "英国伦敦优化产品"), "低门槛伦敦回国优化备选款"),
                    ]),
                ],
            },
            {
                "sub_h3": "1.3 优化线路 + 家宽 / 双 ISP 复合机（直连回程 + 住宅身份二合一）",
                "sub_desc": "单机同时具备一定大陆优化回程与本土家宽 / 双 ISP 数据库属性，适合希望省去前置中转、单节点兼顾直连与流媒体/跨境社媒落地的场景。",
                "regions": [
                    ("美国 & 中国台湾（US / TW）", [
                        ("sixtynet", " / ".join([
                            A_ART_SLUG("sixtynet", "sixtynet", "洛杉矶 Wave 家宽重测"),
                            A_ART_SLUG("sixtynet", "sixtynetpro", "美国优化家宽（Wave / COX，$25/月）"),
                        ]), "`[退款爽快·防蹬坏预警]` 独一份 Coresite LA2 大陆半优化 + Wave/COX 家宽 5Gbps 机器（多位 TK 大户反馈易秒封，建议短期按需用）"),
                        ("novixlink", A_ART_SLUG("novixlink", "novixntt", "洛杉矶 LAX-NTT Lite（约 34.95 元/月）"), "大陆优化回程 + 美国 NTT 双 ISP 伪家宽低价二合一款"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyoo", "美国 4837ISP-TCVM（26.99 元/月）"), "美西 4837 直连回程 + 双 ISP 伪家宽入门款，显著低于同类均价"),
                        ("tcs", A_ART_SLUG("tcs", "tcs", "台湾 Taipei Premium（$9.99/月，2Gbps）"), "港台互联优秀 + 台湾大陆基础优化，社区口碑极稳的 TK 直播与流媒体二合一神机"),
                    ]),
                ],
            },
        ],
    },
    {
        "cat_h2": "二、落地机（流量出口 / 流媒体解锁 / 家宽身份机）",
        "cat_desc": (
            "按猫猫博客《VPS IP 质量检测指南》定义，**落地机**直接代表你的终端访问身份，绝大多数无大陆直连优化（需搭配上方线路机中转拉取），"
            "核心看 **IP 库住宅纯净度、流媒体与 AI 解锁、港台/日美 Tier1·Akari·GSL 国际互联**。下分**真家宽独立 IP**、**真家宽 NAT 共享**、**伪家宽（双 ISP）**、**机房纯落地**四小类。"
        ),
        "subcats": [
            {
                "sub_h3": "2.1 真家宽 / 商宽（独立静态·动态 IP）",
                "sub_desc": "由真实本土宽带运营商（HKT、HGC、Hinet、Seednet、TBC、KDDI、So-Net、Hawaiian Telcom、AT&T、Frontier、Verizon、TELUS、FPT、TMNET 等）分配独立 IPv4，满足严苛 AI、金融与跨境业务纯净度需求。",
                "regions": [
                    ("中国香港（HK）", [
                        ("boil", A_ART_SLUG("boil", "boil", "HKT 1.0G 打机神线 & 2.5G 家/商宽自由切换 VDS"), "`[👑 皇冠推荐 · 不退款]` 亚太家宽头牌“港仔”，面板易用省心，大户款支持 HKT 商宽/家宽 API 双切"),
                        ("kaze", " / ".join([
                            A_ART_SLUG("kaze", "kaze", "HKT 家宽初测"),
                            A_ART_SLUG("kaze", "kazehkt", "HKT 独立 IP 独享宽带（$18/月起）"),
                        ]), "主打香港 HKT / HGC 独立 IP + 100M~1Gbps 独享带宽无限流量，性价比与新面板体验出色"),
                        ("synexvm", A_ART_SLUG("synexvm", "synexvm", "香港将军澳 PCCW-HKT 1Gbps 独享 VDS & 300M 打机线"), "面向大户与游戏党的高配香港真家宽/商宽独享无限流量 VDS（$25~$79.1/月）"),
                        ("pqs", A_ART_SLUG("pqs", "pqshkt", "香港 HKT 动态家宽（支持自助换 IP + DDNS）"), "`[需实名]` 彼得巧大户级香港 HKT 动态独享家宽"),
                        ("moonvm", A_ART_SLUG("moonvm", "moonvm", "香港 HGC 100Mbps / HKT 动态一键换 IP"), "2018 年老牌港台家宽商，面板小白友好、带宽冗余足（注意磁盘锁 IO）"),
                        ("yinnet", A_ART_SLUG("yinnet", "yinnet", "香港独立 HGC 家宽 IP（五折后约 $5/月）"), "常驻五折码后仅约 35 元/月的超低门槛香港独立 HGC 家宽"),
                    ]),
                    ("中国台湾（TW）", [
                        ("boil", A_ART_SLUG("boil", "boil", "台湾 Hinet 高性能真家宽"), "`[👑 皇冠推荐]` 港仔台湾本土真家宽，IP 纯净且宿主机性能强劲"),
                        ("fachost", " / ".join([
                            A_ART_SLUG("fachost", "fachost", "台湾 Hinet / Seednet 独立 IP 深测"),
                            A_ART_SLUG("fachost", "fachosttbc", "苗栗/新北 TBC 真家宽 VDS"),
                            A_ART_SLUG("fachost", "fachostsonet", "台湾 So-Net 家宽"),
                        ]), "台湾家宽运营商最齐全的本土团队（无分流纯家宽、低密度不超卖，教程详尽）"),
                        ("pqs", A_ART_SLUG("pqs", "pqstwhinet2", "台湾彰化 Hinet 商宽 / Hinet 动态独享"), "`[需实名]` 稀缺彰化 Hinet 商业宽带与动态家宽，工单响应极快"),
                        ("moonvm", A_ART_SLUG("moonvm", "moonvm", "台湾 Hinet 静态（$45/月）与动态切换系列"), "少见的台湾 Hinet 静态独立 IP 及成熟的动态一键换 IP 方案"),
                        ("tcs", A_VID("tcs", "台湾 Hinet / 远传 SeedNet / 中嘉 KBT 动态独立 IP"), "台湾一人老商（$24.99/月无限流起），面板一键换 IP（注意家宽带分流策略）"),
                        ("nmcloud", A_ART_SLUG("nmcloud", "nmcseednet", "台湾 Seednet 独立 IP 家宽"), "工厂云下游“牛马云”，定位不烂大街也不天价的折中派台湾独立家宽"),
                    ]),
                    ("日本（JP）", [
                        ("tokyonline", A_ART_SLUG("tokyonline", "tokyonline", "东京 KDDI / So-Net 独立 IP 真家宽（380~550 元/月）"), "`[不退款·HDD盘]` 稀缺东京本土独享 KDDI / So-Net 真家宽 10TB 大流量（性能偏弱、新老 IP 看脸）"),
                        ("boil", A_ART_SLUG("boil", "boilcpe", "日本 CPE KDDI 5G 蜂窝真家宽 & SoftBank 独享"), "`[👑 皇冠推荐]` 顶级日本 5G 蜂窝住宅出口与埼玉县 SoftBank 1Gbps 动态独享"),
                        ("zorocloud", A_ART_SLUG("zorocloud", "zorocloudglbb", "日本 GLBB 独立 IP 家宽（JP-Titan-Plus，128 元/月）"), "高人气平价日本 GLBB 住宅 ISP 独立 IP 落地机"),
                    ]),
                    ("美国 & 加拿大（US / CA）", [
                        ("qqpw", A_ART_SLUG("qqpw", "hawaii", "夏威夷 Hawaiian Telcom 独立 IP VDS（$35/月，7940HS）"), "`[👑 皇冠推荐 · 不退款]` 猫猫自用近一年仍五库全绿的顶级美国家宽 + Ryzen 7940HS 性能怪兽（唯夏威夷物理延迟略高）"),
                        ("boil", " / ".join([
                            A_ART_SLUG("boil", "boil", "加拿大 TELUS 500M 独享无限流 VDS"),
                            A_ART_SLUG("boil", "boilusfrontier", "美国 Frontier（Verizon）静态大带宽家宽"),
                        ]), "`[👑 皇冠推荐]` 独一档加拿大 TELUS 高性能家宽 VDS 与美西 Frontier 静态大口家宽"),
                        ("vircs", A_ART_SLUG("vircs", "vircs", "加州公寓自拉 AT&T / Frontier 静态独享真家宽（$35.99/月）"), "美国家宽老牌头部正规军，自有加州公寓拉线（50Mbps 无限流；注意老段若被蹬坏不免费换 IP）"),
                        ("wirecat", " / ".join([
                            A_ART_SLUG("wirecat", "wirecat", "美国 AT&T 5G / Verizon 5G / T-Mobile 家宽"),
                            A_ART_SLUG("wirecat", "wirecattest", "美国 Sail / Comcast / Starlink 家宽"),
                        ]), "`[半实名电话验证·入出站双IP]` 美国家宽品种博物馆，单网卡机房入站 IP + 家宽出站 IP 天然好分流"),
                        ("aaitr", " / ".join([
                            A_ART_SLUG("aaitr", "aaitr", "美国家宽全系初测"),
                            A_ART_SLUG("aaitr", "aaitrfrontier", "Frontier 静态家宽（119 元/月起）"),
                            A_ART_SLUG("aaitr", "aaitrverizon", "Verizon 静态家宽复测"),
                        ]), "`[需实名·常缺货]` 119~149 元/月超低门槛美国 AT&T / Frontier / Verizon 独立真家宽"),
                        ("novixlink", A_ART_SLUG("novixlink", "novixcox", "拉斯维加斯 LAS-COX 真家宽（约 99.95 元/月）"), "百元档美国 COX 独立住宅 IP 落地机"),
                        ("residentialservice", A_ART_SLUG("residentialservice", "residentialservice", "美国 Windstream / RCN 独立 IP 家宽（$15/月）"), "113 元/月中端高性价比美国独立家宽/商宽 VDS（优先选 Windstream 段）"),
                        ("zorocloud", A_ART_SLUG("zorocloud", "zorocloudatt", "美国 AT&T 静态独立 IP 家宽"), "索隆云美区 AT&T 静态住宅落地新品"),
                    ]),
                    ("东南亚（越南 VN / 马来西亚 MY / 新加坡 SG）", [
                        ("pqs", A_ART_SLUG("pqs", "pqsvnfpt", "越南 FPT 动态家宽独享（200M 无限流，400 元/月）"), "少见的越南 FPT 独享带宽动态真家宽，支持 API 与自助换 IP"),
                        ("yinnet", A_ART_SLUG("yinnet", "yinnet", "越南独立真家宽（五折后 $6/月）"), "猫猫点名夸赞“质量数一数二”的低价越南真家宽代表"),
                        ("mondoze", A_ART_SLUG("mondoze", "mondozetmnet", "马来西亚 TMNET 动态住宅 IP（$249.99/年无限流）"), "`[系统随机端口]` 2012 年吉隆坡本土老牌商自营稀缺 TMNET 动态真家宽"),
                        ("zorocloud", " / ".join([
                            A_ART_SLUG("zorocloud", "zorocloudmy", "马来西亚 TM 静态家宽（149 元/月）"),
                            A_ART_SLUG("zorocloud", "zorocloudsg", "新加坡 SPTel 商宽/类家宽（188 元/月）"),
                        ]), "东南亚热门稀缺本土 ISP 独立 IP 落地系列"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.2 真家宽 / 商宽（NAT 共享 IP 与多国聚合出口）",
                "sub_desc": "通过共享公网端口或单机聚合多国真实家宽出口，把动辄数百元/月的真家宽压到十几至数十元/月（注意无 80/443 标准端口，仅做代理出口）。",
                "regions": [
                    ("全球多国聚合 & 中国香港（Global / HK）", [
                        ("boil", A_ART_SLUG("boil", "boil", "包羅萬有 2500Mbps（一机 35 个全球家宽出口，$48.88/月）"), "`[👑 皇冠推荐]` 单台机器内置覆盖港台日美加等 35 个真实家宽出口，解锁玩家终极玩具"),
                        ("kaze", " / ".join([
                            A_ART_SLUG("kaze", "kazecmhk", "香港 CMHK 家宽 NAT"),
                            A_ART_SLUG("kaze", "kazehkbnnat", "香港 HKBN 家宽 NAT"),
                            A_ART_SLUG("kaze", "kazewttnat", "香港 WTT 商宽 NAT"),
                        ]), "香港主流本土宽带（CMHK / HKBN / WTT）高性价比 NAT 全家桶"),
                    ]),
                    ("日本 & 中国台湾（JP / TW）", [
                        ("xuezhangvps", " / ".join([
                            A_ART_SLUG("xuezhangvps", "xuezhangvpskddi", "日本 KDDI / SoftBank / Biglobe 动态 NAT（35 元/月）"),
                            A_ART_SLUG("xuezhangvps", "xuezhangvpshinet", "台湾 Hinet 动态家宽 NAT"),
                        ]), "`[每日换IP防烂段]` 35 元/月起超低门槛日台动态真家宽 NAT 专门店"),
                        ("miraigrid", A_ART_SLUG("miraigrid", "miraigrid", "日本 NURO / So-Net 住宅共享（$7.99/月）"), "极冷门日本 NURO 光纤家宽（IPv4 共享 + IPv6 独享，均走 NURO 住宅网）"),
                        ("ciallonetworks", A_ART_SLUG("ciallonetworks", "ciallojp", "日本千叶 Chiba SoftBank 半静态家宽 NAT（100 元/月）"), "`[人工审核开机]` 严控滥用的高质量日本千叶软银真家宽 NAT（10 端口）"),
                        ("fachost", A_ART_SLUG("fachost", "fachosthinetnat", "台湾 Hinet 家宽 NAT"), "工厂云官方低密度台湾 Hinet NAT 方案"),
                        ("nmcloud", A_ART_SLUG("nmcloud", "nmcloud", "台湾 HINET-K-STD（25 元/月）/ SeedNet-L-STD（20 元/月）"), "20~25 元/月稳健中端台湾双运营商动态 NAT"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyootw", "台湾 Hinet 家宽 NAT"), "云悠平价台湾 Hinet NAT 补充节点"),
                    ]),
                    ("美国 & 加拿大（US / CA）", [
                        ("qqpw", A_ART_SLUG("qqpw", "hawaii", "夏威夷 Hawaii NAT VPS（Tiny $12/年 / Lite $2/月）"), "`[👑 皇冠推荐 · 禁CN直连]` 12 刀/年即可蹭上顶级夏威夷真家宽纯净 IP（必须用非大陆海外前置连接）"),
                        ("aaitr", A_ART_SLUG("aaitr", "aaitrverizonnat", "美国 Verizon / Frontier 动态家宽 NAT"), "`[需实名·禁CN解析]` 美西稀缺低价 Frontier / Verizon 动态真家宽 NAT"),
                        ("xuezhangvps", A_ART_SLUG("xuezhangvps", "学长网络", "加拿大 Bell Canada 动态家宽 NAT（36.75 元/月）"), "少见的加拿大 Bell 本土动态家宽 NAT（每 2~5 天自动换 IP）"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.3 伪家宽（双 ISP 属性机房 IP · 无大陆直连优化）",
                "sub_desc": "物理托管于商业数据中心但宣告了部分数据库标为 `ISP` 的地址段，兼具机房带宽与低成本住宅标签，必须配合前置中转使用。",
                "regions": [
                    ("亚太 / 欧美 / 印非多国节点", [
                        ("ipraft", " / ".join([
                            A_ART_SLUG("ipraft", "ipraft", "全球 19+ 地区双 ISP 伪家宽深测（新/台/美/阿联酋等）"),
                            A_ART_SLUG("ipraft", "ipraftindia", "印度双 ISP 新品"),
                        ]), "覆盖冷门小国最广的双 ISP 伪家宽大户（台湾 $3/月起；各机房品控差异大需按篇核查）"),
                        ("yinnet", " / ".join([
                            A_ART_SLUG("yinnet", "yinnet", "多国双 ISP 全家桶（韩/台/美等）"),
                            A_ART_SLUG("yinnet", "yinnetuk", "英国 UK 独立 IP 家宽"),
                            A_ART_SLUG("yinnet", "yinnetfr", "法国 FR 独立 IP 伪家宽"),
                        ]), "常年 5 折码的低预算全球双 ISP 铺货王（港/越/台优，欧美韩部分段需防送中）"),
                        ("zorocloud", " / ".join([
                            A_ART_SLUG("zorocloud", "zorocloudin", "印尼双 ISP"),
                            A_ART_SLUG("zorocloud", "zorocloudkr", "韩国双 ISP"),
                            A_ART_SLUG("zorocloud", "zorocloudde", "德国原生双 ISP"),
                        ]), "索隆云多国原生 / 双 ISP 机房落地矩阵"),
                        ("novixlink", A_ART_SLUG("novixlink", "novixcg", "美国 Cogent（CG）双 ISP 伪家宽"), "诺联主机低价美国 Cogent 双 ISP 跨境电商账号落地机"),
                        ("yunyoo", A_ART_SLUG("yunyoo", "yunyoo", "英国纽卡斯尔 TCVM-Mini（15.99 元/月）"), "15.99 元/月 4TB 大流量的英国多库家宽属性原生落地小鸡"),
                        ("taphip", A_ART_SLUG("taphip", "taphip", "韩国伪家宽（18 元/月）"), "18 元/月超低价韩国双 ISP 尝鲜落地机"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.4 机房落地机（原生 IP 解锁 / Akari·GSL·T1 国际互联 / 住宅 IPv6 分流）",
                "sub_desc": "专注国际骨干互联（港台 Akari 13ms、日美西雅图 GSL、亚太 JINX T1）、内置 DNS/原生流媒体全解锁或极低价冷门地区原生出口。",
                "regions": [
                    ("港台日新及东南亚（HK / TW / JP / SG / TH / MY）", [
                        ("bage", A_ART_SLUG("bage", "bage", "港 / 日 / 新 / 美 / 德 / 英多地区大口双栈解锁落地"), "MJJ 圈经典“落地毕业套餐”：5Gbps 大口 + 双栈原生/DNS 全解锁 + 强劲性能（$11.11~$30.79/年）"),
                        ("datawave", A_ART_SLUG("datawave", "datawave", "香港 HK-STD & 台湾 TW-STD Akari 对端（10 元/月）"), "`[组网高手向]` 10 元/月白菜价接入 Akari，实测港↔台延迟仅 **13.7ms**、单线程破 **1Gbps**"),
                        ("bestvm", " / ".join([
                            A_ART_SLUG("bestvm", "bestvmtw", "台湾 TWBGP-Lite（13.5 元/月 Akari）"),
                            A_ART_SLUG("bestvm", "bestvmjpbgp", "日本 JPBGP 测试"),
                        ]), "`[持续高占限速100M]` 富婆家平价 Akari 港台日互联全家桶（注意突发跑满 30~120 秒会触发半小时限速）"),
                        ("rfc", A_ART_SLUG("rfc", "rfc", "HK / JP / SG T1ION（JINX 国际互联，$29.99/年起）"), "花卷亚太 T1 国际互联纯落地系列，全系白送 DNS 流媒体解锁与 Emby 服"),
                        ("skyline", A_ART_SLUG("skyline", "skyline", "日本 / 新加坡自接线落地机"), "Equinix TY8/SG1 自接线解锁落地机，非广东移动与联通部分地区亦可直连快乐"),
                        ("aethercloud", A_ART_SLUG("aethercloud", "aethercloud", "香港 Prime（$7/年，机房 v4 + 港台越日多国家宽 v6）"), "7 刀/年带多地区家庭宽带 IPv6 免费分流出口的高可玩性纯落地小鸡"),
                        ("taipei101", " / ".join([
                            A_ART_SLUG("taipei101", "taipei101tw", "台湾 Taipei-Touchdown 独立 IP"),
                            A_ART_SLUG("taipei101", "taipei101sg", "新加坡落地新品"),
                            A_ART_SLUG("taipei101", "taipei101jp", "日本落地新品"),
                        ]), "AS54286 新兴 IaaS 平台亚太原生落地节点"),
                        ("nube", A_ART_SLUG("nube", "nubethai", "泰国曼谷原生 IP 弹性云"), "稀缺按小时计费泰国本土原生 IP 落地节点"),
                        ("mondoze", A_ART_SLUG("mondoze", "mondozelinuxvps", "马来西亚 Cyberjaya 机房原生 IP（$8.33/月无限流）"), "吉隆坡老牌本土 IDC 自有机房大马原生 IP 无限流量 VPS"),
                    ]),
                    ("美国 & 欧亚冷门节点（US / TR / UK）", [
                        ("bugnet", A_ART_SLUG("bugnet", "bugnet", "美国西雅图 Seattle VPS Mars（GSL 上游，£32.99/年）"), "`[不退款]` 西雅图接入 GSL 国际骨干 + 双栈原生 IP，组“沪→日→美西雅图”超低延迟链路利器"),
                        ("taipei101", " / ".join([
                            A_ART_SLUG("taipei101", "taipei101", "美国 LAX1 / Houston4 / TEX1（$0.95~$0.98/月）"),
                            A_ART_SLUG("taipei101", "taipei101laxspe", "美国 LAX 特殊落地新品"),
                        ]), "`[下单流程繁琐]` 不到 1 刀/月 2.9TB 流量的高纯净美国原生/商宽属性神仙价落地小鸡"),
                        ("aethercloud", A_ART_SLUG("aethercloud", "aethercloud", "美国 Prime（$7/年，2.5G 口 + AT&T 家宽 IPv6）"), "7 刀/年机房 IPv4 搭配真实 AT&T 家庭宽带 IPv6 出站分流"),
                        ("dpnet", A_ART_SLUG("dpnet", "dpnet", "土耳其 Budget-2（$2.4/月，4C8G / 90G / 无限流）"), "`[新商偏灵·慎入]` 稀缺超低价高配土耳其节点，但服务与解锁杂乱需月付防灵"),
                        ("residentialservice", " / ".join([
                            A_ART_SLUG("residentialservice", "residentialservicetk", "土耳其 BGP VDS"),
                            A_ART_SLUG("residentialservice", "residentialserviceuk", "英国落地产品"),
                        ]), "土耳其与英国冷门纯净落地补充方案"),
                    ]),
                ],
            },
        ],
    },
    {
        "cat_h2": "三、性能机 / 建站机 / 大盘存储鸡",
        "cat_desc": "专注单核/多核强算力（Ryzen 9 9950X / 7950X3D / EPYC）、高 SLA 建站托管（套 Cloudflare 盾或法兰克福/美西前置反代）以及大容量无限流量 PT/备份存储。",
        "subcats": [
            {
                "sub_h3": "3.1 高频性能 / 建站 VPS 与 VDS（Ryzen 9950X / 7950X3D / EPYC SLA 99.9%）",
                "sub_desc": "CPU 与 NVMe IO 性能拉满、在线率稳健，专为生产建站、Docker 容器编排、游戏服与编译任务打造。",
                "regions": [
                    ("欧洲（德国 DE / 荷兰 NL / 英国 UK）", [
                        ("netcup", A_VID("netcup", "德国 RS 1000 G12（独享核 10.74 欧/月）& VPS 500 G12（4.96 欧/月）"), "`[👑 皇冠推荐 · 猫猫博客同款托管商]` 2008 年德国大厂，SLA 99.9% 稳如磐石 + G 口无限流，月底活动常送翻倍硬盘（注册审核较严）"),
                        ("quicksrv", " / ".join([
                            A_ART_SLUG("quicksrv", "quicksrvams", "荷兰 AMS-Standard 16（EPYC 9354P + 40G + 异地备份）"),
                            A_ART_SLUG("quicksrv", "quicksrvuk", "英国 UK-Game 16（Ryzen 9 9950X + 30Tbps 高防）"),
                        ]), "15.99 欧/月给足 4C16G + 300~350GB NVMe + 30Tbps DDoS 防护的高配欧洲建站/游戏新贵（重要数据仍需自备异地备份）"),
                        ("bage", A_ART_SLUG("bage", "bage", "德国法兰克福 BFTINY（9950X，$11.11/年）"), "黑五闪购级德国 Ryzen 9 9950X 小钢炮兼流媒体解锁机"),
                    ]),
                    ("美国 & 亚太（US / SG / JP / HK）", [
                        ("digitalfyre", " / ".join([
                            A_ART_SLUG("digitalfyre", "digitalfyre", "美国洛杉矶 LAX S2（8C8G 9950X，$10/月）"),
                            A_ART_SLUG("digitalfyre", "digitalfyresg", "新加坡高性能 VPS（8C8G，$10/月）"),
                        ]), "`[👑 皇冠推荐]` 2009 年波士顿老牌主机商，Ryzen 9 9950X + 高速 NVMe + 10Gbps 大口，同价位建站性能性价比拉满"),
                        ("bugnet", " / ".join([
                            A_ART_SLUG("bugnet", "bugnetjp", "日本建站机初测"),
                            A_ART_SLUG("bugnet", "bugnetjp2", "东京 Chlorine（Ryzen 9 7950X3D + DDR5 ECC，£6.99/月）"),
                            A_ART_SLUG("bugnet", "bugnetper", "美国西雅图 Performance"),
                        ]), "`[不退款]` 罕见搭载 AMD R9 7950X3D 大三缓神 U 的东京/西雅图高性能建站小钢炮"),
                        ("ciallonetworks", " / ".join([
                            A_ART_SLUG("ciallonetworks", "ciallohk", "香港高性能建站新品"),
                            A_ART_SLUG("ciallonetworks", "ciallohkepyc", "香港 EPYC 高性能建站机"),
                        ]), "香港本地低延迟 EPYC 建站机型"),
                        ("evoxt", A_ART_SLUG("evoxt", "evoxt", "全球 16 机房 6.0GHz 高频云服务器（$2.99/月起）"), "全系高达 6.0GHz Turbo 单核性能，按周/按月灵活部署轻量海外业务"),
                        ("geelinx", A_ART_SLUG("geelinx", "geelinxhk", "香港 HK 计算型 VPS 新品"), "香港计算向入门 VPS 节点"),
                    ]),
                ],
            },
            {
                "sub_h3": "3.2 大盘鸡（大容量存储 / 无限流量 PT 刷流与冷备）",
                "sub_desc": "提供大硬盘或 G 口无限流量组合，适合冷数据异地备份、自建图床网盘与 PT 刷流。",
                "regions": [
                    ("德国 & 美国（DE / US）", [
                        ("netcup", A_VID("netcup", "德国 G 口无限流量 RS / Storage 系列（月底活动硬盘翻倍）"), "`[👑 皇冠推荐]` MJJ 圈德国刷 PT 与大盘建站常青树，月底固定活动常享同价位双倍 SSD/HDD"),
                        ("ciallonetworks", A_ART_SLUG("ciallonetworks", "ciallous", "美国凤凰城 Phoenix 大硬盘高流量双栈机"), "凤凰城双栈原生 IP + 大容量存储高流量落地与冷备机"),
                        ("greencloud", A_VID("greencloud", "多机房 Storage Promo 大盘与三年付翻倍系列"), "国际知名促销大盘与大内存机型常客（活动款不退，看准机房再出手）"),
                    ]),
                ],
            },
        ],
    },
]


def wrap_pre(text):
    text = text.replace("```", "'''")
    out = []
    for line in text.splitlines():
        while len(line) > 104:
            out.append(line[:104])
            line = line[104:]
        out.append(line)
    return "\n".join(out).strip()


def build_vol2(out_path="/tmp/vol2_templated.md"):
    seen_vids = set()
    total_tax_rows = 0
    for cat in VOL2_TAXONOMY:
        for sc in cat["subcats"]:
            for _, rows in sc["regions"]:
                for vid, _, _ in rows:
                    assert vid in BY_ID, f"Unknown vendor id in taxonomy: {vid}"
                    seen_vids.add(vid)
                    total_tax_rows += 1

    missing_vids = set(BY_ID.keys()) - seen_vids
    assert not missing_vids, f"Vendors missing from VOL2_TAXONOMY: {missing_vids}"

    MD = []
    w = MD.append

    w("---")
    w("title: MeowVPS 正式收录 56 家主力商家与皇冠标杆汇总：按分类、地区与实测原文整理（下卷）")
    w("description: 按猫猫博客（MeowVPS）选机分类体系（线路机 / 落地机 / 性能·建站·大盘鸡 → 细分小类 → 地区）全景梳理全部 56 家正式主力商家（含 DMIT、搬瓦工、netcup、DigitalFyre、港仔 Boil、夏威夷 qqpw 六大皇冠标杆），汇总 137 篇官方专测与可折叠终端报告原文，与上卷共同实现 MeowVPS 全库 117 家 100% 覆盖。")
    w("pubDate: 2026-11-18")
    w("tags: [VPS, 测评, 线路, 落地, 家宽, 组网, NodeQuality]")
    w("---")
    w("")
    w("> 📚 **MeowVPS 全库 117 家商家 100% 完整双卷索引**：")
    w("> - **[上卷 · 61 家新收录与转正潜力商家 + 457 条 NodeSeek 社区实测汇总](/archives/nodeseek-merchant-reviews-2026h2)**：覆盖近期新晋热门商家（六六云、白丝云、艾云、ZgoCloud、丽萨主机、懒猫云、Tamago、BeroHost、Bocchi、JCloud、NexKr 等 61 家）、全量猫猫官方专测链接与 319 份可折叠终端报告原文。")
    w("> - **本篇（下卷）· 56 家正式主力老牌商家 + 6 大皇冠标杆 + 137 篇猫猫官方深度专测**：覆盖猫猫博客正式归档的全部主力大牌与细分头部商家（上下两卷 `61 + 56 = 117` 家，**零重叠、零遗漏**）。")
    w("> - **配套选型与实操方法论**：[VPS 测评怎么读：带宽、IP 标签与流量成本](/archives/reading-vps-reviews) ｜ [VPS 线路与落地怎么搭：链式代理、反向隧道与 Po0](/archives/relay-and-egress-guide) ｜ [Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback)")
    w("")
    w("如果说[上卷](/archives/nodeseek-merchant-reviews-2026h2)解决的是“近期论坛里新冒出来的热门黑马和小众神机靠不靠谱”，那么本篇**下卷**解决的就是“**经过长期市场验证的一线大厂、亚太旗舰与各国家宽正规军该怎么挑**”。本文沿用与上卷完全一致的 **猫猫博客（MeowVPS）三级选机坐标系（三大主类 → 细分小类 → 地区 → 具体机型）**，将全部 **56 家** 正式主力商家的官方档案卡、退款与实名规则、猫猫锐评以及 **137 篇** 专测文章（含 **137 份默认折叠的终端实测数据原文** 与 **2 篇跨商家同场横评**）一网打尽。")
    w("")

    # ---------- Crown Flagships Section ----------
    w("## 👑 猫猫钦点 6 大皇冠推荐标杆（好评如潮）")
    w("")
    w("在全部 117 家收录商家中，仅有以下 **6 家** 获得了猫猫博客最高等级的 **皇冠推荐（`recommended: true` · 好评如潮）** 认证，分别镇守**顶级优化线路、亚太真家宽、美国纯净真家宽、欧洲稳态建站与高性价比 9950X 性能机**五大核心赛道，不想折腾踩坑的读者可直接从这 6 家里对号入座：")
    w("")
    w("| 皇冠商家（点击直达） | 镇守赛道 | 代表拳头机型与参考价 | 退款 / 实名政策 | 猫猫核心评价提炼 |")
    w("| --- | --- | --- | --- | --- |")
    crown_order = ["dmit", "bwh", "boil", "qqpw", "netcup", "digitalfyre"]
    crown_tracks = {
        "dmit": "美西 / 香港 / 日本顶级优化线路",
        "bwh": "美西 / 荷兰高性价比大厂优化线路",
        "boil": "港 / 台 / 日 / 加 / 美全能真家宽",
        "qqpw": "美国夏威夷五库全绿顶级真家宽",
        "netcup": "德国 SLA 99.9% 建站与 PT 刷流神机",
        "digitalfyre": "美西 / 新加坡 Ryzen 9950X 高性能建站",
    }
    for cid in crown_order:
        cv = BY_ID[cid]
        cc = cv["card"]
        reps_short = "；".join(f"**{r['name']}**（{r['spec'].split('；')[0]}）" for r in cc["rep_lines"][:2])
        pol = f"{cc['refund'].split('；')[0] or '见官网'} / {cc['kyc'] or '免实名'}"
        w(f"| 👑 {A_VID(cid, cv['name'])} | {crown_tracks[cid]} | {esc_cell(reps_short, 140)} | {esc_cell(pol, 60)} | {esc_cell(cc['meow_comment'], 120)} |")
    w("")

    # ---------- Taxonomy Overview ----------
    w("## 选机分类体系总览（猫猫博客口径）")
    w("")
    w(
        f"下面将本卷全部 **56 家正式商家、{total_tax_rows} 组代表地区产品线** 严格按 **三大主类 → 9 个细分小类 → 地区** 展开。"
        "支持使用上方筛选栏按关键词（如 `9929`、`CN2`、`Hinet`、`AT&T`、`9950X`、`NAT`）实时过滤，点击任意商家或机型即可跳至对应的档案卡与实测报告："
    )
    w("")
    w("| 大类 | 细分小类（点击跳转） | 覆盖地区 | 收录机型组数 | 核心选购定位 |")
    w("| --- | --- | --- | --- | --- |")

    summary_meta = [
        ("一、线路机", "1.1 精品优化与专线（CN2 GIA / CTGNet / 9929 / CMIN2 / 沪港台入口）", "上海/专线、香港、日本、新加坡/台湾、美国、荷/德/英", "电信必看、全天候晚高峰稳速与拉海外家宽的黄金前置"),
        ("一、线路机", "1.2 普通骨干优化与单网快乐机（4837 / 10099 / CMI / 软银 SoftBank / IIJ / 弹性按量）", "香港、日本/韩国、新加坡/大马/台湾、美/德/英", "联通移动高性价比直连、大马电信扶贫与按小时弹性云"),
        ("一、线路机", "1.3 优化线路 + 家宽 / 双 ISP 复合机（直连回程 + 住宅身份二合一）", "美国、台湾", "单机兼顾大陆优化回程与 Wave/COX/NTT/台湾直播落地"),
        ("二、落地机", "2.1 真家宽 / 商宽（独立静态·动态 IP）", "香港、台湾、日本、美国/加拿大、越南/大马/新加坡", "本土真实 ISP 独立 IP，应对高风控 AI、金融与跨境业务"),
        ("二、落地机", "2.2 真家宽 / 商宽（NAT 共享 IP 与多国聚合出口）", "全球 35 出口聚合、香港、日本/台湾、美国/加拿大", "12 刀/年或 20~35 元/月低成本共享真实动态家宽出口"),
        ("二、落地机", "2.3 伪家宽（双 ISP 属性机房 IP · 无大陆直连优化）", "新/台/美/英/法/德/韩/印/印尼等 19+ 地区", "常驻折扣多国双 ISP 机房段，需搭配前置中转使用"),
        ("二、落地机", "2.4 机房落地机（原生 IP 解锁 / Akari·GSL·T1 国际互联 / 住宅 IPv6 分流）", "港/台/日/新/泰/马、美国西雅图/得州、土耳其/英国", "港台 13.7ms 极速互联、DNS/原生全解锁与 $0.95/月神仙落地"),
        ("三、性能/建站/大盘", "3.1 高频性能 / 建站 VPS 与 VDS（Ryzen 9950X / 7950X3D / EPYC SLA 99.9%）", "德国/荷兰/英国、美国/新加坡/日本/香港", "netcup 99.9% SLA 生产建站与 9950X / 7950X3D 性能怪兽"),
        ("三、性能/建站/大盘", "3.2 大盘鸡（大容量存储 / 无限流量 PT 刷流与冷备）", "德国、美国凤凰城、全球促销节点", "G 口无限流量刷 PT、月底翻倍硬盘与大容量冷备"),
    ]

    sub_counts = {}
    for cat in VOL2_TAXONOMY:
        for sc in cat["subcats"]:
            sub_counts[sc["sub_h3"]] = sum(len(rows) for _, rows in sc["regions"])

    for cat_short, sub_h3, regs_str, pos_str in summary_meta:
        short_label = sub_h3.split("（")[0]
        w(f"| {cat_short} | [{short_label}]({{{{ANCHOR_SELF:{sub_h3}}}}}) | {regs_str} | {sub_counts[sub_h3]} 组 | {pos_str} |")
    w("")

    # Emit full taxonomy tables
    for cat in VOL2_TAXONOMY:
        w(f"## {cat['cat_h2']}")
        w("")
        w(cat["cat_desc"])
        w("")
        for sc in cat["subcats"]:
            w(f"### {sc['sub_h3']}")
            w("")
            w(sc["sub_desc"])
            w("")
            for reg_name, rows in sc["regions"]:
                w(f"**{reg_name}**")
                w("")
                w("| 商家 | 机型 / 专测直达 | 线路 / IP / 硬件与避坑要点 |")
                w("| --- | --- | --- |")
                for vid, link_md, feat in rows:
                    vname = BY_ID[vid]["name"]
                    prefix = "👑 " if BY_ID[vid]["recommended"] else ""
                    w(f"| {prefix}{A_VID(vid, vname)} | {link_md} | {feat} |")
                w("")

    # ---------- Master 56-Vendor Summary Table ----------
    ordered_vids = crown_order + [v["id"] for v in sorted(DATA, key=lambda x: x["id"].lower()) if v["id"] not in crown_order]
    assert len(ordered_vids) == 56

    w("## 56 家正式商家与产品线总览")
    w("")
    w("> 🧭 [↑ 返回顶部分类导览]({{ANCHOR:选机分类体系总览（猫猫博客口径）}})")
    w("")
    w("| 商家（附猫猫档案卡） | 核心地区与赛道标签 | 代表产品线 | 官方专测篇数 | 最新档案/专测日期 |")
    w("| --- | --- | --- | --- | --- |")
    for vid in ordered_vids:
        v = BY_ID[vid]
        c = v["card"]
        crown = "👑 " if v["recommended"] else ""
        t_regs = "/".join(v["tags"].get("regions", [])[:6])
        t_feats = " · ".join(v["tags"].get("features", []))
        reps_str = "、".join(r["name"] for r in c["rep_lines"][:3]) or "多产品线"
        art_dates = [a["date"] for a in v["articles"] if a["date"]]
        latest_dt = max(art_dates) if art_dates else (c["updated"] or "2026-07")
        w(f"| {crown}{A_VID(vid, v['name'])}（[档案卡]({v['card_url']})） | `{t_feats}`（{t_regs}） | {esc_cell(reps_str, 90)} | {len(v['articles'])} 篇 | {latest_dt} |")
    w("")

    # ---------- Per-Vendor Detailed Sections (All 56 Vendors + 137 Official Reviews) ----------
    details_emitted = 0
    for vid in ordered_vids:
        v = BY_ID[vid]
        c = v["card"]
        w(f"## {v['name']}")
        w("")
        if v["recommended"]:
            w(f"> 👑 **猫猫博客皇冠推荐标杆（{c['rating'] or '好评如潮'}）** ｜ 🧭 [↑ 返回顶部分类导览]({{{{ANCHOR:选机分类体系总览（猫猫博客口径）}}}})")
        else:
            w("> 🧭 [↑ 返回顶部分类导览]({{ANCHOR:选机分类体系总览（猫猫博客口径）}})")
        w("")

        if c["intro"]:
            w(c["intro"])
            w("")

        w("| 档案维度 | 核查详情 |")
        w("| --- | --- |")
        badge = f"👑 皇冠推荐（{c['rating'] or '好评如潮'}）" if v["recommended"] else (c["rating"] or "正式收录")
        links_cell = f"[MeowVPS 商家档案卡]({v['card_url']})"
        if c["site_url"]:
            links_cell += f" ｜ [商家官网]({c['site_url']})"
        w(f"| 收录状态与入口 | {badge} ｜ {links_cell} |")
        if c["refund"] or c["kyc"] or c["pay"]:
            pol_parts = []
            if c["refund"]: pol_parts.append(f"**退款**：{c['refund']}")
            if c["kyc"]: pol_parts.append(f"**实名**：{c['kyc']}")
            if c["pay"]: pol_parts.append(f"**支付**：{c['pay']}")
            w(f"| 退款 / 实名 / 支付 | {esc_cell(' ｜ '.join(pol_parts), 340)} |")
        if c["features"]:
            w(f"| 实测核心特点 | {esc_cell('；'.join(c['features']), 360)} |")
        if c["rep_lines"]:
            rep_fmt = "；".join(
                f"**{r['name']}**（{r['desc'] + '，' if r['desc'] else ''}{r['spec']}）" if r["spec"] else f"**{r['name']}**（{r['desc']}）"
                for r in c["rep_lines"]
            )
            w(f"| 代表产品线与参考价 | {esc_cell(rep_fmt, 420)} |")
        if c["meow_comment"]:
            w(f"| 猫猫博客锐评 | {esc_cell(c['meow_comment'], 380)} |")
        if c["mjj_comments"]:
            w(f"| 社区用户反馈摘录 | {esc_cell(' ｜ '.join(c['mjj_comments'][:2]), 340)} |")
        w("")

        if not v["articles"]:
            w(
                "> 📌 **专测说明**：`netcup` 目前在猫猫博客以皇冠建站托管商家身份正式收录（MeowVPS 本站即托管于 netcup），"
                "官方暂未单独发布单篇脚本跑分博文。选购其德国卡尔斯鲁厄 **RS 1000 G12（独享 EPYC 核 / SLA 99.9%）** 或 **VPS 500 G12** 时，"
                "建议留意每月月底固定翻倍活动、准备好真实账单资料通过人工审核，并搭配上方 **1.1 欧洲 9929 / 荷兰搬瓦工前置** 或 Cloudflare 反代获得最佳大陆访问体验。"
            )
            w("")
            continue

        for idx, art in enumerate(v["articles"]):
            h3_title = f"专测 {idx + 1}：{art['title']}（{art['date']}）"
            w(f"### {h3_title}")
            w("")
            w(f"- **猫猫官方评测原文**：[{art['title']}]({art['url']})（发布日期：`{art['date']}`）")

            takeaways = []
            seen_t = set()
            for btag, btxt in art["blocks"]:
                if len(btxt) < 18 or btxt in seen_t:
                    continue
                if any(skip in btxt for skip in ("欢迎来到", "如果你不知道", "免责声明", "版权归", "未经允许", "点击前往购买", "优惠码：")):
                    continue
                seen_t.add(btxt)
                takeaways.append(esc_cell(btxt, 220))
                if len(takeaways) >= 5:
                    break
            if takeaways:
                w("- **专测要点摘录**：")
                for tk in takeaways:
                    w(f"  - {tk}")
            w("")

            if art["combined_pre"]:
                pre_clean = wrap_pre(art["combined_pre"])
                n_lines = len(pre_clean.splitlines())
                details_emitted += 1
                w("<details>")
                w(f"<summary>展开查看猫猫专测终端报告原文（摘录 {art['pre_kept_count']}/{art['pre_total_count']} 段 · 共 {n_lines} 行）</summary>")
                w("")
                w("```text")
                w(pre_clean)
                w("```")
                w("")
                w("</details>")
                w("")

    # ---------- Footer Cross-Link ----------
    w("## 上下卷联动与选机延伸阅读")
    w("")
    w("- **想查近期新冒头的黑马商家与 457 条论坛实测？** 请看 **[上卷：NodeSeek 商家测评汇总：MeowVPS 新收录 57 家商家的产品线与 NQ/TQ 原文](/archives/nodeseek-merchant-reviews-2026h2)**（涵盖 61 家新晋/转正商家与 319 份可展开终端报告原文）。")
    w("- **想看猫猫博客跨商家横向对比跑分？** 请参考 [**《热门机器横评系列(1)：美西优化线路》**](https://meowvps.com/blog/benchboxus/) 与 [**《热门机器横评系列(2)：欧洲线路机器》**](https://meowvps.com/blog/benchboxeu/)。")
    w("- **不确定怎么看单线程、重传、双 ISP 与流量池？** 请看 **[VPS 测评怎么读：带宽、IP 标签与流量成本](/archives/reading-vps-reviews)**。")
    w("- **买好线路机与家宽落地后怎么串成完整链路？** 请看 **[VPS 线路与落地怎么搭：链式代理、反向隧道与 Po0](/archives/relay-and-egress-guide)** 与 **[Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback)**。")
    w("")

    full_md = "\n".join(MD)

    assert full_md.count("```") % 2 == 0, "Unbalanced code fences!"
    assert full_md.count("<details>") == details_emitted and full_md.count("</details>") == details_emitted
    bad_tbl = [l for l in full_md.splitlines() if l.startswith("| ") and l.endswith("\\|")]
    assert not bad_tbl, f"Malformed table rows: {bad_tbl[:3]}"
    assert "aff=" not in full_md.lower() and "aff.php" not in full_md.lower(), "Affiliate link leaked!"

    open(out_path, "w", encoding="utf-8").write(full_md)
    print(f"VOL2 TEMPLATED SUCCESS: 56/56 vendors, {total_tax_rows} taxonomy entries, {details_emitted} <details> blocks, {len(full_md):,} chars ({len(full_md.splitlines()):,} lines) -> {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/vol2_templated.md")
    args = ap.parse_args()
    build_vol2(args.out)
