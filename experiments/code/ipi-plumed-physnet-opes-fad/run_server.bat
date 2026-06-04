@echo off
:: Launch PhysNet i-PI force server on Windows (GPU side)
:: Start this BEFORE launching i-PI in Docker
setlocal
set PYTHON=C:\Users\zonezone\miniforge3\envs\zong-tf210\python.exe
set CUDA_BIN=C:\Users\zonezone\miniforge3\envs\zong-tf210\Library\bin
set PATH=%CUDA_BIN%;%PATH%
set SERVER=%~dp0physnet_server.py
set LOGFILE=C:\Users\zonezone\Desktop\YCU_research\MetaDynamics\OmegaWiki\logs\physnet-ipi-server.log

echo === PhysNet i-PI server started %DATE% %TIME% === >> "%LOGFILE%" 2>&1
"%PYTHON%" -u "%SERVER%" --port 31415 --beads 32 >> "%LOGFILE%" 2>&1
echo === PhysNet i-PI server stopped %DATE% %TIME% === >> "%LOGFILE%" 2>&1
endlocal
