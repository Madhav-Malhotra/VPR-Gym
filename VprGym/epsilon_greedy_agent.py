"""
Action-Value Agent Experiments

Runs experiments with configurable RL agents (epsilon-greedy, softmax, etc.)
"""

import numpy as np
from src.vprGym import VprEnv
from rl_agents import ActionValueAgent
import json
import csv
import time
from pathlib import Path
import os


def run_epsilon_greedy_experiment(
    inner_num=0.1,
    port="5555",
    seed=0,
    arch="vtr_flow/arch/titan/stratixiv_arch.timing.xml",
    benchmark="vtr_flow/benchmarks/titan_blif/stereo_vision_stratixiv_arch_timing.blif",
    reward_func="WLbiased_runtime_aware",
    policy='epsilon_greedy',
    averaging='sample',
    epsilon=0.1,
    temperature=1.0,
    alpha=0.1,
    output_dir=None,
    print_steps=1000,
    log_steps=2,
    timeout=None,
    target_wl=None,
    target_cpd=None,
):
    """Run action-value agent experiment.

    Args:
        policy: 'epsilon_greedy' or 'softmax'
        averaging: 'sample' or 'exponential'
        epsilon: For epsilon-greedy policy
        temperature: For softmax policy
        alpha: For exponential averaging
        timeout: Time budget in seconds (None = no limit)
        target_wl: Target wire length to reach (None = no target)
        target_cpd: Target critical path delay to reach (None = no target)
    """

    # Setup logging with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Create output directory structure: exp/{timestamp}/epsilon_greedy/
    if output_dir is None:
        output_path = Path(f"exp/{timestamp}/epsilon_greedy")
    else:
        output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"=== Action-Value Agent Experiment ===")
    print(f"Policy: {policy}, Averaging: {averaging}")

    # Create environment
    prior_path = os.getcwd()
    env = VprEnv(
        inner_num=inner_num,
        port=port,
        seed=seed,
        arch=arch,
        directory=str(output_path),
        benchmark=benchmark,
        reward_func=reward_func,
    )
    log_file = os.path.join(os.getcwd(), "log.json")
    csv_file = os.path.join(os.getcwd(), "log.csv")

    # Create agent
    agent = ActionValueAgent(
        num_actions=env.num_actions,
        policy=policy,
        averaging=averaging,
        epsilon=epsilon,
        temperature=temperature,
        alpha=alpha
    )

    # Experiment tracking
    episode_log = {
        "config": {
            "policy": policy,
            "averaging": averaging,
            "epsilon": epsilon,
            "temperature": temperature,
            "alpha": alpha,
            "inner_num": inner_num,
            "seed": seed,
            "benchmark": benchmark,
            "reward_func": reward_func,
            "timeout": timeout,
            "target_wl": target_wl,
            "target_cpd": target_cpd,
        },
        "stages": [],
    }

    # CSV writer setup
    csv_file_handle = open(csv_file, "w", newline="")
    csv_writer = csv.DictWriter(
        csv_file_handle,
        fieldnames=[
            "stage",
            "step",
            "action",
            "reward",
            "Q_value",
            "action_count",
            "exploration",
            "delta",
            "delta_bb",
            "delta_time",
            "best_action",
            "best_Q",
        ],
    )
    csv_writer.writeheader()

    stage = 1
    stage_data = {"stage": stage, "num_actions": env.num_actions, "steps": []}

    done = False
    step = 0

    # Track reward statistics for finding good epsilon
    all_rewards = []

    # Start timer for timeout mode
    experiment_start_time = time.time()

    print("Starting placement...")

    while not done:
        # Check timeout
        if timeout is not None and (time.time() - experiment_start_time) > timeout:
            print(f"\nTimeout reached ({timeout}s), terminating experiment...")
            episode_log["termination_reason"] = "timeout"
            break
        # Select action
        action = agent.select_action()

        # Take action in environment
        _, reward, done, info = env.step(action)

        # Update agent
        if isinstance(info, dict) and "delta" in info:
            # Normal step with reward
            agent.update(action, reward)

            step += 1
            all_rewards.append(reward)

            # Check target conditions
            if target_wl is not None and "WL" in info and info["WL"] <= target_wl:
                print(f"\nTarget wire length reached: {info['WL']} <= {target_wl}")
                episode_log["termination_reason"] = "target_wl_reached"
                done = True
            elif target_cpd is not None and "CPD" in info and info["CPD"] <= target_cpd:
                print(f"\nTarget CPD reached: {info['CPD']} <= {target_cpd}")
                episode_log["termination_reason"] = "target_cpd_reached"
                done = True

            # Write to CSV
            if step % log_steps == 0:
                csv_writer.writerow(
                    {
                        "stage": stage,
                        "step": step,
                        "action": int(action),
                        "reward": float(reward),
                        "Q_value": float(agent.Q[action]),
                        "action_count": int(agent.action_counts[action]),
                        "delta": float(info["delta"]),
                        "delta_bb": float(info["delta_bb"]),
                        "delta_time": float(info["delta_time"]),
                        "best_action": int(np.argmax(agent.Q)),
                        "best_Q": float(np.max(agent.Q)),
                    }
                )

            # Print progress
            if step % print_steps == 0:
                print(f"Step {step}: Reward {reward:.6f}, Best Q={np.max(agent.Q):.4f}")

        elif info == "stage2":
            # Stage transition
            print(f"\n=== Stage 2: {step} steps completed ===")
            stage_data["final_statistics"] = agent.get_statistics()
            episode_log["stages"].append(stage_data)
            agent.reset_for_stage2(env.num_actions)
            stage = 2
            stage_data = {"stage": stage, "num_actions": env.num_actions, "steps": []}

        elif info == "reset":
            print("Reset signal")

    # Close CSV file
    csv_file_handle.close()

    # Save final stage data
    stage_data["final_statistics"] = agent.get_statistics()
    episode_log["stages"].append(stage_data)

    # Final results
    print("\n=== Experiment Complete ===")
    try:
        print(f'Wire Length: {info["WL"]}')
        print(f'Critical Path Delay: {info["CPD"]}')
        print(f'Runtime: {info["RT"]}')
        print(f'Total Swaps: {info["SWAP"]}')
        print()

        # Add results to log
        episode_log["results"] = {
            "wire_length": info["WL"],
            "critical_path_delay": info["CPD"],
            "runtime": info["RT"],
            "total_swaps": info["SWAP"],
        }
    except Exception as e:
        print("ERROR: could not access final info: ", e)
        episode_log["results"] = {}

    # Add termination info
    if "termination_reason" not in episode_log:
        episode_log["termination_reason"] = "completed"
    episode_log["elapsed_time"] = time.time() - experiment_start_time

    # Add reward distribution analysis
    episode_log["reward_analysis"] = {
        "mean": float(np.mean(all_rewards)) if all_rewards else 0.0,
        "std": float(np.std(all_rewards)) if all_rewards else 0.0,
        "min": float(np.min(all_rewards)) if all_rewards else 0.0,
        "max": float(np.max(all_rewards)) if all_rewards else 0.0,
        "median": float(np.median(all_rewards)) if all_rewards else 0.0,
        "percentiles": {
            "25": float(np.percentile(all_rewards, 25)) if all_rewards else 0.0,
            "50": float(np.percentile(all_rewards, 50)) if all_rewards else 0.0,
            "75": float(np.percentile(all_rewards, 75)) if all_rewards else 0.0,
            "90": float(np.percentile(all_rewards, 90)) if all_rewards else 0.0,
            "95": float(np.percentile(all_rewards, 95)) if all_rewards else 0.0,
        },
    }

    # Save complete log
    with open(log_file, "w") as f:
        json.dump(episode_log, f, indent=2)

    print(f"Logs: {log_file}, {csv_file}")

    # Revert to base working dir
    os.chdir(prior_path)

    return episode_log


if __name__ == "__main__":
    # Default experiment - you can modify these parameters
    run_epsilon_greedy_experiment(epsilon=0.1)  # 10% exploration
