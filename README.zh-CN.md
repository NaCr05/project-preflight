# Project Preflight

[English](README.md) | **简体中文**

> 面向 AI 编码智能体、带阶段闸门的编码前工作流编排器。

`project-preflight` 将一个模糊的软件想法或尚未完成规划的项目，推进为一份有证据支撑的实施交接。它会识别项目当前所处阶段，给出下一条需要你显式调用的规划 Skill 指令，在你返回后校验产物，跨会话保存进度，并在项目被证明已经准备就绪之前阻止生产代码开发。

## 工作流程

```mermaid
flowchart LR
    A["模糊想法"] --> P1["$project-preflight"]
    P1 -->|"显式 Handoff"| B["$grill-me"]
    B -->|"返回恢复"| P2["$project-preflight<br/>Gate 1"]
    P2 --> C["$wayfinder → 返回"]
    C --> D["$to-spec → 返回"]
    D --> E["$to-tickets → 返回"]
    E --> F["READY_FOR_IMPLEMENTATION"]
```

Project Preflight 每次只推进一个有证据支持的 Gate。每个专项阶段都是一个清晰可见的 Handoff：Project Preflight 输出准确的 `$skill-name` 指令后停止；你显式调用该 Skill，等持久化产物形成后，再调用 `$project-preflight` 进行 Gate 评估。终点是可靠的实施交接，而不是已经写完的产品代码。

**[查看完整中文流程指南 →](docs/workflow.zh-CN.md)**

## 为什么需要它

单独使用规划 Skill 很有帮助，但项目依然可能跳过阶段、在会话之间丢失状态、在多份文档中重复维护决策，或者误把“已经有 Spec”当成“已经可以开发”。Project Preflight 补齐了这条生命周期：

- 阶段识别与断点恢复；
- 显式由用户调用的 Handoff，而不是隐藏的 Skill 串联；
- 基于证据的 Gate；
- 不绑定具体 Issue Tracker 的产物指针；
- 范围与实施防护规则；
- 核心技术假设失效后的回退机制；
- 精确的 `READY_FOR_IMPLEMENTATION` 实施交接。

它负责编排，而不是替代：

- 使用 `grill-me` 完成需求探索；
- 使用 `wayfinder` 解决尚未完成的关键决策；
- 使用 `to-spec` 综合生成项目规格；
- 使用 `to-tickets` 生成 Tracer Bullet Tickets。

这些上游 Skill 不随本仓库打包，并继续保留各自的行为与许可证。

## 本地安装

将 `skills/project-preflight` 复制到 Codex Skills 目录，并保持目录名为 `project-preflight`。例如放在：

```text
<CODEX_HOME>/skills/project-preflight
```

四个上游 Skill 需要单独安装，并且必须出现在当前活动 Skill 目录中。Project Preflight 会在输出 Handoff 前检查当前阶段依赖；如果用户无法显式调用所需 Skill，它会停止推进并给出明确的阻塞原因。

## 使用方式

从一个想法开始：

```text
使用 $project-preflight。我想做一个开源 Agent，用来……
```

稍后恢复：

```text
使用 $project-preflight 恢复这个项目的 preflight。
```

审查已有规划：

```text
使用 $project-preflight 判断这份 Spec 和 Tickets 是否已经可以进入实施。
```

Skill 会在目标项目中维护一个唯一的规范状态文件：

```text
.project/preflight.md
```

该文件记录当前阶段、Gate 状态、阻塞项，以及 Idea、Decision Map、Spec 和 Tickets 的规范产物指针，但不会复制这些产物的正文。

Project Preflight 通过内置 State lifecycle module 修改该文件。候选状态会先完成验证，再原子替换旧文件，因此失败操作不会破坏上一份有效状态。远程指针会给出明确警告；GitHub Issue 指针还可以使用 `--check-remote` 做只读检查。

## 就绪 Gate

1. **问题清晰度** —— 用户、问题、价值、输入、输出、MVP、Non-Goals 和可衡量的成功标准都已明确。
2. **决策就绪度** —— 可能推翻架构的未知项与可行性风险已经解决，或已明确证明不会阻塞后续工作。
3. **规格就绪度** —— 范围、行为、测试决策和开放问题足够明确，可以判断任何功能是否属于当前项目范围。
4. **执行就绪度** —— Tickets 是纵向、可测试、依赖正确且不超出范围的切片，并包含第一条 Tracer Bullet。

只有 Gate 4 通过后，项目才能进入 `READY_FOR_IMPLEMENTATION`。

## 仓库结构

- `skills/project-preflight/` —— 可分发的 Skill。
- `docs/product-spec.md` —— v0.2 产品范围和成功标准。
- `docs/workflow.zh-CN.md` —— 完整用户旅程、Gate、产物、暂停点和回退规则。
- `docs/decisions/` —— 仅追加演进的架构决策记录。
- `tests/` —— 确定性的状态契约测试。
- `evals/` —— 机器可读行为案例、隔离 Fixture、可重放评分和带日期的前向评测证据。

## 验证修改

验证器仅使用 Python 标准库：

```text
python -m unittest discover -s tests -v
python skills/project-preflight/scripts/validate_preflight.py tests/fixtures/valid-idea.md --repo-root tests/fixtures
python skills/project-preflight/scripts/preflight_state.py template --check skills/project-preflight/assets/preflight-template.md
python evals/run_behavior_evals.py list
```

使用 Skill Creator 的 `quick_validate.py` 检查 `skills/project-preflight`，可以验证 Skill 的打包元数据。

## 当前状态

本仓库现在采用显式 Handoff orchestration 和经过验证的 State lifecycle interface。本地 Markdown 仍是默认模式；inline 与本地指针会确定性检查，GitHub Issue 已有真实只读 adapter，其他远程 URL 不会再被静默视为已验证。上游发布行为和自动依赖安装仍保持独立。

## 许可证

MIT，详见 `LICENSE`。
