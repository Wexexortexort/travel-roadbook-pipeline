# 贡献指南

感谢你愿意为本项目做贡献。本文说明开发约定与提交规范。

## 目录

- [开发环境](#开发环境)
- [项目结构](#项目结构)
- [编码约定](#编码约定)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [改动清单](#改动清单)

---

## 开发环境

```bash
git clone https://github.com/Wexexortexort/travel-roadbook-pipeline.git
cd travel-roadbook-pipeline

python -m pip install pillow      # 必需
python -m pip install fonttools   # 可选：仅字体子集化需要

python scripts/preflight.py --quick   # 自检
```

---

## 项目结构

```
travel-roadbook-pipeline/
├── SKILL.md                          # 技能主文档（Agent 执行入口）
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
├── scripts/
│   ├── preflight.py                  # 环境依赖体检
│   ├── imgverify.py                  # 分级闸门图片校验
│   └── imgcrop.py                    # 裁切落盘 / 命名断言 / 手选图替换
├── references/
│   ├── roadbook-spec-v1.0.md         # 路书制作规范（结构·视觉·内容）
│   └── image-validation.md           # 图片校验机制设计说明
├── examples/
│   ├── candidates.sample.json        # 可直接运行的候选清单
│   ├── verdict.light.sample.txt      # 轻量档真实输出
│   └── verdict.full.sample.txt       # 完整档真实输出
└── .github/ISSUE_TEMPLATE/
```

---

## 编码约定

### 脚本

- **零第三方依赖优先** —— 除 Pillow（图片）、fontTools（字体）这类明确用途的库外，不引入新依赖
- **不得写死绝对路径** —— 用 `环境变量 → 标准位置 → PATH` 三级查找。参考 `preflight.py` 的 `_cands()` 实现
- **容错模式** —— 逐项 `try`，异常写入报告文件而非依赖 stdout：

  ```python
  rep = []
  def log(m): rep.append(str(m))
  try:
      ...逐项 try...
  except Exception:
      log("FATAL:\n" + traceback.format_exc())
  io.open(RPT, "w", encoding="utf-8").write("\n".join(rep))
  ```

- **不打印密钥** —— 只回报长度与前缀特征
- **中文注释**，面向使用者的输出也用中文

### 文档

- **`SKILL.md` 是给 Agent 执行的操作手册，不是产品介绍。**
  判断标准：**这句话删掉后，Agent 的操作会不会变？** 不会变的就是「元说明」，属于 README 而非 SKILL.md。
  典型噪音：`本 skill 解决什么` / `已随包携带` / `分享给他人时` / `接收方需要…`
- **不要写死具体项目的痕迹** —— 地名、本机路径、个人车型。改用通用表述（`某地标` / `某景区`）；
  但**实证数字应保留**（误差 km 数、比例），它们不含身份信息，是说服力的来源

### 阈值与示例

改动 `imgverify.py` 的 `TH` 阈值或闸门逻辑时，**请同步更新 `examples/` 下的示例输出**，并确认：

```bash
python scripts/imgverify.py --cand examples/candidates.sample.json              # light
python scripts/imgverify.py --cand examples/candidates.sample.json --gates full # full
```

---

## 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

### type

| 前缀 | 用途 |
|---|---|
| `feat` | 新功能 |
| `fix` | 修 bug |
| `docs` | 仅文档变更 |
| `refactor` | 重构（不改变外部行为） |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建流程、依赖、工具链 |

### scope（可选）

`preflight` / `imgverify` / `imgcrop` / `skill` / `spec` / `readme`

### 示例

```
feat(imgverify): 支持按 cat 自定义词族

新增 --cat-hint 参数，允许为不同目的地覆盖默认词族，
高原/海岛/古城的关键词分布差异较大。

Closes #12
```

```
fix(imgcrop): 天数补零到两位

lstrip('Dd') 会剥掉所有 D/d 字符且不补零，
导致 d9-sight.webp 与 d09-sight.webp 不匹配，
好图被误判淘汰。改用正则 + %02d。
```

> 💡 **subject 用祈使句、不加句号、不超过 50 字符**；正文说明「为什么」而非「做了什么」（diff 已经显示做了什么）。

---

## Pull Request 流程

1. Fork 并创建分支：`git checkout -b feat/your-feature`
2. 修改代码，**在本地跑通 `preflight.py` 与相关脚本**
3. 若改动影响输出，更新 `examples/` 与 `CHANGELOG.md`
4. 提交（遵循上面的规范）
5. 发起 PR，说明：
   - 解决了什么问题
   - 改动方式与取舍
   - 你验证过什么（命令 + 结果）

### Review 关注点

| 维度 | 会看什么 |
|---|---|
| **正确性** | 数值口径是否可溯源？是否引入未验证的断言？ |
| **可移植性** | 是否写死了本机路径 / 项目特定信息？ |
| **边界情况** | 缺 Key、缺 bsk、图片全不合格时是否优雅降级？ |
| **文档一致** | `SKILL.md` / `README.md` / `CHANGELOG.md` 是否同步？ |

---

## 改动清单

提交 PR 前自查：

- [ ] 脚本可通过 `python -m py_compile scripts/*.py`
- [ ] 未引入新的第三方依赖（或已说明理由）
- [ ] 脚本内无写死的绝对路径
- [ ] 未提交任何密钥（`.gitignore` 已覆盖 `*.key`）
- [ ] 改动阈值 / 闸门逻辑时，已同步更新 `examples/`
- [ ] `SKILL.md` 未引入「面向作者的元说明」
- [ ] `CHANGELOG.md` 已更新（若为用户可见变更）
- [ ] 提交信息符合 Conventional Commits
