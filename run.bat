@echo off
setlocal
cd /d "%~dp0"

REM Make sure the app has been installed
if not exist "tts_env\Scripts\python.exe" (
    echo [ERROR] The app is not installed yet.
    echo Double-click install.bat first, then come back here.
    echo.
    pause
    exit /b 1
)

call tts_env\Scripts\activate.bat
python tts_engine.py
if errorlevel 1 (
    echo.
    echo Generation finished WITH errors - see the messages above.
) else (
    echo.
    echo Generation complete!
)
echo.
pause
endlocal