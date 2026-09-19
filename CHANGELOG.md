# Changelog

本项目的所有重要变更记录于此。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [1.0.0] - 2026-09-19

首个公开发布版本。

### Added

- **端到端流水线**：Phase -1（环境预检）→ 0（交互式需求采集）→ 1（路线规划）→
  2（多渠道交叉验证）→ 3（内容规划）→ 4（HTML 生成）→ 5（图片补充与校验）→ 6（交付前自检）
- **`scripts/preflight.py`** — 环境依赖体检，含自包含的缺失指引；路径无关
  （环境变量 → 标准位置 → PATH 三级查找）
- **`scripts/imgverify.py`** — 分级闸门图片校验
  - `light`（默认，闸门 ①②）/ `full`（五道全跑）/ 编号串（如 `1245`）
  - 五道闸门：有效性 / 尺寸合理性 / 素材类型 / 语义一致性 / 命名互锁
- **`scripts/imgcrop.py`** — 3:4 裁切落盘、命名断言、用户手选图替换通道（命名约定驱动，零配置）
- **`references/roadbook-spec-v1.0.md`** — 通用路书制作规范（结构 / 视觉 / 内容三类约束）
- **`references/image-validation.md`** — 图片校验机制的设计说明与调参指南
- **情报时效三筛**：2 年内发布 + 同季节 + 时效分水岭，递进式硬筛
- **单文件零外链 HTML 交付**：不需要部署、服务器或任何账号
- 示例目录 `examples/`：可直接运行的候选清单与三档真实判定输出

### 设计取舍

- 图片默认走**轻量档** —— 图片是加分项，不是核心交付物
- **不含部署/上线步骤** —— 交付物是本地文件
- OSRM **只用作里程交叉**，不作时长口径
- 无真实数据拟合的装饰性图形不绘制

[1.0.0]: https://github.com/Wexexortexort/travel-roadbook-pipeline/releases/tag/v1.0.0
