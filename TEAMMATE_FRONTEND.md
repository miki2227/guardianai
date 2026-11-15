# Independent teammate task: recorded-run evidence viewer

Copy the following prompt to your teammate. The backend work remains with the
runtime owner; the viewer is a separate frontend contribution.

---

Work on `frontend/recorded-run-viewer`, branched from the latest `master` of
`https://github.com/miki2227/guardianai`. Build a local, read-only frontend for
GuardianAI's recorded execution evidence. Use `frontend/` as your implementation
directory. React, TypeScript and Vite are a suitable small starting point; there
is no existing frontend framework to preserve. Make a PR when ready.

The purpose is to make an actual supervised run understandable: what work was
requested, which Linux commands ran, what the observer received and decided,
which operation was blocked, and whether termination or a capture problem
occurred. This is a research console, not a marketing page.

## Ownership boundary

- Edit only `frontend/**` and optional `docs/frontend/**`.
- Read the Python/C runtime, research reports and datasets as references. Do not
  change them, their schemas, existing evidence, root dependencies or manifests.
- Implement parsing adapters in the frontend so runtime work can continue
  independently. Document unsupported/missing fields instead of changing backend
  files to fit the UI.
- Do not create an execution/control API, deploy the site, add authentication,
  contact external services, or expose API keys. A live stop button would require
  a separate backend contract; do not simulate one.

## Start from actual data

Read `CODING_AGENT.md`, `research/CODING_AGENT_RUN.md` and
`research/OWNER_LIFETIME_RUN.md`. Use these retained examples:

1. `research/coding-agent-runs/grok-v1/summary.json` and its four scope directories:
   a benign name-service policy stop, a round-limit exit, a timed-out build and a
   completed build/review.
2. `research/system-runs/owner-lifetime/summary.json` and `cancellation.json`:
   ordinary build completion versus a deliberately cancelled real build. The
   cancelled run has no runtime verdict; show that missing state honestly.
3. `research/system-runs/shared-context-build/evidence/`: multiple workers and
   shared observer receipts.
4. `research/content-observer-runs/v1/summary.json`, `client-run/agent-content/`
   and `session/evidence/_content/`: prompt/assistant-content and tool-input/result
   decisions alongside the Linux evidence. Follow `PROJECT_DIRECTION.md` and
   `research/CONTENT_OBSERVER_RUN.md` for the current undergraduate project scope.
   Content `flagged` is a suspicion verdict, not proof of a covert convention;
   host message checks occur after emission. The two journals have separate order.
5. `research/paired-workflow-runs/v1/summary.json`: two continuing conversations,
   retry scopes and peer handoffs. The workflow is incomplete: show the content
   stop, empty response file and unrun final phase. The follow-up runtime kill
   and unmonitored developer build are distinct cases; see
   `research/PAIRED_WORKFLOW_RUN.md`. A stop-request file is not a broker
   acknowledgement, and an exit-zero client can still have an error result.
6. `research/paired-workflow-runs/v2/summary.json` and its cancellation folders:
   completed four-phase work, explicit final-command closure, `review_cleared`
   decisions and request-linked stop acknowledgements. Preserve initial and
   confirmation scores separately. A successful finish has `scope_stopped: true`
   and `closed: true`; that is not automatically a threat. Broker acknowledgement,
   namespace kill, worker exit and client exit remain distinct observations.
7. `research/history-retrieval-runs/v1/live-summary.json` and the saved
   `history_retrieval` inputs: older source excerpts, SHA-256 receipts, character
   offsets and omitted-match counts. Resolve a hit from the saved input's folder,
   then `root_relative_to_input`, then `source`. See `HISTORY.md`. Display the
   precomputed JSON packets without needing a browser SQLite engine. A matching
   hash verifies the recorded text, not the truth of an old agent claim.

8. `research/flow-runs/v3/summary.json`, `flow-policy.json` and `audit.json`:
   real build/index work, two allowed publications and two hard flow denials.
   Show possible-exposure labels, recipient clearances and their propagation.
   A receipt's `commit_prepared` is distinct from the final ledger's `committed`.
   A null observer sequence means a hard policy decision before Jev. This is a
   controlled classification, not malicious intent. Calls without flow tracking
   use `mode: untracked`. Retain failed v1/v2 runs separately; see `FLOW.md`
   and `research/FLOW_POLICY_RUN.md`.

Important file shapes are `coding-session.json`, `runtime.json`,
`guarded-agent.json`, session `session.json`, worker `manifest.json`,
`observer-input-N.json`, and `_observer/input-N.json` / `decision-N.json`.
Inspect the files themselves; this list is not a promise of one universal schema.

## First usable version

Allow a user to choose a run directory through a browser file input with
directory selection. Parse locally; no upload or backend process is required.
Also provide a small bundled demo copied from real retained JSON, with its source
paths documented. Do not invent scores, events or counters.

Provide a run overview, a command/worker list, an event timeline and a detail
panel. The detail panel should show argv, return code, syscall, paths, errno,
permission-denial status, available native stack frames, Jev probability/model,
and the relevant saved observer input. Show hash receipts and link their imported
source files. Offer local download of selected original JSON.

Keep separate dimensions separate: worker outcome, observer verdict, capture
status and lifecycle closure. Render `no_observed_violation`, `violation`,
`abstain`, ordinary nonzero exit, incomplete evidence and unavailable verdicts
distinctly. A missing value is unknown, never zero or success. `recorded` does
not mean complete telemetry. The legacy `denied` flag means any failed syscall;
use `errno` and `permission_denied` for permission failures. Native frames are
execution stacks, not model thoughts. A local name-service denial is not proof
of malicious intent.

Distinguish clocks and ordering: syscall timestamps, elapsed times and observer
receipt order are different fields. Do not imply cross-worker causality or merge
them onto one unlabeled clock. Observer input paths are relative to their session
evidence root, not always the worker folder. Preserve those joins.

If showing token usage, use the reported fields with their source. Sum-over-call
usage is not context-window occupancy. Keep the requested model alias separate
from the persisted provider model ID. Show omitted history and truncated output
where the artifacts expose them.

## Delivery

Use a calm, readable layout with clear typography, useful filtering, keyboard
navigation and responsive panels. Render imported strings as text, never HTML.
Large traces should be loaded on demand; the first screen should use the smaller
JSON summaries. Surface parse errors with the file path and allow partial viewing
when other files are valid.

Validate by running the UI against the real successful, failed and cancelled
examples. Do not add large test suites just to count tests. Deliver the frontend,
a short setup/import guide, screenshots of those actual views, and a PR explaining
which formats and cases work and what remains unsupported. Keep attribution and
authorship consistent with the repository; do not add generated-agent credits.

---

This frontend can proceed independently while kernel launch, monitoring and
supervisor lifecycle work continues. Its first version is a recorded-run viewer;
live control and new backend interfaces are deliberately a separate task.
