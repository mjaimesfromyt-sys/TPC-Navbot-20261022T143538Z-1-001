import os
import sys
import glob
import json
import hashlib
import time
from typing import List, Dict, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing import TextPreprocessor
from src.embedding import EmbeddingGenerator
from src.vector_store import VectorStore

class IngestionPipeline:
    """
    End-to-End Automated Document Ingestion Pipeline for TPC NavBot.
    Monitors raw knowledge documents, handles cleaning, chunking, embedding generation,
    and incremental upserting into the ChromaDB vector database.
    """
    def __init__(
        self,
        raw_data_dir: str = r"c:\Users\ranz\Desktop\TPC Navbot\data\raw",
        manifest_path: str = r"c:\Users\ranz\Desktop\TPC Navbot\data\ingestion_manifest.json",
        vector_store: Optional[VectorStore] = None
    ):
        self.raw_data_dir = raw_data_dir
        self.manifest_path = manifest_path
        self.processor = TextPreprocessor(chunk_size=400, chunk_overlap=50)
        self.embedder = EmbeddingGenerator()
        self.vector_store = vector_store or VectorStore(embedding_generator=self.embedder)
        self.manifest = self._load_manifest()

    def _load_manifest(self) -> Dict[str, str]:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self):
        os.makedirs(os.path.dirname(self.manifest_path), exist_ok=True)
        with open(self.manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)

    def _compute_file_hash(self, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def ingest_file(self, filepath: str, force: bool = False) -> List[Dict]:
        """
        Ingests a single text document into the pipeline.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        current_hash = self._compute_file_hash(filepath)
        filename = os.path.basename(filepath)

        if not force and self.manifest.get(filename) == current_hash:
            return []

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        metadata = self.processor.extract_metadata(content, filename)
        chunks = self.processor.chunk_text(content, metadata)

        if chunks:
            self.vector_store.add_chunks(chunks)

        self.manifest[filename] = current_hash
        self._save_manifest()
        return chunks

    def run(self, force: bool = False) -> Dict:
        """
        Executes end-to-end automated batch ingestion over all documents in raw_data_dir.
        """
        start_time = time.time()
        txt_files = sorted(glob.glob(os.path.join(self.raw_data_dir, "*.txt")))

        total_scanned = len(txt_files)
        processed_files = []
        new_chunks_count = 0

        print(f"\n===============================================================================")
        print(f"            TPC NAVBOT AUTOMATED END-TO-END INGESTION PIPELINE                 ")
        print(f"===============================================================================")
        print(f"Directory: {self.raw_data_dir}")
        print(f"Total documents found: {total_scanned}")
        print(f"Force re-index mode: {force}\n")

        for filepath in txt_files:
            filename = os.path.basename(filepath)
            file_hash = self._compute_file_hash(filepath)

            if force or self.manifest.get(filename) != file_hash:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                meta = self.processor.extract_metadata(content, filename)
                chunks = self.processor.chunk_text(content, meta)

                if chunks:
                    self.vector_store.add_chunks(chunks)
                    new_chunks_count += len(chunks)

                self.manifest[filename] = file_hash
                processed_files.append(filename)
                print(f"[INGESTED] {filename} -> {len(chunks)} chunks created & embedded")
            else:
                pass

        self._save_manifest()
        elapsed_sec = round(time.time() - start_time, 2)

        summary = {
            "status": "COMPLETED",
            "total_documents_scanned": total_scanned,
            "documents_updated_or_added": len(processed_files),
            "new_chunks_indexed": new_chunks_count,
            "total_collection_chunks": len(self.vector_store.documents),
            "elapsed_seconds": elapsed_sec,
            "vector_store_type": "ChromaDB Persistent Client",
            "collection_name": self.vector_store.collection_name
        }

        print(f"\n-------------------------------------------------------------------------------")
        print(f"INGESTION SUMMARY:")
        print(f" - Documents Scanned: {total_scanned}")
        print(f" - Documents Ingested/Updated: {len(processed_files)}")
        print(f" - Chunks Stored in ChromaDB: {new_chunks_count}")
        print(f" - Total Active Vector Chunks: {len(self.vector_store.documents)}")
        print(f" - Execution Time: {elapsed_sec}s")
        print(f"-------------------------------------------------------------------------------\n")

        return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="TPC NavBot Automated Ingestion Pipeline")
    parser.add_argument("--force", action="store_true", help="Force re-indexing of all documents")
    parser.add_argument("--dir", type=str, default=r"c:\Users\ranz\Desktop\TPC Navbot\data\raw", help="Target raw dataset directory")
    args = parser.parse_args()

    pipeline = IngestionPipeline(raw_data_dir=args.dir)
    pipeline.run(force=args.force)

if __name__ == "__main__":
    main()
