# Agent User Learning（AUL）

**给 Agent 加上用户记忆与学习：记住偏好，下次用上，随纠正更新。**

[English](README.md) · [接入你的项目](INTEGRATE.md) · [架构](docs/architecture.md) · [事件协议](skills/agent-user-learning/references/protocol.md)

用户说：“写代码时回复简短一点。”下次处理代码任务时，agent 就能读到这条偏好。后来用户说：“还是一步一步解释吧。”AUL 更新记录；用户要求忘记时，再将它从有效记忆中移除。

AUL 将用户主动表达的偏好、目标和背景保存在各自的 SQLite 数据库里，为每次任务提供少量相关上下文。项目提供 Python SDK、JSON CLI 和可安装的 Skill。引擎在本地运行，需要 Python 3.11+，没有第三方运行时依赖，也不调用模型。

## 直接让你的 Agent 接入

打开自己的项目，把这段话交给 coding agent：

> 把 AUL（https://github.com/karurukaruru/agent-user-learning）接入这个项目，作为用户记忆与学习层。先读该仓库的 INTEGRATE.md，接到现有 agent 的任务流程中，并用测试验证跨会话保存、相关记忆读取、纠正和遗忘。请实际完成接入，并说明哪些已可用、哪些还需要接线。

[INTEGRATE.md](INTEGRATE.md) 提供具体接入任务：从哪里连接、如何安装、调用哪些接口，以及怎样验证结果。

**目前已有：**存储、按场景读取、证据追溯、纠正和遗忘。宿主需要连接任务流程，并从用户消息提取结构化事件；还没有提取器时，可以先接上明确的“记住”命令。AUL 负责用户记忆，可以与现有文档检索和聊天历史一起使用。

## 跑通完整流程

需要 Git 和 Python 3.11+，在自己的 Python 环境中运行：

```sh
git clone https://github.com/karurukaruru/agent-user-learning.git
cd agent-user-learning
python -m pip install .
python examples/agent_integration.py
```

```text
1. Before learning: Review this patch | reply style: default
2. Next session: Review this patch | reply style: Use short replies.
3. Different task: Review this draft | reply style: default
4. After correction: Review this patch | reply style: Explain step by step.
5. After forgetting: Review this patch | reply style: default
```

示例会关闭并重新打开真实的 SQLite 数据库，把上下文传入回复函数，结束后清理临时数据。回复函数是确定性的演示实现，不需要 API Key。接入时将 `demo_respond` 替换为现有 agent 调用，并将用户上下文作为低优先级数据传入。见 [完整示例源码](examples/agent_integration.py)。

## 运行流程

```text
[用户任务]
  -> Host：确定用户 + 选择场景
  -> AUL：读取该用户的 SQLite 事件
  -> 重放 + 过滤过期证据 + 选择相关记录
  -> context()：用户理解 + 帮助方式 + 版本
  -> Agent：当前请求 + 有长度限制的用户上下文
  -> 执行任务 + 回复

[用户表达 / 纠正 / 针对具体行为的反馈]
  -> Host：提取结构化事件 + 保留来源 ID
  -> AUL observe(event, expected_version)
       |-- 校验通过 + 版本一致 -> 写入 SQLite -> 下次读取生效
       |-- 相同事件重试 ------> 不重复写入
       |-- 版本冲突 ----------> 重新读取 + 重新判断提案
       `-- 事件无效 ----------> 修正输入

[用户控制]
  -> inspect / explain -> 查看记录与支持证据
  -> correction ------> 新的明确事件 -> 更新上下文
  -> forget_rule -----> 删除该项历史与反馈 -> 重新推导
```

Host 选择场景并提取事件；AUL 校验、保存和选择用户上下文。保存的上下文作为低优先级用户数据使用，不授予操作权限。组件关系和写入约定见 [架构说明](docs/architecture.md)，也可查看 [图片版流程图](docs/images/aul-workflow.png)。

## 使用场景

- Coding agent：保存解释方式、代码审查和进度汇报偏好。
- 写作与学习工具：根据相关目标、已有经验和示例偏好安排内容。
- 消息应用：为回复提供长度、格式等偏好，并根据用户纠正更新。

## 两个核心部分

| 部分 | 记录什么 | 用途 |
| --- | --- | --- |
| 用户理解 | 明确分享的资料、兴趣、喜好、目标、习惯、限制、临时状态 | 理解用户的需求和背景 |
| 帮助方式 | 回答长度、例子形式、解释顺序、工作流程等偏好 | 调整 agent 的具体行为 |

每条记录保留证据和来源，用户可以纠正或遗忘。Agent 在当前任务中读取相关记录，由接入方将它们用于回复或执行。

## 使用 Python SDK

完成上述安装后，在项目目录运行这个 SDK 示例：

```python
from agent_user_learning import UserLearner

with UserLearner("../aul-demo.db", "demo-user") as learner:
    learner.observe({
        "event_id": "extract:user-message-42:goal",
        "source_id": "user-message-42",
        "session_id": "session-7",
        "kind": "attribute",
        "scope": "writing:blog",
        "key": "goals.finish-draft",
        "value": "Wants to finish a first draft.",
        "signal": "explicit",
        "evidence": "User says they want to finish a first draft."
    }, expected_version=learner.version)
    context = learner.context(["writing", "writing:blog"])
    print(context["user"]["goals"])
```

示例把虚构目标写入项目目录旁的 `aul-demo.db`。CLI 可以读取同一份记录：

```sh
aul --db ../aul-demo.db --user-id demo-user context --scope writing:blog
aul --db ../aul-demo.db --user-id demo-user inspect
aul --db ../aul-demo.db --user-id demo-user explain --kind attribute --rule-id 'writing:blog|goals.finish-draft'
```

真实用户的数据库应放在仓库外的私有目录，每个用户单独保存，并预先创建父目录。

## 接入 agent

Skill 可复制到 Codex、Claude Code、OpenCode 使用的目录，安装位置见 [英文说明](README.md#use-as-a-skill)。主机需要在任务前读取上下文，在交互后写入学习事件；复制 Skill 会提供说明和运行时，具体调用流程仍需接入。详见 [接入方式](skills/agent-user-learning/references/integration.md)。

## 学习规则

- 明确表达或纠正的事件写入后生效；推测的兴趣、习惯等需要两个不同会话、两个独立来源的重复证据。
- 身份和限制只接受明确的用户证据，不从几次聊天推断人格或敏感身份。
- 当前状态必须带有效期；临时忙碌不会自动变成永久特点。
- 场景标签由接入方选择；更具体场景可覆盖一般偏好。
- 能查看、解释、纠正和遗忘；忘记一项喜好会删除同场景该项目喜欢／不喜欢的历史，避免旧值恢复。
- 以用户为单位隔离数据库；保存简短证据和来源，不保存整段对话。

当前是 **0.1.0 本地原型**，使用 Python 标准库和 SQLite。AUL 处理结构化事件；接入方负责从消息提取事件、选择任务场景和调用 agent，并管理身份验证、存储权限和备份删除。数据库使用 schema 2，暂未提供早期版本的迁移工具。

[接入示例](examples/agent_integration.py)及其测试已验证确定性回复函数中的调用流程。各框架的专用适配器和真实交互评估仍需继续完善，包括重复纠正次数、任务完成情况和不相关偏好的使用情况。

## 项目文档

| 文档 | 内容 |
| --- | --- |
| [接入任务书](INTEGRATE.md) | 交给 coding agent，完成实际接入与验收 |
| [可运行示例](examples/agent_integration.py) | 跨会话保存、回复函数、场景读取、纠正和遗忘 |
| [Architecture](docs/architecture.md) | 生命周期、组件、存储和版本冲突 |
| [Protocol](skills/agent-user-learning/references/protocol.md) | 事件格式、场景、上下文限制和用户控制 |
| [Integration](skills/agent-user-learning/references/integration.md) | Host 接入要求和评估方式 |
| [Contributing](CONTRIBUTING.md) | 开发环境、修改流程、检查和问题复现 |
| [Changelog](CHANGELOG.md) | 原型功能和当前源码改动 |

采用 [MIT 开源许可证](LICENSE)。
