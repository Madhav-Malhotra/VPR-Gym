"""
Ablation Study Runner

Runs multiple experiments with different agents and configurations
to compare their effectiveness.
"""

import json
import time
from pathlib import Path
import subprocess
import sys


def run_experiment(script_name, experiment_name, port, output_dir):
    """
    Run a single experiment in the current process.

    Args:
        script_name: Python script to run (e.g., 'example.py')
        experiment_name: Name for logging
        port: ZMQ port to use
        output_dir: Base output directory for the ablation study
    """
    print(f"\n{'='*60}")
    print(f"Running: {experiment_name}")
    print(f"Script: {script_name}")
    print(f"Port: {port}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # Import and run the appropriate experiment
    if "example" in script_name:
        # Random agent
        from example import run_random_experiment

        result = run_random_experiment(port=port, output_dir=str(output_dir / "random"))

    elif "fsm" in script_name:
        # FSM agent
        from fsm_agent import run_fsm_experiment

        result = run_fsm_experiment(
            port=port, output_dir=str(output_dir / "fsm"), reward_threshold=0.00001
        )

    elif "epsilon" in script_name:
        # Epsilon-greedy agent
        from epsilon_greedy_agent import run_epsilon_greedy_experiment

        result = run_epsilon_greedy_experiment(
            port=port, output_dir=str(output_dir / "epsilon_greedy")
        )

    else:
        print(f"Unknown script: {script_name}")
        return None

    elapsed_time = time.time() - start_time

    print(f"\n{experiment_name} completed in {elapsed_time:.2f} seconds")

    return {
        "experiment": experiment_name,
        "script": script_name,
        "elapsed_time": elapsed_time,
        "result": result,
    }


def run_ablation_study():
    """
    Run complete ablation study comparing all agents.
    """

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"exp/{timestamp}/ablation_study")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Ablation Study ===")
    print(f"Output directory: {output_dir}")
    print(f"Timestamp: {timestamp}")

    # Define experiments to run
    experiments = [
        {
            "name": "Random Agent",
            "script": "example.py",
            "port": "5555",
            "description": "Baseline: Random action selection",
        },
        {
            "name": "FSM Agent (threshold=0.0)",
            "script": "fsm_agent.py",
            "port": "5556",
            "description": "FSM with branch-predictor style states",
        },
        {
            "name": "Epsilon-Greedy Agent (ε=0.1)",
            "script": "epsilon_greedy_agent.py",
            "port": "5557",
            "description": "Action-value with sample average and ε-greedy",
        },
    ]

    study_results = {"timestamp": timestamp, "experiments": []}

    # Run each experiment sequentially (to avoid port conflicts)
    for exp in experiments:
        print(f"\n\n{'#'*60}")
        print(f"# {exp['name']}")
        print(f"# {exp['description']}")
        print(f"{'#'*60}")

        result = run_experiment(exp["script"], exp["name"], exp["port"], output_dir)

        if result:
            study_results["experiments"].append(result)

            # Save intermediate results
            results_file = output_dir / "ablation_study_results.json"
            with open(results_file, "w") as f:
                json.dump(study_results, f, indent=2)

    # Generate comparison summary
    print(f"\n\n{'='*60}")
    print("ABLATION STUDY COMPLETE")
    print(f"{'='*60}\n")

    print("Experiment Summary:")
    print(f"{'Agent':<30} {'Time (s)':<12} {'Status':<12}")
    print("-" * 60)

    for exp in study_results["experiments"]:
        print(f"{exp['experiment']:<30} {exp['elapsed_time']:<12.2f} {'✓':<12}")

    return study_results


if __name__ == "__main__":
    run_ablation_study()
