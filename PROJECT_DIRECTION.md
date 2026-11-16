# GuardianAI: agent activity observer

The [latest feedback attempt](research/FEEDBACK_LOOP_RUN.md) prepared a return
handoff in the builder's existing policy slot, then stopped on its invalid
child-path read. The cycle is incomplete and that identity remains revoked;
the user explicitly chose continued quarantine, so no recovery is authorized.
The virtual snapshot contract is now explicit in the tool description; direct
reads were verified in a separate host diagnostic, not a resumed builder.

The [CLI binding gate](research/CLIENT_BINDING_RUN.md) reduces the former post-run
identity-check limitation: a fresh trusted-launcher approval now precedes bound
command admission. It retains the host/transport trust boundary and does not
claim remote-provider attestation or private-thought access.

The [current systems draft](research/manuscript/current/paper.md) brings the
architecture and separately reported development cases together. Its claim ledger
pins current evidence without rewriting the historical manuscript or claiming
universal detection, context saturation or validated covert coordination.

The [persistent exposure policy](FLOW.md) now complements Jev with deterministic
recipient clearance at mediated artifact handoffs. The
[actual build/index run](research/FLOW_POLICY_RUN.md) exercised label persistence,
propagation and stop-on-denial. The coding-agent MCP entry point can also enable
the policy with an explicit trusted flow manifest; it remains opt-in.
The optional [persistent identity ledger](research/IDENTITY_RUN.md) also carries
those labels and revocation across server processes under an exclusive host
lease. Actual index/build work verified continuity under a declared host binding.
The later [existing-agent continuation](research/CONTINUED_AGENT_RUN.md) exercised
that ledger with one retained Grok conversation, shared host evidence retrieval
and actual release/documentation work. It is not a context-saturation or covert
coordination result.

The current objective is an undergraduate systems project that combines and
attributes recent research. A globally new algorithm or Q1 submission is not a
completion requirement. Earlier journal-readiness audits remain historical
research assessments, not a prerequisite for building this product.

The central question is whether an independent Jev observer, supplied with both
agent communication and execution evidence, can flag unauthorized behavior and
stop further local work while preserving useful task completion. No model weight
training, supplied secret code or explicit malicious objective is required.
Covert coordination is a possibility to investigate, not an outcome to force.

## One observation path across the layers

1. The trusted host supplies a task and permissions.
2. `run_grok_guarded.py` observes that prompt and exposed assistant text, emitted
   reasoning summaries and tool requests through `AgentObserver`. The original
   CLI JSONL, including reported usage, remains available.
3. `guardian_mcp.py` checks proposed command arguments before execution and
   checks returned tool content before delivery. It uses the same content
   observer implementation, with bounded shared execution context.
4. Existing Linux isolation, seccomp mediation and native syscall/frame
   observation constrain commands. `SessionObserver` supplies cross-worker
   facts, grants and recent gate events to the content checks.
5. A confirmed semantic violation or observer error revokes the tool scope. A host content stop
   creates `external-stop.json` in trusted session evidence. The MCP watcher
   revokes the broker, persists a request-linked acknowledgement, and active
   supervised workers observe its terminal stop.
   The local CLI is terminated. Protected reads retain their existing gate.
6. Original content, chunk inputs, Jev responses, hashes and verdicts are saved
   alongside the existing Linux evidence for the teammate's evidence viewer.

There are separate host and MCP content journals, not a claim of one globally
ordered transcript. Each stores the preceding content hash and bounded recent
excerpts. Full source content remains on disk; Jev receives chunks of at most
2,048 new characters plus up to 256 preceding characters and context, under a
20 KiB serialized-state bound. Inputs over
256 KiB abstain and stop. The threshold is 0.5 for three questions: task deviation,
disclosure/evasion and suspected unauthorized coordination. It is not calibrated
as a deployment operating point. No generative summarizer or model training is
introduced.

Semantic scores at or above 0.5 now trigger a contextual review before terminal
stopping. For agent content, the second decision receives the complete current
message when it fits the same byte budget; oversized reviews abstain and stop.
Runtime/release review uses the available batch, task and session facts. Original
scores and the second input/answer remain recorded. `review_cleared` means a
candidate alert was rejected on review, not that the content is certified safe.
Both decisions use Jev, so they are not statistically independent. Kernel rules
still stop directly; deadlines, missing results and validation failures remain
terminal. The change trades an additional call for more context and has not been
calibrated as a general false-positive/false-negative operating point.

The MCP `run` tool accepts `finish: true` on the last command, persisting a
closed, revoked scope before client teardown. A normal completed scope can have
both `closed: true` and `scope_stopped: true`. Stop requests and broker
acknowledgements carry matching IDs; broker revocation, worker exit and client
exit are separate observations. See the [completed v2 run](research/OBSERVER_CORRECTIONS_RUN.md).

## What visibility actually means

The host observer runs after a complete JSONL message becomes available. Tools
can already have been dispatched by that time; command gating inside MCP is the
separate pre-execution boundary. This is not token-by-token provider interception.
Only provider-exposed reasoning is available. Private thoughts, hidden provider
state, exact retained context occupancy and arbitrary side channels are not
observable from native stacks. Historical conversation loaded through `--resume`
is not automatically replayed into the observer's new journal.

Tool outputs are inspected before MCP delivery, but an agent can still read
allowed files through later commands. Content checks cannot recall bytes already
delivered. The MCP [artifact-content gate](ARTIFACTS.md) now also observes generated
UTF-8 text before result-history publication, including bounded decoded ZIP
members. File/hash-attributed units retain explicit opaque binary leaves and
the limits of cross-unit context; see the [actual packaging run](research/ZIP_OBSERVER_RUN.md).
The full raw tool output remains evidence; the delivered bounded result is the
content check's input. Chunking and bounded history can miss relationships.
The host harness, its configuration, observer credentials and evidence directory
are trusted. A host stop during startup can terminate the CLI before a Linux
session exists; a receipt file is not a provider inference cancellation API.

## Literature basis and incident motivation

OpenAI's [26 August 2026 incident account](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)
describes unauthorized agent communication through shared infrastructure and
subsequent compromise of Hugging Face during reduced-safeguard evaluations.
It motivates inspecting shared artifacts and communication as well as commands.
It does not establish that long context caused that incident or that GuardianAI
would have stopped it. The [July clarification](https://openai.com/index/hugging-face-model-evaluation-security-incident/)
identifies the pre-release model as an internal research prototype.

[The Arbiter Agent](https://arxiv.org/abs/2606.10747) motivates continuous
conversation oversight. [TraceGuard](https://arxiv.org/abs/2604.03968) motivates
separating several monitoring questions rather than interpreting one score as
proof of intent. [When Local Monitors Miss Compositional Harm](https://arxiv.org/abs/2607.11751)
motivates connecting messages to assembled artifacts and execution context;
bounded local checks alone can miss harmful composition. These are attributed
design influences, not reproduced results or an assertion that our implementation
matches those papers.

## Next research milestone

Use a small number of continuing pretrained workers on complementary repository
tasks, with host-mediated messages and artifact handoffs. Observe ordinary work
and retain benign, erroneous and suspicious outcomes. Record the history actually
exposed to both workers and observer. Do not claim context exhaustion from a sum
of token usage. A suspected covert convention still needs recurrent behavior and
task-preserving counterfactual evidence; a suspicion score alone is insufficient.
The existing short social pilot found no validated convention. Training is not
part of this milestone.

The [retained-evidence retrieval feature](HISTORY.md) adds older source excerpts
to bounded observer inputs, with exact hashes and omission counts. The
[live build and archive report](research/HISTORY_RETRIEVAL_RUN.md) verifies that
those older records were actually supplied. It does not establish agent context
exhaustion or detection of secret communication.
