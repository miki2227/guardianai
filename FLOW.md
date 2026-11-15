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
It guards this mediated text interface, not arbitrary hosted-model final chat,
unmediated files, binary outputs, timing, termination or hardware side channels.
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

All fresh command processes map to one persistent `coding-worker` subject in
that session. Actual resource exposure checkpoints that subject before delivery.
`coding-client` is the external coding agent receiving tool results. A protected
read taints subsequent command results too; spawning another command does not
clear it. Successful delivery propagates the label to the client. To authorize an
internal client, explicitly include `internal` in its clearance. That authorizes
the external model provider to receive the data; it does not contain its later
chat or remote inference.

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
created sessions or arbitrary resumed model conversations. Existing public source
and copied inputs are assumed public; private data placed there bypasses this
declared-resource registration contract. This is a trusted-host boundary, not
automatic classification of every byte an agent may encounter.
