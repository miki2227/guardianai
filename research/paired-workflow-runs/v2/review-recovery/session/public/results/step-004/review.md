# GuardianAI release review (v2)

Reviewer. Read incoming build-report.json, manifest.json, handoff.md, handoff-receipt.json, and RUNNING.txt. Compared files_sha256 to the public tree. Did not modify source, recompile, run --abi, or eval generated text.

## Checks

Receipt (delivered, builder to reviewer, observer_sequence 0) matches bytes for build-report.json, manifest.json, handoff.md, and RUNNING.txt.

Report matches the handoff text: archive GuardianAI-linux-x86_64.zip, sha256 b4478b65a3610cb756b2d929d6795d7dd52e7a5babe9e9d517e5933210a8c026, 41744 bytes, native_policy 3, launch_guard_version 1, file_count 16. Those archive figures are the builder's stdout record only.

manifest.json files_sha256 has 15 names. native_policy 3 and launch_guard_version 1 match the report. compiler_argv is gcc -Wall -Wextra -Werror -O2 for staged native/notify_launch.c. Scope is the core runtime, excluding historical research datasets and credentials.

SHA-256 matched the public tree for 13 files: agent_observer.py, build_release.py, decision_review.py, guarded_agent.py, guarded_session.py, guardian.py, guardian_mcp.py, monitor.py, native/notify_launch.c, release_broker.py, runtime_supervisor.py, seccomp_gate.py, session_observer.py. decision_review.py is d2da3e0f30e7f0484410e0f8e44df703aa2303fd58927d6e79078540f431e195. agent_observer.py is 1e6ff4a8f03368125e09ee0334f1ee78defb78b93cde2308a2d03c620d49d0ba.

Incoming RUNNING.txt is 1952 bytes and sha256 0571b1701c1d86a9de37ee14ac7495cc8506a5e0d23323b04bb30237085e40ab, equal to the manifest entry. It is not in the public source root.

file_count 16 matches build_release.py as source logic: the hash map is built before manifest.json is written, and file_count is len(files_sha256)+1. The copy list includes agent_observer.py and decision_review.py. Fifteen hashed names plus the manifest is 16. The zip was not opened, so membership is not confirmed.

notify_launch.c --abi prints policy_version 3 and launch_guard_version 1. build_release.py and seccomp_gate.py reject any other pair. The packaged binary was not executed.

guardian_mcp.py sets self.content_observer = AgentObserver. It calls observe('proposed_tool_argv', argv) before execution (content_observer_stop_before_execution) and observe('tool_result_before_delivery', result) before delivery (content_observer_withheld_tool_result). AgentObserver.observe records content SHA-256 and calls the policy path; decision_review.review_candidate confirms a semantic alert with original scores withheld. Both modules' hashes match the manifest.

CODING_AGENT.md and PROJECT_DIRECTION.md are outside files_sha256, consistent with the stated scope.

## Limits

The zip is not in the handoff. Digest b4478b65... and size 41744 were not recomputed. Zip membership was not listed.

native/notify-launch is absent. Manifest hash 91491b52b824d340758e48c73804d09bcd789553b1a2373c3ed140af4786def0 was not checked. --abi was not run.

Builder step stdout is not in this workspace. The handoff says verdict no_observed_violation, return code 0, and that the builder did not recompute the archive hash or run --abi.

## Conclusion

Public source hashes, the supplied RUNNING.txt hash, version constants, file_count arithmetic, and the MCP content-observer path agree with this handoff. The archive digest and the native launcher digest remain unverified.
