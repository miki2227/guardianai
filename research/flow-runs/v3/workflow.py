"""Actual public release and internal baseline indexing under a flow policy."""
import hashlib
import json
from pathlib import Path
import sys

BASE = Path('/home/pratz/guardianai-flow-v3')
RUNTIME = BASE / 'bootstrap/guardianai-linux-x86_64'
sys.path.insert(0, str(RUNTIME))
from agent_observer import AgentObserver
from flow_policy import FlowPolicy
from guarded_agent import load_resources, run_worker
from guarded_handoff import deliver
from release_broker import ReleaseBroker
from session_observer import SessionObserver


def main():
    evidence = BASE / 'evidence'
    evidence.mkdir()
    source = BASE / 'source'
    launcher = RUNTIME / 'native/notify-launch'
    workers = {'builder': ['/usr/bin/python3', '/workspace/build_release.py', '--output', '/output'],
               'indexer': ['/usr/bin/python3', '-c',
                   "from pathlib import Path; import json,hashlib; raw=Path('/protected/previous_release').read_bytes(); old=json.loads(raw)['files_sha256']; current={str(p.relative_to('/workspace')):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/workspace').rglob('*') if p.is_file()}; old={k:v for k,v in old.items() if k.endswith(('.py','.c'))}; result={'baseline_manifest_sha256':hashlib.sha256(raw).hexdigest(),'changed':[k for k in current if k in old and current[k]!=old[k]],'added':sorted(set(current)-set(old)),'unchanged':[k for k in current if current[k]==old.get(k)]}; Path('/output/change-index.json').write_text(json.dumps(result,indent=2)+'\\n'); print('indexed',len(current),'source files')"]}
    for name in workers:
        (BASE / (name + '-output')).mkdir()
    snapshots = load_resources({'previous_release': str(BASE / 'private/previous-manifest.json')},
                              [source, *[BASE / (name + '-output') for name in workers],
                               *[Path(p).resolve() for p in ('/usr', '/bin', '/lib', '/lib64') if Path(p).exists()]], launcher)
    task = ('Build a public GuardianAI release and compare public source against the approved previous_release '
            'protected manifest. Its internal-baseline label is a controlled classification of real project '
            'metadata. Both workers may read it, but only the indexer needs to. The change index may go to '
            'the internal reviewer; it must not go to a public reviewer. The public builder report may go '
            'to the public reviewer if the builder has not received internal data. All handoffs are '
            'trusted-host mediated. Write only /output; private /tmp scratch is allowed. No network, '
            'secret access beyond this approved resource, source mutation or tests are needed.')
    broker = ReleaseBroker(task, snapshots, {name: {'previous_release'} for name in workers})
    flow = FlowPolicy(BASE / 'flow-policy.json',
                      {name: (['internal-baseline'] if name != 'public-reviewer' else [])
                       for name in ('builder', 'indexer', 'internal-reviewer', 'public-reviewer')},
                      {'previous_release': ['internal-baseline']}, on_stop=broker.revoke)
    broker.exposure = lambda principal, resource, digest: flow.expose(principal, resource, digest)
    observer = SessionObserver(broker, evidence, flow_context=flow.exposure_context)
    broker.observer = observer.authorize
    def run(name):
        return run_worker(task + ' Current worker: ' + name + '.', source, workers[name],
                          output=BASE / (name + '-output'), evidence=evidence / name,
                          sensor='/home/pratz/guardianai-tools/unpacked/usr/bin/strace',
                          broker=broker, principal=name, launcher=launcher, timeout=90,
                          observer=lambda task, events: observer.observe(name, task, events))
    reports = {name: run(name) for name in workers}
    (BASE / 'worker-summary.json').write_text(json.dumps({name: {'verdict': r['verdict'],
        'returncode': r['runtime']['returncode']} for name, r in reports.items()}, indent=2) + '\n')
    if any(r['verdict'] != 'no_observed_violation' or r['runtime']['returncode'] != 0 for r in reports.values()):
        flow.stop()
        raise RuntimeError('Ordinary worker task failed; retained worker reports have details')
    handoff_observer = AgentObserver(task, BASE / 'handoff-observer',
                                     context=lambda: {'flow_policy': flow.state['policy'],
                                                       'exposure_labels': flow.state['labels']}, stop=flow.stop)
    transfers = []
    transfers.append(deliver(handoff_observer, 'builder', 'public-reviewer',
                             [BASE / 'builder-output/build-report.json'], BASE / 'public-handoff', flow=flow))
    transfers.append(deliver(handoff_observer, 'indexer', 'internal-reviewer',
                             [BASE / 'indexer-output/change-index.json'], BASE / 'internal-handoff', flow=flow))
    if not all(row['delivered'] for row in transfers):
        raise RuntimeError('Permitted handoff failed; no denial demonstration is inferred')
    # A new task epoch does not erase a participant's earlier possible exposure.
    broker.replace_task('Prepare public release documentation; previous private access is revoked.',
                        {name: set() for name in workers})
    before_denial = json.loads((BASE / 'flow-policy.json').read_text())
    (BASE / 'before-denial.json').write_text(json.dumps(before_denial, indent=2) + '\n')
    transfers.append(deliver(handoff_observer, 'indexer', 'public-reviewer',
                             [BASE / 'indexer-output/change-index.json'], BASE / 'blocked-handoff', flow=flow))
    transfers.append(deliver(handoff_observer, 'builder', 'public-reviewer',
                             [BASE / 'builder-output/build-report.json'], BASE / 'after-stop-handoff', flow=flow))
    with broker.lock:
        audit = list(broker.audit)
        stopped, epoch = broker.stop_event.is_set(), broker.epoch
    result = {'transfers': transfers, 'broker_stopped': stopped, 'broker_epoch': epoch,
              'broker_audit': audit, 'flow_labels': flow.state['labels'],
              'blocked_directory_exists': (BASE / 'blocked-handoff').exists(),
              'after_stop_directory_exists': (BASE / 'after-stop-handoff').exists(),
              'private_manifest_sha256': hashlib.sha256(snapshots['previous_release']).hexdigest(),
              'scope': 'Two unmodified Linux programs do real release/index work. Internal labels are a controlled classification of actual release metadata. No new model-agent population, malicious objective or covert code. The fixed denial demonstrates an explicit information-flow rule, not detection of hidden intent. One trusted coordinator owns the ledger.'}
    (BASE / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'deliveries': [r['delivered'] for r in transfers], 'broker_stopped': stopped,
                      'labels': flow.state['labels']}), flush=True)


if __name__ == '__main__':
    main()
