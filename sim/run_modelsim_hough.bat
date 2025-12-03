@echo off
REM Batch script to run Hough Transform test in ModelSim
REM Usage: run_modelsim_hough.bat [gui|batch]

set MODELSIM_PATH=C:\intelFPGA\18.1\modelsim_ase\win32aloem
set VSIM=%MODELSIM_PATH%\vsim.exe

if not exist "%VSIM%" (
    echo ERROR: ModelSim not found at %VSIM%
    echo Please update MODELSIM_PATH in this script
    pause
    exit /b 1
)

echo ========================================
echo Hough Transform ModelSim Test
echo ========================================
echo.

if "%1"=="batch" (
    echo Running in BATCH mode...
    "%VSIM%" -c -do "do run_hough_modelsim.do; quit -f"
) else (
    echo Running in GUI mode...
    "%VSIM%" -gui -do run_hough_modelsim.do
)
