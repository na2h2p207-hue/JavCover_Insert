@echo off
chcp 65001 > nul
cd /d "%~dp0"

:loop
if "%~1"=="" goto done
echo Processing: "%~1"
python "%~dp0rename\manual_fix.py" "%~1"
shift
goto loop

:done
echo.
echo All done.
pause
