"""Offline, audited project-only budget update preserving the current revision."""
import json
import shutil
import sqlite3
import uuid
from pathlib import Path
from api_round import PROJECT, VikingAPIWorkflow


def main():
    flow = VikingAPIWorkflow(PROJECT)
    reason = 'User explicitly replaced the 12 execution pilot limit with 100 on 2026-10-18; retain spent attempts, exclusions, task identity and all semantic evidence.'
    audit_id = 'pilot_budget_' + uuid.uuid4().hex
    backup = flow.root / 'backups' / audit_id
    assert not list((flow.root / 'state').glob('*.lock')), 'Executor lock exists'
    tables = ('tasks', 'batch_runs', 'batch_items', 'api_calls', 'quality_attempts', 'quality_authors', 'pilot_attempt_exclusions')
    with flow.db() as db:
        before = flow.config(db)
        assert before['pilot_call_limit'] == 12
        assert json.loads((flow.root / 'config/workflow.json').read_text(encoding='utf-8')) == before
        assert not db.execute('SELECT 1 FROM api_calls WHERE status NOT IN ("received","cancelled")').fetchone()
        # Historical waiting runs may belong to obsolete/done tasks. Only a
        # current live lease can represent an outstanding local handoff.
        assert not db.execute('SELECT 1 FROM batch_runs b JOIN tasks t ON t.id=b.task_id AND t.lease_token=b.token WHERE t.status="running" AND b.status="waiting" AND NOT EXISTS (SELECT 1 FROM batch_runs n WHERE n.task_id=b.task_id AND n.token=b.token AND (n.round>b.round OR (n.round=b.round AND n.rowid>b.rowid)))').fetchone()
        tasks = db.execute('SELECT * FROM tasks WHERE status="running"').fetchall()
        assert len(tasks) == 3
        for task in tasks:
            assert task['stage'] == 'pilot_review'
            run = db.execute('SELECT * FROM batch_runs WHERE task_id=? AND token=? ORDER BY round DESC,rowid DESC LIMIT 1', (task['id'], task['lease_token'])).fetchone()
            assert run['status'] in ('repair_required', 'needs_attention', 'failed')
        usage = flow.pilot_usage(db)
        assert usage == {'raw': 14, 'exempt': 2, 'effective': 12}, usage
        snapshot = {t: [dict(r) for r in db.execute('SELECT * FROM ' + t)] for t in tables}
        revision = flow.meta(db, 'revision')
        glossary = flow.meta(db, 'glossary')
        paused = flow.meta(db, 'paused')
    backup.mkdir(parents=True)
    with sqlite3.connect(flow.db_path) as source, sqlite3.connect(backup / 'workflow.sqlite3') as destination:
        source.backup(destination)
    shutil.copy2(flow.root / 'config/workflow.json', backup / 'workflow.json')
    flow.pause(True)
    with flow.db() as db:
        assert flow.config(db) == before
        assert all(snapshot[t] == [dict(r) for r in db.execute('SELECT * FROM ' + t)] for t in tables)
        after = {**before, 'pilot_call_limit': 100}
        flow.put(db, 'config', after)
        from translation_workflow import write_json
        write_json(flow.root / 'config/workflow.json', after)
        audit = {'before': before, 'after': after, 'reason': reason, 'revision': revision, 'semantic_reset': False, 'usage': usage, 'backup': str(backup)}
        write_json(flow.root / 'history' / (audit_id + '.json'), audit)
        flow.event(db, 'project_pilot_budget_change', audit)
        assert flow.meta(db, 'revision') == revision
        assert flow.meta(db, 'glossary') == glossary
        assert all(snapshot[t] == [dict(r) for r in db.execute('SELECT * FROM ' + t)] for t in tables)
    flow.pause(paused)
    report = {'audit': audit_id, 'revision': revision, 'pilot_plan': flow.pilot_plan(), 'pending_issued_api': 0, 'preserved_tables': list(tables)}
    write_json(flow.root / 'reports/pilot_budget_100_20261018.json', report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
