@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo SPPS Planner V3.0.0 - install build tools and build installer
echo ============================================================

set "PY_CMD="
py -3.11 --version >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD py -3.12 --version >nul 2>nul && set "PY_CMD=py -3.12"
if not defined PY_CMD (
  where winget.exe >nul 2>nul
  if errorlevel 1 goto :no_winget
  echo [1/4] Installing 64-bit Python 3.12 for the current user...
  winget install --id Python.Python.3.12 --exact --scope user --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :fail
  set "PY_CMD=py -3.12"
)

echo [2/4] Installing Python build requirements...
%PY_CMD% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
%PY_CMD% -m pip install -r requirements.txt -r requirements-dev.txt
if errorlevel 1 goto :fail

where ISCC.exe >nul 2>nul
if errorlevel 1 if not exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" if not exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" if not exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
  where winget.exe >nul 2>nul
  if errorlevel 1 goto :no_winget
  echo [3/4] Installing Inno Setup...
  winget install --id JRSoftware.InnoSetup --exact --scope user --accept-package-agreements --accept-source-agreements
  if errorlevel 1 goto :fail
)

echo [4/4] Verifying source and building EXE plus installer...
%PY_CMD% tools\verify_windows_release.py
if errorlevel 1 goto :fail
call BUILD_INSTALLER.bat --no-pause
if errorlevel 1 goto :fail

echo.
echo [OK] Complete Windows installer build finished.
echo %CD%\installer\output\SPPS_Planner_Setup_V3.0.0.exe
pause
exit /b 0

:no_winget
echo [ERROR] Python or Inno Setup is missing and winget is unavailable.
echo Install Python 3.11/3.12 and Inno Setup 6/7, then run this file again.
goto :fail

:fail
echo [ERROR] Installation or build failed. Review the first error above.
pause
exit /b 1
