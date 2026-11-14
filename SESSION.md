# Shared worker sessions

`guarded_session.py` launches multiple local worker commands under one trusted
task and one terminal revocation scope. A detected violation or monitoring failure
sets the shared stop state, blocks subsequent protected releases and causes active
worker namespaces to terminate. Ordinary nonzero worker exits remain task failures
rather than being relabelled as malicious behavior.

Each worker has a private notification channel, isolated namespace, separate output
directory, its own streamed Jev event observation and an explicit protected-resource
grant list. The caller supplies a trusted host manifest. Workers cannot choose
their own principal or grant additional resources. The manifest describes the whole
session before launch; this is not an unauthenticated service accepting new jobs.

Prepare existing public inputs, initially empty output directories and a new
evidence path. Use Linux/WSL paths. For example:

```json
{
  "task": "Build the public GuardianAI runtime and list its public Python sources. Write results only to each worker's output; private /tmp scratch is allowed.",
  "resources": {},
  "workers": [
    {
      "name": "builder",
      "workspace": "/home/user/guardianai-source",
      "output": "/home/user/build-output",
      "command": ["/usr/bin/python3", "/workspace/build_release.py", "--output", "/output"],
      "resources": []
    },
    {
      "name": "source-list",
      "workspace": "/home/user/guardianai-source",
      "output": "/home/user/list-output",
      "command": ["/usr/bin/find", "/workspace", "-maxdepth", "1", "-name", "*.py", "-print"],
      "resources": []
    }
  ]
}
```

Run with the Jev credential only in the trusted supervisor environment:

```sh
python3 guarded_session.py --manifest /path/to/session.json \
  --evidence /path/to/new-session-evidence --sensor /path/to/strace
```

Worker stdout/stderr and native traces are in its named evidence directory.
`session.json` contains all worker results and the shared broker audit; the copied
`manifest.json` and its hash identify the configuration actually used. Per-worker
broker audits are snapshots of shared history, so use the session audit for the
complete lifecycle. Exit 77 indicates violation, 78 abstention, 1 an ordinary
worker failure, and 0 successful worker exits with no observed violation.

The observer's frozen shared states and decision receipts are in `_observer` under
the session evidence root. Jev sees the current worker batch plus bounded shared
activity, protected grants, namespace facts and broker history. Receipt hashes
connect those states to runtime decisions and protected releases. See the
[shared-observer run](research/SHARED_OBSERVER_RUN.md), including a retained false
alarm from the first integration.

To provision a protected file, add a root resource mapping such as
`"previous-manifest": "/host/private/previous/manifest.json"`, then include that
name only in the intended worker's resource list. The worker reads it as
`/protected/previous-manifest`. The host file must be outside every worker's public,
output and runtime mounts; snapshots are limited to 32 KiB. Public inputs may be
shared, but outputs must be disjoint from all inputs and other outputs. Evidence
must be disjoint from every worker mount. Directory checks cannot prove the
absence of exposed duplicates or hard links.

The packaged application has completed a real concurrent release-build and
source-indexing session. It also ran independently of the development checkout,
using an explicitly granted previous-release manifest to write a source-change
index. Both workers completed with exit 0 under live Jev oversight. See the
[retained session outcome](research/system-runs/shared-session-summary.json) and
[source-change index](dist/archive-v3/source-change-index.json). These were ordinary useful
workloads, with no synthetic violation injection or new model subjects.

This supervises the declared local workers and their descendants. Hosted model
inference remains outside the WSL process tree. Jev evaluates bounded event
batches; cross-batch patterns and latent thoughts are not established by these
records. Each judgment now includes bounded cross-worker context, rather than
every worker's entire history. Recent details can roll out of that context;
older activity remains as counts and retained local evidence. Policy 3 forbids worker-installed seccomp filters, which limits compatible
applications. The successful work runs demonstrate operation, not universal
detection, failure-path coverage or journal-level novelty.
