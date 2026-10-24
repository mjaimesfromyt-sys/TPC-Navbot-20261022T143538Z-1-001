# School-confirmed records and remaining information gaps

## Confirmation recorded

On 23 October 2026 the user provided `TPC_NavBot_30_Knowledge_Records.md`, stated
that its information had been confirmed with the school, and supplied reviewer
**Flordelis Tortuga**, confirmation date **10-23-2026**, and reference **Admin and
handbook**. The registry uses the normalized date **2026-10-23** and source type
`authorized_campus_record` for the curated records.

This is **school confirmation reported by the user**. The software did not
independently contact the school or inspect an actual handbook edition. The
reviewer's position and handbook title/version/page references were not supplied.
Those details remain unspecified.

## What is active

Thirty `school_confirmed_*.txt` files contain selected explicit facts from the
submission, with content hashes and review metadata. The original thirty
`doc_*.txt` generated samples retain `verified: false`. The source registry
is the approval authority used by retrieval.

A separate `user_confirmed_bsis_office.txt` source records the project maintainer's
24 October 2026 clarification, "Naa sa main building sulod," in response to the
BSIS / Information Systems department office location question. Its only location
fact is **inside the Main Building**. The registry identifies this as direct user
confirmation; it does not attribute it to the earlier school reviewer or handbook.
No floor, room, office hours, route, or BSAIS office location was supplied.

Later on 24 October 2026 the user was explicitly asked for the BSAIS,
English/BAEL, Political Science/BAPS, and Early Childhood Education/BECED office
locations and replied, "Naa ra gihaponn sa main building maka ask raman kas mga
tao inag sulod nmo sa main building." Separate `user_confirmed_bsais_office.txt`,
`user_confirmed_bael_office.txt`, `user_confirmed_baps_office.txt`, and
`user_confirmed_beced_office.txt` sources retain that later confirmation: the
four offices are inside the Main Building, and students can ask someone after
entering for the exact office. This supersedes the earlier missing BSAIS location;
it supplies no exact floor, room, hours, named staff, or walking route. Existing
Criminology and Agriculture building facts are unchanged.

Approved fields include the supplied landmark-based locations, Main Building
office assignments where stated, specified weekday hours, selected services,
the common computer-laboratory rules, the seven supplied program titles, and
public college contact channels. Source wording is retained in English; this
import does not claim that new translations were reviewed by school personnel.
The application's language detection, labels, and fallback messages remain
available in English, Bisaya, and Tagalog.

Some reviewed topic records only identify a referral office or document an
information gap. A reviewed source does not establish facts absent from that
source. Questions requiring missing fields must still return an unavailable
information response.

## Information deliberately left unavailable

| Topic | Still needed for additional factual answers |
|---|---|
| Offices and classrooms | Exact official room codes, floors, and detailed department assignments. The Registrar's gate-relative location was clarified by the user as "in front of the main gate." |
| Computer laboratories | Official building/room identifiers, distinctions between the two labs where needed, and authorized outside-class access. |
| Gymnasium and visitors | Scope of public/student access, organized-event approval, bookings, and visitor eligibility. |
| Canteen | Meaning of the product word "sling," holiday hours, and visitor rules. |
| Library | Library-card application procedure, borrowing limits, visitor permissions, and holiday hours. |
| Clinic | Current emergency contacts/referral procedures and any transaction-specific ID or eligibility requirements. No patient records are imported. |
| Faculty offices | Exact rooms, appointments, access permission, and whether the reported knocking rule is official. |
| Wi-Fi | Exact login steps, acceptable-use rules, visitor eligibility, and whether "24/7" refers to network uptime or physical library access. |
| Student IDs | Lost versus damaged ID procedure, replacement fees, processing time, temporary IDs, and affidavit applicability. Free new IDs do not establish free replacements. |
| Enrollment/admission | Current official dates, category-specific requirements, copy counts/formats, late enrollment, fees, and who must take an entrance exam/interview. |
| Programs/departments | Current intake availability, official department names, coordinators, and room assignments. |
| Calendar/examinations | Actual approved calendar/timetable, deadlines, handbook edition/sections, permit requirements, and exact late/make-up rules. |
| Grading/attendance | Actual passing grade, scale, weights/formula, INC/appeal deadlines, absence limits, tardiness thresholds, and consequences. |
| Handbook/dress code | Exact handbook edition/pages, uniform-day schedule, ID rules, sanctions, and grievance deadlines. |
| Safety | Approved local campus emergency numbers, evacuation maps/routes, assembly areas, equipment locations, and safety-plan version. Generic draft instructions are not promoted to campus-specific advice. |
| Accessibility | Checked ramps, elevators, accessible toilets/parking, assistance arrangements, and accessible routes. |
| Vehicles/parking | Meaning and exceptions of the 8:30 AM rule, actual gate hours, parking locations, speed limits, and enforcement rules. |
| Communications | Exact handbook/document references and designated channels for urgent announcements; no independent website availability check is claimed. |

No `route_data`, measured distance, or walking time was added. Relative positions
such as "beside the clinic" can support a location answer; they are not a reviewed
walking route from an arbitrary starting point.

The user clarified the Registrar's location on 23 October 2026 as **in front of
the main gate**. This supplied landmark is included in location answers, alongside
the previously supplied Main Building assignment. The clarification and new file
hash are recorded in the source registry and submission history. No extra staff
review or route measurements are claimed. Location-only questions omit route
warnings; explicit route/time questions still withhold unsupported details.

## Traceability and future updates

The unchanged original, extracted records, intake metadata, and selected-fact
mapping are in
[`data/submissions/school_confirmation_2026-10-23/`](../data/submissions/school_confirmation_2026-10-23/README.md).
`curation.json` records which fields were retained or omitted for each topic.

Record numbers differ from the old generated sample numbering. In particular,
submitted record 09 is the Registrar, while old sample 09 is Student Affairs.
The import uses new filenames to avoid mixing them.

When new information arrives, update the curated source, obtain review of the
changed facts, update the hash/review metadata, and re-ingest as described in
[the verification workflow](09_source_verification.md). The web app reloads its
session-local retrieval object when source/review files change and retains the
visible transcript; follow-up context is reset against current evidence.
