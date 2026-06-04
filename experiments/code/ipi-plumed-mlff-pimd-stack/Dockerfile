FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
# Using devel (not runtime) so PLUMED configure finds CUDA headers and
# can optionally enable its GPU module; TF 2.10 GPU inference works with
# the cuDNN 8 libs already in this image.

LABEL description="i-PI + PLUMED + ML Force Server for PIMD Enhanced Sampling"

ENV DEBIAN_FRONTEND=noninteractive

# ── System build deps ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    build-essential cmake gfortran \
    python3 python3-pip python3-dev \
    libfftw3-dev liblapack-dev libblas-dev \
    libopenmpi-dev openmpi-bin \
    git wget curl \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3 /usr/bin/python

# Cython required for PLUMED Python bindings before compiling
RUN pip3 install --no-cache-dir "cython<3"

# ── PLUMED 2.9.2 (compiled with Python API for i-PI integration) ────────────
# This layer is the expensive one (~20 min); keep it early for Docker cache reuse.
ARG PLUMED_TAG=v2.9.2
RUN git clone --depth=1 --branch ${PLUMED_TAG} \
        https://github.com/plumed/plumed2 /tmp/plumed2 && \
    cd /tmp/plumed2 && \
    CC=gcc CXX=g++ ./configure \
        --prefix=/usr/local \
        --enable-python \
        --enable-modules=+opes \
        PYTHON_BIN=python3 && \
    make -j$(nproc) && \
    make install && \
    rm -rf /tmp/plumed2

ENV PATH=/usr/local/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# i-PI loads PLUMED kernel via ctypes using this path
ENV PLUMED_KERNEL=/usr/local/lib/libplumedKernel.so

# ── i-PI (Python PIMD orchestrator) ────────────────────────────────────────
RUN pip3 install --no-cache-dir ipi

# ── PLUMED Python wrapper (required by i-PI's FFPlumed) ────────────────────
# Uses PLUMED_KERNEL env var to load the kernel compiled above.
RUN pip3 install --no-cache-dir plumed

# ── ML / scientific stack (PhysNet force server) ───────────────────────────
# numpy<1.24 required for TF 2.10 compatibility
RUN pip3 install --no-cache-dir \
    "numpy<1.24" \
    ase \
    pyyaml \
    tensorflow==2.10.1

WORKDIR /workspace
CMD ["/bin/bash"]
