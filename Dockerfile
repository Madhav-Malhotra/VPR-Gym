FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
# set out workspace
ENV WORKSPACE=/workspace
RUN mkdir -p ${WORKSPACE}
WORKDIR ${WORKSPACE}
COPY . ${WORKSPACE}
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
# Build VTR
RUN make && make install
# Container's default launch command
SHELL ["/bin/bash", "-c"]