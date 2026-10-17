"""Resolve collisions in an already accepted glossary review without editing worker results."""
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path

import glossary_tool
from workflow_tokens import count_tokens


def stable(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(stable(value).encode('utf-8')).hexdigest()


def normalize_additions(decisions):
    """Only the unambiguous old alias is accepted; the accepted result stays untouched."""
    result = copy.deepcopy(decisions)
    aliases = []
    for index, item in enumerate(result['additions']):
        row = item['row']
        if item['table'] != 'non_translate' and 'translation' in row:
            if 'recommended_translation' in row and row['recommended_translation'] != row['translation']:
                raise ValueError(f'Ambiguous legacy addition translation alias at addition:{index}')
            if not isinstance(row['translation'], str):
                raise ValueError(f'Invalid legacy addition translation alias at addition:{index}')
            row['recommended_translation'] = row.pop('translation')
            aliases.append({'addition': index, 'from': 'translation', 'to': 'recommended_translation'})
    return result, aliases


def semantic(table, row):
    # These fields describe provenance or editorial commentary; preserve them on
    # the kept row, but do not treat differing source locations as a new meaning.
    ignored = {'source', 'evidence_rows', 'extraction_candidates', 'provisional_selection',
               'note', 'reason', 'review_provenance'}
    return stable({'table': table, 'fields': {k: v for k, v in row.items() if k not in ignored}})


def candidates(snapshot, decisions):
    glossary_tool.validate_shape(snapshot)
    rows = []
    edits = {(x['table'], x['index']): x for x in decisions['edits']}
    removed = {(x['table'], x['index']) for x in decisions['quarantine']}
    for table in glossary_tool.TABLES:
        for index, original in enumerate(snapshot[table]):
            if (table, index) in removed:
                continue
            row = copy.deepcopy(original)
            if (table, index) in edits:
                row.update(copy.deepcopy(edits[(table, index)]['patch']))
            rows.append({'ref': f'{table}:{index}', 'table': table, 'row': row,
                         'original_ref': True})
    for index, item in enumerate(decisions['additions']):
        rows.append({'ref': f'addition:{index}', 'table': item['table'],
                     'row': copy.deepcopy(item['row']), 'original_ref': False})
    groups = defaultdict(list)
    for candidate in rows:
        source = candidate['row'].get('source')
        if not isinstance(source, str) or not source.strip():
            raise ValueError('Candidate has an empty/invalid source: ' + candidate['ref'])
        groups[source.strip().casefold()].append(candidate)
    return {key: value for key, value in groups.items() if len(value) > 1}


def group_id(source):
    return 'G' + hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]


def group_data(groups):
    equivalent, conflicts = [], []
    for source, members in sorted(groups.items()):
        item = {'group_id': group_id(source), 'source_key': source, 'members': members,
                'refs': [m['ref'] for m in members]}
        (equivalent if len({semantic(m['table'], m['row']) for m in members}) == 1 else conflicts).append(item)
    return equivalent, conflicts


def provenance(group, original_decisions, review_lookup):
    raw = []
    for member in group['members']:
        ref = member['ref']
        if member['original_ref']:
            table, index = ref.split(':')
            actions = [copy.deepcopy(x) for key in ('edits', 'quarantine')
                       for x in original_decisions[key] if x['table'] == table and x['index'] == int(index)]
            reviews = copy.deepcopy(review_lookup.get(ref, []))
            reviewer = original_decisions['review_instances'].get(ref)
        else:
            addition = original_decisions['additions'][int(ref.split(':')[1])]
            actions = [{'action': 'addition', **copy.deepcopy(addition)}]
            reviews = []
            reviewer = original_decisions.get('addition_reviewers', {}).get(ref)
        raw.append({'ref': ref, 'table': member['table'], 'row': copy.deepcopy(member['row']),
                    'original_actions': actions, 'entry_reviews': reviews, 'reviewer': reviewer})
    return raw


def conflict_payload(group, original_decisions, review_lookup, texts, snapshot_hash, source_hash, accepted_hash):
    members = provenance(group, original_decisions, review_lookup)
    allowed = sorted({n for m in members for n in m['row'].get('evidence_rows', [])
                      if type(n) is int and 1 <= n <= len(texts)})
    # Every cited ordinal remains allowed; two representative originals from each
    # member are included in full. Workers can request more context separately.
    shown = sorted({n for m in members for n in m['row'].get('evidence_rows', [])[:2]
                    if type(n) is int and 1 <= n <= len(texts)})
    return {'group_id': group['group_id'], 'source_key': group['source_key'],
            'snapshot_sha256': snapshot_hash, 'source_sha256': source_hash,
            'accepted_decisions_sha256': accepted_hash,
            'refs': group['refs'], 'candidates': members, 'allowed_evidence_rows': allowed,
            'records': [{'ordinal': n, 'source': texts[n - 1]} for n in shown]}


def render_input(batch, template):
    return ('# 已审术语同源冲突定向裁决\n'
            '逐组对照候选的原审校、出处和原文。不能以票数或排列顺序决定语义。'
            '只处理本包 group_id；不得改原任务文件。每组返回 keep_ref 与必要 patch，'
            '或有依据地 quarantine 整组（keep_ref=null、patch={}）。reviewer_id 必须是真实的新审校实例 ID。'
            'source_excerpt 必须是所引 evidence_rows 原文中的连续子串。\n\n'
            '## 输入\n```json\n' + stable(batch) +
            '\n```\n\n## 输出模板\n```json\n' + stable(template) + '\n```\n')


def prepared_input(batch_id, input_hash, batch):
    template = {'format_version': 1, 'batch_id': batch_id, 'input_hash': input_hash,
                'reviewer_id': '<actual Luna instance ID>', 'decisions': [
                    {'group_id': p['group_id'], 'action': 'keep', 'keep_ref': p['refs'][0], 'patch': {},
                     'reason': '<specific semantic basis>', 'evidence_rows': [],
                     'source_excerpt': '<continuous original excerpt>', 'issues': []} for p in batch]}
    return render_input({'batch_id': batch_id, 'input_hash': input_hash, 'groups': batch}, template), template


def prepare_batches(conflicts, original_decisions, review_lookup, texts, hashes, token_limit, output):
    payloads = [conflict_payload(g, original_decisions, review_lookup, texts, *hashes) for g in conflicts]
    batches, current = [], []
    def cost(items, batch_number):
        batch_id = f'B{batch_number:05d}'
        input_hash = sha({'batch_id': batch_id, 'groups': items, 'hashes': hashes})
        content, _ = prepared_input(batch_id, input_hash, items)
        return count_tokens(content) + 450 * len(items)
    for payload in payloads:
        trial = current + [payload]
        # Reserve one detailed decision per group as well as the full prompt.
        tokens = cost(trial, len(batches) + 1)
        if tokens > token_limit:
            if not current:
                raise ValueError(f'Resolution group {payload["group_id"]} exceeds complete input/output budget: {tokens} > {token_limit}; no evidence truncated')
            batches.append(current)
            current = [payload]
            tokens = cost(current, len(batches) + 1)
            if tokens > token_limit:
                raise ValueError(f'Resolution group {payload["group_id"]} exceeds complete input/output budget: {tokens} > {token_limit}; no evidence truncated')
        else:
            current = trial
    if current:
        batches.append(current)
    output = Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Resolution output already contains files; keep it and choose a new handoff directory')
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'format_version': 1, 'revision': None, 'snapshot_sha256': hashes[0],
                'source_sha256': hashes[1], 'accepted_decisions_sha256': hashes[2],
                'conflict_group_ids': [p['group_id'] for p in payloads], 'batches': []}
    for index, batch in enumerate(batches, 1):
        batch_id = f'B{index:05d}'
        input_hash = sha({'batch_id': batch_id, 'groups': batch, 'hashes': hashes})
        content, template = prepared_input(batch_id, input_hash, batch)
        input_path = output / f'{batch_id}.input.md'
        result_path = output / f'{batch_id}.result.json'
        input_path.write_text(content, encoding='utf-8')
        (output / f'{batch_id}.template.json').write_text(json.dumps(template, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        manifest['batches'].append({'batch_id': batch_id, 'input_hash': input_hash,
                                    'group_ids': [p['group_id'] for p in batch],
                                    'input_file': input_path.name, 'result_file': result_path.name,
                                    'template_file': f'{batch_id}.template.json'})
    path = output / 'manifest.json'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return path, manifest


def load_resolutions(manifest_path, conflicts, hashes, texts, raw, review_lookup, independent, revision=None):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if (manifest.get('format_version') != 1 or
            (revision is not None and manifest.get('revision') != revision) or
            [manifest.get(k) for k in ('snapshot_sha256', 'source_sha256', 'accepted_decisions_sha256')] != list(hashes)):
        raise ValueError('Resolution manifest snapshot/source/accepted decisions hash mismatch')
    expected = {g['group_id']: g for g in conflicts}
    if (not isinstance(manifest.get('conflict_group_ids'), list) or
            len(manifest['conflict_group_ids']) != len(expected) or set(manifest['conflict_group_ids']) != set(expected)):
        raise ValueError('Resolution manifest must cover the current conflict groups exactly once')
    seen, accepted, seen_batches = set(), {}, set()
    for batch in manifest.get('batches', []):
        batch_id = batch.get('batch_id')
        if not isinstance(batch_id, str) or not batch_id.startswith('B') or not batch_id[1:].isdigit():
            raise ValueError('Invalid resolution batch ID')
        if batch_id in seen_batches:
            raise ValueError('Duplicate resolution batch ID')
        seen_batches.add(batch_id)
        gids = batch.get('group_ids')
        if not isinstance(gids, list) or not gids or len(gids) != len(set(gids)) or not set(gids) <= set(expected):
            raise ValueError('Resolution batch has invalid group scope')
        if any(g in seen for g in gids):
            raise ValueError('Resolution group assigned more than once')
        seen.update(gids)
        expected_payloads = [
            conflict_payload(expected[g], raw, review_lookup, texts, *hashes)
            for g in gids]
        expected_hash = sha({'batch_id': batch_id, 'groups': expected_payloads, 'hashes': hashes})
        if batch.get('input_hash') != expected_hash:
            raise ValueError('Resolution batch input hash mismatch: ' + batch_id)
        input_name = batch.get('input_file')
        result_name = batch.get('result_file')
        if input_name != f'{batch_id}.input.md' or result_name != f'{batch_id}.result.json':
            raise ValueError('Resolution paths must use their batch ID')
        input_file = manifest_path.parent / input_name
        if not input_file.is_file():
            raise ValueError('Resolution input file missing: ' + str(input_file))
        expected_input, _ = prepared_input(batch_id, expected_hash, expected_payloads)
        if input_file.read_text(encoding='utf-8') != expected_input:
            raise ValueError('Resolution input content changed: ' + batch_id)
        result_file = manifest_path.parent / result_name
        if not result_file.is_file():
            raise ValueError('Resolution result file missing: ' + str(result_file))
        result = json.loads(result_file.read_text(encoding='utf-8-sig'))
        if (result.get('format_version') != 1 or result.get('batch_id') != batch_id or
                result.get('input_hash') != batch.get('input_hash')):
            raise ValueError('Resolution result identity/hash mismatch: ' + batch_id)
        reviewer = result.get('reviewer_id')
        if not isinstance(reviewer, str) or not reviewer.startswith('/root/') or len(reviewer) < 7:
            raise ValueError('Resolution requires a real subagent reviewer ID: ' + batch_id)
        decisions = result.get('decisions')
        if (not isinstance(decisions, list) or len(decisions) != len(gids) or
                any(not isinstance(d, dict) for d in decisions) or
                {d.get('group_id') for d in decisions} != set(gids)):
            raise ValueError('Resolution result must cover assigned groups exactly once: ' + batch_id)
        for item in decisions:
            group = expected[item['group_id']]
            rows = item.get('evidence_rows')
            allowed = {n for m in group['members'] for n in m['row'].get('evidence_rows', [])
                       if type(n) is int and 1 <= n <= len(texts)}
            excerpt = item.get('source_excerpt')
            if (not isinstance(rows, list) or not rows or len(set(rows)) != len(rows)
                    or any(type(n) is not int or n not in allowed for n in rows)
                    or not isinstance(excerpt, str) or not excerpt.strip()
                    or not any(excerpt in texts[n - 1] for n in rows)):
                raise ValueError('Resolution source_excerpt must cite allowed continuous original text: ' + item['group_id'])
            if not isinstance(item.get('reason'), str) or not item['reason'].strip():
                raise ValueError('Resolution requires a specific reason: ' + item['group_id'])
            original_reviewers = {raw['review_instances'].get(ref) for ref in group['refs']}
            original_reviewers.update(raw.get('addition_reviewers', {}).get(ref) for ref in group['refs'])
            if reviewer in original_reviewers or not independent(reviewer, allowed):
                raise ValueError('Resolution requires a new reviewer independent of extraction: ' + item['group_id'])
            issues = item.get('issues', [])
            if not isinstance(issues, list) or any(not isinstance(i, dict) for i in issues):
                raise ValueError('Resolution issues must be a list of objects')
            if any(i.get('severity') == 'blocking' for i in issues):
                raise ValueError('Unresolved blocking glossary resolution issue: ' + item['group_id'])
            action = item.get('action')
            if action not in ('keep', 'quarantine'):
                raise ValueError('Resolution action must be keep or quarantine')
            patch = item.get('patch', {})
            if action == 'keep':
                if item.get('keep_ref') not in group['refs'] or not isinstance(patch, dict):
                    raise ValueError('Resolution keep_ref/patch is outside its group')
                forbidden = {'source', 'evidence_rows', 'extraction_candidates', 'provisional_selection', 'review_provenance'}
                if any(key in forbidden for key in patch):
                    raise ValueError('Resolution patch cannot alter source or provenance')
            elif item.get('keep_ref') not in (None, '') or patch not in ({}, None):
                raise ValueError('Whole-group quarantine cannot select a keeper or patch')
            accepted[item['group_id']] = {**copy.deepcopy(item), 'reviewer_id': reviewer,
                                          'batch_id': batch_id, 'input_hash': batch['input_hash']}
    if seen != set(expected) or set(accepted) != set(expected):
        raise ValueError('Resolution result scope incomplete')
    return accepted


def merge_decisions(snapshot, raw, normalized, equivalent, conflicts, resolutions, review_lookup):
    final = copy.deepcopy(normalized)
    # Each original ref may have exactly one final action under glossary_tool.
    original_actions = {'edits': copy.deepcopy(raw['edits']), 'quarantine': copy.deepcopy(raw['quarantine']),
                        'additions': copy.deepcopy(raw['additions'])}
    edits = {(x['table'], x['index']): x for x in final['edits']}
    quarantine = {(x['table'], x['index']): x for x in final['quarantine']}
    dropped_additions = set()
    report = []
    for group in equivalent + conflicts:
        resolution = resolutions.get(group['group_id'])
        if group in conflicts and resolution is None:
            raise ValueError('Conflicting reviewed source needs prepare-glossary-resolution: ' + group['source_key'])
        keeper = resolution.get('keep_ref') if resolution else group['refs'][0]
        patch = resolution.get('patch', {}) if resolution else {}
        full_quarantine = resolution is not None and resolution['action'] == 'quarantine'
        all_rows = provenance(group, raw, review_lookup)
        all_evidence = sorted({n for x in all_rows for n in x['row'].get('evidence_rows', []) if type(n) is int})
        retained = None if full_quarantine else next(x for x in group['members'] if x['ref'] == keeper)
        if retained:
            merged_row = copy.deepcopy(retained['row'])
            merged_row.update(copy.deepcopy(patch))
            merged_row['evidence_rows'] = all_evidence
            candidates = []
            for x in all_rows:
                candidates.extend(copy.deepcopy(x['row'].get('extraction_candidates', [])))
            if candidates:
                merged_row['extraction_candidates'] = candidates
            notes = [x['row'].get('note') for x in all_rows if x['row'].get('note')]
            if notes:
                merged_row['note'] = '\n'.join(dict.fromkeys(notes))
            merged_row['review_provenance'] = {'source_refs': group['refs'], 'reviewers':
                {x['ref']: x['reviewer'] for x in all_rows}, 'resolution': resolution or 'equivalent'}
        for member in group['members']:
            ref = member['ref']
            reason = (resolution['reason'] if resolution else '已审候选语义字段完全相同，机械合并')
            if member['original_ref']:
                table, number = ref.split(':'); key = (table, int(number))
                if member is retained:
                    delta = {k: v for k, v in merged_row.items() if snapshot[table][int(number)].get(k) != v}
                    if delta:
                        edits[key] = {'table': table, 'index': int(number), 'patch': delta,
                                      'reason': reason, 'evidence_rows': all_evidence[:2]}
                    quarantine.pop(key, None)
                else:
                    edits.pop(key, None)
                    quarantine[key] = {'table': table, 'index': int(number), 'reason': reason,
                                       'evidence_rows': all_evidence[:2]}
            elif member is retained:
                final['additions'][int(ref.split(':')[1])]['row'] = merged_row
            else:
                dropped_additions.add(int(ref.split(':')[1]))
        report.append({'group_id': group['group_id'], 'source_key': group['source_key'],
                       'kind': 'conflict' if group in conflicts else 'equivalent',
                       'original_reviews': all_rows, 'decision': resolution or {'action': 'keep', 'keep_ref': keeper,
                                                                                 'reason': 'same semantic fields'}})
    final['edits'] = list(edits.values())
    final['quarantine'] = list(quarantine.values())
    final['additions'] = [x for i, x in enumerate(final['additions']) if i not in dropped_additions]
    final['review_summary'] += f'\n同源合并：{len(equivalent)} 组等价，{len(conflicts)} 组独立定向裁决。'
    final['resolution_provenance'] = {'original_actions': original_actions, 'groups': report}
    return final


def normalize_r8_building_categories(snapshot, decisions):
    """Keep two reviewed building subtypes while using the shared build schema.

    This runs only on the derived freeze decisions. The accepted task results,
    collision payloads and their hashes remain unchanged.
    """
    expected = {561: ('watch tower', '瞭望塔'), 2447: ('Stronghold', '要塞')}
    final = copy.deepcopy(decisions)
    conversions = []
    for index, (source, translation) in expected.items():
        ref = f'terms:{index}'
        original = snapshot['terms'][index]
        matches = [item for item in final['edits'] if item['table'] == 'terms' and item['index'] == index]
        if len(matches) != 1 or any(item['table'] == 'terms' and item['index'] == index for item in final['quarantine']):
            raise ValueError('Expected one retained reviewed building edit: ' + ref)
        action = matches[0]
        row = {**original, **action['patch']}
        if (row.get('source'), row.get('recommended_translation'), row.get('category_path')) != (source, translation, '建筑'):
            raise ValueError('Reviewed building row differs from the r8 compatibility scope: ' + ref)
        prior_note = row.get('note', '')
        if prior_note is None:
            prior_note = ''
        if not isinstance(prior_note, str):
            raise ValueError('Expected textual note for reviewed building row: ' + ref)
        subtype_note = '细分类：建筑（原审校类别；共享术语分类枚举归入“其他”）'
        after_note = prior_note.rstrip() + ('\n' if prior_note.strip() else '') + subtype_note
        action['patch']['category_path'] = '其他'
        action['patch']['note'] = after_note
        conversions.append({'ref': ref, 'source': source, 'from_category_path': '建筑',
                            'to_category_path': '其他', 'previous_note': prior_note,
                            'derived_note': after_note,
                            'basis': 'r8 reviewed building subtype; shared glossary_tool.TERM_CATEGORIES has no 建筑 value'})
    final['resolution_provenance']['category_schema_compatibility'] = conversions
    return final
