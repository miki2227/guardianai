# GuardianAI recorded-run viewer

A local, read-only React/Vite viewer for retained GuardianAI run evidence. It has
no server API, upload path, execution controls or live stop control. Imported
folder contents stay in the current browser tab.

## Run locally

```sh
cd frontend
npm install
npm run dev
```

Open the localhost URL printed by Vite. `npm run build` makes a static build in
`frontend/dist/`.

Use **Import run folder** and choose a recorded run folder. The browser uses
`webkitdirectory` folder selection. For a folder with nested sessions, select
the narrowest folder that contains the relevant `summary.json` or
`coding-session.json` and its evidence tree. The app also includes two bundled
examples so its first view works without selecting files.

## Included real examples

The bundled JSON is copied without alteration from repository artifacts:

| Viewer example | Source artifacts |
|---|---|
| Grok build and review | `research/coding-agent-runs/grok-v1/summary.json`; `session-completion/evidence/coding-session.json`; `step-001/manifest.json`, `runtime.json`, and `observer-input-0.json` |
| Owner lifetime | `research/system-runs/owner-lifetime/summary.json`, `normal/evidence/coding-session.json`, `cancelled/evidence/coding-session.json`, and `cancellation.json` |

The first dataset shows the policy stop, successful commands, and the actual
30-second abstention in its retained scope list. The selected successful build
shows its recorded 236 syscall events and Jev action receipts. The second dataset
shows normal completion alongside the separate SIGKILL cancellation. The
cancelled build has an interrupted worker return code and an unavailable runtime
verdict; it is not counted as a successful or violating worker.

`frontend/src/demo/` contains these source JSON copies. The full run directories
remain the authoritative records.

## What is shown

- Task and command argv when those fields were saved.
- Worker exit, runtime/observer verdict, capture status, lifecycle closure and
  stop state as separate fields.
- Syscall event time, syscall, paths, errno, permission denial and native
  execution stack when included in the runtime event.
- Jev model, probability, action and linked observer input fields exposed by a
  saved action receipt.
- Evidence JSON file names and local JSON downloads. Manifest hash receipts
  remain available in the original manifest JSON.
- Parse/read errors for files that cannot be parsed, with partial run viewing
  retained for the remaining files.

The syscall list is capped at 2,000 rendered events per selection. Native stacks
are execution stacks, not model reasoning. `recorded` means the artifact says
recorded; it does not assert complete telemetry. Missing values remain unknown.
The old `denied` flag is displayed separately from `permission_denied` and
`errno`. A policy stop is an observed policy outcome, not a claim about intent.

## Format support and current limits

The first adapter recognizes session `coding-session.json` records and summaries
with a `scopes[].calls[]` shape, and joins a locally imported `runtime.json` and
`manifest.json` for a selected step-001 when present. Other JSON files remain
available in the evidence file list. It does not yet implement the additional
research schemas in the frontend handoff: content observer journals, paired
workflow/provenance joins, flow/MCP/identity audit joins, saved FTS packets,
artifact and ZIP observer receipts, peer handoffs, or controller stop
acknowledgement joins. For these formats the viewer offers partial file
inspection, not a claim that all relationships have been reconstructed.

No trace text parser, browser SQLite engine, native-ledger path resolver, hash
recomputation, or causal ordering across workers/clocks is implemented. The
browser does not infer a verdict from return code, file presence, `denied`, or
an absent value. It also does not currently expose stdout/stderr bodies. Large
trace files should be excluded when selecting an import; the UI reads files in
the selected directory into browser memory.

## Review screenshots

The overview and syscall/decision panels can be reviewed by running the local
viewer and selecting the bundled examples. Captured review images should be
attached to the PR from those real views; they are not synthetic dashboard
mockups.
