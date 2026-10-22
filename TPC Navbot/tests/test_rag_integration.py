"""One offline integration contract; all campus facts here are synthetic fixtures."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.embedding import EmbeddingGenerator
from src.llm_rag import TPCNavBotRAG
from src.preprocessing import TextPreprocessor
from src.vector_store import VectorStore


class RAGIntegrationTests(unittest.TestCase):
    def test_reviewed_multilingual_routes_revocation_and_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            raw = base / "raw"
            raw.mkdir()
            source = raw / "synthetic_library.txt"
            source.write_text(
                "Building Name: Synthetic Test Hall\nLocation ID: TEST-ONLY\n\n"
                "Destination: Library\nRoom: TEST101\n"
                "Synthetic campus test fixture only: library directions route from Main Gate.\n",
                encoding="utf-8")
            steps = {"english": ["Use the signed synthetic corridor."],
                     "bisaya": ["Sunda ang timailhan sa sintetikong agianan."],
                     "tagalog": ["Sundan ang palatandaan sa sintetikong daan."]}
            registry = base / "registry.json"
            registry.write_text(json.dumps({"documents": {source.name: {
                "verified": True, "source_type": "authorized_campus_record",
                "official_source": "SYNTHETIC TEST FIXTURE; not a real campus source",
                "reviewed_by": "Automated test", "reviewed_at": "2020-01-01",
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "location_data": {"destination": "Library", "building": "Synthetic Test Hall", "room": "TEST101"},
                "route_data": {"destination": "Library", "start": "Main Gate", "steps": steps,
                               "walking_minutes": 2, "distance_m": 12},
            }}}), encoding="utf-8")
            processor = TextPreprocessor(source_registry_path=registry)
            store = VectorStore(EmbeddingGenerator(mode="lexical"), backend="memory",
                                raw_data_dir=raw, source_registry_path=registry)
            store.add_chunks(processor.process_directory(raw))
            bot = TPCNavBotRAG(vector_store=store, initialize_knowledge_base=False, use_llm=False)
            cases = (
                ("english", "Directions to Library from Main Gate?", "Explain quantum physics."),
                ("bisaya", "Unsaon pag-adto sa library gikan sa Main Gate?", "Unsa ang quantum physics?"),
                ("tagalog", "Paano pumunta sa library mula sa Main Gate?", "Ano ang quantum physics?"),
            )
            for language, question, unrelated in cases:
                with self.subTest(language=language):
                    answer = bot.chat(question, session_id=language)
                    self.assertEqual(answer["status"], "SUCCESS")
                    self.assertEqual(answer["language"], language)
                    self.assertIn(steps[language][0], answer["answer"])
                    self.assertIn("2 " + ("minutes" if language == "english" else "minuto"), answer["answer"])
                    self.assertTrue(answer["sources"])
                    refusal = bot.chat(unrelated, session_id=language)
                    self.assertEqual(refusal["status"], "OFF_TOPIC")
                    self.assertEqual(refusal["language"], language)
                    self.assertEqual(refusal["sources"], [])
            wrong_start = bot.query("Directions to Library from Main Entrance?")
            self.assertNotIn(steps["english"][0], wrong_start["answer"])
            self.assertNotIn("2 minutes", wrong_start["answer"])
            # A source change invalidates approval at search time, before ingestion.
            source.write_text(source.read_text(encoding="utf-8") + "Edited after review.\n", encoding="utf-8")
            for language, question, _ in cases:
                answer = bot.chat(question, session_id="edited-" + language)
                self.assertEqual(answer["status"], "UNVERIFIED")
                self.assertEqual(answer["language"], language)
                self.assertEqual(answer["sources"], [])
                self.assertNotIn(steps[language][0], answer["answer"])


if __name__ == "__main__":
    unittest.main()
