# Observe generated text before MCP publication

After command execution and the recipient-clearance check, the MCP adapter
snapshots generated `/output` files and sends complete text artifacts to Jev
before publishing the directory into later commands' result history. This
supplements the existing argv, runtime and stdout/stderr checks. A quiet command
can leave consequential text in a file without printing it.

The content kind is `artifact_contents_before_publication`. Its saved content
record contains paths, byte counts, SHA-256 values and full decoded text. It
uses the existing bounded chunks, history retrieval, semantic questions and
contextual review. Files that are not UTF-8, or contain NUL, have
`kind: opaque_binary` and no text field. Archives and encodings are not unpacked.
Their hashes establish byte identity; they do not establish semantic safety.

The private worker evidence contains `artifact-inventory.json`. The tool response
and call record expose the same metadata as `artifact_observation`, without
duplicating the full text. `observer_sequence` joins it to `_content/content-N.json`
and `_content/decision-N.json`. An empty output has no content decision and a null
sequence. That means no files needed review, not a positive Jev verdict.

## Publication and failure

The worker has completed before this snapshot. Only ordinary singly linked
files and directories are accepted. Symlinks, hard links and special files
refuse publication. File reads use no-follow and nonblocking flags so an output
FIFO cannot block the trusted reader. The inventory includes relative names,
not resolved link targets.

One publication permits at most 128 filesystem entries, 16 MiB of file bytes
and 192 KiB of serialized file evidence. The existing content observer has its
own state and review budgets; a full-context review that exceeds its budget
still abstains. These fixed limits keep work bounded and can refuse legitimate
large exports. They are compatibility limits, not evidence of malicious intent.

A snapshot failure, confirmed content stop or observer fault withholds the
directory and stdout/stderr delivery and stops later commands. Snapshot faults
record a private inventory diagnostic and return `abstain`, even when the earlier
worker exited zero with an unflagged runtime. Runtime outcome, publication
outcome and task success remain distinct. An ordinary nonzero exit can still
return unflagged diagnostics when observation succeeds.

The host output tree remains trusted against concurrent modification after
worker teardown. In public-only mode, broker revocation and the directory rename
now use the same commit lock; see the [actual cancellation](research/PUBLICATION_STOP_RUN.md).
Publication renames that completed tree; this is not a signed
snapshot protocol against a malicious host. Public input provisioning, remote
inference, already emitted chat and nontext covert channels remain outside this
new gate. Empty directory names are not included in the file-content packet.
A Jev allow is a classifier decision, not a detection guarantee.
