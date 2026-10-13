# Contributing

Useful contributions include reproducible fixes, host adapters and examples
that demonstrate a complete read/write workflow. Start with the [architecture](docs/architecture.md)
and [event protocol](skills/agent-user-learning/references/protocol.md).

## Contribution priorities

These are open areas for contribution, not completed features. Start with one
small, reproducible result. An issue describing the intended integration is
useful for larger changes; small fixes can go straight to a pull request.

| Priority | Contribution | A useful first result |
| --- | --- | --- |
| 1 | A real host integration | Wire an existing agent's turn handler to AUL; document installation and pass the acceptance checks in [INTEGRATE.md](INTEGRATE.md), including reopen, correction, forgetting and user isolation. State whether extraction is automatic or uses explicit commands. |
| 2 | Extraction and relevance evaluation | Publish synthetic or shareable, consented cases with expected events/scopes. Include quoted text, one-off requests, contradictory statements and delayed corrections. Report missed facts, false memories and irrelevant recall separately. |
| 3 | User memory controls | Add a small host UI or command flow to view evidence, correct a record and forget an item. Show that the next agent turn uses the changed state and another user cannot access it. |
| 4 | Storage lifecycle and workload measurements | Measure context-read latency and write behavior at documented event counts and concurrency on named hardware. Use results to guide retention, snapshots or migrations; preserve replay, correction and forgetting semantics. |

For a personal agent, a reliable explicit "remember / correct / forget" flow
is a useful first integration. For a small business application, add the host's
authentication, user controls and backup/deletion lifecycle, then measure its
actual workload. AUL's current synthetic tests do not establish production
scale or extraction quality.

Reports from using AUL in your own project are welcome: what you connected,
which commands worked, where integration failed, and a minimal synthetic
reproduction. Do not include private conversations or user databases.

## Development setup

Use Python 3.11 or newer. Clone the repository, then create a virtual environment:

```sh
python -m venv .venv
```

On macOS/Linux, use `.venv/bin/python` for the commands below. On Windows, use
`.venv\Scripts\python.exe`. After activating the environment, `python` refers
to that interpreter:

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/sync_skill.py --check
python examples/user_learning_demo.py
python examples/agent_integration.py
```

The runtime uses the standard library. Installation may obtain setuptools for
the build environment. The demo and tests use synthetic data and need no model
credentials.

## Changing the engine

Edit `src/agent_user_learning/engine.py`, then generate the portable Skill runtime:

```sh
python scripts/sync_skill.py
python scripts/sync_skill.py --check
```

Commit both files together. Re-run the relevant checks after a change. For a
behavioral fix, add a regression test that reproduces the failure and checks
the observable result. Describe changes to event validation, schema, retry
behavior or deletion in the protocol and changelog.

Keep databases, virtual environments, credentials and private conversation
material outside commits. Examples and test fixtures should be fictional.

## Reporting a problem

Include the Python version, OS, AUL version, command or SDK call, synthetic
input, expected result and actual result. For a write problem, include the
relevant version and event IDs. Reduce the example before sharing it, and
replace personal evidence with a synthetic equivalent.

## Pull requests

Explain the failure or use case, the resulting behavior, and the checks you
ran. Identify which results came from automated tests and which came from a
running host application. Use [the integration brief](INTEGRATE.md) for the
acceptance checks an adapter should pass. An adapter should document its lifecycle calls,
per-user storage, conflict handling and user control interface.

GitHub Actions runs installation, tests, runtime sync and the offline demo on
Ubuntu and Windows with Python 3.11 and 3.13. Check the run associated with
your actual commit.

## Editing documentation and the diagram

Keep English and Chinese introductions aligned. Detailed contracts belong in
the protocol or integration guide; the README should help someone understand
and try the project.

The README files contain the task workflow as text and arrows;
`docs/architecture.md` contains the component map. Keep those diagrams aligned
with the engine's read, write, retry and forgetting behavior.

The optional illustrated diagram is `docs/images/aul-workflow.svg`. Export the matching PNG
after editing it, for example using Inkscape:

```sh
inkscape docs/images/aul-workflow.svg --export-type=png --export-filename=docs/images/aul-workflow.png
```

Inkscape is an optional documentation tool, not a runtime dependency. Verify
that all text is readable and that the arrows match the engine and host lifecycle.

Contributions to the repository are covered by its [MIT license](LICENSE).
