# Runtime source navigation

AST lines and SHA-256 for this /workspace/source snapshot. A map only, not proof that observers, stops, or publication are complete.

## Entrypoints

- build_release.py:11 main
- build_release.py:72 __main__
- guarded_agent.py:91 main
- guarded_agent.py:122 __main__
- guarded_session.py:99 __main__
- guardian.py:111 main
- guardian.py:134 __main__
- guardian_mcp.py:413 main
- guardian_mcp.py:435 __main__
- peer_handoff.py:91 main
- peer_handoff.py:101 __main__
- runtime_supervisor.py:375 __main__

## Observer, publication, and stop

- agent_observer.py:25 AgentObserver
- agent_observer.py:36 AgentObserver.observe
- decision_review.py:10 review_candidate
- flow_policy.py:98 FlowPolicy.stop
- guardian_mcp.py:243 CodingSession.acknowledge_stop
- guardian_mcp.py:338 CodingSession.observe_artifacts
- release_broker.py:17 ScopeStop
- release_broker.py:31 judge_release
- release_broker.py:37 ReleaseBroker
- runtime_supervisor.py:27 observe
- session_observer.py:14 SessionObserver
- session_observer.py:101 SessionObserver.observe

## Boundaries

Names are functions, methods, and classes containing observe, stop, publish, handoff, release, or review, plus main and __main__. Hashes cover .py files and native/notify_launch.c. incoming/ is omitted. Nothing was executed.
