"""Archive unattempted Sol jobs made from a fixed marker-representation defect.

Do not change drafts or completed repair budgets; the updated scanner replans
actual remaining failures. All superseded jobs remain in the historical DB.
"""
import json
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

sys.path.insert(0, 'D:/StaticHanHua/Tools/localization')
from translation_workflow import Workflow, fingerprint, write_json

project = Path(__file__).resolve().parents[2]
flow = Workflow(project)
assert not (flow.root / 'state/api_round.lock').exists()
folder = flow.root / 'backups' / ('marker_validator_recheck_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
folder.mkdir(parents=True)
source = sqlite3.connect(flow.db_path.as_uri() + '?mode=ro', uri=True)
target = sqlite3.connect(folder / 'workflow.sqlite3')
source.backup(target)
target.close(); source.close()
with flow.db() as db:
    assert flow.meta(db, 'revision') == 17
    assert not db.execute('SELECT 1 FROM tasks WHERE status="running"').fetchone()
    assert not db.execute('SELECT 1 FROM api_calls WHERE status="reserved"').fetchone()
    before = fingerprint([list(r) for r in db.execute('SELECT * FROM records ORDER BY ordinal')])
    routes_before = flow.repair_routes(db, flow.config(db), 'translate')
    jobs = [dict(t) for t in db.execute('SELECT * FROM tasks WHERE revision=17 AND status="pending"')]
    assert jobs
    for task in jobs:
        payload = json.loads(task['payload'])
        assert payload.get('repair_tier') == 'sol' and task['attempt'] == 0 and task['result'] is None
        assert payload.get('draft_scan_key') and task['backend'] == 'codex'
        assert not db.execute('SELECT 1 FROM quality_attempts WHERE task_id=?', (task['id'],)).fetchone()
    for task in jobs:
        db.execute('UPDATE tasks SET status="obsolete" WHERE id=?', (task['id'],))
    assert routes_before == flow.repair_routes(db, flow.config(db), 'translate')
    assert before == fingerprint([list(r) for r in db.execute('SELECT * FROM records ORDER BY ordinal')])
    report = dict(status='recheck_ready', revision=17, archived_unattempted_jobs=[t['id'] for t in jobs],
        affected_ids=sorted({i for t in jobs for i in json.loads(t['ids'])}), backup=str(folder),
        reason='Strict marker validator rejected exact original literals returned from repair candidates. Validator now accepts exact complete restored representation and still rejects missing/repeated/fabricated markers.',
        drafts_unchanged=True, completed_repair_counts_unchanged=True,
        next_action='run_api_round.py --stage draft_check; validator policy v3 forces fresh validation')
    flow.event(db, 'marker_validator_recheck', report)
write_json(folder / 'report.json', report)
write_json(flow.root / 'reports/marker_validator_recheck.json', report)
print(json.dumps({'status':report['status'],'archived_jobs':len(jobs),'affected_records':len(report['affected_ids']),'backup':str(folder)}))
