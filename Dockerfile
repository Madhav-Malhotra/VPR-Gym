FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
# set out workspace
ENV WORKSPACE=/workspace
RUN mkdir -p ${WORKSPACE}
WORKDIR ${WORKSPACE}

# Copy only dependency files first (these change rarely)
COPY install_apt_packages.sh requirements.txt ${WORKSPACE}/
COPY VprGym/requirements.txt ${WORKSPACE}/VprGym/

# Install and cleanup is done in one command to minimize the build cache size
RUN apt-get update -qq \
# Extract package names from install_apt_packages.sh
    && sed '/sudo/d' install_apt_packages.sh | sed '/#/d' | sed 's/ \\//g' | sed '/^$/d' | sed '/^[[:space:]]*$/d' \
# Install packages
    | xargs apt-get -y install --no-install-recommends \
# Additional packages not listed in install_apt_packages.sh
    && apt-get -y install --no-install-recommends \
    wget \
    ninja-build \
    libeigen3-dev \
    libtbb-dev \
    python3-pip \
    libzmq3-dev \
    git \
# Install cppzmq (header-only library)
    && cd /tmp \
    && git clone https://github.com/zeromq/cppzmq.git \
    && cd cppzmq \
    && mkdir build && cd build \
    && cmake .. \
    && make -j4 install \
    && cd /workspace \
# Install python packages
    && pip install -r requirements.txt \
    && pip install -r VprGym/requirements.txt \
# Cleanup
    && apt-get autoclean && apt-get clean && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/* /tmp/cppzmq

# Copy source code needed for build (CMake files, Makefiles, source)
COPY CMakeLists.txt Makefile ${WORKSPACE}/
COPY cmake ${WORKSPACE}/cmake/
COPY libs ${WORKSPACE}/libs/
COPY vpr ${WORKSPACE}/vpr/
COPY ODIN_II ${WORKSPACE}/ODIN_II/
COPY abc ${WORKSPACE}/abc/
COPY ace2 ${WORKSPACE}/ace2/
COPY utils ${WORKSPACE}/utils/
COPY blifexplorer ${WORKSPACE}/blifexplorer/
COPY verilog_preprocessor ${WORKSPACE}/verilog_preprocessor/

# Build VTR (this layer will be cached unless source code changes)
RUN make && make install

# Copy only the essential benchmarks and architectures to reduce image size
# This avoids copying large Titan benchmark directories (8.2GB+)
# Note: Only includes stratixiv architecture and mkDelayWorker32B benchmark

# Copy VPR flow essential directories
COPY vtr_flow/scripts ${WORKSPACE}/vtr_flow/scripts/
COPY vtr_flow/tasks ${WORKSPACE}/vtr_flow/tasks/
COPY vtr_flow/misc ${WORKSPACE}/vtr_flow/misc/
COPY vtr_flow/parse ${WORKSPACE}/vtr_flow/parse/
COPY vtr_flow/sdc ${WORKSPACE}/vtr_flow/sdc/
COPY vtr_flow/tech ${WORKSPACE}/vtr_flow/tech/
COPY vtr_flow/primitives.v ${WORKSPACE}/vtr_flow/primitives.v

# Copy only the stratixiv architecture (used in ablation study)
RUN mkdir -p ${WORKSPACE}/vtr_flow/arch/titan ${WORKSPACE}/vtr_flow/arch/common
COPY vtr_flow/arch/titan/stratixiv_arch.timing.xml ${WORKSPACE}/vtr_flow/arch/titan/
COPY vtr_flow/arch/common/ ${WORKSPACE}/vtr_flow/arch/common/

# Copy minimal benchmarks (only the small blif directory - 47MB, and verilog for mkDelayWorker32B)
# Also includes the stereo_vision benchmark used by example.py
# Excludes most of titan_blif (8.2GB) and titan_other_blif (509MB)
COPY vtr_flow/benchmarks/blif ${WORKSPACE}/vtr_flow/benchmarks/blif/
RUN mkdir -p ${WORKSPACE}/vtr_flow/benchmarks/verilog ${WORKSPACE}/vtr_flow/benchmarks/titan_blif
COPY vtr_flow/benchmarks/verilog/mkDelayWorker32B.v ${WORKSPACE}/vtr_flow/benchmarks/verilog/
COPY vtr_flow/benchmarks/titan_blif/stereo_vision_stratixiv_arch_timing.blif ${WORKSPACE}/vtr_flow/benchmarks/titan_blif/

# Copy Python VprGym code
COPY VprGym ${WORKSPACE}/VprGym/

# Copy root-level project files
COPY *.py *.sh *.md ${WORKSPACE}/

# Container's default launch command
SHELL ["/bin/bash", "-c"]