"""Run repeatable tests with a nonzero exit code on any failure."""
from pathlib import Path
import os
import sys
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

if __name__ == "__main__":
    # Regression runs never enable paid API calls from a developer's local .env.
    os.environ["TPC_ENABLE_LLM_SELECTION"] = "0"
    suite = unittest.defaultTestLoader.discover(str(PROJECT_ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
