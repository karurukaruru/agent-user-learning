# Agent User Learning (AUL)

**User memory and learning for agents. Remember preferences, use them next time, and learn from corrections.**

[中文说明](README.zh-CN.md) · [Integrate into your project](INTEGRATE.md) · [Architecture](docs/architecture.md) · [Protocol](skills/agent-user-learning/references/protocol.md)

A user says, "Keep coding replies short." On the next coding task, the agent
receives that preference. Later the user says, "Explain step by step instead."
AUL updates it. If the user asks to forget it, it leaves the active memory.

AUL stores user-stated preferences, goals and background in a per-user SQLite
database, then returns a small, relevant context for each task. Use it through
a Python SDK, JSON CLI or portable Skill. The engine runs locally with Python
3.11+, no runtime dependencies and no model calls.

## Ask your agent to integrate AUL

Copy this into your coding agent with your project open:

> Integrate AUL (https://github.com/karurukaruru/agent-user-learning) into this project as its user memory and learning layer. Read INTEGRATE.md in that repository, wire it into our existing agent's turn flow, and verify persistence, relevant recall, correction and forgetting with tests. Implement the integration, and tell me what works and what still needs wiring.

[INTEGRATE.md](INTEGRATE.md) gives the agent a concrete implementation brief:
where to connect, how to install, which APIs to call, and what to verify.

**What you get today:** storage, scoped recall, evidence, corrections and
forgetting. Your host connects the lifecycle and extracts structured events
from user messages. Start with explicit remember commands if you have no
extractor yet. Use AUL for user memory alongside your existing document search
and conversation history.

## Try the complete loop

Requires Git and Python 3.11+. Run in your Python environment:

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

The demo closes and reopens a real SQLite database, passes context to a response
callback, and removes its temporary data when finished. Its responder is a
deterministic stub; no API key is needed. Replace `demo_respond` with your
existing agent call, keeping the user context as lower-priority data.
See the [starter source](examples/agent_integration.py).

## Runtime workflow

```text
[User task]
  -> Host: resolve user + choose scopes
  -> AUL: read per-user SQLite events
  -> Replay + filter expiry + select relevant records
  -> context(): user attributes + behavior rules + version
  -> Agent: current request + bounded user context
  -> Execute task + respond

[User statements / corrections / targeted feedback]
  -> Host: extract structured events + preserve source IDs
  -> AUL observe(event, expected_version)
       |-- Valid + current version -> SQLite commit -> Next context read
       |-- Identical retry -------> No duplicate write
       |-- Version conflict ------> Reread + reassess proposal
       `-- Invalid event ---------> Fix input

[User controls]
  -> inspect / explain -> Records + supporting evidence
  -> correction ------> New explicit event -> Updated context
  -> forget_rule -----> Remove item history + feedback -> Replay
```

The host chooses scopes and extracts events. AUL validates, stores and selects the user context. Stored context is lower-priority user data and grants no permissions. See [Architecture](docs/architecture.md) for the component map and write contract, or open the [illustrated workflow](docs/images/aul-workflow.png).

## Where to use it

- Coding agents: keep preferences for explanations, code review and progress updates.
- Writing and study tools: use relevant goals, experience and preferred examples.
- Messaging apps: supply preferences for reply length and format; update them from user corrections.

## What it learns

| Category | Example | Effect on help |
| --- | --- | --- |
| Profile | User-stated name or experience | Address the user appropriately; choose a suitable starting level |
| Interests, likes, dislikes | Prefers a quiet workspace | Avoid unwanted suggestions in a work context |
| Goals | Finish a first draft | Prioritize the next useful step |
| Habits and constraints | Studies in short sessions; needs accessible formatting | Fit plans to the user's routine and stated needs |
| Current state | Busy today, with an expiry | Adapt this session without making a permanent assumption |
| Help preferences | Short examples; explanation before code | Adjust communication and workflow |

**User attributes** describe the user's background and needs. **Behavior rules** describe how they want help. Each record keeps its source, and the user can correct or forget it. An agent reads a small set of relevant records for the current task.

## Use the Python SDK

After the installation above, run this example from the repository directory:

```python
from agent_user_learning import UserLearner

# Store the demo database beside the repository.
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
    # Give this context to your agent as lower-priority user data.
    print(context["user"]["goals"])
```

This writes a fictional goal to `../aul-demo.db`. You can inspect the same database with the CLI:

```sh
aul --db ../aul-demo.db --user-id demo-user context --scope writing:blog
aul --db ../aul-demo.db --user-id demo-user inspect
aul --db ../aul-demo.db --user-id demo-user explain --kind attribute --rule-id 'writing:blog|goals.finish-draft'
```

For real users, choose a private location outside the repository, create its parent directory, and keep a separate database for each user.

## Use as a Skill

Copy the complete `skills/agent-user-learning` directory into the location used by your agent. The bundled runtime uses only the Python standard library; installing the SDK is optional for Skill use.

| Host | Project location | Personal location |
| --- | --- | --- |
| Codex | `.agents/skills/agent-user-learning/` | `~/.agents/skills/agent-user-learning/` |
| Claude Code | `.claude/skills/agent-user-learning/` | `~/.claude/skills/agent-user-learning/` |
| OpenCode | `.opencode/skills/agent-user-learning/` | `~/.config/opencode/skills/agent-user-learning/` |

See the hosts' official [Codex](https://developers.openai.com/codex/skills/), [Claude Code](https://code.claude.com/docs/en/skills), and [OpenCode](https://opencode.ai/docs/skills/) documentation. The host needs to call AUL before and after tasks; copying the Skill exposes its instructions and runtime but does not create those calls. See [Integration](skills/agent-user-learning/references/integration.md) for the workflow.

## How learning works

1. Your application chooses task labels, called scopes, and reads `context()` before the agent starts work.
2. The agent uses the relevant context along with the user's current request.
3. After the interaction, your application turns useful user statements into structured events and writes them to AUL.
4. Explicit statements and corrections take effect when written. Inferred interests or habits need matching evidence from two distinct sources in two sessions. Profile and constraint records require explicit statements.
5. The user can inspect, explain, correct or forget records.

Your application selects the scopes. `general` is always included, and later supplied scopes take precedence for the same key. Temporary `current.*` records need an expiry. Inferences cannot replace explicit records in the same scope. The [Protocol](skills/agent-user-learning/references/protocol.md) covers event formats, version checks, retries and forgetting.

## Status and development

Version **0.1.0** is a local prototype built with Python's standard library and SQLite. AUL processes structured events; the host supplies extraction from messages, task selection and agent calls. The host also handles authentication, storage permissions and deletion from backups. The database uses schema 2; migration from earlier prototypes is not included.

```sh
python -m pip install .
python -m unittest discover -s tests -v
python scripts/sync_skill.py --check
```

Change the SDK engine first, then run `python scripts/sync_skill.py` to regenerate the portable runtime. Tests cover user understanding, behavior adaptation, scope precedence, expiry, forgetting, replay, concurrent writers, bounded context and offline CLI portability.

The [integration starter](examples/agent_integration.py) and its tests verify the
callback flow with a deterministic responder. Framework-specific adapters and
real interaction testing remain next steps: whether users need fewer repeated
corrections and whether irrelevant preferences stay out of responses.

## Project guide

| Resource | Contents |
| --- | --- |
| [Integration brief](INTEGRATE.md) | Give this to your coding agent to implement and verify an integration |
| [Runnable starter](examples/agent_integration.py) | Persistence, response callback, scoped recall, correction and forgetting |
| [Architecture](docs/architecture.md) | Lifecycle, components, storage and conflict handling |
| [Protocol](skills/agent-user-learning/references/protocol.md) | Event fields, scopes, context limits and user controls |
| [Integration](skills/agent-user-learning/references/integration.md) | Host responsibilities and evaluation |
| [Contributing](CONTRIBUTING.md) | Setup, changes, checks and reproducible reports |
| [Changelog](CHANGELOG.md) | Prototype features and current source changes |

Licensed under [MIT](LICENSE).
