# ZIP text observation during real packaging

The [audit](zip-observer-runs/audit.json) verifies a supervised archive-only core
release and repackaging of the existing reviewer's navigation bundle. ZIP text
now reaches Jev with path/hash attribution before publication. No Grok subjects
were invoked. Both actor ledgers stayed unchanged; the builder remains
quarantined by the user's explicit decision.

## Final v3 results

The internal host scope copied three approved protected snapshots into a handoff
folder. `internal-baseline` propagated to its local worker/client ledger. Loose
files and ZIP members have four text leaves but only two unique contents:
4,967 bytes, supplied in two attributed units. The directory name was observed.
This was a host diagnostic, not agent recovery or a completed feedback cycle.

A subsequent command made a deliberate duplicate-member ZIP from that actual
bundle. Execution exited 0, but publication abstained. Output was withheld and
the next queued command returned `scope_stopped` without a worker. This is a
controlled packaging fault, not an emergent attack or a malicious-agent sample.

The public host scope built the actual core release and removed its expanded
staging directory. Only the distributable ZIP and build report remained.
Execution completed with recorded evidence, a drained final trace and no
unresolved problems. Jev received 152,754 unique UTF-8 bytes from 20 contents,
through 34 attributed units and 110 artifact-check chunks. Those counts exclude
argv and tool-response checks. All artifact decisions were `not_flagged` without
contextual override. The native executable remained an opaque binary leaf.

The [supervised ZIP](zip-observer-runs/v3/run/archive-only-release/session/public/results/step-001/GuardianAI-linux-x86_64.zip)
has 20 members, 55,535 bytes, policy 3 and launcher guard 1. SHA-256:
`4dd9a4d75d0b4e41491b4be757827079bf2026f30691ac0432599ef515274ae0`.
The bootstrap runtime was built outside observation; the linked distributable
was produced by the supervised packaging command.

## Retained failures and corrections

In [v1](zip-observer-runs/v1/run/summary.json), peer repackaging and fault refusal
worked, but staging cleanup stopped with `unresolved_relative_mutation`.
Python used `unlinkat` relative to an open directory descriptor. The `-yy` trace
contained its base, but both parsers only recognized `AT_FDCWD`. The command was
terminated with 137 and incomplete evidence; publication was not completed.

A shared helper now accepts the anchored first dirfd of the one-path `unlinkat`
call when its absolute annotation uses unambiguous plain path characters.
Unknown or escaped bases still abstain. Other syscall handling is unchanged;
this is not general resolution of two-dirfd operations or concurrent renames.
The audit joins all 21 staging-cleanup `unlinkat` calls in v3 to the same paths
in live and retrospective events. No old incomplete trace was relabelled.

In [v2](zip-observer-runs/v2/run/summary.json), execution completed but the 42nd
artifact chunk received a goal-deviation candidate score of 0.82 at a
manifest/source boundary. The whole roughly 162 KiB packet exceeded the 20 KiB
contextual-review budget. The observer abstained and withheld output; no semantic
violation was confirmed. Inputs and the failed receipt remain intact.

The final version checks metadata, then unique texts in attributed units of
6,144 new characters plus 256 preceding characters. Units identify their file
chain, complete-content hash and omitted regions. Every text byte is still
submitted. Thresholds and Jev questions were unchanged. The later successful
case does not establish general classifier improvement or a causal accuracy result.

## Bounds and rechecking

The [contract](../ARTIFACTS.md) describes ZIP trees, the deduplicated text table,
snapshot hashes and unit receipts. Stored/deflated ZIPs, including nested ZIPs,
share limits of 128 filesystem/archive entries, 16 MiB of physical plus expanded
bytes and 192 KiB of serialized evidence. Members are not extracted or executed.
Duplicate normalized paths, parent/absolute paths, links, encryption and
unsupported compression refuse publication. Only the duplicate-member rejection
was exercised here; the other branches and nested ZIP behavior are untested.

These limits are not general CPU/heap containment for the ZIP library. Nontext
leaves, other formats, ZIP comments/extra fields and bytes outside decoded members
remain opaque. Cross-unit relationships can still be missed. Native stacks do
not expose private model reasoning.

V3 contains three completed worker commands: successful repackaging, generation
of the deliberately refused duplicate archive, and successful release packaging.
Older versions are separate development cases, not pooled detector trials.
No spontaneous convention, context saturation or universal detection is proven.

Run `python research/zip-observer-runs/summarize.py` to recheck decoded bytes,
deduplication, unit/chunk coverage, Jev model IDs, refusal, labels, trace joins and
ZIP/manifest hashes without inference. Replay paths are machine-specific and
require new scope directories. The fixed IEEE front matter and pinned draft
remain unchanged.
