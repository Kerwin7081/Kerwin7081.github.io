# Kerwin / Enya 投研网页排版与发布 Skill

版本：v1.3  
最后更新：2026-05-13  
适用对象：ChatGPT、Claude、Codex、OpenClaw、Enya、Abba 及其他自动化 Agent  
适用场景：把 Kerwin 的宏观研究、公司深度、产业链分析、组合复盘、客户分享内容生成公开 HTML 网页。

---

## 0. 最重要的执行原则

本文件是 Kerwin / Enya 投研网页的固定执行标准。任何 Agent 生成网页时，必须先读本文件，再生成 HTML。

### 单一事实源

以后所有 Agent 的网页排版、发布、首页上架规则，以本文件为唯一标准。

其他 skill、模板、脚本、发布入口如果与本文件冲突，一律以本文件为准，并应回指本文件，不得各自维护分叉标准。

网页生产分为两个阶段：

### 阶段一：生成预览版

Agent 必须先按照本 Skill 生成 HTML 页面，供 Kerwin 审阅确认。

此阶段只输出或保存预览版，不得直接发布到官网。

### 阶段二：Kerwin 确认后发布

只有当 Kerwin 明确说出以下意思时，才允许发布：

```text
发布
确认发布
发布到官网
更新官网
可以发布
```

然后 Agent 才能把文件写入正式发布目录：

```bash
/opt/agent-publish-stage/{slug}/index.html
/opt/agent-publish-stage/{slug}/meta.json
```

注意：发布器现在默认不会自动把页面加入首页；只有显式首页审批后，页面才会上首页。

系统自动部署到：

```text
https://enyaclawd.com/{slug}/
```

严禁在 Kerwin 未确认前直接发布到官网。

### 首页上架规则

首页上架与“页面已生成”不是同一动作。

1. 页面可以先生成预览版，供 Kerwin 审阅。
2. 在 Kerwin 未明确确认前，禁止把页面加入首页列表。
3. 首页列表的开关文件是：

```text
/opt/kerwin-agent/repos/site/registry.json
```

4. 只有在 Kerwin 确认后，才允许新增或更新对应 registry 条目。
5. 首页卡片标题默认使用 Kerwin 指定文案，不得擅自改写。
6. 首页默认按发布时间倒序排列；若同日多篇，以 `published_at` 更晚者排在更前。
7. 不允许再由 Agent 直接手改首页列表；必须通过统一脚本执行：首页准入脚本：
8. 首页前端只渲染 `homepage_approved: true` 的条目；未带该标记的页面即使存在，也不上首页。

```bash
python3 /opt/kerwin-agent/repos/site/tools/homepage_registry.py approve \
  --slug <slug> \
  --title "<title>" \
  --date "<YYYY年M月D日>" \
  --deck "<deck>" \
  --tag "<tag>" \
  --source enya \
  --published-at "<ISO8601>"
```

下架首页：

```bash
python3 /opt/kerwin-agent/repos/site/tools/homepage_registry.py hide --slug <slug>
```

推荐做法：

- 预览阶段：先完成 `index.html`，必要时仅生成直链预览，不更新首页 registry。
- 确认发布阶段：使用统一脚本写入或更新 `registry.json`，让页面进入首页。
- 禁止多个 Agent 直接各自修改 `registry.json` 结构或排序逻辑。

---

## 1. 核心视觉原则

所有 Kerwin / Enya 投研网页默认采用 **780px 窄版投研简报模板**。

页面气质应接近：

```text
金融研究简报
公众号长文
客户可分享研究页
投顾视角专题报告
```

目标：

1. 清晰阅读。
2. 专业可信。
3. 方便客户转发。
4. 手机端表现稳定。
5. 保持 Kerwin / Enya 统一视觉识别。

禁止：

1. 不要自由发挥成宽屏 Dashboard。
2. 不要使用 1100px 以上大卡片网页。
3. 不要把页面做成炫技型视觉作品。
4. 不要删除 Kerwin / Enya 固定身份识别元素。

---

## 2. 正式发布标准

Enya 网站正式发布路径采用服务器发布中转目录。

标准流程：

```bash
mkdir -p /opt/agent-publish-stage/{slug}/
```

目录内必须放置两个文件：

```text
index.html
meta.json
```

自动部署后的正式地址：

```text
https://enyaclawd.com/{slug}/
```

注意：

1. GitHub Pages 根目录单文件不是首选正式发布流程。
2. 如果临时使用 GitHub Pages 单文件，也必须遵守本 Skill 的视觉和结构规范。
3. 正式官网更新必须走 `/opt/agent-publish-stage/{slug}/`。

---

## 3. meta.json 标准

```json
{
  "title": "页面标题",
  "slug": "page-slug",
  "date": "2026-05-11",
  "author": "Kerwin",
  "category": "AI Research",
  "summary": "一句话摘要",
  "tags": ["AI", "NVIDIA", "Semiconductor"],
  "source": "Kerwin Team x OpenClaw Enya",
  "published": true
}
```

字段说明：

- `title`：页面标题，面向客户展示。
- `slug`：URL slug，只用英文小写、数字和短横线。
- `date`：报告日期。
- `author`：固定为 `Kerwin`。
- `category`：研究类别。
- `summary`：一句话摘要。
- `tags`：主题标签。
- `source`：建议固定为 `Kerwin Team x OpenClaw Enya`。
- `published`：正式发布时设为 `true`。

---

## 4. 页面基础视觉变量

HTML 内必须使用以下 CSS 变量作为默认色系：

```css
:root {
  --bg: #fff1e5;
  --paper: #fffaf4;
  --ink: #1f1a17;
  --muted: #6f6258;
  --line: #dccdbf;
  --blue: #2563eb;
  --up: #16a34a;
  --down: #dc2626;
  --warn: #92400e;
  --gold: #8a5b2b;
  --date: #8b4513;
}
```

含义：

- `--bg`：页面底色，暖纸色。
- `--paper`：顶部、卡片、正文纸张色。
- `--ink`：主文字，近黑褐色。
- `--muted`：次级文字。
- `--line`：分割线。
- `--gold`：Kerwin 主识别色。
- `--blue`：数据强调色。
- `--up`：利好、上涨、正向指标。
- `--down`：风险、下跌、负向指标。
- `--warn`：警示。
- `--date`：日期色。

---

## 5. 页面宽度与整体结构

必须采用 780px 主容器，正文内部 700px。

```css
.page {
  max-width: 780px;
  margin: 0 auto;
  padding: 10px 10px 28px;
}

.shell {
  background: var(--paper);
  border: 1px solid var(--line);
  box-shadow: 0 10px 30px rgba(15,23,42,.06);
}

.wrap {
  max-width: 700px;
  margin: 0 auto;
  background: #fff;
}
```

页面固定结构顺序：

```text
1. 返回首页按钮
2. page + shell 外壳
3. topbar 顶部信息区
4. wrap 内容区
5. hero 主视觉区
6. nav 横向导航
7. section 正文章节
8. conclusion 结语区
9. footer 免责声明与署名
```

---

## 6. 返回首页按钮

页面顶部必须有返回首页按钮，放在 `body` 开始后、`.page` 之前。

```html
<div class="back"><a href="/">← 返回首页</a></div>
```

```css
.back {
  max-width: 780px;
  margin: 0 auto;
  padding: 6px 16px 0;
}

.back a {
  display: inline-block;
  font-family: Arial, 'PingFang SC', sans-serif;
  font-size: 12px;
  color: #8a5b2b;
  text-decoration: none;
  font-weight: 700;
  padding: 3px 10px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--paper);
}
```

页面底部也应保留一个返回首页入口，避免移动端用户读到底部后必须回滚。

---

## 6A. 页面浏览量统计

每个正式子页面必须带浏览量统计。

要求：

1. 在 `</head>` 前加入页面标识：

```html
<!-- pv-counter data-page-slug={slug} -->
```

2. 页面底部显示浏览量文本与数值容器：

```html
<div class="counter-wrap">👀 页面浏览量：<span id="counter-num">...</span></div>
```

3. 在 `</body>` 前加入统计脚本：

```html
<script>
(function(){
  var slugVal = '{slug}';
  var counterUrl = 'https://enyaclawd-counter.kerwin-finance.workers.dev?page=' + encodeURIComponent(slugVal);
  var el = document.getElementById('counter-num');
  fetch(counterUrl).then(function(r){return r.json()}).then(function(d){ if(el) el.textContent = d.count.toLocaleString(); }).catch(function(){ if(el) el.textContent = '-'; });
  fetch(counterUrl,{method:'POST'}).then(function(r){return r.json()}).then(function(d){ if(el) el.textContent = d.count.toLocaleString(); }).catch(function(){});
})();
</script>
```

4. 不得删除统计区；若页面极简，也必须至少保留隐藏度较低的可见浏览量模块。

---

## 7. Topbar 顶部区

Topbar 是 Kerwin 网页最重要的身份识别区，必须保留。

```html
<div class="topbar">
  <div class="top-kicker">KERWIN TEAM PRESENTS</div>
  <h1 class="top-title">主题名称<br>研究简报</h1>
  <div class="top-date">报告发布日期：2026年5月11日</div>
  <div class="top-block">
    本文由 Kerwin 团队自动化呈现：Kerwin 确定研究主题及校对逻辑，OpenClaw 打造的 Enya 全程自动化编码实现。<br>
    底层 AI 模型：GPT-5.5 及 Claude 付费版。Enya：香港首个由 OpenClaw 打造的女性投顾 Agent。
  </div>
</div>
```

```css
.topbar {
  background: linear-gradient(180deg,#fff8f0 0%,#fffaf4 100%);
  padding: 18px 22px 14px;
  border-top: 8px solid #111;
  border-bottom: 1px solid #111;
}

.top-kicker {
  font: 700 11px/1.2 Arial,sans-serif;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: #8a7769;
  margin-bottom: 8px;
}

.top-title {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.12;
  margin: 0 0 6px;
  color: #16110d;
}

.top-date {
  font-size: 13px;
  color: #8b4513;
  line-height: 1.6;
  font-weight: 600;
}

.top-block {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
  font-size: 13px;
  line-height: 1.8;
  color: #4b413a;
  font-family: Arial, Helvetica, sans-serif;
}
```

---

## 8. Hero 主视觉区

```html
<div class="hero">
  <div class="badge">2026 kerwin 宏观对冲及 AI 精选组合</div>
  <div class="hero-title">主题标题</div>
  <div class="hero-sub">副标题 / 投研判断</div>
  <div class="hero-meta">2026年5月11日 · 专题研究报告</div>
</div>
```

```css
.hero {
  background: linear-gradient(180deg,#fff8ef 0%,#fdf4ea 100%);
  padding: 34px 24px 28px;
  text-align: center;
  border-bottom: 1px solid #ead7c9;
}

.badge {
  display: inline-block;
  background: #f7efe6;
  border: 1px solid #dccdbf;
  border-radius: 20px;
  padding: 5px 14px;
  color: #8a5b2b;
  font: 700 11px Arial,sans-serif;
  letter-spacing: 1px;
  margin-bottom: 18px;
}

.hero-title {
  color: #16110d;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 10px;
}

.hero-sub {
  color: #7b4f24;
  font: 14px Arial, Helvetica, sans-serif;
  margin-bottom: 6px;
}

.hero-meta {
  color: #9a3412;
  font: 700 12px Arial, Helvetica, sans-serif;
}
```

---

## 9. 横向导航 nav

每篇文章必须有横向导航，锚点对应正文 section。

```html
<nav class="nav">
  <a href="#intro">核心判断</a>
  <a href="#structure">交易结构</a>
  <a href="#companies">公司解剖</a>
  <a href="#conclusion">结语</a>
</nav>
```

```css
.nav {
  display: flex;
  overflow-x: auto;
  background: #fcf5ee;
  border-bottom: 1px solid var(--line);
  scrollbar-width: none;
}

.nav::-webkit-scrollbar {
  display: none;
}

.nav a {
  flex-shrink: 0;
  padding: 11px 14px;
  font: 600 12px Arial,sans-serif;
  color: #7a685a;
  text-decoration: none;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
}

.nav a:hover {
  color: #1f1a17;
  border-color: #8a5b2b;
}
```

---

## 10. Section 正文章节

```html
<div class="section" id="intro">
  <div class="section-label">引言 · 核心判断</div>
  <h2>章节标题</h2>
  <p>正文内容。</p>
</div>
```

```css
.section {
  padding: 26px 20px;
  border-bottom: 1px solid #efe3d7;
}

.section-label {
  font: 700 10px Arial,sans-serif;
  color: #8a5b2b;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 14px;
}

.section h2 {
  font-size: 22px;
  line-height: 1.35;
  margin: 0 0 14px;
  color: #16110d;
}

.section h3 {
  font-size: 17px;
  line-height: 1.4;
  margin: 18px 0 10px;
  color: #2d2419;
  padding-bottom: 8px;
  border-bottom: 1px solid #e7ddd3;
}

p {
  font-size: 14px;
  line-height: 1.85;
  color: #3d3229;
  margin: 0 0 12px;
}
```

---

## 11. Stat Grid 数据卡片

适合展示关键数字、合同金额、增长率、市值、Capex、市场份额等。

```html
<div class="stat-grid">
  <div class="stat-cell">
    <div class="stat-value gold">$5亿</div>
    <div class="stat-label">真实预付现金</div>
  </div>
</div>
```

```css
.stat-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 16px 0;
}

.stat-cell {
  background: #fdfaf5;
  border: 1px solid #e7ddd3;
  padding: 18px 16px;
  text-align: center;
}

.stat-value {
  font: 700 28px Georgia,'Times New Roman',serif;
  color: #16110d;
  line-height: 1.1;
  margin-bottom: 6px;
}

.stat-value.up { color: var(--up); }
.stat-value.down { color: var(--down); }
.stat-value.blue { color: var(--blue); }
.stat-value.gold { color: var(--gold); }

.stat-label {
  font: 12px Arial,sans-serif;
  color: #6f6258;
  line-height: 1.4;
}
```

---

## 12. Table 表格

所有对比内容必须用 `table-wrap` 包裹，保证手机端横向滚动。

```html
<div class="table-wrap">
  <table>
    <thead>
      <tr><th>维度</th><th>公司A</th><th>公司B</th></tr>
    </thead>
    <tbody>
      <tr><td>指标</td><td>内容</td><td>内容</td></tr>
    </tbody>
  </table>
</div>
```

```css
.table-wrap {
  overflow-x: auto;
  margin: 16px 0;
  border: 1px solid #e5d9cc;
}

table {
  width: 100%;
  border-collapse: collapse;
  font: 13px Arial,sans-serif;
  min-width: 500px;
}

thead tr {
  background: #3d3229;
  color: #f5f0e8;
}

thead th {
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  letter-spacing: .04em;
  font-size: 11px;
}

tbody tr:nth-child(even) {
  background: #fdfaf7;
}

tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid #e5d9cc;
  color: #3d3229;
  line-height: 1.5;
  vertical-align: top;
}
```

---

## 13. Flow 流程图

用于资金流、产业传导、风险传导、政策传导和商业模式拆解。

```html
<div class="flow">
  <div class="flow-box">第一层</div>
  <div class="flow-arrow">↓</div>
  <div class="flow-box alt">第二层</div>
  <div class="flow-arrow">↓</div>
  <div class="flow-box accent">结论层</div>
</div>
```

```css
.flow {
  display: flex;
  flex-direction: column;
  gap: 0;
  margin: 16px 0;
}

.flow-box {
  background: #f5f0e8;
  color: #3d3229;
  padding: 12px 16px;
  font: 13px Arial,sans-serif;
  line-height: 1.5;
  border: 1px solid #e5ddd3;
  border-radius: 4px;
}

.flow-box.alt {
  background: #eaf0f7;
  border-color: #c8d6e5;
}

.flow-box.light {
  background: #f0f4e8;
  border-color: #d0dcc0;
}

.flow-box.accent {
  background: #fef5f0;
  border-color: #e8c8b0;
}

.flow-arrow {
  text-align: center;
  font-size: 18px;
  color: #b8a590;
  padding: 2px 0;
  line-height: 1;
}
```

---

## 14. Callout 核心判断

```html
<div class="callout">
  <div class="callout-label">核心结论</div>
  <p>这里写核心判断。</p>
</div>
```

```css
.callout {
  border: 1px solid #e7ddd3;
  border-left: 4px solid #8a5b2b;
  padding: 18px 20px;
  margin: 16px 0;
  background: #fdfaf5;
  font-size: 13px;
  line-height: 1.8;
  color: #5c3d1e;
}

.callout-label {
  font: 700 10px Arial,sans-serif;
  letter-spacing: .15em;
  color: #8a5b2b;
  text-transform: uppercase;
  margin-bottom: 8px;
}
```

---

## 15. Alert 风险提示

```html
<div class="alert">
  <div class="alert-label">风险提示</div>
  <p>这里写风险。</p>
</div>
```

```css
.alert {
  background: #fff7ed;
  border-left: 3px solid #c77728;
  border-radius: 4px;
  padding: 14px 16px;
  margin: 16px 0;
  font-size: 13px;
  color: #6b3f15;
}

.alert strong {
  color: #9a3412;
}

.alert-label {
  font: 700 10px Arial,sans-serif;
  letter-spacing: .15em;
  color: #9a3412;
  text-transform: uppercase;
  margin-bottom: 8px;
}
```

---

## 16. Path Grid 投资路径 / 观察项

用于投资含义、红线判断、多空逻辑、战略路径、组合动作、观察指标。

### 16.1 数字编号卡片

```html
<div class="path-grid">
  <div class="path-item">
    <div class="path-num">01</div>
    <div>
      <div class="path-title">标题</div>
      <p class="path-desc">说明文字。</p>
    </div>
  </div>
</div>
```

```css
.path-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin: 16px 0;
}

.path-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #fdfaf5;
  border: 1px solid #e7ddd3;
  border-radius: 6px;
}

.path-num {
  font: 700 32px Georgia,serif;
  color: #8a5b2b;
  line-height: 1;
  flex-shrink: 0;
  width: 38px;
}

.path-title {
  font: 600 13px Arial,sans-serif;
  color: #5c3d1e;
  letter-spacing: .04em;
  margin-bottom: 6px;
}

.path-desc {
  font-size: 13px;
  line-height: 1.7;
  color: #6b5d53;
  margin: 0;
}
```

### 16.2 股票代码 / Ticker 卡片

重要修订：**不要把股票代码 GLW、IREN、NVDA、TSM、AMD 等放进 `.path-num`。**

`.path-num` 只适合 `01 / 02 / 03` 这种数字编号。股票代码长度不固定，如果使用 `.path-num`，会导致大字母与正文重叠。

股票代码必须使用 `.ticker`。

```html
<div class="path-item">
  <div class="ticker">GLW</div>
  <div>
    <div class="path-title">Corning：稳健型核心仓观察</div>
    <p class="path-desc">说明文字。</p>
  </div>
</div>
```

```css
.ticker {
  min-width: 64px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dccdbf;
  background: #f7efe6;
  color: #8a5b2b;
  border-radius: 4px;
  font: 800 15px Arial,sans-serif;
  letter-spacing: .06em;
  flex-shrink: 0;
}
```

---

## 17. Timeline 方法论 / 事件线

```html
<div class="timeline">
  <div class="timeline-item">
    <div class="timeline-date">方法论 01</div>
    <div class="timeline-content">说明文字。</div>
  </div>
</div>
```

```css
.timeline {
  margin: 16px 0;
  position: relative;
  padding-left: 28px;
  border-left: 2px solid #e0d5c5;
}

.timeline-item {
  margin-bottom: 20px;
  position: relative;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: -34px;
  top: 4px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #8a5b2b;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #8a5b2b;
}

.timeline-date {
  font: 11px 'Courier New',monospace;
  color: #8a5b2b;
  letter-spacing: .06em;
  margin-bottom: 3px;
}

.timeline-content {
  font: 13px Arial,sans-serif;
  color: #4b3826;
  line-height: 1.6;
}
```

---

## 18. Tag 标签

```html
<span class="tag green">利好</span>
<span class="tag red">风险</span>
<span class="tag amber">观察</span>
<span class="tag grey">中性</span>
```

```css
.tag {
  display: inline-block;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 700;
  border-radius: 2px;
}

.tag.green { background: #dcfce7; color: #166534; }
.tag.red { background: #fee2e2; color: #991b1b; }
.tag.amber { background: #fef3c7; color: #92400e; }
.tag.grey { background: #f0ede8; color: #6f6258; }
```

---

## 19. Conclusion 结语区

结语区可使用深色背景，增强收束感。

```html
<div class="conclusion" id="conclusion">
  <h2>结语</h2>
  <p>结论文字。</p>
</div>
```

```css
.conclusion {
  background: #1f1a17;
  padding: 28px 20px;
  border-bottom: 1px solid #111;
}

.conclusion h2 {
  color: #f5f0e8;
  font-size: 22px;
  margin-bottom: 14px;
}

.conclusion p {
  color: #e8d5b8;
}
```

---

## 20. Footer 标准

Footer 必须包含免责声明和固定署名。

标准文案：

```html
<div class="footer">
  本文为投资研究参考，不构成具体投资建议。数据截至 YYYY 年 M 月 D 日。<br>
  © Kerwin｜宏观对冲及AI 精选组合研究｜Enya.Clawd 自动化呈现
</div>
```

如果需要列来源，可写：

```html
<div class="footer">
  本文为投资研究参考，不构成具体投资建议。数据来源：NVIDIA 官方公告、公司公告、SEC 文件、Reuters、Bloomberg、Enya 系统。截至 YYYY 年 M 月 D 日。<br>
  © Kerwin｜宏观对冲及AI 精选组合研究｜Enya.Clawd 自动化呈现
</div>
```

Footer 样式：

```css
.footer {
  padding: 20px;
  font-size: 11px;
  color: #6f6258;
  line-height: 1.8;
  border-top: 1px solid #e7ddd3;
  background: #fbf7f1;
  font-family: Arial, Helvetica, sans-serif;
}
```

注意：

- 固定署名必须使用：`© Kerwin｜宏观对冲及AI 精选组合研究｜Enya.Clawd 自动化呈现`
- 不要再使用旧版：`© Kerwin｜AI 精选组合研究｜Enya.Clawd 自动化呈现`

---

## 21. 移动端标准

必须保留手机端适配。

```css
@media(max-width:640px) {
  .page { padding: 0 4px 20px; }
  .topbar { padding: 16px 16px 12px; }
  .top-title { font-size: 26px; }
  .hero { padding: 28px 16px 24px; }
  .hero-title { font-size: 26px; }
  .section { padding: 22px 16px; }
  .section h2 { font-size: 20px; }
  .stat-grid { grid-template-columns: 1fr 1fr; }
  .stat-value { font-size: 24px; }
  td, th { font-size: 11px; padding: 6px 8px; }
  .path-item { gap: 12px; padding: 14px; }
  .path-num { font-size: 28px; width: 30px; }
  .ticker { min-width: 54px; height: 30px; font-size: 13px; }
}
```

移动端原则：

1. 保留双列统计卡片。
2. 表格必须允许横向滚动。
3. 导航必须允许横向滑动。
4. 不使用复杂大图。
5. 不使用超宽卡片。
6. 股票代码必须用 `.ticker`，避免重叠。

---

## 22. 禁止事项

1. 不要使用 1100px 以上宽屏 Dashboard 版式。
2. 不要把股票代码放进 `.path-num`。
3. 不要删除返回首页按钮。
4. 不要删除 Topbar 固定出品人文案。
5. 不要删除 Hero 区。
6. 不要删除横向导航。
7. 不要直接输出纯 Markdown 作为最终网页。
8. 不要把正文做成密集大段，没有 section-label、h2、callout、stat-grid、table 等结构。
9. 不要使用中文网站作为数据来源。
10. 不要在 footer 使用旧版权文案。
11. 不要在 Kerwin 未确认前直接发布到官网。
12. 不要把 GitHub Pages 单文件更新误认为 Enya 官网正式发布。

---

## 23. Agent 标准工作流

### 23.1 生成网页时

Agent 应先生成：

```text
index.html
meta.json
```

并把 HTML 预览版发给 Kerwin 确认。

确认前只做以下动作：

1. 输出 HTML 代码。
2. 生成本地预览文件。
3. 放到草稿目录。
4. 生成可审阅链接，但必须明确标注为预览。

### 23.2 发布网页时

只有 Kerwin 明确说“发布”后，才执行：

```bash
mkdir -p /opt/agent-publish-stage/{slug}/
cp index.html /opt/agent-publish-stage/{slug}/index.html
cp meta.json /opt/agent-publish-stage/{slug}/meta.json
```

最终地址：

```text
https://enyaclawd.com/{slug}/
```

发布后必须反馈：

```text
已发布
slug
正式地址
index.html 和 meta.json 已写入
```

---

## 24. Agent 执行简版

给其他 Agent 的极简执行指令：

```text
请先读取 Kerwin7081.github.io 仓库根目录的 KERWIN_WEB_SKILL.md，再按该规范生成 HTML。

必须使用：
背景 #fff1e5，正文纸色 #fffaf4，主文字 #1f1a17，强调色 #8a5b2b。
页面宽度 max-width 780px，正文 wrap max-width 700px。
结构必须包含：返回首页按钮、page+shell、topbar、hero、nav、section、stat-grid、table-wrap、flow、callout、alert、path-grid、timeline、conclusion、footer。

Topbar 固定包含：
KERWIN TEAM PRESENTS
主题名称 + 研究简报
报告发布日期
固定出品人文案。

Footer 固定署名：
© Kerwin｜宏观对冲及AI 精选组合研究｜Enya.Clawd 自动化呈现

股票代码如 GLW、IREN、NVDA、TSM、AMD 必须使用 .ticker 样式，不得使用 .path-num。

工作流：
先生成 HTML 预览给 Kerwin 确认。
Kerwin 明确说“发布”后，才写入：
/opt/agent-publish-stage/{slug}/index.html
/opt/agent-publish-stage/{slug}/meta.json
最终地址：
https://enyaclawd.com/{slug}/
```

---

## 25. 标准参考页面

当前标准由以下页面沉淀而来：

1. `/ai-tech-cycle/`
2. `/korea-national-wealth-ai-brief-tmp/`
3. `/nvda-corning-iren-dsx-20260508.html` 最新修复版

其中第 3 个页面的关键修订是：

- 修复 `GLW / IREN` 大字与正文重叠。
- 新增 `.ticker` 股票代码样式。
- Footer 固定改为：`© Kerwin｜宏观对冲及AI 精选组合研究｜Enya.Clawd 自动化呈现`。
- 明确 GitHub Pages 单文件不等于 Enya 官网正式发布。

---

## 26. 最终判断

Kerwin / Enya 网页不是普通 HTML 页面，而是一种固定投研表达格式。以后任何 Agent 生成网页时，必须先遵守本文件，再根据具体内容调整章节和数据。

视觉可微调，身份识别不可漂移。

最关键的三条执行纪律：

1. **先生成，给 Kerwin 确认，再发布。**
2. **发布必须走 `/opt/agent-publish-stage/{slug}/index.html + meta.json`。**
3. **股票代码用 `.ticker`，不要用 `.path-num`。**
