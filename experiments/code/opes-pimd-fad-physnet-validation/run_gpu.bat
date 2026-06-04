@echo off
:: OPES-PIMD PhysNet FAD validation: GPU runner
:: Usage: run_gpu.bat <seed>
setlocal
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-tf210\python.exe
set CUDA_BIN=C:\Users\zonezone\miniforge3\envs\zong-tf210\Library\bin
set PATH=%CUDA_BIN%;%PATH%
set TRAIN=%~dp0train.py
set CONFIG=%~dp0config.yaml
set OUTDIR=%~dp0results_physnet
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-opes-pimd-fad-physnet-validation.log

echo === OPES SEED %1 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed %1 --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === OPES SEED %1 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
