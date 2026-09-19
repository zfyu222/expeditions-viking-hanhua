@echo off
setlocal EnableExtensions

set "PATCH_DIR=%~dp0"
set "GAME_ROOT=%~dp0.."
set "DATA_DIR=%GAME_ROOT%\Expeditions Viking_Data"
set "SOURCE=%DATA_DIR%\resources.assets"
set "BACKUP=%DATA_DIR%\resources.assets.zfy.backup"
set "TEMP=%DATA_DIR%\resources.assets.zfy.tmp"

if not exist "%SOURCE%" (
  echo ERROR: resources.assets was not found.
  echo Extract the ZFY_Translation_Patch folder into the game root, then run this script again.
  pause
  exit /b 1
)
if exist "%BACKUP%" (
  echo ERROR: A backup already exists: %BACKUP%
  echo Restore it manually before reinstalling this patch.
  pause
  exit /b 1
)

echo Backing up original resources.assets...
copy /y "%SOURCE%" "%BACKUP%" >nul || goto :failed
echo Applying translation patch...
"%PATCH_DIR%hpatchz.exe" "%SOURCE%" "%PATCH_DIR%resources.assets.hdiff" "%TEMP%"
if errorlevel 1 goto :restore

move /y "%TEMP%" "%SOURCE%" >nul || goto :restore
echo Done. Start the game and select English in its language settings.
pause
exit /b 0

:restore
echo ERROR: Patch failed. The game version may not be supported or resources.assets was modified.
if exist "%TEMP%" del /q "%TEMP%"
if exist "%BACKUP%" move /y "%BACKUP%" "%SOURCE%" >nul
echo Original resources.assets was restored.
pause
exit /b 1

:failed
echo ERROR: Unable to create a backup. Close the game and check folder permissions.
pause
exit /b 1
