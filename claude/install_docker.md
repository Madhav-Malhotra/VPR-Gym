# Docker Setup for VPR-Gym Python Experiments

This guide shows you how to use Docker to create a pre-built VPR-Gym environment where you only need to edit Python experiment files without worrying about building VTR.

## Quick Start

### 1. Build the Docker Image (One-Time Setup)

From the VPR-Gym root directory:

```bash
docker build -t vpr-gym .
```

This builds VTR and installs all dependencies. **This takes 20-30 minutes** but only needs to be done once.

### 2. Run the Container with Volume Mounting

Mount your local `VprGym/` directory so you can edit Python files on your host machine:

```bash
docker run -it --rm \
  -v "$(pwd)/VprGym:/workspace/VprGym" \
  -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
  -w /workspace/VprGym \
  vpr-gym \
  bash
```

**What this does:**
- `-v "$(pwd)/VprGym:/workspace/VprGym"` - Mounts your local VprGym directory into the container
- `-v "$(pwd)/vtr_flow:/workspace/vtr_flow"` - Mounts benchmarks/architectures (read-only access is fine)
- `-w /workspace/VprGym` - Sets working directory to VprGym (required for experiments)
- `--rm` - Automatically removes container when you exit
- `-it` - Interactive terminal

### 3. Run Your Experiment

Inside the container:

```bash
python3 example.py
```

### 4. Edit Files on Your Host

While the container is running, edit Python files in `VprGym/` on your host machine with your favorite editor. Changes are immediately reflected in the container.

## Development Workflow

### Recommended Setup

The repository includes a `run_docker.sh` helper script that supports multiple modes:

**Usage:**
```bash
./run_docker.sh                    # Interactive bash shell
./run_docker.sh my_experiment.py   # Run Python file interactively
./run_docker.sh -D my_experiment.py # Run in detached (background) mode
```

Make it executable if needed:
```bash
chmod +x run_docker.sh
```

**Features:**
- Automatically creates timestamped experiment directories in `VprGym/exp/{timestamp}/`
- Logs all output to `run.log` in the experiment directory
- Volume mounts ensure all results are immediately available on your host machine
- Unique container names prevent conflicts when running multiple experiments

### Creating Your Own Experiment

1. On your host machine, create a new Python file in `VprGym/`:
   ```python
   # VprGym/my_experiment.py
   import numpy as np
   from src.vprGym import VprEnv

   env = VprEnv(
       inner_num=0.1,
       port='5555',
       seed=0,
       arch='vtr_flow/arch/titan/stratixiv_arch.timing.xml',
       directory='my_results',
       benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif',
       reward_func='WLbiased_runtime_aware'
   )

   # Your RL algorithm here
   done = False
   while not done:
       action = env.action_space.sample()  # Random action
       _, reward, done, info = env.step(action)

       if info == 'stage2':
           print("Entered stage 2")
           break

   print(f"Results: WL={info['WL']}, CPD={info['CPD']}")
   ```

2. Run it using the helper script:
   ```bash
   # Interactive mode (drops to shell after completion)
   ./run_docker.sh my_experiment.py

   # Detached mode (runs in background)
   ./run_docker.sh -D my_experiment.py
   ```

3. Results are automatically saved to:
   - `VprGym/exp/{timestamp}/run.log` - Complete output log
   - `VprGym/my_results/` - VPR experiment outputs (accessible from host)

## Running Multiple Experiments in Parallel

### Option 1: Multiple Containers

Open multiple terminals and run the same container with different ports:

**Terminal 1:**
```bash
docker run -it --rm \
  -v "$(pwd)/VprGym:/workspace/VprGym" \
  -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
  -w /workspace/VprGym \
  vpr-gym bash

# Inside container:
python3 experiment_port5555.py  # Uses port='5555'
```

**Terminal 2:**
```bash
docker run -it --rm \
  -v "$(pwd)/VprGym:/workspace/VprGym" \
  -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
  -w /workspace/VprGym \
  vpr-gym bash

# Inside container:
python3 experiment_port6666.py  # Uses port='6666'
```

### Option 2: Background Containers (Using Helper Script)

The `run_docker.sh` script makes this easy:

```bash
# Start first experiment in background
./run_docker.sh -D experiment1.py

# Start second experiment in background (automatically gets unique port/container)
./run_docker.sh -D experiment2.py

# Monitor specific experiment
docker logs -f vpr-gym-20250131_143022

# List all running experiments
docker ps -f name=vpr-gym
```

Each experiment gets:
- Unique timestamped container name
- Separate output directory in `VprGym/exp/{timestamp}/`
- Complete logs in `run.log`

## Accessing Results

All experiment outputs are written to directories under `VprGym/` which are mounted from your host. You can access them directly:

```bash
# On your host machine
ls VprGym/my_results/
cat VprGym/my_results/seed_0_inner_num_0.1_RL_gym_placement_blk_type_off/vpr_stdout.log
```

## Installing Additional Python Packages

If you need extra Python libraries:

### Temporary Installation (Lost on Container Exit)

Inside the container:
```bash
pip3 install torch numpy matplotlib
python3 my_dl_experiment.py
```

### Permanent Installation (Rebuild Image)

1. Edit `VprGym/requirements.txt` on your host:
   ```
   pyzmq
   gym
   torch
   numpy
   matplotlib
   ```

2. Rebuild the Docker image:
   ```bash
   docker build -t vpr-gym .
   ```

## Troubleshooting

### Port Already in Use Errors

If you see ZeroMQ binding errors, make sure each parallel experiment uses a unique port:

```python
# Experiment 1
env = VprEnv(port='5555', ...)

# Experiment 2
env = VprEnv(port='6666', ...)
```

### Permission Issues with Mounted Volumes

If you get permission errors writing to mounted directories:

```bash
# Run container as your user
docker run -it --rm \
  -u $(id -u):$(id -g) \
  -v "$(pwd)/VprGym:/workspace/VprGym" \
  -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
  -w /workspace/VprGym \
  vpr-gym bash
```

### Container Can't Find Benchmarks

Make sure you mount `vtr_flow`:
```bash
-v "$(pwd)/vtr_flow:/workspace/vtr_flow"
```

And use relative paths in your Python code:
```python
benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif'
```

### VPR Binary Not Found

If VPR isn't in the PATH, the Docker build may have failed. Rebuild:

```bash
docker build --no-cache -t vpr-gym .
```

Check that `make install` completed successfully in the build logs.

### CMake Cache Error During Build

If you see errors like:
```
CMake Error: The current CMakeCache.txt directory /workspace/build/CMakeCache.txt
is different than the directory /home/user/VPR-Gym/build where CMakeCache.txt was created.
```

**Solution:** Your local `build/` directory is being copied into Docker with cached paths. The `.dockerignore` file should prevent this, but if you created it after the first build attempt:

```bash
# Ensure .dockerignore exists and contains 'build/'
cat .dockerignore

# Clean and rebuild
docker build --no-cache -t vpr-gym .
```

If the problem persists, manually exclude the build directory:
```bash
# Option 1: Temporarily move build directory
mv build build.backup
docker build -t vpr-gym .
mv build.backup build

# Option 2: Clean local build first
make distclean
docker build -t vpr-gym .
```

## Advanced: Building Without Full VTR Source

If you want a smaller image that only includes built binaries:

Create `Dockerfile.runtime`:

```dockerfile
FROM ubuntu:20.04 AS builder
ARG DEBIAN_FRONTEND=noninteractive
ENV WORKSPACE=/workspace
RUN mkdir -p ${WORKSPACE}
WORKDIR ${WORKSPACE}
COPY . ${WORKSPACE}
RUN apt-get update -qq && \
    sed '/sudo/d' install_apt_packages.sh | sed '/#/d' | sed 's/ \\//g' | sed '/^$/d' | sed '/^[[:space:]]*$/d' | \
    xargs apt-get -y install --no-install-recommends && \
    apt-get -y install --no-install-recommends wget ninja-build libeigen3-dev libtbb-dev python3-pip && \
    make && make install

FROM ubuntu:20.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    python3 python3-pip libgomp1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /workspace/vpr/vpr /usr/local/bin/
COPY --from=builder /workspace/vtr_flow /workspace/vtr_flow
COPY --from=builder /workspace/VprGym /workspace/VprGym
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt && \
    pip3 install -r /workspace/VprGym/requirements.txt

WORKDIR /workspace/VprGym
```

Build and run:
```bash
docker build -f Dockerfile.runtime -t vpr-gym-slim .
docker run -it --rm -v "$(pwd)/VprGym:/workspace/VprGym" vpr-gym-slim bash
```

This creates a much smaller image (~500MB vs ~3GB) but you can't rebuild VTR inside it.

## Summary

**For pure Python experimentation:**
1. Build image once: `docker build -t vpr-gym .`
2. Run with mounts: `docker run -it --rm -v "$(pwd)/VprGym:/workspace/VprGym" -v "$(pwd)/vtr_flow:/workspace/vtr_flow" -w /workspace/VprGym vpr-gym bash`
3. Edit Python files on your host machine
4. Run experiments in the container: `python3 my_experiment.py`
5. Access results on your host in `VprGym/<directory>/`

You never need to rebuild VTR or worry about dependencies as long as you're only changing Python code!
