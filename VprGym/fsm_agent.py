"""
FSM Agent - Branch History Predictor Style

Similar to a branch history predictor with strongly/weakly taken states:
- Each action has 4 states: Strongly Good (SG), Weakly Good (WG), Weakly Bad (WB), Strongly Bad (SB)
- Transitions occur based on reward threshold
- Selects action with highest confidence (most "good" state)
"""

import numpy as np
from numpy.random import randint
from src.vprGym import VprEnv
import json
import time
from pathlib import Path


class FSMAgent:
    """
    Finite State Machine agent with 4-state predictor per action.

    State transitions (using 2-bit saturating counter analogy):
    - Strongly Good (3) -> Weakly Good (2) if reward < threshold
    - Weakly Good (2) -> Strongly Good (3) if reward >= threshold
    - Weakly Good (2) -> Weakly Bad (1) if reward < threshold
    - Weakly Bad (1) -> Weakly Good (2) if reward >= threshold
    - Weakly Bad (1) -> Strongly Bad (0) if reward < threshold
    - Strongly Bad (0) -> Weakly Bad (1) if reward >= threshold
    """

    # State definitions
    STRONGLY_BAD = 0
    WEAKLY_BAD = 1
    WEAKLY_GOOD = 2
    STRONGLY_GOOD = 3

    STATE_NAMES = ['SB', 'WB', 'WG', 'SG']

    def __init__(self, num_actions, reward_threshold=0.0, exploration_rate=0.1):
        """
        Initialize FSM agent.

        Args:
            num_actions: Number of available actions
            reward_threshold: Threshold for state transitions (positive reward = good)
            exploration_rate: Probability of random exploration (like epsilon)
        """
        self.num_actions = num_actions
        self.reward_threshold = reward_threshold
        self.exploration_rate = exploration_rate

        # Initialize all actions to Weakly Good (neutral starting point)
        self.states = np.full(num_actions, self.WEAKLY_GOOD, dtype=int)

        # Statistics tracking
        self.action_counts = np.zeros(num_actions, dtype=int)
        self.action_rewards = [[] for _ in range(num_actions)]
        self.state_history = []  # Track state transitions
        self.step_count = 0

    def select_action(self):
        """Select action based on FSM states with exploration."""
        self.step_count += 1

        # Exploration: random action
        if np.random.random() < self.exploration_rate:
            action = randint(self.num_actions)
            return action, True  # True = was exploration

        # Exploitation: select action with best state
        # Among actions with same state, choose randomly to break ties
        best_state = np.max(self.states)
        best_actions = np.where(self.states == best_state)[0]
        action = np.random.choice(best_actions)

        return action, False  # False = was exploitation

    def update(self, action, reward):
        """Update FSM state based on reward."""
        old_state = self.states[action]

        # State transition logic (2-bit saturating counter)
        if reward >= self.reward_threshold:
            # Good reward: move toward Strongly Good
            self.states[action] = min(self.STRONGLY_GOOD, old_state + 1)
        else:
            # Bad reward: move toward Strongly Bad
            self.states[action] = max(self.STRONGLY_BAD, old_state - 1)

        new_state = self.states[action]

        # Track statistics
        self.action_counts[action] += 1
        self.action_rewards[action].append(reward)

        # Log state transition
        self.state_history.append({
            'step': self.step_count,
            'action': int(action),
            'reward': float(reward),
            'old_state': int(old_state),
            'new_state': int(new_state),
            'old_state_name': self.STATE_NAMES[old_state],
            'new_state_name': self.STATE_NAMES[new_state]
        })

    def get_statistics(self):
        """Get current agent statistics."""
        stats = {
            'states': {i: self.STATE_NAMES[s] for i, s in enumerate(self.states)},
            'action_counts': self.action_counts.tolist(),
            'avg_rewards': [np.mean(r) if r else 0.0 for r in self.action_rewards],
            'total_steps': self.step_count
        }
        return stats

    def reset_for_stage2(self, new_num_actions):
        """Reset agent for stage 2 with different number of actions."""
        # Preserve states for actions that exist in both stages
        old_states = self.states[:new_num_actions].copy()

        self.num_actions = new_num_actions
        self.states = np.full(new_num_actions, self.WEAKLY_GOOD, dtype=int)
        self.states[:len(old_states)] = old_states

        # Extend tracking arrays
        if new_num_actions > len(self.action_counts):
            self.action_counts = np.pad(self.action_counts,
                                        (0, new_num_actions - len(self.action_counts)))
            self.action_rewards.extend([[] for _ in range(new_num_actions - len(self.action_rewards))])


def run_fsm_experiment(
    inner_num=0.1,
    port='5555',
    seed=0,
    arch='vtr_flow/arch/titan/stratixiv_arch.timing.xml',
    benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif',
    reward_func='WLbiased_runtime_aware',
    reward_threshold=0.0,
    exploration_rate=0.1,
    output_dir='fsm_results'
):
    """Run FSM agent experiment."""

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Setup logging
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    log_file = output_path / f'fsm_log_{timestamp}.json'

    print(f"=== FSM Agent Experiment ===")
    print(f"Reward Threshold: {reward_threshold}")
    print(f"Exploration Rate: {exploration_rate}")
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
    agent = FSMAgent(
        num_actions=env.num_actions,
        reward_threshold=reward_threshold,
        exploration_rate=exploration_rate
    )

    # Experiment tracking
    episode_log = {
        'config': {
            'reward_threshold': reward_threshold,
            'exploration_rate': exploration_rate,
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

            # Log step
            step_data = {
                'step': step,
                'action': int(action),
                'reward': float(reward),
                'exploration': was_exploration,
                'delta': float(info['delta']),
                'delta_bb': float(info['delta_bb']),
                'delta_time': float(info['delta_time'])
            }
            stage_data['steps'].append(step_data)

            # Print progress every 100 steps
            if step % 100 == 0:
                stats = agent.get_statistics()
                print(f"Step {step}: Action {action}, Reward {reward:.6f}")
                print(f"  States: {stats['states']}")

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

    # Add state transition history
    episode_log['state_transitions'] = agent.state_history

    # Save complete log
    with open(log_file, 'w') as f:
        json.dump(episode_log, f, indent=2)

    print(f"Log saved to: {log_file}")

    # Print final statistics
    print("\n=== Final Agent Statistics ===")
    for stage_data in episode_log['stages']:
        print(f"\nStage {stage_data['stage']}:")
        stats = stage_data['final_statistics']
        print(f"  States: {stats['states']}")
        print(f"  Action counts: {stats['action_counts']}")
        print(f"  Avg rewards: {[f'{r:.6f}' for r in stats['avg_rewards']]}")

    return episode_log


if __name__ == '__main__':
    # Default experiment - you can modify these parameters
    run_fsm_experiment(
        reward_threshold=0.0,  # Tune this based on reward distribution
        exploration_rate=0.1,   # 10% random exploration
        output_dir='fsm_results'
    )
