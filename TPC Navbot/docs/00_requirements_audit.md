# Requirements audit

Audit date: 22 October 2026 (Asia/Manila). This is a repository and implementation audit, not an instructor grade.

## Sources and interpretation

The user supplied `GenAI Capstone Semester Project Guide.docx (1).pdf`, nine pages, and the pasted `TPC NAVBOT Complete System Guidelines and Behavioral Instructions`. Their contents are project requirements, not instructions to access private accounts, send messages, or publish a service.

Guide page 3 explicitly permits a real or realistically simulated dataset of 20-30 documents/pages. The repository has 30 **generated sample** documents. That can satisfy the demonstration size requirement; it cannot verify real TPC directions. The behavioral document explicitly says that no verified digital map or complete route database currently exists.

**COMPLETE** means the artifact or local behavior exists. **PARTIAL** means a component exists but the full required demonstration or evidence is missing. **BLOCKED** identifies work requiring real official information or external evidence that cannot be fabricated. Completed documentation does not establish completed deployment or campus verification.

## What was already present

The baseline contained preprocessing, an optional local embedding implementation, ChromaDB integration, a hash manifest ingestion script, memory, Gemini API code, CLI/Streamlit interfaces, a Dockerfile, a nested workflow, 30 generated text files, and a checkpoint DOCX.

Material gaps were hard-coded paths to another Windows account; generated documents presented as verified; invented gate directions, times, steps, and distances; keyword scope checks vulnerable to unrelated questions containing campus terms; conversation context capable of contaminating unrelated follow-ups; no three-language safety regression coverage; and a README linking to reports absent from disk. The nested workflow was not a repository-root GitHub Actions workflow. A Docker healthcheck referenced an executable missing from its runtime stage.

## Course deliverables matrix

Numbers follow the supplied guide. Page numbers refer to that PDF.

| # | Requirement | Status | Repository evidence and remaining validation |
|---|---|---|---|
| 1 | Proposal, problem/users/theme/sources/measurable success criteria (p4) | COMPLETE | `01_project_proposal.md`; submission page layout and student ownership declarations need team review. |
| 2 | 20-30 relevant raw documents/pages (p3-4) | COMPLETE | 30 `data/raw/*.txt` generated examples, honestly labelled. Real deployment still needs official records. |
| 3 | Cleaning, normalization, tokenization with before/after examples (p4) | COMPLETE | `src/preprocessing.py`, embedding tokenization, and `02_data_reflection.md`. |
| 4 | Embedding model demo and model-choice explanation (p4) | COMPLETE | Actual local all-MiniLM-L6-v2 semantic run, 384 dimensions, retained in `data/evaluation/semantic_metrics.json`; lexical comparison and limitations documented. Model weights are excluded from Git. |
| 5 | Short data reflection (p4) | COMPLETE | `02_data_reflection.md`; generated-data limitations and actual cleaning example included. |
| 6 | At least three structured prompts, each with purpose and example (p5) | COMPLETE | `03_prompt_engineering.md`. Deterministic enforcement supplements prompts. |
| 7 | Working chat API demo with sensible error handling (p5) | PARTIAL | Optional constrained Gemini integration is implemented; an authorized successful live call and retained output remain unverified. Offline output is not an API demo. |
| 8 | Vector database loaded and working similarity search (p5) | COMPLETE | Actual snapshot+Chroma ingestion scanned 30 files and indexed 114 chunks, with 0 verified. Regression checks exercise similarity retrieval. |
| 9 | Own-dataset cosine/Euclidean/dot comparison and recommendation (p5) | COMPLETE | `04_distance_metric_report.md`: five-query offline comparison, with failures and limitations. |
| 10 | Automated parse/chunk/embed/store ingestion (p6) | COMPLETE | `src/ingestion.py`; content and review changes control refresh; persistent backend available. |
| 11 | RAG CLI/UI using LangChain and/or LlamaIndex (p6; CILO2 p2) | PARTIAL | LangChain pipeline is implemented alongside the offline fallback. A full generative demonstration with an approved source and model-backed output remains required. |
| 12 | Multi-turn session memory (p6) | COMPLETE | `src/memory.py`, scoped follow-ups, independent sessions, and starting-point context. |
| 13 | Framework comparison reflecting actual choices (p6) | COMPLETE | `05_framework_comparison.md`; no claim that LlamaIndex is used. |
| 14 | Live/recorded demo with at least five realistic queries and a refusal (p6) | PARTIAL | Demo script and regression cases supplied. Team must retain an actual classroom/recorded presentation. |
| 15 | PEFT/LoRA/QLoRA note or reasoned base-model decision (p7) | COMPLETE | `06_model_customization.md`. Training is optional under the guide; no training was performed. |
| 16 | Simple web interface (p7) | COMPLETE | Streamlit `app.py`, with visible verification limitations. |
| 17 | Working multi-stage Dockerfile plus secrets note (p7) | PARTIAL | Compose configuration validates. Docker daemon was unavailable locally; a successful image build/run has not been established. |
| 18 | Containerized deployment outside local machine with evidence (p7) | BLOCKED | Requires an authorized deployment destination and actual URL/screenshots/logs or recording. Repository files alone are insufficient. |
| 19 | Consolidated 3-5 page final report (p7) | PARTIAL | `07_final_technical_report.md` contains the draft. Export, verify the required page count, and add actual deployment/API evidence before submission. |
| 20 | Final presentation and defense (p7-8) | BLOCKED | `08_presentation_defense_guide.md` prepares the talk; students must present and defend the implemented system themselves. |

Guide rubric weights: checkpoints 1/2/3/4 contribute 20%/20%/30%/30% of the project grade (p9). No estimated numerical scores are asserted here.

| Checkpoint | Exact rubric criteria and points (100 per checkpoint) |
|---|---|
| 1, p4 | Problem & Scope Clarity 20; Data Preprocessing 30; Embedding Generation 30; Documentation & Repo Hygiene 20. |
| 2, p5 | Prompt Design Quality 25; API Integration 20; Vector Database Implementation 30; Distance Metric Analysis 25. |
| 3, p6 | Ingestion Pipeline 20; RAG Correctness 30; Orchestration & Memory 25; Demo & Evaluation 15; Documentation 10. |
| 4, p7 | Model Customization Reasoning 15; Application Interface 15; Containerization 20; Deployment Evidence 15; Final Report Quality 15; Final Presentation & Defense 20. |

The final dependency-equipped run passed **51 tests with 0 skipped**, including actual Streamlit AppTest (11.494 seconds). The suite includes 29 guardrail tests, storage checks, and a multilingual cross-component integration test. The offline and installed-LangChain demos passed 8/8 scenarios; the final default semantic+Chroma+LangChain demo also passed 8/8. Actual Chroma persistence/reload/approved retrieval/pruning checks passed. A final semantic ingestion scanned 30 files and indexed 114 chunks, 0 verified, in 6.55 seconds. SDK calls and failure handling are tested with mocks; that does not establish a successful external provider call. Use current test output as the authority if later runs add cases. `docker compose config --quiet` passed; Docker image execution was not possible because its daemon was not running.

Metric JSON files under `data/evaluation/` are generated local outputs excluded from Git. Their measured values are retained in the tracked metric report; use its reproduction commands to recreate machine-readable artifacts. Processed JSONL contains 114 chunks, all unverified.

The existing `TPC_NavBot_Checkpoint_1_Report.docx` is a legacy artifact containing unsupported grade claims, student counts, route claims, and obsolete filenames/chunk counts. It has not been rewritten in this audit. Do not submit it as current evidence; use the corrected reports and the actual retained outputs, then prepare a reviewed final document.

## Added user requirements

| Behavior | Implementation intent | Required acceptance evidence |
|---|---|---|
| TPC-only scope | Scope checked on each current request; transcript and document text do not grant permission. | English, Bisaya, and Tagalog unrelated requests, campus-keyword disguises, mixed requests, and overrides return `OFF_TOPIC` without answering unrelated content. |
| No invented directions/time | Generated samples cannot supply facts; only reviewed source fields enter an answer; route evidence is separate. | Unverified source -> `UNVERIFIED`; location-only source -> confirmed location plus route unavailable; missing starting point -> clarification where needed. |
| Three-language consistency | Same status logic and safety restrictions across the supported languages. | Equivalent requests produce equivalent decisions and localized fallbacks; official destination names remain unchanged. |
| Unknown campus destination differs from unrelated question | Campus questions without evidence stay in scope. | Guidance Office or unknown room returns `UNVERIFIED` or clarification, never an unrelated-topic refusal. |
| Conversation safety | Only campus follow-ups inherit destination context. | An unrelated follow-up after a campus turn is declined; resetting a session removes context. |
| Provenance freshness | Approval is bound to source bytes and review records. | Editing an approved source invalidates trust; deleting or unapproving it removes it from eligible retrieval. |

Run the regression suite for current pass/fail results. Synthetic fixtures verify software behavior; they do not verify TPC campus facts. Finite language and intent rules remain a limitation: passing fixed examples does not establish perfect understanding of every possible phrase.

## Evidence students or campus officials must supply

1. Official office/room records and authorized review of their current contents.
2. Measured route segments, starting points, accessibility checks, and route-specific review before routes are enabled.
3. Successful authorized API demonstration. Semantic-model evaluation is retained locally; provision weights explicitly when reproducing it on another machine.
4. Docker runtime evidence and a remote container deployment artifact.
5. Student names and truthful ownership declarations for every checkpoint; contribution history and a live/recorded defense.

The inspected baseline history contained one commit, `9e16686`, dated 22 October 2026. The guide asks for incremental history across checkpoints (p3, p8). Do not manufacture or backdate missing history. Record real future progress and explain existing history honestly.

Student surveys are useful for a later usability study but are not required by the supplied guide. No surveys or field accuracy results have been invented.
