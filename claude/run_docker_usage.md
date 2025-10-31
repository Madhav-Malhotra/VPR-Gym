# Enhanced run_docker.sh Script

## Overview

The `run_docker.sh` script has been enhanced to support running specific Python experiments with automatic result management and timestamping.

## Usage

```bash
./run_docker.sh                      # Interactive bash shell (default)
./run_docker.sh my_experiment.py     # Run Python file interactively
./run_docker.sh -D my_experiment.py  # Run in detached background mode
```

## Key Features

### 1. Automatic Timestamped Directories

Every run creates a unique timestamped directory:
```
VprGym/exp/20250131_143522/
├── run.log              # Complete stdout/stderr
└── (other outputs)
```

### 2. Three Modes of Operation

**Mode 1: Interactive Shell (Default)**
```bash
./run_docker.sh
```
- Opens an interactive bash shell in the container
- You can run any commands manually
- Working directory: `/workspace/VprGym`

**Mode 2: Interactive Python Execution**
```bash
./run_docker.sh example.py
```
- Runs your Python script
- Logs all output to `exp/{timestamp}/run.log`
- Drops to bash shell after completion (for debugging)
- Press Ctrl+D to exit when done

**Mode 3: Detached Background Execution**
```bash
./run_docker.sh -D example.py
```
- Runs experiment in background
- Returns immediately
- Monitor with: `docker logs -f vpr-gym-{timestamp}`
- Perfect for long-running experiments

### 3. Automatic Result Collection

All data is automatically available on your host machine because the script uses Docker volume mounts:

```bash
-v "$(pwd)/VprGym:/workspace/VprGym"
```

**This means:**
- No manual copying needed!
- Files written inside the container to `/workspace/VprGym/` appear instantly in your local `VprGym/` directory
- Results persist even after container exits

## Examples

### Example 1: Quick Test
```bash
# Run the example script interactively
./run_docker.sh example.py

# After it finishes, explore results
ls VprGym/exp/20250131_143522/
cat VprGym/exp/20250131_143522/run.log
```

### Example 2: Background Experiment
```bash
# Start experiment
./run_docker.sh -D my_long_experiment.py

# Output shows:
# Starting experiment in detached mode...
# Container name: vpr-gym-20250131_143522
# Results will be saved to: ./VprGym/exp/20250131_143522

# Monitor progress
docker logs -f vpr-gym-20250131_143522

# Check if still running
docker ps -f name=vpr-gym

# Results are already on your machine!
ls VprGym/exp/20250131_143522/
```

### Example 3: Multiple Parallel Experiments
```bash
# Start 3 experiments in parallel
./run_docker.sh -D experiment_lr001.py
./run_docker.sh -D experiment_lr01.py
./run_docker.sh -D experiment_lr1.py

# Each gets unique container and directory:
# vpr-gym-20250131_143522 → VprGym/exp/20250131_143522/
# vpr-gym-20250131_143523 → VprGym/exp/20250131_143523/
# vpr-gym-20250131_143524 → VprGym/exp/20250131_143524/

# Check all running experiments
docker ps -f name=vpr-gym
```

## Understanding Data Flow

### What Happens Inside the Container

When your Python script runs:

```python
env = VprEnv(
    directory='my_results',  # Creates work directory
    ...
)
```

VPR creates: `/workspace/VprGym/my_results/seed_0_inner_num_0.1_.../`

### What You See on Your Host

Because of the volume mount, you immediately see:
```
./VprGym/my_results/seed_0_inner_num_0.1_.../
├── vpr_stdout.log
├── placement.place
└── (other VPR outputs)
```

**Plus** the script adds:
```
./VprGym/exp/20250131_143522/
└── run.log  # Complete Python output
```

### No Manual Copying Required!

The volume mount creates a **bidirectional sync**:
- Changes in container → instantly visible on host
- Changes on host → instantly visible in container
- Files persist after container exits (container uses `--rm` but volumes remain)

## Technical Details

### Volume Mounting Explanation

```bash
-v "$(pwd)/VprGym:/workspace/VprGym"
```

This creates a **bind mount**:
- **Host path**: `$(pwd)/VprGym` (your local directory)
- **Container path**: `/workspace/VprGym` (inside container)
- **Effect**: They are the SAME filesystem location

**Not a copy, but a direct mount!**

When the container writes to `/workspace/VprGym/exp/{timestamp}/run.log`, it's directly writing to your local disk at `./VprGym/exp/{timestamp}/run.log`.

### Why This Works

1. **Docker Volume Mount**: Creates shared filesystem view
2. **Working Directory**: `-w /workspace/VprGym` ensures scripts run from correct location
3. **Relative Paths**: Your Python scripts use relative paths like `directory='my_results'`
4. **Result**: Everything lands in the mounted directory, visible on both sides

### Comparison with Copying

**Old way (manual copy):**
```bash
# Run experiment
docker run ... my_script.py

# Container creates: /some/container/path/results/
# You need: docker cp container:/some/container/path/results/ ./local/
```

**New way (volume mount):**
```bash
# Run experiment
./run_docker.sh my_script.py

# Container writes: /workspace/VprGym/exp/.../
# You see: ./VprGym/exp/.../  (automatically, in real-time!)
```

## Directory Structure After Running

```
VPR-Gym/
├── VprGym/
│   ├── exp/                           # Timestamped experiment logs
│   │   ├── 20250131_143522/
│   │   │   └── run.log
│   │   ├── 20250131_143545/
│   │   │   └── run.log
│   │   └── ...
│   ├── my_results/                    # VPR work directories (from your script)
│   │   └── seed_0_inner_num_0.1_.../
│   │       ├── vpr_stdout.log
│   │       └── ...
│   ├── example.py
│   └── my_experiment.py
└── run_docker.sh
```

## Troubleshooting

### File Permission Issues

If you see permission errors:
```bash
# Run container as your user
docker run -it --rm \
  -u $(id -u):$(id -g) \
  -v "$(pwd)/VprGym:/workspace/VprGym" \
  ...
```

### Results Not Appearing

Check the mount is correct:
```bash
# Inside container, check mount
docker run -it --rm -v "$(pwd)/VprGym:/workspace/VprGym" vpr-gym ls -la /workspace/VprGym
```

Should show your local files.

### Cannot Find Python File

The script looks for: `VprGym/{your_file}.py`

```bash
# Wrong (won't find it)
./run_docker.sh /full/path/to/VprGym/my_experiment.py

# Correct (relative to VprGym/)
./run_docker.sh my_experiment.py

# Also correct (if in subdirectory)
./run_docker.sh experiments/my_experiment.py
```

## Summary

**Key Innovation**: Volume mounts eliminate the need for manual data copying. Files written in the container are instantly available on your host machine because they share the same underlying filesystem location. The script enhances this with automatic timestamping and logging for easy experiment tracking.
