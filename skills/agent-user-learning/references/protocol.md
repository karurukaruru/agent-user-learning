# AUL protocol (schema 2)

- [User attributes](#user-attributes)
- [Help preferences](#help-preferences)
- [Targeted behavior feedback](#targeted-behavior-feedback)
- [Reads and projection](#reads-and-projection)
- [Writes, retries and forgetting](#writes-retries-and-forgetting)

The Python `UserLearner` and bundled `scripts/aul.py` share the same engine.
All events require nonempty single-line `event_id`, `source_id` and `evidence`.
Limits: IDs 160 characters, evidence 360, action/value 240, scope/key 80.
Scope/key identifiers use lowercase letters, digits and `._:/-`; `|` is reserved.

## User attributes

```json
{
  "expected_version": 0,
  "event": {
    "event_id": "extract:user-message-42:goal",
    "source_id": "user-message-42",
    "session_id": "session-7",
    "kind": "attribute",
    "scope": "study:japanese",
    "key": "goals.pass-n4",
    "value": "Wants to pass JLPT N4.",
    "signal": "explicit",
    "evidence": "User says they want to pass JLPT N4."
  }
}
```

| Key group | Example key | Rule |
| --- | --- | --- |
| `profile` | `profile.name`, `profile.experience` | Explicit user evidence required |
| `interests` | `interests.music` | Explicit or corroborated inference |
| `likes` | `likes.city-pop` | Shares suffix with opposite dislike |
| `dislikes` | `dislikes.city-pop` | Active entry replaces opposite in same scope |
| `goals` | `goals.pass-n4` | A concrete user goal |
| `habits` | `habits.study-session` | A useful recurring routine |
| `constraints` | `constraints.accessibility` | Explicit user evidence required |
| `current` | `current.energy` | Requires `expires_at` |

Choose one stable key per independently correctable item. Use values that
accurately represent the user's statement, not diagnostic labels. Expiry is
an ISO timestamp with timezone, for example `2026-10-12T00:00:00+08:00`.
Expired evidence does not contribute to a derived record.

## Help preferences

A `preference` uses the same metadata, with a concrete `action` instead of
`value`. Its key is host-defined and does not require an attribute group.

```json
{
  "expected_version": 1,
  "event": {
    "event_id": "extract:user-message-43:format",
    "source_id": "user-message-43",
    "session_id": "session-7",
    "kind": "preference",
    "scope": "study:japanese",
    "key": "examples.format",
    "action": "Use short worked examples.",
    "signal": "explicit",
    "evidence": "User asks for short worked examples."
  }
}
```

Signals: `explicit`, `correction`, `inferred`. The first two activate
immediately. Inference requires the same scope, key and value/action from
two distinct source IDs in two distinct sessions. Repetition inside one
session or rewriting the same source does not qualify. Candidates are visible
in `inspect`, excluded from runtime context and never hide confirmed values.
Explicit records cannot be replaced by inferences in the same scope.

## Targeted behavior feedback

```json
{
  "expected_version": 2,
  "event": {
    "event_id": "evaluate:reply-8",
    "source_id": "user-message-44",
    "kind": "feedback",
    "rule_id": "study:japanese|examples.format",
    "rule_revision": 2,
    "outcome": "accepted",
    "evidence": "User explicitly confirms the short example format helped."
  }
}
```

Use the actual ID and revision read from context; the example assumes the
preference was the second inserted event. Revisions are SQLite sequence IDs,
not the store version. Outcomes are `accepted` or `rejected`. A rejection
disables that behavior; only a fresh explicit event can reactivate it. Feedback
for an absent, candidate or stale rule is rejected. It cannot target attributes.
Acceptance records evaluation; it does not automatically increase a confidence
score or infer new personal facts.

## Reads and projection

- `inspect`: full derived attributes/rules, statuses, revisions and source IDs.
- `context --scope ...`: compact user groups and active behavior rules from one
  frozen snapshot. Defaults: 2400 Unicode characters, 8 attributes, 6 rules.
- `policy --scope ...`: behavior-only projection. Defaults: 1800 characters,
  6 rules; useful for hosts with an existing user model.
- `explain --rule-id <scope>|<key> --kind attribute|preference`: bounded source
  evidence for an item and feedback for the active behavior revision.

`general` is implicit. Later scopes take precedence for the same key; a
narrower rejection suppresses the corresponding general behavior. Opposite
tastes use the more specific scope. Context prioritizes profile, constraints,
goals and current state before optional interests, reserves room for behavior
when present, and drops entries to fit the serialized character budget. These
are character caps, not provider token limits. Evidence stays out of context.
The host must select relevant scopes; no implicit ancestry or topic classifier
is supplied. `study:japanese` does not automatically include `study`.

## Writes, retries and forgetting

Read the current version before each new write. Unknown fields and invalid
values are rejected. Repeating an identical `event_id` payload is idempotent,
even with a stale version. Reusing the ID for different content fails. Other
stale writes fail with `VersionConflict`; reread and reassess before retrying.
CLI failures return exit 2 with a generic error code, without echoing evidence.

```sh
python <skill-dir>/scripts/aul.py --db <private-db> --user-id <user-id> forget-rule --scope music --key likes.city-pop --kind attribute --expected-version <current-version>
python <skill-dir>/scripts/aul.py --db <private-db> --user-id <user-id> forget --source-id <source-id> --expected-version <current-version>
```

`forget-rule` removes all revisions of a key and dependent preference feedback.
For an attribute taste item, it also removes the opposite taste's history in
that scope. `forget` retracts evidence from a source and dependent feedback;
replay may restore older supported values or demote an inference to candidate.
Neither operation claims physical deletion from SQLite pages or backups. Hosts
must prevent re-extraction from forgotten sources and delete other copies.

Store schema is 2. A user/schema mismatch fails closed; this prototype has no
migration from schema 1. One private database per user is required; `user_id`
is an isolation assertion, not authentication. The host supplies access controls.
