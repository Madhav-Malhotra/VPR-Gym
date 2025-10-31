"""
Epsilon-Greedy Action-Value Agent

Simple Q-learning style agent with:
- Action-value estimates (Q-values) initialized to 0
- Sample average for updating Q-values
- Epsilon-greedy policy for action selection
"""

import numpy as np
from numpy.random import randint
from src.vprGym import VprEnv
import json
import time
from pathlib import Path


class EpsilonGreedyAgent:
    """
    Simple action-value agent with epsilon-greedy policy.

    Uses sample average to estimate action values:
    Q(a) = average of rewards received when action a was taken
    """

    def __init__(self, num_actions, epsilon=0.1):
        """
        Initialize epsilon-greedy agent.

        Args:
            num_actions: Number of available actions
            epsilon: Probability of taking random action (exploration)
        """
        self.num_actions = num_actions
        self.epsilon = epsilon

        # Action-value estimates (Q-values) - initialized to 0
        self.Q = np.zeros(num_actions, dtype=float)

        # Track number of times each action was selected
        self.action_counts = np.zeros(num_actions, dtype=int)

        # Track sum of rewards for each action (for sample average)
        self.reward_sums = np.zeros(num_actions, dtype=float)

        # Complete reward history for analysis
        self.action_rewards = [[] for _ in range(num_actions)]

        # Step tracking
        self.step_count = 0
        self.exploration_count = 0
        self.exploitation_count = 0

    def select_action(self):
        """Select action using epsilon-greedy policy."""
        self.step_count += 1

        # Epsilon-greedy selection
        if np.random.random() < self.epsilon:
            # Exploration: random action
            action = randint(self.num_actions)
            self.exploration_count += 1
            return action, True  # True = exploration
        else:
            # Exploitation: greedy action (max Q-value)
            # Break ties randomly
            max_q = np.max(self.Q)
            best_actions = np.where(self.Q == max_q)[0]
            action = np.random.choice(best_actions)
            self.exploitation_count += 1
            return action, False  # False = exploitation

    def update(self, action, reward):
        """Update Q-value using sample average."""
        # Increment action count
        self.action_counts[action] += 1

        # Update reward sum
        self.reward_sums[action] += reward

        # Update Q-value (sample average)
        self.Q[action] = self.reward_sums[action] / self.action_counts[action]

        # Store complete reward history
        self.action_rewards[action].append(reward)

    def get_statistics(self):
        """Get current agent statistics."""
        stats = {
            'Q_values': self.Q.tolist(),
            'action_counts': self.action_counts.tolist(),
            'reward_sums': self.reward_sums.tolist(),
            'avg_rewards': [np.mean(r) if r else 0.0 for r in self.action_rewards],
            'std_rewards': [np.std(r) if r else 0.0 for r in self.action_rewards],
            'total_steps': self.step_count,
            'exploration_count': self.exploration_count,
            'exploitation_count': self.exploitation_count,
            'exploration_rate': self.exploration_count / self.step_count if self.step_count > 0 else 0
        }
        return stats

    def reset_for_stage2(self, new_num_actions):
        """Reset agent for stage 2 with different number of actions."""
        # Preserve Q-values for actions that exist in both stages
        old_Q = self.Q[:new_num_actions].copy()
        old_counts = self.action_counts[:new_num_actions].copy()
        old_sums = self.reward_sums[:new_num_actions].copy()

        self.num_actions = new_num_actions

        # Initialize new arrays
        self.Q = np.zeros(new_num_actions, dtype=float)
        self.action_counts = np.zeros(new_num_actions, dtype=int)
        self.reward_sums = np.zeros(new_num_actions, dtype=float)

        # Copy over existing values
        self.Q[:len(old_Q)] = old_Q
        self.action_counts[:len(old_counts)] = old_counts
        self.reward_sums[:len(old_sums)] = old_sums

        # Extend reward history
        if new_num_actions > len(self.action_rewards):
            self.action_rewards.extend([[] for _ in range(new_num_actions - len(self.action_rewards))])


def run_epsilon_greedy_experiment(
    inner_num=0.1,
    port='5555',
    seed=0,
    arch='vtr_flow/arch/titan/stratixiv_arch.timing.xml',
    benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif',
    reward_func='WLbiased_runtime_aware',
    epsilon=0.1,
    output_dir='epsilon_greedy_results'
):
    """Run epsilon-greedy agent experiment."""

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Setup logging
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    log_file = output_path / f'epsilon_greedy_log_{timestamp}.json'

    print(f"=== Epsilon-Greedy Agent Experiment ===")
    print(f"Epsilon: {epsilon}")
    print(f"Benchmark: {benchmark}")
    print(f"Log file: {log_file}")
    print()

    # Create environment
    env = VprEnv(
        inner_num=inner_num,
        port=port,
        seed=seed,
        arch=arch,
        directory=output_dir,
        benchmark=benchmark,
        reward_func=reward_func
    )

    # Create agent
    agent = EpsilonGreedyAgent(
        num_actions=env.num_actions,
        epsilon=epsilon
    )

    # Experiment tracking
    episode_log = {
        'config': {
            'epsilon': epsilon,
            'inner_num': inner_num,
            'seed': seed,
            'benchmark': benchmark,
            'reward_func': reward_func
        },
        'stages': []
    }

    stage = 1
    stage_data = {
        'stage': stage,
        'num_actions': env.num_actions,
        'steps': []
    }

    done = False
    step = 0

    # Track reward statistics for finding good epsilon
    all_rewards = []

    print("Starting placement...")

    while not done:
        # Select action
        action, was_exploration = agent.select_action()

        # Take action in environment
        _, reward, done, info = env.step(action)

        # Update agent
        if isinstance(info, dict) and 'delta' in info:
            # Normal step with reward
            agent.update(action, reward)

            step += 1
            all_rewards.append(reward)

            # Log step
            step_data = {
                'step': step,
                'action': int(action),
                'reward': float(reward),
                'Q_value': float(agent.Q[action]),
                'action_count': int(agent.action_counts[action]),
                'exploration': was_exploration,
                'delta': float(info['delta']),
                'delta_bb': float(info['delta_bb']),
                'delta_time': float(info['delta_time'])
            }
            stage_data['steps'].append(step_data)

            # Print progress every 100 steps
            if step % 100 == 0:
                stats = agent.get_statistics()
                print(f"Step {step}: Action {action}, Reward {reward:.6f}, Q(a)={agent.Q[action]:.6f}")
                print(f"  Exploration rate: {stats['exploration_rate']:.2%}")
                print(f"  Best Q-value: {np.max(agent.Q):.6f} (action {np.argmax(agent.Q)})")
                print(f"  Q-values: {[f'{q:.4f}' for q in agent.Q]}")

        elif info == 'stage2':
            # Stage transition
            print(f"\n=== Transitioning to Stage 2 ===")
            print(f"Stage 1 completed: {step} steps")

            # Save stage 1 data
            stage_data['final_statistics'] = agent.get_statistics()
            episode_log['stages'].append(stage_data)

            # Reset for stage 2
            agent.reset_for_stage2(env.num_actions)

            stage = 2
            stage_data = {
                'stage': stage,
                'num_actions': env.num_actions,
                'steps': []
            }

            print(f"Stage 2: {env.num_actions} actions available")
            print()

        elif info == 'reset':
            # Agent reset
            print("Environment reset signal")

    # Save final stage data
    stage_data['final_statistics'] = agent.get_statistics()
    episode_log['stages'].append(stage_data)

    # Final results
    print("\n=== Experiment Complete ===")
    print(f'Wire Length: {info["WL"]}')
    print(f'Critical Path Delay: {info["CPD"]}')
    print(f'Runtime: {info["RT"]}')
    print(f'Total Swaps: {info["SWAP"]}')
    print()

    # Add results to log
    episode_log['results'] = {
        'wire_length': info['WL'],
        'critical_path_delay': info['CPD'],
        'runtime': info['RT'],
        'total_swaps': info['SWAP']
    }

    # Add reward distribution analysis
    episode_log['reward_analysis'] = {
        'mean': float(np.mean(all_rewards)),
        'std': float(np.std(all_rewards)),
        'min': float(np.min(all_rewards)),
        'max': float(np.max(all_rewards)),
        'median': float(np.median(all_rewards)),
        'percentiles': {
            '25': float(np.percentile(all_rewards, 25)),
            '50': float(np.percentile(all_rewards, 50)),
            '75': float(np.percentile(all_rewards, 75)),
            '90': float(np.percentile(all_rewards, 90)),
            '95': float(np.percentile(all_rewards, 95))
        }
    }

    # Save complete log
    with open(log_file, 'w') as f:
        json.dump(episode_log, f, indent=2)

    print(f"Log saved to: {log_file}")

    # Print final statistics
    print("\n=== Final Agent Statistics ===")
    for stage_data in episode_log['stages']:
        print(f"\nStage {stage_data['stage']}:")
        stats = stage_data['final_statistics']
        print(f"  Q-values: {[f'{q:.6f}' for q in stats['Q_values']]}")
        print(f"  Action counts: {stats['action_counts']}")
        print(f"  Avg rewards: {[f'{r:.6f}' for r in stats['avg_rewards']]}")
        print(f"  Std rewards: {[f'{r:.6f}' for r in stats['std_rewards']]}")
        print(f"  Exploration rate: {stats['exploration_rate']:.2%}")

    # Print reward distribution
    print("\n=== Reward Distribution (for tuning hyperparameters) ===")
    print(f"Mean: {episode_log['reward_analysis']['mean']:.6f}")
    print(f"Std: {episode_log['reward_analysis']['std']:.6f}")
    print(f"Min: {episode_log['reward_analysis']['min']:.6f}")
    print(f"Max: {episode_log['reward_analysis']['max']:.6f}")
    print(f"Median: {episode_log['reward_analysis']['median']:.6f}")
    print(f"Percentiles: {episode_log['reward_analysis']['percentiles']}")

    return episode_log


if __name__ == '__main__':
    # Default experiment - you can modify these parameters
    run_epsilon_greedy_experiment(
        epsilon=0.1,  # 10% exploration
        output_dir='epsilon_greedy_results'
    )
