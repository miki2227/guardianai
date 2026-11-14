# Private name-service failure emulation

15 November 2026. In the retained real Grok pilot, an ordinary `ls -la` command
requested `/var/run/nscd/socket`. The all-connect terminal rule stopped its scope.
That was a benign workload failure, not evidence of malicious intent. The new
gate preserves the network block while returning a supported failure for this
specific local service lookup.

For an x86-64 `connect` notification, the gate copies at most 110 sockaddr bytes.
Only AF_UNIX with the exact pathname `/var/run/nscd/socket` or
`/run/nscd/socket` receives the constant error `ENOENT`. The gate does not execute
the connection, open a service socket or use `CONTINUE`; changing the target's
memory after inspection cannot turn this branch into a connection. Other
connection requests still enter the existing terminal-denial branch. This is a
bounded implementation argument under the trusted-gate assumptions, not a
universal network or intent-detection proof.
[UNIX socket layout](https://man7.org/linux/man-pages/man7/unix.7.html),
[notification replies and continuation caveats](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html).

The audit records `local_service_lookup_denied`, the notification ID, native PID,
pathname and reply errno. Supported runtime manifests declare
`nscd_missing_service_emulation`. Only a matching AF_UNIX pathname with completed
`ENOENT`, under that declared profile, receives
`connect_disposition: emulated_missing_nscd` in the live and retrospective views.
The supplied observer state explains that no service access occurred. Raw capture
and old manifests without this profile declaration retain their prior behavior.
These optional fields extend the evidence format without renaming existing ones.

## Actual operation

The packaged supervisor replayed the exact earlier Grok argv: public file
discovery followed by a metadata listing. The original command and the hash of
its source record are retained in
[reference-command.json](system-runs/nss-compat/reference-command.json).
No new model-agent inference was launched for this work.

The listing completed with exit 0, `no_observed_violation`, a recorded capture
and a fully drained trace. Four NSS notification records matched four completed
ENOENT events carrying the new disposition. It produced 23 scoped events and
three saved observer inputs. The same session then completed actual GCC release
compilation/packaging, with 236 scoped events and 41 inputs. Every final event
revision from both operations matched a submitted frozen input and its hash;
the retrospective rule interpretation also returned `no_observed_violation`.
Normal MCP closure was recorded.

The task declaration and input revision differ from the earlier failed pilot.
This is a successful real-command replay, not a matched classifier-accuracy
experiment. The abstract UNIX namespace, other pathname sockets and ordinary
network requests are not added to the exception. This run does not reproduce
every denial route or adversarial pointer interleaving. A forged harmless-looking
request can receive the same constant failure; its latent intent remains unknown.
The correction is a compatibility mechanism using existing notification
facilities, not established journal-level novelty.

The [summary](system-runs/nss-compat/summary.json), controller, source snapshot,
native traces, gate audit and Jev inputs/decisions are retained together. Earlier
failed evidence is unchanged. The current [runtime archive](../dist/GuardianAI-linux-x86_64.zip)
has SHA-256 `07acd5e884564b530637f564a0b3054c1fbbaaa3bd3ce7e0dd9d256f603b66d3`.
Archive/member hashes and packaged Python/C sources were checked. The earlier
lifetime-guard package remains in `dist/archive-v6`.
