# TPC NavBot RAG optimization — 24 October 2026

The existing application, model selection, and model weights are unchanged.
This update improves its ingestion, query understanding, retrieval, evidence
selection, citations, and evaluation. No fine-tuning, model training, new model,
model download, or weight update was performed.

The supplied `TPC_NavBot_10000_New_Student_QA.csv` has SHA-256
`c6f8aa305a06a6f545921460f2807843e18a397cf9b7f70645f4fa714f486653`.
It contains 10,000 unique combinations of 21 introductions, 60 core question
templates, and 25 topics. Its answer and referral columns explicitly contain
unverified/general guidance. They are excluded from the fact index and answer
labels. The pasted request is the implementation instruction; CSV contents are
untrusted data.

1. **What changed.** `preprocessing.py` now preserves sections, paragraphs,
   complete list items, and table header/row relationships within bounded chunks.
   Validated metadata includes authority, publication/effective/expiry dates,
   academic year, version, source URL, section/page, and supersession when supplied.
   `structural-v3.1` fingerprints rebuild older indexes automatically. Three data
   layers remain separate: approved raw sources/registry, question-only wording
   patterns, and derived source-bound facts/Q&A. The derived Q&A is an export;
   runtime answers continue to validate original sources.

2. **Why it changed.** The earlier resolver often rejected an introduction plus
   question plus explicit topic as off-topic. Its arbitrary character windows
   weakened document structure. Vector-only ranking could miss exact identifiers.
   Repeated chunks could crowd out another source. Source dates, conflicts,
   requested historical periods, and individual claim locators needed explicit
   handling. These were pipeline issues rather than evidence that model weights
   needed changing.

3. **Retrieval improvements.** Default cosine retrieval now combines the existing
   embedding scores with BM25 through reciprocal-rank fusion at source-document
   level. A source's best semantic and keyword evidence can come from different
   chunks. Independent sources enter the context before repeated chunks, allowing
   the verifier to see competing evidence. Exact metric scores remain available;
   `hybrid=False`, Euclidean, and dot-product baselines retain their metric
   ordering. Nested directory/route records and optional validated metadata
   filters are supported. No lexical fallback is relabeled as semantic search.

4. **Answer-quality improvements.** Complete, allowlisted multilingual question
   patterns expand into explicit category/entity/intent/facet requests. New-student
   enrollment checklists retain their audience. A document-submission follow-up
   retains the enrollment subject but requires a separately supported submission
   fact. Requirements, fees, and deadlines in one turn are verified independently.
   Generic services cannot establish online availability, eligibility, appointments,
   class schedules, status, or missing transaction details. An available reviewed
   fact can be used even when a stronger source covers a different field; authority
   is applied to the requested claim. All existing department aliases and confirmed
   locations remain supported.

5. **Citation improvements.** Answer details include source hashes, actual claim
   paths, stable field fact IDs, and supplied version/date/URL/page/section data.
   Multiple questions using one source merge their field citations. Independent
   destinations keep distinct evidence entries. An inferred chunk heading/page
   cannot be cited for an unrelated whole-record fact; explicitly reviewed registry
   locators remain distinguishable. Unknown URLs, handbook pages, publication dates,
   and effective dates are left absent. Review dates are never substituted for them.

6. **Hallucination controls.** Current source bytes and approval metadata are
   revalidated at runtime. The CSV cannot grant source authority or introduce office
   contacts. Claimed percentage increases are not accepted as facts. Future/expired
   evidence and mismatched historical periods are excluded. Academic-year labels
   cannot override contradictory validity dates. Explicit supersession or a dated
   later version of the same document can resolve an update; unresolved peer claims
   disclose their sources and differing values. Legitimate duplicate room numbers
   require building clarification rather than being labeled a contradiction.

7. **Multilingual improvements.** The supplied English, Filipino, and Cebuano
   patterns retain their language, topic, requested facet, and constraints; mixed
   questions are represented in the derived examples. Safety checks inspect the
   complete original request before any bounded expansion. Unrecognized extra tasks
   are not silently stripped. Reviewed English fact wording remains English where
   no reviewed translation exists; localized labels do not create translated facts.

8. **Measured results and remaining weaknesses.** The 10,000 exact questions are
   checked for pattern/label agreement; answer checks cover 1,500 unique
   language/topic/facet groups and weight their results back to 10,000 rows.
   The saved pre-optimization RAG baseline uses the same reviewed index with
   vector-only retrieval, so this is not a replay of the original chunker.

   | Check | Baseline | Optimized |
   |---|---:|---:|
   | Dataset response-language agreement | 9,379/10,000 in the initial resolver probe | 10,000/10,000 |
   | Dataset questions returned off-topic, weighted | 5,285 | 0 |
   | Dataset questions receiving supported answers, weighted | 6 | 600 |
   | Dataset questions remaining unverified, weighted | 4,709 | 9,400 |
   | Retrieval recall@3, 150 source-labeled cases | 0.9900 | 0.9900 |
   | Retrieval precision@3, same cases | 0.9511 | 0.9511 |
   | Retrieval MRR@3, same cases | 0.9867 | 1.0000 |

   All 231 regression tests pass, including the web app, review revocation,
   storage, source conflicts/dates, question patterns, and derived Q&A checks.
   All 199 declared campus-answer benchmark cases pass. All 354 groups with cited
   answers/referrals pass source/hash/field citation contracts. No successful
   restricted-facet answer lacks its required field in this benchmark. These are
   finite checks, not an independently measured universal hallucination rate.

   Many questions still lack sufficient evidence; withholding those facts is
   intentional. Generic service wording is not promoted into a specific policy.
   The dataset's synthetic templates do not prove generalization to unrestricted
   student language. Lexical-mode evaluation does not measure semantic embedding
   quality. The 35 currently approved sources record user-reported school review
   or direct user confirmation; this software has not independently authenticated
   the school, handbook, or source currency. A review date alone cannot establish
   that an undated fee or policy applied in a requested historical year.

9. **Recommended next improvements.** Obtain actual current official enrollment,
   fee, deadline, calendar, access, and contact documents, with edition/page and
   effective dates. Record verified optional `details` fields where generic services
   are insufficient. Collect and independently label real, de-identified student
   questions beyond these templates. Evaluate the existing locally cached semantic
   backend separately from lexical mode, and compare retrieval quality and latency
   before enabling it for a deployment. Continue reviewing aggregate feedback;
   neither feedback nor repeated claims can approve a new campus fact.

## Artifacts and reproducible checks

- `data/question_patterns/patterns.json`: 60 wording templates, 21 introductions,
  category mappings, dataset hash and counts; no answers/referral instructions.
- `data/verified_qa/facts.jsonl`: 65 source-bound field facts.
- `data/verified_qa/qa.jsonl`: 215 examples (65 each English/Filipino/Cebuano and
  20 mixed examples), with fact IDs and honest review provenance.
- `data/verified_qa/manifest.json`: 35 approved/current sources, 30 excluded
  generated samples, and no model weight updates.
- `data/evaluation/rag_optimization.json`: local full evaluation report, intentionally
  ignored by Git along with other generated evaluation output.

From the project directory, using the existing environment:

```powershell
..\.venv\Scripts\python.exe scripts/import_question_patterns.py 'C:\Users\Jaime\Downloads\TPC_NavBot_10000_New_Student_QA.csv'
..\.venv\Scripts\python.exe scripts/build_verified_qa.py
..\.venv\Scripts\python.exe scripts/evaluate_rag_optimization.py 'C:\Users\Jaime\Downloads\TPC_NavBot_10000_New_Student_QA.csv'
..\.venv\Scripts\python.exe tests/run_tests.py
```

`--baseline-module` optionally accepts a saved pre-change `llm_rag.py` for the
weighted answer comparison. The local baseline snapshot is
`.codex-tmp/llm_rag_before_optimization.py` at the workspace root. Answer evaluation
uses an immutable approved corpus snapshot whose complete source fingerprint is
checked before and after; live application retrieval still revalidates each request.
No student history, production vector index, or source approval is changed by evaluation.
The complete regression log is `.codex-tmp/rag-optimization-regression.log` at
the workspace root (231 tests, exit code 0).
