@echo off
:: Run seeds 123 and 7 (fresh runs, after seed 42 completes)
:: Each seed gets its own Python process to avoid TF GPU memory crash on re-init
setlocal
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-test\python.exe
set TRAIN=%~dp0train.py
set CONFIG=%~dp0config.yaml
set OUTDIR=%~dp0results_physnet
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-wt-metad-pimd-fad-physnet-baseline.log

echo === SEED 123 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed 123 --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === SEED 123 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1

echo === SEED 7 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed 7 --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === SEED 7 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1

echo === ALL SEEDS DONE %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
