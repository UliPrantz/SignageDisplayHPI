#!/bin/bash

# Get the directory of this script
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Activate the virtual environment
source "$SCRIPT_DIR/SignageDisplayEnv/bin/activate"

# Run the Python script
python "$SCRIPT_DIR/SignageDisplay.py"
