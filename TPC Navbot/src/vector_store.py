"""Durable, idempotent vector storage with source validation before retrieval.

The v2 snapshot is authoritative. Legacy Chroma collections are neither loaded nor
trusted. Chroma, when available, mirrors the current snapshot in a new namespace.
"""
import hashlib
import json
import math
import os
import warnings
from pathlib import Path

from src.config import PERSIST_DIRECTORY, RAW_DATA_DIR, SOURCE_REGISTRY_PATH
from src.embedding import EmbeddingGenerator
from src.preprocessing import TextPreprocessor


DESTINATION_ALIASES = {
    "library": ("library", "aklatan", "basahanan", "basahan", "learning center"),
    "cashier": ("cashier", "cashiering", "finance services", "finance office", "kahera", "kaser"),
    "registrar": ("registrar", "records office"),
    "guidance": ("guidance", "counseling", "counselling", "tagapayo"),
    "clinic": ("clinic", "klinika", "tambalanan", "medical", "dental"),
    "canteen": ("canteen", "cafeteria", "kantina", "kainan", "kan anan", "kan an", "kaonan", "dining hall"),
    "gymnasium": ("gymnasium", "gym", "gymnasyum", "covered court"),
    "computer studies": ("computer studies", "bsis", "bsais", "comlab", "computer lab", "ccis"),
    "criminology": ("criminology", "bscrim", "kriminolohiya"),
    "agriculture": ("agriculture", "agrikultura", "bsag"),
    "student affairs": ("student affairs", "saso", "student services"),
    "security": ("security", "guardhouse", "guard house", "gwardya", "lost and found", "lost found"),
    "administration": ("administration", "admin building"),
    "admissions": ("admissions", "scholarship", "scholarships"),
    "chapel": ("chapel", "kapilya", "ecumenical"),
    "nstp": ("nstp", "rotc", "cwts"),
    "student government": ("student government", "ssg", "supreme student"),
    "restroom": ("restroom", "comfort room", "toilet", "cr", "kasilyas", "palikuran"),
}


def _normalized_words(text):
    import re
    return " ".join(re.findall(r"\w+", text.casefold().replace("_", " ")))


def canonical_destinations(text):
    """Exact multilingual phrase matching, never substring-based word boosts."""
    words = " " + _normalized_words(text) + " "
    return {name for name, aliases in DESTINATION_ALIASES.items()
            if any(" " + _normalized_words(alias) + " " in words for alias in aliases)}


class VectorStore:
    def __init__(self, embedding_generator=None, collection_name="tpc_navbot_collection",
                 persist_directory=None, raw_data_dir=None, source_registry_path=None,
                 backend="auto"):
        if backend not in {"auto", "json", "memory", "chroma"}:
            raise ValueError("backend must be auto, json, memory, or chroma")
        self.embedder = embedding_generator or EmbeddingGenerator()
        self.raw_data_dir = Path(raw_data_dir or RAW_DATA_DIR).resolve()
        self.source_registry_path = Path(source_registry_path or SOURCE_REGISTRY_PATH)
        self.persist_directory = str(persist_directory or PERSIST_DIRECTORY)
        # Embedding spaces never share a collection or a snapshot.
        signature = getattr(self.embedder, "signature", f"custom:{self.embedder.vector_dim}")
        self.embedding_signature = signature
        suffix = hashlib.sha256(signature.encode()).hexdigest()[:12]
        self.collection_name = f"{collection_name}_v2_{suffix}"
        self._snapshot = Path(self.persist_directory) / f"{self.collection_name}.json"
        self._persistent = backend != "memory"
        self.backend = "JSON persistent vector index" if self._persistent else "in-memory vector index"
        self.chroma_client = self.collection = None
        self._records = {}
        self._tracked_sources = set()
        if self._persistent:
            self._load_snapshot()
        if backend in {"auto", "chroma"}:
            try:
                import chromadb
                from chromadb.config import Settings
                self.chroma_client = chromadb.PersistentClient(
                    path=self.persist_directory, settings=Settings(anonymized_telemetry=False))
                self.collection = self.chroma_client.get_or_create_collection(
                    name=self.collection_name, metadata={"hnsw:space": "cosine"})
                self.backend = "ChromaDB + persistent snapshot"
                self._mirror_snapshot()
            except Exception as exc:
                if backend == "chroma":
                    raise RuntimeError("ChromaDB backend requested but unavailable") from exc
                warnings.warn("ChromaDB unavailable; using persistent JSON vectors with exact similarity search.", RuntimeWarning)
                self.chroma_client = self.collection = None
        self._refresh_arrays()

    def _load_snapshot(self):
        if not self._snapshot.exists():
            return
        try:
            data = json.loads(self._snapshot.read_text(encoding="utf-8"))
            if data.get("schema_version") != 2 or data.get("embedding_signature") != self.embedding_signature:
                return
            self._tracked_sources = {name for name in data.get("tracked_sources", []) if isinstance(name, str)}
            for row in data.get("records", []):
                if not isinstance(row, dict) or not isinstance(row.get("metadata"), dict):
                    continue
                vector = row.get("embedding", [])
                if len(vector) != self.embedder.vector_dim or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in vector):
                    continue
                if isinstance(row.get("id"), str) and isinstance(row.get("text"), str):
                    self._records[row["id"]] = row
                    if isinstance(row["metadata"].get("source_doc"), str):
                        self._tracked_sources.add(row["metadata"]["source_doc"])
            counts = data.get("source_chunk_counts", {})
            if isinstance(counts, dict):
                for name in list(self._tracked_sources):
                    actual = sum(r["metadata"].get("source_doc") == name for r in self._records.values())
                    if name in counts and counts[name] != actual:
                        self._tracked_sources.discard(name)
                        self._records = {key: row for key, row in self._records.items() if row["metadata"].get("source_doc") != name}
        except (OSError, ValueError, TypeError, AttributeError):
            warnings.warn("Unreadable vector snapshot; re-ingest source documents to rebuild it.", RuntimeWarning)

    def _save_snapshot(self):
        if not self._persistent:
            return
        self._snapshot.parent.mkdir(parents=True, exist_ok=True)
        temporary = self._snapshot.with_suffix(".json.tmp")
        temporary.write_text(json.dumps({
            "schema_version": 2,
            "embedding_signature": self.embedding_signature,
            "tracked_sources": sorted(self._tracked_sources),
            "source_chunk_counts": {name: sum(r["metadata"].get("source_doc") == name for r in self._records.values())
                                    for name in sorted(self._tracked_sources)},
            "records": list(self._records.values()),
        }, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, self._snapshot)

    def _mirror_snapshot(self):
        if self.collection is None:
            return
        try:
            present = set(self.collection.get(include=[]).get("ids", []))
            stale = present - self._records.keys()
            if stale:
                self.collection.delete(ids=sorted(stale))
            rows = list(self._records.values())
            for start in range(0, len(rows), 100):
                batch = rows[start:start + 100]
                self.collection.upsert(
                    ids=[r["id"] for r in batch],
                    documents=[r["text"] for r in batch],
                    embeddings=[r["embedding"] for r in batch],
                    metadatas=[{k: v for k, v in r["metadata"].items() if isinstance(v, (str, int, float, bool))} for r in batch])
        except Exception:
            warnings.warn("ChromaDB mirror update failed; authoritative JSON snapshot remains available.", RuntimeWarning)
            self.collection = None
            self.backend = "JSON persistent vector index"

    def _refresh_arrays(self):
        rows = list(self._records.values())
        self.ids = [r["id"] for r in rows]
        self.documents = [r["text"] for r in rows]
        self.metadatas = [r["metadata"] for r in rows]
        self.embeddings = [r["embedding"] for r in rows]

    def _commit(self):
        self._save_snapshot()
        self._mirror_snapshot()
        self._refresh_arrays()

    def _upsert(self, chunks):
        for chunk in chunks:
            text, metadata = chunk["text"], dict(chunk["metadata"])
            chunk_id = metadata.get("chunk_id")
            if not isinstance(chunk_id, str) or not chunk_id or not metadata.get("source_doc"):
                raise ValueError("Each chunk needs source_doc and a stable chunk_id")
            current = self._records.get(chunk_id)
            embedding = current["embedding"] if current and current["text"] == text else self.embedder.embed_text(text)
            self._records[chunk_id] = {"id": chunk_id, "text": text, "metadata": metadata, "embedding": embedding}
            self._tracked_sources.add(metadata["source_doc"])

    def add_chunks(self, chunks):
        """Upsert stable IDs; ingestion uses replace_document to prune removed chunks."""
        self._upsert(chunks)
        self._commit()

    def replace_document(self, source_doc, chunks):
        if any(c.get("metadata", {}).get("source_doc") != source_doc for c in chunks):
            raise ValueError("All replacement chunks must belong to source_doc")
        desired_ids = {c["metadata"]["chunk_id"] for c in chunks}
        self._upsert(chunks)
        self._tracked_sources.add(source_doc)
        for chunk_id, row in list(self._records.items()):
            if row["metadata"].get("source_doc") == source_doc and chunk_id not in desired_ids:
                del self._records[chunk_id]
        self._commit()

    def delete_document(self, source_doc):
        for chunk_id, row in list(self._records.items()):
            if row["metadata"].get("source_doc") == source_doc:
                del self._records[chunk_id]
        self._tracked_sources.discard(source_doc)
        self._commit()

    def has_document(self, source_doc):
        return source_doc in self._tracked_sources

    def source_documents(self):
        return set(self._tracked_sources)

    def _verified_rows(self):
        expected = {}
        for row in self._records.values():
            metadata = row["metadata"]
            filename = metadata.get("source_doc", "")
            if not isinstance(filename, str) or Path(filename).name != filename:
                continue
            if filename not in expected:
                try:
                    source = (self.raw_data_dir / filename).resolve()
                    if source.parent != self.raw_data_dir:
                        continue
                    chunks = TextPreprocessor(source_registry_path=self.source_registry_path).process_file(source)
                    expected[filename] = {c["metadata"]["chunk_id"]: c for c in chunks}
                except (OSError, UnicodeError, ValueError):
                    expected[filename] = {}
            actual = expected[filename].get(row["id"])
            # Reject stale chunks, stale approvals, forged metadata and legacy DB entries.
            if (actual and actual["metadata"].get("verified_source") is True
                    and actual["text"] == row["text"] and actual["metadata"] == metadata):
                yield row

    def search(self, query, top_k=3, metric="cosine", verified_only=True):
        if metric not in {"cosine", "euclidean", "dot_product"}:
            raise ValueError(f"Unsupported metric: {metric}")
        if top_k <= 0:
            return []
        rows = list(self._verified_rows()) if verified_only else list(self._records.values())
        if not rows:
            return []
        targets = canonical_destinations(query)
        if len(targets) == 1:
            target = next(iter(targets))
            matched = []
            for row in rows:
                metadata = row["metadata"]
                identity = " ".join(str(metadata.get(key, "")) for key in ("building", "source_doc"))
                # Verified structured destination names can identify generic file names.
                for key in ("location_data", "route_data"):
                    try:
                        fact = json.loads(metadata.get(key, "{}"))
                        if isinstance(fact, dict):
                            identity += " " + str(fact.get("destination", ""))
                            aliases = fact.get("aliases", [])
                            if isinstance(aliases, list):
                                identity += " " + " ".join(alias for alias in aliases if isinstance(alias, str))
                    except (TypeError, ValueError):
                        pass
                if target in canonical_destinations(identity):
                    matched.append(row)
            # An explicit facility must never silently retrieve a different one.
            rows = matched
            query = f"{target} {query}"
        query_emb = self.embedder.embed_text(query)
        # All metrics use the same active snapshot, so Chroma distance conventions
        # and stale mirror records cannot change application trust or ranking.
        results = []
        for row in rows:
            if metric == "euclidean":
                score = 1.0 / (1.0 + self.embedder.euclidean_distance(query_emb, row["embedding"]))
            elif metric == "dot_product":
                score = self.embedder.dot_product(query_emb, row["embedding"])
            else:
                score = self.embedder.cosine_similarity(query_emb, row["embedding"])
            results.append({"id": row["id"], "score": float(score), "text": row["text"], "metadata": dict(row["metadata"])})
        return sorted(results, key=lambda r: (-r["score"], r["id"]))[:top_k]
