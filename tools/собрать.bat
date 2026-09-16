@echo off
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul && set PY=py || set PY=python
%PY% tools\build_catalog.py
if errorlevel 1 (
  echo.
  echo Не удалось запустить Python. Установите python.org и повторите.
  pause
  exit /b 1
)
echo.
echo Сайт обновлён. Откройте index.html или запустите tools\открыть-сайт.bat
pause
