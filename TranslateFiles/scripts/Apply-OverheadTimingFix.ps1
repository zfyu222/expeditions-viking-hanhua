param([string]$GameRoot = (Split-Path $PSScriptRoot -Parent), [switch]$Uninstall)
$ErrorActionPreference = 'Stop'
try {
    $original = 'c7b37f617f2e4561b939f02aebba5841ee87c554d8c5f43bf18887d362106af5'
    $patched = '456812cc062145b3958bb234c265e4d0d91713b0f1025836ef4d6d90da16b203'
    $target = Join-Path $GameRoot 'Expeditions Viking_Data/Managed/Assembly-CSharp.dll'
    $backup = $target + '.zfy-timing.backup'
    function Hash([string]$p) {
        $stream = [IO.File]::OpenRead($p)
        $algorithm = [Security.Cryptography.SHA256]::Create()
        try { [BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '').ToLowerInvariant() }
        finally { $stream.Dispose(); $algorithm.Dispose() }
    }
    if (Get-Process -Name 'Expeditions Viking' -ErrorAction SilentlyContinue) { throw 'Close the game first.' }
    $current = Hash $target
    if ($Uninstall) {
        if ($current -eq $original) { Write-Host 'Already restored.'; exit 0 }
        if ($current -ne $patched -or (Hash $backup) -ne $original) { throw 'Unsupported DLL or invalid backup. Nothing changed.' }
        Copy-Item -LiteralPath $backup -Destination $target -Force
        if ((Hash $target) -ne $original) { throw 'Restore verification failed.' }
        Write-Host 'Timing fix removed.'; exit 0
    }
    if ($current -eq $patched) { Write-Host 'Timing fix already installed.'; exit 0 }
    if ($current -ne $original) { throw 'Unsupported DLL version or another code mod. Nothing changed.' }
    if (Test-Path -LiteralPath $backup) {
        if ((Hash $backup) -ne $original) { throw 'Existing backup is invalid. Nothing changed.' }
    } else {
        Copy-Item -LiteralPath $target -Destination $backup
        if ((Hash $backup) -ne $original) { throw 'Backup verification failed.' }
    }
    $temporary = $target + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    try {
        & (Join-Path $PSScriptRoot 'hpatchz.exe') $target (Join-Path $PSScriptRoot 'overhead-timing.hdiff') $temporary
        if ($LASTEXITCODE -ne 0) { throw 'Patch failed. Original DLL is unchanged.' }
        if ((Hash $temporary) -ne $patched) { throw 'Patched DLL verification failed. Original DLL is unchanged.' }
        [IO.File]::Replace($temporary, $target, $backup)
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
    }
    Write-Host 'Timing fix installed.'
    exit 0
} catch { Write-Host ('ERROR: ' + $_.Exception.Message); exit 1 }
