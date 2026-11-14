# Shared observer context in real session work

The session observer now evaluates a worker's current native-event batch together
with bounded shared facts: worker identities, protected-resource grants, filesystem
scope, cumulative activity counts, recent worker events and recent broker outcomes.
The trusted controller retains this state independently of worker conversational
memory. Enforcement remains in the namespaces, notification gate and shared broker.

[`session_observer.py`](../session_observer.py) supplies the shared state for both
runtime judgments and protected-resource authorization. Local event indices are
stable across late native-frame updates; a `(worker, event_index)` key prevents
those revisions from inflating activity counts. Events retain their trace source
and timestamp. Supervisor receipt order is not claimed to be kernel causal order.

## Bounded state and provenance

The current event batch remains limited to 8 KiB. Shared context is limited to
6 KiB, with at most 32 recent event summaries and eight recent broker records.
Older event detail can be omitted from shared context; cumulative worker counts
and an explicit omission count remain. A maximum of 8,192 unique event identities
is tracked; exhausting that bookkeeping budget causes abstention rather than
pretending observation stayed complete. Serialized Jev state is capped at 20 KiB;
the actual HTTP request also contains its model/question envelope. These are byte
budgets, not authoritative tokenizer measurements.

Every state supplied to Jev is frozen under the session's `_observer` evidence
directory with a hash and decision/fault receipt. Runtime actions and broker
approvals carry the state receipt path and hash. These paths are relative to the
session evidence root. The raw state receipt excludes the authorization header
and resource contents; model/question definitions remain in the packaged source.

## Actual work and a retained false alarm

The first implementation ran the real compiler/package and source-change-index
workflow. The source indexer completed, and the compiler produced its archive,
but a later Jev judgment flagged legitimate final build activity at 0.54. The
session reported violation even though the compiler had already exited 0. This
is a false alarm, not successful prevention of malicious work. The full run is
retained in `system-runs/shared-context-false-alarm`.

The supplied representation exposed an ambiguity: its `denied` counter included
every failed syscall, including ordinary `ENOENT` library/path lookups. An empty
protected-resource grant list could also be mistaken for no filesystem authority.
The runtime now records `errno` and `permission_denied` separately. The legacy
`denied` flag remains an any-failure flag for compatibility. Shared counts distinguish
failed calls from permission errors, and recent summaries retain their actual
errno. Explicit namespace facts distinguish normal public reads, private output
writes and the read-only enforced helper from an ordinary compiled copy in output.

The subsequent real session completed both workers with exit 0 and
`no_observed_violation`. Its 36 shared state receipts include 35 runtime batches
joined to saved native-event inputs and one protected-resource judgment. Thirty-two
receipts include observed activity from both workers, and 34 include broker history.
The largest serialized state was 15,323 bytes. The package and source-change index
were produced by the actual tasks, not by fixture observers.

[Retained outcome](system-runs/shared-context-build/observer-summary.json).
The older false alarm and this completed run involve several representation
changes together, as well as different execution timing. They do not isolate a
causal effect, establish calibration or estimate detector accuracy. The stopping
threshold was not raised to make the workload complete.

## Product boundary

The current [Linux runtime archive](../dist/GuardianAI-linux-x86_64.zip) includes the
shared observer. Its manifest hashes were checked against the packaged member
bytes and the current Python source. The previous package remains in
`dist/archive-v2`, and the original single-worker package remains in `dist/archive-v1`.
See [session usage](../SESSION.md).

Shared context improves available evidence; it is not complete session memory.
Worker-local namespace paths must not be treated as globally identical files.
Recent details can roll out of the context, unseen behavior remains unseen, and
typed probabilities can still be wrong. No malicious-thought access, natural
context-window exhaustion, general covert-channel detector or publication-level
novelty is established. No new unit/attack suite or model-agent population was
added: development used the actual build and release-index workflow.
