# Final review

Evidence-bounded check of incoming response.md and operator-guide.md against the public source and the prior v2 review. Not a safety certification of the packaged runtime. This workspace did not include the zip, native/notify-launch, RUNNING.txt, build-report.json, or manifest.json. Receipt hashes for the two new files match: response.md 09f840d36a499c0f34837e4db3b6631554253b19a73894ba00eeea3e56078928 (1646 bytes), operator-guide.md cf2fb367993df2b13c09caceadfef4b75e600595942e584782f9432f81cd66f4 (2355 bytes). observer_sequence is 2.

## Builder response

The response does not claim a rebuild or a new digest. It repeats the prior report figures (zip sha256 b4478b65a3610cb756b2d929d6795d7dd52e7a5babe9e9d517e5933210a8c026, 41744 bytes, native_policy 3, launch_guard_version 1, file_count 16) and labels that digest as build stdout plus build-report.json. It agrees files_sha256 omits manifest.json because the map is written first and file_count is len(files_sha256)+1. It leaves zip membership, the launcher hash 91491b52b824d340758e48c73804d09bcd789553b1a2373c3ed140af4786def0, and a live --abi result open. That matches the prior review. Current build_release.py still gates policy_version 3 and launch_guard_version 1 and sets file_count to len(files_sha256)+1. The 13 public-file matches and the RUNNING.txt measurement (1952 bytes, sha256 0571b1701c1d86a9de37ee14ac7495cc8506a5e0d23323b04bb30237085e40ab) were prior-session checks. They were not repeated here because those artifacts are not in this incoming set.

## Operator guide

The guide follows the RUNNING.txt literals embedded in build_release.py: Python 3.10+, Bubblewrap user namespaces, strace with native stacks and --kill-on-exit, guard version 1, SIGKILL parent-death notification, TYPESAFE_API_KEY only in the supervisor environment, empty output, new evidence, protected paths outside mounts, 32 KiB snapshots, no worker-installed seccomp filters, emulated ENOENT for the two nscd sockets, other connects stop the scope, exit 77 violation, exit 78 abstention, and MCP containment limited to commands dispatched by guardian_mcp.py. Those points also appear in guardian.py, guarded_agent.py, guarded_session.py, release_broker.py (32768 bytes), monitor.py, runtime_supervisor.py, and seccomp_gate.py. The guide states it does not confirm the packaged binary. That limit is accurate.

## Verdict

Accept the documentation handoff. Do not accept the archive or launcher as verified. Ship or deploy the zip only after its bytes and the compiled notify-launch are checked.
