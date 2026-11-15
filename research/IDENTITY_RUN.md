# Continuing exposure labels across MCP server processes

Date: 2026-11-15. An optional host-owned `--identity-ledger` now carries exposure
labels and revocation across coding-agent MCP server processes. It is paired with
the trusted flow manifest. The [configuration contract](../FLOW.md#continuing-one-identity-across-mcp-processes)
defines ownership, explicit closure and the exclusive sidecar lease.

The host binds one canonical ledger path to one continuing conversation. This is
not provider identity authentication or automatic discovery of a model's memory.
Direct Python callers must hold the same lease for their session's lifetime.
Policy labels and clearances must match on reopening. There is no silent reset,
policy migration or declassification.

## Implemented lifetime separation

A local MCP scope closes after successful explicit `finish: true`. Its broker
stays stopped, while its persistent identity retains labels and can resume under
a new server process. A semantic, runtime, flow or operator stop instead persists
identity revocation, which a new process cannot clear.

An active-session marker is checkpointed before commands are accepted. Explicit
clean completion clears it. Unclean EOF/exception stops the identity; a marker
left by abrupt death causes the next opener to stop it. This is an implementation
argument, not a measured abrupt-death recovery result. File replacement is not
fsync/power-loss durability. Locks assume cooperating trusted processes on native
Linux storage; deletion, alternate lock paths or uncooperative host writers can
defeat that assumption. The history grows rather than silently dropping labels.

## Actual useful work

The [recorded MCP coordinator](identity-runs/v1/workflow.py) ran fixed useful Linux
commands over actual stdio. It did not launch new model subjects. The protected
input was real previous-release metadata assigned a controlled
`internal-baseline` classification, not an actual private-data breach.

1. **Index:** a command read the approved previous-release manifest through the
   kernel broker and produced an internal source-change index. The internal
   client received it. Explicit closure left both worker/client labels intact
   and the persistent identity resumable.
2. **Build:** a new MCP server reused that ledger and built the current release.
   It added no protected read. The build's startup record already had the label;
   all 51 saved runtime-observer inputs contained it. Its delivered report
   inherited the label, and explicit closure again left the identity resumable.
   While this server was live, another server tried the same identity and failed
   at the exclusive lease before creating a session or executing any command.
3. **Verify and stop:** another resumed process verified the current MCP source's
   checksum. The operator then requested a stop. The request-linked broker
   acknowledgement was saved, and the next checksum request was refused.
4. **Revoked resumption:** a later server reopened the same ledger. It inherited
   revocation and refused its first command, with no execution/evidence directory.

Three Linux commands completed with exit zero and `no_observed_violation`; four
ordinary MCP conversations were recorded, plus the refused contending startup.
There was one protected resource commit, in the index phase. No worker was active
at the operator stop, so this run does not add an in-flight process-kill result.
The [earlier cancellation evidence](OBSERVER_CORRECTIONS_RUN.md) remains separate.

## Evidence audit

The [audit](identity-runs/v1/audit.json) and
[audit script](identity-runs/v1/summarize.py) join actual request/response IDs,
startup label/history counts, kernel commit hashes, per-session ledger snapshots,
the operator request/acknowledgement and the delivered build manifest. The build
has no resource-commit event and no new exposure entry, so its inherited label
is not explained by a fresh protected read. The contender's recorded owner
process was live; a leftover lock file alone is not used as ownership evidence.

Each successful phase's `identity-after.json` preserves its actual ledger after
server exit. These are explicit copies of the host-owned ledger, not invented
replays. The `coding-session.json` local scope can be closed/stopped while its
identity snapshot is resumable. Viewers must distinguish those lifetimes.

The [supervised package](identity-runs/v1/build/session/public/results/step-001/GuardianAI-linux-x86_64.zip)
has 19 members, native policy 3 and launch guard 1. Its source/member hashes were
verified. SHA-256:

```text
58b9d4d13785546f2367477e00e39419f00d1865d98a6eb26086a948e09e5502
```

This is host-bound continuity plumbing based on established persistent
information-flow ideas, attributed in the [prior flow report](FLOW_POLICY_RUN.md).
It does not establish model-agent misalignment, spontaneous covert coordination,
private-thought access, context saturation, all recovery paths or automatic
identity binding for a resumed hosted conversation. Historical semantic evidence
is not automatically merged into the new server's observer history; this feature
preserves confidentiality labels rather than all earlier traces.

Publishing these experimental metadata/source artifacts to Git is a trusted-host
evidence export outside the MCP boundary. It does not demonstrate enforcement on
the repository publisher or authorize export of genuinely confidential inputs.
