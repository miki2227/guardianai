# Current undergraduate systems draft

Read `paper.md` or the compiled `output/pdf/main.pdf`. `main.tex` is generated from
the Markdown source using IEEEtran's conference layout. `frontmatter.json` holds
the user's unchanged title, author names/IDs, abstract and keywords; the builder
checks those against the Markdown metadata. The separate parent manuscript and its frozen manifest have
not been rewritten. This draft describes the newer observation, persistent-flow
and continuing-agent integration, with failures and open requirements retained.
Affiliations and a target venue are not invented. No journal submission is
performed, and this draft is not labelled Q1-ready.

`claims.json` pins the source files and selected quantitative facts used in the
paper. From this directory inside the full repository, run:

```sh
python verify_claims.py
python build_ieee.py
tectonic -X compile --outdir output/pdf --outfmt pdf --print --untrusted main.tex
```

Pandoc, PyYAML and a usable LaTeX compiler are required for rebuilding. The actual local
compiler invocation and outcome are retained in `compile-report.json`.
`verification.json` records hash/field checks, not proof of every narrative claim.
No fresh model calls were added. One real supervisor-crash recovery case (E6)
was added in response to the user's testing request. E1-E5 use the pinned data
revision; E6 is included in the current repository alongside this draft.
Cases use separate retained revisions and must not be pooled into a
single benchmark or advertised as replicated detector accuracy.

The paper package contains the draft sources, figure, compiled PDF, ledger and
validation records. It excludes the runtime and full execution dataset. Extract
it under the same `research/manuscript/current` layout in a checkout containing
the pinned data to run the verifier. Public source links point to the data
revision, not to a claim that the package independently reproduces hosted models.
The verifier reads implementation bytes from the explicitly pinned Git revision
and retained experiment files from the checkout. It does not verify current HEAD
as though it were the older tested runtime, and never refreshes expected hashes.
Git history must contain that revision. Later runtime updates can coexist with
this frozen paper's evidence; the result records how many implementation sources
were resolved from Git. The PDF's fixed front matter and data claims are unchanged.
