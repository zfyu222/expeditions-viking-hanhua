"""Collect three Sol-audited paid replies without changing content or authors."""
import json
from pathlib import Path
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, 'D:/StaticHanHua/Tools/localization')
from translation_workflow import Workflow, write_json, read_json, digest, encoded, fingerprint
from workflow_task_contract import canonical_api_result

project = Path(__file__).resolve().parents[2]
flow = Workflow(project)
assert not (flow.root / 'state/api_round.lock').exists()
names = ['review-r17-01208-57d0d852','review-r17-01314-2d960106-s7e0cbbe7','review-r17-01325-d3431c78-s91fb6310']
folder = flow.root / 'backups' / ('review_format_recovery_' + uuid.uuid4().hex)
folder.mkdir(parents=True)
source = sqlite3.connect(flow.db_path.as_uri() + '?mode=ro', uri=True)
target = sqlite3.connect(folder / 'workflow.sqlite3')
source.backup(target)
target.close(); source.close()
entries = []
with flow.db() as db:
    assert not db.execute('SELECT 1 FROM api_calls WHERE status="reserved"').fetchone()
    calls_before = fingerprint([list(r) for r in db.execute('SELECT * FROM api_calls ORDER BY id')])
    records_before = fingerprint([list(r) for r in db.execute('SELECT * FROM records ORDER BY ordinal')])
    for name in names:
        audits = list((flow.root / 'tasks' / name / 'handoffs').glob('*/response.format_recovery.audit.json'))
        assert len(audits) == 1
        audit = read_json(audits[0])
        sid = audit['source_session_id']
        run = dict(db.execute('SELECT * FROM batch_runs WHERE id=?', (sid,)).fetchone())
        task = dict(db.execute('SELECT * FROM tasks WHERE id=?', (name,)).fetchone())
        assert task['status'] == 'running' and task['lease_token'] == run['token']
        assert not db.execute('SELECT 1 FROM batch_items WHERE task_id=? AND token=?', (name, run['token'])).fetchone()
        assert audit['task_input_hash'] == task['input_hash']
        for field in ('raw', 'input', 'transport'):
            assert digest(audit['source_' + field + '_path']) == audit['source_' + field + '_sha256']
        response = audits[0].with_name('response.format_recovered.json')
        assert digest(response) == audit['recovered_sha256']
        canonical = canonical_api_result(read_json(response), read_json(audit['source_transport_path']),
            sid, name, task['input_hash'], json.loads(run['scope']))
        assert len(canonical['records']) == len(json.loads(run['scope']))
        output = response.with_name('result.format_recovered.canonical.json')
        write_json(output, canonical)
        latest = audit['latest_session_id']
        if latest != sid:
            other = dict(db.execute('SELECT * FROM batch_runs WHERE id=?', (latest,)).fetchone())
            assert other['task_id'] == name and other['token'] == run['token'] and other['status'] == 'waiting'
            db.execute('UPDATE batch_runs SET status=?,receipt=? WHERE id=?',
                ('format_recovery_unused', encoded({'status':'format_recovery_unused', 'reason':audit['selection_reason'], 'recovered_session':sid}), latest))
        db.execute('UPDATE batch_runs SET status=?,result_file=?,receipt=NULL WHERE id=?', ('waiting', str(output), sid))
        old_until = task['lease_until']
        if old_until < time.time():
            db.execute('UPDATE tasks SET lease_until=? WHERE id=?', (time.time()+flow.config(db)['lease_seconds'], name))
        entry = dict(task_id=name, session_id=sid, actual_author=run['worker'],
            audit=audit, canonical_result=str(output), prior_session_status=run['status'],
            prior_session_receipt=run['receipt'], prior_lease_until=old_until,
            preserved_attempt=task['attempt'])
        entries.append(entry)
    flow.event(db, 'review_paid_format_recovery', {'backup':str(folder), 'entries':entries, 'semantic_content_unchanged':True})
receipts = [flow.batch_finish(e['session_id']) for e in entries]
with flow.db() as db:
    assert calls_before == fingerprint([list(r) for r in db.execute('SELECT * FROM api_calls ORDER BY id')])
    assert records_before == fingerprint([list(r) for r in db.execute('SELECT * FROM records ORDER BY ordinal')])
    assert all(r['status'] == 'submitted' for r in receipts)
    for entry in entries:
        assert db.execute('SELECT attempt FROM tasks WHERE id=?', (entry['task_id'],)).fetchone()[0] == entry['preserved_attempt']
    report = dict(status='collected', backup=str(folder), entries=entries, receipts=receipts,
        recovered_records=sum(r['records'] for r in receipts), api_history_unchanged=True,
        formal_records_unchanged=True, quality='candidates_saved; not_semantic_acceptance',
        summary=flow.batch_summary(db))
write_json(folder / 'report.json', report)
write_json(flow.root / 'reports/review_paid_format_recovery_e6e1efeb.json', report)
print(json.dumps({'status':report['status'], 'recovered_records':report['recovered_records'], 'summary':report['summary']}))
