"""Create the reviewed v1.4 archive through the common packager."""
import json
from pathlib import Path
import sys
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
import package_reviewed_v14

def main():
    policy=json.loads((PROJECT/'TranslateFiles/reports/release_v14_user_instruction.json').read_text('utf-8'))
    arguments=['package_reviewed_v14.py','--project',str(PROJECT),'--version','1.4',
        '--introduction','为《Expeditions Viking》Steam Windows 版制作的简体中文汉化补丁。\n\n反馈：https://github.com/zfyu222/expeditions-viking-hanhua/issues\n下载与更新：https://github.com/zfyu222/expeditions-viking-hanhua/releases',
        '--coverage','对白、选项、常用界面、技能、物品、教程、家园、场景与角色名称。',
        '--game-version',policy['game_version'],'--platform',policy['platform'],
        '--install','退出游戏，将 ZFY_Translation_Patch 文件夹解压到游戏根目录，运行其中“应用汉化补丁.bat”。安装器自动备份原资源，版本不兼容时拒绝应用。游戏语言选择 English；如有旧 Custom Localization 覆盖文件，请先自行移走或备份。',
        '--uninstall','退出游戏，将 Expeditions Viking_Data/resources.assets.zfy.backup 恢复为 resources.assets，再移走 ZFY_Translation_Patch 文件夹。也可通过 Steam 验证文件恢复原版。',
        '--verification','已完成 238 条回填改动的独立语义审校及必要修复；23,195 条文本与部署资源逐条一致，9 个 TextAsset 逐字节一致；在临时目录按玩家一键安装流程安装，资源哈希与构建产物相同，备份和重复安装保护通过。本版按项目所有者明确要求未启动游戏进行新的实机测试。',
        '--known-issues','AI 汉化可能仍有措辞或语境问题；本版未做新的实机复测，任务日志界面未单独实测。仅支持指定原始资源版本，其他 Mod 或已修改资源可能无法应用。',
        '--changes','完成 238 条回填补译的独立语义审校，相比 v1.3 回填候选修正 13 条；处理选项漏译回退、术语语境及强调范围。审校结果纳入正式译文，保留 291 处性别分支本地化，重新构建并验证差分安装。']
    for name in ('resources.assets.hdiff','hpatchz.exe','应用汉化补丁.bat'):
        arguments.extend(['--include','ReleasePayload/'+name+'=ZFY_Translation_Patch/'+name])
    sys.argv=arguments+['--dry-run'];assert package_reviewed_v14.main()==0
    old=PROJECT/'Dispatch/Files';archive=PROJECT/'TranslateFiles/backups/dispatch_files_before_v14'
    if old.exists():
        assert old.resolve().is_relative_to(PROJECT.resolve()) and archive.resolve().is_relative_to(PROJECT.resolve())
        if archive.exists():raise ValueError('Staging backup already exists; inspect before retry')
        old.rename(archive)
    sys.argv=arguments
    return package_reviewed_v14.main()

if __name__=='__main__':raise SystemExit(main())
