@echo off

cd /d "%~dp0"

title Net Novel Outline Agent

echo.
echo   ============================================
echo    Starting Net Novel Outline Agent
echo   ============================================
echo.
echo   Working dir: %CD%
echo.

rem ===== Step 1: detect a working Python 3 interpreter =====
set "PY_EXE="

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :have_python

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :have_py

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :have_python3

goto :no_python

:have_python
python -c "import sys" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :no_python
set "PY_EXE=python"
goto :py_ok

:have_py
py -3 -c "import sys" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :no_python
set "PY_EXE=py -3"
goto :py_ok

:have_python3
python3 -c "import sys" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :no_python
set "PY_EXE=python3"
goto :py_ok

:py_ok
echo   [OK] Found Python: %PY_EXE%
echo.

rem ===== Step 2: ensure flask and webview are installed =====
%PY_EXE% -c "import flask, webview" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :install_deps

goto :deps_ok

:install_deps
echo   [INFO] Missing flask / pywebview. Installing dependencies...
echo.
%PY_EXE% -m pip install --disable-pip-version-check -r requirements.txt
if %ERRORLEVEL% NEQ 0 goto :pip_fail

%PY_EXE% -c "import flask, webview" >nul 2>&1
if %ERRORLEVEL% NEQ 0 goto :dep_fail

:deps_ok
echo   [OK] Dependencies ready.
echo.

rem ===== Step 3: launch app =====
echo   Launching app.py ...
echo   (Close this window or Ctrl+C to stop)
echo   """
echo.

%PY_EXE% -u app.py
set "RC=%ERRORLEVEL%"

echo.
echo   """
if %RC% NEQ 0 (
    echo   [ERROR] app.py exited with code %RC%.
    echo   Scroll up to see the error message.
) else (
    echo   app.py exited normally.
)
echo.
pause
exit /b %RC%


:no_python
echo   [ERROR] Python 3.9+ was NOT found in PATH.
echo.
echo   Tried: python / py / python3
echo.
echo   Install Python from: https://www.python.org/downloads/
echo   IMPORTANT: tick "Add Python to PATH" during install.
echo.
echo   After installing, open a NEW cmd window and re-run this bat.
echo.
pause
exit /b 1


:pip_fail
echo.
echo   [ERROR] pip install failed.
echo   Try manually: %PY_EXE% -m pip install -r requirements.txt
echo.
pause
exit /b 1


:dep_fail
echo.
echo   [ERROR] Dependencies still missing after install.
echo   Try manually: %PY_EXE% -m pip install flask pywebview
echo.
pause
exit /b 1