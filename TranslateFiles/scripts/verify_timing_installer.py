"""Exercise the shipped PowerShell installer on isolated DLL copies."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
PAYLOAD = PROJECT / 'Dispatch/OverheadTimingFix'
ORIGINAL = PROJECT / 'Analysis/overhead_timing/Assembly-CSharp.original.dll'
PATCHED = PROJECT / 'Analysis/overhead_timing/Assembly-CSharp.fixed.dll'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    root = Path(tempfile.mkdtemp(prefix='timing fix ', dir=PROJECT/'TranslateFiles/cache'))
    target = root/'Expeditions Viking_Data/Managed/Assembly-CSharp.dll'
    target.parent.mkdir(parents=True)
    shutil.copy2(ORIGINAL, target)
    def run(script=PAYLOAD/'Apply-TimingFix.ps1', uninstall=False, success=True):
        args = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script), '-GameRoot', str(root)]
        if uninstall:
            args.append('-Uninstall')
        result = subprocess.run(args, capture_output=True, timeout=60)
        assert (result.returncode == 0) == success, result.stdout.decode(errors='replace')+result.stderr.decode(errors='replace')
    run()
    assert digest(target) == digest(PATCHED)
    assert digest(Path(str(target)+'.zfy-timing.backup')) == digest(ORIGINAL)
    run()  # Idempotent install.
    run(uninstall=True)
    assert digest(target) == digest(ORIGINAL)
    run(uninstall=True)
    target.write_bytes(b'unsupported version')
    run(success=False)
    assert target.read_bytes() == b'unsupported version'
    shutil.copy2(ORIGINAL, target)
    broken = root/'corrupt payload'
    shutil.copytree(PAYLOAD, broken)
    (broken/'overhead-timing.hdiff').write_bytes(b'broken diff')
    run(script=broken/'Apply-TimingFix.ps1', success=False)
    assert digest(target) == digest(ORIGINAL)
    assert not list(target.parent.glob('*.tmp'))
    report = dict(status='passed', checks=['install', 'repeat_install', 'uninstall', 'repeat_uninstall', 'wrong_version_refused', 'corrupt_patch_original_unchanged'], original_sha256=digest(ORIGINAL), patched_sha256=digest(PATCHED), fixture=str(root), new_in_game_test=False)
    (PROJECT/'TranslateFiles/reports/overhead_timing_installer.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
