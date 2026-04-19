```markdown
# 体育考试管理系统：设计系统指南 (Design System Manual)

## 1. 核心设计愿景：动能精密 (Kinetic Precision)

本设计系统旨在打破传统 SaaS 仪表盘的沉闷感，将“竞技体育的爆发力”与“教育评价的严谨性”完美融合。我们的设计北极星是 **“动能精密” (Kinetic Precision)**。

这不是一个常规的表格堆砌系统。我们通过有意的**非对称布局 (Intentional Asymmetry)**、**分层深度 (Layered Depth)** 和**大字号排版 (Editorial Typography)**，营造出一种类似高端运动杂志的编辑感。界面不仅是数据的载体，更是运动员（学生）表现的数字化舞台。

---

## 2. 色彩系统 (Color Palette)

色彩不应仅是装饰，而应作为“数据状态的直观翻译”。

### 核心色彩逻辑
- **完美/满分 (Perfect):** `on_surface` (#111827) —— 深沉的炭黑，象征巅峰表现与绝对权威。
- **卓越 (Excellent):** `success` (#10B981) —— 充满生命力的绿色，用于优秀评价。
- **及格 (Passing):** `yellow` (#F59E0B) —— 警示与通过的平衡点。
- **不及格 (Failing):** `error` (#EF4444) —— 醒目、果断。
- **品牌/主色 (Primary):** `primary` (#00685f) —— 运动蓝绿调，传达专业、可靠且具备活力的企业形象。

### 无边框原则 (The "No-Line" Rule)
严禁使用 1px 的实线边框进行物理分割。所有的区域划分必须通过以下方式实现：
1. **色块位移:** 利用 `surface` 与 `surface-container-low` 的色差定义边界。
2. **影之深度:** 仅在浮动组件上使用极淡的弥散投影。

### 表面阶梯与嵌套 (Surface Hierarchy)
通过 `surface-container` 的五个能级（Lowest to Highest）构建物理层级。
- **背景层:** 使用 `surface` (#f8f9ff)。
- **内容容器:** 使用 `surface_container_lowest` (#ffffff) 以获得最高对比度。
- **嵌套卡片:** 在容器内，使用 `surface_container_low` (#eff4ff) 或玻璃材质。

### 玻璃态与渐变 (Glass & Gradient)
- **浮动面板:** 使用 `surface_variant` 并结合 `backdrop-filter: blur(20px)`。
- **签名渐变:** 重要的行动按钮（CTA）或核心趋势图表，应在 `primary` 到 `primary_container` 之间建立线性渐变，赋予界面“灵魂”与动态感。

---

## 3. 排版系统 (Typography)

我们追求的是“具有呼吸感的数据层次”。

| 类别 | 字体 (Font Family) | 规模 (Size) | 情感表达 |
| :--- | :--- | :--- | :--- |
| **Display (L/M/S)** | Plus Jakarta Sans | 2.25rem - 3.5rem | 极具张力的分数展示，强调竞技感 |
| **Headline (L/M/S)** | Plus Jakarta Sans | 1.5rem - 2.0rem | 模块标题，体现编辑性布局的权威感 |
| **Title (L/M/S)** | Inter / PingFang SC | 1.0rem - 1.375rem | 数据组标签，清晰、平衡 |
| **Body (L/M/S)** | Inter / PingFang SC | 0.75rem - 1.0rem | 核心内容，极致的可读性 |
| **Label (M/S)** | Inter | 0.6875rem - 0.75rem | 辅助说明，不干扰主视觉 |

**设计细节：** 中文字体建议优先使用 `PingFang SC` 或 `Source Han Sans`，并适当增加字间距（Letter Spacing），避免在深色背景下显得过于拥挤。

---

## 4. 高级深度与海拔 (Elevation & Depth)

### 阶梯式分层 (Tonal Layering)
通过颜色的明度变化而非阴影来创造深度。例如，一个“学生成绩概览”面板应遵循：
- `surface` (底层) > `surface_container_low` (卡片背景) > `surface_container_lowest` (核心数据点凸显)。

### 环境阴影 (Ambient Shadows)
当需要悬浮效果时，使用基于 `on_surface` 颜色的色调阴影，而非死板的灰色：
- **Box-shadow:** `0px 24px 48px rgba(11, 28, 48, 0.06)`
- 这种投影应像雾一样弥散，模拟自然光照射下的物理质感。

### 幽灵边框 (The "Ghost Border")
若在特定高亮场景下必须使用边框，请使用 `outline_variant` 标记并设置 10%-20% 的不透明度。它应当是“感知可见”而非“视觉阻碍”。

---

## 5. 组件规范 (Components)

### 按钮 (Buttons)
- **Primary:** `primary` 背景 + `on_primary` 文字，采用 `xl` (0.75rem) 圆角。悬停时启用 15% 透明度的叠层。
- **Kinetic Action:** 带有微小位移感（Movement Stroke）的渐变按钮，用于启动考试等关键任务。

### 数据可视化碎片 (Data Viz Fragments)
- **仪表盘:** 严禁使用标准饼图。采用带有 `backdrop-blur` 的环形图，并结合 `blurred movement strokes`（模糊动感线条）来展示学生体能趋势。
- **网格:** 核心背景层背景可注入 24px 的极淡点状网格（Dot Grid），增强精密感。

### 状态标签 (Chips)
- **满分标签:** 背景为 `on_surface` (#111827)，文字为 `primary_fixed`，体现极致荣耀感。
- **反馈标签:** 去除背景色，仅使用 `surface_variant` 作为背景，并用 4px 的圆点指示器（Success/Error）表示状态。

---

## 6. 执行准则 (Do's & Don'ts)

### ✅ 执行 (Do's)
- **拥抱负空间:** 允许数据在大面积的空白中“呼吸”。
- **意图化不对称:** 在仪表盘顶部使用非对称的磁贴排版（Masonry-like layout）。
- **微互动:** 给所有卡片添加微小的 Hover 升起效果（使用 Tonal Layering 切换，而非加深阴影）。

### ❌ 避免 (Don'ts)
- **禁止线框化:** 严禁在卡片周围使用可见的 100% 不透明度边框。
- **禁止视觉廉价感:** 避免使用系统自带的蓝（#0000FF），必须使用经过调和的 `primary` 蓝绿色调。
- **禁止数据拥挤:** 单个屏幕内，核心 Display 指标不得超过 3 个。

---

### 结语
本系统并非一套死板的限制，而是一套构建**能量感**的框架。通过对 `surface` 层级的细腻打磨和排版的错落布置，我们要让 PE 考试管理工作从“繁琐的录入”转变为“对卓越表现的数字化见证”。```