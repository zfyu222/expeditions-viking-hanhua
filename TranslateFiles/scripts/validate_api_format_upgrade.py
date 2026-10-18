"""Bounded real-API validation in a separate workflow copy (max 3 requests).

Production records/queues and the user's local credentials are never modified.
"""
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import uuid

sys.path.insert(0, 'D:/StaticHanHua/Tools/localization')
import translation_workflow as w
import ainiee_bridge as bridge
from workflow_task_contract import canonical_api_result
from workflow_api_reliability import format_retry_feedback
from workflow_profile import RunProfile

project = Path(__file__).resolve().parents[2]
root = project / 'TranslateFiles'
folder = root / 'backups' / ('api_format_validation_' + uuid.uuid4().hex)
fixture = folder / 'fixture'
fixture_root = fixture / 'TranslateFiles'
(fixture_root / 'state').mkdir(parents=True)
source = sqlite3.connect((root / 'state/workflow.sqlite3').as_uri() + '?mode=ro', uri=True)
target = sqlite3.connect(fixture_root / 'state/workflow.sqlite3')
source.backup(target)
target.close(); source.close()
shutil.copytree(root / 'config', fixture_root / 'config')
flow = w.Workflow(fixture)
with flow.db() as db:
    config = flow.config(db)
    glossary = flow.meta(db, 'glossary')
    dest = fixture_root / glossary['path']
    dest.parent.mkdir(parents=True)
    shutil.copy2(root / glossary['path'], dest)
    # One untouched real pending review batch containing protected text.
    candidates = [dict(r) for r in db.execute('SELECT * FROM tasks WHERE revision=17 AND stage="review" AND status="pending" ORDER BY rowid')]
    selected = next(t for t in candidates if any('[' in r['source'] for r in json.loads(t['payload'])['records']))
    db.execute('UPDATE tasks SET ready_at=? WHERE revision=17 AND stage="review" AND status="pending"', (time.time()+86400,))
    db.execute('UPDATE tasks SET ready_at=0 WHERE id=?', (selected['id'],))
first = flow.batch_open('review', 'validation-api-initial-' + uuid.uuid4().hex, backend='api', prepared=True)
assert first['task_id'] == selected['id']

# Replay an actual failed initial handoff in this copy, to exercise the real
# batch-retry generator, error feedback, request and collection, not a mock.
task_id = 'review-r17-00039-d755ba01'
initial_sid = '6d35f3547ad34784a9c35010e0b4d7ba'
with flow.db() as db:
    task = dict(db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone())
    run = dict(db.execute('SELECT * FROM batch_runs WHERE id=?', (initial_sid,)).fetchone())
    assert task['attempt'] == 2 and run['status'] == 'superseded'
    db.execute('DELETE FROM batch_runs WHERE task_id=? AND id!=?', (task_id, initial_sid))
    db.execute('DELETE FROM batch_items WHERE task_id=?', (task_id,))
    db.execute('DELETE FROM review_candidates WHERE task_id=?', (task_id,))
    db.execute('UPDATE tasks SET status="running",attempt=1,lease_until=?,result=NULL WHERE id=?', (time.time()+3600, task_id))
    db.execute('UPDATE batch_runs SET status="waiting",receipt=NULL WHERE id=?', (initial_sid,))
second = flow.batch_retry(initial_sid, 'validation-api-retry-' + uuid.uuid4().hex,
    'invalid_model_result', format_error=True)
feedback_input = Path(second['input_file']).read_text(encoding='utf-8')
assert '本次格式重试' in feedback_input and 'json_column' in feedback_input

# Replay the real numeric-ID response: only its ID type differs from the Sol
# recovered reply, and its original API session binding is retained.
sid = '76f49a9b099c4b68af164a4045e59371'
paid = root / 'tasks' / task_id / 'handoffs' / sid
transport = w.read_json(paid / 'api_id_transport.v2.json')
raw = bridge.parse_response((paid / 'response.raw.txt').read_text(encoding='utf-8'))
scope = list(transport['short_to_canonical'].values())
canonical = canonical_api_result(raw, transport, sid, task_id, transport['input_hash'], scope)
expected = canonical_api_result(w.read_json(paid / 'response.format_recovered.json'), transport, sid, task_id, transport['input_hash'], scope)
assert canonical == expected
guards = {}
for label, mutate in (
    ('duplicate_after_normalization', lambda x: x['records'].append(copy.deepcopy(x['records'][13]))),
    ('unknown_integer', lambda x: x['records'][0].update(id=99999)),
    ('boolean_id', lambda x: x['records'][0].update(id=True)),
    ('missing_keep_and_translation', lambda x: (x['records'][0].pop('keep', None), x['records'][0].pop('translation', None))),
    ('nonboolean_keep', lambda x: x['records'][0].update(keep='true')),
):
    bad = copy.deepcopy(raw); mutate(bad)
    try:
        canonical_api_result(bad, transport, sid, task_id, transport['input_hash'], scope)
    except ValueError:
        guards[label] = 'rejected'
    else:
        raise AssertionError(label + ' was accepted')

settings, key = w.load_api_settings(config)
settings = copy.deepcopy(settings)
settings['extra_body'] = {**settings.get('extra_body', {}), 'response_format': {'type':'json_object'}}
client = bridge.AINieeAPI(settings, key)
del key
requests = []
receipts = []
errors = []
try:
    for session in (first, second):
        assert len(requests) < 3
        requests.append(dict(session_id=session['session_id'], usage={'usage_reported':False}))
        content, usage = client.request('', Path(session['input_file']).read_text(encoding='utf-8'))
        requests[-1]['usage'] = usage
        response_root = Path(session['result_file']).parent
        w.atomic_write(response_root / 'response.raw.txt', content)
        w.write_json(response_root / 'response.metadata.json', usage)
        result = bridge.parse_response(content)
        w.write_json(response_root / 'response.parsed.json', result)
        mapping = w.read_json(response_root / 'api_id_transport.v2.json')
        with flow.db() as db:
            run = flow._batch_run(db, session['session_id'])
            task = flow.valid_task(db, run['task_id'], run['token'])
            result = canonical_api_result(result, mapping, run['id'], task['id'], task['input_hash'], json.loads(run['scope']))
            db.execute('INSERT INTO api_calls(task_id,time,status,usage,session_id) VALUES (?,?,?,?,?)',
                (task['id'],time.time(),'validation_received',w.encoded(usage),run['id']))
        w.write_json(session['result_file'], result)
        receipt = flow.batch_finish(session['session_id'])
        assert receipt['status'] == 'submitted'
        # Strictly check actual evidence for this saved candidate only. Do not
        # invent a full round completion in the validation copy.
        strict_errors = []
        with flow.db() as db:
            task = dict(db.execute('SELECT * FROM tasks WHERE id=?', (session['task_id'],)).fetchone())
            strict_task = {**task, 'payload': w.encoded({**json.loads(task['payload']), 'strict_review':True})}
            originals = {r['id']:r for r in json.loads(task['payload'])['records']}
            saved_items = [json.loads(r['item']) for r in db.execute('SELECT item FROM review_candidates WHERE task_id=?', (task['id'],))]
            for item in saved_items:
                try:
                    flow.validate_body_item(db, strict_task, result, item, originals[item['id']], config, flow.rules(db,config), flow.glossary(db))
                except ValueError as error:
                    strict_errors.append(dict(id=item['id'],error=str(error)))
        receipts.append(dict(session_id=session['session_id'],status=receipt['status'],records=receipt['records'],
                             strict_validation_errors=strict_errors))
except bridge.ApiFailure as error:
    errors.append(str(error))
except (ValueError, AssertionError) as error:
    errors.append(str(error))
finally:
    client.close()
report = dict(status=('format_passed_with_quality_findings' if any(r['strict_validation_errors'] for r in receipts) else 'passed')
              if len(receipts)==2 and not errors else 'needs_attention',
    fixture=str(fixture), real_api_requests=len(requests), request_limit=3,
    json_mode={'type':'json_object'}, lossless_numeric_id_replay='identical_canonical_result',
    rejection_guards=guards, retry_feedback_present=True, requests=requests, receipts=receipts,errors=errors,
    production_records_queues_unchanged=True, validation_results_not_used_as_production_review=True)
w.write_json(folder / 'report.json',report)
w.write_json(root / 'reports/api_format_upgrade_validation.json',report)
print(json.dumps({k:report[k] for k in ('status','real_api_requests','errors','receipts')},ensure_ascii=True))
