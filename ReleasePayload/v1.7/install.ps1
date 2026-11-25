param([ValidateSet('install','uninstall')][string]$Action='install', [string]$GameRoot=(Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
function Hash([string]$p) {
    $s=[IO.File]::OpenRead($p); $h=[Security.Cryptography.SHA256]::Create()
    try { [BitConverter]::ToString($h.ComputeHash($s)).Replace('-','').ToLowerInvariant() }
    finally { $s.Dispose(); $h.Dispose() }
}
$work=$null; $changed=@(); $success=$false
try {
    if(Get-Process -Name 'Expeditions Viking' -ErrorAction SilentlyContinue){throw 'Close the game first.'}
    $config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json
    $plan=@(); $recoveries=@()
    # Validate every input and original backup before touching any target.
    foreach($item in $config.files){
        $target=Join-Path $GameRoot $item.path; $backup=$target+$item.backup_suffix
        $current=Hash $target
        if($current -ne $item.original -and $current -ne $item.patched -and $current -notin $item.legacy){throw ('Unsupported file: '+$item.path)}
        if(Test-Path -LiteralPath $backup){
            if((Hash $backup) -ne $item.original){throw ('Invalid original backup: '+$item.path)}
        } elseif($current -ne $item.original){
            $recovery=$item.recoveries | Where-Object {$_.source -eq $current} | Select-Object -First 1
            if(!$recovery){throw ('No supported backup recovery for: '+$item.path)}
            $recoveries+=@{item=$item;target=$target;backup=$backup;recovery=$recovery}
        }
        $wanted=if($Action -eq 'install'){$item.patched}else{$item.original}
        if($current -ne $wanted){$plan+=@{item=$item;target=$target;backup=$backup;current=$current;wanted=$wanted}}
    }
    if($plan.Count -eq 0 -and $recoveries.Count -eq 0){Write-Host 'Already up to date.'; exit 0}
    $work=Join-Path $GameRoot ('.zfy-v16-'+[Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $work | Out-Null
    # Recover only exact known releases, using verified reverse diffs. Do not
    # mistake a translated file for an original, or download game resources.
    $recoveryIndex=0
    foreach($step in $recoveries){
        $step.output=Join-Path $work ('recovered-'+$recoveryIndex.ToString());$recoveryIndex++
        & (Join-Path $PSScriptRoot 'hpatchz.exe') $step.target (Join-Path $PSScriptRoot $step.recovery.diff) $step.output
        if($LASTEXITCODE -ne 0 -or (Hash $step.output) -ne $step.item.original){throw 'Original recovery failed; no game files changed.'}
    }
    foreach($step in $recoveries){Copy-Item -LiteralPath $step.output -Destination $step.backup}
    $index=0
    foreach($step in $plan){
        if(!(Test-Path -LiteralPath $step.backup)){
            Copy-Item -LiteralPath $step.target -Destination $step.backup
            if((Hash $step.backup) -ne $step.item.original){throw 'Backup verification failed.'}
        }
        $step.before=Join-Path $work ($index.ToString()+'.before')
        $step.output=Join-Path $work ($index.ToString()+'.after'); $index++
        Copy-Item -LiteralPath $step.target -Destination $step.before
        if($Action -eq 'install'){
            & (Join-Path $PSScriptRoot 'hpatchz.exe') $step.backup (Join-Path $PSScriptRoot $step.item.diff) $step.output
            if($LASTEXITCODE -ne 0){throw 'Patch generation failed; no game files changed.'}
        }else{Copy-Item -LiteralPath $step.backup -Destination $step.output}
        if((Hash $step.output) -ne $step.wanted){throw 'Output verification failed; no game files changed.'}
    }
    foreach($step in $plan){
        $changed+=,$step
        Copy-Item -LiteralPath $step.output -Destination $step.target -Force
        if((Hash $step.target) -ne $step.wanted){throw 'Installed file verification failed.'}
    }
    $success=$true
    Write-Host ('Done: '+$Action+'. Select English in the game language settings.')
}catch{
    $message=$_.Exception.Message
    foreach($step in $changed){
        try {
            Copy-Item -LiteralPath $step.before -Destination $step.target -Force
            if((Hash $step.target) -ne $step.current){throw 'Rollback hash mismatch'}
        }catch{Write-Host ('Restore failed. Recovery copy: '+$step.before); $work=$null}
    }
    Write-Host ('ERROR: '+$message)
}finally{
    if($work -and (Test-Path -LiteralPath $work)){
        # Delete only files created in our unique workspace, never recurse over the game.
        Get-ChildItem -LiteralPath $work -File | ForEach-Object {Remove-Item -LiteralPath $_.FullName}
        Remove-Item -LiteralPath $work
    }
}
if(!$success){exit 1}
exit 0
