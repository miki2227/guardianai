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
Existing MCP/hosted-agent entry points do not automatically enable this policy.
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
