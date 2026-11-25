"""Rebuild the reviewed text and prepare the full v1.7 installer."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from build_v15 import PROJECT, sha

sys.path.insert(0, str(PROJECT))
from batch_replace_uabea import KNOWN_PATH_IDS, REPLACEMENTS, run_uabea
from build_localization import CATEGORY_DIRS, CATEGORY_FILES, LOCALIZATION_DIR

PAYLOAD = PROJECT / 'ReleasePayload/v1.7'
REPORTS = PROJECT / 'TranslateFiles/reports'
SCRIPTS = Path(__file__).resolve().parent


def main():
    cache = PROJECT / 'TranslateFiles/cache'
    cache.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='v17-build-', dir=cache))
    xml = work / 'Chinese_Localization'
    original = PROJECT / 'backup/resources.assets'
    assets = work / 'resources.assets'
    previous = PROJECT / 'ReleasePayload/v1.6'
    config = json.loads((previous / 'config.json').read_text(encoding='utf-8-sig'))
    text = config['files'][0]
    if sha(original) != text['original']:
        raise ValueError('Original resource hash does not match the supported Steam version')
    shutil.copy2(original, assets)

    # Verify the engine identifiers and source extraction before rewriting.
    for category, filename in CATEGORY_FILES.items():
        name = Path(filename).stem
        exported = work / filename
        stdout, stderr, code = run_uabea(['exporttext', str(assets), str(KNOWN_PATH_IDS[name]), str(exported)])
        expected = Path(LOCALIZATION_DIR) / CATEGORY_DIRS[category] / filename
        if (code or f'Exported TextAsset "{name}"' not in stdout
                or exported.read_text(encoding='utf-8-sig') != expected.read_text(encoding='utf-8-sig')):
            raise ValueError(f'Original TextAsset mismatch: {name} ({stderr})')

    def python(path, *args):
        subprocess.run([sys.executable, str(path), *map(str, args)], check=True, cwd=PROJECT)

    python(SCRIPTS / 'repack_prepare.py', '--variants')
    python(SCRIPTS / 'verify_repack_csv.py')
    csv_report = json.loads((REPORTS / 'repack_csv_verification.json').read_text(encoding='utf-8'))
    if any(csv_report[key] for key in (
            'tag_problem_count', 'player_tag_with_ascii_count', 'double_bracket_mismatch_count')):
        raise ValueError('Repack CSV failed protected text validation')
    python(PROJECT / 'build_localization.py', '--output', xml, '--report', REPORTS / 'v17_build_localization.json')
    python(SCRIPTS / 'verify_built_xml.py', '--output', xml, '--report', REPORTS / 'v17_build_xml_verification.json')
    xml_report = json.loads((REPORTS / 'v17_build_xml_verification.json').read_text(encoding='utf-8'))
    build_report = json.loads((REPORTS / 'v17_build_localization.json').read_text(encoding='utf-8'))
    if (set(xml_report['categories']) != set(CATEGORY_FILES)
            or build_report['total_written'] != csv_report['rows']):
        raise ValueError('Generated XML does not cover every translation record')

    for name, relative in REPLACEMENTS.items():
        chinese = xml / 'Chinese/Localization' / relative
        stdout, stderr, code = run_uabea(['importtext', str(assets), str(KNOWN_PATH_IDS[name]), str(chinese)])
        if code or 'Imported' not in stdout:
            raise ValueError(f'Import failed: {name} ({stderr})')

    verified = {}
    for name, relative in REPLACEMENTS.items():
        chinese = xml / 'Chinese/Localization' / relative
        pid = KNOWN_PATH_IDS[name]
        exported = work / f'verified-{pid}.txt'
        stdout, stderr, code = run_uabea(['exporttext', str(assets), str(pid), str(exported)])
        if code or f'Exported TextAsset "{name}"' not in stdout or sha(exported) != sha(chinese):
            raise ValueError(f'Reimport validation failed: {name} ({stderr})')
        verified[name] = {'path_id': pid, 'xml_sha256': sha(chinese)}

    PAYLOAD.mkdir(exist_ok=True)
    for file in previous.iterdir():
        if file.is_file() and file.name not in {'config.json', text['diff']}:
            shutil.copy2(file, PAYLOAD / file.name)
    hdiff = PROJECT.parents[1] / 'Tools/HDiffPatch/windows64/hdiffz.exe'
    reverse = 'recover-v17-resources.hdiff'
    for source, target, delta in ((original, assets, text['diff']), (assets, original, reverse)):
        subprocess.run([str(hdiff), '-f', '-s-64', str(source), str(target), str(PAYLOAD / delta)], check=True)
    text['legacy'] = [text['patched'], *text['legacy']]
    text['patched'] = sha(assets)
    text['recoveries'].append({'source': text['patched'], 'diff': reverse})
    config['version'] = '1.7'
    (PAYLOAD / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8-sig')
    entries = [
        {'path': file.relative_to(PROJECT).as_posix(),
         'game_path': file.name if file.suffix == '.cmd' else '汉化工具/' + file.name,
         'sha256': sha(file)}
        for file in sorted(PAYLOAD.iterdir()) if file.is_file()
    ]
    report = {
        'status': 'passed', 'records': csv_report['rows'],
        'official_sha256': sha(PROJECT / 'expeditions-viking_text_translated.csv'),
        'resources_sha256': text['patched'], 'original_resources_sha256': text['original'],
        'assets': str(assets), 'text_assets': verified, 'payload_files': entries,
    }
    (REPORTS / 'release_v17_repack.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Validated {len(verified)} TextAssets. Repack report: {REPORTS / "release_v17_repack.json"}')


if __name__ == '__main__':
    main()
