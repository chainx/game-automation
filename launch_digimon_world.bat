@echo off
setlocal
set "PROJECT_DIR=%~dp0"
if not exist "%PROJECT_DIR%Digimon_World\Digimon_World.py" set "PROJECT_DIR=D:\Programming\GitHub repos\game-automation\"
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo Could not open the project folder: "%PROJECT_DIR%"
    pause
    exit /b 1
)
python "Digimon_World\Digimon_World.py"
if errorlevel 1 (
    echo.
    echo Digimon World automation exited with an error.
    pause
)
endlocal
