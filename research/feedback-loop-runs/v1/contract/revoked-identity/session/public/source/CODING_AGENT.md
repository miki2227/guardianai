# Existing coding agents through GuardianAI

Bound Grok sessions can now require startup verification before executing any
Linux command. Pair MCP `--expected-conversation ID` with launcher
`--resume ID --require-binding`. Existing stored bindings remain required even
when that MCP flag is later omitted. See [the binding contract](FLOW.md#verify-the-cli-before-admitting-commands)
and [the real build/rejection report](research/CLIENT_BINDING_RUN.md). This trusts
the host and CLI metadata; it does not authenticate remote model weights.

`guardian_mcp.py` is a Linux MCP stdio server exposing one tool, `run`, whose
`argv` commands execute through the existing Jev/native-stack supervisor and
policy-3 kernel gate. The coding agent's model transport runs in its existing
host harness. This integration supervises tool execution; it does not put hosted
inference or a Windows client inside the Linux namespace.

Provide a dedicated public source directory, a declared task, the trusted
supervisor Jev credential and a new session directory disjoint from the source
and runtime. For example, a client's stdio MCP server command is:

```sh
python3 /path/to/guardian_mcp.py \
  --task "Review the public source and build its release; write findings to /output" \
  --workspace /path/to/public-source \
  --session /path/to/new-session \
  --sensor /path/to/strace
```

On Windows, that MCP command can be `wsl.exe -d kali-linux -- python3 ...` with
Linux paths for the arguments. Install the trusted runtime with Unix execute
permissions preserved. Python `ZipFile.extractall` does not restore the native
helper's execute bit; restore `native/notify-launch` to executable if using that
extraction method.
Forward the supervisor credential through the
trusted launcher environment, never in a prompt or literal committed config.
The contained commands receive the existing cleared environment.

For declared protected inputs, add `--flow-manifest /absolute/host/flow.json`.
[FLOW.md](FLOW.md) defines its resource paths, labels and worker/client clearances.
For a continuing peer's published text, [PEER_HANDOFF.md](PEER_HANDOFF.md) prepares
a resource with the producer's accumulated labels and a pinned byte digest.
An optional resource `sha256` is checked against the loaded snapshot before a
worker or identity session starts. The [paired run](research/PEER_HANDOFF_RUN.md)
records actual delivery to the second bound conversation.
One persistent worker label covers every fresh command in the session. Resource
exposure can therefore withhold stdout/stderr and result-history publication from
a client without clearance, then stop subsequent commands. This option is trusted
host configuration; existing callers without it retain public-only inputs.
For a continuing client crossing MCP processes, the optional `--identity-ledger`
retains labels and revocation under an exclusive host lease. Explicit `finish`
closes a local scope while retaining a resumable identity; unclean closure or a
security/operator stop revokes it. The host must bind the same path to the same
conversation. See [the identity contract](FLOW.md#continuing-one-identity-across-mcp-processes).
The [real continued-agent workflow](research/CONTINUED_AGENT_RUN.md) exercised
this setup with one retained Grok conversation. The host content observer now
receives saved `information_flow` and `identity_at_start` facts. These remain
bounded session snapshots, not direct access to the provider's hidden context.

Disable the client's other execution, filesystem, web and delegation tools.
Otherwise they can bypass this adapter. The installed Grok CLI supports
`--tools search_tool,use_tool --no-subagents --disable-web-search`; its observed
startup catalog and actual tool-use log must still be retained. Its native MCP
permission rule is `MCPTool(guardianai__run)`. The
[Grok CLI reference](https://docs.x.ai/build/cli/reference) and bundled headless
guide describe its version-dependent flags. Do not substitute an unknown tool
name: an unrecognized allowlist entry can leave the default tools enabled.

The MCP tool accepts, for example:

```json
{"argv":["/usr/bin/python3","-c","from pathlib import Path; print(Path('/workspace/source/guardian_mcp.py').read_text())"]}
```

Every command has a fresh worker namespace and empty `/output`. The public source
snapshot is at `/workspace/source`. After runtime and delivery checks, its output directory moves
into `/workspace/results/step-NNN`, read-only for subsequent commands. Copying or
editing an input source in place is unsupported; write proposed files or patches
to `/output`. This preserves useful state between tool calls without changing the
public-input policy. Each stdout/stderr response contains at most 8 KiB and an
explicit truncation flag; full output remains in supervisor evidence.

Generated text files now pass through a separate
[artifact-content gate](ARTIFACTS.md) before result-history publication. Saved
inventories link file hashes to the actual Jev content decision. Nontext files
are inventoried as opaque binaries; their meaning is not classified. Unsupported
file types or exceeded snapshot budgets abstain and stop publication.

Public-only publication rechecks broker revocation under the commit lock. An
acknowledged stop that wins before the directory rename withholds the result.
The [real cancellation and normal run](research/PUBLICATION_STOP_RUN.md) retain
both the former late-publication failure and corrected behavior.

One broker stop state and bounded session observer span the calls. A violation or
monitoring failure closes that authority for later commands. Restarting the MCP
server with the same session path fails; provisioning a new scope is a trusted
host action. The server allows at most 16 commands per scope. Commands default
to a 30-second execution deadline; the host can set `--command-timeout` up to
600 seconds for actual longer jobs. The observer's separate deadline is unchanged.
This does not establish context-window pressure.

The current MCP adapter additionally sends proposed argv to `AgentObserver`
before execution and returned tool content before delivery. A flag or observer
fault revokes the session. Inputs, content chunks and three Jev scores are retained
under `evidence/_content/`. The existing syscall observer remains active.
The [combined workflow report](research/CONTENT_OBSERVER_RUN.md) records actual
operation and its limits.

The gate emulates a missing private NSS service for the two exact pathname
sockets `/var/run/nscd/socket` and `/run/nscd/socket`. It returns `ENOENT` without
executing a connection; other connection requests still stop the scope. This
lets ordinary metadata listing fall back to numeric identities. The
[real-command replay](research/NSS_COMPATIBILITY_RUN.md) retains both native
notification records and the optional `connect_disposition` evidence field.

`run_grok_guarded.py` launches the existing Windows Grok CLI, pinned to the
previously requested `grok-4.7` and low effort, with only MCP meta-tools. It polls
the session report and terminates the local CLI when the Linux scope stops. Its
required arguments are `--grok`, `--client`, `--prompt`, `--report` and `--evidence`;
the client directory must already contain the configured MCP server. `--report`
is the host-visible path to the new session's `evidence/coding-session.json`.
Optional `--resume` continues an existing Grok conversation under a newly
provisioned scope. The launcher limits a run to 12 model rounds and ten minutes.
Its environment disables workflows, memory and compatibility discovery for that
process. User authentication remains with the existing Grok installation.

The host launcher now observes its supplied prompt and complete emitted assistant
messages, including exposed thinking/text/tool-request blocks, under
`agent-content/` in launcher evidence. It does not access hidden provider reasoning
or reconstruct the pre-existing history of a resumed conversation. These checks
are post-emission; the CLI may already have dispatched a tool. The separate MCP
argv check is the pre-execution content gate. Tool results are checked inside MCP.
A host observer stop writes `external-stop.json` in the trusted Linux evidence
directory; the MCP watcher revokes the broker and the host terminates the local
CLI. The content observer uses the provider client's 20-second HTTP timeout per
chunk, not the syscall observer's two-second completion contract. Full details
and remaining gaps are in [PROJECT_DIRECTION.md](PROJECT_DIRECTION.md).

The host harness and launch configuration are trusted. A poll failure can delay
client termination; the stopped Linux broker still refuses subsequent commands.
Supported guarded launches now use a guard-version-1 native helper and strace
`--kill-on-exit` to bind local worker execution to the supervising Linux thread's
lifetime. See the [real build/cancellation run](research/OWNER_LIFETIME_RUN.md).
This requires the trusted nonprivileged tracer path; abrupt death can still leave
an incomplete final closure record.
Terminating the local client cannot recall released data or cancel inference
already running at the provider. Session IDs and usage totals alone do not prove
retained-token occupancy, compaction or long-context failure.

The [observer timing fields](research/OBSERVER_TIMING_RUN.md) distinguish call
completion from later consumption, expose deadline/application status, and join
each response to its saved runtime event batch. They use each worker's elapsed
clock; they are not provider latency or a shared cross-worker clock. Late completed
responses are rejected under the existing two-second observer-call budget.

The current semantic policy preserves 0.5 as the alert threshold and requires a
second contextual Jev decision before stopping for that alert. Content review
uses the complete current message, rather than just the triggering chunk, if it
fits the 20 KiB state limit. Runtime and release review use the available task,
batch and shared facts. Initial scores, `confirmation` receipts and final review
decisions are retained. `review_cleared` continues ordinary work. A confirmed
violation, invalid/missing result, oversized review or missed deadline stops the
scope; deterministic kernel rules do not wait for semantic confirmation. The
second call is not an independent-model vote, and accuracy remains uncalibrated.

Use `"finish": true` alongside `argv` on the last MCP command. After its result
has been inspected, the server revokes authority and persists `closed: true`.
Later commands are refused. Give the final model answer without further tool
calls. Without explicit finish, EOF/SIGTERM still attempts normal closure, but
abrupt process death can leave an incomplete record. Closed/revoked after a
successful final call is ordinary completion, not a threat verdict.

A host stop now writes a unique request ID and waits up to two seconds for the
matching `external-stop-ack.json` before terminating the local client. The broker
persists its stopped snapshot before that acknowledgement. The launcher stores
`stop-control.json` and reports missing acknowledgements explicitly. A broker
acknowledgement alone does not assert that every worker has exited; runtime
actions and process evidence establish that separately. The
[correction run](research/OBSERVER_CORRECTIONS_RUN.md) records normal completion,
actual build cancellation and the original failures unchanged.

The current observers also [retrieve older retained evidence](HISTORY.md) through
SQLite FTS5. Saved `history_retrieval` fields expose source hashes, character spans
and omitted-match counts. Per-scope indexes are the default. A trusted launcher
can pass `--history-root` for an existing dedicated parent of its current and
earlier evidence directories; source files must remain unchanged and available.
This does not reconstruct unexposed model history or change current grants.
