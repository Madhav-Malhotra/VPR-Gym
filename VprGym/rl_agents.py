"""
RL Agent Classes

Configurable action-value agents for VPR placement experiments.
"""

import numpy as np
from numpy.random import randint


class ActionValueAgent:
    """
    Configurable action-value agent.

    Supports:
    - Policies: 'epsilon_greedy' or 'softmax'
    - Averaging: 'sample' or 'exponential'
    """

    def __init__(self, num_actions, policy='epsilon_greedy', averaging='sample',
                 epsilon=0.1, temperature=1.0, alpha=0.1):
        """
        Initialize action-value agent.

        Args:
            num_actions: Number of available actions
            policy: 'epsilon_greedy' or 'softmax'
            averaging: 'sample' (sample average) or 'exponential' (exponential weighted average)
            epsilon: Exploration parameter for epsilon-greedy (default 0.1)
            temperature: Temperature parameter for softmax (default 1.0)
            alpha: Step size for exponential averaging (default 0.1)
        """
        self.num_actions = num_actions
        self.policy = policy
        self.averaging = averaging
        self.epsilon = epsilon
        self.temperature = temperature
        self.alpha = alpha

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

    def select_action(self):
        """Select action based on policy."""
        self.step_count += 1

        if self.policy == 'epsilon_greedy':
            # Epsilon-greedy selection
            if np.random.random() < self.epsilon:
                # Exploration: random action
                action = randint(self.num_actions)
            else:
                # Exploitation: greedy action (max Q-value)
                max_q = np.max(self.Q)
                best_actions = np.where(self.Q == max_q)[0]
                action = np.random.choice(best_actions)

        elif self.policy == 'softmax':
            # Softmax (Boltzmann) selection
            # Normalize Q-values to prevent overflow
            q_normalized = self.Q - np.max(self.Q)
            exp_q = np.exp(q_normalized / self.temperature)
            probs = exp_q / np.sum(exp_q)
            action = np.random.choice(self.num_actions, p=probs)

        else:
            raise ValueError(f"Unknown policy: {self.policy}")

        return action

    def update(self, action, reward):
        """Update Q-value based on averaging method."""
        # Increment action count
        self.action_counts[action] += 1

        if self.averaging == 'sample':
            # Sample average: Q(a) = sum of rewards / count
            self.reward_sums[action] += reward
            self.Q[action] = self.reward_sums[action] / self.action_counts[action]

        elif self.averaging == 'exponential':
            # Exponential weighted average: Q(a) = Q(a) + α[R - Q(a)]
            self.Q[action] = self.Q[action] + self.alpha * (reward - self.Q[action])

        else:
            raise ValueError(f"Unknown averaging method: {self.averaging}")

        # Store complete reward history
        self.action_rewards[action].append(reward)

    def get_statistics(self):
        """Get current agent statistics."""
        stats = {
            "Q_values": self.Q.tolist(),
            "action_counts": self.action_counts.tolist(),
            "reward_sums": self.reward_sums.tolist(),
            "avg_rewards": [np.mean(r) if r else 0.0 for r in self.action_rewards],
            "std_rewards": [np.std(r) if r else 0.0 for r in self.action_rewards],
            "total_steps": self.step_count,
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
        self.Q[: len(old_Q)] = old_Q
        self.action_counts[: len(old_counts)] = old_counts
        self.reward_sums[: len(old_sums)] = old_sums

        # Extend reward history
        if new_num_actions > len(self.action_rewards):
            self.action_rewards.extend(
                [[] for _ in range(new_num_actions - len(self.action_rewards))]
            )