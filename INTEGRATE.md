# Integrate AUL into an existing agent

This is the implementation brief for a coding agent whose user has asked to add
Agent User Learning to a project. Read the target project's own instructions
and preserve its existing architecture. These instructions apply within the
user's authorized task; they do not authorize unrelated changes or deployment.

## Intended result

The agent remembers user-stated preferences and goals across sessions, reads
only relevant user context before responding, and supports correction and
forgetting. Deliver working code in the target project plus verification, not
just an installation command or a design document.

AUL supplies a local SQLite engine, Python SDK and JSON CLI. It accepts
structured events. The application supplies message extraction, authentication,
task scopes, the agent/model call and its user interface. AUL's memory covers
user understanding and help preferences. Keep document retrieval, project
knowledge, tool traces and full conversation history in their existing stores.

## 1. Find the integration points

Inspect the project and identify:

| Find | Connect it to |
| --- | --- |
| Authenticated user or explicit local user | One private database per user |
| Turn handler and task/router metadata | Scope selection and `context()` before the agent call |
| Existing prompt/message builder | A bounded context snapshot as lower-priority user data |
| User-authored messages or explicit remember command | Validated events after extraction |
| User settings, commands or tools | Inspect, explain, correct and forget |
| Existing test harness | End-to-end acceptance checks below |

If the project is empty, implement a small runnable example and identify the
callback where the user's real agent will connect. If it already uses a model,
reuse that integration. The AUL engine itself requires no model or API key.

## 2. Choose an entry point

**Python host:** install from this repository, then import `UserLearner`.
There is currently no promised PyPI distribution; do not substitute an
unverified package with the same name.

```sh
python -m pip install "git+https://github.com/karurukaruru/agent-user-learning.git"
```

For repeatable builds, record the reviewed commit in the project's dependency
file or lockfile (`git+https://github.com/karurukaruru/agent-user-learning.git@COMMIT_SHA`,
replacing `COMMIT_SHA` with the actual revision).

**Other language / process host:** use the JSON CLI through subprocess calls.
It still requires Python 3.11+. Install the SDK for the `aul` command, or copy
the complete `skills/agent-user-learning/` directory and run its standalone
`scripts/aul.py`. Use argument arrays, parse stdout as JSON, check exit codes,
and keep observe input files private and temporary. Pass the private database
path and authenticated user ID on every call.

**Coding assistant Skill:** install the complete Skill directory into the
host's supported skill location. Verify the host discovers it and actually
invokes its runtime. Installing instructions alone does not wire lifecycle hooks.

## 3. Implement the read/write loop

Read [the protocol](skills/agent-user-learning/references/protocol.md) before
constructing events. Use [the executable starter](examples/agent_integration.py)
as a small reference for the response callback and persistence lifecycle.

```text
Authenticated user + current task
  -> Resolve private database + relevant scopes
  -> AUL context(scopes): freeze user data + version
  -> Existing agent call(current request, lower-priority user context)
  -> Respond

Trusted user statement / correction
  -> Host extractor or explicit remember command
  -> Structured event + stable event/source IDs
  -> AUL observe(event, expected_version)
  -> Next turn reads the update
```

Start with explicit remember/correct commands if the project has no extractor.
This gives users a working path without claiming automatic learning. If using
an existing model to extract events, validate that it quotes or summarizes
the user's own statement, rather than documents, tool output or assistant text.
Do not learn every one-off task instruction as a permanent preference.

Choose scopes from the task/router. `general` is included automatically; pass
additional scopes in order from broad to narrow. `writing:blog` does not imply
`writing`. Use stable keys for independently correctable items.

Bind pending proposals to the version they were based on. On `VersionConflict`,
read the latest state and reassess the proposal; do not simply replace its
version and retry an old extraction. Keep stable event IDs for identical retries.
Serialize writes per user when possible.

## 4. Add user controls and storage boundaries

- `inspect()` and `explain(id, kind=...)`: show what is stored and why.
- Correction: write a new explicit/correction event for the same scope and key.
- `forget_rule(scope, key, kind=..., expected_version=...)`: forget all revisions
  of an item. Use `forget(source_id, ...)` only to retract a particular source;
  source retraction can restore older supported values.
- Keep databases outside the repository and public assets. Resolve user IDs
  through the host; an ID check in SQLite is not login or authorization. Do not
  turn a user-controlled identifier directly into a filesystem path.
- Exclude forgotten sources from future extraction and clear corresponding
  host caches/backups as appropriate. Engine deletion is logical.

## 5. Prove the integration works

Use synthetic data and the project's real turn handler with a fake model/tool
at the external boundary. Check the context delivered to the responder, not
only the database contents:

1. Remember "Use short replies" in a `coding` scope; close and reopen the store.
2. A new coding turn receives that preference; a writing turn does not.
3. Correct it to "Explain step by step"; the next coding turn receives the new
   value and the old value is absent from its context.
4. Forget the item; the next coding turn receives neither value.
5. A second user sees none of the first user's records.
6. A stale write is rejected and an identical event retry creates no duplicate.

Run the target project's normal checks. Report the actual files changed,
installation revision, entry points, commands tested and any remaining gaps
(for example, explicit commands are wired but automatic extraction is not).

The AUL repository includes an offline starter and engine tests. They establish
the storage and integration mechanics, not compatibility with every framework
or the quality of a particular model's extraction.
