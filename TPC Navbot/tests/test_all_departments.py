"""All seven supplied program names resolve without inventing office facts.

Real answers use a temporary lexical index of the reviewed corpus. Separate
synthetic office records exercise destination separation, never campus claims.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.embedding import EmbeddingGenerator
from src.ingestion import IngestionPipeline
from src.llm_rag import TPCNavBotRAG
from src.preprocessing import SourceRegistry
from src.vector_store import VectorStore
from test_guardrails import approved_hit, bot


# Expected names are independent of the production catalogue.
DEPARTMENTS = (
    ("english department", "BAEL", "English Language", "Bachelor of Arts in English Language", "english"),
    ("political science department", "BAPS", "Political Science", "Bachelor of Arts in Political Science", "political science"),
    ("education department", "BECED", "Early Childhood Education", "Bachelor in Early Childhood Education", "education"),
    ("agriculture department", "BSAG", "Agriculture", "Bachelor of Science in Agriculture", "agriculture"),
    ("bsais department", "BSAIS", "Accounting Information Systems", "Bachelor of Science in Accounting Information Systems", "accounting information systems"),
    ("criminology department", "BSCRIM", "Criminology", "Bachelor of Science in Criminology", "criminology"),
    ("bsis department", "BSIS", "Information Systems", "Bachelor of Science in Information Systems", "information systems"),
)


class AllDepartmentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = Path(cls.temporary.name)
        raw = PROJECT_ROOT / "data" / "raw"
        registry = PROJECT_ROOT / "data" / "source_registry.json"
        cls.store = VectorStore(
            EmbeddingGenerator(mode="lexical"), backend="memory",
            persist_directory=temporary / "vectors", raw_data_dir=raw,
            source_registry_path=registry,
        )
        IngestionPipeline(
            raw_data_dir=raw, source_registry_path=registry,
            vector_store=cls.store, manifest_path=temporary / "manifest.json",
            processed_path=temporary / "chunks.jsonl",
        ).run()

    def setUp(self):
        self.nav = TPCNavBotRAG(
            vector_store=self.store, initialize_knowledge_base=False, use_llm=False,
        )

    def test_all_program_subjects_acronyms_and_office_variants_are_understood(self):
        for entity, acronym, subject, program, _ in DEPARTMENTS:
            for name in (acronym, subject, program):
                for query in (name, f"{name} office", f"{name} department", f"{name} dept"):
                    with self.subTest(query=query):
                        self.assertEqual(self.nav._entity(query), entity)
                        self.assertEqual(self.nav._intent(query), "location")
                        self.assertTrue(self.nav.is_in_scope(query))
        for query, entity in (
            ("PolSci office", "political science department"),
            ("BSA department", "agriculture department"),
            ("Education department", "education department"),
            ("English department", "english department"),
        ):
            with self.subTest(query=query):
                self.assertEqual(self.nav._entity(query), entity)
                self.assertTrue(self.nav.is_in_scope(query))

    def test_real_department_locations_use_only_their_reviewed_sources(self):
        known = {
            "bsis department": ("inside the main building", "user_confirmed_bsis_office.txt"),
            "bsais department": ("inside the main building", "user_confirmed_bsais_office.txt"),
            "english department": ("inside the main building", "user_confirmed_bael_office.txt"),
            "political science department": ("inside the main building", "user_confirmed_baps_office.txt"),
            "education department": ("inside the main building", "user_confirmed_beced_office.txt"),
            "criminology department": ("behind the main building", "school_confirmed_03_criminology_building.txt"),
            "agriculture department": ("to the right from the main gate", "school_confirmed_04_agriculture_building_field_office.txt"),
        }
        for entity, acronym, _, _, label in DEPARTMENTS:
            with self.subTest(department=entity):
                response = self.nav.query(f"Where is the {acronym} department?")
                landmark, source = known[entity]
                self.assertEqual(response["status"], "SUCCESS", response)
                self.assertIn(landmark, response["answer"].casefold())
                self.assertEqual(response["source_details"][0]["source_doc"], source)

    def test_full_subject_location_questions_work_in_three_languages(self):
        for entity, _, subject, _, label in DEPARTMENTS:
            for template, language in (
                ("Where is the {name} department?", "english"),
                ("Asa dapit ang {name} department?", "bisaya"),
                ("Saan po ang {name} department?", "tagalog"),
            ):
                query = template.format(name=subject)
                with self.subTest(query=query):
                    response = self.nav.query(query)
                    self.assertEqual(response["status"], "SUCCESS", response)
                    self.assertEqual(response["language"], language)
                    self.assertEqual(self.nav._entity(query), entity)
                    self.assertIn(label, response["answer"].casefold())

    def test_program_availability_answers_only_the_requested_reviewed_title(self):
        for _, acronym, subject, program, _ in DEPARTMENTS:
            for query in (
                f"Does TPC offer {acronym}?",
                f"Does TPC offer {subject}?",
                f"Do you offer {program}?",
            ):
                with self.subTest(query=query):
                    response = self.nav.query(query)
                    self.assertEqual(response["status"], "SUCCESS", response)
                    self.assertIn(program, response["answer"])
                    for _, _, _, other_program, _ in DEPARTMENTS:
                        if other_program != program:
                            self.assertNotIn(other_program, response["answer"])
                    self.assertEqual(response["source_details"][0]["source_doc"],
                                     "school_confirmed_20_academic_programs_and_departments.txt")

    def test_all_department_list_questions_use_the_reviewed_seven_programs(self):
        for query, language in (
            ("List all departments", "english"),
            ("What departments does TPC have?", "english"),
            ("What departments are offered?", "english"),
            ("Unsa ang mga departamento sa TPC?", "bisaya"),
            ("Ano ang mga departamento sa TPC?", "tagalog"),
        ):
            with self.subTest(query=query):
                response = self.nav.query(query)
                self.assertEqual(response["status"], "SUCCESS", response)
                self.assertEqual(response["language"], language)
                for _, _, _, program, _ in DEPARTMENTS:
                    self.assertIn(program, response["answer"])
                self.assertEqual(len(response["source_details"]), 1)
                self.assertEqual(response["source_details"][0]["source_doc"],
                                 "school_confirmed_20_academic_programs_and_departments.txt")
                self.assertNotIn("Main Building", response["answer"])

    def test_user_confirmed_office_sources_are_content_bound_and_location_only(self):
        registry = SourceRegistry(PROJECT_ROOT / "data" / "source_registry.json")
        entries = registry.entries()
        for short_name in ("bsis", "bsais", "bael", "baps", "beced"):
            filename = f"user_confirmed_{short_name}_office.txt"
            with self.subTest(source=filename):
                content = (PROJECT_ROOT / "data" / "raw" / filename).read_bytes()
                entry = entries[filename]
                self.assertNotIn(b"\r\n", content)
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())
                self.assertEqual(entry["reviewed_at"], "2026-10-24")
                self.assertEqual(entry["review_method"], "location_confirmation_reported_by_user")
                self.assertIn("direct", entry["reviewed_by"].casefold())
                self.assertTrue(registry.metadata(filename, content)["verified_source"])
                self.assertFalse(registry.metadata(filename, content + b"changed")["verified_source"])
                facts = entry["location_data"]
                self.assertIn("inside the main building", facts["location"].casefold())
                for field in ("floor", "room", "hours", "staff"):
                    self.assertNotIn(field, facts)
                self.assertNotIn("route_data", entry)

    def test_missing_department_hours_keep_the_current_department_subject(self):
        for entity, acronym, _, _, label in DEPARTMENTS:
            with self.subTest(department=entity):
                session_id = "department-hours-" + acronym
                self.nav.chat(f"{acronym} office", session_id=session_id)
                response = self.nav.chat("What are its hours?", session_id=session_id)
                self.assertEqual(response["status"], "UNVERIFIED", response)
                self.assertIn(label, response["answer"].casefold())
                self.assertEqual(response["sources"], [])
                self.assertNotIn("8:00", response["answer"])
                self.assertEqual(self.nav.memory_manager.get_session(session_id).last_entity, entity)

    def test_seven_synthetic_offices_never_borrow_another_programs_room(self):
        fixtures = []
        for index, (_, acronym, _, _, _) in enumerate(DEPARTMENTS):
            hit = approved_hit(
                f"{acronym} Department Office", building=f"Synthetic Hall {index}",
                room=f"FIXTURE-{index + 701}",
            )
            hit["metadata"]["source_doc"] = f"fictional-{acronym.lower()}-office.txt"
            fixtures.append(hit)
        nav = bot(fixtures, use_llm=False)
        for index, (_, acronym, subject, program, _) in enumerate(DEPARTMENTS):
            for query in (f"{acronym} office", f"Where is the {subject} department?", f"{program} office"):
                with self.subTest(query=query):
                    response = nav.query(query)
                    self.assertEqual(response["status"], "SUCCESS", response)
                    self.assertIn(f"FIXTURE-{index + 701}", response["answer"])
                    self.assertEqual(response["source_details"][0]["source_doc"],
                                     f"fictional-{acronym.lower()}-office.txt")
                    for other_index in range(len(DEPARTMENTS)):
                        if other_index != index:
                            self.assertNotIn(f"FIXTURE-{other_index + 701}", response["answer"])

    def test_department_aliases_preserve_external_and_named_place_qualifiers(self):
        for _, acronym, subject, _, _ in DEPARTMENTS:
            for query, status in (
                (f"Where is the {acronym} office at MIT?", "OFF_TOPIC"),
                (f"Where is the Graduate {subject} office at TPC?", "UNVERIFIED"),
                (f"Where is the {acronym} office in the Science Building at TPC?", "UNVERIFIED"),
            ):
                with self.subTest(query=query):
                    response = self.nav.query(query)
                    self.assertEqual(response["status"], status, response)
                    self.assertEqual(response["sources"], [])
                    self.assertNotIn("main building", response["answer"].casefold())

    def test_missing_synthetic_department_does_not_borrow_another_office(self):
        for _, acronym, _, _, label in DEPARTMENTS:
            fixtures = []
            for other_entity, other_acronym, _, _, _ in DEPARTMENTS:
                if other_acronym == acronym:
                    continue
                hit = approved_hit(
                    f"{other_acronym} Department Office", building="Unrelated Synthetic Hall",
                    room="UNRELATED-999",
                )
                hit["metadata"]["source_doc"] = f"fictional-{other_entity.replace(' ', '-')}.txt"
                fixtures.append(hit)
            with self.subTest(department=acronym):
                response = bot(fixtures, use_llm=False).query(f"Where is the {acronym} office?")
                self.assertEqual(response["status"], "UNVERIFIED", response)
                self.assertIn(label, response["answer"].casefold())
                self.assertEqual(response["sources"], [])
                self.assertNotIn("Unrelated Synthetic Hall", response["answer"])
                self.assertNotIn("UNRELATED-999", response["answer"])

    def test_accounting_service_and_language_requests_do_not_become_departments(self):
        self.assertEqual(self.nav._entity("Where is the accounting office?"), "cashier")
        for query in (
            "Explain English grammar.",
            "Write an essay in English.",
            "Please answer in English.",
            "Where is the BAEL office? Explain binary search.",
            "Where is the BAPS department and tell me the weather?",
        ):
            with self.subTest(query=query):
                response = self.nav.query(query)
                self.assertEqual(response["status"], "OFF_TOPIC", response)
                self.assertEqual(response["sources"], [])


if __name__ == "__main__":
    unittest.main()
