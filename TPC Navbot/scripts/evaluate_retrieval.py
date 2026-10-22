"""Measure retrieval on simulated coursework data, without approving it for live answers."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.config import RAW_DATA_DIR
from src.embedding import EmbeddingGenerator
from src.preprocessing import TextPreprocessor


CASES = [
    ("Where is the library?", "doc_08_tpc_library_learning_center.txt"),
    ("Where is the Registrar's Office?", "doc_19_tpc_office_of_the_registrar.txt"),
    ("Where is the BSIS Department Office?", "doc_01_tpc_computer_studies_bsis_bsais.txt"),
    ("Asa dapit ang Guidance Office?", "doc_12_tpc_guidance_counseling_center.txt"),
    ("Saan po ang cashier?", "doc_18_tpc_cashier_finance_services.txt"),
]


def evaluate(mode="lexical"):
    embedder = EmbeddingGenerator(mode=mode)
    chunks = TextPreprocessor().process_directory(RAW_DATA_DIR)
    vectors = embedder.embed_batch([chunk["text"] for chunk in chunks])
    measurements = {}
    for metric in ("cosine", "euclidean", "dot_product"):
        cases = []
        for query, expected in CASES:
            query_vector = embedder.embed_text(query)
            def score(vector):
                if metric == "euclidean":
                    return -embedder.euclidean_distance(query_vector, vector)
                if metric == "dot_product":
                    return embedder.dot_product(query_vector, vector)
                return embedder.cosine_similarity(query_vector, vector)
            ranked = sorted(range(len(chunks)), key=lambda index: score(vectors[index]), reverse=True)
            sources = [chunks[index]["metadata"]["source_doc"] for index in ranked]
            rank = sources.index(expected) + 1 if expected in sources else None
            cases.append({"query": query, "expected_source": expected,
                          "top_source": sources[0] if sources else None,
                          "top_chunk_score": score(vectors[ranked[0]]) if ranked else None,
                          "first_relevant_chunk_rank": rank})
        measurements[metric] = {
            "hit_at_1": sum(case["first_relevant_chunk_rank"] == 1 for case in cases) / len(cases),
            "hit_at_3": sum(case["first_relevant_chunk_rank"] is not None and case["first_relevant_chunk_rank"] <= 3 for case in cases) / len(cases),
            "mean_reciprocal_rank": sum(1 / case["first_relevant_chunk_rank"] if case["first_relevant_chunk_rank"] else 0 for case in cases) / len(cases),
            "cases": cases,
        }
    return {"dataset": "Unverified simulated TPC coursework corpus; evaluation only",
            "documents": len({chunk['metadata']['source_doc'] for chunk in chunks}),
            "chunks": len(chunks), "embedding_backend": embedder.backend,
            "model": embedder.model_name if embedder.is_semantic else None,
            "dimensions": embedder.vector_dim,
            "notes": "Raw embeddings; no destination boosts or source verification bypass in live service. Euclidean scores are negative distances; higher is better.",
            "metrics": measurements}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["lexical", "semantic", "auto"], default="lexical")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.mode)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
