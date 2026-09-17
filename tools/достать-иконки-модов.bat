@echo off
chcp 65001 >nul
cd /d "%~dp0.."
where py >nul 2>nul && set PY=py || set PY=python
echo Извлечение иконок из модов Steam Workshop...
%PY% tools\extract_mod_icons.py
if errorlevel 1 (
  echo.
  echo Ошибка. Нужен Python и: pip install "armaio[pillow]"
  pause
  exit /b 1
)
echo.
echo Обновляю каталог сайта...
%PY% tools\build_catalog.py
if errorlevel 1 (
  echo Не удалось собрать каталог.
  pause
  exit /b 1
)
echo.
echo Готово.
pause
