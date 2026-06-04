@echo off
echo Building ipi-plumed-mlff image...
echo Note: PLUMED compilation takes ~20 minutes on first build.
echo       Subsequent builds use the Docker layer cache.
echo.

docker build ^
    --progress=plain ^
    -t ipi-plumed-mlff:latest ^
    -f Dockerfile ^
    .

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful. Image: ipi-plumed-mlff:latest
    docker images ipi-plumed-mlff:latest
) else (
    echo.
    echo Build FAILED. Check output above.
    exit /b 1
)
