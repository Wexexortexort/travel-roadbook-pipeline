<div align="center">

# 路书生成器

**把一句话目的地，变成一份可核实、图文匹配、可打印的 HTML 路书**

[![License: MIT](https://img.shields.io/badge/License-MIT-2ea44f.svg?style=flat-square)](LICENSE)
[![Agent Skill](https://img.shields.io/badge/Works%20with-Claude%20Code%20%7C%20Codex%20%7C%20Cursor%20%7C%20WorkBuddy-4B6BFB.svg?style=flat-square)](#安装)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](#环境要求)
[![Data](https://img.shields.io/badge/data-AMap%20REST%20%2B%20RedNote-FF5A5F.svg?style=flat-square)](#为什么比其他做法更可靠)
[![Dependencies](https://img.shields.io/badge/dependencies-Pillow%20%7C%20fontTools%20(optional)-2496ED.svg?style=flat-square)](#环境要求)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](#贡献指南)

一个端到端的 **Agent 技能包**：从需求采集、路线规划、多源交叉验证，到生成零外链的单文件 HTML 路书。

[为什么更可靠](#为什么比其他做法更可靠) · [功能特性](#功能特性) · [安装](#安装) · [快速开始](#快速开始) · [配置](#配置说明) · [示例](#示例) · [常见问题](#常见问题) · [贡献](#贡献指南) · [许可证](#许可证)

</div>

---

## 项目简介

**English Summary**

> An end-to-end agent skill that turns a one-line travel request into a verifiable, print-ready
> single-file HTML roadbook. Instead of relying on stale model recall, it grounds every number in
> **queried sources**: **AMap REST** for route calculation (mileage, duration, tolls), and
> **Xiaohongshu (RedNote)** search for first-hand on-the-ground intel — filtered by recency and season.
> Gated image validation keeps photos honest, with a hard rule that **every number must be traceable
> to a source**.

### 为什么比其他做法更可靠

普通做法是**让模型凭记忆写**——训练数据里那些攻略可能已经过时好几年，路况、补能设施、景区规则全变了。本项目把关键信息改成**现查现用**：

| 维度 | 普通做法 | 本项目的做法 |
|---|---|---|
| **路线与里程** | 模型凭印象估，或抄几年前的攻略数字 | 调用**高德 REST 路线计算** —— 路网数据最新最全的来源之一，逐段返回里程、预计时长与过路费 |
| **在地情报** | 用搜索引擎找攻略，**结果不知道是哪一年写的** | **自动在小红书检索真实笔记** —— 一手实拍与实地反馈，比二手转载的搜索摘要鲜活得多 |
| **时效性** | 热门攻略常年霸榜，越热越可能过期 | 递进式硬筛：**只采信 2 年内**发布的笔记，再找「时效分水岭」（新路通车 / 充电桩投运 / 景区改制），分水岭之前的信息**整体作废** |
| **季节性** | 7 月的草原攻略被拿去规划 10 月行程，景观与路况全错 | **只采信与本次行程同季节**的笔记 —— 判定看客观条件（气温带 / 昼夜长度 / 雨季 / 结冰期），**不看月份数字** |

> 🔎 一句话总结：**把「模型回忆」换成「现查现用 + 时效过滤」。**
> 高德负责「路怎么走、多远、多久」，小红书负责「到了那边现在是什么样」。

> ⚠️ **关于"实时"的说明**：高德路线 API 返回的是**查询时点的路线计算结果**，
> **不是实时路况**。用 `strategy=0`（速度优先）时更明确不含拥堵规避。
> 里程/时长/收费均为**估算值**；需要实时拥堵、施工、封路信息时，
> 本项目要求引用**交通状态字段或官方交通源**（省交通厅 / 12328 / 景区官微），
> 不会把一次路线查询包装成"实时路况"。详见 [SKILL.md §2.1](SKILL.md)。

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

### 🗺 路线与数据（高德 REST 路线计算）

- **逐段里程核验**：以高德 REST `/v3/direction/driving?strategy=0` 为**主口径**，取查询时点返回的里程与预计时长；OSRM 作独立交叉引擎（只信里程，不信时长——其对中国限速的模型不准）
- **POI 坐标校准**：非城区 POI 先经 `/v3/place/text` 校准坐标，避免景区支线段里程失真
- **落脚点比选三步法**：按**纯驾驶时长**而非里程挑过夜城市，比"最长单日"而非平均值
- **单日疲劳预警**：纯驾驶 > 8 h 的日子单独标出

> 为什么是高德：路网数据最新最全的来源之一。**相比"模型记忆里的数字"，这是实质改进** ——
> 但它返回的是查询时点的**路线估算**，不是实时路况。里程/时长标为「查询时点估算」，
> 施工与封路一律走官方交通源（省交通厅 / 12328 / 景区官微）。
> 想更贴近路况可换 `strategy=10/12`（考虑路况、躲避拥堵），但**换了策略就换了口径**，需全行程重算。

### 📰 小红书情报检索（反过时）

**自动在小红书检索真实笔记**，取一手实拍与实地反馈，代替搜索引擎里年份不明的二手攻略。情报在进入候选池前必须过三道递进硬筛：

1. **只采信 2 年内发布**的笔记（中国路网与补能设施更新周期普遍 1–2 年）
2. **只采信与本次行程同季节**的笔记 —— 判定看客观条件（气温带 / 昼夜长度 / 雨季 / 结冰期），**不看月份数字**；交界月按实况判
3. 再找**时效分水岭**（新路通车、充电桩投运、景区改制等），分水岭之前的信息整体作废

> 同季节素材不足时，**宁可减少情报量，也不跨季节硬凑**。
>
> 普通搜索的问题是**没有时间戳语义** —— 一篇 2021 年的热门攻略会常年排在前面，而它描述的路况可能早已不成立。

### 🖼 分级闸门图片校验

按需选择严格程度，**默认轻量档**（图片是加分项，不是核心交付物）：

| 档 | 适用 | 跑的闸门 |
|---|---|---|
| **A · 不放图** | 不需要 / 行程短 / 时间紧 | — |
| **B · 轻量** ⭐ 默认 | 要图，但不苛求精确匹配 | ① 有效性 ② 尺寸 |
| **C · 完整** | 明确要求"图必须对得上" | ①–⑤ 全部 |

五道闸门：**① 有效性**（破图/防盗链占位图/头像）→ **② 尺寸合理性**（挡长图拼接）→ **③ 素材类型**（挡攻略信息图）→ **④ 语义一致性**（`keywords` 必须命中图片邻近文案）→ **⑤ 命名互锁**（`photos/d{天:02d}-{cat}.webp`）。

> 🔒 **图片是纯图片，不带任何跳转链接** —— 不生成"图片来源"外链区，不给 `<img>` 套 `<a href>`。
> 小红书的笔记链接带**有时效的访问参数**，写进对外页面迟早失效，读者点进去看到"内容不存在"
> 比不放链接更糟。路书是带在手上的离线文档，图片的价值在于看到，不在于点得动。

### 🎯 交互式需求采集

12 项必要信息分三轮递进采集（**先给一版骨架，再指着骨架追问**——用户说不清自己想要什么，但看到具体方案立刻能指出哪里不对）。采集完输出一张「需求卡」作为开工依据。

### 🧩 HTML 生成规范

随包附带一份通用的路书制作规范（`references/roadbook-spec-v1.0.md`），约束结构（五层骨架）、视觉（低饱和双专色、三栈字体、七档响应式）与内容（数据标注格式、置信度分级、禁用词）三类要求。**若你另有自己的规范，以你的为准。**

---

## 安装

### 环境要求

| 依赖 | 必需性 | 说明 |
|---|---|---|
| **Python 3.10+** | 🔴 **必需** | 运行全部构建与校验脚本 |
| **高德 REST Key** | 🟡 建议（**可跳过**） | 免费申请；没有则里程走 OSRM 或由用户提供读数，全部标 ⏳ 待核实 |
| **浏览器自动化工具** | 🟡 建议（**可跳过**） | **任选其一，不锁死实现**：bsk / browser-use / Agent-Browser / Playwright |
| **Pillow** | 🟡 建议（可跳过） | 图片处理（`imgcrop.py`）；不做图则免 |
| **fontTools** | ⚪ 可选 | 仅自托管中文字体子集化时需要 |

> **只有第一档会挡住你。** 高德 Key 与浏览器工具都没有时，技能照常开工 ——
> 走备选方案（OSRM 里程 / 由用户贴攻略链接），只是相关内容会标注 ⏳ 待核实。

### 方式一：作为 Agent 技能安装（推荐）

这是一个标准的 **Agent Skill** —— 只要你的 Agent 支持「读取技能目录下的 `SKILL.md`」这一约定，就能直接使用。安装只需把仓库克隆进它的技能目录：

```bash
git clone https://github.com/Wexexortexort/travel-roadbook-pipeline.git <你的技能目录>/travel-roadbook-pipeline
```

目录名与 `SKILL.md` 的 `name` 字段一致，克隆后即可被直接发现，**无需改名或额外注册**。

各家 Agent 的默认技能目录（供参考，以你所用工具的文档为准）：

<details>
<summary><b>展开查看各 Agent 的技能目录</b></summary>

| Agent | 默认技能目录 | 备注 |
|---|---|---|
| **Claude Code** | `~/.claude/skills/` | 用户级；项目级可放 `<项目>/.claude/skills/` |
| **Codex** | `~/.codex/skills/` | 用户级；亦支持项目级目录 |
| **WorkBuddy** | `~/.workbuddy/skills/` | 用户级；项目级可放 `<项目>/.workbuddy/skills/` |
| **Cursor** | `<项目>/.cursor/skills/` | 以项目级为主 |
| **其他** | 见其文档 | 只要识别 `SKILL.md` 约定即可，本技能未使用任何平台私有字段 |

</details>

> 若你的 Agent 用不同约定（如放在项目内的 `.agent/skills/`），放进去即可 —— `SKILL.md` 的 frontmatter 只用了 `name` / `description` 这类通用字段，**没有平台专有依赖**。

### 方式二：只用脚本，不接入 Agent

三个脚本都是独立 CLI，可以脱离任何 Agent 单独跑：

```bash
git clone https://github.com/Wexexortexort/travel-roadbook-pipeline.git
cd travel-roadbook-pipeline
python -m pip install pillow          # 建议（不做图则免）
python -m pip install fonttools       # 可选
```

### 首次自检（强烈建议）

```bash
python scripts/preflight.py --workdir /path/to/your/roadbook
```

输出：

```
✅ 全部依赖就位        可做全量核验（含高德 Key 与浏览器工具）
🟡 可以开工（降级模式） 只缺「建议项」—— 照常开工、走备选方案，交付时标注未核实项
❌ 缺少必需项          只有这一档真的挡住你
```

缺什么，脚本会直接告诉你怎么补 —— 它的缺失指引是自包含的，不依赖任何上游上下文。

---

## 快速开始

安装完成后，直接对 Agent 说：

```
帮我做一份国庆 7 天川西小环线的路书，从成都出发，2 人轮换开车，纯电车
```

Agent 会按编排链推进：

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

### 高德 Key（可选，免费）

1. 到 [lbs.amap.com](https://lbs.amap.com) 注册并完成**实名认证**（个人开发者即可）
2. 控制台 → 应用管理 → 创建应用 → 添加 Key
3. 🔴 **服务平台必须选「Web 服务」** —— 选成「Web端(JS API)」调 REST 会返回 `INVALID_USER_KEY`，而人会误以为 Key 本身有问题。**这是最高频的坑。**
4. 数字签名**建议不启用**（启用了每次请求要额外算 sig）
5. 存成文件，例如：

```bash
mkdir -p ~/.config/roadbook
echo -n "你的KEY" > ~/.config/roadbook/amap.key
```

> ⚠️ **密钥纪律**：**不要把 Key 贴进对话** —— 对话通道会对疑似密钥做截断/脱敏（实测 40 字符的凭据只收到 24 字符）。一律让用户写成文件，脚本读文件。

**`preflight.py` 的输出默认已脱敏**，可以放心贴进 issue 或截图：

| 内容 | 默认输出 | 加 `--verbose` |
|---|---|---|
| 高德 Key | `已配置（长度 32）` —— **不输出任何字符、哈希或路径** | 同上 + 脱敏路径 |
| 依赖路径 | `已找到` / `<home>\.local\bin\bsk.exe` | 完整脱敏路径 |
| 浏览器工具原始状态 | 不输出 | 脱敏后的前 200 字符 |
| 家目录 | `<home>` 或 `E:\…\尾两层` | 同左 |

输出前还有一道兜底扫描，自动拦截 `xsec_token` / `cookie` / `authorization` / `Bearer` / `api_key` / `secret` / `C:\Users\…` / `/home/…`。

需要排查环境问题时再加 `--verbose`。

### 浏览器自动化工具（可选，任选其一）

技能只要求三项能力：**打开页面 / 取整页 HTML / 在页面上下文执行 JS**，且能复用你的登录态。
**不锁定具体实现**，以下任选其一：

| 工具 | 安装 | 说明 |
|---|---|---|
| **browser-skill (bsk)** ⭐首选 | `npm i -g browser-skill` | 直接复用本机 Chrome 登录态，无需另配 profile，最省事 |
| **browser-use** | `pip install browser-use` | 通用浏览器自动化 agent |
| **Agent-Browser** | `npm i -g agent-browser` | 通用浏览器自动化 CLI |
| **Playwright CLI** | `npm i -g playwright` | 官方框架，需自备持久化 profile |

用 bsk 时额外两步：

1. 在 Chrome 里安装 BrowserSkill 扩展并启用
2. **在该 Chrome 登录 [xiaohongshu.com](https://www.xiaohongshu.com)**（bsk 复用你的登录态，这是它比爬虫可靠的原因）

验证：`bsk status --json` → `browsers connected` 非 0。

> **一个都没有也没关系** —— 让用户直接贴攻略链接或截图即可（`xhs-shared-note-extract` 无需登录就能读正文），只是在地情报会变薄。

### 环境变量（依赖不在标准位置时）

`preflight.py` 按 **环境变量 → 标准位置 → PATH** 的顺序查找，脚本内**不含任何写死的路径**：

```bash
export BROWSER_TOOL_PATH=/path/to/tool     # 浏览器自动化工具（旧名 BSK_PATH 仍兼容）
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

高德 REST 是**主口径**，因为它的路网数据最新最全（这点明显优于模型记忆）。OSRM 免 Key，作为独立交叉引擎（偏差 >10% 需人工复核）。两者角色不同、不可平权——冲突时以高德为准。

但要注意**高德给的是「查询时点的路线估算」，不是实时路况**：里程、时长、收费都是估算值。实时拥堵 / 施工 / 封路请走官方交通源（省交通厅 / 12328 / 景区官微）。
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
