"""Bounded, source-bound import of the explicitly authorized 238 repack proposals.

Semantic work and acceptance use the shared review pipeline, not this importer.
"""
import csv
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import uuid

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT.parents[1]/'Tools/localization'))
import translation_workflow as w

def read_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        rows=list(csv.reader(stream))
    assert all(len(r)==1 for r in rows)
    return [r[0] for r in rows]

def prepare():
    flow=w.Workflow(PROJECT)
    receipt=flow.root/'reports/repack_review_scope_20261019.json'
    if receipt.exists():raise ValueError('Scope already prepared; continue existing tasks')
    prep=w.read_json(flow.root/'reports/repack_translation_prep.json')
    official=PROJECT/'expeditions-viking_text_translated.csv'
    candidate=flow.root/'repack/translation_for_repack.csv'
    assert w.digest(official)==prep['official_sha256']
    assert w.digest(candidate)==prep['repack_sha256']
    src=read_rows(PROJECT/'expeditions-viking_text.csv')
    proposed=read_rows(candidate)
    indexes=sorted({row['index'] for key in ('restored','brace_fixes','overrides') for row in prep[key]})
    assert len(indexes)==238 and len(src)==len(proposed)==23195
    backup=flow.root/'backups'/('repack_review_'+uuid.uuid4().hex)
    backup.mkdir(parents=True)
    source=sqlite3.connect(flow.db_path.as_uri()+'?mode=ro',uri=True)
    dest=sqlite3.connect(backup/'workflow.sqlite3')
    try:source.backup(dest)
    finally:source.close();dest.close()
    for path in (official,candidate,flow.root/'config/workflow.json'):
        shutil.copy2(path,backup/path.name)
    rows=[];previous_candidates=[]
    with flow.db() as db:
        config=flow.config(db)
        assert not db.execute('SELECT 1 FROM tasks WHERE status="running"').fetchone()
        assert not db.execute('SELECT 1 FROM api_calls WHERE status="reserved"').fetchone()
        assert db.execute('SELECT count(*) FROM records WHERE stage="review"').fetchone()[0]==23195
        flow.require_review_round_complete(db,'review');flow.guard_sol_dispatch(db)
        for index in indexes:
            record=dict(db.execute('SELECT * FROM records WHERE ordinal=?',(index+1,)).fetchone())
            assert record['source']==src[index] and not record['locked']
            record.update(proposed_translation=proposed[index],origin='v1.3 repack proposal',index=index)
            rows.append(record)
            previous_candidates.extend(dict(r) for r in db.execute('SELECT * FROM review_candidates WHERE record_id=?',(record['id'],)))
        # This is an explicit user-authorized candidate import, not an approval.
        # Archive producer candidates so a prior accepted candidate cannot replace
        # this newly supplied translation/exception snapshot during task planning.
        w.write_json(backup/'records_before_import.json',rows)
        w.write_json(backup/'review_candidates_before_import.json',previous_candidates)
        for record in rows:
            db.execute('DELETE FROM review_candidates WHERE record_id=?',(record['id'],))
            db.execute('UPDATE records SET translation=? WHERE id=?',
                       (record['proposed_translation'],record['id']))
        flow.event(db,'import_repack_proposals',{'records':len(rows),'backup':str(backup),
            'candidate_sha256':w.digest(candidate),'source_sha256':w.digest(PROJECT/'expeditions-viking_text.csv'),
            'approval':False,'origin':'project repack_prepare.py / v1.2 shipped translations and four overrides'})
    reason=('用户授权对回填后新增的本批译文作独立语义审校。候选来自旧版补译，不代表已审通过。'
            '逐条核对完整原文、选项动作、数量、否定、语气、术语和格式；'
            '花括号内是玩家可见选项，应正常翻译并保留括号。'
            '拉丁语/古英语/盖尔语风味台词应结合原句功能与冻结规则判断是否保留，不因存在外语就强制音译或改成另一句外语。'
            '保持已正确的正文，仅修实际错误；按共同协议留下六维证据和必要语境例外。')
    result=flow.reopen_body_ids(reason,[r['id'] for r in rows])
    report={'scope_records':238,'record_ids':[r['id'] for r in rows],
            'original_official_sha256':prep['official_sha256'],'repack_proposal_sha256':prep['repack_sha256'],
            'backup':str(backup),'source_binding_verified':True,'original_rows':rows,'dispatch':result}
    w.write_json(receipt,report)
    print(json.dumps({'scope_records':238,'dispatch':result,'report':str(receipt)},ensure_ascii=True))

if __name__=='__main__':prepare()
