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

# Copy the rest of the project (benchmarks, Python code, etc.)
# This layer will rebuild when you add Titan benchmarks, but won't rebuild dependencies or VTR
COPY . ${WORKSPACE}

# Container's default launch command
SHELL ["/bin/bash", "-c"]