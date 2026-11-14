# Actual application build and standalone run

Following the user's direction to run the project as a real system, the launcher
ran ordinary GCC compilation and application packaging under live Jev oversight.
No new probe suites, artificial attack cases or model-agent sessions were added
for this work.

The completed distribution is
[`original GuardianAI-linux-x86_64.zip`](../dist/archive-v1/GuardianAI-linux-x86_64.zip), a core-runtime
archive containing the Python supervisor, kernel notification adapter, broker,
native source, compiled policy-3 helper, build tool, usage instructions and a
per-file hash manifest. It excludes historical research datasets and credentials.
The native helper was compiled on Kali WSL2 and needs compatible Linux x86-64
runtime libraries; its C source is included for rebuilding on the target system.

Original archive SHA-256 (the latest package adds shared sessions; see [SESSION.md](../SESSION.md)):
`cd5746a0182882992bc8f0bddbe6470314982fb483448dc1a1ba8265b629459f`.

The first guarded build stopped correctly with an abstention after the remote
observer rejected a growing cumulative request. Replaying the failed request
returned HTTP 400 with `max_tokens_exceeded`. Its event snapshot was 64,749 bytes;
that is a serialized byte count, not a measured token count. The failed build and
diagnostics remain in `system-runs/build-failed-context-limit`.

## Runtime change required by actual work

The supervisor now submits bounded event batches instead of repeatedly submitting
the entire growing history. Each serialized event batch is capped at 8 KiB. New
events and later native-frame revisions remain pending until submitted; stored
inputs carry their original event indices. Events are not silently discarded to
make a request fit. A single oversized event still causes abstention, as do model
faults, deadlines and backlog exhaustion. HTTP faults now record their status code.

This is a streaming observation contract. Jev sees each batch with the task and
policy; earlier batches remain in local evidence rather than being supplied in
every request. Cross-batch semantic patterns can be missed. The byte cap is an
engineering bound on event payload, not a guarantee about tokenizer counts or
arbitrarily long task text. These limits must remain explicit in research claims.
TypeSafe documents separate per-request/per-question context limits and the
`max_tokens_exceeded` error. [Model context](https://docs.typesafe.ai/models),
[request errors](https://docs.typesafe.ai/api/errors).

## Completed real workloads

The development launcher built the current source distribution using GCC, then
wrote its archive and build report in `/output`. It completed with worker exit 0,
`no_observed_violation`, and a recorded capture. It submitted 155 final scoped
events in 23 observer requests; the largest serialized event batch was 8,176 bytes.

The packaged application then ran from its own directory outside the development
checkout and rebuilt the distribution from its packaged source. That standalone
run also completed with exit 0 and `no_observed_violation`. Its 155 final scoped
events were submitted in 25 requests, with a maximum event batch of 8,077 bytes.
The standalone launcher used its packaged helper and modules, not imports from
the development checkout.

All recorded final event revisions matched a submitted frozen observer input in
both runs, and each input hash was checked. The delivered ZIP's member bytes match
its per-file manifest. These are inspections of real build artifacts and runtime
evidence; they do not establish complete telemetry, malicious-intent detection,
security recall or journal novelty. No new unit suite was run after the streaming
change; the earlier 92-test result belongs to the policy-3 validation revision.

See the [actual-run summary](system-runs/build-summary.json),
[original build report](../dist/archive-v1/build-report.json) and retained runtime directories.

## Build or run

On Linux/WSL, an ordinary local build is:

```sh
python3 build_release.py --output /new/release-directory
```

To build under the actual observer, use an empty output directory and a new
evidence directory:

```sh
python3 guarded_agent.py \
  --task 'Build the public GuardianAI runtime using gcc and build_release.py; write the distribution only in /output.' \
  --workspace /path/to/guardianai-source \
  --output /path/to/empty-output --evidence /path/to/new-evidence \
  --sensor /path/to/strace -- \
  /usr/bin/python3 /workspace/build_release.py --output /output
```

The trusted supervisor needs the configured Jev credential. The worker receives
neither that credential nor external network access. The archive's `RUNNING.txt`
also explains normal guarded command execution and protected-resource provisioning.
