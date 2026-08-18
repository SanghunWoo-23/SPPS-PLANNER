@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_VERSION=V4.0.0"
set "SETUP_EXE=installer\output\SPPS_Planner_Setup_V4.0.0.exe"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

echo [1/3] Building and validating portable EXE...
call BUILD_EXE_ONLY.bat --no-pause
if errorlevel 1 (
  echo [ERROR] Portable EXE stage failed. See the specific BUILD_EXE_ONLY error above.
  exit /b 1
)

set "ISCC="
where ISCC.exe >nul 2>nul && set "ISCC=ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"

if not defined ISCC (
  echo [ERROR] Inno Setup Compiler was not found.
  echo Install Inno Setup 6 or 7, then run this file again.
  echo The portable EXE is available at dist\SPPS_Planner\SPPS_Planner.exe
  if "%NO_PAUSE%"=="0" pause
  exit /b 1
)

if exist "installer\output" rmdir /s /q "installer\output"
mkdir "installer\output"

echo [2/3] Compiling Inno Setup installer...
"%ISCC%" "installer\SPPS_Planner_Setup.iss"
if errorlevel 1 (
  echo [ERROR] Installer compilation failed.
  if "%NO_PAUSE%"=="0" pause
  exit /b 1
)

if not exist "%SETUP_EXE%" (
  echo [ERROR] Installer output was not found: %SETUP_EXE%
  if "%NO_PAUSE%"=="0" pause
  exit /b 1
)
set "VERIFY_PY="
py -3.11 --version >nul 2>nul && set "VERIFY_PY=py -3.11"
if not defined VERIFY_PY py -3.12 --version >nul 2>nul && set "VERIFY_PY=py -3.12"
if not defined VERIFY_PY set "VERIFY_PY=python"
echo [3/3] Verifying EXE and installer outputs...
%VERIFY_PY% tools\verify_windows_release.py --check-exe --check-installer
if errorlevel 1 (
  echo [ERROR] Final EXE/installer verification failed.
  if "%NO_PAUSE%"=="0" pause
  exit /b 1
)

echo.
echo [OK] Installer created:
echo %CD%\%SETUP_EXE%
if "%NO_PAUSE%"=="0" pause
exit /b 0
