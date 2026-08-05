@echo off
chcp 65001 >nul
title 网文动态大纲
cd /d "%~dp0"

:: 检查 Python 是否可用
where py >nul 2>&1
if %errorlevel% neq 0 (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo   [错误] 未检测到 Python，请先安装 Python 3.9+
        echo   下载地址：https://www.python.org/downloads/
        echo   安装时请勾选 "Add Python to PATH"
        echo.
        pause
        exit /b 1
    )
    set PYTHON=python
) else (
    set PYTHON=py
)

:: 检查依赖是否安装
%PYTHON% -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo   [提示] 正在安装依赖...
    echo.
    %PYTHON% -m pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo   [错误] 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

echo.
echo   正在启动 网文动态大纲...
echo.
%PYTHON% -OO app.py
