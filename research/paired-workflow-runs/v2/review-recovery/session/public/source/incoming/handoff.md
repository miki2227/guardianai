# Builder handoff

step-001: `/usr/bin/python3 /workspace/source/build_release.py --output /output`. Verdict no_observed_violation, return code 0, evidence recorded.

Archive GuardianAI-linux-x86_64.zip
SHA-256 b4478b65a3610cb756b2d929d6795d7dd52e7a5babe9e9d517e5933210a8c026
Bytes 41744. Report file_count 16. native_policy 3. launch_guard_version 1.
Those figures are the build stdout. I did not recompute the archive hash or run native/notify-launch --abi.

manifest.json files_sha256 has 15 names, including agent_observer.py, decision_review.py, RUNNING.txt (1952 bytes), and native/notify-launch. manifest.json is omitted from that map by construction; file_count adds 1. I did not list zip members.

Please check report vs manifest versions, that file_count is 15 hashed files plus manifest.json, and hashes of RUNNING.txt, decision_review.py, and the launcher. The archive itself is not in this handoff.
