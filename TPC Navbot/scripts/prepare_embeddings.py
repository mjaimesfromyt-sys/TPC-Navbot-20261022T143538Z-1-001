"""Explicitly download a semantic model; normal application startup stays offline."""
import argparse
import os
from pathlib import Path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "models" / "all-MiniLM-L6-v2")
    args = parser.parse_args()
    os.environ.setdefault("HF_HOME", str(args.output.resolve().parent / ".cache"))
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(args.model)
    model.save(str(args.output.resolve()))
    print(f"Model saved locally to {args.output.resolve()}")
    print("Set TPC_EMBEDDING_MODEL to this folder and TPC_EMBEDDING_MODE=semantic.")
