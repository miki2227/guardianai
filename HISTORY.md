# Retrieval from retained observer evidence

`evidence_memory.py` indexes retained observer records in SQLite FTS5. It does not
train a model or generate a narrative memory. For each incoming content item or
native batch, it looks for older records sharing identifiers, paths or other
lexical terms. It returns at most three verified source excerpts, each at most
1,024 characters, with the source path, SHA-256 and character offset.

The latest eight records in the current observer stream are excluded from search;
their existing recent context remains separate. Retrieval records the number of
indexed records, eligible lexical matches and matching records omitted. The
existing 20 KiB state limit still applies. Low-ranked retrieved excerpts are
dropped first if necessary; omission counts remain explicit. Confirmation review
uses the same budget rule when it needs room for the complete current message.

Source files must remain available and unchanged for the life of an index.
Retrieved excerpts come from those files after SHA-256 verification, not from an
unverified index copy. Changed/missing sources, database failures and oversized
states propagate to the existing abstain/stop path. The index and original
evidence are trusted supervisor data outside the worker mounts.

By default, each `AgentObserver` or `SessionObserver` has a per-scope index under
its evidence directory. A trusted host can pass `memory_root=` to `AgentObserver`,
or `--history-root` to `run_grok_guarded.py`, to share an index across continuing
launcher scopes. That dedicated root must already exist and contain the current
and earlier launcher evidence. Do not use a broad unrelated project/home root.
This option does not reconstruct provider-hidden history. It only searches
records actually observed and indexed under the selected root.
The [continued-agent run](research/CONTINUED_AGENT_RUN.md) exercised that shared
host root across three real invocations of one retained conversation, with
hash/span verification of delivered excerpts from preceding invocations. It did
not import the conversation's older provider history or prove semantic completeness.

In saved inputs, `history_retrieval.root_relative_to_input` identifies the index's
source root relative to that input file's directory. Each hit's `source` is
relative to that root. Normalize path separators when importing Windows and Linux
datasets. Resolve only files actually present in the imported dataset; a missing
source is unknown. `start_character` addresses UTF-8-decoded source text, not a
byte offset or a model-token position.

This is lexical retrieval with SQLite BM25 ranking, not semantic completeness or
proof of collusion. Older observations do not grant current permissions or prove
cross-worker causality. Counts describe saved records and lexical matches, not
independent actions or a detector's recall. Whole source records remain on disk,
but Jev still receives bounded context. SQLite indexes can grow with retained
evidence; the selected history root is a host-managed lifetime boundary.
Hash verification proves that an earlier observation is unchanged; it does not
make an agent's earlier factual claim true.

Python's `sqlite3` must support FTS5. This was verified on the Windows host and
Kali WSL installation used here. The [actual run](research/HISTORY_RETRIEVAL_RUN.md)
provides the archive queries, live inputs, source joins and package hashes.
