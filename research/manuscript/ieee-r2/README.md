# Updated IEEE systems-study revision

Read `paper.md` or `output/pdf/main.pdf`. This revision integrates the later
identity-binding, protected peer-handoff, publication-cancellation, virtual-file
failure and ZIP-observation evidence. It preserves the supplied title, four
author names/IDs, abstract and keywords exactly in source. The first paragraph
distinguishes the abstract's original proposal from completed work. No weight
updates, validated spontaneous convention, context saturation or Q1 readiness
are claimed. The builder remains quarantined under the user's explicit decision.

The `current/` draft and the earlier parent manuscript remain separate frozen
artifacts. This folder does not replace or refresh their measurements. Its data
edition is Git commit `170eefe9f0a56a6a44a8be8f8f3bc768ae55d20f`, which contains
separate case-specific source snapshots. That does not mean every case ran the
same implementation. No new inference or execution trials were run for writing.

## Rebuild and verify

In a full checkout with the pinned Git history, keep this folder at
`research/manuscript/ieee-r2`. Pandoc, PyYAML, Matplotlib, PyMuPDF, Pillow and an
IEEEtran-capable LaTeX compiler are required for the full authoring workflow.
The source package already includes the figures. Run:

```sh
python verify_claims.py
python build_figures.py
python build_ieee.py
tectonic -X compile --outdir output/pdf --print --untrusted main.tex
python inspect_pdf.py
python package.py
```

`claims.json` pins 39 sources, 89 selected descriptive facts and 13 literal
implementation statements. The verifier reads those bytes from the pinned Git
revision, checks fields and confirms that the earlier manuscripts are unchanged.
It performs no model calls, live actor poll, semantic proof or detector benchmark.
The selected facts include both positive outcomes and failures. Underlying case
audits perform stronger raw trace/payload joins; consult their scope statements.

`create_ledger.py` initializes the ledger once and refuses to overwrite it.
Do not rerun it to bless changed evidence. New data require an explicit revision.
`build_figures.py` draws the architecture and a zero-based chart from the verified
input-field facts. Those token fields are not retained-context occupancy.

The actual local compiler invocation is retained in `compile-report.json`.
`pdf-check.json` records source/PDF front-matter checks, geometry and page count.
Visual inspection is also required; text extraction alone does not verify layout.
The source archive excludes the complete execution dataset and credentials.
Model re-execution is outside the rebuild steps and may produce different results.

## Scholarly scope

The eight references were checked against primary records for this revision;
metadata and the limited basis of each comparison are in `reference-audit.json`.
The 2026 arXiv papers are preprints. The comparison identifies prior mechanisms
and attributed design influences, not proof of a globally new algorithm or
performance superiority. This is a reviewable undergraduate systems draft;
no journal submission, affiliation or publication identifier is invented.
