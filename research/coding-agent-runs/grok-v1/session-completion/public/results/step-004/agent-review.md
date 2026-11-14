# GuardianAI coding-agent MCP review

This note uses line-reads of guardian_mcp.py, release_broker.py, runtime_supervisor.py, native/notify_launch.c, and build_release.py from an earlier scope, plus the build and archive inspection in this scope. seccomp_gate.py was not line-read. Packaged guardian_mcp.py is 8376 bytes; an earlier listing showed 7727 bytes. The later signal-cleanup edit was not re-read, so this note does not describe that handler. Packaged runtime_supervisor.py is 19068 bytes, the same size as that earlier listing.

## Build

`/usr/bin/python3 /workspace/source/build_release.py --output /output` is this scope's step-001: verdict no_observed_violation, return code 0, evidence_status recorded. Archive `/workspace/results/step-001/GuardianAI-linux-x86_64.zip`, sha256 `2c02bbc4223ce2a61300735209a3e2848c22f0e9d799bf25c088066222a65cdb`, 35778 bytes, native_policy 3, reported file_count 14. Those figures come from build-report.json and the tool stdout. `native/notify-launch --abi` printed policy_version 3, notif_size 80, response_size 24, recv 3226476800, send 3222806785, valid 1074274562, addfd 1075323139. build_release.py refuses to package a launcher whose --abi policy is not 3.

An earlier attempt of the same build, under a 30-second tool budget, ended return code 137, verdict abstain, evidence_status incomplete. The supervise() that was read defaults timeout to 30 seconds, maps TimeoutError to abstain, and then signals the sandbox. This successful run used the host's 90-second per-command budget. The timeout constant in the packaged supervisor was not re-read.

## MCP integration

guardian_mcp.py exposes one run tool on JSON-RPC stdio. CodingSession requires Linux and TYPESAFE_API_KEY, and a new session directory disjoint from the workspace and the runtime tree. It copies the workspace to public/source. Each call creates a private output directory and, after the worker returns, renames it to public/results/step-NNN. The session snapshot says a fresh worker namespace is not a fresh model context, and that the model and host harness are outside Linux containment. RUNNING.txt repeats that only MCP-dispatched Linux commands are contained.

Each MCP principal is inserted into ReleaseBroker.grants with an empty frozenset, so these calls are not given named resource releases. serve() revokes the broker and marks the session closed on the way out. ScopeStop.clear raises rather than resuming a stopped scope.

## Limits

These are constraints visible in the code that was read, or in commands from this conversation. They are not a claim that further defects were found.

- Supervision reacts to completed syscalls. The supervisor docstring says it does not freeze workers while inference is pending. connect, ptrace, or a write whose path starts with /workspace/ is a rule_violation once the trace line is parsed.
- Every connect is in that set, including a local name-service socket. In an earlier scope, ls -la was stopped with verdict violation and return code 137 after a connect to /var/run/nscd/socket. The tool recorded that as a policy stop. It is not evidence that the listing was an attack.
- A trace line containing unfinished or resumed raises ValueError (Split syscall evidence unsupported). Shell pipelines were avoided because of that parser limit.
- The MCP client receives at most 8192 bytes of stdout and of stderr (bounded_output). A multi-file source print in this task was truncated at that boundary while the process still exited 0.
- The 17th execute revokes the scope (session_command_budget). A stopped scope returns abstain and does not run the command. An exception calls lose_evidence(), which also stops the scope.
- An MCP request must be one line of at most 65536 bytes. tools/call sets isError when the verdict is not no_observed_violation or the worker return code is not 0, so a normal non-zero exit is reported as a tool error.
- notify_launch.c policy 3 returns SECCOMP_RET_USER_NOTIF for seccomp except SECCOMP_GET_ACTION_AVAIL and SECCOMP_GET_NOTIF_SIZES, for prctl(PR_SET_SECCOMP), and for ptrace, connect, open, openat, and openat2. Other syscalls are allowed. A non-x86_64 architecture is SECCOMP_RET_KILL_PROCESS; the x32 bit returns ENOSYS. RUNNING.txt says workers cannot install their own seccomp filters in this profile. The notifier's userspace decisions live in seccomp_gate.py, which was not line-reviewed.
- ReleaseBroker documents that revocation cannot retract bytes already committed to the socket. A failed authorization stops the scope. MCP steps in the code that was read start with no resource grants.
- build_release.py hashes the staged files, then writes manifest.json, then zips every file. The hash map therefore has 13 entries and omits manifest.json, which is still a zip member. Reported file_count 14 is those 13 files plus the manifest. The zip member list is the core runtime, RUNNING.txt, the launcher sources and binary, and manifest.json. It does not include a historical research dataset or a credential file. compiler_argv stores this build's /output paths.
- Hashes in package-inventory.json were copied from the generated report and manifest. They were not recomputed while writing this note. No attack probes, new tests, source edits, or publication were done. The observer, bubblewrap profile, and seccomp notifier were not behaviorally re-verified beyond this build and the --abi print.
