"""Print anonymous question trends for an administrator's source-review workflow.

Run locally: python scripts/review_learning.py
No facts, embeddings, source reviews, or model weights are changed by this tool.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.learning import LearningStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, help="Optional metrics SQLite file")
    parser.add_argument("--limit", type=int, default=20, help="Maximum categories to show (1-2000)")
    parser.add_argument("--all", action="store_true", help="Include answered and off-topic categories")
    args = parser.parse_args()
    store = LearningStore(args.database)
    print(json.dumps({
        "policy": "Anonymous aggregate observations only; no self-training or automatic fact updates.",
        "retention_days": store.retention_days,
        "categories": store.summary(limit=args.limit, gaps_only=not args.all),
        "review_steps": [
            "Prioritize repeated unresolved or negatively rated school topics.",
            "Ask authorized school personnel to verify the missing information and its source.",
            "Add confirmed information through the existing reviewed source-registry workflow.",
            "Add regression questions and rerun the evaluation before releasing the update.",
        ],
        "interpretation": "Counts measure demand, not unique users, factual correctness, or verification.",
    }, indent=2))


if __name__ == "__main__":
    main()
