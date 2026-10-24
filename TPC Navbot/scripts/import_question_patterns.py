"""Profile question wording; do not ingest CSV answers into the fact corpus."""
import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.question_dataset import write_question_patterns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Student-question CSV; its answer columns are ignored')
    parser.add_argument('--output', type=Path, default=PROJECT_ROOT / 'data/question_patterns/patterns.json')
    args = parser.parse_args()
    artifact = write_question_patterns(args.source, args.output)
    print(json.dumps(artifact['dataset_profile'], ensure_ascii=False, indent=2))
    print(f'Question-only review artifact: {args.output}')


if __name__ == '__main__':
    main()
