@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_VERSION=V2.0.0"
set "SETUP_EXE=installer\output\SPPS_Planner_Setup_V2.0.0.exe"

call BUILD_EXE_ONLY.bat --no-pause
if errorlevel 1 exit /b 1

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
  pause
  exit /b 1
)

if exist "installer\output" rmdir /s /q "installer\output"
mkdir "installer\output"

"%ISCC%" "installer\SPPS_Planner_Setup.iss"
if errorlevel 1 (
  echo [ERROR] Installer compilation failed.
  pause
  exit /b 1
)

if not exist "%SETUP_EXE%" (
  echo [ERROR] Installer output was not found: %SETUP_EXE%
  pause
  exit /b 1
)

echo.
echo [OK] Installer created:
echo %CD%\%SETUP_EXE%
pause
exit /b 0
