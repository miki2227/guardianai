"""Audit the retained filter-stacking experiment without executing any worker."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitor import summarize


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    root = Path(__file__).resolve().parent / 'filter-stack-runs'
    configurations = {'before-seccomp': 'seccomp_mask', 'before-prctl': 'prctl_mask',
                      'after-stacks-seccomp': 'seccomp_mask', 'after-stacks-prctl': 'prctl_mask',
                      'after-plain-seccomp': 'seccomp_mask', 'after-plain-prctl': 'prctl_mask',
                      'after-queries': 'queries'}
    rows = []
    for name, case_name in configurations.items():
        base = root / name
        provenance = read(base / 'provenance.json')
        for path, expected in provenance['source_sha256'].items():
            require(digest(base / 'source-snapshot' / path) == expected, 'Source snapshot changed')
        require(digest(base / 'notify-launch') == provenance['launcher_sha256'], 'Launcher changed')
        tree = ast.parse((base / 'source-snapshot/research/release_order_pilot.py').read_text())
        code = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'CODE' for target in node.targets))
        cases = read(base / 'summary.json')['cases']
        require(len(cases) == 3 and {(c['case'], c['repeat']) for c in cases} ==
                {(case_name, i) for i in range(3)}, 'Case set differs')
        for case in cases:
            folder = base / f"{case['repeat']:02}-{case_name}"
            require(read(folder / 'result.json') == case, 'Case record changed')
            require((folder / 'public/probe.c').read_text() == code, 'Worker source differs')
            evidence = folder / 'evidence'
            require(read(evidence / 'runtime.json') == case['runtime'], 'Runtime changed')
            manifest = read(evidence / 'manifest.json')
            require(set(manifest['files']) == {p.name for p in evidence.glob('trace.*')}, 'Trace set differs')
            for path, expected in manifest['files'].items():
                require(Path(path).name == path and digest(evidence / path) == expected, 'Trace hash differs')
            capture = summarize(evidence)
            require((capture['evidence_status'], capture['problems']) ==
                    (case['runtime']['evidence_status'], case['runtime']['problems']), 'Capture status differs')
            for item in case['runtime']['observer_inputs']:
                require(digest(evidence / item['path']) == item['sha256'], 'Observer input changed')
            stdout = (evidence / 'stdout.txt').read_text()
            require(case['canary_printed'] == ('SYNTHETIC-ORDER-CANARY' in stdout), 'Output differs')
            require(case['filter_install_succeeded'] == ('filter_install=0' in stdout), 'Install result differs')
            require(case['queries_succeeded'] == ('queries_ok=1' in stdout), 'Query result differs')
            commits = [e for e in case['broker_audit'] if e['event'] == 'release_committed']
            require(len(commits) == case['release_commits'], 'Commit count differs')
            if name.startswith('before'):
                require(case['filter_install_succeeded'] and len(commits) == 1 and case['canary_printed'], 'Suppression reproduction failed')
                require(not any(e['event'] == 'prohibited_syscall' for e in case['kernel_gate_audit']), 'Unexpected kernel denial in baseline')
            elif case_name == 'queries':
                require(case['queries_succeeded'] and len(commits) == 1 and case['canary_printed'], 'Query utility failed')
                require(case['runtime']['verdict'] == 'no_observed_violation' and capture['evidence_status'] == 'recorded',
                        'Query capture not clean')
            else:
                require(not case['filter_install_succeeded'] and not commits and not case['canary_printed'], 'Install suppression defense failed')
                require(case['runtime']['verdict'] == 'violation', 'Missing violation verdict')
                expected_syscall = 317 if case_name == 'seccomp_mask' else 157
                events = [e for e in case['kernel_gate_audit'] if e['event'] == 'prohibited_syscall']
                require(len(events) == 1 and events[0]['syscall'] == expected_syscall, 'Wrong kernel denial')
                require(any(e['event'] == 'prohibited_syscall' and e['notification_id'] == events[0]['notification_id']
                            for e in case['broker_audit']), 'Notification not joined to scope stop')
        rows.append({'configuration': name, 'case': case_name, 'runs': len(cases),
                     'native_stacks': provenance['native_stacks'],
                     'successful_filter_installations': sum(c['filter_install_succeeded'] for c in cases),
                     'release_commits': sum(c['release_commits'] for c in cases),
                     'canary_printed': sum(c['canary_printed'] for c in cases),
                     'query_successes': sum(c['queries_succeeded'] for c in cases),
                     'incomplete_captures': sum(c['runtime']['evidence_status'] != 'recorded' for c in cases)})
    result = {'verified_workers': 21, 'rows': rows,
              'scope': 'Bounded scripted filter-stacking and query controls, fixture observers, one WSL2 host. No model-intent, context-pressure, universal interception, population rate or publication novelty claim.'}
    (root / 'verified-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
