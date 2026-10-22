import os
from src.embedding import EmbeddingGenerator

try:
    import chromadb
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

class VectorStore:
    """
    Vector Database implementation using ChromaDB for indexing TPC campus text chunks
    and executing similarity queries across Cosine, Euclidean, and Dot Product metrics.
    """
    def __init__(self, embedding_generator=None, collection_name: str = "tpc_navbot_collection", persist_directory: str = r"c:\Users\ranz\Desktop\TPC Navbot\data\chroma_db"):
        self.embedder = embedding_generator or EmbeddingGenerator()
        self.documents = []
        self.embeddings = []
        self.metadatas = []
        self.ids = []
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        self.chroma_client = None
        self.collection = None

        if HAS_CHROMADB:
            try:
                os.makedirs(self.persist_directory, exist_ok=True)
                self.chroma_client = chromadb.PersistentClient(path=self.persist_directory)
                try:
                    self.collection = self.chroma_client.get_or_create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                except Exception:
                    self.collection = self.chroma_client.create_collection(
                        name=self.collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
            except Exception as e:
                print(f"ChromaDB initialization notice: {e}")
                self.chroma_client = None
                self.collection = None

    def add_chunks(self, chunks: list):
        if not chunks:
            return

        new_ids = []
        new_docs = []
        new_metas = []
        new_embs = []

        for chunk in chunks:
            text = chunk['text']
            meta = chunk['metadata']
            chunk_id = meta.get('chunk_id', f"id_{len(self.ids)+1:04d}")
            emb = self.embedder.embed_text(text)

            self.ids.append(chunk_id)
            self.documents.append(text)
            self.metadatas.append(meta)
            self.embeddings.append(emb)

            new_ids.append(chunk_id)
            new_docs.append(text)
            new_embs.append(emb)

            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            new_metas.append(clean_meta)

        if self.collection:
            try:
                self.collection.upsert(
                    ids=new_ids,
                    embeddings=new_embs,
                    documents=new_docs,
                    metadatas=new_metas
                )
                print(f"Indexed {len(self.ids)} text chunks into ChromaDB Collection ('{self.collection_name}').")
            except Exception as e:
                print(f"Indexed {len(self.ids)} text chunks into VectorStore (ChromaDB notice: {e}).")
        else:
            print(f"Indexed {len(self.ids)} text chunks into VectorStore.")

    def search(self, query: str, top_k: int = 3, metric: str = "cosine") -> list:
        if len(self.documents) == 0:
            return []

        query_emb = self.embedder.embed_text(query)
        q_lower = query.lower()

        # Attempt search via ChromaDB vector store collection if available
        if self.collection:
            try:
                chroma_res = self.collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(top_k * 3, len(self.documents)),
                    include=["documents", "metadatas", "distances"]
                )
                if chroma_res and chroma_res.get('ids') and len(chroma_res['ids']) > 0 and len(chroma_res['ids'][0]) > 0:
                    results = []
                    ids = chroma_res['ids'][0]
                    docs = chroma_res['documents'][0]
                    metas = chroma_res['metadatas'][0]
                    distances = chroma_res['distances'][0]

                    for idx in range(len(ids)):
                        dist = distances[idx]
                        score = max(0.0, 1.0 - dist)
                        bldg = (metas[idx].get('building', '')).lower()
                        src_doc = (metas[idx].get('source_doc', '')).lower()

                        if ('bsis' in q_lower or 'comlab' in q_lower or 'computer' in q_lower or 'kompyuter' in q_lower) and ('computer studies' in bldg or 'computer_studies' in src_doc):
                            score += 0.40
                        elif ('crim' in q_lower or 'criminology' in q_lower or 'pulis' in q_lower) and ('criminology' in bldg or 'criminology' in src_doc):
                            score += 0.40
                        elif ('agri' in q_lower or 'agriculture' in q_lower or 'uma' in q_lower or 'tanom' in q_lower) and ('agriculture' in bldg or 'agriculture' in src_doc):
                            score += 0.40
                        elif ('polsci' in q_lower or 'english' in q_lower or 'beced' in q_lower or 'academic' in q_lower) and ('main academic' in bldg or 'main_academic' in src_doc):
                            score += 0.40
                        elif ('cashier' in q_lower or 'registrar' in q_lower or 'admin' in q_lower or 'tuition' in q_lower or 'fee' in q_lower or 'pay' in q_lower or 'permit' in q_lower or 'bayad' in q_lower or 'bayranan' in q_lower or 'bayaran' in q_lower or 'matrikula' in q_lower or 'magbayad' in q_lower) and ('administration' in bldg or 'administration' in src_doc or 'cashier' in src_doc or 'registrar' in src_doc):
                            score += 0.40
                        elif ('gym' in q_lower or 'sports' in q_lower or 'dulaan' in q_lower) and ('gymnasium' in bldg or 'gymnasium' in src_doc):
                            score += 0.40
                        elif ('clinic' in q_lower or 'medical' in q_lower or 'nurse' in q_lower or 'health' in q_lower or 'tambal' in q_lower or 'tambalanan' in q_lower or 'malipong' in q_lower or 'sakit' in q_lower or 'doktor' in q_lower) and ('clinic' in bldg or 'clinic' in src_doc):
                            score += 0.40
                        elif ('lost' in q_lower or 'security' in q_lower or 'guard' in q_lower or 'gwardya' in q_lower or 'bantay' in q_lower or 'nawala' in q_lower or 'nawagtang' in q_lower) and ('security' in bldg or 'security' in src_doc):
                            score += 0.40
                        elif ('library' in q_lower or 'libro' in q_lower or 'basahan' in q_lower or 'aklatan' in q_lower) and ('library' in bldg or 'library' in src_doc):
                            score += 0.40
                        elif ('canteen' in q_lower or 'cafeteria' in q_lower or 'kaonan' in q_lower or 'kainan' in q_lower or 'pagkaon' in q_lower) and ('canteen' in bldg or 'canteen' in src_doc):
                            score += 0.40
                        elif ('saso' in q_lower or 'affairs' in q_lower) and ('student affairs' in bldg or 'student_affairs' in src_doc):
                            score += 0.40

                        results.append({
                            "id": ids[idx],
                            "score": float(score),
                            "text": docs[idx],
                            "metadata": metas[idx]
                        })

                    results.sort(key=lambda x: x['score'], reverse=True)
                    return results[:top_k]
            except Exception as e:
                pass

        # In-memory vector calculation fallback
        results = []
        for idx, doc_emb in enumerate(self.embeddings):
            if metric == "cosine":
                score = self.embedder.cosine_similarity(query_emb, doc_emb)
            elif metric == "euclidean":
                dist = self.embedder.euclidean_distance(query_emb, doc_emb)
                score = 1.0 / (1.0 + dist)
            elif metric == "dot_product":
                score = self.embedder.dot_product(query_emb, doc_emb)
            else:
                raise ValueError(f"Unsupported metric: {metric}")

            bldg = (self.metadatas[idx].get('building', '')).lower()
            src_doc = (self.metadatas[idx].get('source_doc', '')).lower()

            if ('bsis' in q_lower or 'comlab' in q_lower or 'computer' in q_lower) and ('computer studies' in bldg or 'computer_studies' in src_doc):
                score += 0.40
            elif ('crim' in q_lower or 'criminology' in q_lower) and ('criminology' in bldg or 'criminology' in src_doc):
                score += 0.40
            elif ('agri' in q_lower or 'agriculture' in q_lower or 'uma' in q_lower or 'tanom' in q_lower) and ('agriculture' in bldg or 'agriculture' in src_doc):
                score += 0.40
            elif ('polsci' in q_lower or 'english' in q_lower or 'beced' in q_lower or 'academic' in q_lower) and ('main academic' in bldg or 'main_academic' in src_doc):
                score += 0.40
            elif ('cashier' in q_lower or 'registrar' in q_lower or 'admin' in q_lower or 'tuition' in q_lower or 'fee' in q_lower or 'pay' in q_lower or 'permit' in q_lower or 'bayad' in q_lower or 'bayranan' in q_lower or 'bayaran' in q_lower or 'matrikula' in q_lower or 'magbayad' in q_lower) and ('administration' in bldg or 'administration' in src_doc or 'cashier' in src_doc or 'registrar' in src_doc):
                score += 0.40
            elif ('gym' in q_lower or 'sports' in q_lower or 'dulaan' in q_lower) and ('gymnasium' in bldg or 'gymnasium' in src_doc):
                score += 0.40
            elif ('clinic' in q_lower or 'medical' in q_lower or 'nurse' in q_lower or 'health' in q_lower or 'tambal' in q_lower or 'tambalanan' in q_lower or 'malipong' in q_lower or 'sakit' in q_lower or 'doktor' in q_lower) and ('clinic' in bldg or 'clinic' in src_doc):
                score += 0.40
            elif ('lost' in q_lower or 'security' in q_lower or 'guard' in q_lower or 'gwardya' in q_lower or 'bantay' in q_lower or 'nawala' in q_lower or 'nawagtang' in q_lower) and ('security' in bldg or 'security' in src_doc):
                score += 0.40
            elif ('library' in q_lower or 'libro' in q_lower or 'basahan' in q_lower or 'aklatan' in q_lower) and ('library' in bldg or 'library' in src_doc):
                score += 0.40
            elif ('canteen' in q_lower or 'cafeteria' in q_lower or 'kaonan' in q_lower or 'kainan' in q_lower or 'pagkaon' in q_lower) and ('canteen' in bldg or 'canteen' in src_doc):
                score += 0.40
            elif ('saso' in q_lower or 'affairs' in q_lower) and ('student affairs' in bldg or 'student_affairs' in src_doc):
                score += 0.40

            results.append({
                "id": self.ids[idx],
                "score": float(score),
                "text": self.documents[idx],
                "metadata": self.metadatas[idx]
            })

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
