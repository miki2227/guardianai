# Persistent confidentiality labels

`flow_policy.py` adds an optional deterministic gate to mediated text handoffs.
Jev still evaluates admissible content. The trusted coordinator separately
requires sender possible-exposure labels to be a subset of recipient clearance.
A prohibited handoff stops the shared scope before publication. This tracks
confidentiality metadata; it does not infer malicious thoughts.

## Integration contract

Use one `FlowPolicy` instance in one trusted coordinator process. Its lock covers
threads in that process; concurrent processes writing the same ledger are not
supported. Create the ledger's parent directory first. For example:

```python
flow = FlowPolicy(
    ledger_path,
    {'builder': ['internal'], 'reviewer': ['internal'], 'public': []},
    {'baseline': ['internal']},
    on_stop=broker.revoke,
)
broker.exposure = flow.expose
```

The broker calls `expose(principal, resource_id, sha256)` before committing
protected bytes. It then rechecks the deadline and current authorization. Supply
`flow_context=flow.exposure_context` to `SessionObserver` so Jev receives actual
exposure facts. Configure content-observer stopping to call `flow.stop`, and use:

```python
receipt = deliver(observer, sender, recipient, artifacts, destination, flow=flow)
```

See the [actual coordinator](research/flow-runs/v3/workflow.py) for complete wiring.
The MCP entry point enables it with an explicit trusted `--flow-manifest`; see
the configuration below. Existing callers without that option remain untracked.
Calls to `deliver` without a policy explicitly record `mode: untracked`.

The host owns subject identities, resource classifications, clearances and paths.
For continuing models, bind commands, conversations and handoffs to the same
stable subject and retain its ledger. Private prompts or inputs outside the
broker require a trusted exposure checkpoint before delivery too. The policy does
not discover them automatically. Task changes and grant revocation do not erase
accumulated labels. There is no semantic declassification.

## Ordering and receipts

Possible exposure is saved before protected-byte commit. Recipient labels are
saved before handoff publication. These conservative checkpoints can overlabel a
subject if delivery fails. Already delivered bytes cannot be recalled. Publication
failure stops the scope but may leave partial authorized output.

The handoff receipt written during publication records `stage: commit_prepared`.
Use the final ledger's `stage: committed` to establish completion. Reopening a
ledger with an unfinished prepared transfer stops it. Hard clearance denials have
`observer_sequence: null`; Jev cannot override that boundary. Reasons distinguish
`recipient_clearance` from a later `scope_stopped` refusal.

The ledger uses atomic file replacement, not a signed journal or power-loss
durability protocol. Host integrity, directory ownership and a single writer are
assumptions. Checkpoint disk I/O happens inside commit locks and can delay stop
processing; this is not a hard real-time implementation.

## Scope

All output from a labelled subject inherits possible exposure, even when its
literal text appears harmless. This coarse rule can block useful public work.
The generic `deliver` helper guards selected text artifacts, not binary handoffs.
The MCP integration below gates the entire worker output directory, including
binary files such as a release ZIP. It does not semantically inspect arbitrary
binary contents; its content checks cover the serialized tool response and
[generated text artifacts](ARTIFACTS.md), including bounded decoded ZIP text.
Nontext leaves retain opaque inventory entries and the same confidentiality
publication gate. Archive interpretation never removes accumulated labels. Arbitrary
hosted-model final chat, unmediated files, timing, termination and hardware side
channels remain outside these interfaces.
It does not label facts inferred entirely from public inputs.

The [real build/index run](research/FLOW_POLICY_RUN.md) records permitted and
prohibited handoffs, retained failures and precise enforcement limits.

## Coding-agent MCP sessions

Pass `--flow-manifest /absolute/host/flow.json` to `guardian_mcp.py`. It accepts:

```json
{
  "resources": {
    "baseline": {"path": "/private/previous-release.json", "labels": ["internal"]}
  },
  "worker_clearance": ["internal"],
  "client_clearance": []
}
```

Paths are absolute Linux host paths outside source, runtime, session and system
mounts. Resources use the existing 32 KiB immutable broker snapshots. The trusted
task must authorize their use; a grant does not bypass Jev. Never let a model
choose the manifest, clearances, resource paths or its session's identity.

A resource may additionally contain `"sha256": "<64 lowercase hex characters>"`.
The MCP server checks this expected digest against its loaded byte snapshot
before creating a worker or opening its identity session. A mismatch refuses
startup. Unpinned existing manifests remain supported. The trusted host owns
the expected digest as well as the manifest; this is not a signed attestation.
[Peer preparation](PEER_HANDOFF.md) emits a pinned resource whose classification
comes from the producer's saved possible-exposure labels, rather than placing
that publication among the next agent's assumed-public source files.

All fresh command processes map to one persistent `coding-worker` subject in
that session. Actual resource exposure checkpoints that subject before delivery.
`coding-client` is the external coding agent receiving tool results. A protected
read taints subsequent command results too; spawning another command does not
clear it. Successful delivery propagates the label to the client. To authorize an
internal client, explicitly include `internal` in its clearance. That authorizes
the external model provider to receive the data; it does not contain its later
chat or remote inference.
Jev's hosted endpoint remains a trusted recipient of submitted observer evidence;
the client-clearance gate does not restrict what the trusted observer is shown.

Both stdout/stderr delivery and publishing `/output` into later commands' result
history wait for the runtime outcome, recipient clearance and content check.
On a hard denial neither is published. Only execution/verdict metadata and the
denial are returned; original output stays in the private host session directory.
Subsequent commands are refused. A semantic stop also withholds result history.
Runtime violation or abstention withholds stdout/stderr and result history even
without a flow manifest. Ordinary nonzero exits with complete, unflagged evidence
can still return diagnostics.

The final ledger is `session/evidence/flow-policy.json`. Kernel principals remain
`step-NNN`; their exposure callbacks map to `coding-worker`, with resource hashes
retained on both sides. Labels persist within this MCP session, not across newly
created sessions unless the persistent identity option below is used. Existing public source
and copied inputs are assumed public; private data placed there bypasses this
declared-resource registration contract. This is a trusted-host boundary, not
automatic classification of every byte an agent may encounter.

## Continuing one identity across MCP processes

For the same continuing client, add
`--identity-ledger /private/agent-identity/flow.json` alongside `--flow-manifest`.
Create its private parent directory first. The ledger must be outside every
worker/session/runtime mount. Use native Linux storage and one canonical path.
The CLI holds an exclusive nonblocking Linux `flock` on a stable `.lock` sidecar
for its entire server lifetime. Locking the JSON file itself would be insufficient
because saves replace that file. A concurrent server using the same identity is
refused before it creates its session. The sidecar's mere existence is not proof
that an owner is running. Never unlink it while an owner may be active.

The trusted host must bind this path to the actual continuing conversation and
reuse it consistently. It is not authentication of a provider conversation ID.
Changing the path, deleting the ledger, copying it under another lock path or
mixing unrelated clients can defeat that binding. Direct Python callers must hold
`identity_lease` around the entire `CodingSession` lifetime; the CLI does this.
Labels and clearances must match the existing policy exactly on reopening. The
feature provides no policy migration, automatic reset or declassification.

With this option, an explicit successful `finish: true` closes the local broker
but keeps the identity resumable with its labels. No later command can run in
that closed local scope. A semantic/runtime/flow stop or external operator stop
revokes the persistent identity. A subsequent server inherits that stop and
refuses work; a new process is not a reset.

The ledger records an active session before commands are accepted and clears it
only on clean explicit completion. EOF or an exception before explicit completion
revokes it. An abrupt process death leaves its marker: the next opener stops the
identity conservatively.

The [real crash-recovery run](research/REAL_SYSTEM_VERDICT.md) now verifies one
live release-worker exit and failed identity resumption after supervisor SIGKILL.
It does not establish every crash timing or power-loss behavior.
Atomic replacement is still not an fsync/power-loss
durability guarantee, and the advisory lock assumes cooperating trusted local
processes. Uncooperative host writers and remote filesystems are outside the
contract. Ledger history can grow; no retention policy silently drops labels.

`coding-session.json` records the ledger path and `identity_at_start` labels,
stop/active state and history counts, alongside current flow facts. A clean local
scope can therefore have `scope_stopped: true` while the persistent identity is
resumable. Consumers must distinguish these two lifetimes. Old per-session mode
continues to stop its local ledger at closure.

## Verify the CLI before admitting commands

For the existing Grok adapter, add `--expected-conversation ID` to the MCP server
and `--resume ID --require-binding` to `run_grok_guarded.py`. The server creates a
fresh challenge in its private evidence directory. The launcher reads matching
CLI system-init metadata and atomically writes a scoped approval. Before creating
a command worker, the server checks the ID and request nonce. Missing or invalid
approval stops the scope after a bounded two-second wait. There is no Jev override.

The first binding is retained in the identity ledger. A different expected ID is
rejected, and omitting the flag cannot disable a stored binding. Each new server
needs a new approval; the previous file cannot satisfy its nonce. The lease and
existing exposure labels remain in force. Default public sessions without a
binding remain explicitly unbound.

This verifies trusted local CLI metadata, not a remote provider signature. The
host must still choose the correct canonical ledger and protect its approval
directory. Scheduling delays can cause a safe refusal. See the
[actual continued build and rejected admissions](research/CLIENT_BINDING_RUN.md).
