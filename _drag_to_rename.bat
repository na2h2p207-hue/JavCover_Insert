@echo off
chcp 65001 > nul
cd /d "%~dp0"

:loop
if "%~1"=="" goto done
echo Processing: "%~1"

if exist "%~1\" (
    rem It is a directory
    python "%~dp0rename\rename_movies.py" --dir "%~1"
) else (
    rem It is a file
    python "%~dp0rename\rename_movies.py" --dir "%~dp1." --target "%~nx1"
)

shift
goto loop

:done
echo.
echo All done.
pause
