# VPR-Gym Complete Installation Guide

This guide provides step-by-step instructions for installing VPR-Gym and all its dependencies.

## Important Notes

**The VPR-Gym repository IS the VTR repository!** This repository already contains the complete VTR (Verilog to Routing) source code with VPR-Gym additions in the `VprGym/` directory. You do NOT need to clone VTR separately.

## Prerequisites

- A 64-bit Linux system (tested on Debian/Ubuntu)
- Internet connection for downloading dependencies and benchmarks
- At least 15GB of free disk space (for VTR build + Titan benchmarks)
- sudo access for installing system packages

## Installation Steps

### Step 1: Install System Dependencies

From the repository root directory (`/home/mdvmlhtr/VPR-Gym`), run:

```bash
./install_apt_packages.sh
```

This installs the following packages:
- Build tools: `make`, `cmake`, `build-essential`, `pkg-config`
- Parsers: `bison`, `flex`
- Python: `python3-dev`, `python3-venv`
- Graphics: `libgtk-3-dev`, `libx11-dev`
- Yosys dependencies: `clang`, `tcl-dev`, `libreadline-dev`
- Documentation: `sphinx-common`

### Step 2: Set Up Python Virtual Environment

Create and activate a Python virtual environment:

```bash
make env
source .venv/bin/activate
```

**Important:** You must activate this virtual environment (`source .venv/bin/activate`) in every new terminal session where you want to use VPR-Gym.

### Step 3: Install Python Dependencies for VTR

```bash
pip install -r requirements.txt
```

This installs:
- `prettytable`
- `lxml`
- `psutil`
- `black==20.8b1` (code formatter)
- `pylint==2.7.4` (linter)

### Step 4: Install cppzmq (ZeroMQ C++ Bindings)

**IMPORTANT: This step must be completed BEFORE building VTR, as the build requires ZeroMQ headers.**

cppzmq is required for communication between the Python RL agent and the VPR C++ code.

#### 4.1: Install libzmq (dependency)

```bash
# Clone libzmq
git clone https://github.com/zeromq/libzmq.git
cd libzmq

# Build and install
mkdir build
cd build
cmake ..
sudo make -j4 install

# Return to VPR-Gym directory
cd ../..
```

#### 4.2: Install cppzmq

```bash
# Clone cppzmq
git clone https://github.com/zeromq/cppzmq.git
cd cppzmq

# Build and install (header-only library)
mkdir build
cd build
cmake ..
sudo make -j4 install

# Return to VPR-Gym directory
cd ..
```

**Note:** cppzmq is a header-only library, so the "install" step mainly copies header files to system directories.

**Where to clone these repositories?**
You can clone `libzmq` and `cppzmq` anywhere on your system (e.g., your home directory or a `~/projects` folder). They do NOT need to be inside the VPR-Gym directory. The `sudo make install` command will install the libraries to system directories (typically `/usr/local/lib` and `/usr/local/include`).

### Step 5: Build VTR

```bash
make -j4
```

This compiles all VTR tools including VPR. The build process:
- Creates a `build/` directory
- Uses CMake to configure the build
- Compiles all required executables

**Note:** The build has been configured to use g++-9 (compatible with Ubuntu 20.04) instead of the system default. This ensures compatibility with the codebase.

To verify the installation, run:

```bash
./vtr_flow/scripts/run_vtr_task.py regression_tests/vtr_reg_basic/basic_timing
```

Expected output should show multiple "OK" results.

### Step 6: Download Titan Benchmarks

The Titan benchmarks are large FPGA benchmark circuits used for testing and research.

**Download Method:** Use the built-in make command (automatic):

```bash
make get_titan_benchmarks
```

This command will:
- Download a ~1GB compressed archive from `http://www.eecg.utoronto.ca/~kmurray/titan/titan_release_1.1.0.tar.gz`
- Verify the MD5 checksum
- Extract benchmark files to `vtr_flow/benchmarks/titan_blif/`
- Extract architecture files to `vtr_flow/arch/titan/`
- Require ~10GB of disk space after extraction

**You do NOT need to:**
- Clone a separate repository
- Manually download and unzip files
- Move files to specific directories

Everything is handled automatically by the make command.

### Step 7: Install VPR-Gym Python Dependencies

Navigate to the VprGym directory and install its specific requirements:

```bash
cd VprGym
pip install -r requirements.txt
```

This installs:
- `pyzmq` (Python bindings for ZeroMQ)
- `gym` (OpenAI Gym framework)

### Step 8: Test VPR-Gym Installation

Run the example script to verify everything works:

```bash
# Make sure you're in the VprGym directory
cd VprGym

# Run the example
python3 example.py
```

**Important:** Always use the `VprGym/` directory as your working directory when running the RL agent.

You can also test the block-type enabled environment:

```bash
python3 blocktype_example.py
```

## Directory Structure

After installation, your repository structure will look like this:

```
VPR-Gym/                          # Root directory (this IS the VTR repository)
├── vpr/                          # VPR source code
├── vtr_flow/                     # VTR flow scripts
│   ├── benchmarks/
│   │   ├── titan_blif/          # Titan benchmarks (after download)
│   │   └── ...
│   └── arch/
│       ├── titan/               # Titan architectures (after download)
│       └── ...
├── VprGym/                       # VPR-Gym RL environment
│   ├── src/                     # VPR-Gym source code
│   ├── example.py               # Basic example
│   ├── blocktype_example.py     # Block-type example
│   └── requirements.txt         # VPR-Gym Python dependencies
├── build/                        # Build artifacts (created by make)
├── .venv/                        # Python virtual environment (created by make env)
├── install_apt_packages.sh       # System package installer
├── Makefile                      # Build system
├── requirements.txt              # VTR Python dependencies
└── README.md
```

External repositories (can be anywhere):
```
~/                                # Or any directory you choose
├── libzmq/                      # ZeroMQ library (after git clone)
└── cppzmq/                      # ZeroMQ C++ bindings (after git clone)
```

## Quick Start Summary

For a fresh installation on Ubuntu/Debian:

```bash
# 1. Install system packages (including g++-9 for compatibility)
./install_apt_packages.sh
sudo apt-get install -y g++-9 gcc-9

# 2. Set up Python environment
make env
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install ZeroMQ (required BEFORE building VTR)
# You can do this anywhere on your system
git clone https://github.com/zeromq/libzmq.git
cd libzmq
mkdir build && cd build
cmake .. && sudo make -j4 install
cd ../..

git clone https://github.com/zeromq/cppzmq.git
cd cppzmq
mkdir build && cd build
cmake .. && sudo make -j4 install
cd ../..

# Return to VPR-Gym directory
cd /home/mdvmlhtr/VPR-Gym

# 5. Build VTR (uses g++-9 automatically via Makefile)
make -j4

# 6. Download Titan benchmarks
make get_titan_benchmarks

# 7. Install VPR-Gym dependencies
cd VprGym
pip install -r requirements.txt

# 8. Test the installation
python3 example.py
```

## Troubleshooting

### Compiler Version Issues

**Why g++-9?** The VPR-Gym codebase was developed for Ubuntu 20.04, which uses g++ 9.x. Newer compilers (g++ 11+) have stricter C++ parsing that causes compilation errors in some external libraries (like libcatch2). Using g++-9 ensures compatibility.

If you're on Ubuntu 24.04 or newer and haven't installed g++-9:
```bash
sudo apt-get install -y g++-9 gcc-9
```

The Makefile in this repository has been configured to automatically use g++-9.

### Virtual Environment Issues

If you see Python import errors, make sure you've activated the virtual environment:
```bash
source .venv/bin/activate
```

### Build Failures

If the build fails, try cleaning and rebuilding:
```bash
make distclean
make -j4
```

### ZeroMQ Issues

**Missing zmq.hpp error during build:**
If you get `fatal error: zmq.hpp: No such file or directory`, you need to install ZeroMQ (Step 4) BEFORE building VTR (Step 5).

**Other ZeroMQ errors:**
1. Verify libzmq is installed: `ldconfig -p | grep zmq`
2. You may need to run `sudo ldconfig` after installing libzmq
3. Check that `pyzmq` is installed in your Python environment: `pip list | grep pyzmq`

### Titan Benchmark Download Fails

If the automatic download fails:
- Check your internet connection
- The download is ~1GB and may take time
- You can retry by running `make get_titan_benchmarks` again

## Additional Resources

- [VTR Documentation](https://docs.verilogtorouting.org/)
- [VPR-Gym Paper](https://doi.org/10.1109/FPL60245.2023.00018)
- [OpenAI Gym Documentation](https://www.gymlibrary.dev/)
- [ZeroMQ Guide](https://zeromq.org/get-started/)
