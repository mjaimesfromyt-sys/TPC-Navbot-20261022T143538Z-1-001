# Project proposal: TPC NavBot

## Problem and users

Freshmen and campus visitors may not know official names or locations of classrooms, offices, laboratories, and student facilities. A useful assistant must recognize common English, Bisaya, and Tagalog questions while distinguishing a verified answer from missing campus information.

The proposed product is a TPC campus location and supported-information assistant. Target users are incoming students, enrolled students, and first-time visitors. It should answer location questions concisely, ask for a building when a room number has multiple matches, preserve relevant conversational context, and decline unrelated tasks.

## Scope and data

The initial repository provides 30 generated text documents about sample campus buildings and services. These are demonstration material, not official campus evidence. Their room numbers, office hours, procedures, prices, and routes require verification before release. Course guide page 3 permits realistically simulated data for the capstone pipeline.

Production content must come from an official campus directory, current institutional notices, an official map, or an authorized campus record. Each source needs an official reference, exact SHA-256, reviewer, and review date in the source registry. A reviewed location is independent of a reviewed walking route.

No verified digital map or complete route database was provided. Therefore the initial version withholds exact routes, distances, times, step counts, and accessibility claims. It can report verified locations as the campus supplies them. Unavailable campus information receives a localized limitation message and a recommendation to confirm with authorized TPC personnel.

## Technical approach

Raw text is cleaned and chunked with source metadata. Locally cached semantic embeddings can populate the vector database; an explicitly labelled lexical fallback supports offline development. Current-turn scope and language checks precede eligible-source retrieval. Structured reviewed facts constrain the final response. Session memory carries a destination or starting point only for relevant campus follow-ups.

LangChain provides composition when installed; a deterministic fallback supports offline development. Optional Gemini integration can select only an allowed retrieved source ID, after which the application renders reviewed facts. A model response is never itself source verification.

Streamlit supplies the web interface and a CLI supports repeatable demonstrations. Persistent indexes and an ingestion manifest support updates. A multi-stage container and repository-root CI configuration support repeatable packaging; remote deployment requires separate evidence.

## Measurable acceptance criteria

1. Retain 30 labelled samples and produce bounded source-attributed chunks.
2. Demonstrate cleaning/tokenization with before/after examples and report the actual embedding backend.
3. Return equivalent decisions for English, Bisaya, and Tagalog cases covering allowed, unavailable, ambiguous, and unrelated requests.
4. Supply no facts from unverified samples, and no route/time/accessibility fields without separate reviewed evidence.
5. Reject unrelated requests even if they include "TPC" or ask the bot to ignore its rules.
6. Preserve relevant campus follow-ups and isolate sessions; unrelated follow-ups are still rejected.
7. Refresh changed/removed sources and invalidate approvals when their hashes change.
8. Retain a five-query demo, backend-labelled metric results, and regression output; later add authorized API and remote deployment artifacts.

These are targets. Actual results belong in evaluation artifacts; the proposal does not assert that every target has been completed.

## Ownership and integrity

Student names and component ownership were not supplied. The team must truthfully declare actual owners of data/embeddings, orchestration/safety, interface/deployment, and documentation at each checkpoint. If working individually, identify that student as owner. Disclose AI assistance and generated samples. Do not invent team names, surveys, interviews, or campus approvals.
