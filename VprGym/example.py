"""
Random Agent - Baseline for Ablation Study

Selects actions uniformly at random without learning.
Provides baseline performance for comparison with learning agents.
"""

import numpy as np
from numpy.random import randint
from src.vprGym import VprEnv, VprEnv_blk_type
import json
import csv
import time
from pathlib import Path
import os


def run_random_experiment(
    inner_num=0.1,
    port="5555",
    seed=0,
    arch="vtr_flow/arch/titan/stratixiv_arch.timing.xml",
    benchmark="vtr_flow/benchmarks/titan_blif/stereo_vision_stratixiv_arch_timing.blif",
    reward_func="WLbiased_runtime_aware",
    output_dir=None,
    print_steps=1000,
    log_steps=2,
    timeout=None,
    target_wl=None,
    target_cpd=None,
):
    """Run random agent experiment with comprehensive logging.

    Args:
        timeout: Time budget in seconds (None = no limit)
        target_wl: Target wire length to reach (None = no target)
        target_cpd: Target critical path delay to reach (None = no target)
    """

    # Setup logging with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # Create output directory structure: exp/{timestamp}/random/
    if output_dir is None:
        output_path = Path(f"exp/{timestamp}/random")
    else:
        output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"=== Random Agent Experiment ===")
    print(f"Benchmark: {benchmark}")
    print()

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

    # Experiment tracking
    episode_log = {
        "config": {
            "agent": "random",
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
    print("CSV file opened successfully.")

    csv_writer = csv.DictWriter(
        csv_file_handle,
        fieldnames=[
            "stage",
            "step",
            "action",
            "reward",
            "delta",
            "delta_bb",
            "delta_time",
            "wire_len",
            "crit_path_del",
        ],
    )
    csv_writer.writeheader()

    stage = 1
    stage_data = {"stage": stage, "num_actions": env.num_actions, "steps": []}

    num_actions = env.num_actions
    avail_arms = list(np.arange(env.num_actions))
    done = False
    step = 0

    # Track statistics
    all_rewards = []
    action_counts = np.zeros(num_actions, dtype=int)

    # Start timer for timeout mode
    experiment_start_time = time.time()

    print("Starting placement...")

    # done indicates whether the RL process is terminated or not
    while not done:
        # Check timeout
        if timeout is not None and (time.time() - experiment_start_time) > timeout:
            print(f"\nTimeout reached ({timeout}s), terminating experiment...")
            episode_log["termination_reason"] = "timeout"
            break
        # Provide an action from agent
        action = avail_arms[randint(num_actions)]
        _, reward, done, info = env.step(action)

        # Track action selection
        action_counts[action] += 1

        # Note that VPR Placement is a two-stage process
        # The number of action will change as the stage changes
        if isinstance(info, dict) and "delta" in info:
            # Normal step with reward
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
                        "delta_bb": float(info["delta_bb"]),
                        "delta_time": float(info["delta_time"]),
                        "wire_len": float(info.get("WL", 0.0)),
                        "crit_path_del": float(info.get("CPD", 0.0)),
                    }
                )

            # Print progress
            if step % print_steps == 0:
                print(f"Step {step}: Action {action}, Reward {reward:.6f}")
                print(f"  Action distribution: {action_counts.tolist()}")

        elif info == "stage2":
            # Stage transition
            print(f"\n=== Transitioning to Stage 2 ===")
            print(f"Stage 1 completed: {step} steps")

            # Save stage 1 statistics
            stage_data["statistics"] = {
                "action_counts": action_counts.tolist(),
                "avg_reward": float(np.mean(all_rewards)) if all_rewards else 0.0,
                "std_reward": float(np.std(all_rewards)) if all_rewards else 0.0,
            }
            episode_log["stages"].append(stage_data)

            # Reset for stage 2
            num_actions = env.num_actions
            avail_arms = list(np.arange(env.num_actions))
            action_counts = np.zeros(num_actions, dtype=int)

            stage = 2
            stage_data = {"stage": stage, "num_actions": env.num_actions, "steps": []}

            print(f"Stage 2: {env.num_actions} actions available")
            print()

        elif info == "reset":
            # Agent reset
            print("Environment reset signal")

    # Close CSV file
    csv_file_handle.close()

    # Save final stage data
    stage_data["statistics"] = {
        "action_counts": action_counts.tolist(),
        "avg_reward": float(np.mean(all_rewards)) if all_rewards else 0.0,
        "std_reward": float(np.std(all_rewards)) if all_rewards else 0.0,
    }
    episode_log["stages"].append(stage_data)

    # Final results
    print("\n=== Experiment Complete ===")
    print()

    # Add results to log
    try:
        episode_log["results"] = {
            "wire_length": info["WL"],
            "critical_path_delay": info["CPD"],
            "runtime": info["RT"],
            "total_swaps": info["SWAP"],
        }
    except Exception as e:
        print("ERROR: coult not access final info: ", e)
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
    }

    # Save complete log
    with open(log_file, "w") as f:
        json.dump(episode_log, f, indent=2)

    print(f"JSON log saved to: {log_file}")
    print(f"CSV log saved to: {csv_file}")

    # Print final statistics
    print("\n=== Final Statistics ===")
    for stage_data in episode_log["stages"]:
        print(f"\nStage {stage_data['stage']}:")
        stats = stage_data["statistics"]
        print(f"  Action counts: {stats['action_counts']}")
        print(f"  Avg reward: {stats['avg_reward']:.6f}")
        print(f"  Std reward: {stats['std_reward']:.6f}")

    print("\n=== Reward Distribution ===")
    print(f"Mean: {episode_log['reward_analysis']['mean']:.6f}")
    print(f"Std: {episode_log['reward_analysis']['std']:.6f}")
    print(f"Min: {episode_log['reward_analysis']['min']:.6f}")
    print(f"Max: {episode_log['reward_analysis']['max']:.6f}")
    print(f"Median: {episode_log['reward_analysis']['median']:.6f}")

    # Revert to base directory
    os.chdir(prior_path)

    return episode_log


if __name__ == "__main__":
    # Default experiment - you can modify these parameters
    run_random_experiment()
