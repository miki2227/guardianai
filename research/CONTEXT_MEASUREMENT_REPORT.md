# Context measurements and persistent-subject evidence

The corrected eight-episode historical social block does not measure persistent
context-window pressure. All 16 sender/receiver dispatch records explicitly declare
`freshContext: true`; none supplies provider token usage. Passing each player's
own note to a fresh call is context-based adaptation, not evidence that a provider
retained a growing conversation. The original task/faction outcomes remain valid
within their stated scope; this audit does not replace or reclassify them as
long-window results.

## Current interface inspection

A read-only inspection of the existing sender subject exposes completed run
identities, requested model, activity messages and run timestamps. Its latest
returned run metadata has no token-usage or context-capacity field and no separate
resolved executed-model value. The saved
[interface response](context-records/subject-interface-inspection.json) is evidence
for this returned surface only; it does not prove that the provider has no such
telemetry elsewhere. No subject was restarted or sent another task.

An active logical thread, its run count, message count and wall-clock age do not
establish retained provider context. Checkpoint events can describe repository
changes and must not automatically be interpreted as model-history compaction.
Similarly, the absence of a compaction event does not establish intact context.

## Working recorder

[`context_record.py`](../context_record.py) records one completed observed exchange:

- The dispatch, request and response must agree on run and subject identities.
- The saved prompt must match the observed request, and the saved reply must match
  the observed response. Truncated records are rejected.
- Exact observed request text, its UTF-8 byte count, raw artifact hashes, requested
  and reported executed model, and explicit context-reset declarations are retained.
- An absent reset declaration becomes `retention_unverified`. Even an explicit
  `freshContext: false` does not prove what history the provider actually retained.
- Provider-reported usage/capacity fields, if present, are retained as reported.
  They are not automatically converted into context occupancy: accounting scope,
  capacity semantics and provider history still need verification.
- `context_pressure` stays `unmeasured`, and `context_limit_exceeded` stays null
  without a validated measurement contract. Prompt bytes never become token counts.

For a newly retained compatible exchange:

```sh
python context_record.py --metadata /path/to/provider-metadata.json \
  --prompt /path/to/sent-prompt.json --reply /path/to/received-reply.txt \
  --destination /new/evidence/turn-directory
```

The metadata format is the actual retained T3 exchange structure (`send`, `run`,
`activity`, optional `controls`), not an arbitrary provider API response. This is
an evidence recorder and validator, not a model transport, tokenizer or mechanism
that extends a context window. Hidden provider/system context is not reconstructed
from the observed user message. Synthetic study prompts should remain free of real
credentials or private data.

## Real-data validation

[`context_import.py`](context_import.py) imports the exact eight corrected cases
named by the social report, including the first fixed case stored under
`full-history-s103`. The complete [import-v2 result](context-records/import-v2/summary.json)
contains 16 verified exchanges from the existing two logical subject identities,
16 declared resets and zero available usage records. Raw source artifacts and
the recorder/importer source snapshots are retained with hashes. The earlier
import-v1 selected only the seven cases with fixed/context filename prefixes;
it remains a 14-record subset and is not the complete corrected-block audit.

Reproduce the full import without any model request:

```sh
python research/context_import.py --destination /new/context-import-directory
```

Five new test methods exercise unknown retention, explicit resets, reported usage
without a verified counting scope, large prompts, wrong-run/subject/message joins,
truncated records, duplicate destinations and artifact/derived-record changes.
These validate the evidence contract, not the provider's internal memory.
The full native Linux suite passed **85 tests**;
[retained log](context-records/tests-wsl2.txt).

## Measurement gate for the next experiment

Keep the requested two persistent Grok subjects and ordinary task stream. Before
calling an arm naturally near or beyond a context limit, obtain retained-context
token accounting and a compatible capacity/output-reservation definition from
the actual serving interface, plus reset/compaction semantics. A public model
capacity alone cannot establish what a wrapper retained for a particular call.
If those measurements remain unavailable, report context pressure as unmeasured.

Controlled truncation and explicit summaries can still be independently assigned
and measured, but must be named as experimenter interventions. Do not silently
present them as natural window exhaustion. Record each summary and the exact
request that uses it. Bind subsequent tool actions to the trusted broker's current
task/epoch and fresh resource version; conversational notes cannot restore revoked
authority. Previously disclosed knowledge is not evidence of a new data release.

This recorder removes an ambiguity in the proposed study, not the remaining
experimental requirement. Persistent hosted inference, natural context pressure,
misalignment emergence and publication-level novelty are still unmeasured.
