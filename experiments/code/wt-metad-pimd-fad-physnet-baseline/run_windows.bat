@echo off
setlocal
set SCRIPT_DIR=%~dp0
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-wt-metad-pimd-fad-physnet-baseline.log
set TRAIN=%SCRIPT_DIR%train.py
set CONFIG=%SCRIPT_DIR%config.yaml
set OUTDIR=%SCRIPT_DIR%results_physnet
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-test\python.exe

:: Seed 42 — RESUME from existing hills/colvar (31.3 ps already done)
echo === Experiment wt-metad-pimd-fad-physnet-baseline launched %DATE% %TIME% === >> "%LOGFILE%" 2>&1
echo === SEED 42 RESUME started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed 42 --out-dir "%OUTDIR%" --resume >> "%LOGFILE%" 2>&1
echo === SEED 42 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1

:: Seed 123 — fresh run (previous attempt crashed on TF re-init)
echo === SEED 123 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed 123 --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === SEED 123 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1

:: Seed 7 — fresh run
echo === SEED 7 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%TRAIN%" --config "%CONFIG%" --seed 7 --out-dir "%OUTDIR%" >> "%LOGFILE%" 2>&1
echo === SEED 7 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1

echo === ALL DONE %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
