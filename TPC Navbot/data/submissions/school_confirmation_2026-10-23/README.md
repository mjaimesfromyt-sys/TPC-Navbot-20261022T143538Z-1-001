# School-confirmation submission — 23 October 2026

The user supplied `TPC_NavBot_30_Knowledge_Records.md` and stated that its
information had been confirmed with the school. The user then supplied:

- Reviewer: **Flordelis Tortuga**.
- Confirmation date: **10-23-2026**, normalized to **2026-10-23**.
- Reference: **Admin and handbook**.

No reviewer position, exact handbook title/edition/pages, or separate signed
confirmation was supplied. These are not invented in the registry. The review
method is `school_confirmation_reported_by_user`.

The original attachment still uses draft/pending labels. Its bytes are preserved
unchanged here, with their SHA-256 in `submission.json`. The user's later
confirmation and its scope are recorded separately rather than rewriting the
attachment to impersonate an official document.

## Contents

- `TPC_NavBot_30_Knowledge_Records.md`: the original, unchanged submission.
- `records/`: 30 individually extracted original sections.
- `records.json`: original section text and extracted field labels.
- `review_registry.json`: **unapproved original-section templates**. These still
  contain placeholders/ambiguities and are not used by the running app.
- `curation.json`: the exact selected facts, active filenames, original record
  references, and omissions for each of the 30 topics.
- `submission.json`: supplied confirmation details and the intake state.

The active reviewed sources are `data/raw/school_confirmed_*.txt`, approved in
`data/source_registry.json`. Only explicit selected facts are present in their
structured answer fields. No unknown room codes, routes, timings, accessibility
features, dates, grading values, or blanket access rules were generated.

Record numbers refer to this submission. They do **not** correspond to the old
`doc_XX` samples. All 30 original generated samples remain unverified.
