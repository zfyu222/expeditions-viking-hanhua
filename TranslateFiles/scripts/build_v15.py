"""Prepare one full v1.5 distribution with both text and timer diffs."""
from pathlib import Path
import hashlib
import json
import shutil

PROJECT=Path(__file__).resolve().parents[2]
PAYLOAD=PROJECT/'ReleasePayload/v1.5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    PAYLOAD.mkdir(parents=True,exist_ok=True)
    for source,name in [(PROJECT/'ReleasePayload/resources.assets.hdiff','resources.assets.hdiff'),
                        (PROJECT/'ReleasePayload/hpatchz.exe','hpatchz.exe'),
                        (PROJECT/'Dispatch/OverheadTimingFix/overhead-timing.hdiff','overhead-timing.hdiff'),
                        (PROJECT/'TranslateFiles/scripts/InstallV15.ps1','install.ps1')]:
        shutil.copy2(source,PAYLOAD/name)
    config={'version':'1.5','launch_mode':'original_exe','files':[
        {'path':'Expeditions Viking_Data/resources.assets','diff':'resources.assets.hdiff',
         'original':'5ffb6e099860f06e325ffefd1784a074bf50c01074f856272c2d9084c3e9eba8',
         'patched':'307cb72ef9b5d1cc34dc2755ec226bdd72e49e154b940354195fd00f2aa3009b',
         'legacy':['0c07814ce8ace8232e1b7fd8be69f2c44eeac58447ed9d29ddb25901efde92d3'],
         'backup_suffix':'.zfy.backup'},
        {'path':'Expeditions Viking_Data/Managed/Assembly-CSharp.dll','diff':'overhead-timing.hdiff',
         'original':'c7b37f617f2e4561b939f02aebba5841ee87c554d8c5f43bf18887d362106af5',
         'patched':'456812cc062145b3958bb234c265e4d0d91713b0f1025836ef4d6d90da16b203',
         'legacy':[],'backup_suffix':'.zfy-timing.backup'}]}
    (PAYLOAD/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8-sig')
    for action,title in [('install','安装汉化'),('uninstall','卸载汉化')]:
        text='@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0汉化工具\\install.ps1" -Action '+action+'\r\nset "ZFY_RESULT=%errorlevel%"\r\npause\r\nexit /b %ZFY_RESULT%\r\n'
        # UTF-8 command files use the console UTF-8 page before the Chinese path.
        text=text.replace('@echo off\r\n','@echo off\r\nchcp 65001 >nul\r\n')
        (PAYLOAD/(title+'.cmd')).write_bytes(text.encode('utf-8'))
    entries=[]
    for f in sorted(PAYLOAD.iterdir()):
        destination=f.name if f.suffix=='.cmd' else '汉化工具/'+f.name
        entries.append({'path':f.relative_to(PROJECT).as_posix(),'game_path':destination,'sha256':sha(f)})
    (PROJECT/'TranslateFiles/reports/release_v15_payload.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared',len(entries),'files')

if __name__=='__main__':main()
