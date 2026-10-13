# Changelog

## Unreleased

- Add a copyable agent integration request and a runnable read/respond/learn example to both READMEs.
- Add INTEGRATE.md with SDK/CLI entry points, host responsibilities and acceptance checks.
- Verify persistent recall, scope selection, correction, forgetting and isolation at the response callback boundary.
- Add repository links and user-memory keywords to package metadata.
- Add text-and-arrow runtime workflows to both READMEs and a component map to the architecture guide.
- Preserve Unicode CLI output on terminals and pipes with limited encodings.
- Reject expiry timestamps that overflow the supported UTC range as invalid input.
- Exclude expired evidence from explanations, including when a source ID is reused.
- Add regression coverage for those three boundary cases.
- Add a workflow diagram that shows host and AUL responsibilities.
- Add architecture and contribution guides.
- Make the SDK quick start runnable and use the same demo database in CLI examples.
- Use general task examples and shorter English and Chinese introductions.

## 0.1.0 prototype

- Python SDK, JSON CLI and portable `agent-user-learning` Skill.
- Per-user SQLite events with evidence, source IDs and version checks.
- Scoped user attributes and help preferences, correction, expiry and targeted feedback.
- Inspect, explain, source retraction and item-level forgetting.
- Bounded context and a standalone runtime generated from the SDK engine.
- Synthetic tests and an offline demonstration.

The package version is 0.1.0. These notes describe the source prototype;
they do not imply a published PyPI package or a tagged GitHub release.
