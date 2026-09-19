# travel-roadbook-pipeline 公开发布说明

> 本文档记录本仓库从零到公开的完整发布流程、决策依据与后续维护规范。
> 发布对象：https://github.com/Wexexortexort/travel-roadbook-pipeline

---

## 一、发布结果速览

| 项目 | 值 |
|---|---|
| 仓库地址 | https://github.com/Wexexortexort/travel-roadbook-pipeline |
| 可见性 | Public（公开） |
| 许可证 | MIT |
| 默认分支 | `main` |
| 文件数 | 16 |
| 总大小 | 约 132 KB |
| Topics | `travel` `roadbook` `itinerary` `self-driving` `workbuddy-skill` `ai-agent` `python` `china-travel` `amap` `html-generator` |
| README | 10 382 字符 / 428 行 / 6 徽章 / 10 个二级章节 / 7 个折叠块 |

---

## 二、发布前决策（四项，均已确认）

### 1. 仓库名：`travel-roadbook-pipeline`

调研过 5 个候选，最终选定本名的原因：

| 候选名 | 结论 |
|---|---|
| `roadbook-skill` | ❌ 已被 `zuo-wentao/Amap-Roadbook-Skill` 占用，且语义高度重叠，易被误认为是同一项目的 fork |
| `roadbook-kit` | ❌ 与 `coral603/travel-roadbook-kit` 高度近似 |
| `travel-roadbook-pipeline` | ✅ **选定** —— 名字即描述（travel + roadbook + pipeline），与技能目录名一致，零歧义 |
| `html-roadbook-generator` | 偏窄，丢掉了「多源交叉验证」这一核心能力 |
| `roadbook-verify` | 偏窄，只体现了校验环节 |

**命名经验**：`<领域>-<产物>-<形态>` 三段式，且**优先与本地技能目录同名**，可避免后续「仓库名 vs 技能名」两套称呼分裂。

### 2. 许可证：MIT

- 与已装的第三方依赖许可全部兼容（技能本身零第三方依赖，仅用 Python 标准库）
- 对 Skill 类项目，MIT 是生态惯例（宽松、无传染性，便于他人直接复制进自己的技能目录）
- 已在 `LICENSE` 中写明 `Copyright (c) 2026 Wexexortexort`
- 已在 README `## 许可证` 章节补充**第三方依赖许可**与**免责声明**两段

### 3. README 语言：中文为主 + 英文摘要

- 主体中文（目标使用者是中文路书场景）
- `## 项目简介` 开头插入 `> **English Summary**` 引用块，供国际用户 5 秒判断项目是否相关
- 章节标题保留中文，锚点目录用中文（GitHub 中文锚点渲染正常）

### 4. 附带文件：加示例与截图目录

- 建了 `examples/`，其中 **`verdict.light.sample.txt` 与 `verdict.full.sample.txt` 是真实脚本输出，不是手写样例**
- 用同一组 4 个候选输入，跑 `light` / `full` / `1245` 三档，得到三份不同结论 —— 直观展示「分级闸门」的取舍差异
- 未放截图（本技能是 CLI + Markdown 流程，无可截图 UI），改为在 README 中直接贴真实终端输出

---

## 三、文件结构组织

```
travel-roadbook-pipeline-release/
├── README.md                          ← 10 382 字符，6 徽章 + 中文目录 + 10 章节
├── LICENSE                            ← MIT
├── CHANGELOG.md                       ← Keep a Changelog 格式
├── CONTRIBUTING.md                    ← 含「编码约定」与「提交规范」
├── .gitignore                         ← 五段（含密钥隔离）
├── SKILL.md                           ← 技能主文档（41 906 B）
├── scripts/
│   ├── preflight.py                   ← 环境体检（13 710 B）
│   ├── imgverify.py                   ← 图片五道闸门校验（16 044 B）
│   └── imgcrop.py                     ← 裁切 + 手选图替换（9 181 B）
├── references/
│   ├── roadbook-spec-v1.0.md          ← 路书制作规范（14 070 B）
│   └── image-validation.md            ← 图片校验细则（8 729 B）
├── examples/
│   ├── candidates.sample.json         ← 4 个候选输入
│   ├── verdict.light.sample.txt       ← light 档真实输出
│   └── verdict.full.sample.txt        ← full 档真实输出
└── .github/
    └── ISSUE_TEMPLATE/
        ├── bug_report.md
        └── feature_request.md
```

**结构设计原则：根目录只放「元文件」，内容按职能分目录。**

- 根目录：`README` / `LICENSE` / `CHANGELOG` / `CONTRIBUTING` / `.gitignore` / `SKILL.md` —— 全部是「关于这个项目」的文件
- `scripts/` `references/` `examples/` —— 全部是「项目的产出物」，且**与 WorkBuddy 技能的目录约定完全一致**（技能加载器要求 `scripts/` 与 `references/` 平铺在技能根目录）
- `.github/` —— 平台约定位置

这样做的收益：**仓库克隆下来直接就是可用的技能目录**，使用者无需二次整理结构。

---

## 四、发布前自检（31 项断言）

发布脚本共 7 组检查，全部通过（`通过 31 / 失败 0`）：

| # | 检查组 | 覆盖内容 |
|---|---|---|
| 1 | 文件清单 | 16 文件 / 134 977 B，与文档清单等式对齐 |
| 2 | **密钥泄露扫描** | 对比 `gh.key` / `amap.key` **真实值全文包含**；正则扫 `gh[ps]_`、`github_pat_`、32 位 hex、`sk-` |
| 3 | **隐私扫描** | 17 个关键词（德化 / 泉州 / 30448 / 小鹏 / 莫高窟 / 黑独山 / 襄阳 / 青海湖 / 水上雅丹 / 大柴旦 / 鱼卡 / 冷湖 / 张掖 / 敦煌 / 祁连 / `C:\Users` / `E:\WorkBuddySpace`）逐行扫行号 |
| 4 | 元说明扫描 | `随 skill` `分享给他人` `接收方` `可移植` `随包` `自包含` `本 skill` 零命中 |
| 5 | **脚本可执行性** | 真实运行 `imgverify --cand examples/candidates.sample.json`；`preflight --quick --json`；三个脚本 `--help` |
| 6 | 文档完整性 | README 八个必备章节 + 英文摘要 + 徽章 + 折叠块；相对链接存在性 |
| 7 | 必需文件齐备 | `README` / `LICENSE` / `CHANGELOG` / `CONTRIBUTING` / `SKILL.md` / `.gitignore` 存在，LICENSE 为 MIT |

**本轮自检发现并修正的 3 个「检查器自身的 bug」**（值得记录，因为都是假阳性）：

1. **`amap.key` 误报为隐私** —— 它同时是**密钥文件名**和**文档里公开的推荐路径**（`~/.workbuddy/keys/amap.key`）。修正：把它从隐私词表移除，改为在密钥扫描里用「真实值全文比对」判定（这才是唯一可靠的判据）
2. **32 位 hex 正则误伤** —— `[0-9a-f]{32}` 没有词边界，会命中「40 位 sha 的前 32 位」等无关串。修正：加 `(?<![0-9a-zA-Z])` / `(?![0-9a-zA-Z])` 前后视断言
3. **`../../issues/new/choose` 误报为失效链接** —— 这是 GitHub 的仓库外相对链接，指向仓库的 Issues 页而非文件。修正：以 `../` 开头的链接跳过文件存在性检查

> **教训**：自检脚本的假阳性比漏检更危险 —— 它会训练使用者忽略告警。规则是：**每一条告警都必须能追溯到具体的、真实的风险，否则就是检查器写错了**。

---

## 五、发布步骤（可复用）

### 前提

- `gh.key` 为 GitHub Personal Access Token，scope 需含 `repo`
- 工作目录 `.routetools/` 存放凭据，**该目录不进版本控制**

### 为什么走 REST API 而不是 `git push`

沙箱环境代理会拦截 `git` 的 HTTPS CONNECT，`git push` 会失败。因此本项目的既定发布通道是 **GitHub Contents API**：

```
PUT /repos/{owner}/{repo}/contents/{path}
```

每文件一次请求，`content` 为 base64 编码的文件内容。

### 四步流程

```
① 建仓     POST /user/repos            body: name / description / private=false / auto_init=false
② 打标签   PUT  /repos/{o}/{r}/topics   body: {"names": [...]}
③ 推文件   PUT  /repos/{o}/{r}/contents/{path}   每文件一次，间隔 0.35s
④ 校验     GET  /repos/{o}/{r}          + /git/trees/main?recursive=1
```

**关键细节：**

- `auto_init: false` —— 不自动建 README，否则第一次推 README 会因「文件已存在」返回 409，需要在 body 里补 `sha`
- **每文件独立 commit**，不依赖本地 git 工作区，天然规避代理问题
- 请求间隔 0.35 s，避开 secondary rate limit
- 特殊字符路径（如 `.github/ISSUE_TEMPLATE/…`）直接放进 URL path 即可，无需额外编码
- 完整脚本：`.routetools/_publish.py`（可重复执行；仓库已存在时自动跳过建仓）

### 发布后校验清单

| 检查项 | 命令 / 方式 | 本次结果 |
|---|---|---|
| 仓库可见性 | `GET /repos/{o}/{r}` → `private` | `false` ✅ |
| 许可证识别 | → `license.spdx_id` | `MIT` ✅ |
| 分支 | → `default_branch` | `main` ✅ |
| 文件齐全 | `GET /git/trees/main?recursive=1` | 16 个 blob ✅ |
| README 渲染 | 拉取 raw 后统计标题 / 徽章 / details | 10 章 / 6 徽章 / 7 折叠 ✅ |

---

## 六、提交信息规范

采用 **Conventional Commits**：

```
<type>(<scope>): <subject>
```

| type | 用途 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat(imgverify): 新增 --gates 分级闸门参数` |
| `fix` | 修 bug | `fix(imgverify): 修正 gate5 日期零填充导致的误淘汰` |
| `docs` | 文档 | `docs: 添加 README` |
| `refactor` | 重构（不改行为） | `refactor(skill): 清除面向作者的元说明` |
| `chore` | 杂务 | `chore: 初始化 scripts/preflight.py` |
| `test` | 测试 | `test: 补充闸门分级回归用例` |

**首次提交的特殊处理**：由于走 Contents API 逐文件推送，每个文件自动生成一条 commit。本次使用的 message 规律是：

- `README.md` → `docs: 添加 README`
- 其余 → `chore: 初始化 <path>`

如需**单条 commit 的干净历史**，改用 Git Data API 的 blob → tree → commit → ref 四步链（`POST /git/blobs` → `POST /git/trees` → `POST /git/commits` → `POST /git/refs`），可一次提交全部文件。

---

## 七、发布注意事项

### 🔴 最高优先级：密钥与隐私

本项目已在发布前做了三重隔离：

1. **`.gitignore` 显式屏蔽** `*.key`、`amap.key`、`gh.key`、`.env`
2. **发布前全文扫描**：拿真实密钥值在全部 16 个文件里做子串比对（这是唯一可靠的方法）
3. **正则兜底**：扫 GitHub Token / PAT / 高德 Key / OpenAI 式密钥四种形态

**红线**：任何情况下都不得把 `.routetools/gh.key`、高德 Key、或含本机绝对路径（`C:\Users\30448`、`E:\WorkBuddySpace`）的内容提交上去。撤销代价远大于发布前多跑一次脚本。

### 🟡 隐私侧：示例数据要脱敏

- `examples/candidates.sample.json` 的 `keywords` 用的是公开地名（西湖），非本次行程地点
- `references/roadbook-spec-v1.0.md` 中的行程示例数字已全部替换为中性占位（`1 234 km` / `¥1 234` / `3/15 · 周六` / `K123+000–K124+000`）
- **判断标准**：示例数据若指向真实行程，等于公开出行计划

### 🟡 SKILL.md 不写元说明

`SKILL.md` 是给**执行 agent** 的操作指令，不是给**人类读者**的项目介绍。判据：

> **这句话删掉后，agent 的操作会不会变？** 不会变 → 是元说明，属于 README。

已被清理的典型噪音：`## 这个 skill 解决什么`、`✅ 规范已随 skill 打包`、`分享给他人时 / 接收方需要…`、`本 skill 设计为可移植`。

### 🟢 发布后维护

- 版本变更同步更新 `CHANGELOG.md`（Keep a Changelog 格式）
- 功能改动同步更新 README 对应章节
- 收到 Issue 后按 `.github/ISSUE_TEMPLATE/` 的字段要求复现
- 若要发布到 Skill 市场，另需准备 `skill.json` 元数据清单

---

## 八、仓库链接

- **主仓库**：https://github.com/Wexexortexort/travel-roadbook-pipeline
- **Issues**：https://github.com/Wexexortexort/travel-roadbook-pipeline/issues/new/choose
- **本地发布目录**：`E:\WorkBuddySpace\旅行\travel-roadbook-pipeline-release\`
- **本地技能目录**：`C:\Users\30448\.workbuddy\skills\travel-roadbook-pipeline\`

> 后续修改流程：改本地技能目录 → 重新复制到发布目录 → 跑 `.routetools/_prepublish.py` → 跑 `.routetools/_publish.py`（已存在仓库时会自动跳过建仓，直接更新文件）。
