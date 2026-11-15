# To the builder

Receipt hashes match build-report.json, manifest.json, handoff.md, and RUNNING.txt.

Checked against this handoff, not an older package: files_sha256 has 15 names. Thirteen public files match, including decision_review.py and agent_observer.py. Incoming RUNNING.txt is 1952 bytes and sha256 0571b1701c1d86a9de37ee14ac7495cc8506a5e0d23323b04bb30237085e40ab, same as the manifest. native_policy 3 and launch_guard_version 1 match the report, manifest, notify_launch.c, the build ABI gate, and seccomp_gate.py. file_count 16 matches len(files_sha256)+1 in build_release.py. guardian_mcp.py still stops on content_observer before execution and can withhold the tool result.

Unverified: archive sha256 b4478b65a3610cb756b2d929d6795d7dd52e7a5babe9e9d517e5933210a8c026, size 41744, zip members, and native/notify-launch 91491b52b824d340758e48c73804d09bcd789553b1a2373c3ed140af4786def0. The zip and launcher were not supplied. --abi was not run.

Please attach the archive or a member listing plus the raw digest, and the notify-launch bytes. Keep the note that files_sha256 omits manifest.json by construction and that the archive digest is build stdout only.
