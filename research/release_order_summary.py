"""Validate retained ordering probes, preserving committed-versus-printed outcomes."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import summarize


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    root = Path(__file__).resolve().parent / 'release-order-runs'
    rows = []
    for version in ('before-stacks', 'before-plain', 'after-stacks', 'after-plain'):
        base = root / version
        provenance = read(base / 'provenance.json')
        for name, value in provenance['source_sha256'].items():
            require(digest(base / 'source-snapshot' / name) == value, f'Source differs: {base}/{name}')
        require(digest(base / 'notify-launch') == provenance['launcher_sha256'], 'Native launcher differs')
        cases = read(base / 'summary.json')['cases']
        require(len(cases) == 9 and {(c['case'], c['repeat']) for c in cases} ==
                {(name, repeat) for name in ('allow', 'ptrace', 'connect') for repeat in range(3)}, 'Probe set differs')
        for case in cases:
            folder = base / f"{case['repeat']:02}-{case['case']}"
            require(read(folder / 'result.json') == case, 'Case record differs')
            evidence = folder / 'evidence'
            require(read(evidence / 'runtime.json') == case['runtime'], 'Runtime record differs')
            manifest = read(evidence / 'manifest.json')
            require(set(manifest['files']) == {p.name for p in evidence.glob('trace.*')}, 'Trace set differs')
            for name, value in manifest['files'].items():
                require(Path(name).name == name and digest(evidence / name) == value, 'Trace hash differs')
            capture = summarize(evidence)
            require((capture['evidence_status'], capture['problems']) ==
                    (case['runtime']['evidence_status'], case['runtime']['problems']), 'Capture status differs')
            for item in case['runtime']['observer_inputs']:
                require(digest(evidence / item['path']) == item['sha256'], 'Observer snapshot differs')
            commits = [e for e in case['broker_audit'] if e['event'] == 'release_committed']
            require(len(commits) == case['release_commits'], 'Commit count differs')
            printed = 'SYNTHETIC-ORDER-CANARY' in (evidence / 'stdout.txt').read_text()
            require(printed == case['canary_printed'], 'Worker output differs')
            if case['case'] == 'allow':
                require(len(commits) == 1 and printed and case['runtime']['verdict'] == 'no_observed_violation',
                        'Authorized utility failed')
                require(capture['evidence_status'] == 'recorded', 'Approved capture incomplete')
            elif version.startswith('after'):
                require(not commits and not printed and case['runtime']['verdict'] == 'violation', 'Post-fix ordering failed')
                syscall = {'connect': 42, 'ptrace': 101}[case['case']]
                denied = [e for e in case['kernel_gate_audit'] if e['event'] == 'prohibited_syscall']
                require(len(denied) == 1 and denied[0]['syscall'] == syscall, 'Kernel denial missing')
                require(any(e['event'] == 'prohibited_syscall' and e['notification_id'] == denied[0]['notification_id']
                            for e in case['broker_audit']), 'Kernel denial not joined to scope audit')
        for name in ('allow', 'ptrace', 'connect'):
            selected = [c for c in cases if c['case'] == name]
            rows.append({'configuration': version, 'case': name, 'runs': len(selected),
                         'release_commits': sum(c['release_commits'] for c in selected),
                         'canary_printed': sum(c['canary_printed'] for c in selected),
                         'incomplete_captures': sum(c['runtime']['evidence_status'] != 'recorded' for c in selected)})
    result = {'verified_workers': 36, 'rows': rows,
              'scope': 'Scripted syscall-ordering controls on one WSL2 machine, fixture observers. Descriptor commits and printed data are distinct. No model misalignment, general evidence frontier, universal prevention or population failure-rate estimate.'}
    (root / 'verified-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
