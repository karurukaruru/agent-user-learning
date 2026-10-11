# Agent User Learning (AUL)

**User context for agents.**

[中文说明](README.zh-CN.md) · [Protocol](skills/agent-user-learning/references/protocol.md) · [Integration](skills/agent-user-learning/references/integration.md)

AUL stores what users share about their interests, preferences, goals, habits and background. Agents read the relevant context for a task, use it to guide their work, and update it when the user makes a correction.

For example, a user prefers brief progress messages while coding but detailed edits when reviewing a draft. AUL keeps these preferences in their respective scopes so the agent can use the appropriate format for each task.

Use the Python SDK, CLI or portable Skill to add user context to an agent or application.

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

These become two projections: **user attributes** describe the user; **behavior rules** describe how to help. The host agent uses both to make decisions. AUL stores bounded evidence and provenance, supports correction and forgetting, and builds a small task-specific context. It does not train model weights or parse conversations by itself.

## Try it locally

Python 3.11 or newer. From this repository:

```sh
python -m pip install .
python examples/user_learning_demo.py
```

The demo uses an in-memory synthetic user. It shows a goal, interests, a help preference, a corrected dislike, and forgetting. No API key or network request is required.

```python
from agent_user_learning import UserLearner

# Choose a private location, outside your repository, with one database per user.
with UserLearner("/private/app-data/user-123.db", "user-123") as learner:
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
```

The parent directory must exist. The sample path is a placeholder; the host chooses storage and access controls.

```sh
aul --db /private/app-data/user-123.db --user-id user-123 context --scope writing:blog
aul --db /private/app-data/user-123.db --user-id user-123 inspect
aul --db /private/app-data/user-123.db --user-id user-123 explain --kind attribute --rule-id 'writing:blog|goals.finish-draft'
```

## Use as a Skill

Copy the complete `skills/agent-user-learning` directory into the location used by your agent. The bundled runtime uses only the Python standard library; installing the SDK is optional for Skill use.

| Host | Project location | Personal location |
| --- | --- | --- |
| Codex | `.agents/skills/agent-user-learning/` | `~/.agents/skills/agent-user-learning/` |
| Claude Code | `.claude/skills/agent-user-learning/` | `~/.claude/skills/agent-user-learning/` |
| OpenCode | `.opencode/skills/agent-user-learning/` | `~/.config/opencode/skills/agent-user-learning/` |

See the hosts' official [Codex](https://developers.openai.com/codex/skills/), [Claude Code](https://code.claude.com/docs/en/skills), and [OpenCode](https://opencode.ai/docs/skills/) documentation. A custom agent can call the SDK or CLI directly. Installation exposes instructions; automatic pre-turn and post-turn hooks must be implemented by the host.

## How learning works

1. Before a task, the host chooses relevant scopes and reads a frozen `context()` snapshot.
2. The agent uses relevant user understanding and help preferences while respecting the current request.
3. After an interaction, the host extracts small structured changes from trusted user evidence. Explicit statements and corrections apply immediately. Inferred interests or habits need matching evidence from two distinct sources in two sessions. Identity and constraints require explicit evidence.
4. The host writes events with the current version. Duplicate retries are idempotent; stale writes and stale feedback are rejected.
5. Corrections replace relevant values. Rejected behavior is disabled. Inspect, explain and forget operations let the user control what is learned.

Scopes are explicit labels, not an automatic topic classifier. `general` is always included; later supplied scopes override earlier ones for the same key. Inferences cannot replace an explicit value in the same scope. Temporary `current.*` attributes require an expiry. Like/dislike keys for the same item use the same suffix so a correction can replace the opposite taste.

## Status and development

Version **0.1.0** is a working local prototype. Runtime dependencies: none. SQLite event replay supplies provenance and user isolation checks. The host remains responsible for extraction quality, relevance, authentication, storage permissions and deletion from backups. Schema 2 rejects earlier prototype databases; no schema migration is included.

```sh
python -m pip install .
python -m unittest discover -s tests -v
python scripts/sync_skill.py --check
```

Change the SDK engine first, then run `python scripts/sync_skill.py` to regenerate the portable runtime. Tests cover user understanding, behavior adaptation, scope precedence, expiry, forgetting, replay, concurrent writers, bounded context and offline CLI portability.

Next priorities are host adapters, real interaction evaluations and better relevance selection. Measure fewer repeated corrections and better task completion before claiming improved user satisfaction. Full transcripts, project knowledge and agent persona may remain in separate systems; user understanding belongs here when it improves help.

Licensed under [MIT](LICENSE).
