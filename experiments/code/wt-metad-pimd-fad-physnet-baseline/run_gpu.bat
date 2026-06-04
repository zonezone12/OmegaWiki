@echo off
:: GPU-enabled runner using zong-tf210 env (TF 2.10 + CUDA 11.2)
:: Usage: run_gpu.bat <seed> [--resume]
:: Required because TF >= 2.11 dropped native Windows GPU support
setlocal
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-tf210\python.exe
set CUDA_BIN=C:\Users\zonezone\miniforge3\envs\zong-tf210\Library\bin
set PATH=%CUDA_BIN%;%PATH%
set TRAIN=%~dp0train.py
set CONFIG=%~dp0config.yaml
set OUTDIR=%~dp0results_physnet
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-wt-metad-pimd-fad-physnet-baseline.log
set RESUME=%2

echo === SEED %1 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed %1 --out-dir "%OUTDIR%" %RESUME% >> "%LOGFILE%" 2>&1
echo === SEED %1 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
