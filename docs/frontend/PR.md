# Add a local recorded-run viewer with audited multi-agent evidence

GuardianAI's retained runs now have a local interface for presentation and
inspection. The default view shows the completed Checkstyle workflow with two
continuing Grok subjects, nine commands and two artifact handoffs. Command
selection joins only the exact worker's runtime and manifest; missing evidence
cannot borrow another worker's events or decisions.

The viewer exposes native syscall stacks, Jev receipts and input references,
phase-level message observation, stdout/stderr, lifecycle state, saved host
audits, handoffs and local file downloads. Historical policy-stop, timeout and
owner-cancellation examples remain available. Imports stay in the browser and
skip unsupported binary/oversized files with visible notes. There are no live
execution controls.

Validation: clean `npm ci`, seven adapter/integrity tests, TypeScript and
production build pass. All 189 new bundled artifacts match source bytes and
SHA-256 receipts. Chromium checks covered default rendering, exact Jev input
references, output, cancellation and folder import; desktop and 390px mobile
views have no page overflow or recorded browser errors. Resolved dependency
audit reports zero known vulnerabilities. Screenshots and setup instructions
are in `docs/frontend`.

The separate large-context attempt is retained with its raw evidence and audit:
nine commands completed, then the reviewer's tenth worker abstained on a
supervisor fault and broker revocation was acknowledged. That experiment did
not complete the planned hour or establish context-window exhaustion. No covert
convention, malicious intent or P0 is claimed. Original quarantine is unchanged.
The offline evidence makes the bundle about 1.65 MB before compression; extended
flow/identity/SQLite schemas are not fully reconstructed by the viewer.
