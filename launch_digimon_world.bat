@echo off
setlocal
set "EMULATOR_DIR=D:\Gaming\Emulators\PS1"
set "CHEAT_ENGINE=C:\Program Files\Cheat Engine\cheatengine-x86_64.exe"
set "PROJECT_DIR=%~dp0"
if not exist "%PROJECT_DIR%Digimon_World\Digimon_World.py" set "PROJECT_DIR=D:\Programming\GitHub repos\game-automation\"
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo Could not open the project folder: "%PROJECT_DIR%"
    pause
    exit /b 1
)
if not exist "%EMULATOR_DIR%\psxfin.exe" (
    echo Emulator not found: "%EMULATOR_DIR%\psxfin.exe"
    pause
    exit /b 1
)
if not exist "%CHEAT_ENGINE%" (
    echo Cheat Engine not found: "%CHEAT_ENGINE%"
    pause
    exit /b 1
)
tasklist /FI "IMAGENAME eq psxfin.exe" /NH | findstr /I /C:"psxfin.exe" >nul
if errorlevel 1 (
    rem Clear findstr's no-match exit code before checking START's result.
    cmd /c exit 0
    start "" /D "%EMULATOR_DIR%" "%EMULATOR_DIR%\psxfin.exe"
    if errorlevel 1 (
        echo Could not start the emulator.
        pause
        exit /b 1
    )
)
tasklist /NH | findstr /I /C:"cheatengine-" /C:"Cheat Engine.exe" >nul
if errorlevel 1 (
    cmd /c exit 0
    start "" "%CHEAT_ENGINE%"
    if errorlevel 1 (
        echo Could not start Cheat Engine.
        pause
        exit /b 1
    )
)
echo.
echo Load Digimon World in the emulator. Automation will connect when ready.
python "Digimon_World\Digimon_World.py"
if errorlevel 1 (
    echo.
    echo Digimon World automation exited with an error.
    pause
)
endlocal
