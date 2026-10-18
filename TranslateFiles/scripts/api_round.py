"""Project-local API round entry point; shared code owns the work and receipt."""

import argparse
from contextlib import redirect_stdout
import json
from pathlib import Path
import sqlite3
import sys


PROJECT = Path(__file__).resolve().parents[2]
SHARED = PROJECT.parents[1] / 'Tools' / 'localization'
sys.path.insert(0, str(SHARED))

import translation_workflow as shared
from run_api_round import STAGES, execute


OVERRIDE = PROJECT / 'TranslateFiles/config/api_budget_override.json'
SYNC_REASON = 'Apply batching settings from api.local.jsonc'


def budget_override():
    value = json.loads(OVERRIDE.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or set(value) != {'task_input_tokens', 'reason'}
            or type(value['task_input_tokens']) is not int or value['task_input_tokens'] <= 0
            or not isinstance(value['reason'], str) or not value['reason'].strip()):
        raise ValueError('Invalid project API budget override')
    return value


class VikingAPIWorkflow(shared.Workflow):
    """Keep the project input cap when shared API batching sync configures."""

    def _pilot_budget_check(self, db, stage, allocated=False):
        if stage in ('pilot_translate', 'pilot_review'):
            limit = self.config(db)['pilot_call_limit']
            spent = self.pilot_spent(db)
            if spent > limit or (not allocated and spent >= limit):
                raise ValueError('Project pilot execution budget exhausted')

    def pilot_plan(self):
        plan = super().pilot_plan()
        with self.db() as db:
            limit = self.config(db)['pilot_call_limit']
        plan['execution_limit'] = limit
        plan['within_budget'] = (plan['within_budget'] and
            plan['executions_effective'] + plan['translation_batches'] + plan['review_batches'] <= limit)
        plan['note'] = 'Project-authorized aggregate limit; all historical raw attempts and audited exclusions retained. Production task and per-record repair limits still apply.'
        return plan

    def claim(self, stage, *args, **kwargs):
        with self.db() as db:
            self._pilot_budget_check(db, stage)
        return super().claim(stage, *args, **kwargs)

    def _batch_session(self, db, task, *args, **kwargs):
        # Shared callers insert the attempt in this same transaction first.
        # Raising here rolls back the allocation, including concurrent retries.
        self._pilot_budget_check(db, task['stage'], allocated=True)
        return super()._batch_session(db, task, *args, **kwargs)

    def batch_repair(self, session_id, *args, **kwargs):
        with self.db() as db:
            run = self._batch_run(db, session_id)
            task = db.execute('SELECT stage FROM tasks WHERE id=?', (run['task_id'],)).fetchone()
            self._pilot_budget_check(db, task['stage'])
        return super().batch_repair(session_id, *args, **kwargs)

    def batch_retry(self, session_id, *args, **kwargs):
        with self.db() as db:
            run = self._batch_run(db, session_id)
            task = db.execute('SELECT stage FROM tasks WHERE id=?', (run['task_id'],)).fetchone()
            self._pilot_budget_check(db, task['stage'])
        return super().batch_retry(session_id, *args, **kwargs)

    def configure(self, patch, reason, impact='auto', record_ids=None):
        if reason != SYNC_REASON:
            return super().configure(patch, reason, impact, record_ids)
        override = budget_override()
        proposed = {**patch, 'task_input_tokens': override['task_input_tokens']}
        with self.db() as db:
            current = self.config(db)
            changed = {key: value for key, value in proposed.items() if current[key] != value}
            if not changed:
                return None
        return super().configure(changed, reason + '; ' + override['reason'], impact, record_ids)


def apply_budget(flow):
    override = budget_override()
    with flow.db() as db:
        current = flow.config(db)
        paused = flow.meta(db, 'paused')
    if paused:
        raise ValueError('Workflow is paused; inspect the existing round before resuming')
    if current['task_input_tokens'] == override['task_input_tokens']:
        return
    flow.pause(True)
    try:
        flow.configure({'task_input_tokens': override['task_input_tokens']},
                       'Apply project API input budget: ' + override['reason'], impact='none')
    finally:
        flow.pause(False)


def child(stage, sessions):
    flow = VikingAPIWorkflow(PROJECT)
    with redirect_stdout(sys.stderr):
        apply_budget(flow)
        summary = shared.run_api(flow, stage, session_ids=sessions)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def dry_run(stage):
    """Inspect the planned budget and sync without touching the workflow DB."""
    override = budget_override()
    path = PROJECT / 'TranslateFiles/state/workflow.sqlite3'
    with sqlite3.connect(f'file:{path.as_posix()}?mode=ro', uri=True) as db:
        meta = {key: json.loads(value) for key, value in db.execute(
            'SELECT key,value FROM meta WHERE key IN ("config","revision","paused","glossary")')}
        running = db.execute('SELECT count(*) FROM tasks WHERE status="running"').fetchone()[0]
        api_calls = db.execute('SELECT count(*) FROM api_calls').fetchone()[0]
        pilot_attempts = db.execute('SELECT count(*) FROM quality_attempts q JOIN tasks t '
            'ON t.id=q.task_id WHERE t.stage IN ("pilot_translate","pilot_review")').fetchone()[0]
    current = meta['config']
    if shared.read_json(PROJECT / 'TranslateFiles/config/workflow.json') != current:
        raise ValueError('Project workflow file differs from saved configuration')
    local_batching = shared.read_local_api_config(shared.API_CONFIG_FILE).get('batching', {})
    projected = {**current, 'task_input_tokens': override['task_input_tokens']}
    merged = shared.merge_config({**shared.DEFAULT, **projected}, local_batching)
    sync_patch = {key: merged[key] for key in local_batching
                  if merged[key] != projected.get(key, shared.DEFAULT[key])}
    effective = {**sync_patch, 'task_input_tokens': override['task_input_tokens']}
    changes = sorted(key for key, value in effective.items() if projected[key] != value)
    return {'status': 'dry_run', 'stage': stage, 'revision': meta['revision'],
            'current_task_input_tokens': current['task_input_tokens'],
            'project_task_input_tokens': override['task_input_tokens'],
            'sync_change_fields_after_budget': changes, 'paused': meta['paused'],
            'running_tasks': running, 'api_calls': api_calls,
            'pilot_quality_attempts': pilot_attempts,
            'frozen_glossary_hash': meta['glossary']['hash'] if meta.get('glossary') else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=STAGES, required=True)
    parser.add_argument('--sessions', nargs='+', help='Explicitly recovered, unissued sessions only')
    parser.add_argument('--dry-run', action='store_true', help='Read-only budget/sync preview; no API call')
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.dry_run:
        try:
            print(json.dumps(dry_run(args.stage), ensure_ascii=False))
            return 0
        except (ValueError, OSError, sqlite3.Error) as error:
            print(json.dumps({'status': 'needs_attention', 'reason': str(error)}, ensure_ascii=False))
            return 1
    if args.child:
        try:
            return child(args.stage, args.sessions)
        except (ValueError, OSError, json.JSONDecodeError) as error:
            print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
            return 1
    command = [sys.executable, str(Path(__file__).resolve()), '--child', '--stage', args.stage]
    if args.sessions:
        command.extend(['--sessions', *args.sessions])
    try:
        receipt = execute(PROJECT, args.stage, command)
    except (ValueError, OSError) as error:
        print(json.dumps({'status': 'needs_attention', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt['status'] == 'completed' else 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
