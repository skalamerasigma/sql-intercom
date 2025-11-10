#!/usr/bin/env python3
"""
Simple runner script for support headcount forecasting.

This script makes it easy to run the forecasting model from the project root.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run main function
from forecasting.forecast_headcount import main

if __name__ == '__main__':
	main()

