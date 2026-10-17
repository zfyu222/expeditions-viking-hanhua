"""Expeditions: Viking r8-only continuation; shared localization code is imported read-only."""
import argparse
from contextlib import contextmanager
import json
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[2]
SHARED = PROJECT.parents[1] / 'Tools' / 'localization'
sys.path.insert(0, str(SHARED))
import translation_workflow as shared
import glossary_tool
import r8_glossary_resolution as glossary_resolution
from workflow_quality import validate_glossary_reviews, nonempty

read_json = shared.read_json
digest = shared.digest
write_json = shared.write_json
DEFAULT = shared.DEFAULT

class VikingR8Workflow(shared.Workflow):

    def glossary_review_state(self, db):
            self.config(db)
            revision = self.meta(db, 'revision')
            tasks = db.execute('SELECT * FROM tasks WHERE stage="glossary_review" AND revision=? '
                               'AND status!="obsolete" ORDER BY id', (revision,)).fetchall()
            if not tasks or any(t['status'] != 'done' for t in tasks):
                raise ValueError('Complete every glossary review task before resolution/freezing')
            folder = self.root / f'glossary/r{revision}'
            snapshot = folder / 'glossary_original.json'
            original = read_json(snapshot)
            refs = {f'{table}:{i}' for table in glossary_tool.TABLES for i, _ in enumerate(original[table])}
            decisions = {'snapshot_sha256': digest(snapshot), 'source_sha256': self.meta(db, 'source_hash'),
                         'review_complete': True, 'review_summary': '', 'reviewed_refs': [],
                         'acknowledged_findings': [], 'edits': [], 'quarantine': [], 'additions': [], 'allow_no_match': [],
                         'entry_reviews': [], 'review_instances': {}, 'addition_reviewers': {}, 'issues': []}
            summaries, review_lookup = [], {}
            for task in tasks:
                partial = json.loads(task['result'])['decisions']
                validate_glossary_reviews(partial, json.loads(task['payload']))
                if (partial.get('snapshot_sha256') != decisions['snapshot_sha256'] or
                        partial.get('source_sha256') != decisions['source_sha256'] or
                        partial.get('review_complete') is not True or not nonempty(partial.get('review_summary')) or
                        any(x.get('severity') == 'blocking' for x in partial.get('issues', []))):
                    raise ValueError('Accepted glossary task no longer satisfies snapshot/source/review gates: ' + task['id'])
                owner = db.execute('SELECT instance FROM quality_results WHERE task_id=?', (task['id'],)).fetchone()
                if not owner:
                    owner = db.execute('SELECT instance FROM quality_attempts WHERE task_id=? AND token=?',
                                       (task['id'], task['lease_token'])).fetchone()
                if not owner:
                    raise ValueError('Missing glossary reviewer provenance')
                decisions['review_instances'].update({ref: owner['instance'] for ref in partial['reviewed_refs']})
                for item in partial.get('entry_reviews', []):
                    review_lookup.setdefault(item['ref'], []).append({**item, 'task_id': task['id']})
                for item in partial.get('additions', []):
                    decisions['addition_reviewers'][f'addition:{len(decisions["additions"])}'] = owner['instance']
                    decisions['additions'].append(item)
                for key in ('reviewed_refs', 'acknowledged_findings', 'edits', 'quarantine', 'allow_no_match', 'entry_reviews', 'issues'):
                    decisions[key].extend(partial.get(key, []))
                summaries.append(partial['review_summary'])
            if len(decisions['reviewed_refs']) != len(refs) or set(decisions['reviewed_refs']) != refs:
                raise ValueError('Global glossary semantic review coverage incomplete or duplicated')
            decisions['acknowledged_findings'] = sorted(set(decisions['acknowledged_findings']))
            decisions['review_summary'] = '\n'.join(summaries)
            normalized, aliases = glossary_resolution.normalize_additions(decisions)
            groups = glossary_resolution.candidates(original, normalized)
            equivalent, conflicts = glossary_resolution.group_data(groups)
            return revision, folder, snapshot, original, decisions, normalized, aliases, equivalent, conflicts, review_lookup


    def prepare_glossary_resolution(self):
        with self.db() as db:
            (revision, folder, snapshot, original, raw, normalized, aliases,
             equivalent, conflicts, reviews) = self.glossary_review_state(db)
            if self.meta(db, 'glossary'):
                raise ValueError('Glossary already frozen')
            texts = glossary_tool.source_rows(self.meta(db, 'source_path'))
            hashes = (digest(snapshot), self.meta(db, 'source_hash'), glossary_resolution.sha(raw))
            target = folder / 'resolution' / hashes[2][:16]
            if (target / 'manifest.json').is_file():
                manifest_path = target / 'manifest.json'
                manifest = read_json(manifest_path)
                if (manifest.get('accepted_decisions_sha256') != hashes[2] or
                        manifest.get('snapshot_sha256') != hashes[0] or manifest.get('source_sha256') != hashes[1]):
                    raise ValueError('Existing resolution handoff does not match accepted decisions')
            else:
                manifest_path, manifest = glossary_resolution.prepare_batches(
                    conflicts, raw, reviews, texts, hashes,
                    self.config(db).get('task_input_tokens', DEFAULT['task_input_tokens']), target)
                manifest['revision'] = revision
                write_json(manifest_path, manifest)
            return {'revision': revision, 'manifest': str(manifest_path),
                    'duplicate_groups': len(equivalent) + len(conflicts),
                    'equivalent_groups': len(equivalent), 'conflict_groups': len(conflicts),
                    'normalized_legacy_aliases': aliases,
                    'batches': [{**b, 'input_file': str(target / b['input_file']),
                                 'result_file': str(target / b['result_file'])} for b in manifest['batches']]}


    def _freeze_glossary_impl(self, resolution_manifest=None, expected_hashes=None):
        with self.db() as db:
            self.config(db)
            if self.meta(db, 'glossary'):
                return {'status': 'already_frozen', 'glossary': self.meta(db, 'glossary')}
            (revision, folder, snapshot, original, raw, normalized, aliases,
             equivalent, conflicts, reviews) = self.glossary_review_state(db)
            texts = glossary_tool.source_rows(self.meta(db, 'source_path'))
            hashes = (digest(snapshot), self.meta(db, 'source_hash'), glossary_resolution.sha(raw))
            resolutions = {}
            if conflicts:
                if not resolution_manifest:
                    raise ValueError(f'{len(conflicts)} conflicting reviewed source groups require prepare-glossary-resolution and --resolution-manifest')
                def independent(instance, ordinals):
                    record_ids = {r['id'] for r in db.execute('SELECT id,ordinal FROM records') if r['ordinal'] in ordinals}
                    if not record_ids:
                        return False
                    return not any(r['record_id'] in record_ids for r in db.execute(
                        'SELECT record_id FROM quality_authors WHERE stage="extract" AND instance=?', (instance,)))
                resolutions = glossary_resolution.load_resolutions(
                    resolution_manifest, conflicts, hashes, texts, raw, reviews, independent, revision)
            decisions = glossary_resolution.merge_decisions(
                original, raw, normalized, equivalent, conflicts, resolutions, reviews)
            decisions = glossary_resolution.normalize_r8_building_categories(original, decisions)
            decisions['resolution_provenance']['legacy_aliases'] = aliases
            output = folder / ('freeze_' + uuid.uuid4().hex[:8])
            output.mkdir()
            decisions_path = output / 'glossary_decisions.json'
            write_json(decisions_path, decisions)
            glossary_tool.build(snapshot, self.meta(db, 'source_path'), decisions_path, output / 'built')
            path = output / 'built/glossary_reviewed.json'
            info = {'path': str(path.relative_to(self.root)), 'hash': digest(path), 'revision': revision}
            if expected_hashes is not None and expected_hashes != resolution_file_hashes(Path(resolution_manifest)):
                raise ValueError('Resolution files changed before frozen glossary registration')
            self.put(db, 'glossary', info)
            self.event(db, 'freeze_glossary', info)
            return {'status': 'frozen', 'glossary': info}

    @contextmanager
    def read_only(self):
        db = sqlite3.connect(self.db_path.as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    def r8_state(self):
        with self.read_only() as db:
            state = self.glossary_review_state(db)
            if state[0] != 8:
                raise ValueError('This project adapter only handles current glossary revision 8')
            if self.meta(db, 'glossary') is not None:
                raise ValueError('The glossary is already frozen')
            return state, self.meta(db, 'source_path'), self.meta(db, 'source_hash')

    def freeze_glossary(self, manifest):
        report = check_resolution(self, manifest)
        if report['missing'] or report['invalid'] or report['manifest_errors']:
            raise ValueError('Resolution check must pass before freezing: ' + json.dumps(report, ensure_ascii=False))
        before = resolution_file_hashes(Path(manifest))
        backup = backup_state(self, 'before_r8_freeze')
        if before != resolution_file_hashes(Path(manifest)):
            raise ValueError('Resolution files changed during backup; freezing cancelled')
        result = self._freeze_glossary_impl(manifest, expected_hashes=before)
        if before != resolution_file_hashes(Path(manifest)):
            raise ValueError('Resolution files changed during freezing; inspect backup and frozen artifact')
        return {**result, 'backup': str(backup)}


def resolution_file_hashes(manifest_path):
    manifest_path = manifest_path.resolve()
    manifest = read_json(manifest_path)
    paths = [manifest_path]
    for batch in manifest['batches']:
        paths.append(manifest_path.parent / batch['input_file'])
        paths.append(manifest_path.parent / batch['result_file'])
    return {str(path): digest(path) if path.is_file() else None for path in paths}


def backup_state(flow, label):
    target = flow.root / 'backups' / (label + '_' + uuid.uuid4().hex[:12])
    target.mkdir(parents=True, exist_ok=False)
    source_db = sqlite3.connect(flow.db_path)
    try:
        saved_db = sqlite3.connect(target / 'workflow.sqlite3')
        try:
            source_db.backup(saved_db)
        finally:
            saved_db.close()
    finally:
        source_db.close()
    config = flow.root / 'config/workflow.json'
    shutil.copy2(config, target / 'workflow.json')
    write_json(target / 'manifest.json', {'database_sha256': digest(target / 'workflow.sqlite3'),
                                          'config_sha256': digest(target / 'workflow.json')})
    return target


def check_resolution(flow, manifest_path):
    manifest_path = Path(manifest_path).resolve()
    (revision, folder, snapshot, original, raw, normalized, aliases,
     equivalent, conflicts, reviews), source, source_hash = flow.r8_state()
    texts = glossary_tool.source_rows(source)
    hashes = (digest(snapshot), source_hash, glossary_resolution.sha(raw))
    report = {'revision': revision, 'reviewed_refs': len(raw['reviewed_refs']),
              'equivalent_groups': len(equivalent), 'conflict_groups': len(conflicts),
              'legacy_aliases': aliases, 'validated': [], 'missing': [],
              'invalid': [], 'manifest_errors': []}
    if not manifest_path.is_file():
        report['manifest_errors'].append('manifest: file missing')
        return report
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError) as exc:
        report['manifest_errors'].append('manifest: ' + str(exc))
        return report
    expected = {group['group_id']: group for group in conflicts}
    if manifest.get('format_version') != 1:
        report['manifest_errors'].append('manifest.format_version: expected 1')
    if manifest.get('revision') != revision:
        report['manifest_errors'].append('manifest.revision: expected current revision 8')
    for key, value in zip(('snapshot_sha256', 'source_sha256', 'accepted_decisions_sha256'), hashes):
        if manifest.get(key) != value:
            report['manifest_errors'].append('manifest.' + key + ': current accepted state hash mismatch')
    ids = manifest.get('conflict_group_ids')
    if not isinstance(ids, list) or len(ids) != len(expected) or set(ids) != set(expected):
        report['manifest_errors'].append('manifest.conflict_group_ids: must cover 276 current groups exactly once')
    batches = manifest.get('batches')
    if not isinstance(batches, list):
        report['manifest_errors'].append('manifest.batches: expected array')
        return report
    seen_batches, seen_groups = set(), set()
    with flow.read_only() as db:
        extraction_authors = {}
        for row in db.execute('SELECT record_id,instance FROM quality_authors WHERE stage="extract"'):
            extraction_authors.setdefault(row['instance'], set()).add(row['record_id'])
        ordinal_ids = {row['ordinal']: row['id'] for row in db.execute('SELECT id,ordinal FROM records')}
        for batch in batches:
            batch_id = batch.get('batch_id')
            errors = []
            if not isinstance(batch_id, str) or not batch_id.startswith('B') or not batch_id[1:].isdigit():
                report['manifest_errors'].append('batch_id: invalid')
                continue
            if batch_id in seen_batches:
                errors.append('manifest.batches: duplicate batch_id')
            seen_batches.add(batch_id)
            gids = batch.get('group_ids')
            if not isinstance(gids, list) or not gids or len(gids) != len(set(gids)) or not set(gids) <= set(expected):
                errors.append('manifest.group_ids: invalid or duplicate group scope')
                gids = []
            if set(gids) & seen_groups:
                errors.append('manifest.group_ids: group appears in another batch')
            seen_groups.update(gids)
            payloads = [glossary_resolution.conflict_payload(expected[g], raw, reviews, texts, *hashes) for g in gids]
            input_hash = glossary_resolution.sha({'batch_id': batch_id, 'groups': payloads, 'hashes': hashes})
            if batch.get('input_hash') != input_hash:
                errors.append('manifest.input_hash: expected original protocol hash')
            if batch.get('input_file') != batch_id + '.input.md':
                errors.append('manifest.input_file: batch filename mismatch')
            if batch.get('result_file') != batch_id + '.result.json':
                errors.append('manifest.result_file: batch filename mismatch')
            input_file = manifest_path.parent / (batch_id + '.input.md')
            expected_input, _ = glossary_resolution.prepared_input(batch_id, input_hash, payloads)
            if not input_file.is_file() or input_file.read_text(encoding='utf-8') != expected_input:
                errors.append('input_file: missing or content differs from accepted protocol')
            result_file = manifest_path.parent / (batch_id + '.result.json')
            if not result_file.is_file():
                report['missing'].append(batch_id)
                if errors:
                    report['invalid'].append({'batch_id': batch_id, 'errors': errors})
                continue
            try:
                result = json.loads(result_file.read_text(encoding='utf-8-sig'))
            except (OSError, ValueError) as exc:
                errors.append('result_file: invalid JSON: ' + str(exc))
                result = {}
            if not isinstance(result, dict):
                errors.append('result: expected object')
                result = {}
            for field, value in (('format_version', 1), ('batch_id', batch_id), ('input_hash', batch.get('input_hash'))):
                if result.get(field) != value:
                    errors.append('result.' + field + ': identity/hash mismatch')
            reviewer = result.get('reviewer_id')
            if not isinstance(reviewer, str) or not reviewer.startswith('/root/') or len(reviewer) < 7:
                errors.append('result.reviewer_id: expected actual new subagent instance ID')
            decisions = result.get('decisions')
            if not isinstance(decisions, list):
                errors.append('result.decisions: expected array')
                decisions = []
            decision_ids = [d.get('group_id') for d in decisions if isinstance(d, dict)]
            if len(decisions) != len(gids) or len(decision_ids) != len(gids) or len(set(decision_ids)) != len(gids) or set(decision_ids) != set(gids):
                errors.append('result.decisions: must cover assigned groups exactly once')
            for index, item in enumerate(decisions):
                prefix = f'result.decisions[{index}]'
                if not isinstance(item, dict) or item.get('group_id') not in expected:
                    errors.append(prefix + '.group_id: outside this batch')
                    continue
                group = expected[item['group_id']]
                if item['group_id'] not in gids:
                    errors.append(prefix + '.group_id: outside this batch')
                allowed = {n for member in group['members'] for n in member['row'].get('evidence_rows', [])
                           if type(n) is int and 1 <= n <= len(texts)}
                rows = item.get('evidence_rows')
                valid_rows = isinstance(rows, list) and bool(rows) and all(type(n) is int and n in allowed for n in rows)
                if not valid_rows or len(rows) != len(set(rows)):
                    errors.append(prefix + '.evidence_rows: require distinct allowed source ordinals')
                    rows = []
                excerpt = item.get('source_excerpt')
                if not isinstance(excerpt, str) or not excerpt.strip() or not any(excerpt in texts[n-1] for n in rows):
                    errors.append(prefix + '.source_excerpt: require a continuous substring of a cited original row')
                if not isinstance(item.get('reason'), str) or not item['reason'].strip():
                    errors.append(prefix + '.reason: require a specific nonempty reason')
                original_reviewers = {raw['review_instances'].get(ref) for ref in group['refs']}
                original_reviewers.update(raw.get('addition_reviewers', {}).get(ref) for ref in group['refs'])
                record_ids = {ordinal_ids[n] for n in allowed if n in ordinal_ids}
                if reviewer in original_reviewers or not record_ids or extraction_authors.get(reviewer, set()) & record_ids:
                    errors.append(prefix + '.reviewer_id: reviewer must be independent of original review and extraction')
                issues = item.get('issues', [])
                if not isinstance(issues, list) or any(not isinstance(issue, dict) for issue in issues):
                    errors.append(prefix + '.issues: expected list of objects')
                elif any(issue.get('severity') == 'blocking' for issue in issues):
                    errors.append(prefix + '.issues: unresolved blocking issue')
                action = item.get('action')
                patch = item.get('patch', {})
                if action not in ('keep', 'quarantine'):
                    errors.append(prefix + '.action: expected keep or quarantine')
                elif action == 'keep':
                    if item.get('keep_ref') not in group['refs']:
                        errors.append(prefix + '.keep_ref: outside this group')
                    if not isinstance(patch, dict):
                        errors.append(prefix + '.patch: expected object')
                    elif set(patch) & {'source', 'evidence_rows', 'extraction_candidates', 'provisional_selection', 'review_provenance'}:
                        errors.append(prefix + '.patch: cannot alter source/provenance')
                elif item.get('keep_ref') not in (None, '') or patch not in ({}, None):
                    errors.append(prefix + '.keep_ref/patch: whole-group quarantine cannot select keeper or patch')
            if errors:
                report['invalid'].append({'batch_id': batch_id, 'errors': errors})
            else:
                report['validated'].append(batch_id)
    if seen_groups != set(expected):
        report['manifest_errors'].append('manifest.batches: group scope incomplete')
    if not report['missing'] and not report['invalid'] and not report['manifest_errors']:
        with flow.read_only() as db:
            def independent(instance, ordinals):
                ids = {r['id'] for r in db.execute('SELECT id,ordinal FROM records') if r['ordinal'] in ordinals}
                return bool(ids) and not any(r['record_id'] in ids for r in db.execute(
                    'SELECT record_id FROM quality_authors WHERE stage="extract" AND instance=?', (instance,)))
            try:
                glossary_resolution.load_resolutions(manifest_path, conflicts, hashes, texts, raw, reviews, independent, revision)
            except ValueError as exc:
                report['manifest_errors'].append('strict_gate: ' + str(exc))
    return report


def configure_api(flow, reason):
    if not shared.API_CONFIG_FILE.is_file():
        raise ValueError('Global API config file is absent; configure it before switching backend')
    with flow.read_only() as db:
        config = flow.config(db)
        revision = flow.meta(db, 'revision')
        glossary = flow.meta(db, 'glossary')
        paused = flow.meta(db, 'paused')
        running = db.execute('SELECT count(*) FROM tasks WHERE status="running"').fetchone()[0]
        body = db.execute('SELECT count(*) FROM records WHERE stage!=? OR translation IS NOT NULL',
                          ('source',)).fetchone()[0]
    if revision != 8 or not glossary or glossary.get('revision') != 8:
        raise ValueError('Freeze r8 glossary before configuring API')
    if config['backend'] == 'api':
        return {'status': 'already_api', 'revision': revision, 'glossary': glossary}
    if running or body:
        raise ValueError('Finish running tasks; API switch requires all body records at source')
    if not paused:
        flow.pause(True)
    try:
        backup = backup_state(flow, 'before_api_configure')
        next_history = flow.root / f'history/config_r{revision + 1}.json'
        archived = None
        if next_history.exists():
            archive = flow.root / 'history' / ('pre_api_r' + str(revision + 1) + '_' + uuid.uuid4().hex[:12])
            archive.mkdir(parents=True)
            archived = archive / next_history.name
            shutil.copy2(next_history, archived)
            write_json(archive / 'archive_manifest.json', {'original': str(next_history),
                                                            'sha256': digest(next_history),
                                                            'archived_sha256': digest(archived)})
            if digest(next_history) != digest(archived):
                raise ValueError('History archive hash mismatch; configure cancelled')
        result = flow.configure({'backend': 'api'}, reason, impact='none')
        with flow.read_only() as db:
            if flow.meta(db, 'glossary') != glossary:
                raise ValueError('Frozen glossary changed after API configure')
        return {**result, 'status': 'configured_api', 'glossary_preserved': True,
                'backup': str(backup), 'archived_history': str(archived) if archived else None}
    finally:
        if not paused:
            flow.pause(False)


def main():
    parser = argparse.ArgumentParser(description='Expeditions: Viking project-only r8 glossary continuation')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('check-resolution', 'freeze'):
        command = sub.add_parser(name)
        command.add_argument('--manifest', required=True)
    sub.add_parser('prepare-resolution')
    api = sub.add_parser('configure-api')
    api.add_argument('--reason', default='r8 glossary frozen; switch custom workflow backend to global API')
    args = parser.parse_args()
    flow = VikingR8Workflow(PROJECT)
    try:
        if args.command == 'check-resolution':
            result = check_resolution(flow, args.manifest)
        elif args.command == 'freeze':
            result = flow.freeze_glossary(args.manifest)
        elif args.command == 'prepare-resolution':
            result = flow.prepare_glossary_resolution()
        else:
            result = configure_api(flow, args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == 'check-resolution' and (result['missing'] or result['invalid'] or result['manifest_errors']) else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

