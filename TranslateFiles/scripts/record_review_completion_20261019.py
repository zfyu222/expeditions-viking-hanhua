"""Record verified review/export receipts; never change translation state."""
import hashlib
import json
from pathlib import Path
import sqlite3

project = Path(__file__).resolve().parents[2]
root = project / 'TranslateFiles'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

validation = read(root / 'reports/final_validation.json')
assert validation['status'] == 'passed' and validation['revision'] == 17
assert validation['records'] == 23195 and validation['semantic_review'] == 'full'
output = Path(validation['path'])
assert sha(output) == validation['translation_sha256']
frozen = root / 'glossary/r8/freeze_731eced6/built/glossary_reviewed.json'
assert sha(frozen) == '8b1369e804c5c7f66803e0961da266077ff087a5ecc849b9e6806ece5c8b31a4'
assert sha(root / 'snapshots/r16_first_draft_20261018T142909Z_9c5af3c9/drafts.jsonl') == 'b2cfd249a6cda5a00d9d87184b7e19e39ea9d306f196a6c91be934d6bd5d77ac'
ids = ['6283c04c78b642fd9d860001ff195e98', '6c8e42b8a94145e2864b24b0021bde8a',
       '64b22c9c013a408c999bf584f1cacfb0', '46020d56ab444d039654eb9562546d5b',
       'e6e1efeb9d7449fd8993c5098b1e10d4', 'df132607ab6546eba1579d2da97a6399',
       '9f93a47a0ce6443ab48ce22753c8a6d0', '822d1d8820024392897f99a5af9298ed',
       'ea600d195d8c49e58c3c1156aa047fc0', 'dda468d773dc41f79a1ab7fbe0cb5061',
       'a079191ac33a443b996c10c7d63ae70d', '8a6bbd3717b54ba680bfc298aa117e7b']
receipts = [read(root / f'reports/api_runs/{x}.json') for x in ids]
recoveries = sorted((root / 'reports').glob('review_paid_format_recovery_*.json'))
with sqlite3.connect((root / 'state/workflow.sqlite3').as_uri() + '?mode=ro', uri=True) as db:
    stages = dict(db.execute('SELECT stage,count(*) FROM records GROUP BY stage'))
    assert stages == {'review': 23195}
    assert db.execute('SELECT count(*) FROM tasks WHERE revision=17 AND status IN ("pending","running","failed")').fetchone()[0] == 0
    assert db.execute('SELECT count(*) FROM api_calls WHERE status="reserved"').fetchone()[0] == 0
report = {
    'status': 'translation_exported', 'revision': 17, 'records': 23195,
    'source': 'expeditions-viking_text.csv', 'output': str(output),
    'validation': validation, 'record_stages': stages,
    'glossary_sha256': sha(frozen), 'original_draft_snapshot_unchanged': True,
    'initial_review': {'records': 23195, 'passed': 22056, 'failed': 1139,
                       'note': 'First failing gate statistics are not semantic accuracy rates.'},
    'ordinary_review_rounds': [read(p) for p in sorted((root / 'reports/review_rounds').glob('review_*.json'))],
    'api_receipts': [str(root / f'reports/api_runs/{x}.json') for x in ids],
    'api_continuation': {
        'requests_started': sum(r['performance']['requests_started'] for r in receipts),
        'accepted_batches': sum(r['accepted'] for r in receipts),
        'failed_attempts': sum(r['failed'] for r in receipts),
        'tokens': {k: sum(r['performance']['run_tokens'].get(k, 0) for r in receipts)
                  for k in ['prompt_tokens','completion_tokens','total_tokens','cached_prompt_tokens','reported_requests','unknown_requests']},
        'note': 'Cached prompt tokens are a subset of prompt tokens. Prior paid history is retained.'},
    'offline_format_recovery': {'reports': [str(p) for p in recoveries],
        'records': sum(read(p)['recovered_records'] for p in recoveries),
        'api_requests': 0, 'semantic_content_unchanged': True},
    'final_dispute_decisions': [str(p) for p in sorted((root / 'reports/sol_rounds').glob('*.decisions*.json'))],
    'known_followups': [
        'Dynamic visible branches remain protected: 498 occurrences / 53 forms; project-specific repack handling and runtime verification remain.',
        'No game repack or in-game validation was performed for this export.',
        'An inherited unmatched exception cannot be removed through API term_refs alone. One failed handoff was completed by an independent Sol using the full shared Codex contract; no transport mapping or shared code was changed.'],
}
# Keep the completion summary compact; detailed round evidence remains in original reports.
report['ordinary_review_rounds'] = [{k: r.get(k) for k in
    ['round','stage','phase','scope','checked_records','failed_records','clean','failure_summary']}
    for r in report['ordinary_review_rounds']]
target = root / 'reports/review_completion_20261019.json'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
section = '''
## 2026-10-19：独立语义审校与正式导出完成

- 延续 revision 17 已保存候选，首轮独立审校完整覆盖 23,195 条。统一验收首轮 22,056 条通过、1,139 条需处理；后续仅重派失败项，保留通过记录、真实来源、作者及累计修复次数。首个失败门槛统计不代表翻译准确率。
- 保留所有付费回复，Sol 对 20 个异常批次作无损格式恢复，共收回 340 条候选，没有为这些恢复新增 API 请求。另有缺少必需字段的批次交新 Sol 独立完成；不自动补 keep、译文或证据。
- 本次接续实际发送 1,720 次 API 请求（包括 237 次失败尝试），服务端报告输入 5,758,196、输出 5,270,021、总计 11,028,217 Token；缓存 2,459,648 为输入子项，不另相加。旧消费及作者历史保留。
- 审校修复按共同累计预算升级：Sol 定向修复保留已满足术语及语境例外；最后所有 23,195 条均到 review。最终报告的 41 项明确遗留提示经 Sol 裁决，3 条确需修复并通过复查；更新报告只再核对 2 项，其余裁决复用。最终质量轮 2 已批准，未启动全文润色。
- 正式译文 `expeditions-viking_text_translated.csv` 由官方 export 生成，无表头、单列、按源记录顺序。导出前全库结构、保护内容及术语/已审语境例外检查通过；最终验收报告 `TranslateFiles/reports/final_validation.json`，本轮汇总 `TranslateFiles/reports/review_completion_20261019.json`。
- r8 冻结术语哈希及审校前 r16 草稿快照哈希不变。没有重新提取术语、重译全文或调用 restart-body；API 模型仍为 deepseek-flash，升级及争议角色使用独立 gpt-6-sol 实例。
- 待下一阶段：动态可见分支仍整体保护（已有清单 498 次、53 种形式），需项目内专项处理及回填后实机检查。本次未修改游戏载荷、未回填或发布，新导出实机状态为 pending_repack；此前版本的实机结论不能替代本轮验证。
- 接续中发现历史无关例外在 API term_refs 中无法表达撤销，已由独立 Sol 使用完整共同 Codex 协议具证撤销并正常收集；未改共享程序或放宽门槛。
'''
readme = project / 'README.md'
text = readme.read_text(encoding='utf-8')
heading = '## 2026-10-19：独立语义审校与正式导出完成'
assert heading not in text
anchor = '### 第 3 步：回填'
assert anchor in text
readme.write_text(text.replace(anchor, section + '\n' + anchor, 1), encoding='utf-8')
doc = root / 'TranslateDoc.md'
text = doc.read_text(encoding='utf-8')
assert heading not in text
doc.write_text(text.rstrip() + '\n\n' + section.strip() + '\n', encoding='utf-8')
print(json.dumps({'status':report['status'],'records':23195,'report':str(target),
                  'translation_sha256':validation['translation_sha256']}, ensure_ascii=True))
