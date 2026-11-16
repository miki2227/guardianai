# CLI tool-result observation

The host launcher now passes CLI `user` blocks of type `tool_result` to
`AgentObserver` as `delivered_tool_result`. Previously that branch observed only
assistant text, exposed thinking and tool requests. MCP command output already
had its own pre-delivery check, but the host journal omitted the CLI's tool replies,
including tool discovery results. The new adapter retains all fields of those
blocks, including content, tool-use ID and error status. A refusal uses the same
launcher stop branch as an assistant-message refusal.

## Actual retained-message replay

[replay.py](tool-result-runs/v1/replay.py) used the exact saved correction-phase
stream from the continued-agent case. It invoked the production adapter and live
`jev-1.14.0`, preserving message order and the original task. It did not start a
Grok client, MCP process or worker. The historical builder was not resumed.

The [audit](tool-result-runs/v1/audit.json) verifies 12 content records: the prompt,
six assistant messages and five tool-result messages. Those results include the
actual `search_tool` discovery response and four `use_tool` replies. Their
serialized blocks occupy 16,237 UTF-8 bytes. Seventeen live chunk calls all
returned `not_flagged`; the maximum individual question probability was 0.41.
There was no confirmation call or observer stop. This is not an accuracy sample.

The audit joins original stream line numbers, exact blocks, content hashes,
preceding-content links, input hashes and complete overlapping chunk spans. It
also verifies the unchanged assistant projection. Both source files are pinned
by SHA-256 in the saved result. Runtime source copies and all Jev inputs and
answers are retained under [run](tool-result-runs/v1/run/result.json).
The canonical builder ledger hash remained
`79da2bf50b7d623a3bd9cbdab1fad63209b388a0d03b3454f8bb92a2509a2c79`;
its persistent revocation was not changed.

## Boundaries

This is live observer inference on historical real messages, not a newly
completed coding-agent workflow or validation of spontaneous covert coordination.
The replay has its own empty recent-history index and explicitly retrospective
execution context; its scores cannot be treated as the original run's decisions.
No stop or process termination occurred in this replay. The shared stop branch
is an implementation fact, not a new stop-latency measurement.

CLI replies have already reached the agent when the launcher reads them. The
existing MCP boundary remains responsible for checking command results before
delivery. Hidden history, private thoughts, unexposed tool traffic, unknown block
types and binary contents remain outside this text adapter. This change does not
authenticate a remote provider or enforce all possible communication channels.

Run `python research/tool-result-runs/v1/audit.py` to verify retained joins. The
replay controller refuses to overwrite its run folder; rerunning inference would
be a new experiment with new responses, not a refresh of this evidence.
