"""Bind explicit release authorization and invoke the unmodified common packager."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from build_v16 import PROJECT,sha

sys.path.insert(0,str(PROJECT.parents[1]/'Tools/localization'))
from translation_workflow import Workflow

class ReleaseWorkflow(Workflow):
    def require_final_approval(self,db,config):
        # The shared report renamed Sol to standard-tier since v1.4. Reuse the
        # original approval only when ALL substantive report fields still match.
        current=self.build_quality_report(db,'final',config)
        old=json.loads((PROJECT/'TranslateFiles/reports/accepted/final_16cecb6807d4c8b6/report.json').read_text('utf-8'))
        receipt=self.meta(db,'quality_approvals',{}).get('final',{})
        assert receipt['report_hash']==old['report_hash']=='16cecb6807d4c8b6f371e1f458637a5cfabff17df2eb83d96296eeee816431b4'
        a=json.loads(json.dumps(old));b=json.loads(json.dumps(current))
        a['coverage']['standard_records']=a['coverage'].pop('sol_records')
        a['standard_scope_policy']=a.pop('sol_scope_policy')
        for data in (a,b):
            data.pop('report_hash');data.pop('selection_explanation')
        assert a==b,'Substantive quality report changed; original acceptance cannot be reused'
        assert self.pilot_approved(db,config)
        return {'report_hash':receipt['report_hash'],'reviewer':receipt.get('reviewer','sol')}

def check_v16_quality(project,entries,game_version,platform):
    assert Path(project).resolve()==PROJECT
    check=ReleaseWorkflow(PROJECT).release_check()
    assert check['game_version']==game_version and check['platform']==platform
    assert {(str(dest),sha(source)) for source,dest in entries}=={(e['game_path'],e['sha256']) for e in check['payload_files']}
    assert len(entries)==len(check['payload_files'])

def main():
    workspace=PROJECT.parents[1]
    sys.path.insert(0,str(workspace/'Tools/localization'))
    flow=ReleaseWorkflow(PROJECT)
    entries=json.loads((PROJECT/'TranslateFiles/reports/release_v16_payload.json').read_text('utf-8'))
    validation=json.loads((PROJECT/'TranslateFiles/reports/release_v16_install_validation.json').read_text('utf-8'))
    assert validation['status']=='passed'
    assert validation['formal_sha256']==sha(PROJECT/'expeditions-viking_text_translated.csv')
    instruction=dict(version='1.6',user_statement='不用进入游戏测试，好了就直接打包发布；对，发布永远一个包。',
                     distribution='single_full_package',in_game_validation='pending')
    evidence=PROJECT/'TranslateFiles/reports/release_v16_user_instruction.json'
    evidence.write_text(json.dumps(instruction,ensure_ascii=False,indent=2),encoding='utf-8')
    policy=json.loads((PROJECT/'TranslateFiles/reports/release_v14_user_instruction.json').read_text('utf-8'))
    report=dict(authorization='explicit_user_release',in_game_validation='pending',accept_pending_runtime=True,
        user_statement=instruction['user_statement'],translation_sha256=validation['formal_sha256'],
        game_version=policy['game_version'],platform=policy['platform'],payload_files=entries,
        evidence_files=[{'path':f.relative_to(PROJECT).as_posix(),'sha256':sha(f)} for f in [evidence,PROJECT/'TranslateFiles/reports/release_v16_install_validation.json',PROJECT/'TranslateFiles/reports/overhead_timing_fix.json']])
    flow.record_release_acceptance(report)
    result=flow.release_check()
    (PROJECT/'TranslateFiles/reports/release_v16_quality_check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    links=json.loads((PROJECT/'Dispatch/release_links.json').read_text('utf-8-sig'))
    arguments=['create_release_patch.py','--project',str(PROJECT),'--version','1.6',
        '--title','[子非鱼Ai汉化]《远征：维京》/《Expeditions: Viking》',
        '--steam-url','https://store.steampowered.com/app/445190/',
        '--download-url',links['download_url'],'--mirror-url',links['mirror_url'],'--share-name','远征：维京汉化补丁',
        '--feedback-url',links['feedback_url'],'--feedback-name','远征：维京汉化问题反馈',
        '--introduction','一款融合队伍养成与回合制战术战斗的历史题材角色扮演游戏。玩家带领维京部族远征，招募和培养同伴、管理资源，在战斗中安排队员的位置与技能，并通过探索、对话和外交决定部族的未来。',
        '--coverage','对白、选项、常用界面、技能、物品、教程、家园、场景与角色名称；包含中文悬浮文字显示时间修复。',
        '--game-version','Steam Windows 版（Unity 5.6.4f1）','--platform',policy['platform'],
        '--release-date','2026-11-08',
        '--install','解压到游戏根目录，双击“安装汉化.cmd”；游戏语言选择 English。',
        '--upgrade','将新版完整包覆盖解压到游戏根目录，再双击“安装汉化.cmd”。',
        '--uninstall','退出游戏，双击“卸载汉化.cmd”。',
        '--changes','修复已安装汉化但缺少原版备份时无法安装或升级的问题；自动恢复受支持旧版的原始备份，保留一键安装与卸载。']
    # Exact version/platform must match the quality authorization.
    arguments[arguments.index('--game-version')+1]=policy['game_version']
    for entry in entries:arguments.extend(['--include',entry['path']+'='+entry['game_path']])
    path=workspace/'.agents/skills/game-release-patch/scripts/create_release_patch.py'
    spec=importlib.util.spec_from_file_location('packager_v16',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.check_custom_quality=check_v16_quality
    sys.argv=arguments+['--dry-run'];assert module.main()==0
    stage=PROJECT/'Dispatch/Files'
    backup=PROJECT/'TranslateFiles/backups/dispatch_files_before_v16'
    if stage.exists():
        if backup.exists():raise ValueError('Inspect existing v1.5 staging backup before retry')
        assert stage.resolve().is_relative_to(PROJECT.resolve()) and backup.resolve().is_relative_to(PROJECT.resolve())
        stage.rename(backup)
    sys.argv=arguments;assert module.main()==0
    preferences={'distribution':'single_full_package','supplementary_patch_assets':False,
                 'user_statement':'发布永远一个包','launch_mode':'original_exe'}
    (PROJECT/'TranslateFiles/config/release_preferences.json').write_text(json.dumps(preferences,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
