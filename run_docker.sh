#!/bin/bash

# Usage: ./run_docker.sh [-D] [python_file.py]
# -D: Run in detached (background) mode
# python_file.py: Optional Python script to run (defaults to interactive bash)

set -e

DETACHED=false
PYTHON_FILE=""
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="vpr-gym-${TIMESTAMP}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -D)
      DETACHED=true
      shift
      ;;
    *)
      PYTHON_FILE="$1"
      shift
      ;;
  esac
done

# Validate Python file if provided
if [[ -n "$PYTHON_FILE" && ! -f "VprGym/$PYTHON_FILE" ]]; then
  echo "Error: Python file 'VprGym/$PYTHON_FILE' not found"
  exit 1
fi

# Build docker command
if [[ "$DETACHED" == true ]]; then
  # Detached mode
  if [[ -z "$PYTHON_FILE" ]]; then
    echo "Error: -D flag requires a Python file to run"
    exit 1
  fi

  echo "Starting experiment in detached mode..."
  echo "Container name: $CONTAINER_NAME"
  echo "Running: $PYTHON_FILE"

  docker run -d --rm \
    --name "$CONTAINER_NAME" \
    -v "$(pwd)/VprGym:/workspace/VprGym" \
    -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
    -w /workspace/VprGym \
    vpr-gym \
    bash -c "python3 $PYTHON_FILE 2>&1 | tee exp/${TIMESTAMP}/run.log"

  echo ""
  echo "Experiment started! Monitor with:"
  echo "  docker logs -f $CONTAINER_NAME"
  echo ""
  echo "Check status with:"
  echo "  docker ps -f name=$CONTAINER_NAME"

else
  # Interactive mode
  if [[ -n "$PYTHON_FILE" ]]; then
    # Run specific Python file interactively
    echo "Running $PYTHON_FILE in interactive mode..."

    docker run -it --rm \
      --name "$CONTAINER_NAME" \
      -v "$(pwd)/VprGym:/workspace/VprGym" \
      -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
      -w /workspace/VprGym \
      vpr-gym \
      bash -c "python3 $PYTHON_FILE 2>&1 | tee exp/${TIMESTAMP}/run.log; echo 'Experiment complete. Results in exp/${TIMESTAMP}/'; exec bash"

  else
    # Interactive bash shell
    echo "Starting interactive Docker container..."
    echo "Working directory: /workspace/VprGym"

    docker run -it --rm \
      --name "$CONTAINER_NAME" \
      -v "$(pwd)/VprGym:/workspace/VprGym" \
      -v "$(pwd)/vtr_flow:/workspace/vtr_flow" \
      -w /workspace/VprGym \
      vpr-gym \
      bash
  fi
fi