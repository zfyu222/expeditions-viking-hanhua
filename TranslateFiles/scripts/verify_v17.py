"""Replay the full installer on isolated original and upgraded Steam files."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

from build_v17 import PAYLOAD, PROJECT, REPORTS, sha


def main():
    with tempfile.TemporaryDirectory(prefix='v17 汉化 ', dir=PROJECT / 'TranslateFiles/cache') as temp:
        root = Path(temp)
        tools = root / '汉化工具'
        archive_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else None
        build = json.loads((REPORTS / 'release_v17_repack.json').read_text(encoding='utf-8'))
        if archive_path:
            with zipfile.ZipFile(archive_path) as archive:
                assert archive.testzip() is None
                manifest = json.loads(archive.read('PATCH_MANIFEST.json'))
                entries = {item['archive_path']: item['sha256'] for item in manifest['files']}
                assert entries == {item['game_path']: item['sha256'] for item in build['payload_files']}
                assert set(archive.namelist()) == set(entries) | {'PATCH_MANIFEST.json', 'SHA256SUMS.txt', '补丁说明.txt'}
                sums = archive.read('SHA256SUMS.txt').decode('utf-8').splitlines()
                assert sorted(sums) == sorted(f'{digest}  {name}' for name, digest in entries.items())
                for name, digest in entries.items():
                    assert hashlib.sha256(archive.read(name)).hexdigest() == digest
                assert all(f'v1.{version}' in archive.read('补丁说明.txt').decode('utf-8-sig') for version in range(2, 8))
                archive.extractall(root)
        else:
            tools.mkdir()
            for item in build['payload_files']:
                shutil.copyfile(PROJECT / item['path'], root / item['game_path'])

        config = json.loads((tools / 'config.json').read_text(encoding='utf-8-sig'))
        a, d = config['files']
        assets, dll = root / a['path'], root / d['path']
        dll.parent.mkdir(parents=True)
        backups = [Path(str(target) + entry['backup_suffix'])
                   for target, entry in zip((assets, dll), config['files'])]
        originals = (PROJECT / 'backup/resources.assets',
                     PROJECT / 'Analysis/overhead_timing/Assembly-CSharp.original.dll')
        targets = (assets, dll)
        checks = []

        def run(action='install', expected=0):
            if archive_path:
                name = '安装汉化.cmd' if action == 'install' else '卸载汉化.cmd'
                command = ['cmd.exe', '/d', '/c', 'call', str(root / name)]
            else:
                command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                           '-File', str(tools / 'install.ps1'), '-Action', action]
            result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, timeout=150)
            assert result.returncode == expected, result.stdout.decode(errors='replace')

        def verify(which):
            assert [sha(target) for target in targets] == [entry[which] for entry in config['files']]

        for original, target in zip(originals, targets):
            shutil.copy2(original, target)
        run()
        verify('patched')
        assert [sha(path) for path in backups] == [a['original'], d['original']]
        checks.append('fresh_install_and_original_backups')
        run()
        verify('patched')
        checks.append('idempotent_install')
        run('uninstall')
        verify('original')
        run('uninstall')
        checks.append('uninstall_and_idempotent_uninstall')

        previous = PROJECT / 'ReleasePayload/v1.6'
        legacy = root / 'legacy.resources.assets'
        subprocess.run([str(tools / 'hpatchz.exe'), str(originals[0]),
                        str(previous / a['diff']), str(legacy)], check=True, stdout=subprocess.DEVNULL)
        assert sha(legacy) == a['legacy'][0]
        shutil.copy2(legacy, assets)
        run()
        verify('patched')
        checks.append('v16_upgrade_with_original_backup')
        for path in backups:
            path.unlink()
        shutil.copy2(legacy, assets)
        run()
        verify('patched')
        assert [sha(path) for path in backups] == [a['original'], d['original']]
        checks.append('v16_upgrade_with_no_original_backups')
        for path in backups:
            path.unlink()
        run()
        assert [sha(path) for path in backups] == [a['original'], d['original']]
        run('uninstall')
        verify('original')
        checks.append('v17_recovers_both_missing_backups_and_uninstalls')

        dll.write_bytes(b'wrong assembly')
        run(expected=1)
        assert sha(assets) == a['original'] and dll.read_bytes() == b'wrong assembly'
        checks.append('unsupported_second_input_leaves_first_untouched')
        shutil.copy2(originals[1], dll)
        (tools / d['diff']).write_bytes(b'corrupt diff')
        run(expected=1)
        verify('original')
        checks.append('corrupt_second_delta_leaves_both_originals')

    report = {'status': 'passed', 'version': '1.7', 'checks': checks,
              'official_sha256': build['official_sha256'],
              'resources_sha256': a['patched'], 'dll_sha256': d['patched']}
    filename = 'release_v17_install_validation.json'
    if archive_path:
        report['archive_sha256'] = sha(archive_path)
        report['archive_crc_and_manifest'] = 'passed'
        filename = 'release_v17_archive_validation.json'
    (REPORTS / filename).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
