@echo off
:: Escalated runner: gamma=100, h=5 kJ/mol, seed=1
:: Usage: run_escalated.bat [seed]
setlocal
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-tf210\python.exe
set CUDA_BIN=C:\Users\zonezone\miniforge3\envs\zong-tf210\Library\bin
set PATH=%CUDA_BIN%;%PATH%
set TRAIN=%~dp0train.py
set CONFIG=%~dp0config_escalated.yaml
set OUTDIR=%~dp0results_physnet
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-wt-metad-pimd-fad-physnet-baseline.log
set SEED=1
if not "%1"=="" set SEED=%1

echo === ESCALATED SEED %SEED% (gamma=100 h=5) started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed %SEED% --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === ESCALATED SEED %SEED% done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
