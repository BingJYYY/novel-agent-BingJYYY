@echo off
chcp 65001 >nul
title 网文动态大纲
cd /d "%~dp0"

python app.py
pause
