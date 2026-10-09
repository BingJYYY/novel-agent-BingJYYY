@echo off

cd /d "%~dp0"

title Diagnose

echo.
echo   ============================================
echo    Environment Diagnostic
echo   ============================================
echo.

echo   Working dir: %CD%
echo.

echo   --- Python check ---
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   py launcher: OK
    py -3 -V
) else (
    echo   py launcher: NOT FOUND
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   python: OK
    python -V
) else (
    echo   python: NOT FOUND
)

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   python3: OK
    python3 -V
) else (
    echo   python3: NOT FOUND
)

echo.
echo   --- pip check ---
py -3 -m pip --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   pip: OK
    py -3 -m pip --version
) else (
    python -m pip --version >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   pip: OK
        python -m pip --version
    ) else (
        echo   pip: NOT FOUND
    )
)

echo.
echo   --- Python dependencies ---

py -3 -c "import flask; print('flask:    OK (version', flask.__version__, ')')" 2>nul
if errorlevel 1 (
    echo   flask:    MISSING
)

py -3 -c "import webview; print('pywebview: OK (version', webview.__version__, ')')" 2>nul
if errorlevel 1 (
    echo   pywebview: MISSING
)

py -3 -c "import langchain_openai; print('langchain_openai: OK')" 2>nul
if errorlevel 1 (
    echo   langchain_openai: MISSING
)

py -3 -c "import yaml; print('pyyaml:   OK')" 2>nul
if errorlevel 1 (
    echo   pyyaml:   MISSING
)

py -3 -c "import sqlalchemy; print('sqlalchemy: OK (version', sqlalchemy.__version__, ')')" 2>nul
if errorlevel 1 (
    echo   sqlalchemy: MISSING
)

echo.
echo   --- WebView2 runtime (needed by pywebview) ---

reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   WebView2 Runtime: INSTALLED
) else (
    reg query "HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo   WebView2 Runtime: INSTALLED
    ) else (
        echo   WebView2 Runtime: NOT FOUND
        echo     (pywebview needs Edge WebView2 runtime; install from
        echo      https://developer.microsoft.com/microsoft-edge/webview2/)
    )
)

echo.
echo   --- Sanity: try importing app.py ---
python -c "import sys; sys.path.insert(0, '.'); import app" 2>nul
if errorlevel 1 (
    echo   app.py import: FAILED
    echo   Full traceback:
    python -c "import sys; sys.path.insert(0, '.'); import app" 2>&1
) else (
    echo   app.py import: OK
)

echo.
echo   ============================================
echo   Done. Send this output to the developer.
echo   ============================================
echo.
pause