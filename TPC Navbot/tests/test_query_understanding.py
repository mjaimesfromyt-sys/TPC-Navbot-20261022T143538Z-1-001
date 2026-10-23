"""Campus query recognition contracts using the actual approved school corpus.

The query aliases below express student wording, not additional school facts.
All ingestion artifacts stay in a temporary directory and use an in-memory store.
"""
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import EmbeddingGenerator
from src.ingestion import IngestionPipeline
from src.llm_rag import MESSAGES, TPCNavBotRAG
from src.vector_store import VectorStore


class CampusQueryUnderstandingTests(unittest.TestCase):
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
        self.bot = TPCNavBotRAG(
            vector_store=self.store, initialize_knowledge_base=False, use_llm=False,
        )

    def assert_location_answer(self, query, landmark, source):
        # Each query is independent: a previous answer cannot supply its entity.
        answer = self.bot.chat(query, session_id="independent-" + query)
        self.assertEqual(answer["status"], "SUCCESS", answer["answer"])
        self.assertIn(landmark.casefold(), answer["answer"].casefold())
        self.assertTrue(answer["source_details"])
        self.assertTrue(all(
            source in detail["source_doc"] for detail in answer["source_details"]
        ), answer["source_details"])
        self.assertNotIn("school_confirmed_", answer["answer"])
        self.assertNotIn("Source:", answer["answer"])
        self.assertNotIn(MESSAGES[answer["language"]]["route_missing"], answer["answer"])
        return answer

    def test_crim_nickname_and_bare_building_queries_use_reviewed_location(self):
        for query in ("crim building", "crim", "BSCRIM", "Criminology Building", "crim bldg", "I need crim building"):
            with self.subTest(query=query):
                answer = self.assert_location_answer(query, "behind the main building", "criminology")
                self.assertEqual(
                    answer["answer"],
                    "The Criminology Building is behind the main building.",
                )

    def test_student_location_phrasing_in_three_languages(self):
        cases = (
            ("Where is the crim building?", "english"),
            ("crim building location", "english"),
            ("Asa ang crim building?", "bisaya"),
            ("Asa dapit ang crim?", "bisaya"),
            ("Nasaan ang crim?", "tagalog"),
            ("Saan po ang crim building?", "tagalog"),
        )
        for query, language in cases:
            with self.subTest(query=query):
                answer = self.assert_location_answer(query, "behind the main building", "criminology")
                self.assertEqual(answer["language"], language)

    def test_other_short_place_queries_choose_their_own_records(self):
        for query, landmark, source in (
            ("registrar", "in front of the main gate", "registrar"),
            ("library", "canteen", "library"),
            ("comlab", "flagpole", "computer_laborator"),
            ("ComLab 1", "flagpole", "computer_laborator"),
            ("faculty room", "Main Building", "faculty"),
            ("registar", "in front of the main gate", "registrar"),
            ("libray", "canteen", "library"),
            ("asa ang kantina", "left side", "canteen"),
            ("saan ang klinika", "guidance", "clinic"),
        ):
            with self.subTest(query=query):
                self.assert_location_answer(query, landmark, source)

    def test_explicit_services_and_hours_are_not_replaced_with_location(self):
        services = self.bot.query("What services are in the crim building?")
        self.assertEqual(services["status"], "SUCCESS", services["answer"])
        self.assertIn("classrooms", services["answer"].casefold())
        self.assertTrue(all("criminology" in item["source_doc"] for item in services["source_details"]))
        hours = self.bot.query("library opening hours")
        self.assertEqual(hours["status"], "SUCCESS", hours["answer"])
        self.assertIn("8:00", hours["answer"])
        self.assertIn("5:00", hours["answer"])
        self.assertNotIn("behind the main building", hours["answer"].casefold())

    def test_closing_time_phrasing_uses_hours_in_english_and_bisaya(self):
        for query, language in (
            ("what time does library close", "english"),
            ("unsang orasa mosira ang library", "bisaya"),
        ):
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "SUCCESS", answer["answer"])
                self.assertEqual(answer["language"], language)
                self.assertIn("5:00", answer["answer"])
                self.assertTrue(all("library" in item["source_doc"] for item in answer["source_details"]))
                self.assertNotIn(MESSAGES[language]["route_missing"], answer["answer"])

    def test_nickname_route_does_not_invent_steps_or_measurements(self):
        answer = self.bot.query("Directions to the crim building from Main Gate?")
        self.assertEqual(answer["status"], "SUCCESS", answer["answer"])
        self.assertIn("behind the main building", answer["answer"].casefold())
        self.assertIn(MESSAGES["english"]["route_missing"], answer["answer"])
        for field in ("walking", "distance", "directions"):
            self.assertNotIn(MESSAGES["english"][field] + ":", answer["answer"])

    def test_unreviewed_fields_and_unknown_named_campus_places_stay_unverified(self):
        for query in (
            "What is the crim building phone number?",
            "Where is the Science Library at TPC?",
            "Where is the Graduate School Building at TPC?",
            "Science Library",
            "Science Library hours",
            "What are the Science Library hours?",
            "What is the Science Library phone number?",
            "Science Library services",
        ):
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "UNVERIFIED", answer["answer"])
                self.assertEqual(answer["sources"], [])
                self.assertEqual(answer["source_details"], [])

    def test_external_destinations_and_unrelated_requests_do_not_borrow_campus_facts(self):
        for query in (
            "Where is the public library?",
            "Where is the library at Harvard?",
            "airport library",
            "crim building and tell me the weather",
            "What is criminology? Explain criminal law.",
            "Write an essay about the library",
        ):
            with self.subTest(query=query):
                answer = self.bot.query(query)
                self.assertEqual(answer["status"], "OFF_TOPIC", answer["answer"])
                self.assertEqual(answer["sources"], [])
                self.assertEqual(answer["source_details"], [])

    def test_short_destination_change_does_not_reuse_previous_campus_subject(self):
        first = self.bot.chat("Where is the Registrar's Office?", session_id="changed-place")
        second = self.bot.chat("crim building", session_id="changed-place")
        self.assertEqual(first["status"], "SUCCESS")
        self.assertEqual(second["status"], "SUCCESS", second["answer"])
        self.assertIn("behind the main building", second["answer"].casefold())
        self.assertNotIn("in front of the main gate", second["answer"].casefold())
        self.assertTrue(all("criminology" in item["source_doc"] for item in second["source_details"]))


if __name__ == "__main__":
    unittest.main()
