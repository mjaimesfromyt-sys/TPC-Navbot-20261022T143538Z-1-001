"""Portable defaults; relative environment paths are resolved from the project."""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except ImportError:
    pass


def project_path(variable, default):
    value = Path(os.environ.get(variable, str(default))).expanduser()
    return value.resolve() if value.is_absolute() else (PROJECT_ROOT / value).resolve()


RAW_DATA_DIR = project_path("TPC_RAW_DATA_DIR", "data/raw")
SOURCE_REGISTRY_PATH = project_path("TPC_SOURCE_REGISTRY", "data/source_registry.json")
PERSIST_DIRECTORY = project_path("TPC_VECTOR_STORE_DIR", "data/vector_store")
MANIFEST_PATH = project_path("TPC_INGESTION_MANIFEST", "data/ingestion_manifest.json")
PROCESSED_CHUNKS_PATH = project_path("TPC_PROCESSED_CHUNKS", "data/processed/chunks.jsonl")
