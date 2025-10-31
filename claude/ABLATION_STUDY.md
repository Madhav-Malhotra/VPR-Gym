# Ablation Study Guide

This directory contains three agent implementations for comparing FPGA placement strategies.

## Available Agents

### 1. Random Agent (`example.py`)
- **Baseline**: Random action selection
- **Purpose**: Establishes lower bound performance
- **Usage**: `python3 example.py`

### 2. FSM Agent (`fsm_agent.py`)
- **Strategy**: Branch-predictor style finite state machine
- **States**: 4 states per action (Strongly Good, Weakly Good, Weakly Bad, Strongly Bad)
- **Transitions**: Based on reward threshold (2-bit saturating counter logic)
- **Hyperparameters**:
  - `reward_threshold`: Threshold for good/bad classification (default: 0.0)
  - `exploration_rate`: Random exploration probability (default: 0.1)

**Key Feature**: Maintains "confidence" in each action through state transitions, similar to branch prediction in CPUs.

### 3. Epsilon-Greedy Agent (`epsilon_greedy_agent.py`)
- **Strategy**: Action-value learning with sample averaging
- **Q-values**: Initialize to 0, update with sample average
- **Policy**: ε-greedy (exploit best Q-value with probability 1-ε, explore randomly with probability ε)
- **Hyperparameters**:
  - `epsilon`: Exploration probability (default: 0.1)

**Key Feature**: Simple and interpretable Q-learning baseline.

## Running Individual Experiments

### Using Docker (Recommended)

```bash
# Random agent
./run_docker.sh example.py

# FSM agent
./run_docker.sh fsm_agent.py

# Epsilon-greedy agent
./run_docker.sh epsilon_greedy_agent.py
```

### Running in Parallel (Faster)

Since each agent uses a different port, you can run them simultaneously:

```bash
# Terminal 1
./run_docker.sh -D example.py

# Terminal 2
./run_docker.sh -D fsm_agent.py

# Terminal 3
./run_docker.sh -D epsilon_greedy_agent.py
```

Monitor with:
```bash
docker ps -f name=vpr-gym
docker logs -f vpr-gym-{timestamp}
```

## Output Files

Each agent creates timestamped logs with detailed information:

### FSM Agent Logs (`fsm_results/fsm_log_{timestamp}.json`)
```json
{
  "config": {
    "reward_threshold": 0.0,
    "exploration_rate": 0.1,
    ...
  },
  "stages": [
    {
      "stage": 1,
      "steps": [...],
      "final_statistics": {
        "states": {"0": "SG", "1": "WG", ...},
        "action_counts": [...],
        "avg_rewards": [...]
      }
    }
  ],
  "state_transitions": [...],
  "results": {
    "wire_length": 12345,
    "critical_path_delay": 1.234,
    ...
  }
}
```

### Epsilon-Greedy Logs (`epsilon_greedy_results/epsilon_greedy_log_{timestamp}.json`)
```json
{
  "config": {
    "epsilon": 0.1,
    ...
  },
  "stages": [
    {
      "stage": 1,
      "steps": [...],
      "final_statistics": {
        "Q_values": [0.123, 0.456, ...],
        "action_counts": [...],
        "avg_rewards": [...],
        "std_rewards": [...],
        "exploration_rate": 0.098
      }
    }
  ],
  "reward_analysis": {
    "mean": 0.00123,
    "std": 0.0456,
    "percentiles": {...}
  },
  "results": {...}
}
```

## Analyzing Results

### Quick Comparison

```bash
# View FSM results
cat fsm_results/fsm_log_*.json | jq '.results'

# View Epsilon-Greedy results
cat epsilon_greedy_results/epsilon_greedy_log_*.json | jq '.results'

# Compare wire lengths
echo "FSM:" && cat fsm_results/fsm_log_*.json | jq '.results.wire_length'
echo "Epsilon-Greedy:" && cat epsilon_greedy_results/epsilon_greedy_log_*.json | jq '.results.wire_length'
```

### Using the Analysis Script

```bash
# Analyze all logs in ablation_results/
python3 run_ablation_study.py analyze
```

Output:
```
=== Performance Comparison ===

FSM:
  Run 1:
    Wire Length: 12345
    Critical Path Delay: 1.234
    Runtime: 56.78
    Total Swaps: 9012

Epsilon-Greedy:
  Run 1:
    Wire Length: 11987
    Critical Path Delay: 1.198
    Runtime: 54.32
    Total Swaps: 8765
    Reward Mean: 0.001234
    Reward Std: 0.045678
```

## Tuning Hyperparameters

### Finding the Right Reward Threshold (FSM Agent)

The reward distribution is logged by the epsilon-greedy agent. Use these statistics:

```python
# From epsilon_greedy_log.json
{
  "reward_analysis": {
    "mean": 0.00123,
    "median": 0.00087,
    "percentiles": {
      "50": 0.00087,  # Use as threshold for FSM
      "75": 0.00234,
      "90": 0.00456
    }
  }
}
```

**Recommendation**: Set FSM `reward_threshold` to median or 50th percentile from epsilon-greedy runs.

### Modifying Agent Parameters

Edit the agent files directly:

**FSM Agent:**
```python
# In fsm_agent.py, at bottom:
if __name__ == '__main__':
    run_fsm_experiment(
        reward_threshold=0.001,  # Adjust based on reward distribution
        exploration_rate=0.05,   # Try different exploration rates
        output_dir='fsm_results'
    )
```

**Epsilon-Greedy Agent:**
```python
# In epsilon_greedy_agent.py, at bottom:
if __name__ == '__main__':
    run_epsilon_greedy_experiment(
        epsilon=0.2,  # Try 0.05, 0.1, 0.2, 0.3
        output_dir='epsilon_greedy_results'
    )
```

## Benchmarks

The agents default to a small benchmark. To test on different circuits:

```python
# Edit the agent file or create a new script:
from fsm_agent import run_fsm_experiment

run_fsm_experiment(
    benchmark='vtr_flow/benchmarks/blif/different_benchmark.blif',
    arch='vtr_flow/arch/titan/stratixiv_arch.timing.xml',
    # ... other params
)
```

Available benchmarks:
- Small: `vtr_flow/benchmarks/blif/*.blif`
- Large (Titan): `vtr_flow/benchmarks/titan_blif/*.blif`

## Experiment Workflow

1. **Baseline**: Run random agent to establish baseline
   ```bash
   ./run_docker.sh -D example.py
   ```

2. **Explore Rewards**: Run epsilon-greedy to understand reward distribution
   ```bash
   ./run_docker.sh -D epsilon_greedy_agent.py
   cat epsilon_greedy_results/epsilon_greedy_log_*.json | jq '.reward_analysis'
   ```

3. **Tune FSM**: Use reward statistics to set FSM threshold
   ```bash
   # Edit fsm_agent.py to set reward_threshold based on step 2
   ./run_docker.sh -D fsm_agent.py
   ```

4. **Compare**: Analyze results
   ```bash
   python3 run_ablation_study.py analyze
   ```

5. **Iterate**: Adjust hyperparameters and repeat

## Common Issues

### Port Already in Use
Each agent defaults to port 5555. For parallel runs, edit the port in each script:
```python
env = VprEnv(port='5556', ...)  # Use different port
```

### Out of Memory
Large Titan benchmarks may require more memory. Start with small benchmarks:
```python
benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif'
```

### Long Runtime
Titan benchmarks can take 30-60 minutes per experiment. Use detached mode:
```bash
./run_docker.sh -D fsm_agent.py
```

## Next Steps

After comparing these simple agents, you can:

1. **Add RL agents**: Implement DQN, PPO, or other deep RL methods
2. **Try different benchmarks**: Test on various circuit sizes
3. **Tune hyperparameters**: Grid search over epsilon, thresholds, etc.
4. **Add features**: Use state information (delta_bb, delta_time) as input
5. **Compare with built-in agents**: VPR has UCB, Softmax, and other bandits built-in

## References

- VPR-Gym paper for reward functions and environment details
- OpenAI Gym documentation for environment interface
- Sutton & Barto "Reinforcement Learning: An Introduction" for action-value methods
