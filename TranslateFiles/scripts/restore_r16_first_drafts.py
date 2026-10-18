"""Project-only, audited restoration of the accepted r16 first-pass drafts.

No translation, API calls, restart-body, or semantic decisions are performed here.
"""
import argparse
import collections
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid

sys.path.insert(0, str(Path('D:/StaticHanHua/Tools/localization')))
from translation_workflow import Workflow, encoded, fingerprint, digest, write_json
from run_api_round import pid_alive
import ainiee_bridge as bridge

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / 'TranslateFiles'
BODY = ('translate', 'review', 'polish', 'final_review')


def no_executor():
    if (ROOT / 'state/api_round.lock').exists():
        raise ValueError('Runner lock exists; inspect/stop the old owner before restoration')
    for path in (ROOT / 'reports/api_runs').glob('*.json'):
        if path.name.endswith('.profile.json'):
            continue
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        if value.get('status') == 'running':
            raise ValueError('Unresolved running receipt: ' + str(path))
        if value.get('pid') and pid_alive(value['pid']):
            # PID reuse is possible; never kill based on an old receipt.
            raise ValueError('A receipt PID is alive; inspect before proceeding: ' + str(path))


def table_hash(db, table):
    rows = [list(r) for r in db.execute('SELECT * FROM ' + table + ' ORDER BY rowid')]
    return {'rows': len(rows), 'sha256': fingerprint(rows)}


def audit(db):
    meta = {r['key']: json.loads(r['value']) for r in db.execute('SELECT * FROM meta')}
    source_path = Path(meta['source_path'])
    assert digest(source_path) == meta['source_hash'], 'Source file hash changed'
    records = {r['id']: dict(r) for r in db.execute('SELECT * FROM records ORDER BY ordinal')}
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        texts = list(csv.reader(stream))
    assert len(texts) == len(records) == 23195
    for row, fields in zip(records.values(), texts):
        assert len(fields) == 1 and fields[0] == row['source']
        expected = f"R{row['ordinal']:07d}_{hashlib.sha256(row['source'].encode()).hexdigest()[:10]}"
        assert row['id'] == expected
    tasks = []
    for row in db.execute('SELECT * FROM tasks WHERE revision=16 AND stage=? ORDER BY rowid', ('translate',)):
        task = dict(row)
        payload = json.loads(task['payload'])
        if 'strict_translation' not in payload and 'draft_scan_key' not in payload:
            tasks.append((task, payload))
    assert len(tasks) == 1063, len(tasks)
    initial_ids = {t['id'] for t, p in tasks}
    # Read each historical table once. Per-record queries over unindexed lineage
    # would repeatedly scan hundreds of MB without adding verification strength.
    lineage_bindings = {(r['task_id'], r['token'], r['record_id'], r['instance'], r['item'])
                        for r in db.execute('SELECT task_id,token,record_id,instance,item FROM record_lineage')
                        if r['task_id'] in initial_ids}
    author_bindings = {(r['record_id'], r['task_id'], r['instance'])
                       for r in db.execute('SELECT record_id,task_id,instance FROM quality_authors')
                       if r['task_id'] in initial_ids}
    api_bindings = {(r['task_id'], r['session_id']) for r in db.execute('SELECT task_id,session_id FROM api_calls')}
    session_results = {}
    recovered, manifest = {}, []
    for task, payload in tasks:
        assert task['status'] == 'done' and task['result']
        assert payload['task_id'] == task['id'] and payload['revision'] == 16
        assert payload['source_hash'] == meta['source_hash']
        assert payload['glossary_version'] == meta['glossary']
        assert payload['style'] == meta['config']['style']
        unsigned = {k: v for k, v in payload.items() if k != 'input_hash'}
        assert fingerprint(unsigned) == task['input_hash'] == payload['input_hash'], task['id']
        result = json.loads(task['result'])
        assert result['task_id'] == task['id'] and result['input_hash'] == task['input_hash']
        ids = json.loads(task['ids'])
        originals = {r['id']: r for r in payload['records']}
        items = {r['id']: r for r in result['records']}
        assert len(ids) == len(set(ids)) == len(payload['records']) == len(result['records'])
        assert set(ids) == set(originals) == set(items)
        cached = {r['record_id']: dict(r) for r in db.execute(
            'SELECT * FROM batch_items WHERE task_id=? AND token=?', (task['id'], task['lease_token']))}
        assert set(cached) == set(ids)
        runs = [dict(r) for r in db.execute('SELECT * FROM batch_runs WHERE task_id=?', (task['id'],))]
        used_sessions = set()
        for record_id in ids:
            assert record_id not in recovered and record_id in records
            original, item, cache = originals[record_id], items[record_id], cached[record_id]
            assert cache['valid'] == 1 and json.loads(cache['item']) == item
            assert isinstance(item.get('translation'), str)
            row = records[record_id]
            protection = original.get('protection', [])
            assert original['ordinal'] == row['ordinal']
            assert Workflow.best_effort_restore(original['source'], protection) == row['source']
            assert not original.get('exceptions'), 'Unexpected initial inherited context exceptions'
            assert (task['id'], task['lease_token'], record_id, cache['instance'], cache['item']) in lineage_bindings, 'Missing actual author/lineage binding'
            assert (record_id, task['id'], cache['instance']) in author_bindings
            author_runs = [r for r in runs if r['worker'] == cache['instance'] and record_id in json.loads(r['scope'])]
            assert author_runs
            run = author_runs[-1]
            output_path = Path(run['result_file'])
            assert output_path.is_relative_to(ROOT) and output_path.is_file()
            if run['id'] not in session_results:
                session_results[run['id']] = json.loads(output_path.read_text(encoding='utf-8-sig'))
            saved = session_results[run['id']]
            assert saved['task_id'] == task['id'] and saved['input_hash'] == task['input_hash']
            assert item in saved['records'], 'Accepted item not in bound session result'
            assert (task['id'], run['id']) in api_bindings
            used_sessions.add(run['id'])
            # Keep the exact raw response fields for the new scanner. Only apply
            # the same known protection substitution as the original collector.
            restored = Workflow.best_effort_restore(item['translation'], protection)
            raw_exceptions = copy.deepcopy(item.get('exceptions', []))
            exceptions = bridge.normalize_exception_sources(raw_exceptions, [], meta['config']['case_sensitive'])
            recovered[record_id] = dict(id=record_id, ordinal=row['ordinal'], source=row['source'],
                translation=restored, exceptions=exceptions, raw_exceptions=raw_exceptions,
                raw_item=item, protection=protection, source_hash=fingerprint(row['source']),
                task_id=task['id'], input_hash=task['input_hash'], instance=cache['instance'], session_id=run['id'])
        manifest.append(dict(task_id=task['id'], input_hash=task['input_hash'], ids=ids,
            payload_sha256=fingerprint(payload), result_sha256=fingerprint(result),
            sessions=[dict(session_id=r['id'], result_file=r['result_file'], result_sha256=digest(r['result_file']))
                      for r in runs if r['id'] in used_sessions]))
    assert set(recovered) == set(records) and len(recovered) == 23195
    return meta, sorted(recovered.values(), key=lambda r: r['ordinal']), manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    no_executor()
    flow = Workflow(PROJECT)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '_' + uuid.uuid4().hex[:8]
    folder = ROOT / 'backups' / ('restore_r16_first_drafts_' + stamp)
    folder.mkdir(parents=True)
    source = sqlite3.connect(flow.db_path.as_uri() + '?mode=ro', uri=True)
    destination = sqlite3.connect(folder / 'workflow.sqlite3')
    try:
        source.backup(destination)
    finally:
        destination.close(); source.close()
    shutil.copy2(ROOT / 'config/workflow.json', folder / 'workflow.json')
    # Archive scan receipts before any new scan can overwrite the standard path.
    for name in ('full_draft_scan.json', 'draft_checks', 'review_rounds'):
        path = ROOT / 'reports' / name
        if path.is_dir():
            shutil.copytree(path, folder / 'reports' / name)
        elif path.is_file():
            (folder / 'reports').mkdir(exist_ok=True)
            shutil.copy2(path, folder / 'reports' / name)
    db = sqlite3.connect((folder / 'workflow.sqlite3').as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    meta, drafts, manifest = audit(db)
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    preserved_tables = [t for t in ('api_calls', 'quality_attempts', 'quality_authors', 'quality_results', 'record_lineage', 'repair_outcomes') if t in tables]
    before = {t: table_hash(db, t) for t in preserved_tables}
    db.close()
    snapshot = ROOT / 'snapshots' / ('r16_first_draft_' + stamp)
    snapshot.mkdir(parents=True)
    with (snapshot / 'drafts.jsonl').open('w', encoding='utf-8', newline='\n') as stream:
        for row in drafts:
            stream.write(encoded(row) + '\n')
    with (snapshot / 'drafts.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerows([r['translation']] for r in drafts)
    write_json(snapshot / 'task_manifest.json', manifest)
    report = dict(status='audited', source_revision=16, source_batches=1063, records=23195,
        exact_id_coverage=True, duplicate_ids=0, source_hash=meta['source_hash'],
        bindings_verified=['task_payload_fingerprint', 'task_result_hash', 'record_id_source_ordinal',
                           'frozen_glossary', 'style', 'valid_batch_item', 'session_result', 'api_call', 'actual_author_lineage'],
        backup=str(folder), snapshot=str(snapshot),
        snapshot_hashes={p.name: digest(p) for p in snapshot.iterdir()},
        original_exception_records=sum(bool(r['raw_exceptions']) for r in drafts),
        protection_mapping_records=sum(bool(r['protection']) for r in drafts),
        history_before=before, no_translation_requests=True)
    if args.apply:
        no_executor()
        with flow.db() as current:
            config = flow.config(current)
            assert flow.meta(current, 'revision') == meta['revision'] == 16
            assert all(table_hash(current, t) == before[t] for t in before), 'History changed since backup'
            assert flow.pilot_approved(current, config)
            assert not current.execute('SELECT 1 FROM records WHERE locked=1').fetchone()
            assert not current.execute('SELECT 1 FROM tasks WHERE status=?', ('running',)).fetchone()
            assert not current.execute('SELECT 1 FROM api_calls WHERE status=?', ('reserved',)).fetchone()
            flow.put(current, 'paused', True)
            cleared = {}
            for table in ('draft_candidates', 'draft_checks', 'draft_check_rounds', 'review_candidates',
                          'review_round_checks', 'review_proof_checks', 'checks', 'repair_regressions'):
                if table in tables:
                    where = ' WHERE stage NOT LIKE "pilot_%"' if table in ('review_candidates', 'repair_regressions') else ''
                    cleared[table] = current.execute('DELETE FROM ' + table + where).rowcount
            for key in [r[0] for r in current.execute('SELECT key FROM meta')
                        if r[0].startswith('draft_') or r[0] in ('review_generation', 'sol_pending_findings', 'last_export', 'in_game_check')]:
                current.execute('DELETE FROM meta WHERE key=?', (key,))
            for key in ('quality_approvals', 'quality_checkpoints'):
                flow.put(current, key, {k: v for k, v in flow.meta(current, key, {}).items() if k == 'pilot'})
            flow.put(current, 'repair_sol_ids', {k: v for k, v in flow.meta(current, 'repair_sol_ids', {}).items() if k.startswith('pilot_')})
            # Keep original done tasks intact. Archive subsequent production queues;
            # their results, paid calls, author and lineage rows remain immutable.
            initial_ids = {t['task_id'] for t in manifest}
            obsolete = [r[0] for r in current.execute('SELECT id FROM tasks WHERE stage IN (?,?,?,?)', BODY) if r[0] not in initial_ids]
            for task_id in obsolete:
                current.execute('UPDATE tasks SET status=?,lease_token=NULL,lease_until=NULL WHERE id=?', ('obsolete', task_id))
                for table in ('batch_runs', 'batch_repair_plans'):
                    if table in tables:
                        current.execute('UPDATE ' + table + ' SET status=? WHERE task_id=?', ('obsolete', task_id))
            for row in drafts:
                current.execute('UPDATE records SET stage=?,translation=?,exceptions=? WHERE id=?',
                    ('translate', row['translation'], encoded(row['exceptions']), row['id']))
                current.execute('INSERT INTO draft_candidates VALUES (?,?,?,?,?,?,?)',
                    (row['id'], encoded(row['raw_item']), encoded(row['protection']), row['translation'],
                     row['source_hash'], row['instance'], row['task_id']))
            revision = meta['revision'] + 1
            flow.put(current, 'revision', revision)
            # Existing common repair routing already isolates older revisions by
            # this boundary. This is a new check scope, with no source reset.
            flow.put(current, 'body_restart_revision', revision)
            flow.put(current, 'restored_first_draft_scope', dict(source_revision=16, check_revision=revision,
                snapshot=str(snapshot), snapshot_sha256=report['snapshot_hashes']['drafts.jsonl'],
                authorization='User explicitly requested original r16 drafts and a new independent program-check scope.'))
            flow.put(current, 'draft_generation', 1)
            assert flow.repair_routes(current, config, 'translate') == {}, 'Old repair budget leaked'
            assert flow.meta(current, 'glossary') == meta['glossary']
            assert flow.meta(current, 'quality_approvals')['pilot'] == meta['quality_approvals']['pilot']
            assert all(table_hash(current, t) == before[t] for t in before)
            for row in drafts:
                saved = current.execute('SELECT translation,exceptions,stage FROM records WHERE id=?', (row['id'],)).fetchone()
                assert tuple(saved) == (row['translation'], encoded(row['exceptions']), 'translate')
            report.update(status='restored', check_revision=revision, paused=True, cleared=cleared,
                          archived_production_tasks=len(obsolete), history_unchanged=True,
                          old_repair_routes_empty=True, restored_records=23195)
            flow.event(current, 'restore_r16_first_drafts', report)
        # Old summaries remain in the complete backup and explicit report archive;
        # remove live scan files so they cannot be mistaken for the new scope.
        for name in ('full_draft_scan.json', 'draft_checks'):
            path = ROOT / 'reports' / name
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                target = folder / ('live_' + name)
                shutil.move(str(path), str(target))
    write_json(snapshot / 'manifest.json', report)
    write_json(folder / 'restore_report.json', report)
    write_json(ROOT / 'reports/restore_r16_first_drafts.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'source_batches', 'records', 'backup', 'snapshot')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
