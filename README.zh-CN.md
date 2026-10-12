# Agent User Learning（AUL）

**从用户告诉 agent 的信息中学习。**

[English](README.md) · [架构](docs/architecture.md) · [事件协议](skills/agent-user-learning/references/protocol.md) · [接入方式](skills/agent-user-learning/references/integration.md)

AUL 保存用户主动分享的兴趣、偏好、目标、习惯和背景。Agent 在执行任务时读取相关上下文，用于安排工作和调整回复；用户纠正时，更新对应记录。

项目提供 Python SDK、CLI 和可安装的 Skill，可以接入 agent 或应用。

例如，用户希望写代码时简短汇报进度，审阅文章时详细说明修改。AUL 分别保存这两种任务的偏好，供 agent 下次执行对应任务时使用。

![AUL 工作流程：读取上下文、完成任务、提取用户事件、校验并更新用户存储](docs/images/aul-workflow.png)

Host 选择场景并提取事件；AUL 校验、保存和选择用户上下文。数据流和写入约定见 [架构说明](docs/architecture.md)。

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

## 快速试用

需要 Python 3.11 或更新版本，在项目目录执行：

```sh
python -m pip install .
python examples/user_learning_demo.py
```

演示使用虚构用户和内存数据库，可离线运行。它展示目标和偏好如何进入上下文、纠正如何替换旧值，以及遗忘后还剩哪些记录。

安装后，在项目目录运行这个 SDK 示例：

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

下一步是完善 agent 和产品的接入方式，评估重复纠正次数、任务完成情况和不相关偏好的使用情况。

## 项目文档

| 文档 | 内容 |
| --- | --- |
| [Architecture](docs/architecture.md) | 生命周期、组件、存储和版本冲突 |
| [Protocol](skills/agent-user-learning/references/protocol.md) | 事件格式、场景、上下文限制和用户控制 |
| [Integration](skills/agent-user-learning/references/integration.md) | Host 接入要求和评估方式 |
| [Contributing](CONTRIBUTING.md) | 开发环境、修改流程、检查和问题复现 |
| [Changelog](CHANGELOG.md) | 原型功能和当前源码改动 |

采用 [MIT 开源许可证](LICENSE)。
