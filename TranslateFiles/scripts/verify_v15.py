"""Replay new install, v1.4 upgrade, uninstall, and all-input preflight."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys
import zipfile
from build_v15 import PROJECT, PAYLOAD, sha

def main():
    root=Path(tempfile.mkdtemp(prefix='v15 整包 ',dir=PROJECT/'TranslateFiles/cache'))
    tools=root/'汉化工具'
    archive_mode=len(sys.argv)>1
    if archive_mode:
        with zipfile.ZipFile(sys.argv[1]) as archive:
            assert archive.testzip() is None
            manifest=json.loads(archive.read('PATCH_MANIFEST.json').decode('utf-8'))
            assert len(manifest['files'])==7
            for entry in manifest['files']:
                import hashlib
                assert hashlib.sha256(archive.read(entry['archive_path'])).hexdigest()==entry['sha256']
            guide=archive.read('补丁说明.txt').decode('utf-8-sig')
            assert all('v'+v in guide for v in ['1.2','1.3','1.4','1.5'])
            archive.extractall(root)
    else:shutil.copytree(PAYLOAD,tools)
    assets=root/'Expeditions Viking_Data/resources.assets'
    dll=root/'Expeditions Viking_Data/Managed/Assembly-CSharp.dll'
    dll.parent.mkdir(parents=True)
    a_backup=Path(str(assets)+'.zfy.backup');d_backup=Path(str(dll)+'.zfy-timing.backup')
    orig_a=PROJECT/'backup/resources.assets';orig_d=PROJECT/'Analysis/overhead_timing/Assembly-CSharp.original.dll'
    new_a=PROJECT/'Game/Expeditions Viking_Data/resources.assets';new_d=PROJECT/'Analysis/overhead_timing/Assembly-CSharp.fixed.dll'
    checks=[]
    def run(action='install',success=True):
        if archive_mode:
            name='安装汉化.cmd' if action=='install' else '卸载汉化.cmd'
            command='cmd.exe /d /c call "'+str(root/name)+'"'
        else:command=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(tools/'install.ps1'),'-Action',action,'-GameRoot',str(root)]
        result=subprocess.run(command,stdin=subprocess.DEVNULL,capture_output=True,timeout=120)
        assert (result.returncode==0)==success,(result.stdout+result.stderr).decode(errors='replace')
    shutil.copy2(orig_a,assets);shutil.copy2(orig_d,dll)
    run();assert sha(assets)==sha(new_a) and sha(dll)==sha(new_d);checks.append('fresh_install')
    assert sha(a_backup)==sha(orig_a) and sha(d_backup)==sha(orig_d)
    run();checks.append('idempotent_install')
    run('uninstall');assert sha(assets)==sha(orig_a) and sha(dll)==sha(orig_d);checks.append('uninstall_both_originals')
    run('uninstall');checks.append('idempotent_uninstall')
    # Old published installer produces exactly this state and original backup.
    shutil.copy2(new_a,assets);run();assert sha(assets)==sha(new_a) and sha(dll)==sha(new_d);checks.append('upgrade_v14')
    run();checks.append('upgrade_with_timer_hotfix_already_present')
    run('uninstall')
    dll.write_bytes(b'unknown dll');run(success=False)
    assert sha(assets)==sha(orig_a) and dll.read_bytes()==b'unknown dll';checks.append('unknown_second_file_no_first_file_change')
    shutil.copy2(orig_d,dll)
    (tools/'overhead-timing.hdiff').write_bytes(b'broken second diff');run(success=False)
    assert sha(assets)==sha(orig_a) and sha(dll)==sha(orig_d);checks.append('corrupt_second_diff_transaction_preserved')
    shutil.copy2(PAYLOAD/'overhead-timing.hdiff',tools/'overhead-timing.hdiff')
    run();d_backup.write_bytes(b'bad original backup');run('uninstall',success=False)
    assert sha(assets)==sha(new_a) and sha(dll)==sha(new_d);checks.append('bad_backup_uninstall_no_partial_changes')
    report=dict(status='passed',version='1.5',checks=checks,fixture=str(root),new_in_game_test=False,
                formal_sha256=sha(PROJECT/'expeditions-viking_text_translated.csv'),resources_sha256=sha(new_a),dll_sha256=sha(new_d))
    if archive_mode:report.update(archive_sha256=sha(Path(sys.argv[1])),zip_crc='passed',manifest_hashes='passed',player_cmd_entrypoints='passed')
    name='release_v15_archive_validation.json' if archive_mode else 'release_v15_install_validation.json'
    (PROJECT/'TranslateFiles/reports'/name).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True,indent=2))

if __name__=='__main__':main()
