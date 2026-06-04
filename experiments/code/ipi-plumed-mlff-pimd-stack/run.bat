@echo off
REM Interactive shell into the container with GPU passthrough.
REM Mounts this experiment dir as /workspace (rw) and the repo root as /repo (ro).
REM Usage: run.bat [optional docker run args]

docker run --gpus all -it --rm ^
    -v "%~dp0:/workspace" ^
    -v "%~dp0..\..\..:/repo:ro" ^
    -w /workspace ^
    --name ipi-plumed-dev ^
    ipi-plumed-mlff:latest ^
    /bin/bash %*
