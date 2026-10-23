# Answer quality and reviewed improvement

The deterministic school benchmark passes 199 of 199 declared cases against
the 30 school-confirmed records. It checks expected facts and source citations,
language, unsupported details, referrals, conversation follow-ups, multipart
questions, and 19 abuse requests. Eight additional focused cases distinguish
BSIS/BSAIS, preserve the reviewed fact that new student IDs are free, and prevent
scholarship/replacement workflows, renewal costs and specific contact requests
from borrowing facts belonging to another service.

Final validation on 24 October 2026: **150 regression tests passed**, including
the 199-case benchmark, eight focused accuracy cases, UI feedback/quota checks,
input attacks, reviewed-source revocation, storage and learning behavior. The
full local runner log is retained in `.codex-tmp/full-regression-final.log` at
the workspace root.

These are regression results, not a claim of universal accuracy. The tests use
the local lexical embedding backend with cloud model selection disabled. They
do not independently authenticate the school's submission or prove that all
information is current. Missing fees, dates, grades, personnel, permissions and
routes still require school confirmation. English source wording is retained
inside localized responses when no reviewed translation exists.

## Reproduce the checks

From `TPC Navbot`, using the installed environment:

```powershell
..\.venv\Scripts\python.exe tests/run_tests.py
..\.venv\Scripts\python.exe scripts/evaluate_school_qa.py --output data/evaluation/school_qa_final.json
```

Evaluation uses temporary indexes and manifests, and never enables paid cloud
calls. The concise local report is `data/evaluation/school_qa_final.json`;
the human-readable report is `data/evaluation/school_qa_summary.md`. Generated
evaluation files are intentionally ignored by Git; the evaluator and tests
are reproducible source files.

## What improves automatically

The web app counts fixed categories: campus topic, requested field, response
status, language, day and optional helpful/not-helpful feedback. It stores no
question text, answer text, names, accounts, session IDs or user-supplied claims
in this database. Unknown topic names become a fixed `unknown` category.
Conversation text stays in bounded in-memory/browser-session history, separately
from aggregate metrics and trusted retrieval records.

Frequently requested fields can rise in suggested follow-ups. Every suggestion
must still correspond to a field in the currently selected reviewed record.
Popularity and thumbs feedback never establish a fact. A user cannot teach the
assistant a new location or instruction by repeating a claim.

The SQLite metrics database defaults to `data/learning/question_metrics.sqlite3`,
with 90-day retention, at most 2,000 aggregate rows and a roughly 4 MiB ceiling.
Set `TPC_LEARNING_PATH` to a private persistent writable path when needed.
Metrics storage failures do not stop answers. Local counts persist across app
restarts; ephemeral hosting may discard them unless durable storage is provided.

## Review and add missing information

```powershell
..\.venv\Scripts\python.exe scripts/review_learning.py
..\.venv\Scripts\python.exe scripts/review_learning.py --all
```

The local administrator report ranks unresolved categories and negative
feedback. It is not exposed as a public chat command. Administrators should:

1. Review frequently missing topics and confirm details with the proper school office.
2. Update the curated source and its approved structured fields.
3. Record the new content hash, reviewer, reference and review date using the
   [source verification workflow](09_source_verification.md).
4. Re-ingest and add representative questions with independently stated expected facts.
5. Run the regression suite and school benchmark before distributing the update.

Optional `location_data.details` fields support specific reviewed answers:
`deadlines`, `fees`, `processing_time`, `borrowing_limits`, `visitor_access`,
`account_recovery`, `wifi_login`, `admission_exam`, and `staff`. Values may be
reviewed strings or language mappings with `english`, `bisaya`, and `tagalog`.
For example, an explicitly fictional test record can contain:

```json
{"destination":"Synthetic Test Office","details":{"fees":{"english":"Fictional test fee: PHP 123."}}}
```

This example is not a TPC fact. Merely editing metadata does not grant approval;
normal content-bound registry validation still applies. Absent or untranslated
specific details remain unverified. A reviewed referral can accompany that
uncertainty without implying that a fee, grade or deadline is known.

## Public input and abuse controls

The application enforces 600 characters and 120 words per message, and at most
three explicit school questions per message. It checks the original complete
turn before retrieval, memory updates or optional model selection. Rejected
payloads do not enter backend conversation history. Detection covers common
Unicode, encoded, role-spoofing, instruction-override, credential-disclosure,
private-record and operational hacking patterns. Legitimate IT recovery,
incident reporting and security-course questions remain allowed for scope checks;
allowing a question does not imply that verified school answers exist.

The web app shares a thread-safe limiter: 12 messages per browser session per
minute and 120 messages per application process per minute. Starting a new
conversation retains the browser quota. Denials do not call retrieval. These
are process-local quotas, not authenticated per-person or distributed quotas;
new browser sessions and multiple workers require a shared gateway or identity
layer for stronger public deployment controls.

Filters cannot prove that every possible injection is blocked. The stronger
boundary remains approved records, constrained source-ID selection, and no
shell, network-scanning, arbitrary-code or file-reading tools accessible to the
chatbot. This follows the layered approach in the
[OWASP prompt injection prevention guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).
