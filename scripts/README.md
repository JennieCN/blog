# VPS 测评归档、渲染、CC 四套皮肤跨站部署与 Halo 发布工具链说明

本目录包含「融夕的书」（`blog.mycampusmail.com`）与「融夕问答社区」（`qa.mycampusmail.com`）的 VPS 商家测评双卷归档、Halo HTML 渲染、CC 四套皮肤跨站同步部署、文章一键发布及无头浏览器端到端回归测试的完整工具链。

## 1. 数据源归档目录

原始抓取数据（MeowVPS 目录 JSON、205 篇 `/blog/` 专测 HTML、NodeSeek 测评帖与 NodeQuality 原始报告，共约 88MB）持久化保存在仓库同级目录（不入 Git）：

- `/Users/cityu/Documents/ChatGPT/vps搭建/data/vps-reviews-202611/`
  - `meow_vol2/`：猫猫博客首页商家 JSON 与全量专测详情页
  - `posts/`：NodeSeek 社区实测帖原文缓存
  - `nqfull/`：NodeQuality / TQuality 终端原始报告缓存

---

## 2. 核心脚本与目录职责

| 路径 | 用途说明 |
| :--- | :--- |
| `scripts/rx-skins/` | CC 四套可切换皮肤（`pop` 撞色贴纸［默认］、`ink` 水墨远山、`luxe` 夕照毛玻璃、`plain` 素色极简）× 亮/暗双模跨站共享静态资源与注入模板：含 `rx-tokens.css`、`rx-halo.css`、`rx-flarum.css`、`rx-switcher.js`、`bootstrap-snippet.js`、3 个水墨矢量素材（`ink-*.svg`）及 `halo-global-head.html` / `flarum-custom-header.html`。 |
| `scripts/deploy-rx-skins.py` | 幂等部署脚本：将 `scripts/rx-skins/*` 同步至 `vps8:/opt/site-stack/rx-skins/`，配置 Caddy 双域名同源静态挂载（`/rx-skins/*`），通过 Halo Console API 更新 `codeInjection.globalHead`，并更新 Flarum `custom_header` + 暖色主题变量与清理缓存（零硬编码凭据，自动生成变更前快照）。 |
| `scripts/tests/test_rx_skins.py` | 启动本地无头 Chrome 对 `scripts/rx-skins/` 执行核心切换器、损坏 Cookie 回退、快速连点防竞态、后台路由排除（`/console`、`/uc`、`/admin`）、Halo/Flarum 四套皮肤样式与 390px 零横向溢出单元测试。 |
| `scripts/server-watch-meowvps.py` | 部署在 `vps8:/opt/site-stack/watch-meowvps.py` 的每周定时巡检脚本（每周一 `09:15` 自动运行），对比线上 `meowvps.com` 目录与 Sitemap，发现新增商家或新专测时写入日志并通过 Resend SMTP 发送去重邮件提醒（零硬编码凭据）。 |
| `scripts/check-meowvps-diff.py` | 对比线上 `meowvps.com` 最新商家目录与 `sitemap-0.xml` 全部 `/blog/` 测评页，校验上卷（61 家）+ 下卷（56 家）是否 **100% 零遗漏、零重叠**。 |
| `scripts/generators/generate_full_article.py` | 生成上卷（`nodeseek-merchant-reviews-2026h2`）带锚点模板 Markdown。 |
| `scripts/generators/parse_vol2_all.py` & `build_vol2.py` | 解析猫猫正式收录商家并生成下卷（`meowvps-official-merchants-2026h2`）带锚点模板 Markdown。 |
| `scripts/generators/taxonomy_guide.py` | 输出统一的「猫猫博客选机分类体系总览（`大类 → 细分小类 → 地区 → 机型`）」索引模块。 |
| `scripts/render-halo-markdown.mjs` | 将 Markdown 渲染为 Halo 专用 HTML：仅对 `h1-h3` 生成目录 ID（避免 `tocbot` 爆表）、将纯文本终端报告转为 `<pre class="vps-raw-report">`（规避 `plugin-shiki` 高斯模糊与数百个 Web Component 开销）、可选注入亮/暗双色交互筛选工具栏（`--inject-toolbar`），并执行 0 断链与 `<details>` 闭合校验。 |
| `scripts/publish-halo.py` | 通过 SSH 隧道向 `vps8`（`127.0.0.1:8091`）发布或更新文章（Post）、独立页面（SinglePage）、置顶权重、下架占位稿及维护顶部主导航菜单。管理凭据仅从 `../private/gatewave-halo-admin.txt` 或环境变量读取，**严禁硬编码**。 |
| `scripts/halo-pages/*.html` | Halo 独立页面源码（`about.html` 关于、`my-reviews.html` 我的自用测评、`tools.html` 实用工具箱、`privacy-policy.html` 隐私政策、`user-agreement.html` 用户协议与免责声明），统一适配四套皮肤与亮/暗模式。 |
| `scripts/verify-live-halo.py` | 启动无头 Chrome（CDP）对线上主站与 Flarum 问答社区执行 HTTP 200、`/rx-skins/*` 静态缓存、四套皮肤 × 亮/暗双模、跨子域 `.mycampusmail.com` Cookie 同步、Flarum SPA 导航、后台零注入隔离、俗称检索、0 断链、0 模糊终端块（`blur`）及 `1280px`/`390px` 零横向溢出全量断言。 |

---

## 3. 日常增量更新标准流程

### 场景 A：修改皮肤样式或交互后部署至双站

```bash
# 1. 本地无头浏览器单元测试
python3 -m unittest scripts/tests/test_rx_skins.py -v

# 2. 幂等同步至 vps8（Halo + Flarum + Caddy）
python3 scripts/deploy-rx-skins.py

# 3. 线上双站端到端回归验证
python3 scripts/verify-live-halo.py
```

### 场景 B：巡检与更新 117 家 VPS 测评文章

```bash
# 第一步：巡检猫猫博客是否有新收录商家或新测评
python3 scripts/check-meowvps-diff.py

# 第二步：渲染 Halo HTML（自动校验锚点与 <details> 数量）
node scripts/render-halo-markdown.mjs \
  src/content/vps/nodeseek-merchant-reviews-2026h2.md \
  --out-html /tmp/vol1.html \
  --expected-details 319 \
  --inject-toolbar

node scripts/render-halo-markdown.mjs \
  src/content/vps/meowvps-official-merchants-2026h2.md \
  --out-html /tmp/vol2.html \
  --expected-details 137 \
  --inject-toolbar

# 第三步：发布到 Halo
python3 scripts/publish-halo.py \
  --post-name post-nodeseek-merchant-reviews-2026h2 \
  --slug nodeseek-merchant-reviews-2026h2 \
  --md src/content/vps/nodeseek-merchant-reviews-2026h2.md \
  --html /tmp/vol1.html \
  --pinned --priority 20 \
  --categories cat-vps \
  --tags "VPS:tag-vps,测评:tag-review,线路:tag-route,落地:tag-egress,家宽:tag-isp,NodeQuality:tag-nodequality"

# 第四步：运行本地与线上全量回归验证
node scripts/verify-content.mjs
npm test
npm run build
python3 scripts/verify-live-halo.py
```
