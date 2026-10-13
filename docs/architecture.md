# Architecture

[Project overview](../README.md) · [Event protocol](../skills/agent-user-learning/references/protocol.md) · [Host integration](../skills/agent-user-learning/references/integration.md)

## Runtime architecture

```text
User request / user messages
  -> Host application
       |-- Authentication + per-user database selection
       |-- Task scopes + trusted message extraction
       |-- Agent / model / tool calls
       `-- User controls: inspect / explain / correct / forget
            |
            v
       AUL entry points
       Python SDK / JSON CLI / portable Skill runtime
            |
            v
       UserLearner engine
       |-- Read:  replay -> expiry -> scope selection -> bounded context
       |-- Write: validate -> deduplicate -> version check -> commit
       `-- Forget: version check -> delete evidence + feedback -> replay on read
            |
            v
       Private SQLite database (one user)
       |-- aul_meta: schema + user_id + version
       `-- aul_events: ordered events + source IDs + evidence

Read path:     Host -> AUL -> SQLite -> AUL context -> Host -> Agent
Learning path: User message -> Host extraction -> AUL validation -> SQLite
Conflict path: VersionConflict -> Host rereads -> Reassess -> Revised proposal
```

The SDK and CLI use the engine directly. The Skill bundles a generated copy
of that same engine; it is another entry point, not an independent service.
See the [task workflow](../README.md#runtime-workflow),
[illustrated workflow](images/aul-workflow.png) or [editable SVG](images/aul-workflow.svg).

## Task lifecycle

The host resolves the user, chooses scopes and calls `context()` before the
agent plans a task. AUL replays the user's events, selects active attributes
and behavior rules, and returns a bounded snapshot with its version. The agent
uses the snapshot as user data alongside the current request.

After the turn, the host extracts useful statements or corrections from the
user's own messages. It passes structured events to `observe()` with an
`expected_version`. AUL validates the event and writes it in a SQLite
transaction. The next context read reflects the updated records.

The diagram shows responsibility, not an autonomous worker. The host implements
message extraction, task selection, model/tool calls and the control interface.

## Components

| Component | Location | Responsibility |
| --- | --- | --- |
| Engine | `src/agent_user_learning/engine.py` | Event validation, transactions, replay, context selection and deletion |
| SDK | `src/agent_user_learning/__init__.py` | Exposes `UserLearner` and `VersionConflict` |
| CLI | `src/agent_user_learning/__main__.py`, `aul` entry point | JSON input/output for processes and tools |
| Skill | `skills/agent-user-learning/` | Instructions, protocol and the standalone engine copy |
| Runtime sync | `scripts/sync_skill.py` | Generates or checks the standalone copy against the engine |
| Host | Application using AUL | Authentication, extraction, scope selection, storage permissions and agent calls |

## Storage and derived records

Each database belongs to one user. `aul_meta` stores its schema, user ID and
version; `aul_events` stores ordered events with source IDs and bounded evidence.
Attributes and behavior rules are derived on reads rather than kept in a
separate mutable profile table.

Explicit statements and corrections activate records. Inferences become active
only after matching evidence from two distinct sources in two sessions. Profile
and constraint attributes require explicit evidence. Expired events do not
contribute to the read projection. Active context includes only the scopes
selected by the host, plus `general`.

The default context limits are 2,400 Unicode characters, eight attributes and
six behavior rules. These are character limits, not model token limits.

## Write contract and recovery

| Situation | Observable behavior | Host action |
| --- | --- | --- |
| Same event ID and validated payload retried | `duplicate: true`; no second event | Treat as the original write already recorded |
| Same event ID with a different payload | Rejected | Fix the event identity; do not overwrite evidence |
| Stale version for a new write | `VersionConflict` | Read current state and reassess the proposal |
| Invalid event | `ValueError` | Correct the event before retrying |
| Wrong user ID or database schema | Rejected when opening | Use the correct per-user database and supported schema |

Avoid blindly retrying a delayed extraction: a newer user correction may have
changed what should be recorded. Serialize learning writes per user where
possible, and keep stable IDs for retries. The protocol contains exact field
requirements and the CLI's error behavior.

## User controls

`inspect()` shows current records; `explain()` returns their supporting evidence.
Corrections use new explicit events. `forget_rule()` removes an item's revisions
and dependent feedback; taste items remove both like and dislike histories in
the selected scope. `forget()` retracts a source and can restore an older value
during replay.

Deletion is logical. The host handles backups, caches and excluding forgotten
information from future extraction. A database's user ID is an isolation check;
application authentication and filesystem permissions remain host responsibilities.

## What validation establishes

The automated suite checks context selection, correction, expiry, forgetting,
replay, version conflicts, user isolation checks and CLI portability. It uses
synthetic data. Adapter behavior, extraction accuracy and user experience need
evaluation in the application that uses AUL.

Current storage is schema 2. A migration from earlier prototype databases is
not included. SDK, CLI and Skill share the same engine; host adapters are the
next integration work.
