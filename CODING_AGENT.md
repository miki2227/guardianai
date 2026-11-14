# Existing coding agents through GuardianAI

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
Linux paths for the arguments. Forward the supervisor credential through the
trusted launcher environment, never in a prompt or literal committed config.
The contained commands receive the existing cleared environment.

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
snapshot is at `/workspace/source`. After completion, its output directory moves
into `/workspace/results/step-NNN`, read-only for subsequent commands. Copying or
editing an input source in place is unsupported; write proposed files or patches
to `/output`. This preserves useful state between tool calls without changing the
public-input policy. Each stdout/stderr response contains at most 8 KiB and an
explicit truncation flag; full output remains in supervisor evidence.

One broker stop state and bounded session observer span the calls. A violation or
monitoring failure closes that authority for later commands. Restarting the MCP
server with the same session path fails; provisioning a new scope is a trusted
host action. The server allows at most 16 commands per scope. Commands default
to a 30-second execution deadline; the host can set `--command-timeout` up to
600 seconds for actual longer jobs. The observer's separate deadline is unchanged.
This does not establish context-window pressure.

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
