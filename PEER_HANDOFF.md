# Protected handoff between continuing coding agents

`peer_handoff.py` prepares a selected producer publication as a protected input
for another bound conversation. It derives the resource classification from the
union of the producer's `coding-worker` and `coding-client` exposure labels.
The host explicitly chooses the recipient and its clearance. Jev reviews the
admissible text; it cannot override a clearance refusal.

This closes a specific integration gap: copying a labelled agent's output into
the recipient's public source tree would bypass the declared-resource contract.
Do not perform that copy. Prepared bytes remain in private host storage until
the kernel broker mediates an authorized read.

## Trusted plan

Create private parent directories for both ledgers first. Use absolute native
Linux paths, distinct canonical ledger paths, a completed producer session and
a new recipient session. For example:

```json
{
  "task": "Relay the internal release report to the authorized reviewer",
  "producer_ledger": "/private/builder/flow.json",
  "producer_session": "/private/build/session",
  "producer_conversation": "existing-builder-id",
  "recipient_ledger": "/private/reviewer/flow.json",
  "recipient_conversation": "existing-reviewer-id",
  "recipient_clearance": ["internal"],
  "workspace": "/public/source",
  "session": "/private/review/session",
  "artifacts": ["/private/build/session/public/results/step-001/build-report.json"]
}
```

An optional `recipient_resource` selects the recipient's existing resource ID.
It defaults to `peer_handoff`. For example, a continuing builder whose saved
policy has only `previous_release` can receive a peer snapshot in that slot by
setting `"recipient_resource": "previous_release"`. The receipt records this ID.
The full saved policy must still match; this does not add resources, expand
clearance or reset labels. Existing multi-resource policies are not migrated by
this helper. A stopped identity remains stopped.

Run from the trusted host, with the existing Jev environment credential:

```sh
python3 /runtime/peer_handoff.py --plan /private/plan.json --evidence /private/new-handoff
```

Both ledger leases are held during preparation. The producer must be healthy,
cleanly closed and bound to the declared conversation. Its completed session
must carry a verified client binding and reference that same ledger. Artifacts
must be distinct regular UTF-8 files under that session's published results.
Individual text snapshots are at most 32 KiB; the entire serialized resource,
including provenance, must fit the broker's 32 KiB limit. Binary relay is outside
this helper's scope. Existing MCP output publication still gates binary files.

## Preparation and delivery

If producer labels exceed recipient clearance, the helper writes a refusal
receipt and exits 77 before reading artifact contents or calling Jev. It does
not create a recipient ledger or payload. This is an offline host-plan refusal;
there is no active recipient thread to terminate at this stage.

On success it writes `peer-resource.json`, `flow-manifest.json` and `receipt.json`.
The JSON payload contains artifact text, individual hashes, both conversation
IDs, inherited labels and the source-ledger hash. The generated flow manifest
pins the complete payload SHA-256. Use that manifest with the normal MCP
`--identity-ledger` and `--expected-conversation` options, plus launcher
`--resume ... --require-binding`. Tell the recipient only the approved resource
path `/protected/RESOURCE_ID` (`/protected/peer_handoff` by default); do not paste
its contents into the prompt. These paths are virtual brokered snapshots. Read
the explicitly approved path directly; `stat`, `exists` or `is_file` cannot
establish availability, and the resource is not a directory to probe for children.

Preparing the resource does not mark the recipient exposed. The existing
broker checkpoints exposure before a committed read; tool-result delivery
then propagates labels to the coding client. MCP startup compares the pinned
digest with the loaded snapshot. A changed payload is refused before worker
creation. Once loaded, the broker uses its immutable snapshot.

A content-observer stop during preparation persists revocation on both offline
identities. A successful preparation alone does not establish recipient
consumption or completed task work; join its digest to actual broker commits
and the recipient ledger. See the [real run](research/PEER_HANDOFF_RUN.md).

## Assumptions and bounds

The host, manifest, ledger mapping, published files and CLI startup metadata
remain trusted. Hashes establish byte identity relative to that configuration;
they do not authenticate a remote provider or prove the truth of an agent's
report. Labels are conservative metadata, not inferred intent. The host must
classify earlier private inputs and route later outputs through the same gates.
The two endpoint providers and Jev receive authorized content outside the Linux
namespace. Each invocation prepares one directed transfer; the selected slot
permits return feedback while preserving an existing policy. The
[first feedback-cycle attempt](research/FEEDBACK_LOOP_RUN.md) remains incomplete
after an agent's invalid child-path read triggered persistent revocation. This
is not a general message bus or coverage of timing, termination and other covert
channels.
