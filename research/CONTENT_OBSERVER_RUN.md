# Combined content and execution observation

15 November 2026. The user's clarified objective is an undergraduate project
combining recent research: Jev observes exposed agent information and behavior,
with the existing Linux boundary supplying enforcement and native evidence.
Global algorithmic novelty and Q1 submission are no longer completion gates.
See [current direction](../PROJECT_DIRECTION.md) for the design and literature.

## Implemented path

`agent_observer.py` asks separate typed Jev questions about task deviation,
disclosure/evasion and suspected unauthorized coordination. It retains original
content, bounded chunk inputs, model responses, hashes, excerpts and verdicts.
The coding-agent launcher supplies its prompt and emitted assistant blocks.
The MCP adapter checks argv before execution and tool content before delivery,
with bounded shared runtime facts. A flag or observer error stops its authority;
a trusted host stop marker also reaches the Linux broker's stop event.
The source-derived stop paths were not exercised in this ordinary-work run.

## Actual continued coding workflow

One existing Grok conversation continued with four assistant turns and three
MCP commands: build the release, inspect the manifest/archive, and write a package
inventory. All commands returned zero and `no_observed_violation`. The actual
package contains the new observer module. No training, supplied covert objective,
secret protocol, new probe suite or extra subject population was introduced.

The retained host journal contains five content records: one prompt and four
assistant messages, with five Jev calls. The MCP journal contains six records:
three argv requests and three tool results, with seven Jev calls because one
result spans chunks. All content decisions were `not_flagged`; the maximum
individual question probability was 0.19 in the host journal and 0.20 in the tool
journal, below the existing 0.5 content threshold. These are observations, not
precision/recall estimates or evidence that the content was certainly safe.
There are also 48 saved kernel/shared observer receipts.

The [summary](content-observer-runs/v1/summary.json), source snapshot, host JSONL,
MCP evidence and [inventory](content-observer-runs/v1/session/public/results/step-003/package-inventory.json)
are retained. `summarize.py` checked all content/input hashes and preceding-content
links, shared-observer input receipts, archive/member hashes and packaged source
matches. Those checks establish consistency of retained files, not completeness
of observation. Native policy is 3 and the launch guard version is 1.

The built 40,092-byte archive has 15 members and SHA-256
`9a9d50596b994d5bef20e60681f8969bf997a0d3629fb70764f4d459e449314c`.
It is preserved in the run artifacts; prior distributions are retained separately.

## Limits preserved

Host observation occurs after complete message emission, not per-token before
generation. Only exposed reasoning text is visible. The host and MCP use separate
bounded journals, not a fully joined transcript. Old resumed context is not
automatically ingested. Artifact bytes absent from delivered tool results are
not automatically inspected; the existing native gate still constrains access.
The 2,048-character chunks and short excerpts can hide distributed meaning.

The largest reported input in this continuation was 47,099 tokens, which does
not establish context exhaustion. No covert convention emerged or was validated.
No content-triggered stop occurred. The tool scope again retained `closed: false`
after client teardown; this missing closure record is not converted to success.
The host CLI exited zero. Actual cancellation of hosted inference is unavailable.
The runtime edits had reached remote commit `ac5e644` during an interrupted turn;
the source snapshot records exactly what this workflow used.

The next milestone is a small set of continuing workers on complementary useful
tasks with explicitly mediated handoffs, inspecting messages and artifacts at
delivery. Suspicion must remain distinct from a causally validated convention.
