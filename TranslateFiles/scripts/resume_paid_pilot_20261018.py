"""Audited one-time r12 recovery. Offline only; never imports an API requester."""
import json
import shutil
import subprocess
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT.parents[1] / 'Tools/localization'))
import translation_workflow as shared
REASON = ('User explicitly authorized restoring default pilot execution limit from 6 to 12 on '
          '2026-10-18, retaining all 5 spent executions, paid responses and r8 freeze. '
          'Project-only recovery; no semantic rule or revision change.')


def main():
    flow = shared.Workflow(PROJECT)
    root = flow.root
    assert not (root / 'state/api_round.lock').exists(), 'API executor lock exists'
    processes = subprocess.check_output(['powershell', '-NoProfile', '-Command',
        'Get-CimInstance Win32_Process | Where-Object { $_.Name -match "python" } | Select-Object ProcessId,CommandLine | ConvertTo-Json'], text=True)
    assert not any(name in processes for name in ('api_round.py', 'run_api_round.py')), 'Executor still running'
    audit_id = 'resume_paid_pilot_' + uuid.uuid4().hex
    backup = root / 'backups' / audit_id
    backup.mkdir()
    with flow.db() as db:
        assert flow.meta(db, 'revision') == 12
        assert flow.config(db)['pilot_call_limit'] in (6, 12)
        assert flow.pilot_spent(db) == 5
        assert not db.execute('SELECT 1 FROM api_calls WHERE status NOT IN ("received","cancelled")').fetchone()
        assert not db.execute('SELECT 1 FROM batch_repair_plans WHERE status!="done"').fetchone()
        old_config = flow.config(db)
        assert shared.read_json(root / 'config/workflow.json') == old_config
        old_paused = flow.meta(db, 'paused')
        tasks = db.execute('SELECT * FROM tasks WHERE status="running"').fetchall()
        assert len(tasks) == 3 and all(t['stage'] == 'pilot_translate' and t['backend'] == 'api' for t in tasks)
        runs = []
        for task in tasks:
            run = db.execute('SELECT * FROM batch_runs WHERE task_id=? AND token=? ORDER BY round DESC,rowid DESC LIMIT 1', (task['id'], task['lease_token'])).fetchone()
            assert run['status'] in ('repair_required', 'needs_attention', 'waiting')
            assert db.execute('SELECT 1 FROM api_calls WHERE session_id=? AND status="received"', (run['id'],)).fetchone()
            runs.append(dict(run))
        snapshot = {table: [dict(r) for r in db.execute('SELECT * FROM ' + table)]
                    for table in ('tasks', 'batch_runs', 'batch_items', 'api_calls', 'quality_attempts', 'quality_authors')}
        snapshot.update(revision=12, config=old_config, processes=processes)
        shared.write_json(backup / 'before.json', snapshot)
    import sqlite3
    with sqlite3.connect(f'file:{flow.db_path.as_posix()}?mode=ro', uri=True) as source:
        with sqlite3.connect(backup / 'workflow.sqlite3') as destination:
            source.backup(destination)
    shutil.copy2(root / 'config/workflow.json', backup / 'workflow.json')
    if old_config['pilot_call_limit'] == 6:
        flow.pause(True)
        flow.configure({'pilot_call_limit': 12}, REASON, impact='none')
        flow.pause(old_paused)
    receipts = []
    for run in runs:
        with flow.db() as db:
            assert not db.execute('SELECT 1 FROM batch_runs WHERE task_id=? AND token=? AND round>?', (run['task_id'], run['token'], run['round'])).fetchone()
            assert not db.execute('SELECT 1 FROM api_calls WHERE status="reserved"').fetchone()
            task = db.execute('SELECT * FROM tasks WHERE id=?', (run['task_id'],)).fetchone()
            if task['lease_until'] < time.time():
                until = time.time() + flow.config(db)['lease_seconds']
                db.execute('UPDATE tasks SET lease_until=? WHERE id=?', (until, task['id']))
                flow.event(db, 'project_restore_expired_paid_candidate_lease', {'task': task['id'], 'token': task['lease_token'], 'before': task['lease_until'], 'after': until, 'reason': 'Verified executor stopped and received terminal request; preserve original task/token/candidates for local revalidation', 'backup': str(backup)})
            db.execute('UPDATE batch_runs SET status="waiting" WHERE id=?', (run['id'],))
            flow.event(db, 'project_reopen_terminal_for_literal_recheck', {'session': run['id'], 'old_receipt': json.loads(run['receipt']), 'backup': str(backup), 'reason': 'Revalidate unchanged paid candidates under project literal adapter; no later or in-flight session'})
        receipts.append(flow.batch_finish(run['id']))
    # Shared batch_finish invokes validate_body_row through validate_body_item.
    # Verify unchanged paid candidate bytes, task identity and all prior lineage.
    with flow.db() as db:
        for old in snapshot['batch_items']:
            now = db.execute('SELECT * FROM batch_items WHERE task_id=? AND token=? AND record_id=?', (old['task_id'], old['token'], old['record_id'])).fetchone()
            assert all(now[k] == old[k] for k in ('item', 'instance', 'summary'))
        assert sum(r['preserved_records'] for r in receipts) == 16
        assert sum(len(r['failed_ids']) for r in receipts) == 14
    sessions = []
    for receipt in receipts:
        worker = 'api-pilot_translate-' + uuid.uuid4().hex
        reason = ('Sol-directed recovery: fix only the actual current term diagnostics after literal-marker adapter. '
                  'Judge ordinary senses from source and supply justified per-row exceptions when appropriate; '
                  'preserve all already satisfied terms and protection. Do not insert unused game markers.')
        session = flow.batch_repair(receipt['session_id'], worker, reason=reason if receipt['status'] == 'needs_attention' else None)
        sessions.append(session)
        assert session['repair_parts'] == 1, 'Unexpected split; stop before further allocation'
        text = Path(session['input_file']).read_text(encoding='utf-8')
        for line in text.splitlines():
            if line.startswith('{'):
                value = json.loads(line)
                for term in value.get('shared_terms', {}).values():
                    assert not (len(term['src']) == 1 and '[' in term.get('dst', '')), 'Pseudo term contamination'
    with flow.db() as db:
        assert flow.meta(db, 'revision') == 12 and len(snapshot['api_calls']) == db.execute('SELECT count(*) FROM api_calls').fetchone()[0]
        assert flow.pilot_spent(db) == 8
        assert shared.read_json(root / 'config/workflow.json') == flow.config(db)
        assert all(not db.execute('SELECT 1 FROM api_calls WHERE session_id=?', (s['session_id'],)).fetchone() for s in sessions)
    report = {'audit_id': audit_id, 'time': datetime.now(timezone.utc).isoformat(), 'backup': str(backup),
              'budget': {'before': 6, 'after': 12, 'spent_before': 5, 'spent_after_allocation': 8},
              'recheck_receipts': receipts, 'unissued_api_sessions': sessions, 'pilot_plan': flow.pilot_plan(),
              'remaining_strategy': '3 allocated repair calls plus 3 independent review batches = projected 11/12 total; 1 execution remains for necessary repair. Sol acceptance still required.'}
    shared.write_json(root / 'reports/paid_pilot_resume_20261018.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
