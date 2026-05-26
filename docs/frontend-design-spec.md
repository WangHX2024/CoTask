# CoTask 前端视觉风格规范

> 版本：2.1 | 状态：强制采纳 | 适用：所有前端页面与组件

参考 Ant Design Pro、Linear、Notion 的现代后台风格 —— **克制、留白、简洁、统一**。

> 本规范的核心是：**每个场景只有一个答案**。如果当前 token 不能直接命中你的需求，那是你的需求有问题，不是规范有问题。

---

## 1. 设计哲学

1. **极致一致**：相同语义的元素，全局完全一致；圆角、间距、阴影都来自 token，绝不硬编码
2. **留白胜过装饰**：用 padding 和 gap 创造层级，不靠边框/分割线
3. **扁平为主**：默认无阴影；阴影只用于"悬浮"语义（弹窗、hover、抽屉）
4. **流式布局**：页面不设 `max-width`，用 padding 提供呼吸感；窄表单用内部容器约束

---

## 2. 圆角系统（仅 4 级）

| Token | 值 | 强制用途 |
|---|---|---|
| `--radius-sm` | **6px** | 徽章、状态标签、按钮（Element Plus 默认）、输入框 |
| `--radius-md` | **8px** | 所有卡片、面板、侧边栏内卡片、列表项 hover 背景（**首选**） |
| `--radius-lg` | **12px** | 弹窗、抽屉、Hero 卡、登录卡 |
| `--radius-full` | **9999px** | 胶囊（角色徽章、未读小红点、头像） |

**禁止**：使用 4px、10px、14px、20px 等任何非 token 值。

---

## 3. 间距系统（8pt 网格 — 只用这 5 个值）

| Token | 值 | **唯一**用途 |
|---|---|---|
| `--space-1` | 4px | 图标与紧邻文字、标签内部、超紧凑徽章间距 |
| `--space-2` | 8px | 按钮之间、chip 之间、icon-button 内填充 |
| `--space-4` | 16px | **卡片内** 元素与元素间距、列表行 padding、紧凑卡片间距 |
| `--space-6` | 24px | **卡片** padding、**页面 section** 间距、卡片网格 gap |
| `--space-8` | 32px | 页面 gutter（≥1280px）、Hero padding |

> **`--space-3` (12px)、`--space-5` (20px) 已弃用**。它们存在于 token 中只是为了向后兼容，**新代码禁止使用**。

### 标准内边距速查（强制）

| 场景 | 值 | 备注 |
|---|---|---|
| **页面 gutter** ≥1280 / 768-1279 / <768 | 32 / 24 / 16 | `.page` 自动处理 |
| **卡片** padding（默认） | 24px | `.card` 自动 |
| **卡片** padding（紧凑列表行） | 16px | `.card--compact` |
| **卡片** padding-x（无 padding-y 列表）| 0 24px | `.card--flush` + 内部行自管 |
| 卡片内元素 **gap** | 16px | `--space-4` |
| 页面内 section 之间 | 24px | `.page` 自带 `gap` |
| 卡片网格 gap | 24px | `--space-6` |
| 工具栏 height / padding-x | 56 / 24 | `.workspace-toolbar` |
| 对话框 header / body / footer | 20 24 / 20 24 / 12 24 | 已统一 |
| 列表项之间 | 0 + border-bottom | 不用 gap，用细分割线 |
| 表单 form-item 之间 | 16px | Element Plus 默认 |
| 表单 form-footer 上方间距 | 24px | padding-top |

---

## 4. 页面布局（统一规则）

### 4.1 三种页面类型

**A. 文档页**（Dashboard / Groups / Profile / Inspiration / Notifications / Members）

```html
<div class="page">              <!-- 流式全宽 + 自动 padding -->
  <div class="page-header">...</div>
  <!-- 全宽内容（卡片网格、统计等） -->
  <div class="card-grid">...</div>

  <!-- 或：窄内容（表单、文档） -->
  <div class="content-narrow">  <!-- max-width 880px 居中 -->
    <div class="card">...</div>
  </div>
</div>
```

`.page` 类：
- `padding`: 32px (≥1280px) / 24px (768–1279px) / 16px (<768px)
- 无 `max-width`，完全流式
- `display: flex; flex-direction: column; gap: var(--space-6)` 自动管理 section 间距

`.content-narrow`：`max-width: 880px; margin: 0 auto;`

**B. 工作区页**（ProjectTree / Timeline / Files / Discussion）

```html
<div class="workspace">           <!-- flex column 填满 .content -->
  <header class="workspace-toolbar">...</header>  <!-- 固定 56px -->
  <div class="workspace-body">...</div>           <!-- flex:1 滚动 -->
</div>
```

工具栏：高 56px、`padding: 0 var(--space-6)`、底部 1px 边框
Body：`padding: var(--space-6)`、`flex: 1`、`overflow: auto`

**C. 独立全屏页**（Login）

不使用 `.page`，自定义布局。

### 4.2 强制规则

1. **禁止** 在页面根元素设置 `max-width` —— 一律走 `.page` + 可选 `.content-narrow`
2. **禁止** 在页面根元素设置自定义 `padding` —— 一律走 `.page`
3. 页面内 section 间距由 `.page` 的 `gap` 自动提供；不要在子元素加 `margin-top`

---

## 5. 色彩系统

### 5.1 品牌

| Token | 亮色 | 用途 |
|---|---|---|
| `--color-primary` | `#3D7EFF` | 主按钮、链接、激活、强调 |
| `--color-primary-hover` | `#2B6AE8` | 主色 hover |
| `--color-primary-light` | `rgba(61,126,255,0.10)` | 激活背景、菜单选中 |
| `--color-primary-lighter` | `rgba(61,126,255,0.05)` | 极淡背景 |

### 5.2 语义

| Token | 亮色 | 用途 |
|---|---|---|
| `--color-success` | `#22C55E` | 已完成 |
| `--color-warning` | `#F59E0B` | 警告、临近 DDL、组长徽章 |
| `--color-danger` | `#EF4444` | 错误、危险、阻塞 |
| `--color-info` | `#6B7280` | 中性 |

### 5.3 表面与文字

| Token | 亮色 | 暗色 |
|---|---|---|
| `--bg-page` | `#F4F6FA` | `#0D1117` |
| `--bg-card` | `#FFFFFF` | `#161B22` |
| `--bg-soft` | `#F8FAFC` | `#1A2130` |
| `--text-primary` | `#111827` | `#E6EDF3` |
| `--text-secondary` | `#4B5563` | `#8B949E` |
| `--text-tertiary` | `#9CA3AF` | `#6E7681` |
| `--border-color` | `#E5E7EB` | `#30363D` |
| `--border-subtle` | `#F3F4F6` | `#21262D` |

---

## 6. 卡片系统

```scss
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);   /* 8px */
  padding: var(--space-6);           /* 24px */
  /* 默认无 box-shadow */
}

.card-hover {
  transition: border-color 150ms ease, box-shadow 150ms ease, transform 150ms ease;
  &:hover {
    border-color: var(--color-primary);
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
  }
}
```

- **默认卡片无阴影** —— 用 1px 边框做层次
- **可点击卡片** 用 `.card-hover` 在 hover 时升起
- 卡片间距永远 `var(--space-6)` (24px)
- 卡片内子元素间距 `var(--space-4)` (16px)

---

## 7. 排版

```css
font-family: "PingFang SC", "HarmonyOS Sans SC", "Microsoft YaHei",
             -apple-system, system-ui, sans-serif;
```

| Token | 值 | 用途 |
|---|---|---|
| `--fs-xs` | 11px | 徽章、备注 |
| `--fs-sm` | 12px | 辅助说明、时间 |
| `--fs-base` | 14px | 正文 |
| `--fs-md` | 15px | 列表项标题、卡片标题 |
| `--fs-lg` | 17px | 区块标题 |
| `--fs-xl` | 20px | 页面主标题 |
| `--fs-2xl` | 24px | 营销/登录标题 |
| `--fs-3xl` | 30px | Hero |

字重：400 正文 / 500 列表 / 600 标题 / 700 主标题

---

## 8. 阴影

| Token | 用途 |
|---|---|
| `--shadow-sm` | 已弃用（卡片默认无阴影）|
| `--shadow-md` | hover 升起、抽屉、弹窗 |
| `--shadow-lg` | 模态遮罩、悬浮卡、登录卡 |

**默认卡片不加阴影**，只用 border 区分。

---

## 9. 通用交互原子类（强制使用）

为了真正"统一所有按钮 / 菜单 / 列表 / 选项"，全局提供 4 个原子类。**新代码不允许自己写同等功能的样式 —— 直接用这些类**：

### 9.1 `.list-row` — 所有"可点击的列表行"

适用：侧边栏菜单项、频道列表、文件/文件夹列表、TOC 目录、@提及弹窗、Dropdown 项。

```html
<div class="list-row" :class="{ 'is-active': selected }">
  <el-icon><File /></el-icon>           <!-- 自动 14px / opacity 0.7 → 1 on hover -->
  <span class="list-row__text">条目名</span>
  <span class="list-row__suffix">12</span> <!-- 可选 -->
</div>
```

- 高度 32px（紧凑），`.list-row--lg` 36px
- hover：`bg-soft` + 主色文字
- `.is-active`：`primary-light` + 主色文字 + 500 字重

### 9.2 `.pill-tab` — 所有"水平 pill 导航"

适用：过滤 chip、分类 tab、状态过滤（开/关/所有）。

```html
<div class="pill-tabs">
  <button class="pill-tab is-active">全部 <span class="pill-tab__count">12</span></button>
  <button class="pill-tab">未读 <span class="pill-tab__count">3</span></button>
</div>
```

- 默认透明背景，hover `bg-soft`，激活 `primary-light` + 主色
- 内嵌 count chip 自动样式化

### 9.3 `.icon-btn` — 所有"图标 only 按钮"

```html
<button class="icon-btn"><el-icon><Edit /></el-icon></button>
```

- 32×32 默认（`--sm` 26、`--lg` 36）
- 透明底，hover `bg-soft` + 主色

### 9.4 `.badge` + `.badge--*` — 所有"状态 / 角色 / 计数徽章"

```html
<span class="badge">默认（中性）</span>
<span class="badge badge--primary">主色</span>
<span class="badge badge--success">成功</span>
<span class="badge badge--warning">警告</span>
<span class="badge badge--danger">危险</span>
<span class="badge badge--pill badge--warning">圆角胶囊</span>
```

- `2px 8px` padding，6px 圆角（`--pill` 全圆角）
- 11px / 500 字重 / 单色软底
- **禁止** 任何 ad-hoc role-badge / urgent-badge / cat-tag 等定义

### 9.5 按钮

| 类型 | 使用 |
|---|---|
| `type="primary"` | 每个 region 最多 1 个 |
| 默认 | 次要操作（白底 + 浅边 + hover 染主色） |
| `type="danger" plain` | 危险操作 |
| `text` | 辅助操作（无边框） |
| `.icon-btn` | 图标 only 操作 |

按钮尺寸：`size="small"` 用于工具栏/列表内；默认尺寸用于页面级主操作。**禁止** emoji 作图标。

### 9.6 表单

- `label-position="top"`
- 提交按钮在 `.form-footer`，`justify-content: flex-end`
- 对话框表单使用 `el-dialog` 的 `#footer` slot

---

## 10. 动效

| 场景 | 时长 | 缓动 |
|---|---|---|
| hover 颜色 / 边框 | 150ms | ease |
| 卡片升起 | 150ms | ease |
| 侧边栏折叠 | 200ms | ease |
| 弹窗 | 250ms | Element Plus 默认 |

禁止 > 300ms。

---

## 11. 暗色模式

- 通过 `html.dark` 切换
- 暗色下卡片**保留同样的 1px border**（更深的色）
- 渐变背景在暗色下应**加深**，保持可读性

---

## 12. 必须遵守

1. **禁止** 任何 `max-width` 写在页面根元素 —— 用 `.page` + `.content-narrow`
2. **禁止** 卡片硬编码 `box-shadow` —— 默认无阴影
3. **禁止** 任何 4/10/14/20px 圆角 —— 用 4 级 token
4. **禁止** 颜色硬编码 —— 用 CSS 变量
5. **禁止** 内联样式带固定数值
6. **禁止** emoji 作图标
7. **禁止** 字号 < 11px
8. **禁止** 在组件里重新定义"可点击列表行 / chip / 状态徽章 / 图标按钮" —— 直接用 `.list-row` / `.pill-tab` / `.badge` / `.icon-btn`
9. **禁止** 使用 `--space-3` (12px) 或 `--space-5` (20px) —— 只能用 4/8/16/24/32px 这 5 个值
10. **禁止** 头像尺寸超出 {24, 28, 32, 40, 48, 64, 80} 这一集合
