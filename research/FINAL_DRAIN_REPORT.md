# Final trace draining and real release build

15 November 2026. Source inspection found a completion race in `supervise`: the
reader processes at most 4,096 lines per trace in one pass, but could accept process
exit after that pass without proving EOF. A chunk containing no scoped events
could therefore leave a later chunk unread. Files created while the pass was in
progress could also miss that final read. This is a source-derived finding, not a
failure observed in the retained earlier build runs.

The runtime now observes tracer exit before enumerating the final trace set,
distinguishes bounded reads from EOF, and continues draining until all files reach
EOF and outstanding observer work settles. A nonempty incomplete line after
tracer exit causes abstention. The report records `final_trace_drained`; that flag
describes this reader condition, not proof of complete kernel telemetry.

The corrected source was packaged on Kali WSL2. Its standalone packaged launcher
then supervised actual GCC compilation and release packaging under live Jev,
outside the development checkout. The worker completed with exit 0,
`no_observed_violation`, a recorded capture and `final_trace_drained: true`.
All 177 final scoped event revisions matched retained submitted observer inputs;
31 input receipts and their hashes were checked.

This ordinary workflow verifies operation after the change. It does not reproduce
the high-volume race, isolate its frequency, prove universal observation, or
evaluate malicious-agent accuracy. No synthetic attack case or unit suite was
added for this correction.

The [run summary](system-runs/final-drain-build/summary.json), source snapshot,
native traces, decisions and compiled outputs are retained together. The current
[runtime archive](../dist/GuardianAI-linux-x86_64.zip) has SHA-256
`7e58ba189e0a56fdc8cd1ee6b8230d56a52099ee181174d8b80f0b9223267253`.
The prior shared-observer release remains in [archive-v3](../dist/archive-v3/build-report.json).
