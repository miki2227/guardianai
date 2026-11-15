
# Operator guide

This follows the supplied RUNNING.txt for the Linux x86-64 core runtime. It is not a new measurement of the archive.

## Requirements

Python 3.10+, Bubblewrap with user namespaces, and strace built with native stack support and --kill-on-exit. The helper must be launch guard version 1. The trusted tracer is tied to the supervising Linux thread by SIGKILL parent-death notification. Give TYPESAFE_API_KEY only to the trusted supervisor environment.

Use a dedicated public input directory, an empty output directory, and a new evidence directory. Keep protected resources outside every public and runtime mount. Resource snapshots are limited to 32 KiB.

Workers cannot install their own seccomp filters in this profile. Connects to /var/run/nscd/socket and /run/nscd/socket are reported as emulated ENOENT and do not perform a connection. Any other connect stops the scope.

## Commands

One worker:

python3 guarded_agent.py --task "Read the approved summary" --workspace /path/to/public --output /path/to/empty-output --evidence /path/to/new-evidence --sensor /path/to/strace --resource summary=/path/to/private/summary.txt -- /usr/bin/cat /protected/summary

Several workers:

python3 guarded_session.py --manifest /path/to/session.json --evidence /path/to/new-evidence --sensor /path/to/strace

The session manifest is trusted host configuration. It carries the task, resources, and workers. Each worker supplies name, workspace, output, command, and a resource-name array.

Coding-agent MCP:

python3 guardian_mcp.py --task "Declared task" --workspace /path/to/public-source --session /path/to/new-session --sensor /path/to/strace

Disable every other execution tool in the MCP client. Only Linux commands dispatched through this MCP server are contained. The model transport and the host harness stay outside that containment and are trusted.

## Results

Exit 77 means a detected violation. Exit 78 means abstention. Any other exit status is the worker's own status.

The archive is the core runtime. Historical research evidence stays in the source project. OS evidence records execution. It does not reveal latent model thoughts.

The supplied build report names native policy 3 and launch guard version 1. The zip and the compiled launcher were not part of this handoff, so this guide does not confirm the packaged binary.
