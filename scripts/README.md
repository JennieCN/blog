# VPS 测评归档、渲染与 Halo 发布工具链说明

本目录包含「融夕的书」（`blog.mycampusmail.com`）VPS 商家测评双卷归档、Halo HTML 渲染、一键同步发布与无头浏览器端到端回归测试的完整工具链。

## 1. 数据源归档目录

原始抓取数据（MeowVPS 目录 JSON、205 篇 `/blog/` 专测 HTML、NodeSeek 测评帖与 NodeQuality 原始报告，共约 88MB）持久化保存在仓库同级目录（不入 Git）：

- `/Users/cityu/Documents/ChatGPT/vps搭建/data/vps-reviews-202611/`
  - `meow_vol2/`：猫猫博客首页商家 JSON 与全量专测详情页
  - `posts/`：NodeSeek 社区实测帖原文缓存
  - `nqfull/`：NodeQuality / TQuality 终端原始报告缓存

---

## 2. 核心脚本职责

| 脚本路径 | 用途说明 |
| :--- | :--- |
| `scripts/check-meowvps-diff.py` | 对比线上 `meowvps.com` 最新商家目录与 `sitemap-0.xml` 全部 `/blog/` 测评页，校验上卷（61 家）+ 下卷（56 家）是否 **100% 零遗漏、零重叠**。 |
| `scripts/generators/generate_full_article.py` | 生成上卷（`nodeseek-merchant-reviews-2026h2`）带锚点模板 Markdown。 |
| `scripts/generators/parse_vol2_all.py` & `build_vol2.py` | 解析猫猫正式收录商家并生成下卷（`meowvps-official-merchants-2026h2`）带锚点模板 Markdown。 |
| `scripts/generators/taxonomy_guide.py` | 输出统一的「猫猫博客选机分类体系总览（`大类 → 细分小类 → 地区 → 机型`）」索引模块。 |
| `scripts/render-halo-markdown.mjs` | 将 Markdown 渲染为 Halo 专用 HTML：仅对 `h1-h3` 生成目录 ID（避免 `tocbot` 爆表）、将纯文本终端报告转为 `<pre class="vps-raw-report">`（规避 `plugin-shiki` 高斯模糊与数百个 Web Component 开销）、可选注入亮/暗双色交互筛选工具栏（`--inject-toolbar`），并执行 0 断链与 `<details>` 闭合校验。 |
| `scripts/publish-halo.py` | 通过 SSH 隧道向 `vps8`（`127.0.0.1:8091`）发布或更新文章（Post）、独立页面（SinglePage）、置顶权重、下架占位稿及维护顶部主导航菜单。管理凭据仅从 `../private/gatewave-halo-admin.txt` 或环境变量读取，**严禁硬编码**。 |
| `scripts/halo-pages/tools.html` | Halo 独立页面 `/tools`（实用工具箱）源码，原生适配亮/暗模式。 |
| `scripts/verify-live-halo.py` | 启动无头 Chrome（CDP）对线上首页置顶顺序、全部分类页、上下卷及指南页进行 HTTP 200、0 断链、0 模糊终端块（`blur`）、亮/暗模式工具栏配色与桌面/移动端零横向溢出全量断言。 |

---

## 3. 日常增量更新标准流程

### 第一步：巡检猫猫博客是否有新收录商家或新测评

```bash
python3 scripts/check-meowvps-diff.py
```

### 第二步：渲染 Halo HTML（自动校验锚点与 `<details>` 数量）

```bash
# 渲染上卷（319 份折叠终端报告 + 交互筛选栏）
node scripts/render-halo-markdown.mjs \
  src/content/vps/nodeseek-merchant-reviews-2026h2.md \
  --out-html /tmp/vol1.html \
  --expected-details 319 \
  --inject-toolbar

# 渲染下卷（137 份折叠终端报告 + 交互筛选栏）
node scripts/render-halo-markdown.mjs \
  src/content/vps/meowvps-official-merchants-2026h2.md \
  --out-html /tmp/vol2.html \
  --expected-details 137 \
  --inject-toolbar
```

### 第三步：发布到 Halo（支持单篇、独立页面或 `--batch-json` 批量会话）

```bash
# 示例：更新上卷并保持首页第一置顶（priority=20）
python3 scripts/publish-halo.py \
  --post-name post-nodeseek-merchant-reviews-2026h2 \
  --slug nodeseek-merchant-reviews-2026h2 \
  --md src/content/vps/nodeseek-merchant-reviews-2026h2.md \
  --html /tmp/vol1.html \
  --pinned --priority 20 \
  --categories cat-vps \
  --tags "VPS:tag-vps,测评:tag-review,线路:tag-route,落地:tag-egress,家宽:tag-isp,NodeQuality:tag-nodequality"

# 示例：发布或更新 /tools 独立页面并挂载到主菜单
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
```

### 第四步：运行本地与线上全量回归验证

```bash
node scripts/verify-content.mjs
npm test
npm run build
python3 scripts/verify-live-halo.py
```
