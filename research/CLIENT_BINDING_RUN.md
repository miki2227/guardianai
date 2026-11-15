# CLI verification before command admission

Bound MCP sessions now wait for a trusted launcher to approve a fresh private
challenge after matching the resumed CLI's startup conversation ID. The gate acts
before a command worker is created. Omitting the flag later cannot disable a
binding already stored in the ledger. This is a local CLI/host contract, not
cryptographic authentication of a remote model provider.

## Real continued work

The [controller](binding-runs/v1/run_workflow.py) resumed the existing builder and
reused its actual previous ledger. It retained the internal-baseline labels and
all earlier exposure records. Two guarded Linux commands built the new release
and wrote a binding note; both exited zero with `no_observed_violation`. There
were no new protected reads, and the scope closed cleanly. Original client
configuration bytes were restored.

The [audit](binding-runs/v1/audit.json) joins the startup ID, private approval and
native challenge. The server's verification timestamp precedes both command
admissions on the same Linux clock. These timestamps establish ordering, not
measured latency. The actual package/member hashes match the source snapshot.

The [new core package](binding-runs/v1/session/public/results/step-001/GuardianAI-linux-x86_64.zip)
has 19 members, native policy 3 and launch guard 1. SHA-256:

```text
eab18c1f58e751fba5142988ed885c2c44df7f0b797546f95a8cdc561dc0e97b
```

## Real MCP rejection checks

The [admission controller](binding-runs/v1/rejected_admissions.py) used isolated
copies of the completed ledger, leaving the real conversation ledger unchanged.
It requested ordinary source-checksum work through actual MCP subprocesses:

- A different expected conversation was refused during startup; the ledger was
  byte-identical afterward and no worker was created.
- Omitting the flag retained the stored binding; absent launcher approval, the
  command was refused and the scope closed.
- Replaying the earlier session's approval failed the fresh challenge; the
  command was refused and the scope closed.

These three deliberate access-control cases executed zero worker commands. They
are not spontaneous model acts, detector-accuracy estimates or evidence of
malicious intent. Requests, responses, stderr and ledger copies are retained.

## Remaining boundaries

The host still owns the canonical ledger path, client configuration, transport
and private approval directory. Uncooperative host writers can bypass this trust
contract. The metadata does not attest remote weights or expose private thoughts.
Missing/invalid approval fails closed after a bounded wait, so scheduling delays
can reject legitimate work. Unbound public sessions retain their explicit mode;
bound ledgers require fresh approval on reopening. Other semantic/confidentiality
gates remain active after admission.

The IEEE paper remains pinned to its earlier case revisions with its user-supplied
front matter unchanged. Its verifier now reads implementation bytes at that
explicit Git revision, rather than mistaking current HEAD for the earlier tested
runtime. This run is an additional result, not a retroactive change to those cases.
