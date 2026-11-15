"""Retrieve older lexical matches from immutable, hash-verified evidence files."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3


class EvidenceMemory:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.database = self.root / 'history.sqlite3'
        with closing(sqlite3.connect(self.database, timeout=1)) as db, db:
            db.execute('CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, path TEXT UNIQUE, sha256 TEXT, kind TEXT)')
            db.execute('CREATE VIRTUAL TABLE IF NOT EXISTS history USING fts5(body)')

    def record(self, source, kind):
        source = Path(source).resolve(strict=True)
        relative = str(source.relative_to(self.root))
        raw = source.read_bytes()
        if len(raw) > 256 * 1024:
            raise ValueError('History record exceeds its byte budget')
        text = raw.decode('utf-8')
        digest = hashlib.sha256(raw).hexdigest()
        with closing(sqlite3.connect(self.database, timeout=1)) as db, db:
            previous = db.execute('SELECT sha256, kind FROM documents WHERE path=?', (relative,)).fetchone()
            if previous:
                if previous != (digest, kind):
                    raise ValueError('Indexed evidence changed')
                return
            row = db.execute('INSERT INTO documents(path,sha256,kind) VALUES(?,?,?)', (relative, digest, kind))
            db.execute('INSERT INTO history(rowid,body) VALUES(?,?)', (row.lastrowid, text))

    def lookup(self, query, *, exclude=()):
        terms = re.findall(r'(?:/[A-Za-z0-9_.-]+){2,}|[a-fA-F0-9]{32,64}|[A-Za-z_][A-Za-z0-9_]{3,}', query)
        terms = sorted({term for term in terms if len(term) <= 256}, key=lambda x: (-len(x), x))[:16]
        excluded = [str(Path(path).resolve().relative_to(self.root)) for path in exclude]
        with closing(sqlite3.connect(self.database, timeout=1)) as db:
            indexed = db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
            result = {'indexed_records': indexed, 'root_relative_to_input': '.', 'query_terms': terms, 'matched_records': 0, 'matched_records_omitted': 0, 'hits': [],
                      'scope': 'Lexical retrieval of earlier evidence, not semantic completeness, current permissions or proof of intent. Excerpts are copied from verified source files; omitted context remains on disk.'}
            if not terms:
                return result
            expression = ' OR '.join('"' + term + '"' for term in terms)
            where = 'history MATCH ?'
            parameters = [expression]
            if excluded:
                where += ' AND d.path NOT IN (' + ','.join('?' for _ in excluded) + ')'
                parameters += excluded
            joined = ' FROM history JOIN documents d ON d.id=history.rowid WHERE ' + where
            result['matched_records'] = db.execute('SELECT COUNT(*)' + joined, parameters).fetchone()[0]
            rows = db.execute('SELECT d.path,d.sha256,d.kind' + joined + ' ORDER BY bm25(history),d.id DESC LIMIT 3', parameters).fetchall()
        for name, expected, kind in rows:
            path = (self.root / name).resolve(strict=True)
            if not path.is_relative_to(self.root):
                raise ValueError('History source escaped its evidence root')
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError('Retrieved evidence hash mismatch')
            text = raw.decode('utf-8')
            positions = [text.lower().find(term.lower()) for term in terms]
            position = next((p for p in positions if p >= 0), 0)
            start = max(0, position - 256)
            result['hits'].append({'source': name, 'sha256': expected, 'kind': kind,
                                   'start_character': start, 'total_characters': len(text),
                                   'excerpt': text[start:start + 1024]})
        result['matched_records_omitted'] = result['matched_records'] - len(result['hits'])
        return result


def fit_history(state):
    """Drop low-ranked history before changing the existing context budgets."""
    retrieval = state.get('history_retrieval')
    if retrieval is not None:
        while True:
            retrieval['matched_records_omitted'] = retrieval['matched_records'] - len(retrieval['hits'])
            if len(json.dumps(state).encode()) <= 20 * 1024 or not retrieval['hits']:
                break
            retrieval['hits'].pop()
