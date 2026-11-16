# Observe generated files and ZIP text before MCP publication

After runtime and recipient-clearance checks, the MCP adapter snapshots generated
output and observes it before publishing the directory into result history. This
supplements argv, syscall and stdout/stderr checks. A quiet command can leave
consequential text in a file without printing it.

The private `artifact-snapshot.json` records file paths, directory names, byte
counts, SHA-256 values and ZIP-member trees. UTF-8 text without NUL is stored once
in `text_by_sha256`; each text leaf references its digest. Identical bytes in a
loose file and a ZIP member need no duplicate text storage. Nontext leaves have
`kind: opaque_binary`. Hashes establish byte identity, not semantic safety.

Stored/deflated ZIP members, including nested ZIPs, are read in memory without
extracting or executing them. Duplicate normalized names, absolute or parent
paths, links, encrypted entries and unsupported compression refuse publication.
Other binary formats remain opaque. ZIP comments, extra fields and container
bytes outside decoded members are not semantically inspected.

## Observation receipts and context

`artifact-inventory.json` and the call's `artifact_observation` contain metadata
without duplicating text. `observer_sequence` joins the metadata check to
`_content/content-N.json` and `_content/decision-N.json`. The content kinds are
`artifact_inventory_before_publication` and `artifact_text_before_publication`;
historical cases retain the earlier single-packet format. `text_units` lists
each text digest, character span, observer sequence and outcome. The snapshot
hash binds metadata and units to the complete private packet.

Each text unit carries its path chain (outer file followed by ZIP members),
digest, full text length and at most 6,144 new characters plus 256 preceding
characters. It uses the existing 2,048-character observer chunks, history lookup
and contextual review. Every unit must pass before publication. A short file
can fit completely in a review unit; omitted regions of a long file are explicit.
Review does not certify relationships outside its available context.

An output with no files or directories has no content decision and a null
sequence; that is not a positive Jev verdict. Directory-only output is observed.

## Publication and failure

The worker has completed before snapshotting. Only ordinary singly linked files
and directories are accepted. Physical symlinks, hard links and special files
refuse publication. Reads use no-follow and nonblocking flags. Names remain
relative to the output or containing archive; members never become host paths.

One publication permits at most 128 filesystem/archive entries, 16 MiB of
physical plus expanded file bytes and 192 KiB of serialized snapshot evidence.
Nested ZIPs share these budgets. The observer retains its separate state and
review budgets; an oversized review still abstains. These limits can refuse
legitimate exports and do not prove a general CPU or heap bound for the trusted
ZIP library.

A snapshot failure, confirmed content stop or observer fault withholds the
directory and stdout/stderr and stops later commands. Expected snapshot faults
record an inventory diagnostic. Exceptions return `abstain` even when execution
exited zero. Runtime outcome, publication outcome and task success are separate.
An ordinary nonzero exit can return diagnostics when observation succeeds.

The host output tree must remain protected from concurrent modification after
worker teardown. Public-only revocation and the directory rename use the same
commit lock; see the [actual cancellation](research/PUBLICATION_STOP_RUN.md).
A stop cannot recall committed output. This is not a signed snapshot protocol
against a malicious host or a transactional stdio transport.

Public input provisioning, remote inference, emitted chat and other covert
channels remain outside this gate. Directory names are included in metadata.
A Jev allow is a classifier decision, not a detection guarantee. The
[actual ZIP packaging run](research/ZIP_OBSERVER_RUN.md) retains failures and
bounds the measured result.
