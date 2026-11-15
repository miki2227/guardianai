# To the builder

Receipt hashes for build-report.json, manifest.json, and handoff.md match.

From build_release.py, files_sha256 is filled before manifest.json is written. The 14 names are 12 copied sources (including agent_observer.py) plus RUNNING.txt and native/notify-launch. file_count adds 1 for manifest.json, so 15 matches that code. native_policy 3 and launch_guard_version 1 match notify_launch.c, the build ABI gate, seccomp_gate.py, and the manifest. Twelve public-source hashes match. CODING_AGENT.md and PROJECT_DIRECTION.md sit outside the map, which fits the core-runtime scope.

Unverified: archive sha256 7a3005fc... and size 40092, zip membership of agent_observer.py, native/notify-launch 91491b52..., and RUNNING.txt 0571b170.... The zip and those two files were not in the handoff. Eval of the RUNNING.txt literal failed with SyntaxError; it was not retried.

Please attach the archive (or zip member names plus the raw digest) and the notify-launch and RUNNING.txt bytes. In handoff.md, state that files_sha256 omits manifest.json by construction, and that the report digest is build stdout only.
