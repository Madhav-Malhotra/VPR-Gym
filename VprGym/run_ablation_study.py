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


def run_experiment(script_name, experiment_name, port):
    """
    Run a single experiment in the current process.

    Args:
        script_name: Python script to run (e.g., 'example.py')
        experiment_name: Name for logging
        port: ZMQ port to use
    """
    print(f"\n{'='*60}")
    print(f"Running: {experiment_name}")
    print(f"Script: {script_name}")
    print(f"Port: {port}")
    print(f"{'='*60}\n")

    start_time = time.time()

    # Import and run the appropriate experiment
    if 'example' in script_name:
        # Random agent
        import example
        result = {'status': 'completed', 'agent': 'random'}

    elif 'fsm' in script_name:
        # FSM agent
        from fsm_agent import run_fsm_experiment
        result = run_fsm_experiment(
            port=port,
            output_dir=f'ablation_results/fsm_{port}'
        )

    elif 'epsilon' in script_name:
        # Epsilon-greedy agent
        from epsilon_greedy_agent import run_epsilon_greedy_experiment
        result = run_epsilon_greedy_experiment(
            port=port,
            output_dir=f'ablation_results/epsilon_greedy_{port}'
        )

    else:
        print(f"Unknown script: {script_name}")
        return None

    elapsed_time = time.time() - start_time

    print(f"\n{experiment_name} completed in {elapsed_time:.2f} seconds")

    return {
        'experiment': experiment_name,
        'script': script_name,
        'elapsed_time': elapsed_time,
        'result': result
    }


def run_ablation_study():
    """
    Run complete ablation study comparing all agents.
    """

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_dir = Path(f'ablation_results/study_{timestamp}')
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Ablation Study ===")
    print(f"Output directory: {output_dir}")
    print(f"Timestamp: {timestamp}")

    # Define experiments to run
    experiments = [
        {
            'name': 'Random Agent',
            'script': 'example.py',
            'port': '5555',
            'description': 'Baseline: Random action selection'
        },
        {
            'name': 'FSM Agent (threshold=0.0)',
            'script': 'fsm_agent.py',
            'port': '5556',
            'description': 'FSM with branch-predictor style states'
        },
        {
            'name': 'Epsilon-Greedy Agent (ε=0.1)',
            'script': 'epsilon_greedy_agent.py',
            'port': '5557',
            'description': 'Action-value with sample average and ε-greedy'
        }
    ]

    study_results = {
        'timestamp': timestamp,
        'experiments': []
    }

    # Run each experiment sequentially (to avoid port conflicts)
    for exp in experiments:
        print(f"\n\n{'#'*60}")
        print(f"# {exp['name']}")
        print(f"# {exp['description']}")
        print(f"{'#'*60}")

        result = run_experiment(exp['script'], exp['name'], exp['port'])

        if result:
            study_results['experiments'].append(result)

            # Save intermediate results
            results_file = output_dir / 'ablation_study_results.json'
            with open(results_file, 'w') as f:
                json.dump(study_results, f, indent=2)

    # Generate comparison summary
    print(f"\n\n{'='*60}")
    print("ABLATION STUDY COMPLETE")
    print(f"{'='*60}\n")

    print("Experiment Summary:")
    print(f"{'Agent':<30} {'Time (s)':<12} {'Status':<12}")
    print("-" * 60)

    for exp in study_results['experiments']:
        print(f"{exp['experiment']:<30} {exp['elapsed_time']:<12.2f} {'✓':<12}")

    print(f"\nResults saved to: {results_file}")

    return study_results


def run_parallel_comparison(benchmark='vtr_flow/benchmarks/blif/mkDelayWorker32B.blif'):
    """
    Run all three agents in parallel on the same benchmark for direct comparison.

    Note: This requires running in separate processes or Docker containers
    with different ports.
    """

    print(f"=== Parallel Comparison ===")
    print(f"Benchmark: {benchmark}")
    print(f"\nRun these commands in separate terminals:")
    print()
    print("Terminal 1 (Random):")
    print("  cd VprGym && python3 example.py")
    print()
    print("Terminal 2 (FSM):")
    print("  cd VprGym && python3 fsm_agent.py")
    print()
    print("Terminal 3 (Epsilon-Greedy):")
    print("  cd VprGym && python3 epsilon_greedy_agent.py")
    print()
    print("Or using Docker:")
    print("  ./run_docker.sh -D example.py")
    print("  ./run_docker.sh -D fsm_agent.py")
    print("  ./run_docker.sh -D epsilon_greedy_agent.py")
    print()


def analyze_logs(log_dir='ablation_results'):
    """
    Analyze experiment logs to compare agent performance.
    """
    log_path = Path(log_dir)

    print(f"=== Log Analysis ===")
    print(f"Analyzing logs in: {log_path}")
    print()

    # Find all log files
    fsm_logs = list(log_path.glob('**/fsm_log_*.json'))
    epsilon_logs = list(log_path.glob('**/epsilon_greedy_log_*.json'))

    print(f"Found {len(fsm_logs)} FSM logs")
    print(f"Found {len(epsilon_logs)} Epsilon-Greedy logs")
    print()

    comparison = {
        'FSM': [],
        'Epsilon-Greedy': []
    }

    # Analyze FSM logs
    for log_file in fsm_logs:
        with open(log_file) as f:
            data = json.load(f)
            comparison['FSM'].append({
                'file': str(log_file),
                'results': data.get('results', {}),
                'config': data.get('config', {})
            })

    # Analyze Epsilon-Greedy logs
    for log_file in epsilon_logs:
        with open(log_file) as f:
            data = json.load(f)
            comparison['Epsilon-Greedy'].append({
                'file': str(log_file),
                'results': data.get('results', {}),
                'config': data.get('config', {}),
                'reward_analysis': data.get('reward_analysis', {})
            })

    # Print comparison
    print("\n=== Performance Comparison ===\n")

    for agent_name, runs in comparison.items():
        if not runs:
            continue

        print(f"{agent_name}:")
        for i, run in enumerate(runs, 1):
            results = run['results']
            print(f"  Run {i}:")
            print(f"    Wire Length: {results.get('wire_length', 'N/A')}")
            print(f"    Critical Path Delay: {results.get('critical_path_delay', 'N/A')}")
            print(f"    Runtime: {results.get('runtime', 'N/A')}")
            print(f"    Total Swaps: {results.get('total_swaps', 'N/A')}")

            # Print reward statistics for epsilon-greedy
            if 'reward_analysis' in run:
                ra = run['reward_analysis']
                print(f"    Reward Mean: {ra.get('mean', 'N/A'):.6f}")
                print(f"    Reward Std: {ra.get('std', 'N/A'):.6f}")

        print()

    # Save comparison
    comparison_file = log_path / 'comparison_summary.json'
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"Comparison saved to: {comparison_file}")

    return comparison


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == 'analyze':
            # Analyze existing logs
            analyze_logs()
        elif sys.argv[1] == 'parallel':
            # Show parallel run instructions
            run_parallel_comparison()
        else:
            print("Usage:")
            print("  python3 run_ablation_study.py          # Run sequential ablation study")
            print("  python3 run_ablation_study.py analyze  # Analyze existing logs")
            print("  python3 run_ablation_study.py parallel # Show parallel run instructions")
    else:
        # Run ablation study
        print("Note: This will run experiments sequentially (may take a long time)")
        print("For faster results, run agents in parallel using separate Docker containers")
        print()
        response = input("Continue with sequential run? (y/n): ")
        if response.lower() == 'y':
            run_ablation_study()
        else:
            print("\nFor parallel execution, run:")
            print("  python3 run_ablation_study.py parallel")
