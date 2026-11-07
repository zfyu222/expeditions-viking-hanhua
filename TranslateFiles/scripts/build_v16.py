"""Add exact-version reverse differences to recover missing original backups."""
import json
from pathlib import Path
import shutil
import subprocess
from build_v15 import PROJECT,sha

PAYLOAD=PROJECT/'ReleasePayload/v1.6'
def main():
    PAYLOAD.mkdir(exist_ok=True)
    for f in (PROJECT/'ReleasePayload/v1.5').iterdir():
        if f.is_file():shutil.copy2(f,PAYLOAD/f.name)
    shutil.copy2(PROJECT/'TranslateFiles/scripts/InstallV16.ps1',PAYLOAD/'install.ps1')
    config=json.loads((PAYLOAD/'config.json').read_text('utf-8-sig'));config['version']='1.6'
    work=PROJECT/'Analysis/overhead_timing/v16';work.mkdir(exist_ok=True)
    v13=work/'resources.v13.assets'
    hpatch=PROJECT/'ReleasePayload/hpatchz.exe'
    if not v13.exists():
        subprocess.run([str(hpatch),str(PROJECT/'backup/resources.assets'),str(PROJECT/'TranslateFiles/backups/release_payload_v13/resources.assets.hdiff'),str(v13)],check=True,stdout=subprocess.DEVNULL)
    pairs=[(config['files'][0],PROJECT/'Game/Expeditions Viking_Data/resources.assets',PROJECT/'backup/resources.assets','recover-v14-resources.hdiff'),
           (config['files'][0],v13,PROJECT/'backup/resources.assets','recover-v13-resources.hdiff'),
           (config['files'][1],PROJECT/'Analysis/overhead_timing/Assembly-CSharp.fixed.dll',PROJECT/'Analysis/overhead_timing/Assembly-CSharp.original.dll','recover-timer-dll.hdiff')]
    for item in config['files']:item['recoveries']=[]
    bindings=[]
    for item,translated,original,name in pairs:
        assert sha(translated) in [item['patched']]+item['legacy'] and sha(original)==item['original']
        subprocess.run([str(PROJECT.parents[1]/'Tools/HDiffPatch/windows64/hdiffz.exe'),'-f','-s-64',str(translated),str(original),str(PAYLOAD/name)],check=True,stdout=subprocess.DEVNULL)
        item['recoveries'].append({'source':sha(translated),'diff':name})
        bindings.append({'source_sha256':sha(translated),'recovered_sha256':sha(original),'diff':name,'diff_sha256':sha(PAYLOAD/name)})
    (PAYLOAD/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8-sig')
    entries=[{'path':f.relative_to(PROJECT).as_posix(),'game_path':f.name if f.suffix=='.cmd' else '汉化工具/'+f.name,'sha256':sha(f)} for f in sorted(PAYLOAD.iterdir()) if f.is_file()]
    (PROJECT/'TranslateFiles/reports/release_v16_payload.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    (PROJECT/'TranslateFiles/reports/release_v16_recovery_bindings.json').write_text(json.dumps(bindings,indent=2),encoding='utf-8')
    print('Prepared',len(entries),'payload files and',len(bindings),'verified reverse differences')

if __name__=='__main__':main()
