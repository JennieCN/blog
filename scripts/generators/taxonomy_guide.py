# -*- coding: utf-8 -*-
"""
MeowVPS (猫猫博客) VPS 分类体系 × 地区全景导览生成器（含三网选机、组网配对、防坑微标签与一线标杆参照）
层级：大类 (线路机 / 落地机 / 性能·建站·存储独服 / 归档避雷) -> 细分小类 -> 地区 -> 具体机型 (带精确锚点跳转)
"""
import re


def A(label, h2, h3=None):
    if h3:
        return f"[{label}]({{{{ANCHOR:{h2}||{h3}}}}})"
    return f"[{label}]({{{{ANCHOR:{h2}}}}})"


def S(label, sub_h3):
    return f"[{label}]({{{{ANCHOR_SELF:{sub_h3}}}}})"


TAXONOMY_DATA = [
    {
        "cat_h2": "一、线路机（CN 大陆优化线路 / 前置中转机）",
        "cat_desc": (
            "按猫猫博客《热门地区服务器 VPS 推荐》与《常见线路科普》口径，**线路机**指具备中国大陆方向直连路由优化、低延迟且抗晚高峰 QoS 的机器，"
            "既可直接日常使用，也常作为拉取海外家宽/落地的**前置中转机**。下分**精品优化与专线**、**普通骨干优化与单网快乐机**、**优化线路 + 双 ISP 伪家宽复合机**三小类。"
        ),
        "subcats": [
            {
                "sub_h3": "1.1 精品优化与专线（CN2 GIA / CTGNet / 9929 / CMIN2 / 沪日专线）",
                "sub_desc": (
                    "三网各自顶级优化（电信 CN2 GIA 或 CTGNet、联通 9929/10099、移动 CMIN2）、三网 CN2 GIA、三网 9929 及内网专线，主打全天候低丢包与晚高峰稳速，**电信用户必看此档**。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：美西/香港/日本顶配稳度标杆为 [**DMIT**](/archives/meowvps-official-merchants-2026h2#dmit)（皇冠推荐）、[**搬瓦工 BWH**](/archives/meowvps-official-merchants-2026h2#搬瓦工bwh)（皇冠推荐）；亚太龙系三网各自优化标杆为 [**Gomami（狗妈咪）**](/archives/meowvps-official-merchants-2026h2#gomami狗妈咪)、[**Neburst（奶爸）**](/archives/meowvps-official-merchants-2026h2#neburst奶爸)；欧洲 9929/CN2 老牌参照 [**咸鱼云 SaltyFish**](/archives/meowvps-official-merchants-2026h2#saltyfish咸鱼云)、[**AkkoCloud**](/archives/meowvps-official-merchants-2026h2#akkocloud)、[**V.PS（小秘书）**](/archives/meowvps-official-merchants-2026h2#vps小秘书)。\n"
                    "> 📊 **猫猫博客官方同场横评对照**：[**《热门机器横评系列(1)：美西优化线路》**](https://meowvps.com/blog/benchboxus/)（搬瓦工 MegaBOX / DMIT / VMISS / VMRack 同台实测）｜[**《热门机器横评系列(2)：欧洲线路机器》**](https://meowvps.com/blog/benchboxeu/)（德/荷/英/俄 15 台线路机横评）。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("Peekabo Networks", A("香港 HK（龙系三网精品）", "Peekabo Networks"), "龙系上游，三网各自顶级回程（CTGGIA / 9929 / CMIN2）+ GSL 国际互联"),
                        ("六六云 666Clouds", A("香港优化新机", "六六云 666Clouds", "产品线四：香港优化新机"), "AS150452，电信 CTGGIA / 联通 10099 / 移动 CMIN2 回程优化"),
                        ("wawo（哇沃主机）", " / ".join([
                            A("HK-Simple-2G-47", "wawo（哇沃主机）", "产品线一：香港 HK-Simple-2G-47（Hk-Kvm-ipv4-D 组）"),
                            A("HK-Simple-0.5G", "wawo（哇沃主机）", "产品线二：香港 HK-Simple-0.5G"),
                            A("HK-Simple-1G-SE", "wawo（哇沃主机）", "产品线三：香港 HK-Simple-1G-SE-2G"),
                            A("HK-One-0.5G", "wawo（哇沃主机）", "产品线四：香港 HK-One-0.5G-52-LS（Hkone-Kvm-B 组）"),
                        ]), "高性价比香港直连优化系列（D 组实测含 CTGGIA / 10099 / CMIN2，59 元/年起）"),
                        ("HKCloudX", " / ".join([
                            A("香港 BGP 优化（老 200M）", "HKCloudX", "产品线一：香港 BGP 优化（老 200M）"),
                            A("迁移 AMD 款（$49/年）", "HKCloudX", "产品线二：迁移 AMD 后 · 香港 BGP 优化（2C4G，49 美元/年）"),
                            A("11 月复测", "HKCloudX", "产品线四：11 月 16 日复测"),
                        ]), "AS62468，回程含电信 CN2/CTGGIA 与联通优化，迁移 AMD 后性能提升"),
                        ("GoldCloud", A("香港三网优化 · 建站 7K62 / CMI HK", "GoldCloud", "产品线一：香港三网优化 · 建站 7K62 / CMI HK"), "EPYC 7K62 宿主机，电信 CTGGIA / 联通 10099 / 移动 CMI 三网优化兼建站"),
                        ("VmShell", " / ".join([
                            A("香港 CMIN2-WEBAPP", "VmShell", "产品线一：香港 CMIN2-WEBAPP"),
                            A("CMIN2.HK-Classic", "VmShell", "产品线二：香港 CMIN2.HK-Classic"),
                        ]), "AS40065，主打移动 CMIN2 精品回程的小带宽轻量香港机"),
                        ("ShanDun Network", A("香港 HK Standard China Route", "ShanDun Network", "产品线四：香港 HK Standard China Route"), "AS401701，电信 CTGGIA / 移动 CMI 香港大陆直连线"),
                    ]),
                    ("日本（JP · 东京）", [
                        ("NoBrand", A("沪日 200M 专线（福建电信实测）", "NoBrand", "产品线七：沪日 200M 专线（福建电信实测）"), "`[内网专线]` 沪日专线直通东京，绕开公网跨境拥堵，延迟极稳"),
                        ("NOSLA", A("东京（26 国庆 S）", "NOSLA", "产品线四：东京（26 国庆 S）"), "xTom Japan（AS3258）上游，三网各自顶级回程（CTGGIA / 9929 / CMIN2）"),
                    ]),
                    ("新加坡（SG）", [
                        ("LazyCatCloud（懒猫云）", A("新加坡线路机（SG-Premium / Basic，上游狗妈）", "LazyCatCloud（懒猫云）", "产品线二：新加坡线路机（SG-Premium / Singapore Basic，上游狗妈）"), "GoMami 龙系上游（AS36002），三网各自顶级（CTGGIA / 9929 / CMIN2），面板可一键绑多国家宽"),
                    ]),
                    ("美国（US · 洛杉矶 LAX / 圣何塞 SJC）", [
                        ("六六云 666Clouds", A("美国原生 IP 三网 CN2 GIA", "六六云 666Clouds", "产品线一：美国原生 IP 三网 CN2 GIA"), "AS979 美西原生 IP + 三网回程 CN2 GIA，含 200Mbps 大带宽款"),
                        ("PanstarCloud", " / ".join([
                            A("美国 LAX Premium DC2", "PanstarCloud", "产品线一：美国 LAX Premium DC2（CN2 / 9929 / CMIN2 三网优化）"),
                            A("商家详测", "PanstarCloud", "商家自营测评"),
                        ]), "`[新晋热门]` 洛杉矶三网各自顶级优化（CN2 / 9929 / CMIN2），近期社区留档最密集"),
                        ("ZgoCloud", A("洛杉矶 AMD Optimised 三网精品", "ZgoCloud", "产品线一：美国洛杉矶 · AMD Optimised 三网精品（CN2 GIA & 9929 & CMIN2）"), "高频 AMD EPYC/Ryzen + 洛杉矶三网各自顶级回程（CN2 GIA / 9929 / CMIN2）"),
                        ("艾云 iaClouds", A("洛杉矶 Enterprise-GGBOOM 三网 CN2 GIA", "艾云 iaClouds（破云 / Brea.cloud）", "产品线二：美国洛杉矶 · Enterprise-GGBOOM 三网 CN2 GIA（280~300 HKD/年）"), "280~300 HKD/年高性价比美西三网 CN2 GIA 年付活动款"),
                        ("FXTRANSIT", A("美西大陆优化 · US NOVA（$36/年）", "FXTRANSIT", "产品线一：美西大陆优化 · US NOVA（$36/年）"), "Sakura Link / DMIT 系上游（AS49304），CN2 GIA / 9929 美西精品年付款"),
                        ("NOSLA", " / ".join([
                            A("圣何塞精品优化（小杯）", "NOSLA", "产品线二：圣何塞精品优化（小杯，已过白）"),
                            A("圣何塞 26 国庆版", "NOSLA", "产品线一：圣何塞 SJC（26 国庆特别版）"),
                            A("洛杉矶 LAX", "NOSLA", "产品线三：洛杉矶 LAX"),
                        ]), "xTom（AS6233）/ Fastnet 上游，圣何塞与洛杉矶三网各自精品优化（CN2 / 9929 / CMIN2）"),
                        ("CloudSilk（白丝云）", A("圣何塞精品大陆优化 BGP（三网 9929）", "CloudSilk（白丝云）", "产品线二：美国圣何塞 · 精品大陆优化 BGP（三网 9929）"), "Kirino（K 系）上游，圣何塞三网 9929 稳定回程代表"),
                        ("FlawlessNode", A("LAX Pro（三网回程 9929）", "FlawlessNode", "产品线二：LAX Pro（三网回程 9929）"), "`[单向出站计费]` SLA Network 原生老宽带段 + 洛杉矶三网 9929 回程，兼顾直连与解锁"),
                        ("PPFlight", " / ".join([
                            A("LIFT S1（$33/年）", "PPFlight", "产品线一：LIFT S1（创始人版 33 刀/年）"),
                            A("LIFT S2", "PPFlight", "产品线二：LIFT S2（5.49 刀/月）"),
                            A("Glide S", "PPFlight", "产品线三：Glide S（创始人套餐）"),
                            A("Plus-s", "PPFlight", "产品线四：Plus-s"),
                            A("洛杉矶三网 CN2-GIA", "PPFlight", "产品线五：洛杉矶三网 CN2-GIA（TQ 文本复测）"),
                        ]), "`[新晋商家]` 洛杉矶 CTGGIA / 9929 / CMIN2 三网各自优化及三网 CN2 GIA 创始人系列"),
                        ("HHost", " / ".join([
                            A("LA China Optimized（换 IP 前）", "HHost", "产品线一：LA China Optimized（换 IP 前）"),
                            A("换 IP 后复测", "HHost", "产品线二：LA China Optimized（11 月 12 日换 IP 后）"),
                        ]), "洛杉矶三网各自精品回程（CN2 GIA / 9929 / CMIN2），11 月换新段后质量提升"),
                        ("LamHosting", A("美国 USCR-Zero / USCR-A", "LamHosting", "产品线三：美国 USCR-Zero / USCR-A"), "美西 CN2 / 9929 / CMIN2 三网大陆优化线"),
                        ("VPS.TAXI", " / ".join([
                            A("洛杉矶 512M（$3/月）", "VPS.TAXI", "产品线一：洛杉矶 512M（约 3 刀/月）"),
                            A("洛杉矶 24 刀年付", "VPS.TAXI", "产品线二：洛杉矶 24 刀年付"),
                            A("30 刀年付等其他套餐", "VPS.TAXI", "产品线六：其他套餐"),
                        ]), "AS149513 Vertex 上游，洛杉矶 9929 / CMIN2 低门槛轻量线（其他套餐亦含美西 10 刀与软银）"),
                        ("GatewaySentry", A("洛杉矶 LAX · VPS-4 与 CN2 款", "GatewaySentry", "产品线一：美国洛杉矶 LAX · VPS-4 与 CN2 款"), "洛杉矶 CN2 / 9929 / CMIN2 大陆优化款"),
                        ("JDIDC", A("美国 3 区 · 9929（4H8G，100M）", "JDIDC"), "AS979 NetLab 段，美西 9929 回程高内存建站/代理款"),
                        ("ShanDun Network", A("US Premium China Route（与双 ISP 同节）", "ShanDun Network", "产品线三：美国优化与双 ISP（US Premium China Route / 4837 ISP / NTT）"), "美西 CN2 / 9929 / CMIN2 精品直连档（同节另含 4837/NTT 双 ISP）"),
                    ]),
                    ("欧洲（EU · 德国 DE / 英国 UK / 俄罗斯 RU）", [
                        ("六六云 666Clouds", A("德国 DE 9929 年付特价（249 元/年）", "六六云 666Clouds", "产品线三：德国 DE 9929 年付特价"), "法兰克福三网 9929 回程，300Mbps / 820G 年付特惠"),
                        ("CloudSilk（白丝云）", A("德国 · 精品大陆优化 BGP（三网 9929）", "CloudSilk（白丝云）", "产品线三：德国 · 精品大陆优化 BGP（三网 9929）"), "K 系经典法兰克福三网 9929 稳定线路，拉欧洲性能机与西班牙家宽首选前置"),
                        ("艾云 iaClouds", A("德国法兰克福 · 三网 9929 优化（DE9929 / 双 11 Pro）", "艾云 iaClouds（破云 / Brea.cloud）", "产品线一：德国法兰克福 · 三网 9929 优化（DE9929 / 双 11 Pro / Ciallo）"), "高人气法兰克福三网 9929 促销线（含与 Ciallo 联名款）"),
                        ("PanstarCloud", A("德国 DEPro", "PanstarCloud", "产品线二：德国 DEPro"), "POLONETWORK 上游，法兰克福 500M 端口 9929 / 10099 优化小鸡"),
                        ("LamHosting", " / ".join([
                            A("德国 DE 9929", "LamHosting", "产品线一：德国 DE 9929"),
                            A("DECR-Zero", "LamHosting", "产品线五：DECR-Zero"),
                        ]), "POLONETWORK 上游，法兰克福三网 9929 回程优化"),
                        ("ShanDun Network", A("德国法兰克福 DE 9929（$2/月起）", "ShanDun Network", "产品线一：德国法兰克福 DE 9929（$2/月起）"), "低月付门槛法兰克福 9929 / CTGGIA 优化小鸡"),
                        ("LazyCatCloud（懒猫云）", A("德国 DE-9929（与美西 4837 同节）", "LazyCatCloud（懒猫云）", "产品线三：美国 LAX-Lite（4837）与德国 DE-9929"), "法兰克福三网 9929 欧洲中转前置"),
                        ("GoodlyCloud（吉云）", A("英国伦敦 · 原生 IP 9929 + CMIN2（299 元/年起）", "GoodlyCloud（吉云）", "产品线一：英国伦敦 · 原生 IP 9929 + CMIN2（299 元/年特价起）"), "伦敦英国原生 IP + 电信联通 9929 / 移动 CMIN2 回程，直连解锁兼备"),
                        ("Misaka", " / ".join([
                            A("德国柏林 Berlin CN2 / PREM-Pro", "Misaka", "产品线一：德国柏林 · Berlin CN2 与 PREM-Pro"),
                            A("俄罗斯莫斯科 CN2 GIA", "Misaka", "产品线二：俄罗斯莫斯科 · CN2 GIA（Misaka-Ru-Pro）"),
                        ]), "稀缺柏林 CN2 与莫斯科三网 CN2 GIA 超低延迟高端欧俄线"),
                    ]),
                    ("其他亚太地区（中国澳门 MO）", [
                        ("VmShell", A("澳门 CMIN2-IP.MO-Lite", "VmShell", "产品线三：澳门 CMIN2-IP.MO-Lite"), "稀缺澳门 IP 定位 + 移动 CMIN2 精品回程小鸡"),
                    ]),
                ],
            },
            {
                "sub_h3": "1.2 普通骨干优化与单网快乐机（4837 / 10099 / CMI / 软银 SoftBank / IIJ / Lumen）",
                "sub_desc": (
                    "以美西三网 4837 大流量、亚太 CMI / Lumen 移动快乐机、日本 SoftBank（联通快乐）/ IIJ 为主；价格亲民、带宽流量给得足，适合联通/移动用户高性价比直连（电信晚高峰易波动）。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：亚太 CMI / Lumen / 大带宽优化老牌参照 [**RFCHOST（花卷科技）**](/archives/meowvps-official-merchants-2026h2#rfchost花卷科技)、[**ISIF Cloud**](/archives/meowvps-official-merchants-2026h2#isif-cloud)、[**绿云 GreenCloud**](/archives/meowvps-official-merchants-2026h2#greencloud绿云)、[**VMISS**](/archives/meowvps-official-merchants-2026h2#vmiss)、[**Nube**](/archives/meowvps-official-merchants-2026h2#nube)。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("PanstarCloud", A("香港 HK Pro / HKP / HKS", "PanstarCloud", "产品线四：香港 HK Pro / HKP / HKS"), "10099 / CMI / 163 混合直连，定位轻量亚太入门"),
                        ("CloudSilk（白丝云）", A("香港绝版 CMI BGP", "CloudSilk（白丝云）", "产品线四：香港绝版 CMI BGP"), "Kirino 上游，三网回程 CMI / 10099 存量款"),
                        ("LazyCatCloud（懒猫云）", A("香港线路机（HK-Lite 双栈 Lumen / HKG-Basic）", "LazyCatCloud（懒猫云）", "产品线一：香港线路机（HK-Lite 双栈 Lumen / HK-Lumen / HKG-Basic）"), "`[移动快乐]` 主打双栈 Lumen 直连及亚太家宽中转前置"),
                        ("Zouter", A("香港 HK BGP Global（103 段 AMD）", "Zouter", "产品线一：香港 HK BGP Global（Standard / Lite / Debut 103 段）"), "`[移动+教育网快乐]` 大带宽香港 AMD 机（电联绕路，偶受 DDoS 影响）"),
                        ("ZgoCloud", A("香港 HongKong AMD Specials（$45/年起）", "ZgoCloud", "产品线四：香港 · HongKong AMD Specials（Starter $45/年 / Lite / 季付）"), "AMD 高频硬件 + 10099/CMI 移动联通友好香港特惠款"),
                        ("FXTRANSIT", A("香港 China Access AXIS 与 HK Nova", "FXTRANSIT", "产品线四：香港 China Access AXIS 与 HK Nova"), "香港 CMI / 163 基础大陆直连访问线"),
                        ("JTTI", A("香港 HK（$49/年）", "JTTI", "产品线一：香港 HK（$49/年）"), "香港年付直连入门机，晚高峰 TQ 实测存在波动"),
                        ("HaloCloud", A("香港 HK Lite", "HaloCloud", "产品线一：香港 HK Lite"), "香港轻量移动友好入门款"),
                        ("GoldCloud", A("香港 HK-DC2 小水管款", "GoldCloud", "产品线二：香港 HK-DC2 小水管款"), "低价小带宽香港直连备用款"),
                    ]),
                    ("日本（JP · 东京 / 大阪）", [
                        ("VPS.TAXI", A("东京软银（Mini $10/年起）", "VPS.TAXI", "产品线四：东京软银"), "`[联通快乐]` 东京 SoftBank 1Gbps 大口，闲时高速、晚高峰视地区波动"),
                        ("ZgoCloud", A("日本大阪 · 周年特惠大阪 IIJ", "ZgoCloud", "产品线五：日本大阪 · 周年特惠大阪 IIJ"), "经典日本三网 IIJ 直连线路 + AMD 强劲硬件"),
                        ("Zouter", A("日本东京 JP BGP Global（14 段与 216 段）", "Zouter", "产品线二：日本东京 JP BGP Global（Standard / Debut / Plus，14 段与 216 段）"), "`[联通/移动快乐]` SoftBank / IIJ / Lumen 混合大带宽"),
                        ("NoBrand", " / ".join([
                            A("Super Chicken 59 Y2", "NoBrand", "产品线一：Super Chicken 59 Y2"),
                            A("JP-TYO-1", "NoBrand", "产品线三：JP-TYO-1"),
                            A("新旧站 TY", "NoBrand", "产品线四：新站 TY 与旧站 TY"),
                            A("Super KFC 9.9", "NoBrand", "产品线五：Super KFC 9.9"),
                            A("NewNB 65 折", "NoBrand", "产品线六：NewNB 65 折循环（tokyo-1C 0.5G 1T）"),
                        ]), "Skyline Connect 等上游，电信一般、联通移动快乐的超低价东京性价比线"),
                        ("LegendVPS", A("日本东京 JP-Spark-1G（$18/年）", "LegendVPS", "产品线三：日本东京 JP-Spark-1G（$18/年）"), "`[11月换老板·建议观望/月付]` Skyline 系联通移动快乐 + 多库家宽属性"),
                        ("LamHosting", A("日本 JPCR-Zero / Japan", "LamHosting", "产品线二：日本 JPCR-Zero / Japan"), "IIJ / SoftBank / Lumen 混合日本直连线"),
                        ("JTTI", A("日本东京 JP-1C-1G-50G（$35/年）", "JTTI", "产品线二：日本东京 JP-1C-1G-50G（35 USD/年）"), "东京 IIJ / 10099 / CMI 回程年付直连机"),
                        ("HaloCloud", A("日本 JP Standard（500GB）", "HaloCloud", "产品线三：日本 JP Standard（500GB）"), "含 SoftBank / Akari / GSL 的东京直连兼国际互联款"),
                        ("BreadCloud（面包云）", " / ".join([
                            A("日本 JP - Bite（$12/年）", "BreadCloud（面包云）", "产品线二：日本 JP - Bite（年付 12 刀）"),
                            A("新 IP 自测", "BreadCloud（面包云）", "产品线四：日本 JP（新 IP 自测）"),
                        ]), "12 刀/年 3Gbps 端口，IPv6 移动单线程可达 270Mbps+"),
                    ]),
                    ("美国（US · 洛杉矶 LAX / 圣何塞 SJC）", [
                        ("CloudSilk（白丝云）", A("圣何塞大陆优化 BGP（回程三网 4837）", "CloudSilk（白丝云）", "产品线一：美国圣何塞 · 大陆优化 BGP（回程三网 4837）"), "猫猫点名推荐的美西 K 系三网 4837 大流量性价比代表"),
                        ("FlawlessNode", A("LAX Basic Special（36 刀年付）", "FlawlessNode", "产品线一：LAX Basic Special（36 刀年付）"), "猫猫点名推荐的洛杉矶三网 4837 回程高流量年付款"),
                        ("艾云 iaClouds", A("美国 GGBOOM 4837（160 HKD/年）", "艾云 iaClouds（破云 / Brea.cloud）", "产品线三：美国 · GGBOOM 4837（1.5TB，160 HKD/年）"), "160 HKD/年 1.5TB 流量的低门槛美西 4837 直连机"),
                        ("GoldCloud", A("洛杉矶 US-DC1（三网 4837 回程建站机）", "GoldCloud", "产品线三：美国洛杉矶 US-DC1（三网 4837 回程建站机）"), "美西三网 4837 回程兼顾常规建站"),
                        ("HaloCloud", A("洛杉矶 Akari 4837（测速）", "HaloCloud", "产品线五：洛杉矶 Akari 4837（测速）"), "Akari 上游洛杉矶 4837 回程款"),
                        ("LazyCatCloud（懒猫云）", A("美国 LAX-Lite（4837）", "LazyCatCloud（懒猫云）", "产品线三：美国 LAX-Lite（4837）与德国 DE-9929"), "洛杉矶三网 4837 入门直连与美区前置"),
                    ]),
                ],
            },
            {
                "sub_h3": "1.3 优化线路 + 双 ISP 伪家宽复合机（大陆优化回程 + 双 ISP 二合一）",
                "sub_desc": (
                    "自带大陆三网 9929 / CMIN2 或 4837 回程优化，同时挂载 Cogent / NTT / GTT 等在多数数据库中标为 `ISP`（双 ISP）的伪家宽 IP 段，"
                    f"适合不想单独折腾前置中转、希望单机兼顾直连与 TikTok/流媒体轻量落地的用户。（无大陆直连优化的纯伪家宽见下方 {S('2.3 伪家宽', '2.3 伪家宽（双 ISP 属性机房 IP · 无大陆直连优化）')}。）\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：美西优化 + 双 ISP 赛道同类参照 [**SixtyNet**](/archives/meowvps-official-merchants-2026h2#sixtynet)、[**NovixLink（诺联主机）**](/archives/meowvps-official-merchants-2026h2#novixlink诺联主机)、[**ZoroCloud（索隆云）**](/archives/meowvps-official-merchants-2026h2#zorocloud索隆云)、[**YUNYOO（云悠）**](/archives/meowvps-official-merchants-2026h2#yunyoo云悠)。"
                ),
                "regions": [
                    ("美国（US · 洛杉矶 LAX）", [
                        ("LisaHost（丽萨主机）", A("美国洛杉矶 9929 精品网络双 ISP 住宅 IP", "LisaHost（丽萨主机）", "产品线一：美国洛杉矶 9929 精品网络双 ISP 住宅 IP"), "AS174 Cogent 双 ISP 住宅标 + 三网回程 9929 精品网二合一代表"),
                        ("ZgoCloud", A("洛杉矶 AMD 双 ISP 优化（9929 / CMIN2，$58/年起）", "ZgoCloud", "产品线二：美国洛杉矶 · AMD 双 ISP 优化（9929 / CMIN2，$58/年起）"), "AS2914 NTT 双 ISP + 电联 9929 / 移动 CMIN2 + 高频 AMD 处理器"),
                        ("六六云 666Clouds", A("美西 4837 伪家宽 / NTT 双 ISP 特惠机（199 元/年）", "六六云 666Clouds", "产品线二：美西 4837 伪家宽 / NTT 双 ISP 特惠机"), "AS2914 NTT 双 ISP + 美西三网 4837 回程年付特价款"),
                        ("GoodlyCloud（吉云）", A("洛杉矶 NTT 双 ISP + 三网 4837 回程", "GoodlyCloud（吉云）", "产品线二：美国洛杉矶 · NTT 双 ISP + 三网 4837 回程"), "NTT 双 ISP 属性配合洛杉矶三网 4837 直连回程"),
                        ("ShanDun Network", A("美国 4837 ISP / NTT 双 ISP", "ShanDun Network", "产品线三：美国优化与双 ISP（US Premium China Route / 4837 ISP / NTT）"), "AS2914 NTT 双 ISP + 美西 4837 / 9929 大陆回程优化"),
                    ]),
                    ("欧洲（EU · 英国伦敦 UK）", [
                        ("ShanDun Network", A("英国伦敦 UK 9929 ISP", "ShanDun Network", "产品线二：英国伦敦 UK 9929 ISP"), "AS3257 GTT 多库家宽属性 + 伦敦三网 9929 大陆优化回程"),
                    ]),
                ],
            },
        ],
    },
    {
        "cat_h2": "二、落地机（流量出口 / 流媒体解锁 / 家宽身份机）",
        "cat_desc": (
            "按猫猫博客《VPS IP 质量检测指南》与《行业黑话》定义，**落地机**直接暴露在目标网站面前代表你的网络身份，一般无大陆直连优化（需配合上方线路机中转拉取），"
            "核心看 **IP 库类型与纯净度、AI / 流媒体解锁、国际互联（Tier1 / GSL / Akari）**。下分**真家宽/商宽（独立 IP）**、**真家宽/商宽（NAT 共享）**、**伪家宽**、**机房落地机**四小类。"
        ),
        "subcats": [
            {
                "sub_h3": "2.1 真家宽 / 商宽（独立静态·动态 IP）",
                "sub_desc": (
                    "由真实本土宽带运营商（AT&T、Frontier/Verizon、Spectrum、NetWest、Wave、Hinet、Seednet、WTT、SKB、Sistec、Exetel、VNPT、Starlink 等）分配独立 IPv4，在 IP2Location / MaxMind 等严苛库中均为真实 ISP/商宽，适合高风控 AI、金融、电商店铺注册与纯净本土业务。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：亚太真家宽皇冠推荐 [**Boil の家裡雲（港仔）**](/archives/meowvps-official-merchants-2026h2#boil-の家裡雲港仔)，美国家宽皇冠推荐 [**qqpw（夏威夷家宽）**](/archives/meowvps-official-merchants-2026h2#qqpw夏威夷家宽)，老牌美/台/日家宽另可对照 [**VIRCS（威尔克斯）**](/archives/meowvps-official-merchants-2026h2#vircs威尔克斯)、[**WireCat（维猫）**](/archives/meowvps-official-merchants-2026h2#wirecat维猫)、[**PittQiao（PQS）**](/archives/meowvps-official-merchants-2026h2#pittqiaopqs)、[**Tokyonline**](/archives/meowvps-official-merchants-2026h2#tokyonline)、[**Mondoze（大马 TMNet）**](/archives/meowvps-official-merchants-2026h2#mondoze)。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("Tamago Network", A("香港 WTT 商宽动态 IP（独立 IP）", "Tamago Network", "产品线一：香港 WTT 商宽动态 IP（独立 IP）"), "`[动态 IP 重拨]` HKBN/WTT 商业宽带独立 IPv4 + 7945HX 宿主机，500Mbps/2.5TB"),
                    ]),
                    ("日本（JP · 东京 / 北海道）", [
                        ("RadoNet", " / ".join([
                            A("日本 Starlink 星链家宽", "RadoNet", "产品线二：日本 Starlink 星链家宽"),
                            A("东京 BIGLOBE 与北海道软银家宽", "RadoNet", "产品线三：东京 BIGLOBE 与北海道软银家宽（2026 年 5 月初留档）"),
                        ]), "`[动态 IP]` AS14593 SpaceX 星链与 BIGLOBE（AS2518）/ 北海道 SoftBank 独享真家宽"),
                        ("AWS Wavelength（猫猫留档）", A("日本 KDDI 5Gbps 家宽（双入口留档）", "猫猫博客非目录特殊家宽留档（2 篇）", "留档一：AWS Wavelength 日本 KDDI 5Gbps 家宽测评（2026-02-11）"), "`[非标品留档·偶掉线重开]` AWS 前置入站 + 纯正日本 KDDI 5Gbps 家宽出站双 IP 架构"),
                    ]),
                    ("中国台湾（TW）", [
                        ("HighEndNetwork", " / ".join([
                            A("SeedNet Home Broadband", "HighEndNetwork", "产品线一：SeedNet Home Broadband"),
                            A("Seednet Lavender", "HighEndNetwork", "产品线二：Seednet Lavender（IP 质量）"),
                            A("Seednet.Matcha", "HighEndNetwork", "产品线三：Seednet.Matcha"),
                            A("Hinet.Sencha（$400/年）", "HighEndNetwork", "产品线四：Hinet.Sencha（400 美元/年）"),
                            A("台湾家宽活动机", "HighEndNetwork", "产品线五：台湾家宽（活动机）"),
                        ]), "`[动态/静态可选]` 远传 Seednet（AS4780，国际互联更佳）与中华电信 Hinet（AS3462）五库全绿真家宽"),
                    ]),
                    ("美国（US · 加州 / 得州 / 西雅图 / 华盛顿 / 北卡）", [
                        ("干杯云 USVPS24", " / ".join([
                            A("AT&T 商业宽带 PRO", "干杯云 USVPS24", "产品线一：AT&T 商业宽带 PRO（网关升级版）"),
                            A("二号线", "干杯云 USVPS24", "产品线二：二号线"),
                            A("加州 AT&T 静态家宽", "干杯云 USVPS24", "产品线三：加州 AT&T 静态家宽"),
                            A("Frontier", "干杯云 USVPS24", "产品线四：Frontier"),
                        ]), "AS7018 AT&T 与 AS5650 Frontier 五库全绿静态真家宽/商宽，大带宽无限流量性价比高"),
                        ("BlossomHost", " / ".join([
                            A("得州 Odessa · NetWest（$17/月）", "BlossomHost", "产品线一：美国得州 Odessa · NetWest 家宽（ISP-XXS，$17/月）"),
                            A("西雅图 · Wave 10Gbps ISP", "BlossomHost", "产品线二：美国西雅图 · Wave 10Gbps ISP（ISP-XXS / ISP-XS）"),
                            A("华盛顿 · Verizon FiOS", "BlossomHost", "产品线三：美国华盛顿 · Verizon FiOS 家宽/商宽"),
                        ]), "NetWest（AS11238）、Wave（AS11404 10G 口）、Verizon FiOS（AS701）三地静态真家宽/商宽新锐"),
                        ("ATTVPS", A("美国加州 AT&T 静态家宽（$28.88/月起）", "ATTVPS"), "加州 AT&T 静态独立 IP，独享 50Mbps 无限流量 + EPYC 宿主机，送中期限内可换 IP"),
                        ("ResidentialVPS", A("美国 Pro AT&T 家宽（$40/月）", "ResidentialVPS", "产品线一：美国 Pro AT&T 家宽（$40/月）"), "`[Windows RDP 交付]` AS7018 AT&T 1Gbps 无限流量静态真家宽远程桌面"),
                        ("IPMELA", A("北卡罗来纳州 · Charter Spectrum 商宽（$25.99/月）", "IPMELA", "产品线一：美国北卡罗来纳州 · Charter Spectrum 商宽（$25.99/月）"), "`[VPS / RDP 可选]` 美东冷门北卡 Charter Spectrum 静态商宽，避开热门撞车段"),
                        ("神秘美国家宽（猫猫留档）", A("美国 AT&T 1Gbps 双栈家宽 + i9-13900K（留档）", "猫猫博客非目录特殊家宽留档（2 篇）", "留档二：神秘美国 AT&T 1Gbps 双栈家宽小鸡留档（2026-04-23）"), "`[非标品未公开来源留档]` 双栈完美 AT&T 真家宽（上行 1G/下行 700M）+ 13900K 怪兽级 IO"),
                    ]),
                    ("欧洲（EU · 西班牙 ES）", [
                        ("JCloudHosting", " / ".join([
                            A("KVM ECO（€2.95/月起）", "JCloudHosting（西班牙家宽）", "产品线一：KVM ECO（Xeon Gold 6154，€2.95/月起）"),
                            A("KVM HIGH", "JCloudHosting（西班牙家宽）", "产品线二：KVM HIGH（Xeon Gold 6430）"),
                            A("RYZEN（9900X，€9.98/月起）", "JCloudHosting（西班牙家宽）", "产品线三：RYZEN（Ryzen 9 9900X，€9.98/月起）"),
                            A("全线详测", "JCloudHosting（西班牙家宽）", "商家自营测评"),
                        ]), "AS198454 Sistec Telecom 五库全绿西班牙原生真家宽，€2.95/月地板价起，RYZEN 档兼备 9900X 强性能"),
                    ]),
                    ("其他亚太与大洋洲（韩国 KR / 越南 VN / 马来西亚 MY / 澳大利亚 AU）", [
                        ("NexKr", A("韩国 SKB 2000Mbps 大带宽真家宽（猫猫官方专测）", "NexKr"), "`[单向出站 60TB·可换 IP]` 韩国 SK Broadband（AS9318）五库全绿真家宽，送 5 个 DDNS，建议东京/香港中转（防送中需留意）"),
                        ("六六云 666Clouds", A("韩国 SEJONG 双 ISP 家宽/商宽（猫猫官方专测）", "六六云 666Clouds", "产品线五：韩国 SEJONG 双 ISP 与英国 GTT 原生 IP（猫猫官方专测）"), "上游直属韩国 SEJONG 原生静态 ISP（200Mbps 口），韩区本土流媒体完整解锁、滥用极少，建议港/日线路机中转（留意防送中）"),
                        ("TOTHOST", " / ".join([
                            A("越南河内 VNPT ISP · TOT K11（~$15/年）", "TOTHOST", "产品线一：越南河内 VNPT ISP · TOT K11（1C1G/20G，无限流量，约 $15/年）"),
                            A("越南双 ISP 家宽 · TOT GT", "TOTHOST", "产品线二：越南双 ISP 家宽 · VPS TOT GT（250Mbps 带宽）"),
                            A("越南 KVM 留档", "TOTHOST", "产品线三：越南 KVM IP 质量留档"),
                        ]), "越南国营宽带商 VNPT（AS45899 / AS135905）真家宽/ISP，无限流量年付约 $15"),
                        ("DataOnline", A("越南河内 · Cheap Cloud VPS 1（4 月底归档）", "DataOnline（近半年公开帖为 0 · 附 2026 年 4 月底测评）", "产品线一：越南河内 · Cheap Cloud VPS 1（2026 年 4 月底归档）"), "`[移动快乐]` 直属越南 VNPT 原生家宽属性出口，约 104 元/年无限流量"),
                        ("WePC（车库云）", " / ".join([
                            A("马来西亚家宽（95Mbps，猫猫专测）", "WePC（车库云）", "产品线二：马来西亚家宽与菲律宾原生 IP 伪家宽（猫猫官方专测）"),
                            A("澳大利亚墨尔本 Exetel 静态家宽与 AU 款", "WePC（车库云）", "产品线一：澳大利亚墨尔本 Exetel 静态家宽与 AU 入门款"),
                        ]), "稀缺大马本土纯落地家宽（新/马中转跑满 95Mbps 低重传）与澳洲 Exetel 静态家宽"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.2 真家宽 / 商宽（NAT 共享 IP 与多国家宽出口）",
                "sub_desc": (
                    "多人共享同一个真实家宽/商宽或蜂窝移动公网 IPv4（按端口映射或内置出口切换，无独立 80/443 建站端口），把动辄 $50+/月的亚太真家宽门槛压到几十元人民币，适合低预算体验纯净动态家宽。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：港台日共享/轻量家宽同类参照 [**Boil（港仔 NAT）**](/archives/meowvps-official-merchants-2026h2#boil-の家裡雲港仔)、[**MoonVM**](/archives/meowvps-official-merchants-2026h2#moonvm)、[**NMCloud（牛马云）**](/archives/meowvps-official-merchants-2026h2#nmcloud牛马云)、[**FacHost（工厂云）**](/archives/meowvps-official-merchants-2026h2#fachost工厂云)、[**KazeCloud**](/archives/meowvps-official-merchants-2026h2#kazecloud)、[**学长网络**](/archives/meowvps-official-merchants-2026h2#学长网络)。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("Tamago Network", " / ".join([
                            A("HKT NAT 500M", "Tamago Network", "产品线二：HKT NAT 500M（HKT.NAT.500M.VPS.6）"),
                            A("HKT NAT 2500M", "Tamago Network", "产品线三：HKT NAT 2500M"),
                            A("WTT NAT 1000M", "Tamago Network", "产品线四：WTT NAT 1000M"),
                        ]), "`[NAT 端口共享·动态 IP]` 香港电讯 HKT（AS4760）五库全绿家宽 NAT 与 WTT 商宽 NAT，最高 2.5G 口"),
                    ]),
                    ("日本（JP · 东京）", [
                        ("LazyCatCloud（懒猫云）", A("日本动态家宽 NAT（KDDI / BIGLOBE / SoftBank）", "LazyCatCloud（懒猫云）", "产品线四：日本动态家宽 NAT（KDDI / BIGLOBE / SoftBank）"), "`[NAT 共享·动态 IP]` AS2516 KDDI 等真家宽 NAT，面板可一键绑定香港/新加坡/美西线路前置"),
                        ("RadoNet", A("东京 KDDI 与 Rakuten 共享家宽 NAT", "RadoNet", "产品线一：日本东京 KDDI 与 Rakuten 共享家宽 NAT"), "`[NAT 共享·蜂窝/固网]` KDDI 固网与 Rakuten Mobile（AS138384 蜂窝属性）共享 NAT，部分带防送中分流"),
                    ]),
                    ("中国台湾（TW）", [
                        ("LamHosting", A("台湾 TW HiNet-A（7.99 元/月）", "LamHosting", "产品线四：台湾 TW HiNet-A（7.99 元/月）"), "`[NAT 共享·动态 IP]` 百元内年付级别的中华电信 Hinet 动态家宽 NAT 轻量款"),
                    ]),
                    ("多国聚合家宽出口（日 / 韩 / 新 / 菲）", [
                        ("LazyCatCloud（懒猫云）", A("全球家宽 Global 多国出口与前置切换对比", "LazyCatCloud（懒猫云）", "产品线五：全球家宽 Global 多国出口与前置切换对比"), "`[多国出口切换]` 单机聚合日本、韩国（KT/SEJONG）、新加坡（StarHub）、菲律宾（DITO）动态家宽出口"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.3 伪家宽（双 ISP 属性机房 IP · 无大陆直连优化）",
                "sub_desc": (
                    "在部分数据库中显示为 `ISP` / 双 ISP，但 IP2Location 等严格库判定为商业数据中心托管的机房产品；带宽稳、价格远低于真家宽，适合常规流媒体与轻度风控场景。"
                    "**注**：若需**自带 9929 / CMIN2 / 4837 大陆直连回程优化**的双 ISP 机器（如丽萨 US 9929、ZgoCloud/六六云/吉云/ShanDun 双 ISP），请见上方 "
                    f"{S('1.3 优化线路 + 双 ISP 伪家宽复合机', '1.3 优化线路 + 双 ISP 伪家宽复合机（大陆优化回程 + 双 ISP 二合一）')}。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：多国双 ISP / 原生住宅标落地参照 [**Yinnet（荫云）**](/archives/meowvps-official-merchants-2026h2#yinnet荫云)、[**IPRaft**](/archives/meowvps-official-merchants-2026h2#ipraft)、[**ZoroCloud（索隆云）**](/archives/meowvps-official-merchants-2026h2#zorocloud索隆云)、[**TapHip**](/archives/meowvps-official-merchants-2026h2#taphip)。"
                ),
                "regions": [
                    ("日本（JP · 东京）", [
                        ("NoBrand", A("COGENT TYO 2（10T 流量 G 口，58 元/年）", "NoBrand", "产品线二：COGENT TYO 2"), "东京 G 口 10TB 大流量低价伪家宽落地机（部分库标家宽）"),
                    ]),
                    ("新加坡（SG）", [
                        ("VPS.TAXI", A("新加坡（NTT ISP / 24 刀年付）", "VPS.TAXI", "产品线五：新加坡"), "AS2914 NTT 新加坡段，多库标家宽属性的东南亚落地小鸡"),
                        ("LegendVPS", " / ".join([
                            A("新加坡 SG-Evo（2C2G / 3C3G）", "LegendVPS", "产品线一：新加坡 SG-Evo 系列（2C2G / 3C3G）"),
                            A("SG-Lite（1G / 2G）", "LegendVPS", "产品线二：新加坡 SG-Lite 系列（1G / 2G）"),
                        ]), "`[11月换老板·建议观望/月付]` 双栈原生 + 多库家宽属性 + 移动快乐"),
                        ("WebHorizon", A("新加坡 Ryzen-KVM-1GB", "WebHorizon", "产品线一：新加坡 Ryzen-KVM-1GB（1C1G / 15G）"), "AS149020，多库标家宽属性 + GSL 国际互联的新加坡 Ryzen 小鸡"),
                    ]),
                    ("美国（US · 达拉斯 DAL / 洛杉矶 LAX）", [
                        ("Bocchi", A("达拉斯 Pulse（双 ISP 落地机）", "Bocchi", "产品线二：达拉斯 Pulse（双 ISP 落地机）"), "AS218613 自有双栈原生段 + 伪家宽属性 + EPYC 9455P 10Gbps 强性能落地"),
                        ("VPS.TAXI", A("洛杉矶 ISP Mini", "VPS.TAXI", "产品线三：洛杉矶 ISP Mini"), "美西低门槛入门双 ISP/伪家宽小鸡"),
                    ]),
                    ("欧洲（EU · 英国 UK）", [
                        ("LisaHost（丽萨主机）", A("英国双 ISP 住宅 IP", "LisaHost（丽萨主机）", "产品线二：英国双 ISP 住宅 IP"), "AS48266 Catixs 多库标家宽属性，主打英区 TikTok 与本土流媒体解锁"),
                        ("六六云 666Clouds", A("英国 GTT 原生 IP / 部分家宽标（1Gbps，猫猫专测）", "六六云 666Clouds", "产品线五：韩国 SEJONG 双 ISP 与英国 GTT 原生 IP（猫猫官方专测）"), "GTT 上游英国原生 IP（1Gbps 大口），德国中转 10~15ms 跑满千兆（注：受测段已送中）"),
                        ("PanstarCloud", A("英国 UK Lite（落地 $0.99/月）", "PanstarCloud", "产品线三：英国 UK Lite（落地 0.99$/月）"), "AS219393 多库标家宽属性的 $0.99/月超低价英区落地小鸡"),
                    ]),
                    ("其他亚太地区（菲律宾 PH）", [
                        ("六六云 666Clouds", A("菲律宾双 ISP（商家自营测评）", "六六云 666Clouds", "商家自营测评"), "稀缺菲律宾马尼拉双 ISP 住宅标落地机，适合香港前置中转拉取"),
                        ("WePC（车库云）", A("菲律宾原生 IP 伪家宽（移动 Lumen 快乐，猫猫专测）", "WePC（车库云）", "产品线二：马来西亚家宽与菲律宾原生 IP 伪家宽（猫猫官方专测）"), "`[移动快乐]` 罕见菲律宾多库家宽标原生 IP，移动走 Lumen 跑满 50Mbps，港系 BBIX 中转仅 17ms"),
                    ]),
                ],
            },
            {
                "sub_h3": "2.4 机房落地机（原生 IP 解锁 / Tier1·GSL·Akari 国际互联 / 廉价机房与玩具机）",
                "sub_desc": (
                    "标准商业机房 IP（不含家宽标），按功能分为三向：① **Akari / GSL / Tier1 国际互联组网机**（如港台 13ms 互联、10G 大口出口）；② **原生 IP / DNS 流媒体解锁机**；③ **百元内低价 KVM 练手/备用玩具机与纯 IPv6 机**。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：高品质原生流媒体解锁与国际互联落地标杆为 [**BageVM**](/archives/meowvps-official-merchants-2026h2#bagevm)、[**DigitalFyre**](/archives/meowvps-official-merchants-2026h2#digitalfyre)（皇冠推荐）、[**DataWave**](/archives/meowvps-official-merchants-2026h2#datawave)、[**Skyline Connect**](/archives/meowvps-official-merchants-2026h2#skyline-connect)、[**BestVM（富婆）**](/archives/meowvps-official-merchants-2026h2#bestvm富婆)。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("HostHatch", " / ".join([
                            A("香港 HK FLASH 3GB", "HostHatch", "产品线一：香港 HK FLASH 3GB"),
                            A("香港 3C3G", "HostHatch", "产品线六：香港 3C3G（TcpQuality）"),
                        ]), "接入 GSL / Lumen 的香港纯国际互联大流量落地机"),
                        ("LisaHost（丽萨主机）", A("香港机型", "LisaHost（丽萨主机）", "产品线三：香港机型"), "AS1014 NetLab 段香港流媒体解锁落地小鸡"),
                        ("Misaka", A("香港国际落地（亚太节点）", "Misaka", "产品线三：亚太节点（新加坡 S3N / 香港国际落地 / 台湾 TW）"), "无大陆直连优化的高规格香港国际机房落地"),
                        ("OrangeVPS", A("香港 HK BASIC-AP-1", "OrangeVPS", "产品线三：香港 HK 与日本东京 BASIC-AP-1"), "接入 GSL / Lumen 的香港低价年付国际落地款"),
                        ("Langya", A("香港落地机（3 月归档）", "Langya（近半年公开帖为 0 · 附 2026 年 3 月测评）", "产品线一：美国芝加哥 GSL 落地机与香港落地机（2026 年 3 月归档）"), "春季归档香港国际路由落地款"),
                        ("HKCloudX", A("MiniV6（香港 IPv6）", "HKCloudX", "产品线三：MiniV6"), "`[纯 IPv6 无 v4]` 超低成本香港 IPv6 纯落地玩具机"),
                        ("wawo（哇沃主机）", A("香港 IPv6-only", "wawo（哇沃主机）", "产品线五：香港 IPv6-only"), "`[纯 IPv6 无 v4]` 低价香港纯 IPv6 分流/练手小鸡"),
                    ]),
                    ("日本（JP · 东京）", [
                        ("FXTRANSIT", A("日本国际方向 · JP Tier1（10Gbps 端口）", "FXTRANSIT", "产品线三：日本国际方向 · JP Tier1（10Gbps 端口）"), "SAKURA 上游 10Gbps 超大端口日本纯国际互联落地机"),
                        ("KFCHost", " / ".join([
                            A("JP Tier1 Global RouteFlex", "KFCHost", "产品线一：JP Tier1 Global RouteFlex"),
                            A("JP RouteFlex（$3.99）", "KFCHost", "产品线二：JP RouteFlex（$3.99，2TB @200Mbps）"),
                        ]), "东京纯国际 Tier1 路由出口机（无大陆优化，需中转拉取）"),
                        ("OrangeVPS", A("日本东京 BASIC-AP-1", "OrangeVPS", "产品线三：香港 HK 与日本东京 BASIC-AP-1"), "东京入门级国际机房落地款"),
                    ]),
                    ("中国台湾（TW · 含港台 Akari 互联）", [
                        ("HaloCloud", A("台湾 TW（原生 IP · Akari 上游）", "HaloCloud", "产品线四：台湾 TW（原生 IP）"), "上游接入 Akari（AS56850）+ GSL，港台 ~13ms 低延迟互联对端与台湾原生机房 IP"),
                        ("Misaka", A("台湾 TW（亚太节点）", "Misaka", "产品线三：亚太节点（新加坡 S3N / 香港国际落地 / 台湾 TW）"), "稀缺台湾高品质商业机房国际互联落地"),
                        ("wawo（哇沃主机）", A("台湾 IPv6（12.2 元/年）", "wawo（哇沃主机）", "产品线六：台湾 IPv6"), "`[纯 IPv6 无 v4]` 接入 GSL / Lumen 的 12.2 元/年台湾 IPv6 玩具落地机"),
                    ]),
                    ("新加坡（SG）", [
                        ("FXTRANSIT", A("新加坡国际方向 · Tier1 SG", "FXTRANSIT", "产品线五：新加坡国际方向 · Tier1 SG"), "新加坡纯国际 Tier1 大带宽出口落地"),
                        ("HaloCloud", A("新加坡 SG（9 刀/年付）", "HaloCloud", "产品线二：新加坡 SG"), "接入 Akari + GSL 的 $9/年高性价比新加坡国际互联小鸡"),
                        ("OrangeVPS", A("新加坡 VPS（促销年付款与 BASIC-AP-1）", "OrangeVPS", "产品线一：新加坡 VPS（促销年付款与 BASIC-AP-1）"), "接入 GSL / Lumen 的新加坡低价年付机房落地"),
                        ("BreadCloud（面包云）", A("新加坡 SG - Crumb", "BreadCloud（面包云）", "产品线三：新加坡 SG - Crumb"), "新加坡低门槛国际方向小鸡"),
                        ("Misaka", A("新加坡 S3N（亚太节点）", "Misaka", "产品线三：亚太节点（新加坡 S3N / 香港国际落地 / 台湾 TW）"), "新加坡高可用国际互联机房节点"),
                    ]),
                    ("美国（US · 洛杉矶 / 圣何塞 / 西雅图 / 芝加哥 / 达拉斯 / 纽约）", [
                        ("FXTRANSIT", A("美国国际方向 · US Tier1（$14/年）", "FXTRANSIT", "产品线二：美国国际方向 · US Tier1（$14/年）"), "接入 GSL / Lumen 的 $14/年美西纯国际互联落地机"),
                        ("ZgoCloud", A("洛杉矶 Global 国际款 / 低价原生 IP / 黑五新段", "ZgoCloud", "产品线三：美国洛杉矶 · Global 国际款 / 低价原生 IP / 黑五 netlab 新段"), "主打美区原生 IP 流媒体解锁 + AMD 高性能低价年付"),
                        ("LegendVPS", A("洛杉矶 US-LAX-1G（$0.5/月起玩具机）", "LegendVPS", "产品线四：美国洛杉矶 US-LAX-1G（$0.5/月起玩具机）"), "`[11月换老板·玩具机]` 接入 GSL 的超低价美西玩具落地机"),
                        ("RackNerd", " / ".join([
                            A("2025 黑五 1G/2.5G", "RackNerd", "产品线一：黑五 1 GB / 2.5 GB KVM（Black Friday 2025）"),
                            A("2023 黑五闪购", "RackNerd", "产品线二：2023 黑五闪购"),
                            A("Buffalo NY 与达拉斯", "RackNerd", "产品线三：1 GB KVM Special Deal（Buffalo, NY）"),
                            A("圣何塞", "RackNerd", "产品线五：圣何塞"),
                        ]), "老牌 $10~$22/年美区多机房低价 KVM 玩具/备用机（达拉斯晚高峰有慢速反馈）"),
                        ("HostDzire", " / ".join([
                            A("LAX 4C6G（$24/年）", "HostDzire", "产品线一：LAX 4C6G 年付 24 刀"),
                            A("ColoCrossing $24/年", "HostDzire", "产品线二：ColoCrossing 上游（年付 24 刀）"),
                            A("SFO 旧金山 4C6G", "HostDzire", "产品线三：SFO 4C6G"),
                        ]), "Leaseweb / CC 上游，$20~$24/年给足 4C6G 的美西高配白菜价机房机"),
                        ("DediRock", " / ".join([
                            A("洛杉矶低价年付款", "DediRock", "产品线一：洛杉矶 LAX 低价年付款"),
                            A("纽约 NY", "DediRock", "产品线二：纽约 NY"),
                            A("同帖 TQ 对比", "DediRock", "产品线四：与其他商家同帖的 TQ 对比"),
                        ]), "CC/HostPapa 系超低价年付美西/美东入门机房机"),
                        ("BreadCloud（面包云）", A("美国 US - Slice（$15/年）", "BreadCloud（面包云）", "产品线一：美国 US - Slice（年付 15 刀）"), "Tier.Net 上游，15 刀/年 4TB@2Gbps 美区机房落地"),
                        ("wawo（哇沃主机）", A("美国 US-Simple-4G-42（9.9 元/月）", "wawo（哇沃主机）", "产品线七：美国 US-Simple-4G-42"), "9.9 元/月 2C4G + 10Gbps 口 4.5TB 大流量 HDD 机房机"),
                        ("Misaka", A("北美节点（西雅图 S2N / 洛杉矶 LAX）", "Misaka", "产品线四：北美节点（西雅图 S2N / 洛杉矶 LAX）"), "北美西雅图与洛杉矶高品质机房落地"),
                        ("Langya", A("美国芝加哥 GSL 落地机（3 月归档）", "Langya（近半年公开帖为 0 · 附 2026 年 3 月测评）", "产品线一：美国芝加哥 GSL 落地机与香港落地机（2026 年 3 月归档）"), "接入 GSL 的美中芝加哥国际互联归档款"),
                    ]),
                    ("欧洲（EU · 德国 DE / 荷兰 NL / 卢森堡 LU）", [
                        ("Zouter", A("德国法兰克福 Global 新品（EPYC 7K62，猫猫专测）", "Zouter", "产品线三：德国法兰克福 Global 落地新品（猫猫官方专测）"), "法兰克福干净原生机房 IP + EPYC 7K62 + 首发 4TB 流量，德系线路机中转轻松跑满 1Gbps"),
                        ("RackNerd", A("2025 黑五第 7 波 · 荷兰阿姆斯特丹（$11/年）", "RackNerd", "产品线四：2025 黑五第 7 波（NL-Amsterdam）"), "$11/年超低门槛阿姆斯特丹机房练手/备用落地"),
                        ("BuyVM", A("瑞士标称（实为卢森堡 Luxembourg）KVM", "BuyVM", "产品线一：瑞士（Luxembourg）KVM"), "`[抗投诉 DMCA 宽松]` FranTech（AS53667）经典卢森堡无限流量 KVM（含 7950X3D 宿主机）"),
                    ]),
                    ("其他亚太与中东地区（韩国 KR / 沙特 SA）", [
                        ("HostHatch", A("韩国首尔（KR）KVM", "HostHatch", "产品线三：韩国（KR）"), "AS155029 首尔机房国际落地节点"),
                        ("LightNode", A("沙特阿拉伯利雅得节点（4 月归档）", "LightNode（近半年公开帖为 0 · 附 2026 年 4 月测评）", "产品线一：沙特阿拉伯利雅得节点（2026 年 4 月归档）"), "`[按时计费可选]` 冷门中东利雅得本土机房出口，适合特定地区定位解锁"),
                    ]),
                ],
            },
        ],
    },
    {
        "cat_h2": "三、性能机 / 建站机 / 大盘鸡与物理独服",
        "cat_desc": (
            "面向编译构建、Docker 多容器、高并发建站、PT/冷备存储与 GPU 算力场景，重点考察 **CPU 单多核代数（Ryzen 9950X / EPYC Turin·Genoa）、DDR5 ECC 内存、NVMe 随机读写与大盘容量**。"
            "（多数海外性能机无大陆直连优化，搭配同区域线路机反代或组网体验最佳。）"
        ),
        "subcats": [
            {
                "sub_h3": "3.1 高频性能 / 建站 VPS 与 VDS（Ryzen 9950X / EPYC Turin·Genoa / 大内存机）",
                "sub_desc": (
                    "搭载旗舰桌面级高频锐龙或新一代服务器 EPYC 处理器、大内存与高速 NVMe 的建站及编译主力机。"
                    f"（若需自带家宽 IP 的 9900X 锐龙机见上方 {A('JCloudHosting RYZEN', 'JCloudHosting（西班牙家宽）', '产品线三：RYZEN（Ryzen 9 9900X，€9.98/月起）')}；"
                    f"自带大陆优化的建站机见上方 {A('GoldCloud 香港 7K62', 'GoldCloud', '产品线一：香港三网优化 · 建站 7K62 / CMI HK')} 与 "
                    f"{A('ZgoCloud 洛杉矶 AMD', 'ZgoCloud', '产品线一：美国洛杉矶 · AMD Optimised 三网精品（CN2 GIA & 9929 & CMIN2）')}。）\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：欧美建站性能与性价比皇冠标杆为 [**netcup**](/archives/meowvps-official-merchants-2026h2#netcup)（皇冠推荐）、[**DigitalFyre**](/archives/meowvps-official-merchants-2026h2#digitalfyre)（皇冠推荐），同类老牌另有 [**quicksrv**](/archives/meowvps-official-merchants-2026h2#quicksrv)、[**Evoxt**](/archives/meowvps-official-merchants-2026h2#evoxt益沃斯)、[**绿云 GreenCloud**](/archives/meowvps-official-merchants-2026h2#greencloud绿云)、[**BUG NET（虫网）**](/archives/meowvps-official-merchants-2026h2#bug-net虫网)。"
                ),
                "regions": [
                    ("日本（JP · 东京）", [
                        ("Bocchi", " / ".join([
                            A("东京 TYO-Pulse（9950X + DDR5 + Gen5 NVMe）", "Bocchi", "产品线一：东京 TYO-Pulse（9950X + DDR5 + Gen5 NVMe）"),
                            A("商家详测", "Bocchi", "商家自营测评"),
                        ]), "Ryzen 9 9950X 顶级单核 + Gen5 NVMe，东京旗舰性能兼国际落地机"),
                        ("HostHatch", A("东京千代田 4C16G（EPYC 7763 YABS 留档）", "HostHatch", "产品线五：东京 4C16G（YABS 留档）"), "EPYC 7763 + 16G 内存 + 180G NVMe 东京大内存建站/应用机"),
                    ]),
                    ("新加坡（SG）与马来西亚（MY）", [
                        ("OrangeVPS", A("新加坡 8C16G 周年/活动大鸡（300 元/年）", "OrangeVPS", "产品线二：8C16G 周年/活动大鸡（300 元/年）"), "300 元/年给足 8C16G 大内存的新加坡多容器/建站活动机"),
                        ("Terabix", A("马来西亚柔佛新山 Cloud VM Premium（AMD Genoa）", "Terabix", "产品线一：马来西亚柔佛新山 · Cloud VM Premium（CVM-4GB，$7/月起）"), "Equinix JH1 机房 AMD Genoa + DDR5 + NVMe Gen4，与新加坡超低延迟互联 + 大马双栈原生 IP"),
                    ]),
                    ("美国（US · 洛杉矶 LAX）", [
                        ("HostHatch", A("洛杉矶 LAX 大鸡（4C32G / 400G NVMe / 50TB）", "HostHatch", "产品线四：洛杉矶 LAX 大鸡"), "32G 超大内存 + 400G NVMe + 50TB 月流量的美西重负载建站机"),
                    ]),
                    ("欧洲（EU · 德国 DE / 荷兰 NL）", [
                        ("BeroHost", " / ".join([
                            A("十周年 12 欧款", "BeroHost", "产品线一：德国十周年 12 欧款与老 12 欧款"),
                            A("Anniversary M（49 欧/年）", "BeroHost", "产品线二：德国十周年 Anniversary M（49 欧/年）"),
                            A("89 欧款（6C24G/300G）", "BeroHost", "产品线三：德国十周年 89 欧款（6C24G / 300G）"),
                            A("XMAS 69 欧款（4C20G）", "BeroHost", "产品线四：XMAS 2025 年付 69 欧款（4C20G，含换母鸡前后对比）"),
                            A("1 欧款", "BeroHost", "产品线五：1 欧款"),
                        ]), "德国 EPYC Turin / 高频大内存 NVMe 神机，配合法兰克福 9929 前置拉取极佳"),
                        ("GatewaySentry", A("荷兰 · Ryzen 9 9950X（4C8G，$8/月）", "GatewaySentry", "产品线二：荷兰 · Ryzen 9 9950X（4C8G，$8/月）"), "$8/月高性价比 4C8G Ryzen 9 9950X 荷兰高频性能机"),
                    ]),
                ],
            },
            {
                "sub_h3": "3.2 大盘鸡（大容量存储块 / HDD 备份与 PT 机）",
                "sub_desc": (
                    "配备 500GB~数 TB 大容量块存储或机械盘阵列，主打冷数据备份、网盘图床与 PT 刷流。\n\n"
                    "> **同赛道大牌标杆参照（猫猫正式库）**：大盘备份与刷流同类参照 [**netcup（RS/存储款）**](/archives/meowvps-official-merchants-2026h2#netcup)、[**Ciallo Networks**](/archives/meowvps-official-merchants-2026h2#ciallo-networks)。"
                ),
                "regions": [
                    ("中国香港（HK）", [
                        ("HostHatch", A("香港 6C24G 大盘", "HostHatch", "产品线二：香港 6C24G 大盘"), "香港稀缺高内存大容量存储机（接入 GSL/10099）"),
                    ]),
                    ("美国（US · 拉斯维加斯 LAS / 美西·美东）", [
                        ("BuyVM", " / ".join([
                            A("拉斯维加斯 KVM + 存储块（512G / 1TB）", "BuyVM", "产品线二：拉斯维加斯 KVM + 存储块"),
                            A("SLAB 存储块读写实测", "BuyVM", "产品线三：存储块读写"),
                        ]), "`[Block Storage 自由挂载]` FranTech 经典存储块 + 无限流量大盘鸡"),
                        ("DediRock", A("Storage Promo 大盘鸡", "DediRock", "产品线三：Storage Promo 大盘鸡"), "美区低价促销大容量 HDD 备份存储鸡"),
                    ]),
                ],
            },
            {
                "sub_h3": "3.3 物理独立服务器（独服 / 杜甫 / GPU 机）",
                "sub_desc": "整台物理硬件完全独享（无虚拟化邻居争抢），适合重度算力、本地大模型推理、视频转码或自开小鸡。",
                "regions": [
                    ("中国香港（HK · 荃湾）", [
                        ("WLX", A("香港荃湾独服（Ryzen 9 9955HX / Ultra 9 285HX + RTX 4070）", "WLX", "产品线一：香港荃湾独立服务器（Ryzen 9 9955HX / Core Ultra 9 285HX + RTX 4070）"), "香港旗舰 9955HX / 285HX 物理独服 + RTX 4070 独显机器"),
                    ]),
                ],
            },
        ],
    },
    {
        "cat_h2": "四、归档避雷与暂无公开帖商家（单列预警）",
        "cat_desc": "已停运、已被标记违规跑路或 NodeSeek / 猫猫博客均暂无公开测评的商家单独汇总于此，**不混入上方正常选机推荐池**，以免误导选购。",
        "subcats": [
            {
                "sub_h3": "4.1 停运与违规跑路历史留档（切勿购买）",
                "sub_desc": "以下两家仅保留 2026 年 3 月历史测评作为目录完整性留档与风险警示（另提醒：上方收录的 [LegendVPS]({{ANCHOR:LegendVPS}}) 已于 2026 年 11 月换老板并开放争议退款，入手前请留意最新动态）。",
                "regions": [
                    ("美国 / 日本（历史归档避雷）", [
                        ("HostBlazer", A("美国达拉斯 DAL Standard 与免费 IPv6（3 月历史留档）", "HostBlazer（已于 2026 年 4 月停运 · 附 3 月历史留档）", "产品线一：美国达拉斯 DAL Standard 与免费 IPv6 款（2026 年 3 月历史归档）"), "`[已失联停运]` 2026 年 4 月停运，仅供历史记录核查"),
                        ("VMVM", A("日本东京春季款与美国盐湖城 9950X（3 月历史留档）", "VMVM（已被标记违规跑路 · 附 2026 年 3 月历史留档）", "产品线一：日本东京春季特别款与美国盐湖城款（2026 年 3 月历史归档）"), "`[违规跑路]` 官方账号已被 NodeSeek 标记违规跑路，严禁购买"),
                    ]),
                ],
            },
            {
                "sub_h3": "4.2 NodeSeek 与猫猫博客均暂无公开测评商家（2 家）",
                "sub_desc": "在 NodeSeek 测评区及猫猫博客专栏检索均暂无公开测评帖，保留索引供后续追踪。",
                "regions": [
                    ("未分地区", [
                        ("CoffeeHost", A("测评区无对应帖子说明", "测评区没有对应帖子的商家"), "MeowVPS“收集中”目录商家，暂无公开测评帖"),
                        ("筋斗云", A("测评区无对应帖子说明", "测评区没有对应帖子的商家"), "MeowVPS“收集中”目录商家，暂无公开测评帖"),
                    ]),
                ],
            },
        ],
    },
]


def render_taxonomy_markdown():
    lines = []
    lines.append("## 选机分类体系总览（猫猫博客口径）")
    lines.append("")
    lines.append(
        "参考猫猫博客（MeowVPS）的《热门地区服务器 VPS 推荐》《常见线路科普》与《VPS IP 质量检测指南》，"
        "多产品线商家不能简单按商家贴单一标签，下面先将本文 **61 家商家（外加 2 篇特殊家宽留档）、193 项产品线与单列条目** 拆解到 **三大主类（外加避雷归档）→ 细分小类 → 地区**，"
        "点击任意商家或机型即可直接跳到下方对应的完整测评与可展开的 NodeQuality 原文："
    )
    lines.append("")
    lines.append("| 大类 | 细分小类（点击跳转） | 覆盖地区 | 收录机型组数 | 核心选购定位 |")
    lines.append("| --- | --- | --- | --- | --- |")

    summary_meta = [
        ("一、线路机", "1.1 精品优化与专线（CN2 GIA / CTGNet / 9929 / CMIN2 / 沪日专线）", "香港、日本、新加坡、美国、德国/英国/俄罗斯、澳门", "全天候直连稳速、拉海外家宽/落地的黄金前置"),
        ("一、线路机", "1.2 普通骨干优化与单网快乐机（4837 / 10099 / CMI / 软银 SoftBank / IIJ / Lumen）", "香港、日本、美国", "大带宽大流量高性价比，适合单网快乐或流量大户"),
        ("一、线路机", "1.3 优化线路 + 双 ISP 伪家宽复合机（大陆优化回程 + 双 ISP 二合一）", "美国、英国", "一线双用，单机兼顾大陆直连回程与双 ISP 轻量落地"),
        ("二、落地机", "2.1 真家宽 / 商宽（独立静态·动态 IP）", "香港、日本、台湾、美国、西班牙、韩国、越南、大马、澳大利亚", "五库全绿真实本土 ISP，过金融/AI/电商店铺强风控"),
        ("二、落地机", "2.2 真家宽 / 商宽（NAT 共享 IP 与多国家宽出口）", "香港、日本、台湾、日韩新菲聚合", "百元内低成本共享真实动态家宽与蜂窝出口"),
        ("二、落地机", "2.3 伪家宽（双 ISP 属性机房 IP · 无大陆直连优化）", "日本、新加坡、美国、英国、菲律宾", "部分库标家宽的商业机房 IP，带宽稳、价格低，需配前置"),
        ("二、落地机", "2.4 机房落地机（原生 IP 解锁 / Tier1·GSL·Akari 国际互联 / 廉价机房与玩具机）", "香港、日本、台湾、新加坡、美国、德/荷/卢森堡、韩国、沙特", "港台/日美高速互联组网、DNS/原生流媒体解锁、$10/年练手玩具"),
        ("三、性能/存储/独服", "3.1 高频性能 / 建站 VPS 与 VDS（Ryzen 9950X / EPYC Turin·Genoa / 大内存机）", "日本、新加坡、马来西亚、美国、德国/荷兰", "9950X / EPYC 强算力、大内存编译与高并发建站"),
        ("三、性能/存储/独服", "3.2 大盘鸡（大容量存储块 / HDD 备份与 PT 机）", "香港、美国", "500GB~TB 级块存储与冷备/PT 大盘"),
        ("三、性能/存储/独服", "3.3 物理独立服务器（独服 / 杜甫 / GPU 机）", "香港", "9955HX / 285HX + RTX 4070 整机物理独享算力"),
        ("四、归档避雷", "4.1 停运与违规跑路历史留档（切勿购买）", "美国、日本（历史归档）", "已停运 HostBlazer 与违规跑路 VMVM 避雷留档"),
        ("四、归档避雷", "4.2 NodeSeek 与猫猫博客均暂无公开测评商家（2 家）", "未分地区", "CoffeeHost、筋斗云无公开测评帖登记"),
    ]

    sub_lookup = {}
    for cat in TAXONOMY_DATA:
        for sc in cat["subcats"]:
            cnt = sum(len(rows) for _, rows in sc["regions"])
            sub_lookup[sc["sub_h3"]] = (cat["cat_h2"], cnt)

    for cat_short, sub_h3, regs_str, pos_str in summary_meta:
        _, cnt = sub_lookup[sub_h3]
        short_label = sub_h3.split("（")[0]
        lines.append(f"| {cat_short} | [{short_label}]({{{{ANCHOR_SELF:{sub_h3}}}}}) | {regs_str} | {cnt} 组 | {pos_str} |")

    lines.append("")
    lines.append("### 附：三网宽带选机与「前置 × 落地」黄金组网速查")
    lines.append("")
    lines.append(
        "单看机器参数容易出现“买回来本地宽带拉不动”或“落地机直连丢包成砖”的情况。实操配置链式转发与自动回退可配合站内教程 "
        "[VPS 线路与落地怎么搭](/archives/relay-and-egress-guide) 与 [Mihomo 链式与回退：三个配置陷阱](/archives/mihomo-chain-and-fallback) 阅读："
    )
    lines.append("")
    lines.append("**1. 按大陆本地宽带挑线路机**")
    lines.append("")
    lines.append("| 本地宽带 | 晚高峰表现与特性 | 优先选购回程代号 | 避坑提醒 |")
    lines.append("| --- | --- | --- | --- |")
    lines.append(f"| **中国电信** | 跨国普通 163 骨干晚高峰拥堵重灾区，最挑线路 | 首选 {S('1.1 精品优化', '1.1 精品优化与专线（CN2 GIA / CTGNet / 9929 / CMIN2 / 沪日专线）')} 中的 `CN2 GIA`、`CTGNet（CTGGIA）`、`9929` 或沪日专线 | 慎买无电信优化的普通软银、纯 Lumen/CMI 与直连机房机 |")
    lines.append(f"| **中国联通** | 国际出口最友好，性价比选择面最广 | `9929 / 10099` 最稳；{S('1.2 普通优化', '1.2 普通骨干优化与单网快乐机（4837 / 10099 / CMI / 软银 SoftBank / IIJ / Lumen）')} 的美西 `4837`、东京 `SoftBank`、`IIJ` 均快乐 | 个别北方/南方省份晚高峰软银偶有波动，看同省 TQ 贴图确认 |")
    lines.append(f"| **中国移动** | 亚太带宽充裕，但跨网拉电联精品线有时反被限速 | 首选 `CMIN2`、香港/新加坡双栈 `Lumen`、`CMI`（含越南 VNPT / 新加坡直连快乐鸡） | 不必盲目溢价追纯电信 CN2 GIA，优先看移动回程是否独立走 CMIN2/CMI |")
    lines.append(f"| **教育网 / 科技网** | IPv6 国际带宽极佳，IPv4 视上游对等而定 | 双栈精品线或 {A('Zouter 香港 AMD', 'Zouter', '产品线一：香港 HK BGP Global（Standard / Lite / Debut 103 段）')}、{A('BreadCloud 日本 v6', 'BreadCloud（面包云）', '产品线二：日本 JP - Bite（年付 12 刀）')} 等大口双栈机 | 善用 IPv6 直连或作为中转入站可显著省钱提速 |")
    lines.append("")
    lines.append("**2. 按目标地区就近配对「线路前置 → 落地 / 性能机」**")
    lines.append("")
    lines.append("| 目标出口区域 | 推荐前置线路机（入站抗晚高峰） | 国际互联跳板与延迟参考 | 推荐后置落地 / 性能机（出站解锁与算力） |")
    lines.append("| --- | --- | --- | --- |")
    lines.append("| **港台澳 & 东南亚** | 香港三网精品（Peekabo / 六六云 / wawo）或香港双栈 Lumen / 新加坡狗妈（懒猫云） | 港↔台 `Akari` 约 **13ms**；港↔新/越/菲约 **25~38ms** | 台湾 Hinet/Seednet 真家宽（HighEnd / LamHosting）、香港 HKT/WTT 家宽（Tamago）、越南 VNPT（TOTHOST）、菲律宾双 ISP（六六云）、柔佛 Genoa（Terabix） |")
    lines.append("| **日本 & 韩国** | 沪日专线（NoBrand）、东京三网精品（NOSLA）、东京软银/IIJ 或香港前置 | 日↔韩约 **30~35ms**；港↔日/韩约 **38~50ms** | 日本星链/BIGLOBE/KDDI 家宽（RadoNet / 懒猫云）、东京 9950X（Bocchi）、韩国 SKB 2G 真家宽（NexKr） |")
    lines.append("| **欧洲全境** | 德国法兰克福 `DE 9929`（白丝云 / 艾云 / 六六云 / Panstar / ShanDun）或伦敦 `9929+CMIN2`（吉云） | 法兰克福↔德/荷 **1~8ms**；法兰克福↔英/西 **15~28ms** | 西班牙真家宽（JCloudHosting，含 9900X）、德国 Turin 大内存机（BeroHost）、荷兰 9950X（GatewaySentry）、英国双 ISP（丽萨 / Panstar）、卢森堡抗投诉（BuyVM） |")
    lines.append("| **北美全境** | 洛杉矶/圣何塞 `CN2 GIA / 9929`（六六云 / Panstar / Zgo / 艾云 / 白丝云 / NOSLA）或美西 `4837` | 洛杉矶↔加州/赌城 **3~10ms**；↔西雅图/得州 **25~35ms**；↔美东 **60ms** | 美国家宽商宽（干杯云 / BlossomHost / ATTVPS / ResidentialVPS / IPMELA）、达拉斯双 ISP（Bocchi）、赌城大盘鸡（BuyVM） |")
    lines.append("")
    lines.append(
        "> **入手前三条铁律**：① 本文收录的新晋“收集中”商家较多，**新商家或刚换老板商家（如 LegendVPS）优先月付试水**，看清是否支持原路退款；"
        "② 注意区分 **`[Windows RDP 交付]`**、**`[NAT 端口共享]`**（无 80/443）、**`[纯 IPv6]`** 与 **`[动态 IP 重拨]`**（需配 DDNS）；"
        "③ 亚太真家宽（尤其韩国、香港、台湾）开机后先测 Google 定位是否“送中”，若异常趁商家免费换 IP 窗口期及时更换。"
    )
    lines.append("")

    for cat in TAXONOMY_DATA:
        lines.append(f"## {cat['cat_h2']}")
        lines.append("")
        lines.append(cat["cat_desc"])
        lines.append("")
        for sc in cat["subcats"]:
            lines.append(f"### {sc['sub_h3']}")
            lines.append("")
            lines.append(sc["sub_desc"])
            lines.append("")
            for reg_name, rows in sc["regions"]:
                lines.append(f"**{reg_name}**")
                lines.append("")
                lines.append("| 商家 | 机型 / 产品线（点击直达测评） | 线路 / IP / 硬件实测特点 |")
                lines.append("| --- | --- | --- |")
                for merchant, link_md, feat in rows:
                    m_h2 = re.search(r"\{\{ANCHOR:([^}|]+)", link_md)
                    merchant_cell = A(merchant, m_h2.group(1)) if m_h2 else merchant
                    lines.append(f"| {merchant_cell} | {link_md} | {feat} |")
                lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    md = render_taxonomy_markdown()
    print("Generated taxonomy markdown lines:", len(md.splitlines()), "bytes:", len(md.encode("utf-8")))
