"""Local semantic embeddings with an explicitly labelled offline lexical fallback."""
import hashlib
import math
import os
import re
import warnings
from src.config import PROJECT_ROOT


class EmbeddingGenerator:
    def __init__(self, vector_dim=384, model_name=None, mode=None):
        local_model = PROJECT_ROOT / "data" / "models" / "all-MiniLM-L6-v2"
        prepared_model = str(local_model) if (local_model / "modules.json").is_file() and (local_model / "config.json").is_file() else "sentence-transformers/all-MiniLM-L6-v2"
        self.model_name = str(model_name or os.environ.get("TPC_EMBEDDING_MODEL", "").strip() or prepared_model)
        self.mode = mode or os.environ.get("TPC_EMBEDDING_MODE", "auto")
        if self.mode not in {"auto", "semantic", "lexical"}:
            raise ValueError("TPC_EMBEDDING_MODE must be auto, semantic, or lexical")
        if vector_dim < 1:
            raise ValueError("vector_dim must be positive")
        self.vector_dim = vector_dim
        self.model = None
        self.initialization_error = ""
        if self.mode != "lexical":
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
                self.vector_dim = self.model.get_sentence_embedding_dimension()
            except Exception as exc:
                self.initialization_error = f"{type(exc).__name__}: local semantic model unavailable"
                if self.mode == "semantic":
                    raise RuntimeError("Semantic mode needs sentence-transformers and a locally cached model; no download was attempted.") from exc
                warnings.warn("Semantic model unavailable locally; using offline lexical hashing (not semantic embeddings).", RuntimeWarning)
        self.backend = "sentence-transformers" if self.model is not None else "lexical-hashing"
        self.is_semantic = self.model is not None
        self.description = f"Local semantic embeddings: {self.model_name}" if self.is_semantic else "Offline lexical hashing; not semantic embeddings"
        self.signature = f"{self.backend}:v2:{self.model_name if self.is_semantic else 'sha256-unigrams'}:{self.vector_dim}"

    def embed_text(self, text):
        if self.model is not None:
            vector = self.model.encode(text, convert_to_numpy=True).tolist()
        else:
            vector = [0.0] * self.vector_dim
            for token in re.findall(r"\w+", text.casefold()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:8], "big") % self.vector_dim
                vector[index] += 1.0 if digest[8] & 1 else -1.0
        norm = math.sqrt(sum(x * x for x in vector))
        return [float(x / norm) for x in vector] if norm else vector

    def embed_batch(self, texts):
        return [self.embed_text(text) for text in texts]

    @staticmethod
    def _validate(u, v):
        if len(u) != len(v):
            raise ValueError("Embedding dimensions differ")

    @staticmethod
    def cosine_similarity(u, v):
        EmbeddingGenerator._validate(u, v)
        norm = math.sqrt(sum(x*x for x in u) * sum(x*x for x in v))
        return sum(a*b for a, b in zip(u, v)) / norm if norm else 0.0

    @staticmethod
    def euclidean_distance(u, v):
        EmbeddingGenerator._validate(u, v)
        return math.sqrt(sum((a-b)**2 for a, b in zip(u, v)))

    @staticmethod
    def dot_product(u, v):
        EmbeddingGenerator._validate(u, v)
        return float(sum(a*b for a, b in zip(u, v)))
