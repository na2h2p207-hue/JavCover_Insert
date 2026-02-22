@echo off
setlocal EnableExtensions DisableDelayedExpansion

REM =====================================================
REM 4K -> 1080p + 30fps + x264 (crf18, medium) + aac 192k
REM - Drag & drop one or more video files onto this BAT.
REM - Or double-click to process current folder.
REM =====================================================

REM Use UTF-8 code page so non-ASCII paths work better
chcp 65001 >nul

REM ====== Settings ======
set "CRF=18"
set "PRESET=medium"
set "ABR=192k"
set "FPS=30"
set "SCALE_H=1080"
REM ======================

REM --- Resolve ffmpeg (priority: BAT dir > ProgramFiles(x86) > ProgramFiles > PATH) ---
set "FFMPEG=ffmpeg"

for %%P in (
  "%ProgramFiles%\lada\_internal\ffmpeg.exe"
  "%ProgramFiles(x86)%\lada\_internal\ffmpeg.exe"
  "%~dp0ffmpeg.exe"
) do (
  if exist "%%~fP" set "FFMPEG=%%~fP"
)

echo.
echo [FFMPEG] "%FFMPEG%"
echo [INFO ] 1080p + %FPS%fps, x264 crf=%CRF% preset=%PRESET%, aac %ABR%
echo.

REM --- If files were dragged onto this BAT, process those ---
if not "%~1"=="" (
  echo [MODE ] Drag ^& drop
  goto :PROCESS_ARGS
)

REM --- Otherwise, process current folder ---
echo [MODE ] Current folder: "%CD%"
for %%F in (*.mp4 *.mkv *.mov *.m4v) do (
  if exist "%%F" call :ENCODE_ONE "%%~fF"
)
goto :DONE


:PROCESS_ARGS
:ARG_LOOP
if "%~1"=="" goto :DONE

REM Only process common video types; skip others quietly
if /I "%~x1"==".mp4" call :ENCODE_ONE "%~f1"
if /I "%~x1"==".mkv" call :ENCODE_ONE "%~f1"
if /I "%~x1"==".mov" call :ENCODE_ONE "%~f1"
if /I "%~x1"==".m4v" call :ENCODE_ONE "%~f1"

shift
goto :ARG_LOOP


:ENCODE_ONE
set "IN=%~1"
set "OUT=%~dpn1_1080p%FPS%.mp4"

echo ------------------------------------------------------------
echo [IN ] "%IN%"
echo [OUT] "%OUT%"
echo.

"%FFMPEG%" -hide_banner -y ^
  -i "%IN%" ^
  -vf "scale=-2:%SCALE_H%,fps=%FPS%" ^
  -c:v libx264 -preset %PRESET% -crf %CRF% ^
  -c:a aac -b:a %ABR% ^
  "%OUT%"

if errorlevel 1 (
  echo [FAIL] %~nx1
) else (
  echo [OK  ] %~nx1
)
echo.
exit /b 0


:DONE
echo Done.
pause
endlocal