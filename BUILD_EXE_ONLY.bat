@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_VERSION=V3.0.0"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
set "PY_CMD="

py -3.11 --version >nul 2>nul && set "PY_CMD=py -3.11"
if not defined PY_CMD py -3.12 --version >nul 2>nul && set "PY_CMD=py -3.12"
if not defined PY_CMD py -3 --version >nul 2>nul && set "PY_CMD=py -3"
if not defined PY_CMD python --version >nul 2>nul && set "PY_CMD=python"
if not defined PY_CMD (
  echo [ERROR] Python 3.11 or 3.12 was not found.
  echo Install 64-bit Python, enable the Python launcher, then run this file again.
  goto :fail
)

if not exist "main_launcher.py" goto :missing
if not exist "SPPS_Planner.spec" goto :missing
if not exist "apps\spps_planner_app\spps_planner\engine.py" goto :missing
if not exist "assets\SPPS_Planner_Icon.ico" goto :missing

echo ============================================================
echo SPPS Planner %APP_VERSION% EXE build
echo ============================================================
%PY_CMD% --version
%PY_CMD% -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
%PY_CMD% -m pip install -r requirements.txt
if errorlevel 1 goto :fail
%PY_CMD% -m compileall -q main_launcher.py suite_gui peptiforg_core apps\spps_planner_app\spps_planner
if errorlevel 1 goto :fail
%PY_CMD% tools\verify_windows_release.py
if errorlevel 1 goto :fail

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
%PY_CMD% -m PyInstaller --clean --noconfirm SPPS_Planner.spec
if errorlevel 1 goto :fail

if not exist "dist\SPPS_Planner\SPPS_Planner.exe" (
  echo [ERROR] PyInstaller completed without the expected EXE.
  goto :fail
)
%PY_CMD% tools\verify_windows_release.py --check-exe
if errorlevel 1 goto :fail
set "SPPS_PLANNER_SELFTEST_OUTPUT=%CD%\dist\SPPS_Planner\runtime_selftest.json"
if exist "%SPPS_PLANNER_SELFTEST_OUTPUT%" del /q "%SPPS_PLANNER_SELFTEST_OUTPUT%"
"%CD%\dist\SPPS_Planner\SPPS_Planner.exe" --self-test
if errorlevel 1 goto :fail
if not exist "%SPPS_PLANNER_SELFTEST_OUTPUT%" goto :selftest_missing
%PY_CMD% tools\verify_packaged_runtime.py "%SPPS_PLANNER_SELFTEST_OUTPUT%"
if errorlevel 1 goto :fail

echo.
echo [OK] EXE created:
echo %CD%\dist\SPPS_Planner\SPPS_Planner.exe
if "%NO_PAUSE%"=="0" pause
exit /b 0

:missing
echo [ERROR] A required project file is missing. Extract the complete ZIP first.
goto :fail

:selftest_missing
echo [ERROR] The packaged EXE did not create its functional self-test report.
goto :fail

:fail
echo [ERROR] EXE build failed. Review the error above.
if "%NO_PAUSE%"=="0" pause
exit /b 1
