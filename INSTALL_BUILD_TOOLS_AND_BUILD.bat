@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo SPPS planner V1.0.0 Native UI One-Click Build
echo ============================================================
echo.

set "PY_CMD="
py -3.11 --version >nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3.11"
if "%PY_CMD%"=="" (
  py -3.12 --version >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3.12"
)
if "%PY_CMD%"=="" (
  py -3 --version >nul 2>&1
  if not errorlevel 1 set "PY_CMD=py -3"
)
if "%PY_CMD%"=="" (
  python --version >nul 2>&1
  if not errorlevel 1 set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
  echo [ERROR] Python was not found.
  pause
  exit /b 1
)

echo [INFO] Python: %PY_CMD%
%PY_CMD% --version

echo.
echo ============================================================
echo [1/4] Installing packages
echo ============================================================
%PY_CMD% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :pipfail
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :pipfail
%PY_CMD% -c "import tkinter, pandas, openpyxl, numpy; print('Required modules OK')"
if errorlevel 1 goto :pipfail

echo.
echo ============================================================
echo [2/4] Building native UI EXE
echo ============================================================
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist installer\installer_output rmdir /s /q installer\installer_output

%PY_CMD% -m PyInstaller --clean --noconfirm --onedir --windowed --name SPPS_Planner ^
  --paths "apps\spps_planner_app" ^
  --icon "assets\SPPS_Planner_Icon.ico" ^
  --add-data "apps;apps" ^
  --add-data "suite_gui;suite_gui" ^
  --add-data "peptiforg_core;peptiforg_core" ^
  --add-data "assets;assets" ^
  --add-data "docs;docs" ^
  --add-data "VERSION.txt;." ^
  --collect-all pandas ^
  --collect-all numpy ^
  --collect-all openpyxl ^
  --collect-all sklearn ^
  --collect-all joblib ^
  --hidden-import suite_gui.spps_tk_gui ^
  --hidden-import peptiforg_core.ui_helpers ^
  --hidden-import spps_planner.engine ^
  --hidden-import spps_planner.parser ^
  --hidden-import spps_planner.export ^
  --hidden-import spps_planner.database ^
  --hidden-import tkinter ^
  --hidden-import tkinter.ttk ^
  --hidden-import tkinter.filedialog ^
  --hidden-import tkinter.messagebox ^
  main_launcher.py

if errorlevel 1 (
  echo [ERROR] EXE build failed.
  pause
  exit /b 1
)

if not exist "dist\SPPS_Planner\SPPS_Planner.exe" (
  echo [ERROR] EXE was not created at dist\SPPS_Planner\SPPS_Planner.exe
  pause
  exit /b 1
)

echo.
echo ============================================================
echo [3/4] Checking Inno Setup 7/6
echo ============================================================
set "ISCC="
where ISCC.exe >nul 2>nul
if not errorlevel 1 set "ISCC=ISCC.exe"
if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
  winget --version >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] Install Inno Setup 7 or 6 and run again.
    pause
    exit /b 2
  )
  winget install --id JRSoftware.InnoSetup -e --accept-package-agreements --accept-source-agreements
)

set "ISCC="
where ISCC.exe >nul 2>nul
if not errorlevel 1 set "ISCC=ISCC.exe"
if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 7\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
  echo [ERROR] Inno Setup compiler was not found.
  pause
  exit /b 2
)

echo.
echo ============================================================
echo [4/4] Building installer
echo ============================================================

rem Inno Setup can fail when the project is stored under a long Windows path.
rem Map the project root to a temporary drive letter for the compile only.
set "BUILD_DRIVE="
for %%D in (S R Q P O N M L K J) do (
  if not exist "%%D:\" if "!BUILD_DRIVE!"=="" set "BUILD_DRIVE=%%D:"
)
if "!BUILD_DRIVE!"=="" (
  echo [ERROR] No free drive letter was found for the short build path.
  pause
  exit /b 1
)

subst !BUILD_DRIVE! "%CD%"
if errorlevel 1 (
  echo [ERROR] Could not create the short build path.
  pause
  exit /b 1
)

"%ISCC%" "!BUILD_DRIVE!\installer\SPPS_Planner_Setup.iss"
set "ISCC_EXIT=!ERRORLEVEL!"
subst !BUILD_DRIVE! /d >nul 2>&1

if not "!ISCC_EXIT!"=="0" (
  echo [ERROR] Installer build failed.
  pause
  exit /b 1
)

if not exist "installer\installer_output\SPPS planner V1.0.0.exe" (
  echo [ERROR] Installer was not created.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo DONE
echo EXE:       dist\SPPS_Planner\SPPS_Planner.exe
echo Installer: installer\installer_output\SPPS planner V1.0.0.exe
echo ============================================================
pause
exit /b 0

:pipfail
echo [ERROR] Package install failed.
pause
exit /b 1
