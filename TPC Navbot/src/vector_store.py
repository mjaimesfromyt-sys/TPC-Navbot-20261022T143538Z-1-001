"""Durable, idempotent vector storage with source validation before retrieval.

The v2 snapshot is authoritative. Legacy Chroma collections are neither loaded nor
trusted. Chroma, when available, mirrors the current snapshot in a new namespace.
"""
import hashlib
import json
import math
import re
import warnings
from collections import Counter
from datetime import date
from functools import lru_cache
from pathlib import Path

from src.campus_entities import ENTITY_ALIASES as DESTINATION_ALIASES, destination_matches
from src.config import PERSIST_DIRECTORY, RAW_DATA_DIR, SOURCE_REGISTRY_PATH
from src.embedding import EmbeddingGenerator
from src.preprocessing import TextPreprocessor
from src.storage_io import atomic_write_text


def canonical_destinations(text):
    """Use the same campus names as the question resolver."""
    return destination_matches(text)


@lru_cache(maxsize=8192)
def _term_counts(text):
    """Cache lexical analysis, never a source's approval or current bytes."""
    # Keep room/course codes and academic years intact as well as Unicode words.
    return Counter(re.findall(r"[^\W_]+(?:[-./][^\W_]+)*", text.casefold()))


def _structured_names(value):
    """Read record identities from both single records and directory wrappers."""
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            return []
    if isinstance(value, list):
        return [name for item in value for name in _structured_names(item)]
    if not isinstance(value, dict):
        return []
    names = [value['destination']] if isinstance(value.get('destination'), str) else []
    if isinstance(value.get('aliases'), list):
        names.extend(alias for alias in value['aliases'] if isinstance(alias, str))
    for key in ('locations', 'routes'):
        if isinstance(value.get(key), (dict, list)):
            names.extend(_structured_names(value[key]))
    return names


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
        atomic_write_text(self._snapshot, json.dumps({
            "schema_version": 2,
            "embedding_signature": self.embedding_signature,
            "tracked_sources": sorted(self._tracked_sources),
            "source_chunk_counts": {name: sum(r["metadata"].get("source_doc") == name for r in self._records.values())
                                    for name in sorted(self._tracked_sources)},
            "records": list(self._records.values()),
        }, ensure_ascii=False))

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
        # Read approval data once for this search, never cache trust between
        # searches. Each source's current bytes are still hashed and re-chunked.
        processor = TextPreprocessor(source_registry_path=self.source_registry_path)
        registry_entries = processor.registry.entries()
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
                    chunks = processor.process_file(source, registry_entries=registry_entries)
                    expected[filename] = {c["metadata"]["chunk_id"]: c for c in chunks}
                except (OSError, UnicodeError, ValueError):
                    expected[filename] = {}
            actual = expected[filename].get(row["id"])
            # Reject stale chunks, stale approvals, forged metadata and legacy DB entries.
            if (actual and actual["metadata"].get("verified_source") is True
                    and actual["text"] == row["text"] and actual["metadata"] == metadata):
                yield row

    @staticmethod
    def _identity(row):
        metadata = row['metadata']
        names = [str(metadata.get(key, '')) for key in ('building', 'source_doc', 'entity')]
        for key in ('location_data', 'route_data'):
            names.extend(_structured_names(metadata.get(key)))
        return ' '.join(names)

    @staticmethod
    def _search_text(row):
        metadata = row['metadata']
        # These values come from the content-bound registry, not the Q&A corpus.
        fields = ('document_title', 'category', 'intent', 'entity', 'department',
                  'section', 'language', 'location_data', 'route_data')
        return ' '.join([row['text']] + [str(metadata.get(key, '')) for key in fields])

    @staticmethod
    def _keyword_scores(query, rows):
        """BM25 over the same currently approved candidate set as vector search."""
        terms = set(_term_counts(query))
        documents = [_term_counts(VectorStore._search_text(row)) for row in rows]
        lengths = [sum(document.values()) for document in documents]
        average = sum(lengths) / len(lengths) if lengths else 0
        frequencies = {term: sum(term in document for document in documents) for term in terms}
        scores = []
        for document, length in zip(documents, lengths):
            score = 0.0
            for term in terms:
                count = document.get(term, 0)
                if not count:
                    continue
                frequency = frequencies[term]
                inverse = math.log(1 + (len(documents) - frequency + 0.5) / (frequency + 0.5))
                normalizer = count + 1.2 * (1 - 0.75 + 0.75 * length / (average or 1))
                score += inverse * count * 2.2 / normalizer
            scores.append(score)
        return scores

    @staticmethod
    def _source_rank(metadata):
        """Authority/date tie-breaks cannot manufacture a missing source date."""
        authority = metadata.get('source_authority')
        if type(authority) is not int or not 1 <= authority <= 7:
            authority = 2 if metadata.get('source_type') in {'official_document', 'official_map'} else 4
        # Review dates are audit events, not publication/effective dates.
        source_date = metadata.get('effective_date') or metadata.get('publication_date') or ''
        try:
            source_date = date.fromisoformat(source_date).isoformat()
        except (TypeError, ValueError):
            source_date = ''
        return authority, source_date

    def search(self, query, top_k=3, metric="cosine", verified_only=True, *, hybrid=True, filters=None):
        """Retrieve current evidence with vector/BM25 fusion by default.

        ``score`` always retains the requested vector metric for compatibility.
        ``retrieval_score`` and ``rank_details`` explain hybrid ordering. Set
        hybrid=False for an exact metric baseline; Euclidean and dot-product
        requests retain their original metric ordering regardless of this flag.
        Explicit metadata filters can narrow evidence but can never approve it.
        """
        if metric not in {"cosine", "euclidean", "dot_product"}:
            raise ValueError(f"Unsupported metric: {metric}")
        allowed_filters = {'category', 'intent', 'entity', 'language', 'department',
                           'academic_year', 'source_type', 'campus'}
        if filters is not None and (not isinstance(filters, dict)
                or any(key not in allowed_filters or not isinstance(value, str)
                       for key, value in filters.items())):
            raise ValueError('Metadata filters must contain supported string fields')
        if top_k <= 0:
            return []
        rows = list(self._verified_rows()) if verified_only else list(self._records.values())
        if filters:
            rows = [row for row in rows if all(
                str(row['metadata'].get(key, '')).casefold() == value.casefold()
                for key, value in filters.items())]
        if not rows:
            return []
        targets = canonical_destinations(query)
        if len(targets) == 1:
            target = next(iter(targets))
            matched = []
            for row in rows:
                if target in canonical_destinations(self._identity(row)):
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
        if not hybrid or metric != 'cosine':
            return sorted(results, key=lambda r: (-r['score'], r['id']))[:top_k]
        if not results:
            return []
        keyword_scores = self._keyword_scores(query, rows)
        vector_order = sorted(range(len(results)), key=lambda index: (-results[index]['score'], results[index]['id']))
        keyword_order = sorted(range(len(results)), key=lambda index: (-keyword_scores[index], results[index]['id']))
        def tied_ranks(order, score):
            ranks, previous, rank = {}, None, 1
            for position, index in enumerate(order, 1):
                value = score(index)
                if previous is None or value != previous:
                    rank = position
                ranks[index], previous = rank, value
            return ranks
        vector_ranks = tied_ranks(vector_order, lambda index: results[index]['score'])
        keyword_ranks = tied_ranks(keyword_order, lambda index: keyword_scores[index])
        # A source can express the best semantic match and the best exact-word
        # match in different chunks. Fuse those signals at document level first
        # so splitting one document cannot make a weaker joint chunk win.
        documents = {}
        for index, result in enumerate(results):
            key = (result['metadata'].get('source_doc', ''), result['metadata'].get('source_sha256', ''))
            document = documents.setdefault(key, {'vector_score': -math.inf, 'keyword_score': 0.0, 'indices': []})
            document['vector_score'] = max(document['vector_score'], result['score'])
            document['keyword_score'] = max(document['keyword_score'], keyword_scores[index])
            document['indices'].append(index)
        keys = list(documents)
        document_vectors = sorted(range(len(keys)), key=lambda index: (-documents[keys[index]]['vector_score'], keys[index]))
        document_keywords = sorted(range(len(keys)), key=lambda index: (-documents[keys[index]]['keyword_score'], keys[index]))
        document_vector_ranks = tied_ranks(document_vectors, lambda index: documents[keys[index]]['vector_score'])
        document_keyword_ranks = tied_ranks(document_keywords, lambda index: documents[keys[index]]['keyword_score'])
        for index, key in enumerate(keys):
            document = documents[key]
            document['vector_rank'] = document_vector_ranks[index] if document['vector_score'] > 0 else None
            document['keyword_rank'] = document_keyword_ranks[index] if document['keyword_score'] > 0 else None
            document['score'] = sum(1 / (60 + rank) for rank in (document['vector_rank'], document['keyword_rank']) if rank)
        for index, result in enumerate(results):
            # Zero/negative matches contribute no invented relevance. BM25 can
            # recover exact identifiers missed by an embedding or hash collision.
            vector_rank = vector_ranks[index] if result['score'] > 0 else None
            keyword_rank = keyword_ranks[index] if keyword_scores[index] > 0 else None
            chunk_score = sum(1 / (60 + rank) for rank in (vector_rank, keyword_rank) if rank)
            key = (result['metadata'].get('source_doc', ''), result['metadata'].get('source_sha256', ''))
            document = documents[key]
            result['retrieval_score'] = document['score']
            authority, source_date = self._source_rank(result['metadata'])
            result['rank_details'] = {
                'method': 'document reciprocal-rank fusion (k=60), then diverse chunks',
                'embedding_backend': getattr(self.embedder, 'backend', 'custom'),
                'vector_score': result['score'], 'bm25_score': keyword_scores[index],
                'vector_rank': vector_rank, 'keyword_rank': keyword_rank,
                'document_vector_rank': document['vector_rank'],
                'document_keyword_rank': document['keyword_rank'],
                'document_bm25_score': document['keyword_score'],
                'chunk_retrieval_score': chunk_score,
                'source_authority': authority, 'source_date': source_date,
            }
        def document_order(key):
            document = documents[key]
            first = results[document['indices'][0]]
            authority, source_date = self._source_rank(first['metadata'])
            return (-document['score'], authority, -int(source_date.replace('-', '') or 0),
                    -document['keyword_score'], key)
        first_chunks, remaining = [], []
        for key in sorted(keys, key=document_order):
            chunks = sorted((results[index] for index in documents[key]['indices']), key=lambda result: (
                -result['rank_details']['chunk_retrieval_score'],
                -result['rank_details']['bm25_score'], -result['score'], result['id']))
            first_chunks.append(chunks[0])
            remaining.extend(chunks[1:])
        # Show independent sources before repeats, so a long document cannot
        # hide a peer source that the answer verifier must check for conflicts.
        # Larger limits still return every eligible chunk, preserving diagnostics.
        return (first_chunks + remaining)[:top_k]
