@echo off
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul && set PY=py || set PY=python
start "" http://127.0.0.1:8080/
%PY% -m http.server 8080
