"""Verify v1.4 resources and differential installer; never launch the game."""
import csv
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from accept_repack_20261019 import sha,rows,collect
sys.path.insert(0,str(PROJECT))
from build_localization import CUSTOM_CATEGORY_DIRS

def main():
    folder=PROJECT/'TranslateFiles/cache/release_v14'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    assets=PROJECT/'Game/Expeditions Viking_Data/resources.assets'
    original=PROJECT/'backup/resources.assets'
    proof=json.loads((PROJECT/'TranslateFiles/reports/repack_review_acceptance_20261019.json').read_text('utf-8'))
    assert proof['status']=='accepted'
    assert proof['official_sha256']==sha(PROJECT/'expeditions-viking_text_translated.csv')
    repack=rows(PROJECT/'TranslateFiles/repack/translation_for_repack.csv')
    with (PROJECT/'extracted_strings.csv').open(encoding='utf-8-sig',newline='') as stream:extracted=list(csv.DictReader(stream))
    assert len(repack)==len(extracted)==23195
    source=rows(PROJECT/'expeditions-viking_text.csv')
    assert all(r['原文']==s for r,s in zip(extracted,source))
    ids={'dialogue':9146,'gui':9040,'homestead':9063,'input':9744,'items':9309,'names':9804,'scenedata':9795,'skills':9165,'tutorial':9799}
    report={'status':'checking','version':'1.4','in_game_test':'not_performed_by_explicit_user_instruction',
            'official_sha256':proof['official_sha256'],'repack_sha256':sha(PROJECT/'TranslateFiles/repack/translation_for_repack.csv'),
            'assets_sha256':sha(assets),'original_sha256':sha(original),'assets':[],'records_checked':0}
    found={}
    for cat,dirname in CUSTOM_CATEGORY_DIRS.items():
        path=folder/f'{cat}.xml'
        command=['D:/StaticHanHua/Tools/UABEA/UABEAvalonia/bin/Release/net8.0/UABEAvalonia.exe','exporttext',str(assets),str(ids[cat]),str(path)]
        subprocess.run(command,capture_output=True,check=True,timeout=60)
        expected=PROJECT/f'Chinese_Localization/Chinese/Localization/{dirname}/{dirname}Chinese.xml'
        assert sha(path)==sha(expected),cat
        found[cat]=collect(cat,path)
        report['assets'].append({'category':cat,'path_id':ids[cat],'xml_sha256':sha(path),'byte_identical':True})
    assert all(found[r['category']].get(r['key'])==t for r,t in zip(extracted,repack))
    report['records_checked']=23195
    payload=PROJECT/'ReleasePayload'
    test_root=folder/'player_install'
    data=test_root/'Expeditions Viking_Data';data.mkdir(parents=True)
    patch=test_root/'ZFY_Translation_Patch';shutil.copytree(payload,patch)
    target=data/'resources.assets';shutil.copy2(original,target)
    installer=patch/'应用汉化补丁.bat'
    assert '"' not in str(installer) and installer.resolve().is_relative_to(folder.resolve())
    command=f'cmd.exe /d /c call "{installer}" < NUL'
    installed=subprocess.run(command,cwd=test_root,capture_output=True,timeout=90)
    (folder/'install.stdout.txt').write_bytes(installed.stdout)
    (folder/'install.stderr.txt').write_bytes(installed.stderr)
    assert installed.returncode==0,'Installer returned failure'
    assert sha(target)==report['assets_sha256']
    assert sha(data/'resources.assets.zfy.backup')==report['original_sha256']
    assert not (data/'resources.assets.zfy.tmp').exists()
    repeated=subprocess.run(command,cwd=test_root,capture_output=True,timeout=30)
    assert repeated.returncode!=0 and sha(target)==report['assets_sha256']
    report['player_install']={'passed':True,'repeat_install_refused':True,'backup_hash_verified':True,'output_sha256':sha(target)}
    report['payload_files']=[{'path':'ReleasePayload/'+path.name,'game_path':'ZFY_Translation_Patch/'+path.name,
        'sha256':sha(path),'size':path.stat().st_size} for path in sorted(payload.iterdir()) if path.is_file()]
    assert len(report['payload_files'])==3
    report['status']='passed'
    report['evidence_folder']=str(folder.relative_to(PROJECT))
    dest=PROJECT/'TranslateFiles/reports/release_v14_static_validation.json'
    dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','records_checked','assets_sha256','in_game_test')},ensure_ascii=True))

if __name__=='__main__':main()
