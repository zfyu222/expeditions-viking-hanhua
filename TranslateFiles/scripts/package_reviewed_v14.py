"""Project-specific release policy: user waived a new game launch for v1.4.

Retain common packager, semantic approval and verified payload bindings. Never
create an in-game pass record for a test that was not performed.
"""
import importlib.util
import json
from pathlib import Path
import sys

PROJECT=Path(__file__).resolve().parents[2]
WORKSPACE=PROJECT.parents[1]
sys.path.insert(0,str(WORKSPACE/'Tools/localization'))
import translation_workflow as w

def check_project_release(project,entries,game_version,platform):
    assert Path(project).resolve()==PROJECT
    waiver=w.read_json(PROJECT/'TranslateFiles/reports/release_v14_user_instruction.json')
    assert waiver['skip_new_in_game_test'] is True and waiver['version']=='1.4'
    proof=w.read_json(PROJECT/'TranslateFiles/reports/repack_review_acceptance_20261019.json')
    validation=w.read_json(PROJECT/'TranslateFiles/reports/release_v14_static_validation.json')
    final=w.read_json(PROJECT/'TranslateFiles/reports/final_validation.json')
    assert proof['status']=='accepted' and proof['scope_records']==238
    assert validation['status']=='passed' and validation['records_checked']==23195
    assert final['status']=='passed'
    assert proof['official_sha256']==validation['official_sha256']==final['translation_sha256']==w.digest(PROJECT/'expeditions-viking_text_translated.csv')
    flow=w.Workflow(PROJECT)
    with flow.db() as db:
        config=flow.config(db);approval=flow.require_final_approval(db,config)
        assert approval['report_hash']==final['quality_review']['report_hash']
        assert db.execute('SELECT count(*) FROM records WHERE stage="review"').fetchone()[0]==23195
        assert not db.execute('SELECT 1 FROM tasks WHERE revision=? AND status IN ("pending","running","failed")',(flow.meta(db,'revision'),)).fetchone()
    expected={(entry['game_path'],entry['sha256']) for entry in validation['payload_files']}
    selected={(str(destination),w.digest(source)) for source,destination in entries}
    assert selected==expected and len(entries)==3
    assert game_version==waiver['game_version'] and platform==waiver['platform']

def main():
    path=WORKSPACE/'.agents/skills/game-release-patch/scripts/create_release_patch.py'
    spec=importlib.util.spec_from_file_location('shared_packager',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.check_custom_quality=check_project_release
    return module.main()

if __name__=='__main__':raise SystemExit(main())
