import math

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

class EmbeddingGenerator:
    """
    Embedding Generator using sentence-transformers (all-MiniLM-L6-v2)
    or standard library vectorizer fallback.
    """
    def __init__(self, vector_dim: int = 384, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.vector_dim = vector_dim
        self._init_model()

    def _init_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.vector_dim = self.model.get_sentence_embedding_dimension()
            print(f"Loaded Embedding Model: {self.model_name} (Dim: {self.vector_dim})")
        except Exception:
            self.model = None

    def embed_text(self, text: str):
        """
        Generates a 1D embedding vector for input text.
        """
        if self.model:
            emb = self.model.encode(text, convert_to_numpy=True)
            norm = np.linalg.norm(emb)
            return (emb / norm).tolist() if norm > 0 else emb.tolist()
        else:
            # Deterministic lightweight vectorizer fallback using pure Python math
            words = text.lower().split()
            vec = [0.0] * self.vector_dim
            for w in words:
                h = sum(ord(c) for c in w)
                idx = h % self.vector_dim
                vec[idx] += 1.0
            sq_sum = sum(x * x for x in vec)
            norm = math.sqrt(sq_sum)
            return [x / norm for x in vec] if norm > 0 else vec

    def embed_batch(self, texts: list) -> list:
        return [self.embed_text(t) for t in texts]

    @staticmethod
    def cosine_similarity(u, v) -> float:
        dot = sum(a * b for a, b in zip(u, v))
        norm_u = math.sqrt(sum(a * a for a in u))
        norm_v = math.sqrt(sum(b * b for b in v))
        if norm_u == 0 or norm_v == 0:
            return 0.0
        return float(dot / (norm_u * norm_v))

    @staticmethod
    def euclidean_distance(u, v) -> float:
        return float(math.sqrt(sum((a - b) ** 2 for a, b in zip(u, v))))

    @staticmethod
    def dot_product(u, v) -> float:
        return float(sum(a * b for a, b in zip(u, v)))


if __name__ == "__main__":
    generator = EmbeddingGenerator()
    sample = "Where is the Office of the Registrar located in TPC?"
    emb = generator.embed_text(sample)
    print(f"Generated embedding vector of dimension: {len(emb)}")
    print(f"First 5 dimensions: {emb[:5]}")
