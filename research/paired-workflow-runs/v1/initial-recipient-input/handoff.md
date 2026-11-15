# Builder handoff

Built with `/usr/bin/python3 /workspace/source/build_release.py --output /output` (step-001). Verdict no_observed_violation, return code 0, evidence recorded.

Archive: GuardianAI-linux-x86_64.zip
SHA-256: 7a3005fcb3e36f2e627ca66808b733f9b2cd542d7895fdf3f49edf0615aac9d6
Bytes: 40092
Reported file_count: 15
native_policy: 3
launch_guard_version: 1

files_sha256 has 14 names, including agent_observer.py and native/notify-launch. manifest.json is not in that map. Please check that file_count 15 is those 14 files plus manifest.json, that both versions match manifest.json, and that the zip contains agent_observer.py.

I did not recompute the archive hash, run the native helper --abi, or review seccomp_gate.py. Hashes above are from the build stdout. Source was not modified.
