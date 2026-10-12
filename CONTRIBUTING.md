# Contributing

Useful contributions include reproducible fixes, host adapters and examples
that demonstrate a complete read/write workflow. Start with the [architecture](docs/architecture.md)
and [event protocol](skills/agent-user-learning/references/protocol.md).

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
running host application. An adapter should document its lifecycle calls,
per-user storage, conflict handling and user control interface.

GitHub Actions runs installation, tests, runtime sync and the offline demo on
Ubuntu and Windows with Python 3.11 and 3.13. Check the run associated with
your actual commit.

## Editing documentation and the diagram

Keep English and Chinese introductions aligned. Detailed contracts belong in
the protocol or integration guide; the README should help someone understand
and try the project.

The source diagram is `docs/images/aul-workflow.svg`. Export the matching PNG
after editing it, for example using Inkscape:

```sh
inkscape docs/images/aul-workflow.svg --export-type=png --export-filename=docs/images/aul-workflow.png
```

Inkscape is an optional documentation tool, not a runtime dependency. Verify
that all text is readable and that the arrows match the engine and host lifecycle.

Contributions to the repository are covered by its [MIT license](LICENSE).
