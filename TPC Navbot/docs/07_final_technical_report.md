# TPC NavBot: final technical report draft

Prepared 22 October 2026. This is the consolidated report source for the guide's 3-5 page submission. It has not been exported into a paginated final document. Complete the remaining evidence items and verify the exported page count before submission.

## Problem, scope, and requirements

TPC NavBot assists freshmen, students, and visitors with Talibon Polytechnic College campus locations and explicitly supported campus services. It supports English, Bisaya, and Tagalog, including common mixed-language messages. The intended outcome is a concise accurate answer or a useful clarification, rather than a plausible response unsupported by campus evidence.

The supplied semester guide requires an end-to-end data pipeline, embeddings, vector search, prompt design, an API demonstration, LangChain and/or LlamaIndex orchestration, multi-turn memory, an interface, containerization, remote deployment evidence, and a defense. It permits realistically simulated data and a reasoned decision against fine-tuning. The user's additional behavioral specification requires TPC-only scope, no invented directions/time, and consistent restrictions and fallbacks across the three languages.

The baseline already had Python pipeline modules, CLI and Streamlit interfaces, a Chroma database, Gemini code, and container configuration. However, it treated generated campus text as verified and supplied hard-coded walking times, distances, step counts, and generic directions from an assumed gate. The old README also claimed reports and completed checkpoints without corresponding evidence. Those claims were replaced with explicit status and a deliverables audit.

## Data pipeline and provenance

The corpus contains 30 generated `.txt` documents about sample campus facilities/services. They are retained to demonstrate ingestion and retrieval. Their room numbers, policies, prices, hours, and routes have not been independently verified. The normal application therefore cannot treat those contents as real campus facts.

Text preprocessing normalizes line endings and whitespace, removes decorative separators, and expands abbreviations such as `Bldg` and `Rm`. It creates bounded overlapping character chunks with source filename, location label, building label, and chunk ID. A retained run produced 114 chunks with maximum length 399 characters under the 400-character default. The reflection report includes actual before/after cleaning and lexical tokenization output.

The source registry holds a review record separately from source text. Eligibility requires an approved source type, official reference, reviewer, review date, and exact SHA-256. Editing the underlying file invalidates its approval. Generated files remain unverified, regardless of confident titles in their text. This protects against stale indexes and accidental promotion of sample content; it does not replace institutional authorization of reviewers.

Ingestion scans raw files, cleans/chunks them, embeds them, and refreshes persistent storage. Its fingerprint includes source content, review metadata, embedding identity, and chunking configuration. Unchanged content can be skipped only when the index still contains it; deleted sources are removed. Processed chunks can be exported for inspection. Source and review changes must be reflected in eligible retrieval, not merely recorded in a manifest.

## Embeddings and retrieval

The embedding interface can use a locally cached Sentence Transformers model. Auto mode attempts only local loading and explicitly reports lexical fallback when unavailable. Semantic mode fails clearly if prerequisites are absent. Lexical mode uses deterministic signed SHA-256 unigram hashing into 384 dimensions followed by unit normalization. Separate retained runs demonstrate both lexical mode and actual local all-MiniLM-L6-v2 semantic embeddings. Model weights were deliberately downloaded, are excluded from Git, and require explicit provisioning on a fresh machine.

The vector store supports durable local snapshots and a Chroma adapter, with an explicitly reported backend. An actual snapshot+Chroma ingestion run scanned 30 files and indexed 114 chunks with 0 verified. Old Chroma data is not automatically trusted as reviewed evidence. Search is combined with destination matching and review checks. Similarity is a ranking aid, not the probability a fact is true.

The metric report compares cosine, Euclidean, and dot product directly on all 114 sample chunks for five queries. The three metrics returned matching top rankings, as expected for unit-normalized vectors. Target-source hit@1 was 0.20, hit@3 0.80, and mean reciprocal rank 0.50 for each metric. The library query ranked canteen first, a Bisaya Guidance query ranked agriculture first, and a Tagalog cashier query ranked Registrar first. The BSIS question ranked the FAQ ahead of its designated computer-studies source. These are lexical retrieval limitations under the explicit filename labels, not production multilingual accuracy estimates.

The semantic run on the same cases yielded hit@1 0.40, hit@3 0.80, and mean reciprocal rank 0.65 for every metric. It improved specific filename-labelled rankings but retained errors and did not verify campus facts. Cosine remains an understandable default. Switching among equivalent normalized metrics cannot repair missing official data or translation gaps. A broader evaluation still needs reviewed labels, real student phrasing, model identifiers, and held-out examples.

## Orchestration, memory, and constrained model use

LangChain core composes retrieval and approval filtering with runnable stages and wraps the fact renderer. The application reports whether the framework or direct standard-library fallback is active. LlamaIndex was compared in the framework note but is not implemented. This is a deliberately narrow framework use with visible application-owned trust checks.

Every current request is assessed for scope before remembered campus context is added. A prior library question does not authorize a subsequent unrelated assignment, joke, or general-knowledge request. Only recognized campus follow-ups inherit the destination or starting point. Sessions remain separate and can be reset. Ambiguous room numbers need clarification rather than a higher similarity score deciding the building.

Optional Gemini selection is disabled by default. When enabled with an authorized key, it may select an exact candidate ID from retrieved records. Its output must match the allowed schema and candidate set. Arbitrary model prose and invented IDs are discarded; provider errors fall back locally. Final facts are rendered from reviewed fields, so the model cannot supply route text or a walking estimate. This constrained design is useful safety evidence, but the full course API demonstration still requires a retained successful authorized call.

The prompt report provides three structured specifications with purposes and examples: scope routing, evidence selection, and multilingual grounded response. Application rules enforce those boundaries independently of a prompt's wording.

## Response safety and multilingual behavior

The application distinguishes unrelated requests from campus questions without evidence. Unrelated requests receive a localized campus-only redirection without an answer to the unrelated task. An unsupported campus office receives a localized unavailable-information message, not an off-topic classification.

Reviewed destination records can include building, floor, room, location, hours, services, and public contact fields. Missing facts are omitted or trigger an unavailable-information response. Official destination identifiers remain unchanged. Separately reviewed routes must match a known starting point and destination before numbered steps are rendered. Walking time, distance, landmarks, and accessibility appear only when separately present in that approved record. A verified office location alone cannot establish an accessible route or travel duration.

No verified digital campus map, full route database, live GPS, or real-time position feature was supplied. The assistant must not claim those capabilities. All bundled production-corpus records remain unverified. Fictional test fixtures demonstrate successful reviewed-answer behavior without establishing real TPC geography.

## Interface, packaging, and validation

Streamlit and CLI entry points expose the same core behavior. The web interface describes verification limitations and avoids presenting generated sample locations or route metrics as confirmed facts. User-facing errors should preserve the same supported language where possible and keep credentials/internal exception details private.

A multi-stage Dockerfile separates dependency construction from runtime and uses a non-root user. Secrets belong in private environment configuration. Repository-root CI is the correct location for GitHub Actions; configuration must not be confused with a completed successful workflow. Local browser execution and a Dockerfile are also insufficient evidence that a container is deployed remotely.

The final dependency-equipped regression run passed 51 tests with no skips, including an actual Streamlit AppTest, in 11.494 seconds. Tests cover source eligibility, stale approvals, session isolation, relevant/unrelated follow-ups, overrides, ambiguous locations, route constraints, and localized behavior. The final semantic+Chroma+LangChain demo passed 8/8 scenarios. Semantic ingestion indexed 114 chunks from 30 files, all unverified, in 6.55 seconds. Fixed tests establish those cases only. API mocks validate handling but do not prove live provider success. The audit separates implemented artifacts from missing demonstrations and avoids numerical grades or fabricated surveys.

## Limitations and remaining submission evidence

Real campus records, official reviewer approvals, measured routes, and accessibility checks remain external prerequisites. Successful authorized API output, a successful container build/run, and a remote deployment artifact remain required. Compose configuration passed validation, but the unavailable local Docker daemon prevented an actual image build/run. The final presentation must include a live demo, backup recording, actual ownership declarations, and students' own explanations.

No LoRA/QLoRA training was performed. The customization note explains low-rank parameter savings, quantized training memory considerations, and why fixing evidence and evaluation currently takes priority. Future adaptation should target measured intent or language deficiencies, not memorize unverified campus facts.

The central lesson is that retrieval and fluent generation do not certify information. A useful campus assistant needs current reviewed evidence, explicit missing-data behavior, narrow model authority, and repeatable evaluation. The current implementation establishes those software boundaries while honestly withholding campus guidance that has not yet been verified.

## References and attribution

- User-supplied semester project guide, pp2-9, and TPC NAVBOT behavioral guidelines: project requirements.
- Generated sample dataset and AI-assisted code: declared in the README and proposal; not official campus evidence.
- [LangChain retrieval documentation](https://docs.langchain.com/oss/python/langchain/retrieval), [LlamaIndex ingestion API](https://developers.llamaindex.ai/python/framework-api-reference/ingestion/), [Sentence Transformers similarity documentation](https://sbert.net/docs/sentence_transformer/usage/semantic_textual_similarity.html): technical references discussed in the dedicated reports.
- [LoRA paper](https://arxiv.org/abs/2106.09685), [QLoRA paper](https://arxiv.org/abs/2305.14314): original research supporting the customization note, not experiments conducted here.
