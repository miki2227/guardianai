"""Join replayed host observations to exact retained CLI blocks and Jev inputs."""
import hashlib
import json
from pathlib import Path


def main():
    saved = Path(__file__).resolve().parent
    project = saved.parents[2]
    run = saved / 'run'
    load = lambda p: json.loads(p.read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    result = load(run / 'result.json')
    for name, expected in result['source_files_sha256'].items():
        assert digest(project / name.replace('\\', '/')) == expected
    stream = project / 'research/continued-agent-runs/v1/correction-client/stdout.jsonl'
    lines = [json.loads(line) for line in stream.read_text().splitlines()]
    content_root = run / 'agent-content'
    previous = None
    chunks, verdicts, maxima = 0, {}, []
    tool_results, text_bytes = 0, 0
    for sequence in range(len(result['events']) + 1):
        content_path = content_root / f'content-{sequence}.json'
        content = load(content_path)
        receipt = load(content_root / f'decision-{sequence}.json')
        assert receipt['content_sha256'] == digest(content_path)
        assert receipt['previous_content_sha256'] == previous
        previous = receipt['content_sha256']
        verdicts[receipt['verdict']] = verdicts.get(receipt['verdict'], 0) + 1
        text = json.dumps(content['content'], ensure_ascii=False)
        offsets = []
        for chunk in receipt['chunks']:
            path = content_root / chunk['input']
            assert digest(path) == chunk['input_sha256']
            state = load(path)
            assert state['content_sha256'] == receipt['content_sha256']
            start = state['chunk_offset_characters']
            offset = start + state['overlap_context_characters']
            offsets.append(offset)
            assert state['current_content'] == text[start:offset + 2048]
            assert len(path.read_bytes()) <= 20 * 1024
            assert chunk['response']['model'] == 'jev-1.14.0'
            maxima.extend(chunk['scores'].values())
            chunks += 1
        assert receipt['verdict'] == 'not_flagged' and offsets == list(range(0, len(text), 2048))
        if sequence:
            event = result['events'][sequence - 1]
            assert sequence == event['sequence']
            item = lines[event['source_line'] - 1]
            if item['type'] == 'user':
                expected = [b for b in item['message']['content'] if b.get('type') == 'tool_result']
                assert content['kind'] == 'delivered_tool_result' and content['content'] == expected
                tool_results += len(expected)
                text_bytes += sum(len(json.dumps(b, ensure_ascii=False).encode()) for b in expected)
            else:
                expected = [{key: b[key] for key in ('type', 'text', 'thinking', 'name', 'input') if key in b}
                            for b in item['message']['content'] if b.get('type') in ('text', 'thinking', 'tool_use')]
                assert content['kind'] == 'emitted_assistant_message' and content['content'] == expected
    expected_lines = [i for i, item in enumerate(lines, 1) if item['type'] in ('assistant', 'user')]
    assert [e['source_line'] for e in result['events']] == expected_lines
    assert result['completed'] and not result['stops']
    assert result['canonical_ledger_before'] == result['canonical_ledger_after']
    assert result['agent_invocations'] == result['worker_commands'] == 0
    summary = {'records_verified': len(result['events']) + 1, 'tool_result_blocks_verified': tool_results,
               'serialized_tool_result_utf8_bytes': text_bytes, 'jev_chunk_calls': chunks,
               'verdicts': verdicts, 'maximum_question_probability': max(maxima),
               'canonical_quarantine_unchanged': True,
               'scope': 'Retained real-message replay and exact source/input joins. No prospective worker or stop-latency claim; no detector-accuracy estimate.'}
    (saved / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
