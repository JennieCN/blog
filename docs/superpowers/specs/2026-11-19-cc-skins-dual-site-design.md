# CC 四套皮肤跨站移植设计文档（Halo 主站 + Flarum 社区）

- **日期**：2026-11-19
- **适用站点**：`https://blog.mycampusmail.com`（Halo `v2.27.3` · `theme-earth`）与 `https://qa.mycampusmail.com`（Flarum `v2.0.2`）
- **源码仓库**：`/Users/cityu/Documents/ChatGPT/vps搭建/blog`

---

## 1. 背景与意图（Intent & Why）

在 2026-11-17 的旧版 Astro 静态站提交（`ae50f6d`）中，CC 为「融夕的书」设计了一套辨识度极高的视觉系统：包含**撞色贴纸（`pop`）**、**水墨远山（`ink`）**、**夕照毛玻璃（`luxe`）**与**素色极简（`plain`）**四套视觉质感，以及顶栏一键换肤按钮、圆形扩散切换动画（View Transitions）和阅读进度条。

2026-11-18 线上架构升级为 **Halo CMS（主站博客）+ Flarum 2.0（问答社区）** 双容器架构后，后台发文与社区交互更加省心，但前端回退到了 Halo `theme-earth` 默认白灰卡片与 Flarum 默认冷灰蓝（`#4D698E`）外观，CC 的视觉设计只留在了本地 Git 仓库中。

**本次目标**：在不改动 Halo / Flarum 容器核心代码、保留后台管理与现有业务功能的前提下，将 CC 的 **4 套完整皮肤 + 深浅色模式 + 顶栏换肤按钮** 统一移植到 `blog.mycampusmail.com` 与 `qa.mycampusmail.com`，实现两站视觉同源、跨站换肤自动同步。

---

## 2. 目标、非目标与反目标（Goals / Non-Goals / Anti-Goals）

### 目标（Goals）
1. **两站统一换装**：`blog.mycampusmail.com` 与 `qa.mycampusmail.com` 均完整支持 **4 套皮肤切换**（`pop` 撞色、`ink` 水墨、`luxe` 夕照、`plain` 素色）以及每套皮肤下的 **亮色 / 暗色（Light / Dark）** 双模式（共 8 种视觉组合）。
2. **还原 CC 原作质感灵魂**（而非仅换背景色）：
   - **撞色（`pop`）**：奶油波点底纹、`2.5px` 粗墨描边、`4px` 硬投影贴纸卡片、明黄（`#ffd23f`）胶囊高亮与按钮按压回弹。
   - **水墨（`ink`）**：宣纸噪点底色、底部远山水墨背景（`ink-mountains.svg`）、页头山水画卷（`ink-landscape.svg`）、「融夕」朱砂印章（`#b5291c`）、飞白笔刷遮罩（`ink-stroke.svg`）与宋体/楷体/行楷字重层级。
   - **夕照（`luxe`）**：暖米色纸张颗粒、缓慢流动的夕照极光光晕、半透明毛玻璃卡片（`backdrop-filter: blur`）与赤陶橙渐变主按钮。
   - **素色（`plain`）**：GitHub Primer 风格纯色背景、`1px` 中性细边框、无光晕无阴影的高信噪比阅读界面。
3. **跨子站状态同步**：用户在 `blog` 或 `qa` 任意一端切换皮肤或深浅色后，状态通过 `.mycampusmail.com` 顶级域 Cookie 同步，跳转到另一子站首屏直接生效且无白屏闪烁（FOUC）。
4. **全量兼容既有定制组件**：
   - Halo 侧：117 家 VPS 测评上下卷（`#vps-vendor-wall` 商家检索墙、搜索工具栏、路由折叠表、`<pre class="vps-raw-report">` 原文代码块）、`/my-reviews`、`/tools`、`/about`、`/privacy-policy`、`/user-agreement`。
   - Flarum 侧：顶部跨站导航栏、专栏直达横幅、每日签到领书币（`#rx-checkin-btn` / `me.php`）、注册/发帖邮箱与图形验证码浮层（`#rx-captcha-float`）。

### 非目标（Non-Goals）
- 不将 `blog.mycampusmail.com` 回退为 Astro 静态站；继续使用 Halo 2.27 后台发布与管理文章。
- 不强行重写 Halo 或 Flarum 的底层 HTML 模板骨架为旧版固定三栏 `.shell`（保持 Halo 主栏+侧栏、Flarum 左侧导航+讨论流各自的自然信息架构）。
- 不移植旧版依赖本地静态 `/posts-index.json` 与 Pagefind 的 `⌘K` 命令面板（Halo 已有原生 `SearchWidget` 搜索弹窗，Flarum 已有原生顶栏全局搜索框，换肤层直接美化两站原生搜索框与弹窗）。

### 反目标（Anti-Goals — 即使技术上能跑也视为失败的情况）
- **污染管理后台**：Halo 后台（`/console`、`/uc`）或 Flarum 后台（`/admin`）被注入前台皮肤导致排版错乱。
- **破坏可读性或对比度**：深色模式或水墨/撞色模式下正文、代码块（尤其是 `vps-raw-report` 终端测试原文）、表格或输入框出现「深底黑字 / 浅底白字」看不清的问题，或重现代码块模糊遮罩。
- **阻碍系统升级**：修改 Docker 镜像内部源码或解包覆盖 `theme-earth` 模板，导致日后升级容器或主题时丢失改动或白屏。
- **移动端溢出**：`390px` 手机视口下因顶栏新增换肤按钮或硬投影边框产生横向滚动条（`scrollWidth > innerWidth`）。

---

## 3. 约束条件（Constraints）

1. **生产环境拓扑**：两站均运行在 `vps8` 的 `/opt/site-stack/docker-compose.yml` 中，前置网关为 `site-proxy`（Caddy 2），后端为 `site-halo`（端口 `8090`）与 `site-flarum`（端口 `8000`）。
2. **SVG `mask-image` 同源限制**：水墨皮肤（`ink`）依赖 `mask-image: url("ink-stroke.svg")`。浏览器对 CSS `mask-image` 执行严格的同源/CORS 校验，因此皮肤静态资源必须在 `blog.mycampusmail.com` 与 `qa.mycampusmail.com` 下**同源路径（`/rx-skins/*`）**直接提供。
3. **两站暗色机制差异**：
   - Halo `theme-earth` 通过 `<html class="dark">` + `localStorage['color-scheme']`（及 Alpine `setColorScheme`）控制深浅色。
   - Flarum 2.0 通过 `<html data-theme="light|dark|auto">` 控制深浅色，所有组件配色均派生自 `[data-theme^=light]` / `[data-theme^=dark]` 下的 CSS 变量（`--body-bg`、`--control-bg`、`--primary-color` 等）。
   - Flarum 前端基于 Mithril.js 单页应用（SPA），路由切换时 `.Header-secondary` 可能重绘，顶栏挂载的自定义按钮必须具备幂等自愈能力。
4. **可访问性与性能降级**：遵循 `prefers-reduced-motion: reduce` 与 `prefers-reduced-transparency: reduce`，关闭极光动画、圆形裁切动画与毛玻璃模糊。

---

## 4. 方案对比与选型（Approaches）

| 方案 | 核心思路 | 权衡（Trade-offs） | 结论 |
| :--- | :--- | :--- | :--- |
| **方案 A：共享皮肤资源包 + 两站无损适配层 + 跨站同步换肤** | 由 Caddy 同源托管 `/rx-skins/*`（SVG 素材、基础变量、Halo/Flarum 适配 CSS 与同步脚本）；通过 Halo `codeInjection` 与 Flarum `custom_header` 注入；用 `.mycampusmail.com` Cookie 同步皮肤与深浅色。 | **优**：零侵入容器镜像与主题包，升级无忧，后台天然隔离，可完整还原 4 套皮肤特效且跨站同步。<br>**劣**：需针对 Halo Tailwind 类名与 Flarum SPA 头部编写精细 CSS 映射与 `MutationObserver` 守护。 | **用户已选定** |
| **方案 B：解包魔改 Halo 主题模板 + Flarum 编译扩展** | 解包 `theme-earth` 改写 Thymeleaf HTML，编写 Flarum 本地 Webpack 扩展重编译产包。 | **优**：可连 HTML DOM 骨架一起重写。<br>**劣**：侵入极深，后续升级主题或容器极易冲突白屏，维护成本过高。 | 放弃 |
| **方案 C：仅注入配色变量（轻量换色）** | 只替换背景色、文字色和主色，省略水墨插画、飞白遮罩、极光毛玻璃和贴纸硬投影。 | **优**：CSS 最短。<br>**劣**：丢失 CC 设计最具辨识度的视觉细节，换装效果打折。 | 放弃 |

---

## 5. 已确认的设计决策与工程拍板（Decisions & Builder Calls）

### 用户已拍板项（User Decisions）
1. **覆盖范围**：`blog.mycampusmail.com`（Halo 主站）与 `qa.mycampusmail.com`（Flarum 社区）两站全部换装。
2. **皮肤范围**：完整保留 CC 的全部视觉皮肤与顶栏一键切换能力，采用**方案 A（无损注入 + 跨站同步）**实施。

### 工程实现拍板项（Builder Calls — 供审阅确认）
1. **4 套完整轮换顺序与默认皮肤（Builder Call）**：
   - 补齐旧版切不回「夕照玻璃」的遗憾，顶栏换肤按钮按 **`撞色（pop）→ 水墨（ink）→ 夕照（luxe）→ 素色（plain）`** 循环切换。
   - 首次访问未设置 Cookie 时的默认皮肤设为 **`pop`（撞色）**，与 CC 在 `2026-11-17` 上线版本（`BaseLayout.astro`）的默认体验保持一致；用户点击一次即可切至「水墨」，再点切至「夕照」或「素色」。
2. **同源静态资源挂载方式（Builder Call）**：
   - 在本地仓库新增版本化目录 `scripts/rx-skins/`，同步至服务器 `/opt/site-stack/rx-skins/`，并在 `docker-compose.yml` 中以只读卷 `./rx-skins:/srv/rx-skins:ro` 挂载进 `site-proxy`（Caddy）。
   - 在 `Caddyfile` 的 `blog.mycampusmail.com` 与 `qa.mycampusmail.com` 两个站点块中统一配置 `handle_path /rx-skins/* { root * /srv/rx-skins; file_server }`，彻底规避跨站依赖与 SVG `mask-image` 跨域限制，同时纳入 `/opt/site-stack/backup.sh` 备份目录。
3. **跨子站状态存储协议（Builder Call）**：
   - 皮肤键：`rx_skin=pop|ink|luxe|plain`；主题键：`rx_theme=light|dark`（未手动切换过深浅色时不强制写死 `rx_theme`，默认跟随系统 `prefers-color-scheme`，一旦用户手动点击深浅色按钮则写入 Cookie 跨站同步）。
   - Cookie 属性：`Domain=.mycampusmail.com; Path=/; Max-Age=31536000; SameSite=Lax; Secure`，同时镜像写入各自域名的 `localStorage` 作为离线兜底。
   - `<head>` 内联约 40 行极简同步引导脚本（Zero-FOUC Bootstrap）：在首屏渲染前读取 Cookie，同步设置 `<html data-rx-skin="...">`，并在 Halo 上同步 `html.dark`（及 `localStorage['color-scheme']`），在 Flarum 上同步 `html[data-theme="light|dark"]`。
4. **Halo 主站（`blog.mycampusmail.com`）视觉映射细节（Builder Call）**：
   - **注入位置**：写入 Halo `/registry/configmaps/system` 的 `codeInjection.globalHead`（Halo 仅在前台主题模板输出该片段，`/console` 与 `/uc` 完全不加载；脚本再加路径守卫双保险）。
   - **顶栏与交互**：在 `#header-menu` 右侧工具图标栏（深浅色图标旁）及移动端抽屉菜单内注入 `#rx-skin-toggle`（显示画笔/方框/调色盘图标 + 当前风格名悬浮提示），点击触发 `document.startViewTransition` 圆形裁切过渡与底部 Toast 提示（`已切换至「水墨」风格`），页面最顶部挂载 `#rx-read-progress` 阅读进度条。
   - **首页 Hero 横幅适配**：
     - `luxe`（夕照）：保留拓扑封面底图并叠加暖色夕照渐变遮罩与呼吸脉冲副标。
     - `ink`（水墨）：将首页 Hero 切换为宣纸底 + 右侧 `ink-landscape.svg` 水墨远山画卷 + 行楷大字标题 + 竖排「融夕」朱砂印章（1:1 复刻 CC `ink.css` `.hall-head` 设计）。
     - `pop`（撞色）：奶油/深紫底纹卡片化 Hero + 粗黑边框 + 右侧明黄硬投影圆章装饰 + 醒目黑体标题。
     - `plain`（素色）：精简为高对比度素色横幅卡片 + `1px` 细边框，去除花哨遮罩。
   - **卡片、正文与定制单页适配**：统一接管 `#filters` 分类胶囊、首页/分类页文章卡片（`.group.flex.flex-col.overflow-hidden.rounded-xl`）、右侧边栏卡片、文章正文（`#post-content` / `.markdown-body`）、引用块与标题装饰（如水墨 H2 飞白下划线与「引号、撞色 H2 旋转明黄方块），并让 `.vps-summary-panel`、`.vps-sticky-bar`、`#vps-vendor-wall`、`.rx-about-*`、`.rx-legal-*` 及 `/tools` 卡片无缝消费 `--rx-*` 令牌；代码块 `<pre class="vps-raw-report">` 与 Shiki 代码块严格锁定高对比度深色代码底（素色浅色下同样保证清晰可读），绝不启用任何 `filter: blur`。
5. **Flarum 社区（`qa.mycampusmail.com`）视觉映射细节（Builder Call）**：
   - **注入位置**：更新 `flarum_settings.custom_header`（仅在前台论坛生效，`/admin` 不加载 `custom_header` 且脚本加路径守卫）。
   - **跨站顶栏与公告条重构**：将现有 `custom_header` 中写死内联颜色（`#18181b` 黑条与 `#eff6ff` 蓝条）重构为语义化 `.rx-qa-crossbar` 与 `.rx-qa-strip`，自动跟随 4 套皮肤与深浅色变换（例如水墨下为宣纸细墨线 + 朱砂点缀，撞色下为奶油黄贴纸条 + 粗黑描边，夕照下为毛玻璃暖色条）；100% 保留 `#rx-points`、`#rx-checkin-btn`、`window.__rxCheckin`（签到成功时额外触发 CC 的 `RXFX.confetti` 彩纸粒子动画！）以及 `#rx-captcha-float` 邮箱/图形验证码全部逻辑。
   - **Flarum 2.0 变量与组件深度映射**：
     - 将 `--rx-bg`、`--rx-surface`、`--rx-text`、`--rx-accent` 等令牌完整映射至 Flarum 2.0 原生 `[data-theme^=light]` 与 `[data-theme^=dark]` 变量（`--body-bg`、`--control-bg`、`--header-bg`、`--primary-color`、`--secondary-color`、`--button-primary-bg`、`--hero-bg`、`--discussion-title-color`、`--code-bg`、`--border-radius`）。
     - 针对 `.App-header`（含水墨飞白底边 / 夕照毛玻璃 / 撞色粗黑底边）、`.Hero`（含水墨远山 +「融夕」朱砂印 / 夕照落日光晕 / 撞色贴纸框）、`.DiscussionListItem`（话题流卡片化/墨线化/贴纸化，置顶帖高亮）、`.TagLabel` & `.TagTile`、`.CommentPost`（楼层卡片）、`.Composer`（发帖编辑器）与 `.Modal-content` 做皮肤专属质感定制。
   - **SPA 常驻换肤与深浅色按钮**：通过轻量 `MutationObserver` 在 `.Header-secondary .Header-controls` 中稳定挂载 `#rx-skin-toggle`（切换 4 套皮肤）与 `#rx-theme-toggle`（切换亮/暗色并同步 Flarum `data-theme` 与 `.mycampusmail.com` Cookie），窄屏（`<=640px`）自动收敛间距与按钮尺寸确保零横向溢出。

---

## 6. 留给实施阶段的细节（Left to the Builder）

1. `/rx-skins/` 内具体文件拆分结构（建议拆分为 `rx-tokens.css`、`rx-halo.css`、`rx-flarum.css`、`rx-switcher.js` 及 3 个水墨 SVG 素材，附带缓存版本号查询参数 `?v=...`）。
2. Halo Tailwind 工具类（如 `.bg-white`、`.dark\:bg-slate-800`）与 Flarum 组件选择器的精确优先级（Specificity）调优，确保无需滥用全局通配 `!important` 即可干净覆盖默认背景色。
3. 自动化部署脚本 `scripts/deploy-rx-skins.py` 的编写（一键同步 `/rx-skins/`、更新 Caddyfile、更新 Halo `codeInjection` 与 Flarum `custom_header`）。
4. 扩展 `scripts/verify-live-halo.py`：用 Headless Chrome 自动遍历 `blog` 与 `qa` 在 `pop / ink / luxe / plain` × `light / dark` 下的计算背景色、正文对比度、水墨 SVG 200 加载状态、跨站 Cookie 同步及 `1280px` / `390px` 零横向溢出校验。
