FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# System dependencies
RUN apt-get update && apt-get install -y \
    build-essential cmake gfortran g++ \
    python3 python3-pip python3-dev \
    libfftw3-dev libopenmpi-dev openmpi-bin \
    git wget curl vim \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip3 install numpy ipi

# Build PLUMED 2.9 with Python interface
WORKDIR /opt
RUN git clone --depth=1 --branch v2.9.3 https://github.com/plumed/plumed2.git
WORKDIR /opt/plumed2
RUN ./configure \
    --prefix=/usr/local \
    --enable-python \
    --enable-fftw \
    PYTHON_BIN=python3 \
    && make -j$(nproc) \
    && make install

# Add PLUMED to environment
ENV PLUMED_KERNEL=/usr/local/lib/libplumedKernel.so
ENV LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH}
ENV PATH=/usr/local/bin:${PATH}

# Patch i-PI to load PLUMED kernel (needed for ffplumed)
# i-PI's PLUMED interface requires PLUMED_KERNEL env var to be set
RUN python3 -c "import ipi; print('i-PI version:', ipi.__version__)"
RUN plumed --version

WORKDIR /simulation
CMD ["bash"]
