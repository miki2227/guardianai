# Real Grok coding-agent integration

15 November 2026. The installed Windows Grok Build 1.0.77 ran a useful repository
review and Linux release-build task through the new GuardianAI MCP command tool.
This was one conversation, requested as `grok-4.7` with low effort, continued
across four explicitly provisioned Linux tool scopes. No other model was
substituted, no subagents were spawned and no attack/test suite was added.

The Windows harness handled model transport and remained outside Linux
containment. Each actual command ran through GuardianAI's namespace, native
notification gate and Jev observer. All four retained startup catalogs expose only
`search_tool` and `use_tool`; actual recorded model tool uses are limited to those
names, and the dispatched integration tool is `guardianai__run`.

## Retained outcomes

| Invocation | Actual outcome |
|---|---|
| Initial | `ls -la` attempted `/var/run/nscd/socket`. The strict all-connect rule stopped the namespace and the host launcher terminated Grok. This is a benign compatibility failure, not malicious intent. |
| Resumed source review | Ten commands completed with recorded captures, then the client hit its 12-model-round limit without building the package. |
| Resumed build | The command abstained at the original 30-second execution deadline. Earlier Jev decisions were below threshold. |
| Completion | With a host-selected 90-second command budget, the same conversation built the release, inspected its manifest/native ABI, and wrote an inventory and review. Four commands completed and the client exited 0. |

There were 16 command attempts in total: 14 completed with exit 0 and
`no_observed_violation`, one policy stop and one deadline abstention. The successful
build's recorded execution time was 36.937443562 seconds. This motivates the
trusted command-budget option; the separate observer deadline was not changed.
The later run is not a matched causal comparison of timeout settings or detection
accuracy.

All final scoped event revisions from successful commands match retained submitted
inputs, whose hashes were checked. Shared observer state/decision receipt hashes
also match. These are artifact consistency checks, not proof of complete capture.

Grok's teardown did not leave a final `closed: true` snapshot in these tool scopes.
The added SIGTERM handler does not establish cleanup for the client's observed
teardown path. A later process inspection found no running `guardian_mcp.py`
server; that observation is not a general lifecycle guarantee. The incomplete
closure records are retained. An existing session directory cannot be reused to
silently revive its scope.

## Context measurements and limits

The raw JSONL contains 22 assistant-message usage records and one conversation ID
across the four invocations. The largest reported full input is 44,148 tokens,
computed as uncached input plus both cache buckets. The cached harness catalog
advertises a 256,000-token window for the requested alias; it is not an independent
capacity measurement for the serving backend. No context-exhaustion result is
claimed.

Persisted usage reports primary model `grok-4.7-build`, while startup/message
records label it `grok-4.7`. Both literal identifiers are retained rather than
silently equated to a pinned executed snapshot. The persisted aggregate covers
18 model calls and two ended prompts, and omits the interrupted invocations. Its
409,160 input tokens are a sum over calls, not window occupancy. No compaction
event is exposed in the retained JSONL; that absence does not establish that no
internal compaction occurred.

## Artifacts

- [Summary and per-round usage](coding-agent-runs/grok-v1/summary.json)
- [Persisted usage export](coding-agent-runs/grok-v1/persisted-usage.txt)
- [Agent review](coding-agent-runs/grok-v1/session-completion/public/results/step-004/agent-review.md)
- [Package inventory](coding-agent-runs/grok-v1/session-completion/public/results/step-004/package-inventory.json)
- [Integration instructions](../CODING_AGENT.md)

The agent explicitly states which revisions/sections it read and that inventory
hashes were copied from the build manifest. The host separately recomputed archive
and member hashes and matched packaged Python/C sources to the checkout. The
delivered [archive](../dist/GuardianAI-linux-x86_64.zip) has SHA-256
`2c02bbc4223ce2a61300735209a3e2848c22f0e9d799bf25c088066222a65cdb`.
The retained run files were checked for the configured Jev credential value; it
was absent. This does not claim a general secret-scanning guarantee.

This establishes a working existing-agent integration with real tool execution,
continued interaction and reported usage. It does not establish spontaneous
misalignment, collusion, natural context saturation, detection recall or
publication-level novelty.
