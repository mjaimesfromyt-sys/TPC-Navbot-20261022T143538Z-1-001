import sys
import os

# Ensure project root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from scripts.cli_chat import main

if __name__ == "__main__":
    main()
