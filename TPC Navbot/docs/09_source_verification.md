# Adding verified campus information

The bundled 30 generated documents must remain unverified. Do not change their status merely to make the demo answer. A generated response, source filename, similarity score, or "official" heading is not approval.

## Review workflow

1. Obtain a current official campus document, map, notice, or authorized record. Confirm permission to include its relevant content. Keep private student records and credentials out of the knowledge base.
2. Create a UTF-8 `.txt` source with LF line endings in `data/raw/`, preserving exact destination names and clearly labelled facts. Save it with LF before computing its hash: `.gitattributes` enforces LF on checkout, and a hash of Windows CRLF bytes will fail verification after deployment. Prefer small single-destination records over prose mixing many buildings.
3. Have an authorized reviewer confirm the contents against the official reference, including whether any area is restricted. Review translated explanatory text; retain official building/office/room names.
4. Compute the exact file SHA-256 in PowerShell: `Get-FileHash -Algorithm SHA256 -LiteralPath 'data/raw/your_source.txt'`. Use the lowercase digest in the registry.
5. Add a `documents[filename]` registry entry with `verified: true`, approved `source_type`, `sha256`, `official_source`, `reviewed_by`, and `reviewed_at` in `YYYY-MM-DD` format. All fields must describe a real review. The source type must be `official_document`, `official_map`, or `authorized_campus_record`.
6. Add reviewed structured facts as described below. Run `python -m src.ingestion --force`, inspect the reported verified count, and test all three languages. A fact must match both the destination and the requested intent.
7. When information changes, edit the raw source and obtain a new review/hash. An old approval must not survive changed bytes. Re-ingest and confirm removed or unapproved documents no longer answer questions.

The registry is an operator review record, not cryptographic proof that a human is authorized. Limit write access to trusted maintainers and keep the underlying official evidence. The application checks completeness and content binding; campus governance supplies the authority.

## Structured location facts

`location_data` is an object, optionally containing `locations`, a list of reviewed destination objects. Each destination needs `destination`; recommended optional fields are:

| Field | Meaning |
|---|---|
| `aliases` | Reviewed list of alternate destination names; official name remains `destination`. |
| `building`, `floor`, `room`, `location` | Only confirmed location facts. |
| `hours`, `services`, `contact` | Only current, public, supported service facts. |
| `accessibility` | Only a separately checked accessibility description. |
| `restricted` | Set `true` for restricted facilities; the bot should not direct students into them. |

Descriptive values can be language dictionaries with keys `english`, `bisaya`, and `tagalog`. Missing translations are omitted rather than invented. Official identifiers should stay unchanged. The renderer also supports a limited labelled plain-text directory, but structured records prevent accidental mixing of facts from different places.

## Separate route facts

`route_data` is an object, optionally containing `routes`, a list of routes. A route needs a confirmed `destination`, `start`, optional `start_aliases`, and ordered `steps`. Steps can be a language dictionary of lists. The destination must match the selected location and the student's actual stated starting point must match the route origin.

Optional fields include positive finite `walking_minutes` and `distance_m`, plus reviewed `landmarks` and `accessibility`. A route without measured/verified time must omit time. A location without a reviewed route must produce a route-unavailable message. A route's accessibility cannot be inferred merely from its existence. Do not assume every student starts at the main gate.

No real TPC route example is provided here because none was supplied for independent verification. The regression fixtures are explicitly fictional and should never be copied into the production registry as real campus evidence.

## Validation before release

Test a valid location, unknown location, duplicate room across buildings, missing route, unknown starting point, unmatched origin, unsupported hours, restricted area, edited source, removed source, and withdrawn approval. Repeat scope/fallback cases in English, Bisaya, and Tagalog. Confirm the source citation identifies the reviewed reference. Retain actual results and address failures before serving real campus guidance.
