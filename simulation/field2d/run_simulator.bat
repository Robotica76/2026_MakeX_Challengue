@echo off
rem Launch the MakeX Storm Breaker 2D simulator (Windows).
rem   run_simulator.bat                 menu: viewer or a chassis demo
rem   run_simulator.bat [viewer args]   e.g. --program ..\control\my_test.py --time-limit 60
rem First run creates ..\..\.venv and installs pygame (needs Python 3.8+ and internet).
setlocal
cd /d "%~dp0"

set "VENV=%~dp0..\..\.venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo Creating the Python environment in .venv ...
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv "%VENV%"
    ) else (
        py -3 -m venv "%VENV%"
    )
)
if not exist "%PY%" goto :nopython

"%PY%" -c "import pygame" >nul 2>nul
if errorlevel 1 (
    echo Installing pygame ...
    "%PY%" -m pip install -r requirements.txt
    if errorlevel 1 goto :pipfail
)

if not "%~1"=="" (
    "%PY%" viewer.py %*
    goto :end
)

echo.
echo   MakeX Storm Breaker - 2D simulator
echo   1. Simulator (empty)
echo   2. Chassis demo - automatic  (Run starts it, about 44 s)
echo   3. Chassis demo - manual     (Open gamepad first, then Run)
echo.
choice /c 123 /n /m "Choose 1, 2 or 3: "
if errorlevel 3 (
    "%PY%" viewer.py --program ..\control\test_chassis_control_manual.py --time-limit 100
) else if errorlevel 2 (
    "%PY%" viewer.py --program ..\control\test_chassis_control_automatico.py --time-limit 60
) else (
    "%PY%" viewer.py
)
goto :end

:nopython
echo.
echo Python 3 was not found. Install it from https://www.python.org/downloads/
echo (tick "Add python.exe to PATH") and run this file again.
pause
exit /b 1

:pipfail
echo.
echo Could not install pygame. Check the internet connection and run this file again.
pause
exit /b 1

:end
if errorlevel 1 pause
endlocal
