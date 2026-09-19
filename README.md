<div align="center">

# 旅游路书生产流水线

**把一句话目的地，变成一份可核实、图文匹配、可打印的 HTML 路书**

[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg?style=flat-square)](LICENSE)
[![Skill](https://img.shields.io/badge/WorkBuddy-Agent%20Skill-4B6BFB.svg?style=flat-square)](#安装)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](#环境要求)
[![Dependencies](https://img.shields.io/badge/dependencies-Pillow%20%7C%20fontTools%20(optional)-2496ED.svg?style=flat-square)](#环境要求)
[![Zero Deploy](https://img.shields.io/badge/deploy-not%20required-6f42c1.svg?style=flat-square)](#设计取舍)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](#贡献指南)

一个端到端的 **AI Agent 技能包**：从需求采集、路线规划、多源数据核验，到生成零外链的单文件 HTML 路书。

[功能特性](#功能特性) · [安装](#安装) · [快速开始](#快速开始) · [配置](#配置说明) · [示例](#示例) · [常见问题](#常见问题) · [贡献](#贡献指南) · [许可证](#许可证)

<sub>📄 [发布说明](RELEASE.md) —— 文件结构组织、提交规范、发布注意事项</sub>

</div>

---

## 项目简介

**English Summary**

> An end-to-end AI agent skill that turns a one-line travel request into a verifiable, print-ready
> single-file HTML roadbook. It orchestrates interactive requirement gathering, route planning,
> cross-source verification (AMap REST + OSRM + Xiaohongshu), HTML generation, and gated image
> validation — with a hard rule that **every number must be traceable to a source**.

### 它解决什么问题

用 AI 规划长途旅行，最常见的失败不是"写得不漂亮"，而是**数字不可信**：里程对不上、图片配错景点、攻略早已过时。这个技能包把四类真实踩过的坑固化成强制流程。

| 坑 | 实证后果（真实项目数据） | 本项目的做法 |
|---|---|---|
| 里程**只核总量、不核逐段** | 总量仅差 39 km，但有一天虚高 **198 km**、另一天漏算 **265 km** | 逐段核验 + 按单日纯驾驶时长排序 |
| 出发地只问到**市级** | 某市与其下辖县相距 100 km，单段误差即达 **198 km** | 强制问到区/县级 |
| 手填景区坐标 | 纬度错 0.28°（≈31 km），当天里程虚高 **76 km** | 任何非城区 POI 先经 POI 搜索校准 |
| 图片**盲取第 N 张**即入页面 | 抓到头像、攻略信息图、与途经点不符的图 | 分级闸门校验（默认轻量档） |

> 💡 设计哲学：**可靠性 > 完整性 > 华丽度。** 一次信息编造，或一张配错景点的图，比朴素但可靠的交付差得多。

### 交付物长什么样

一份**零外链的单文件 HTML**：

- 双击即可打开，不需要服务器、不需要联网、不需要任何账号
- 可直接打印 / 导出 PDF（路书是带在手上的东西）
- 内含内联 SVG 信息图（路线示意、补能空档、海拔剖面）
- 每条信息带**置信度徽章**（🔎 已核实 / ⏳ 待核实 / 📝 批注 / ⚠️ 风险）

---

## 功能特性

### 🗺 路线与数据

- **逐段里程核验**：以高德 REST `/v3/direction/driving?strategy=0` 为主口径，OSRM 作独立交叉引擎（只信里程，不信时长——其对中国限速的模型不准）
- **POI 坐标校准**：非城区 POI 先经 `/v3/place/text` 校准坐标，避免景区支线段里程失真
- **落脚点比选三步法**：按**纯驾驶时长**而非里程挑过夜城市，比"最长单日"而非平均值
- **单日疲劳预警**：纯驾驶 > 8 h 的日子单独标出

### 📰 情报时效三筛（递进式硬筛）

小红书情报在进入候选池前必须过三道筛：

1. **只采信 2 年内发布**的笔记（中国路网与补能设施更新周期普遍 1–2 年）
2. **只采信与本次行程同季节**的笔记 —— 判定看客观条件（气温带 / 昼夜长度 / 雨季 / 结冰期），**不看月份数字**；交界月按实况判
3. 再找**时效分水岭**（新路通车、充电桩投运、景区改制等），分水岭之前的信息整体作废

> 同季节素材不足时，**宁可减少情报量，也不跨季节硬凑**。

### 🖼 分级闸门图片校验

按需选择严格程度，**默认轻量档**（图片是加分项，不是核心交付物）：

| 档 | 适用 | 跑的闸门 |
|---|---|---|
| **A · 不放图** | 不需要 / 行程短 / 时间紧 | — |
| **B · 轻量** ⭐ 默认 | 要图，但不苛求精确匹配 | ① 有效性 ② 尺寸 |
| **C · 完整** | 明确要求"图必须对得上" | ①–⑤ 全部 |

五道闸门：**① 有效性**（破图/防盗链占位图/头像）→ **② 尺寸合理性**（挡长图拼接）→ **③ 素材类型**（挡攻略信息图）→ **④ 语义一致性**（`keywords` 必须命中图片邻近文案）→ **⑤ 命名互锁**（`photos/d{天:02d}-{cat}.webp`）。

### 🎯 交互式需求采集

12 项必要信息分三轮递进采集（**先给一版骨架，再指着骨架追问**——用户说不清自己想要什么，但看到具体方案立刻能指出哪里不对）。采集完输出一张「需求卡」作为开工依据。

### 🧩 HTML 生成规范

随包附带一份通用的路书制作规范（`references/roadbook-spec-v1.0.md`），约束结构（五层骨架）、视觉（低饱和双专色、三栈字体、七档响应式）与内容（数据标注格式、置信度分级、禁用词）三类要求。**若你另有自己的规范，以你的为准。**

---

## 安装

### 环境要求

| 依赖 | 必需性 | 说明 |
|---|---|---|
| **Python 3.10+** | 必需 | |
| **Pillow** | 必需 | 图片处理（`imgcrop.py`） |
| **bsk**（browser-skill） | 必需 | 复用你已登录的 Chrome 抓小红书；`preflight.py` 会给出安装指引 |
| **高德 REST Key** | 必需 | 免费申请，见下方 |
| **fontTools** | 可选 | 仅自托管中文字体子集化时需要 |

### 方式一：作为 WorkBuddy 技能安装（推荐）

```bash
git clone https://github.com/Wexexortexort/travel-roadbook-pipeline.git \
  ~/.workbuddy/skills/travel-roadbook-pipeline
```

技能目录名与 `SKILL.md` 的 `name` 字段一致，克隆后即可被直接发现，**无需改名**。

### 方式二：独立使用脚本

```bash
git clone https://github.com/Wexexortexort/travel-roadbook-pipeline.git
cd travel-roadbook-pipeline
python -m pip install pillow          # 必需
python -m pip install fonttools       # 可选
```

### 首次自检（强烈建议）

```bash
python scripts/preflight.py --workdir /path/to/your/roadbook
```

输出：

```
✅ 就绪            全部关键依赖在位
❌ 缺少关键依赖    缺高德 Key 或 bsk，必须先补齐
```

缺什么，脚本会直接告诉你怎么补 —— 它的缺失指引是自包含的，不依赖任何上游上下文。

---

## 快速开始

安装完成后，直接对 Agent 说：

```
帮我做一份国庆 7 天川西小环线的路书，从成都出发，2 人轮换开车，纯电车
```

Agent 会按流水线推进：

```
Phase -1  环境预检          → 缺什么先补什么
Phase  0  交互式需求采集    → 三轮追问 12 项，产出需求卡
Phase  1  路线规划          → 骨架 + 落脚点比选
Phase  2  多渠道交叉验证    → 高德 REST（主口径）+ OSRM（交叉）+ 小红书（时效三筛）
Phase  3  路书内容规划      → 11 个信息模块
Phase  4  HTML 生成         → 单文件、零外链、可打印
Phase  5  图片补充与校验    → 三档路径（默认轻量）
Phase  6  交付前自检        → 静态检查 + 数据守恒 + 浏览器实测
```

---

## 配置说明

### 高德 Key（免费）

1. 到 [lbs.amap.com](https://lbs.amap.com) 注册并完成**实名认证**（个人开发者即可）
2. 控制台 → 应用管理 → 创建应用 → 添加 Key
3. 🔴 **服务平台必须选「Web 服务」** —— 选成「Web端(JS API)」调 REST 会返回 `INVALID_USER_KEY`，而人会误以为 Key 本身有问题。**这是最高频的坑。**
4. 数字签名**建议不启用**（启用了每次请求要额外算 sig）
5. 存成文件，例如：

```bash
mkdir -p ~/.workbuddy/keys
echo -n "你的KEY" > ~/.workbuddy/keys/amap.key
```

> ⚠️ **密钥纪律**：**不要把 Key 贴进对话** —— 对话通道会对疑似密钥做截断/脱敏（实测 40 字符的凭据只收到 24 字符）。一律让用户写成文件，脚本读文件。`preflight.py` 也只回报长度与前缀特征，**绝不回显密钥本体**。

### bsk 安装

1. 安装 browser-skill CLI
2. 在 Chrome 里安装 BrowserSkill 扩展并启用
3. **在该 Chrome 登录 [xiaohongshu.com](https://www.xiaohongshu.com)**（bsk 复用你的登录态，这是它比爬虫可靠的原因）
4. 验证：`bsk status --json` → `browsers connected` 非 0

### 环境变量（依赖不在标准位置时）

`preflight.py` 按 **环境变量 → 标准位置 → PATH** 的顺序查找，脚本内**不含任何写死的路径**：

```bash
export BSK_PATH=/path/to/bsk              # bsk 可执行文件
export AMAP_KEY_FILE=/path/to/amap.key    # 高德 Key 文件
```

Windows PowerShell：

```powershell
[Environment]::SetEnvironmentVariable('AMAP_KEY_FILE', 'D:\keys\amap.key', 'User')
```

### 图片闸门阈值

阈值集中在 `scripts/imgverify.py` 顶部的 `TH` 字典，也可用 `--config` 传入覆盖：

```json
{
  "min_side": 480,
  "min_bytes": 20480,
  "ratio_lo": 0.5,
  "ratio_hi": 2.0,
  "max_text_ratio": 0.35
}
```

---

## 示例

### 1. 环境体检

```bash
python scripts/preflight.py --quick
```

### 2. 图片闸门判定（三档对比）

仓库内 `examples/` 提供了一份可直接运行的候选清单，以及三档的真实输出：

```bash
# B 档（默认）：只跑 ①②
python scripts/imgverify.py --cand examples/candidates.sample.json

# C 档：五道全跑
python scripts/imgverify.py --cand examples/candidates.sample.json --gates full

# 自选（如只跑 ①④⑤）
python scripts/imgverify.py --cand examples/candidates.sample.json --gates 1245
```

同一组 4 个候选，两档结果**不同**（这正是取舍所在）：

**轻量档 → 采用第 3 个（攻略信息图会通过）**

```
[1] ❌ 淘汰  tiny.jpg          ❌ ① 字节 3200 < 20480（疑似防盗链占位图）
[2] ❌ 淘汰  avatar.jpg        ❌ ① 是头像元素
[3] ✅ 通过  infographic.jpg   ✅ ① 有效  ✅ ② 1200x1600 (0.75)
采用第 3 个候选   落盘应为: photos/d09-sight.webp
```

**完整档 → 采用第 4 个（真风景图）**

```
[3] ❌ 淘汰  infographic.jpg   ❌ ③ 疑似攻略信息图/截图（邻近文案命中 攻略/清单/价格表）
[4] ✅ 通过  real-sight.jpg    ✅ ① ② ③ ④ 命中 西湖 ⑤ photos/d09-sight.webp
采用第 4 个候选   落盘应为: photos/d09-sight.webp
```

> 完整输出见 [`examples/verdict.light.sample.txt`](examples/verdict.light.sample.txt)
> 与 [`examples/verdict.full.sample.txt`](examples/verdict.full.sample.txt)。

### 3. 取结构化候选（在页面上下文里执行）

❌ 不要用正则抓 CDN URL 后盲取第 N 张 —— 抓到头像和信息图是必然，不是意外。

✅ 改为取结构化候选：

```javascript
Array.from(document.querySelectorAll('.note-slider img, .swiper-slide img, #noteContainer img'))
  .filter(i => i.naturalWidth > 0)
  .map(i => ({
    src: i.currentSrc || i.src,
    w: i.naturalWidth,
    h: i.naturalHeight,
    alt: i.alt || '',
    near: (i.closest('figure,div,section')?.innerText || '').slice(0, 150),
    is_avatar: !!i.closest('[class*=avatar], [class*=Avatar]')
  }))
```

`near` 是**图片旁边的文案**，也就是语义证据 —— 比看 URL 可靠得多。

### 4. 图片落盘（命名与元数据互锁）

```bash
python scripts/imgcrop.py --src raw/d09.jpg --day 9 --cat sight
# → photos/d09-sight.webp   （裁 3:4 → 480×640 → WebP q78）
```

命名由 `(day, cat)` 唯一决定，写盘前先断言 —— 从根上杜绝"景点图存成 food 名"这类错位。

用户手选图通道（命名约定驱动，零配置）：

```bash
python scripts/imgcrop.py --replace ./图片替换 --photos photos/ --backup backup/photos
# D10-景点-某地标.png  → d10-sight.webp
```

---

## 设计取舍

这些是本项目刻意做的选择，不是遗漏：

| 取舍 | 理由 |
|---|---|
| **不做部署/上线** | 交付物是本地单文件 HTML。不需要域名、服务器、任何部署凭据 |
| **图片默认为轻量档** | 图片是加分项，不是核心交付物。花在图上的时间若开始挤压核验工作，就是做过头了 |
| **OSRM 只用作里程交叉** | 其时长模型对中国限速不准（285 km 给 3.5 h ≈ 86 km/h，山区高速不可能） |
| **无真实数据的图形不画** | 装饰性图形不许画得像数据。没有实测拟合的曲线要么标注「示意」要么不做 |
| **同季节素材不足时不凑** | 跨季节套用攻略（10 月出发参考 7 月草原攻略）会得到完全错误的景观与路况判断 |

---

## 常见问题

<details>
<summary><b>调用高德 API 返回 <code>INVALID_USER_KEY</code>，但 Key 是刚申请的？</b></summary>

Key 的服务平台选错了。必须选「**Web 服务**」，而不是「Web端(JS API)」。这是最高频的坑——报错信息会让人以为是 Key 本身无效。
</details>

<details>
<summary><b>为什么要问出发地到"区/县级"？我只说城市不行吗？</b></summary>

会出大问题的量级。实际案例中，某"市"与其下辖县相距 100 km 且在主线上，只问到市级会导致**单段误差 198 km** —— 足以改变第一天的落脚点选择。
</details>

<details>
<summary><b>图片抓取总是抓到头像和攻略长图？</b></summary>

说明你在用"正则抓 CDN URL + 盲取第 N 张"的旧做法。改用 `bsk evaluate` 取结构化候选（含 `naturalWidth`、`is_avatar`、`near` 文案），再跑闸门判定。见[示例 3](#3-取结构化候选在页面上下文里执行)。
</details>

<details>
<summary><b>轻量档把攻略信息图放进去了，是 bug 吗？</b></summary>

不是，这是**写明的取舍**。轻量档只跑闸门 ①②（挡破图与畸形图），不判断语义。需要精确匹配就上 C 档：`--gates full`。
</details>

<details>
<summary><b>必须用高德吗？可以用 Google Maps / OSRM 吗？</b></summary>

高德 REST 是**主口径**，因为它是国内路网数据最准的来源。OSRM 免 Key，作为独立交叉引擎（偏差 >10% 需人工复核）。两者角色不同、不可平权——冲突时以高德为准。
</details>

<details>
<summary><b>字体子集化后，新改的文字变成了宋体/衬线体？</b></summary>

顺序反了。**必须：先改完所有文案 → 最后跑子集化脚本。** 如果先跑子集再改文案，新增的字不在子集里，会**静默回退**到系统字体——不报错、无破绽、肉眼极难发现。
</details>

<details>
<summary><b>Cookie / 登录态会失效吗？</b></summary>

bsk 复用你本机 Chrome 的真实登录态，所以比爬虫稳定，但登录态本身仍会过期。`bsk status --json` 可检查 `browsers connected` 是否非 0。
</details>

---

## 贡献指南

欢迎 Issue 与 PR。

### 报告问题

请使用 [Issue 模板](../../issues/new/choose)，并尽量附上：

- 复现命令与完整输出
- 你的环境（OS / Python 版本 / 是否装了 bsk）
- 若是里程或数据问题，请给**具体段落**与期望值

### 提交代码

```bash
git checkout -b feat/your-feature
# ... 修改 ...
git commit -m "feat(imgverify): 支持按 cat 自定义词族"
git push origin feat/your-feature
```

**提交信息规范**（[Conventional Commits](https://www.conventionalcommits.org/)）：

| 前缀 | 用途 |
|---|---|
| `feat:` | 新功能 |
| `fix:` | 修 bug |
| `docs:` | 仅文档 |
| `refactor:` | 重构（不改行为） |
| `chore:` | 构建/工具链 |

示例：`fix(imgcrop): 天数补零到两位，修复 d9 与 d09 不匹配`

### 开发约定

- **脚本保持零第三方依赖**（除 Pillow / fontTools 这类明确的图片与字体库）
- **脚本内不得写死绝对路径** —— 用环境变量 → 标准位置 → PATH 三级查找
- **修改 `SKILL.md` 后，请确认没有引入「面向作者的元说明」**：判断标准是 *这句话删掉后，Agent 的操作会不会变？* 不会变的就是元说明，属于 README 而非 SKILL.md
- **改动阈值或闸门逻辑时，请同步更新 `examples/` 下的示例输出**

---

## 许可证

本项目采用 [MIT License](LICENSE)。你可以自由使用、修改、分发，包括商业用途，只需保留版权声明。

### 第三方依赖许可

| 依赖 | 许可 |
|---|---|
| Pillow | HPND |
| fontTools | MIT |
| 高德开放平台 API | 遵守[高德开放平台服务条款](https://lbs.amap.com/) |

### 免责声明

本工具生成的路书为**辅助参考**。里程、时长、费用来自第三方地图 API，可能存在误差；开放时间、票价、桩况等**易变信息**请以官方渠道为准。请自行核实后出行。

---

<div align="center">
<sub>If this project helped you, consider giving it a ⭐</sub>
</div>
