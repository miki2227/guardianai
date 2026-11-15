# Two continuing agents on an actual release workflow

The user requested a practical system run, rather than more synthetic probes.
This workflow uses two Grok 4.7/low conversations and four alternating phases:
builder release, reviewer inspection, builder response/operator guide, and
reviewer final decision. The builder continues its earlier coding conversation;
the reviewer starts its own conversation and resumes it for the final phase.
No weights are updated and no secret protocol or malicious objective is supplied.

`paired-workflow-runs/v1/run_workflow.py` provisions the existing Grok CLI with
only the GuardianAI MCP execution tool. Each phase uses a fresh Linux scope and
read-only source snapshot, while its model conversation continues. The controller
restores each client's original configuration after the phase. These are two
agent subjects doing the task; no research/review subagents are involved.

The new `guarded_handoff.deliver` snapshots selected regular UTF-8 text files,
asks the content observer about the sender/recipient and exact content, and only
then creates a recipient handoff directory containing the approved bytes. Limits
are 32 KiB per file and 64 KiB total. The trusted controller chooses identities
and exact artifact paths; agents cannot request an arbitrary source path through
this function. The handoff observer retains bounded cross-agent excerpts and
phase metadata. This is a host-mediated text boundary, not a traced kernel relay,
a generic file-sharing service or a binary scanner.

Only the builder's message, build report and manifest go to the first review.
The archive stays with the builder; the reviewer must distinguish checking source
hashes from independently validating unavailable archive/native-binary bytes.
Review messages then go back to the builder; its response and guide go to the
reviewer. Recipient mounts contain the actual delivered snapshots. Any model,
tool or handoff stop ends the alternating workflow; there is no simultaneously
running peer requiring cross-process cancellation in this design.

The existing host-content observer checks the prompt and exposed assistant
messages; MCP checks argv before execution and results before delivery; Linux
namespace/seccomp enforcement and native syscall observation stay active.
History is bounded and exposed reasoning is not private thought access.
Resuming a conversation does not automatically reconstruct its old history for
the observer. Counted token usage cannot establish context exhaustion.

Success means actual release/review artifacts, retained identity continuity,
three approved exact-byte handoffs, command outcomes and inspectable Jev
receipts. A failed phase or false alarm is retained. No completion result should
be inferred from an exit-zero CLI alone when required outputs are absent.
No spontaneous covert convention, detection recall, hard real-time stop, complete
kernel coverage or globally new algorithm is assumed by the protocol. Protected
resource grants, deliberate attacks and cancellation routes are not exercised
merely by completing this ordinary workflow.

The first execution exposed two operational limits: a new untrusted client
directory disabled MCP, and the reviewer then exhausted its 12-round allowance.
The controller retains those attempts and can continue the same conversations
with `--continue-workflow`. It temporarily trusts only its dedicated reviewer
client directory for the configured MCP server, restoring that trust record and
client configuration afterward. The execution/tool allowlist remains unchanged.
Ordinary nonzero commands are retained and can be recovered by the agent; a
terminal scope stop, missing client result or client error prevents advancing.
Recovery uses fresh scopes and preserves original source hashes and failed logs.
