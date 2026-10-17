"""Offline strict revalidation of saved pilot candidates; never sends API requests."""
import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sqlite3
import sys

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT.parents[1] / 'Tools/localization'))
import translation_workflow as shared
from viking_term_adapter import install


@contextmanager
def readonly(path):
    db = sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()


def inspect():
    flow = shared.Workflow(PROJECT)
    original_helper = shared.bridge.helper
    result = {'checked_at': datetime.now(timezone.utc).isoformat(), 'sessions': []}
    with readonly(flow.db_path) as db:
        config = flow.config(db)
        glossary = flow.glossary(db)
        rules = flow.rules(db, config)
        tasks = db.execute('SELECT * FROM tasks WHERE stage="pilot_translate" AND revision=? AND status="running"',
                           (flow.meta(db, 'revision'),)).fetchall()
        for task in tasks:
            runs = db.execute('SELECT * FROM batch_runs WHERE task_id=? AND token=? ORDER BY round DESC, rowid DESC',
                              (task['id'], task['lease_token'])).fetchall()
            if not runs:
                continue
            run = runs[0]
            payload = json.loads(task['payload'])
            originals = {r['id']: r for r in payload['records']}
            items = {r['record_id']: r for r in db.execute('SELECT * FROM batch_items WHERE task_id=? AND token=?',
                                                         (task['id'], task['lease_token']))}
            report = {'session_id': run['id'], 'task_id': task['id'], 'status': run['status'],
                      'round': run['round'], 'old_receipt': json.loads(run['receipt']), 'records': []}
            for rid in json.loads(task['ids']):
                record = {'id': rid}
                cached = items.get(rid)
                if not cached:
                    record.update(before='Missing result ID', after='Missing result ID')
                else:
                    item = json.loads(cached['item'])
                    row = db.execute('SELECT * FROM records WHERE id=?', (rid,)).fetchone()
                    summary = {'review_summary': json.loads(cached['summary'])}
                    restored = shared.bridge.restore(item['translation'], originals[rid]['protection'])
                    record['extra_square_markers'] = dict(Counter(re.findall(r'\[[^\[\]\r\n]+\]', restored)) -
                        Counter(re.findall(r'\[[^\[\]\r\n]+\]', row['source'])))
                    candidate = dict(task)
                    candidate['ids'] = json.dumps([rid])
                    independent = flow.independent_worker(db, candidate, cached['instance'])
                    for label in ('before', 'after'):
                        shared.bridge.helper = original_helper
                        if label == 'after':
                            install(shared.bridge)
                        try:
                            if not independent:
                                raise ValueError('Independent reviewer instance required for this record')
                            translation, _ = flow.validate_body_row(row, task, summary, item, originals[rid],
                                                                     config, rules, glossary)
                            record[label] = 'pass'
                        except ValueError as error:
                            record[label] = str(error)
                report['records'].append(record)
            report['all_pass_after'] = all(r['after'] == 'pass' for r in report['records'])
            result['sessions'].append(report)
        result['accounting'] = {table: db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                                for table in ('api_calls', 'quality_attempts', 'quality_authors', 'record_lineage')}
    shared.bridge.helper = original_helper
    install(shared.bridge)
    return flow, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    _, report = inspect()
    path = Path(args.report).resolve()
    if not path.is_relative_to(PROJECT / 'TranslateFiles/reports'):
        raise ValueError('Report must be inside project reports')
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'report': str(path), 'sessions': [{k: s[k] for k in
          ('session_id', 'task_id', 'all_pass_after')} for s in report['sessions']]}, ensure_ascii=True))


if __name__ == '__main__':
    main()
