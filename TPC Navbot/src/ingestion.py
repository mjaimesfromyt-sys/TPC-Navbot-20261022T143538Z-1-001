"""Incremental ingestion: portable paths, review-aware updates, and stale pruning."""
import hashlib
import json
import sys
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import MANIFEST_PATH, PROCESSED_CHUNKS_PATH, RAW_DATA_DIR, SOURCE_REGISTRY_PATH
from src.preprocessing import TextPreprocessor
from src.storage_io import atomic_text_writer, atomic_write_text
from src.vector_store import VectorStore


class IngestionPipeline:
    def __init__(self, raw_data_dir=None, manifest_path=None, vector_store=None, source_registry_path=None, processed_path=None):
        self.raw_data_dir = str(raw_data_dir or RAW_DATA_DIR)
        self.manifest_path = str(manifest_path or MANIFEST_PATH)
        self.processed_path = str(processed_path or PROCESSED_CHUNKS_PATH)
        self.source_registry_path = source_registry_path or SOURCE_REGISTRY_PATH
        self.processor = TextPreprocessor(source_registry_path=self.source_registry_path)
        self.vector_store = vector_store or VectorStore(raw_data_dir=self.raw_data_dir, source_registry_path=self.source_registry_path)
        self.embedder = self.vector_store.embedder
        self.manifest = self._load_manifest()

    def _load_manifest(self):
        try:
            manifest = json.loads(Path(self.manifest_path).read_text(encoding="utf-8"))
            return manifest if isinstance(manifest, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_manifest(self):
        atomic_write_text(self.manifest_path, json.dumps(self.manifest, indent=2))

    def _export_processed(self):
        with atomic_text_writer(self.processed_path) as output:
            for text, metadata in zip(self.vector_store.documents, self.vector_store.metadatas):
                output.write(json.dumps({"text": text, "metadata": metadata}, ensure_ascii=False) + "\n")

    @staticmethod
    def _compute_file_hash(filepath):
        return hashlib.sha256(Path(filepath).read_bytes()).hexdigest()

    def _fingerprint(self, filepath):
        entry = self.processor.registry.entries().get(Path(filepath).name, {})
        payload = {"sha256": self._compute_file_hash(filepath), "review": entry,
                   "embedding": self.vector_store.embedding_signature, "chunker": "bounded-v2:400:50"}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def ingest_file(self, filepath, force=False):
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
        fingerprint = self._fingerprint(path)
        # A manifest alone must never suppress rebuilding a missing vector index.
        if not force and self.manifest.get(path.name) == fingerprint and self.vector_store.has_document(path.name):
            return []
        chunks = self.processor.process_file(path)
        self.vector_store.replace_document(path.name, chunks)
        self.manifest[path.name] = fingerprint
        self._save_manifest()
        return chunks

    def run(self, force=False):
        start = time.monotonic()
        raw_dir = Path(self.raw_data_dir)
        if not raw_dir.is_dir():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
        files = sorted(raw_dir.glob("*.txt"))
        active_names = {p.name for p in files}
        removed = (set(self.manifest) | self.vector_store.source_documents()) - active_names
        for name in sorted(removed):
            self.vector_store.delete_document(name)
            self.manifest.pop(name, None)
        changed, chunk_count = 0, 0
        for path in files:
            fingerprint = self._fingerprint(path)
            needs_update = force or self.manifest.get(path.name) != fingerprint or not self.vector_store.has_document(path.name)
            if needs_update:
                chunks = self.ingest_file(path, force=True)
                changed += 1
                chunk_count += len(chunks)
        self._save_manifest()
        self._export_processed()
        return {
            "status": "COMPLETED", "total_documents_scanned": len(files),
            "documents_updated_or_added": changed, "documents_removed": len(removed),
            "new_chunks_indexed": chunk_count, "total_collection_chunks": len(self.vector_store.documents),
            "verified_chunks": sum(m.get("verified_source") is True for m in self.vector_store.metadatas),
            "elapsed_seconds": round(time.monotonic() - start, 2),
            "vector_store_type": self.vector_store.backend, "collection_name": self.vector_store.collection_name,
            "embedding_backend": self.embedder.backend, "semantic_embeddings": self.embedder.is_semantic,
            "processed_chunks_path": self.processed_path,
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TPC NavBot incremental document ingestion")
    parser.add_argument("--force", action="store_true", help="Re-index all documents")
    parser.add_argument("--dir", default=str(RAW_DATA_DIR), help="Raw TXT directory")
    parser.add_argument("--registry", default=str(SOURCE_REGISTRY_PATH), help="Human-reviewed source registry")
    args = parser.parse_args()
    pipeline = IngestionPipeline(raw_data_dir=args.dir, source_registry_path=args.registry)
    print(json.dumps(pipeline.run(force=args.force), indent=2))


if __name__ == "__main__":
    main()
