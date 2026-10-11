# Integrating AUL into an agent or product

AUL is a user understanding and adaptation component. Any agent that can run
Python or call a process can use it. The SDK and portable Skill runtime share
one engine; no OpenWoven import or external service is required.

## Host lifecycle

1. Resolve an authenticated user and their private database. Create its parent
   directory with appropriate permissions. Keep it outside version control.
2. Classify the current task into relevant scopes. Read a frozen context once
   for that task, before planning and generating a response.
3. Pass it as lower-priority user data. Use goals to prioritize work, experience
   to choose depth, interests to choose suitable examples, and behavior rules
   to shape help. Never treat arbitrary stored values as system instructions.
4. Complete the task. Extract small changes from trusted user-authored messages;
   do not harvest project documents or quotes as personal evidence. Distinguish
   temporary instructions from recurring preferences and user identity from
   hypothetical characters. Use stable source/event IDs for retry safety.
5. Serialize learning writes per user. Reread version before committing and
   reassess stale proposals. Ensure delayed extraction cannot overwrite a newer
   explicit correction. Schedule inference conservatively or show candidates
   for user confirmation when identity or ambiguity matters.
6. Support inspect, explain, correction and item-level forgetting. Stop future
   re-extraction of forgotten information, and delete corresponding host caches
   or backups as appropriate. The engine's deletion is logical.

A minimal application starts with explicit statements. Add inference only when
its extraction quality has been evaluated. The engine validates structured
events, not whether an extractor has honestly represented the user.

## SDK and CLI

```python
from agent_user_learning import UserLearner, VersionConflict

with UserLearner(private_db, authenticated_user_id) as learner:
    snapshot = learner.context(["study", "study:japanese"])
    # Host: respond using this snapshot and the current request.
    # Host: extract an event from a trusted user statement.
    # learner.observe(event, expected_version=snapshot["version"])
    # If stale, inspect current state and reassess before resubmitting.
```

CLI observe takes a JSON file containing exactly `expected_version` and `event`.
Use the SDK for structured integration or the bundled standalone script for a
Skill. A Skill contains instructions and a tool; the host must actually invoke
it. Installation alone creates no automatic hooks, autonomous learning worker,
or synchronization between products.

## Isolation and interpretation

- Use one private database per user. SQLite concurrency plus version checks
  prevent competing writers from silently overwriting the same version.
- Do not learn identity or constraints through inference; preserve the user's
  own wording. No personality diagnosis, credentials or speculative sensitive
  traits belong in this layer.
- Scope understanding narrowly enough to avoid irrelevant personalization.
  A dislike during study need not erase a general interest in another setting.
- Agent persona, project knowledge and full conversation archives may live in
  their own stores. Use AUL attributes for personal understanding that improves
  help, without duplicating an entire transcript.

## Evaluate before promising improvement

Evaluate mechanics with synthetic users: corrections supersede old values,
expiry works, irrelevant scopes stay out, forgetting removes all revisions,
and the context remains bounded. Then evaluate actual interactions, with
appropriate user controls:

| Metric | What to observe |
| --- | --- |
| Repeated corrections | Does the user need to restate an already learned preference? |
| Task completion | Does relevant user context improve the requested outcome? |
| Unwanted adaptation | Does the agent overuse interests or apply stale assumptions? |
| Correction/forget accuracy | Do changes take effect and remain changed? |
| Context cost | Are useful entries retained inside the character/token budget? |

Synthetic tests validate implementation behavior. They do not establish product
satisfaction, extractor accuracy, or improved outcomes for real users.
