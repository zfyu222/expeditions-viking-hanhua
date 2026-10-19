# 按玩家安装流程在临时目录完整还原 v1.3 补丁载荷并校验哈希
$ErrorActionPreference = 'Stop'
$root = 'C:\Temp\ev_install_test'
$zipCheck = 'C:\Temp\ev_zip_check'
$project = 'D:\StaticHanHua\Projects\Expeditions Viking'

if (Test-Path $root) { Remove-Item $root -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Join-Path $root 'Expeditions Viking_Data') | Out-Null
Copy-Item (Join-Path $project 'backup\resources.assets') (Join-Path $root 'Expeditions Viking_Data\resources.assets')
Copy-Item (Join-Path $zipCheck 'ZFY_Translation_Patch') (Join-Path $root 'ZFY_Translation_Patch') -Recurse

$bat = Join-Path $root 'ZFY_Translation_Patch\应用汉化补丁.bat'
$out = Join-Path $root 'install.log'
$p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$bat`" < NUL" -WorkingDirectory $root -NoNewWindow -Wait -PassThru -RedirectStandardOutput $out
Write-Output ("install_exit=" + $p.ExitCode)
Get-Content $out

$patched = (Get-FileHash (Join-Path $root 'Expeditions Viking_Data\resources.assets') -Algorithm SHA256).Hash
$expected = (Get-FileHash (Join-Path $project 'Game\Expeditions Viking_Data\resources.assets') -Algorithm SHA256).Hash
$backup = (Join-Path $root 'Expeditions Viking_Data\resources.assets.zfy.backup')
Write-Output ("patched=" + $patched)
Write-Output ("expected=" + $expected)
Write-Output ("match=" + ($patched -eq $expected))
Write-Output ("backup_exists=" + (Test-Path $backup))
if (Test-Path $backup) { Write-Output ("backup_hash_matches_original=" + ((Get-FileHash $backup -Algorithm SHA256).Hash -eq (Get-FileHash (Join-Path $project 'backup\resources.assets') -Algorithm SHA256).Hash)) }
Write-Output ("temp_left=" + (Test-Path (Join-Path $root 'Expeditions Viking_Data\resources.assets.zfy.tmp')))
