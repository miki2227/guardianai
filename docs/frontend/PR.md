# PR: Add a local GuardianAI recorded-run evidence viewer

## Summary

- Add a React/TypeScript/Vite read-only local viewer under `frontend/`.
- Import recorded run folders in the browser, parse recognized session/summary
  JSON, and expose worker commands, syscall details, Jev receipts, evidence
  files, and lifecycle state.
- Bundle unmodified JSON copies from the retained Grok completion and
  owner-lifetime normal/cancelled runs.
- Keep successful observation, violation, abstention, nonzero exit, interrupted
  execution, incomplete capture, and unavailable verdict as distinct states.
- Add setup, import, format-support, and limitation notes in
  `docs/frontend/README.md`.

## Validation

- `npm run build` — TypeScript check and Vite production build pass.
- Open the local app against bundled Grok and owner-lifetime JSON; inspect
  successful, policy-stopped, abstained, and interrupted/unknown examples.

## Scope and known limitations

Only `frontend/**` and `docs/frontend/**` are changed. Python/C runtime files and
root dependencies are untouched. The first parser does not yet reconstruct the
extended research dataset joins described in `TEAMMATE_FRONTEND.md`; the README
lists unsupported schemas. No live-control button or API was added.
