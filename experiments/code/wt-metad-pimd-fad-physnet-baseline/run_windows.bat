@echo off
setlocal
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\exp-wt-metad-pimd-fad-physnet-baseline.log
echo === SEED 42 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
python -u "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\train.py" --config "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\config.yaml" --seed 42 --out-dir "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\results_physnet" >> "%LOGFILE%" 2>&1
echo === SEED 42 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
echo === SEED 123 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
python -u "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\train.py" --config "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\config.yaml" --seed 123 --out-dir "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\results_physnet" >> "%LOGFILE%" 2>&1
echo === SEED 123 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
echo === SEED 7 started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
python -u "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\train.py" --config "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\config.yaml" --seed 7 --out-dir "C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\experiments\code\wt-metad-pimd-fad-physnet-baseline\results_physnet" >> "%LOGFILE%" 2>&1
echo === SEED 7 done %DATE% %TIME% === >> "%LOGFILE%" 2>&1
echo === ALL DONE %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
