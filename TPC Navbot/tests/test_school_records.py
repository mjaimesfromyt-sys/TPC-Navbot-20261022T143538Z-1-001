"""Offline contracts for the supplied school-confirmed corpus and its limits.

These tests inspect the real records without changing their review metadata or
writing to the production ingestion manifest, processed corpus, or vector index.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import EmbeddingGenerator
from src.ingestion import IngestionPipeline
from src.llm_rag import MESSAGES, TPCNavBotRAG
from src.preprocessing import SourceRegistry
from src.vector_store import VectorStore


class SchoolConfirmedRecordsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = PROJECT_ROOT / "data" / "raw"
        cls.registry_path = PROJECT_ROOT / "data" / "source_registry.json"
        cls.entries = SourceRegistry(cls.registry_path).entries()
        cls.confirmed = {
            name: entry for name, entry in cls.entries.items()
            if name.startswith("school_confirmed_")
        }
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        temporary = Path(cls.temporary.name)
        cls.store = VectorStore(
            EmbeddingGenerator(mode="lexical"), backend="memory",
            persist_directory=temporary / "vectors", raw_data_dir=cls.raw,
            source_registry_path=cls.registry_path,
        )
        cls.ingestion = IngestionPipeline(
            raw_data_dir=cls.raw, source_registry_path=cls.registry_path,
            vector_store=cls.store, manifest_path=temporary / "manifest.json",
            processed_path=temporary / "processed" / "chunks.jsonl",
        )
        cls.summary = cls.ingestion.run()

    def setUp(self):
        self.bot = TPCNavBotRAG(
            vector_store=self.store, initialize_knowledge_base=False, use_llm=False,
        )

    def test_confirmed_records_have_content_bound_review_provenance(self):
        self.assertEqual(len(self.confirmed), 30)
        registry = SourceRegistry(self.registry_path)
        for name, entry in self.confirmed.items():
            with self.subTest(source=name):
                content = (self.raw / name).read_bytes()
                self.assertTrue(entry["verified"])
                self.assertEqual(entry["reviewed_by"], "Flordelis Tortuga")
                self.assertEqual(entry["reviewed_at"], "2026-10-23")
                self.assertIn("admin", entry["official_source"].lower())
                self.assertIn("handbook", entry["official_source"].lower())
                self.assertEqual(entry["sha256"], hashlib.sha256(content).hexdigest())
                self.assertTrue(registry.metadata(name, content)["verified_source"])
                self.assertNotIn("route_data", entry)

    def test_generated_samples_stay_unverified_and_out_of_student_retrieval(self):
        samples = {name: entry for name, entry in self.entries.items() if name.startswith("doc_")}
        self.assertEqual(len(samples), 30)
        for name, entry in samples.items():
            with self.subTest(source=name):
                self.assertFalse(entry["verified"])
                self.assertEqual(entry["source_type"], "generated_sample")
        self.assertGreater(self.summary["verified_chunks"], 0)
        self.assertEqual(
            {meta["source_doc"] for meta in self.store.metadatas if meta["verified_source"]},
            set(self.confirmed),
        )
        for query in ("library", "registrar", "guidance"):
            with self.subTest(query=query):
                hits = self.store.search(query)
                self.assertTrue(hits)
                self.assertTrue(all(hit["metadata"]["source_doc"] in self.confirmed for hit in hits))

    def test_library_location_hours_and_sources_in_three_languages(self):
        for language, query in (
            ("english", "Where is the library?"),
            ("bisaya", "Asa dapit ang library?"),
            ("tagalog", "Saan po ang aklatan?"),
        ):
            with self.subTest(language=language):
                answer = self.bot.chat(query, session_id="library-" + language)
                self.assertEqual(answer["status"], "SUCCESS")
                self.assertEqual(answer["language"], language)
                self.assertIn("canteen", answer["answer"].lower())
                self.assertTrue(answer["sources"])
                self.assertTrue(all(source.split(" [", 1)[0] in self.confirmed for source in answer["sources"]))
                self.assertEqual(answer["source_details"][0]["reviewed_at"], "2026-10-23")
                self.assertEqual(answer["source_details"][0]["reviewed_by"], "Flordelis Tortuga")
                self.assertIn("handbook", answer["source_details"][0]["official_source"].lower())
                self.assertNotIn("school_confirmed_", answer["answer"])
                self.assertNotIn(MESSAGES[language]["route_missing"], answer["answer"])
        hours = self.bot.query("What are the library office hours?")
        self.assertEqual(hours["status"], "SUCCESS")
        self.assertIn("8:00", hours["answer"])
        self.assertIn("5:00", hours["answer"])

    def test_destination_change_uses_relevant_evidence_instead_of_previous_source(self):
        registrar = self.bot.chat("Where is the Registrar's Office?")
        library = self.bot.chat("Where is the library?")
        self.assertEqual(registrar["status"], "SUCCESS")
        self.assertEqual(library["status"], "SUCCESS")
        registrar_source = registrar["source_details"][0]["source_doc"]
        library_source = library["source_details"][0]["source_doc"]
        self.assertIn("registrar", registrar_source)
        self.assertIn("library", library_source)
        self.assertNotEqual(registrar_source, library_source)
        self.assertNotIn(registrar_source, library["sources"][0])
        for response in (registrar, library):
            with self.subTest(source=response["source_details"][0]["source_doc"]):
                detail = response["source_details"][0]
                self.assertEqual(response["sources"], [
                    f"{detail['source_doc']} [{detail['official_source']}]",
                ])
                self.assertNotIn(detail["source_doc"], response["answer"])
                self.assertNotIn(detail["official_source"], response["answer"])

    def test_registrar_location_uses_supplied_main_gate_landmark_without_route_warning(self):
        answer = self.bot.query("Where is the Registrar's Office?")
        self.assertEqual(answer["status"], "SUCCESS")
        self.assertIn("in front of the main gate", answer["answer"].lower())
        self.assertNotIn(MESSAGES["english"]["route_missing"], answer["answer"])
        self.assertNotIn("Source:", answer["answer"])
        self.assertIn("registrar", answer["source_details"][0]["source_doc"])

    def test_registrar_landmark_does_not_invent_route_steps_or_walking_time(self):
        for query in ("Directions to the registrar from Main Gate?",
                      "How many minutes walking to the registrar from Main Gate?"):
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "SUCCESS")
                self.assertIn("in front of the main gate", answer["answer"].lower())
                self.assertIn(MESSAGES["english"]["route_missing"], answer["answer"])
                for field in ("walking", "distance", "directions"):
                    self.assertNotIn(MESSAGES["english"][field] + ":", answer["answer"])

    def test_guidance_uses_confirmed_location_instead_of_old_sample_room(self):
        answer = self.bot.query("Where is the Guidance Office?")
        self.assertEqual(answer["status"], "SUCCESS")
        self.assertIn("main", answer["answer"].lower())
        self.assertIn("clinic", answer["answer"].lower())
        self.assertTrue(answer["sources"])
        self.assertTrue(all(source.split(" [", 1)[0] in self.confirmed for source in answer["sources"]))

    def test_programs_laboratories_faculty_and_it_are_retrievable(self):
        cases = (
            ("What programs are offered at TPC?", "Bachelor of Science in Information Systems"),
            ("Where is ComLab 1?", "flagpole"),
            ("What are the computer laboratory rules?", "No eating or drinking"),
            ("Where is the faculty room?", "Main Building"),
            ("Where is the IT Office?", "Main Building"),
        )
        for query, expected in cases:
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "SUCCESS")
                self.assertIn(expected, answer["answer"])
                self.assertTrue(answer["sources"])
                self.assertTrue(all(source.split(" [", 1)[0] in self.confirmed for source in answer["sources"]))

    def test_unknown_fields_and_sample_room_numbers_are_not_filled_from_samples(self):
        for query in (
            "What is the library phone number?",
            "Is the library wheelchair accessible?",
            "Where is Room 203?",
            "What is the passing grade at TPC?",
            "What is the school calendar?",
            "What is the campus emergency hotline?",
            "What are the campus parking rules?",
        ):
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "UNVERIFIED")
                self.assertTrue(answer["answer"].startswith(MESSAGES["english"]["unverified"]))
                if query in ("What is the passing grade at TPC?", "What is the school calendar?"):
                    # These topics now help the student reach the approved
                    # referral while still withholding grades and dates.
                    self.assertIn("Confirm with:", answer["answer"])
                    self.assertTrue(answer["sources"])
                    self.assertTrue(all(source.split(" [", 1)[0] in self.confirmed for source in answer["sources"]))
                    self.assertNotRegex(answer["answer"], r"\b(?:75|2026|October|November)\b")
                else:
                    self.assertEqual(answer["sources"], [])
                    self.assertEqual(answer["answer"], MESSAGES["english"]["unverified"])

    def test_landmark_location_does_not_confer_measured_or_step_by_step_route(self):
        answer = self.bot.query("Directions to the library from Main Gate?")
        self.assertEqual(answer["status"], "SUCCESS")
        self.assertIn("canteen", answer["answer"].lower())
        self.assertIn(MESSAGES["english"]["route_missing"], answer["answer"])
        self.assertNotIn(MESSAGES["english"]["walking"] + ":", answer["answer"])
        self.assertNotIn(MESSAGES["english"]["distance"] + ":", answer["answer"])
        self.assertNotIn(MESSAGES["english"]["directions"] + ":", answer["answer"])


if __name__ == "__main__":
    unittest.main()
