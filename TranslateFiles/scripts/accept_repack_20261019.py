"""Independent read-only acceptance of deployed text and the v1.3 patch archive."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
import uuid

PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT))
from build_localization import CUSTOM_CATEGORY_DIRS, build_key

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def rows(path):
    with path.open(encoding='utf-8-sig',newline='') as stream:
        data=list(csv.reader(stream))
    assert all(len(r)==1 for r in data)
    return [r[0] for r in data]

def collect(category,path):
    root=ET.parse(path).getroot()
    if category=='dialogue':return {e.get('id',''):e.text or '' for e in root.findall('Localize')}
    parents={c:p for p in root.iter() for c in p}
    result={}
    for element in root.iter():
        if element is root:continue
        if len(element)==0 and element.text and element.text.strip():
            result[build_key(root,element,parents)]=element.text
        elif element.tag in ('Male','Female'):
            for child in element:
                if child.text and child.text.strip():
                    result[f"{element.tag}/{element.get('id','')}/{child.tag}"]=child.text
    return result

def main():
    folder=PROJECT/'TranslateFiles/cache/accept_repack_20261019'/uuid.uuid4().hex[:12]
    folder.mkdir(parents=True,exist_ok=False)
    assets=PROJECT/'Game/Expeditions Viking_Data/resources.assets'
    original=PROJECT/'backup/resources.assets'
    official=PROJECT/'expeditions-viking_text_translated.csv'
    repack=PROJECT/'TranslateFiles/repack/translation_for_repack.csv'
    report={'deployed_sha256_before':sha(assets),'official_sha256':sha(official),
            'repack_sha256':sha(repack),'original_sha256':sha(original),'problems':[]}
    prep=json.loads((PROJECT/'TranslateFiles/reports/repack_translation_prep.json').read_text('utf-8'))
    assert report['official_sha256']==prep['official_sha256']
    assert report['repack_sha256']==prep['repack_sha256']
    src=rows(PROJECT/'expeditions-viking_text.csv');translated=rows(repack);approved=rows(official)
    with (PROJECT/'extracted_strings.csv').open(encoding='utf-8-sig',newline='') as stream:
        extracted=list(csv.DictReader(stream))
    assert len(src)==len(translated)==len(approved)==len(extracted)==23195
    assert all(r['原文']==s for r,s in zip(extracted,src))
    report['csv_records']=len(src)
    changed=[i for i,(a,b) in enumerate(zip(approved,translated)) if a!=b]
    semantic={e['index'] for k in ('restored','brace_fixes','overrides') for e in prep[k]}
    report['changed_records']=len(changed)
    report['semantic_changed_records']=len(semantic)
    report['visible_branch_records']=prep['player_variants']['records']
    tool=Path('D:/StaticHanHua/Tools/UABEA/UABEAvalonia/bin/Release/net8.0/UABEAvalonia.exe')
    ids={'dialogue':9146,'gui':9040,'homestead':9063,'input':9744,'items':9309,
         'names':9804,'scenedata':9795,'skills':9165,'tutorial':9799}
    found={};report['assets']=[]
    for category,dirname in CUSTOM_CATEGORY_DIRS.items():
        target=folder/f'{category}.xml'
        result=subprocess.run([str(tool),'exporttext',str(assets),str(ids[category]),str(target)],capture_output=True,timeout=60)
        assert result.returncode==0 and target.is_file(),category
        expected=PROJECT/f'Chinese_Localization/Chinese/Localization/{dirname}/{dirname}Chinese.xml'
        assert sha(target)==sha(expected),category
        found[category]=collect(category,target)
        report['assets'].append(dict(category=category,path_id=ids[category],sha256=sha(target),byte_identical=True))
    for index,(record,text) in enumerate(zip(extracted,translated)):
        if found[record['category']].get(record['key'])!=text:
            report['problems'].append(dict(index=index,kind='deployed_text_mismatch'))
    report['checked_records']=len(src)
    report['english_visible_branches']=sum(len(re.findall(r'\[Player:[^\]]*[A-Za-z][^\]]*/[^\]]*\]',s)) for s in translated)
    archive=next((PROJECT/'Dispatch').glob('*1.3.zip'))
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        manifest=json.loads(package.read('PATCH_MANIFEST.json').decode('utf-8'))
        report['archive_sha256']=sha(archive)
        report['archive_files']=package.namelist()
        for entry in manifest['files']:
            name=entry['path'];content=package.read(name)
            assert hashlib.sha256(content).hexdigest()==entry['sha256']
            assert len(content)==entry['size']
            assert sha(PROJECT/'ReleasePayload'/Path(name).name)==entry['sha256']
        report['archive_payload_hashes_verified']=True
    patched=folder/'resources.assets'
    result=subprocess.run([str(PROJECT/'ReleasePayload/hpatchz.exe'),str(original),
        str(PROJECT/'ReleasePayload/resources.assets.hdiff'),str(patched)],capture_output=True,timeout=60)
    assert result.returncode==0,'HDiffPatch failed'
    report['reconstructed_sha256']=sha(patched)
    assert report['reconstructed_sha256']==report['deployed_sha256_before']
    check=json.loads((PROJECT/'TranslateFiles/reports/in_game_check_manual_v13.json').read_text('utf-8'))
    assert check['translation_sha256']==report['official_sha256']
    for entry in check['payload_files']+check['evidence_files']:
        assert sha(PROJECT/entry['path'])==entry['sha256'],entry['path']
    report['in_game_evidence_hashes_verified']=True
    report['in_game_checks']=check['checks']
    report['deployed_sha256_after']=sha(assets)
    assert report['deployed_sha256_after']==report['deployed_sha256_before']
    report['technical_status']='passed' if not report['problems'] else 'failed'
    report['acceptance_status']='technical_pass_with_review_gap'
    report['limitations']=[
        '238 repack text changes are outside the formal CSV semantic review; existing release provenance is not independent semantic approval.',
        'Quest journal was not separately exercised in the recorded game test. Its not_applicable label means untested here, not that the game has no quests.',
        'This run verifies the differential payload reconstruction, not a fresh interactive game session or the complete batch installer UI.']
    destination=PROJECT/'TranslateFiles/reports/repack_acceptance_20261019.json'
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('technical_status','acceptance_status','checked_records','changed_records','semantic_changed_records','deployed_sha256_after')},ensure_ascii=True))

if __name__=='__main__':main()
