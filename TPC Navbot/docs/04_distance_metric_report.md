# Distance metric comparison on the project dataset

Measured locally on 22 October 2026 using 30 generated documents, 114 chunks, and `EmbeddingGenerator(mode="lexical")`: 384-dimensional signed SHA-256 unigram vectors, normalized to unit length. No semantic model, cloud API, or campus verification was used.

This experiment embeds the raw query and every chunk, then ranks by each mathematical metric. It bypasses scope checks, verified-source filtering, destination matching, and metadata boosting to isolate metric behavior. Student retrieval must not present these unverified documents as facts. The local generated artifact is `data/evaluation/lexical_metrics.json`; evaluation JSON is excluded from Git and recreated with:

```powershell
python scripts/evaluate_retrieval.py --mode lexical --output data/evaluation/lexical_metrics.json
```

Cosine is `dot(u,v)/(||u|| ||v||)` and dot is `sum(u_i*v_i)`; larger values rank first. Euclidean is `sqrt(sum((u_i-v_i)^2))`; smaller distances rank first. For nonzero unit vectors, dot equals cosine and squared Euclidean equals `2-2*cosine`, so their rankings match apart from ties. Normalized dot/cosine equivalence is also documented by [Sentence Transformers](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html).

| Query | Top source for all three metrics | Cosine | Euclidean distance | Dot | Inspection |
|---|---|---:|---:|---:|---|
| Where is the library? | `doc_07_tpc_canteen_dining_hall.txt` | 0.452267 | 1.046645 | 0.452267 | Target library source first appears at rank 2. |
| Where is the Registrar's Office? | `doc_19_tpc_office_of_the_registrar.txt` | 0.529813 | 0.969729 | 0.529813 | Target source ranks first. |
| Where is the BSIS Department Office? | `doc_30_tpc_official_faq.txt` | 0.586395 | 0.909510 | 0.586395 | Target computer studies source first appears at rank 3. |
| Asa dapit ang Guidance Office? | `doc_04_tpc_agriculture_building.txt` | 0.331832 | 1.156000 | 0.331832 | Target guidance source first appears at rank 6. |
| Saan po ang cashier? | `doc_19_tpc_office_of_the_registrar.txt` | 0.162221 | 1.294433 | 0.162221 | Target cashier source first appears at rank 2. |

All three metrics had target-source hit@1 **0.20**, hit@3 **0.80**, and mean reciprocal rank **0.50**. These use the first matching chunk from the exact expected filename in the script; multiple chunks from one document occupy separate ranks. A different source, such as the FAQ, might share relevant text but is not the selected target label. The JSON stores Euclidean as negative distance so every reported score can sort descending; the table above converts it back to positive distance.

This demonstrates metric equivalence and lexical-representation limitations. It does **not** show one metric has better accuracy or a high score verifies a fact. Five hand-selected queries are insufficient for a general accuracy estimate. Hash collisions, shared terms, and English-heavy text can rank the wrong destination first, especially for Bisaya/Tagalog questions.

Use cosine as the default for clarity; normalized dot is equivalent. Changing these metrics alone cannot repair the failures. Keep destination matching, provenance filters, and insufficient-evidence fallbacks, then evaluate a genuinely multilingual semantic model on a larger reviewed set. Retain backend/model IDs and relevance judgments. Different backend scores and hybrid ranks are not interchangeable confidence probabilities.

## Actual semantic-model comparison

A second run used a downloaded local `sentence-transformers/all-MiniLM-L6-v2` model with 384-dimensional normalized vectors, on the exact same five queries and filename labels. Its local generated artifact is `data/evaluation/semantic_metrics.json`. Each metric yielded hit@1 **0.40**, hit@3 **0.80**, and mean reciprocal rank **0.65**.

| Query | Top source | Cosine / dot | Euclidean distance | First target-source rank |
|---|---|---:|---:|---:|
| Where is the library? | `doc_07_tpc_canteen_dining_hall.txt` | 0.468149 | 1.031359 | 2 |
| Where is the Registrar's Office? | `doc_19_tpc_office_of_the_registrar.txt` | 0.591004 | 0.904429 | 1 |
| Where is the BSIS Department Office? | `doc_30_tpc_official_faq.txt` | 0.543245 | 0.955777 | 2 |
| Asa dapit ang Guidance Office? | `doc_05_tpc_administration_building.txt` | 0.429968 | 1.067738 | 4 |
| Saan po ang cashier? | `doc_18_tpc_cashier_finance_services.txt` | 0.362131 | 1.129486 | 1 |

These five cases show an improvement under the specified labels, with several failures still present. They do not establish statistical significance, general multilingual quality, or campus truth. The semantic run does not change the unverified status of the corpus.

To reproduce, provision that model separately, set `TPC_EMBEDDING_MODEL` to its absolute local model directory, and run `python scripts/evaluate_retrieval.py --mode semantic --output data/evaluation/semantic_metrics.json`. The output retains the actual local model path; it is machine-specific. Weights are excluded from Git. Rerun evaluation whenever chunking, tokenization, embedding configuration, or corpus contents change, and retain new output rather than silently reusing these snapshot numbers.
