# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

VPR-Gym is a platform for exploring AI techniques in FPGA placement optimization. It connects OpenAI Gym with the Verilog to Routing (VTR) project to enable reinforcement learning research for FPGA placement, bridging Python-based ML libraries with VTR's C++ codebase.

## Build System

### Initial Setup

```bash
# Install system dependencies
./install_apt_packages.sh

# Create and activate virtual environment
make env
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Build VTR (C++ components)
make
```

### Build Commands

- `make` - Default release build (uses gcc-9 and g++-9 via CMake)
- `make BUILD_TYPE=debug` - Debug build with symbols
- `make BUILD_TYPE=release_pgo` - Profile-guided optimization (2-stage build)
- `make clean` - Clean build artifacts
- `make distclean` - Clean everything including CMake generated files

The Makefile is a wrapper around CMake. Build output goes to `build/` directory by default.

### Testing

- `./run_quick_test.py` - Quick validation tests
- `./run_reg_test.py` - Full regression test suite
- `./run_reg_test.py pgo_profile` - Generate profiling data for PGO builds

## Architecture

### Two-Tier Communication System

VPR-Gym uses a client-server architecture with ZeroMQ for communication:

1. **Python Client (VprGym/)**: OpenAI Gym environment that RL agents interact with
2. **C++ Server (vpr/)**: VPR placer modified to accept external move decisions via ZeroMQ

The Python client spawns a VPR process and communicates via ZeroMQ sockets on configurable ports (default: 5555).

### Key Components

#### Python Layer (VprGym/)

- `VprGym/src/vprGym.py`: Core Gym environments
  - `VprEnv`: Basic environment where actions are directed move types (integers 0 to num_actions-1)
  - `VprEnv_blk_type`: Extended environment where actions are tuples [move_type, block_type]
- `VprGym/src/reader.py`: Parses VPR log files to extract metrics (WL, CPD, runtime, swaps)
- `VprGym/example.py`: Basic single-environment example
- `VprGym/blocktype_example.py`: Block-type-aware environment example

#### C++ Layer (vpr/src/place/)

- `simpleRL_move_generator.cpp`: Main RL integration point
  - `RLGymGenerator`: Receives actions from Python via ZeroMQ, translates to VPR moves
  - `SimpleRLMoveGenerator`: Built-in k-armed bandit agents (Epsilon-Greedy, Softmax, UCB, EXP3, etc.)
- `RL_agent_util.cpp/h`: Factory functions for creating move generators
- Move generator classes: `UniformMoveGenerator`, `MedianMoveGenerator`, `CentroidMoveGenerator`, `WeightedCentroidMoveGenerator`, `WeightedMedianMoveGenerator`, `CriticalUniformMoveGenerator`, `FeasibleRegionMoveGenerator`

### Two-Stage Placement Process

VPR placement operates in two stages with different available move types:

1. **Stage 1**: Initial placement with 4 move types
2. **Stage 2**: Refinement with 7 move types (includes critical path and feasible region moves)

The Python environment signals stage transitions via `info == 'stage2'`, requiring agents to be reset or adapted.

### Communication Protocol

The ZeroMQ protocol exchanges:

- **Initialization**: VPR sends num_actions, num_types, horizon, num_blks (blocks per type)
- **Action Request**: Python sends action index (or [action, block_type] tuple)
- **Response**: VPR sends one of:
  - `"end"` - Placement complete
  - `"reset"` - Agent should reset
  - `"stage2"` - Transition to stage 2
  - `"<reward> <delta> <delta_bb> <delta_time>"` - Reward and cost deltas

### Reward Functions

Configurable via `reward_func` parameter in VprEnv:
- `"basic"` - Simple reward based on cost improvement
- `"WLbiased_runtime_aware"` (default) - Balances wire length and runtime
- `"runtime_aware"` - Normalizes by move execution time

## Working with VPR-Gym

### Running an RL Experiment

Always run from the `VprGym/` directory as the working directory:

```bash
cd ./VprGym
python3 example.py
```

### Parallel Environments

To run multiple environments in parallel, assign different port numbers to avoid conflicts:

```python
env1 = VprEnv(port='5555')
env2 = VprEnv_blk_type(port='6666')
```

### Important Parameters

When creating environments:
- `inner_num`: Controls SA inner loop iterations (e.g., 0.1)
- `port`: ZeroMQ port string (must be unique per environment)
- `seed`: Random seed for reproducibility
- `arch`: Path to FPGA architecture XML (relative to VTR root)
- `benchmark`: Path to BLIF benchmark file (relative to VTR root)
- `directory`: Working directory for experiment outputs
- `reward_func`: Reward calculation method

### Benchmarks and Architectures

- Architectures: `vtr_flow/arch/` (e.g., `titan/stratixiv_arch.timing.xml`)
- Benchmarks: `vtr_flow/benchmarks/` (blif/, titan_blif/, arithmetic/, etc.)
- Titan benchmarks must be downloaded separately following VTR documentation

### Output Parsing

After placement completes (`done == True`), access results from `info` dict:
- `info['WL']`: Wire length (bounding box estimate)
- `info['CPD']`: Critical path delay
- `info['RT']`: Total runtime
- `info['SWAP']`: Number of swaps performed

During placement, `info` contains normalized deltas:
- `info['delta']`: Normalized total cost change
- `info['delta_bb']`: Normalized bounding box cost change
- `info['delta_time']`: Normalized timing cost change

## C++ VPR Integration

### Enabling RL Gym Mode

VPR must be invoked with specific flags:
- `--RL_gym_placement on` - Enable external RL agent
- `--RL_gym_placement_blk_type on/off` - Enable block-type-aware actions
- `--RL_gym_port <port>` - ZeroMQ port to bind
- `--place_reward_fun <func>` - Reward function selection

These are automatically set by VprEnv when spawning VPR.

### Move Generators

VPR supports 7 directed move types (in Stage 2):
0. Uniform (random)
1. Median
2. Centroid
3. Weighted Centroid
4. Weighted Median
5. Critical Uniform
6. Feasible Region

Stage 1 uses only move types 0-3.

### Built-in Bandit Agents

If not using the Gym interface, VPR includes built-in k-armed bandit agents:
- `EpsilonGreedyAgent`
- `EpsilonDecayAgent`
- `SoftmaxAgent`
- `UCBAgent` (MOSS variant)
- `UCB1_Agent` (Sliding-window UCB)
- `EXP3Agent`
- `UCBCAgent` (Clustered UCB)
- `MOSSAgent`

## Dependencies

Root-level `requirements.txt`:
- prettytable, lxml, psutil
- black==20.8b1, pylint==2.7.4

VprGym-specific `VprGym/requirements.txt`:
- pyzmq (ZeroMQ Python bindings)
- gym (OpenAI Gym)

External C++ dependency:
- cppzmq (C++ ZeroMQ bindings) - must be installed separately

## Common Issues

### Port Conflicts

If you see ZeroMQ binding errors, another environment is using that port. Always use unique ports for parallel environments.

### Working Directory

VPR-Gym must be run from the `VprGym/` directory. The code uses relative paths from there to the VTR root.

### Long Timeouts

The environment waits 30 seconds after receiving "end" to allow VPR to flush logs. This is necessary for result parsing.

## File Structure Notes

- C++ source code is in `vpr/src/`
- Python gym interface is in `VprGym/src/`
- Build output goes to `build/`
- Experiment outputs go to directories created under the specified `directory` parameter
- Log files (`vpr_stdout.log`) are written to experiment-specific subdirectories
