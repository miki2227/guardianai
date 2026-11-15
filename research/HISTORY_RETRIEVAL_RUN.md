# Retrieval of older retained evidence

15 November 2026. The previous observer kept full records on disk but supplied
only recent excerpts/events to Jev. The new evidence-memory index retrieves older
lexical matches with exact source provenance. This addresses a concrete monitoring
visibility gap without training or launching more working-agent models.

## Implemented boundary

`EvidenceMemory` indexes immutable source references and UTF-8 text using SQLite
FTS5. It selects up to 16 bounded lexical query terms and ranks matches with
BM25, returning at most three source excerpts of 1,024 characters. Every returned
file is checked against its saved SHA-256 before excerpting. A hit retains its
source path, kind, character offset and full source length. The latest eight
input/content records remain in the separate recent-context path and are excluded
from retrieval. The 20 KiB state budget is unchanged; low-ranked hits are omitted
before existing context is trimmed. Match/omission counts are explicit.

This is a standard retrieval technique and an undergraduate systems integration,
not a new search algorithm. The [Arbiter Agent](https://arxiv.org/abs/2606.10747)
already studies continual oversight with limited inspection resources.
[When Local Monitors Miss Compositional Harm](https://arxiv.org/abs/2607.11751)
shows why local views can miss harmful composition and why even full traces may
be insufficient without the relevant representation. Our inference is that
recovering older evidence is useful infrastructure, not a solution to that
observability limit. [SQLite's FTS5 documentation](https://www.sqlite.org/fts5.html)
describes the search and ranking primitives used here.

## Actual retained-run archive

[build_archive.py](history-retrieval-runs/v1/build_archive.py) created a searchable
archive of 153 real records from the completed v2 paired run: host-agent content,
tool content, runtime observer states and mediated handoffs. Copies are byte
identical to their original sources; the source manifest preserves those hashes.
Import order is not a global causal clock. Saved states may repeat observations,
so this is not a count of 153 independent agent actions.

Queries derived from the actual published archive hash and final review decision
excluded all final-phase source records. The first query found 16 eligible
matches and returned three, with 13 omitted, in a 3,972-byte context. The second
found 97 and returned three, with 94 omitted, in a 6,768-byte context. Every source
hash and excerpt span matched its retained file. These are useful evidence-archive
queries, not attack trials, semantic-retrieval recall or detector-accuracy results.
No Jev or Grok calls were used to construct or query this archive.

## Live release build and inspection

The current packaged supervisor then performed an actual GCC release build and
printed/inspected the public evidence-memory module through MCP. Both commands
returned zero with `no_observed_violation`, and explicit finish recorded closure.
The trusted host drove those commands; no new Grok subjects were launched.

There were 49 runtime observer inputs. Forty contained retrieved older evidence,
with 117 returned spans verified against exact source bytes and offsets. Every
retrieved native source preceded the latest-eight-input window. The largest saved
state was 20,095 bytes, below 20,480. The SQLite record count, input receipt hashes,
match/omission counts, source spans and archive/member hashes were checked by
[summarize.py](history-retrieval-runs/v1/summarize.py).

The [built archive](history-retrieval-runs/v1/build-run/session/public/results/step-001/GuardianAI-linux-x86_64.zip)
has 17 members, 44,047 bytes and SHA-256
`a6b0e41871239c2b81d72f47f65351a41111196525106b4d09f775e5d17a8e69`.
Native policy remains 3 and launch guard version 1. The build source and receipt
data are retained alongside the [live summary](history-retrieval-runs/v1/live-summary.json).

## Remaining visibility limits

This run proves that older retained source material reached actual Jev inputs
within the existing state budget. It does not prove better detection, emergence
of a covert convention, provider context exhaustion or access to hidden thoughts.
Lexical matching can miss semantically related text, encodings and channels that
share no selected terms. Excerpts can still omit important context. Historical
content remains untrusted evidence, not current policy or an authorization grant.
The trusted store and index lifetime require host management; privileged host
tampering is outside the worker-containment model. The optional shared launcher
history root is implemented, but this live build used per-scope indexes; the
multi-stream archive demonstrates combined offline retrieval only.
