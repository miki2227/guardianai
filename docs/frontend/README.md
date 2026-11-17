# GuardianAI recorded-run viewer

A local React/Vite interface for presenting actual retained GuardianAI evidence.
No backend API, uploads, execution controls or live stop button. Imported files
stay in the browser tab. Native stacks describe execution, not private thoughts.

## Start

Use Node 20.19+ or 22.12+ (validated with Node 24.15):

```sh
cd frontend
npm ci
npm test
npm run dev
```

Open the localhost URL printed by Vite. `npm run build` creates `frontend/dist`.
The production bundle contains offline evidence and is larger than a typical
application shell (about 1.65 MB before compression); no remote fetch is needed.

## Presentation path

1. Open **Two-agent Checkstyle**, the default. It is the accepted v5 experiment:
   two continuing Grok 4.7 low-effort subjects, three phases, nine commands,
   133 scoped events and two verified public artifact handoffs.
2. Expand **Workflow evidence** for the saved host audit and each handoff.
   Delivery is a recorded assertion here; independent verification is in the
   source audit, not performed again by the viewer. These public handoffs used
   explicit `untracked` flow mode.
3. Select a command. Open **Syscall timeline** and select an event for its stack.
   **Jev decisions** exposes scores, model, deadlines, application state and exact
   runtime/session input references. Missing files remain missing.
4. Open **Message observation (phase)** for saved host-client and MCP content
   receipts. These cover the phase, not only the selected command. Expand a
   receipt to inspect initial chunks and confirmation/multipart review fields.
5. Open **Command output** or download selected-worker evidence. **Show all run
   files** explicitly includes files not joined to that worker.
6. Switch to **Grok build & review** for older policy-stop and timeout records,
   or **Owner cancellation** for a retained interrupted build.

The v5 findings are provisional subject outputs. No P0 or emergent covert
convention was established. The later [context-pressure attempt](../../research/CONTEXT_PRESSURE_RUN.md)
did not complete; it is not substituted for the accepted v5 demo.

## Source integrity and joins

`npm run sync-demo` copies 189 exact files from `research/checkstyle-paired/v5`
into `frontend/src/demo/paired`. `source-sha256.json` lists their original byte
hashes. Tests recompute all hashes and compare every copy to the source. Existing
historical examples remain in `frontend/src/demo` as supplied in the original PR.

Each session command joins only its exact sibling `step-NNN/runtime.json` and
`manifest.json`; there is no first-worker or first-runtime fallback. Historical
`summary.json` with `scopes[].calls[]` also works. Return code, capture status,
runtime verdict, closure and stop state remain separate. A nonzero/interrupted
worker, incomplete capture or review-cleared alert cannot become a green worker
success. A clean `finish=true` also revokes the finished scope; a stopped marker
alone does not mean misconduct.

## Import limits

Choose the narrowest run directory containing sessions and their evidence.
Folder selection strips only the selected root directory name. Supported local
text extensions: JSON, JSONL, Markdown, TXT, LOG and TOML. Files over 2 MiB and
imports exceeding 64 MiB are skipped with visible notes. Binary databases,
archives and raw traces are excluded before reading. Invalid JSON remains
inspectable text with a parse note; unsupported shapes do not invent commands.

The event list renders at most 2,000 events per selection. There is no raw trace
parser, SQLite engine, native-path resolver, causal clock ordering, independent
hash verification in the browser, complete FTS/flow/identity reconstruction or
live telemetry subscription. Oversized files skipped at import may remove some
relationships. The adapter never fills gaps from a different worker.

## Validation

Seven adapter/integrity tests pass; TypeScript and production build pass.
`npm audit` reports zero known vulnerabilities for the resolved dependencies.
A headless Chromium check covered default nine-command rendering, two handoffs,
Jev input references, stdout/stderr, owner cancellation and directory import.
Desktop and 390px mobile views had no page overflow after the mobile grid fix;
no browser errors were recorded. Screenshots are in `screenshots/`.
