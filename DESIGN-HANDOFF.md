# 前端设计交接说明

本文档面向接手前端视觉与交互设计的设计师/工程师，说明站点结构、可自由改动的范围、必须保留的接口，以及验收方式。

## 1. 项目概览

「融夕的书」是一个个人技术笔记站，形态为「专栏长文 + 互动论坛」双流集合体：博客负责沉淀长文，社区论坛负责实时讨论，两边共享同一套登录态。

- 技术栈：Astro 5（静态输出）+ Tailwind CSS 4（通过 `@tailwindcss/vite`）+ TypeScript
- 构建：`npm run build` 产出 `dist/`，同时运行 Pagefind 生成站内搜索索引
- 部署：推送到 `main` 分支后由托管平台自动构建发布
- 页面路由：全部在 `src/pages/` 下，静态预渲染

## 2. 目录结构

```
src/
  config.ts              站点名称、简介、五个板块定义、评论服务地址
  content.config.ts      内容集合 schema（五个板块 + 问答归档）
  content/<板块>/*.md    文章正文（Markdown + frontmatter）
  styles/global.css      全局样式与设计变量（主要改动点）
  layouts/
    BaseLayout.astro     页面骨架：导航、页脚、阅读进度条、图片灯箱
    PostLayout.astro     文章页：正文、目录、上下篇、同板块讨论联动
  components/
    Nav.astro            顶部导航与登录态
    HybridStream.astro   「长文 + 帖子」双流列表与切换
    PostList.astro       文章列表
    PostMeta.astro       日期、标签、阅读数
    SectionCard.astro    首页板块卡片
    Search.astro         站内搜索
    Comments.astro       评论区挂载
  pages/
    index.astro          首页
    [...section]/        五个板块的列表页与文章页
    qa/                  社区大厅与归档问答
    tools.astro          在线工具箱
    timeline.astro       建站日志
    about.astro          关于
    tags/[tag].astro     标签页
    search.astro         搜索页
    404.astro            404 页
    rss.xml.ts           RSS
```

## 3. 可自由改动的范围

- 视觉风格：配色、字体、圆角、阴影、间距、动效
- 布局结构：首页分区、卡片排布、文章页栏宽与目录位置、页脚内容
- 组件外观：只要保留第 4 节列出的选择器与 id，内部结构与样式都可以重写
- 新增页面或区块：例如文章底部推荐、板块介绍横幅、页脚友链

主要改动点：

- `src/styles/global.css`：`:root` 与 `html.dark` 两套 CSS 变量，改配色与圆角基本只需改这里
- `src/config.ts`：站点标题、简介、作者名、板块名称与描述

## 4. 必须保留的接口

以下选择器与 id 被脚本或外部服务依赖，改动外观时请保留它们本身：

| 位置 | 标识 | 用途 |
|---|---|---|
| `Nav.astro` | `#nav-user-box`、`#nav-user-badge`、`#nav-checkin-btn`、`#nav-cta-btn`、`#nav-cta-btn-m` | 跨站登录态、书币显示与签到 |
| `Nav.astro` | `.admin-link` | 管理员入口显隐 |
| `Nav.astro` | `#theme-toggle`、`#theme-toggle-m` | 深浅色切换 |
| `HybridStream.astro` | `.hybrid-stream`、`.stream-tab[data-filter]`、`.stream-item[data-kind]`、`.stream-list`、`.forum-count-badge` | 双流列表与筛选切换 |
| `BaseLayout.astro` | `#read-progress`、`#lightbox`、`#lightbox-img` | 阅读进度条与图片放大 |
| `PostLayout.astro` | `#post-forum-box`、`#post-forum-list` | 文章底部同板块讨论 |
| `Comments.astro` | `#waline` | 评论区挂载点 |
| `PostMeta.astro` | `.waline-pageview-count[data-path]` | 阅读量统计 |
| `tools.astro` | `vps-price`、`vps-cycle`、`vps-expire`、`vps-result`、`bat-s`、`bat-p`、`bat-ah`、`bat-result`、`ping-list`、`glossary-search`、`.glossary-item[data-text]`、`.copy-cmd[data-cmd]` | 各计算器与工具 |
| `index.astro` | `#hero-live-stats`、`#stat-forum-disc` | 首页实时统计 |

## 5. 不要改动的部分

- `public/yjcnb/`：内容管理后台页面，与外部接口配合，改动会中断发文功能
- `functions/`：登录与后台接口，属于服务端逻辑
- `public/robots.txt`：搜索爬虫规则，后台路径需要保持屏蔽
- `astro.config.mjs` 中 sitemap 的 `filter`：用于把后台路径排除在站点地图之外

## 6. 本地运行与验收

```bash
npm install
npm run dev      # 本地预览
npm test         # 单元测试
npm run build    # 构建 + 生成搜索索引
node scripts/verify-build.mjs    # 检查构建产物
node scripts/verify-cms.mjs      # 检查后台配置
```

提交前请确保 `npm test` 与 `npm run build` 均通过。

## 7. 设计建议

- 站点内容以长文为主，正文可读性优先：栏宽、行高、字号层级比装饰更重要
- 深浅色两套主题都需要检查，所有颜色请使用 CSS 变量，避免硬编码
- 移动端需要单独检查导航折叠、卡片单列、代码块横向滚动
- 双流列表里长文与帖子需要一眼可区分，但视觉权重保持平衡
- 文章页右侧目录在窄屏下可改为折叠或隐藏
