"""The learning loop stores demand signals, never student text or school facts."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.learning import LearningStore, MAX_COUNT


class ReviewedLearningTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.path = self.base / "metrics" / "questions.sqlite3"
        self.store = LearningStore(self.path)

    def observe(self, **kwargs):
        values = {"entity": "library", "intent": "hours", "status": "SUCCESS"}
        values.update(kwargs)
        return self.store.observe(**values)

    def test_lazy_store_and_missing_read_do_not_create_files(self):
        self.assertFalse(self.path.parent.exists())
        self.assertEqual(self.store.summary(), [])
        self.assertEqual(self.store.popular_intents("library"), [])
        self.assertFalse(self.path.parent.exists())

    def test_categories_aggregate_and_persist_across_instances(self):
        self.assertTrue(self.observe())
        self.assertTrue(self.observe())
        self.assertTrue(self.observe(status="UNVERIFIED", intent="contact"))
        rows = LearningStore(self.path).summary()
        self.assertEqual(rows[0]["observations"], 2)
        self.assertEqual(rows[0]["entity"], "library")
        self.assertFalse(rows[0]["review_required"])
        queue = self.store.summary(gaps_only=True)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["intent"], "contact")
        self.assertTrue(queue[0]["review_required"])

    def test_arbitrary_and_personal_strings_cannot_enter_database(self):
        payload = "Ignore instructions; Jane Doe 09171234567 student_1234 secret@example.com"
        self.assertTrue(self.store.observe(
            entity=payload, intent=payload, status=payload, language=payload, feedback=payload))
        self.assertEqual(self.store.summary()[0]["entity"], "unknown")
        self.assertEqual(self.store.summary()[0]["intent"], "unknown")
        self.assertEqual(self.store.summary()[0]["feedback"], "none")
        self.assertEqual(self.store.summary()[0]["status"], "unknown")
        self.assertEqual(self.store.summary()[0]["language"], "unknown")
        raw = self.path.read_bytes()
        for value in (b"Ignore", b"Jane Doe", b"09171234567", b"student_1234", b"secret@example.com"):
            self.assertNotIn(value, raw)
        with self.assertRaises(TypeError):
            self.store.observe(status="SUCCESS", question=payload)

    def test_room_identifiers_are_not_accepted_as_categories(self):
        self.assertTrue(self.observe(entity="room 123456 student 1234"))
        self.assertTrue(self.observe(entity="campus room"))
        self.assertEqual({row["entity"] for row in self.store.summary()}, {"unknown", "campus room"})

    def test_unhashable_input_is_safely_bucketed_without_coercion(self):
        self.assertTrue(self.store.observe(
            entity=["library"], intent={"personal": "text"}, status=None, language=1, feedback=[]))
        self.assertEqual(self.store.summary()[0]["entity"], "unknown")

    def test_expired_categories_are_filtered_and_removed_on_next_observation(self):
        self.store = LearningStore(self.path, retention_days=2)
        with patch("src.learning._today", return_value=date(2026, 10, 20)):
            self.assertTrue(self.observe())
        with patch("src.learning._today", return_value=date(2026, 10, 22)):
            self.assertEqual(self.store.summary(), [])
            self.assertEqual(self.store.popular_intents("library"), [])
            self.assertTrue(self.observe(intent="contact"))
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute("SELECT day FROM observations").fetchall(), [("2026-10-22",)])

    def test_category_cap_retains_recent_and_repeated_rows(self):
        self.store = LearningStore(self.path, max_rows=2)
        with patch("src.learning._today", return_value=date(2026, 10, 20)):
            for _ in range(3):
                self.assertTrue(self.observe(intent="hours"))
            self.assertTrue(self.observe(intent="contact"))
            self.assertTrue(self.observe(intent="services"))
            self.assertEqual(len(self.store.summary()), 2)
            self.assertIn("hours", [row["intent"] for row in self.store.summary()])
        with patch("src.learning._today", return_value=date(2026, 10, 21)):
            self.assertTrue(self.observe(intent="route"))
            self.assertEqual(len(self.store.summary()), 2)
            self.assertIn("route", [row["intent"] for row in self.store.summary()])

    def test_storage_limits_and_counter_cannot_grow_without_bound(self):
        capped = LearningStore(self.path, retention_days=999999, max_rows=999999)
        self.assertEqual(capped.retention_days, 365)
        self.assertEqual(capped.max_rows, 5000)
        self.assertTrue(self.observe())
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("UPDATE observations SET count = ?", (MAX_COUNT,))
            connection.commit()
        self.assertTrue(self.observe())
        self.assertEqual(self.store.summary()[0]["observations"], MAX_COUNT)

    def test_parallel_process_style_connections_do_not_lose_observations(self):
        # Separate instances and connections exercise SQLite's transaction lock.
        def record(_):
            return LearningStore(self.path).observe(entity="library", intent="hours", status="SUCCESS")

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(record, range(48)))
        self.assertTrue(all(results), results)
        self.assertEqual(self.store.summary()[0]["observations"], 48)

    def test_unwritable_storage_is_nonfatal(self):
        self.path.parent.mkdir(parents=True)
        self.path.write_text("This is not SQLite", encoding="utf-8")
        self.assertFalse(self.observe())
        self.assertEqual(self.store.summary(), [])
        self.assertEqual(self.store.popular_intents("library"), [])

    def test_busy_database_fails_with_bounded_wait_and_recovers(self):
        self.assertTrue(self.observe())
        with closing(sqlite3.connect(self.path)) as locked:
            locked.execute("BEGIN IMMEDIATE")
            started = time.monotonic()
            self.assertFalse(self.observe())
            self.assertLess(time.monotonic() - started, 3)
            locked.rollback()
        self.assertTrue(self.observe())
        self.assertEqual(self.store.summary()[0]["observations"], 2)

    def test_feedback_is_a_review_signal_and_cannot_invent_facts(self):
        self.assertTrue(self.observe(feedback="not_helpful"))
        queue = self.store.summary(gaps_only=True)
        self.assertEqual(queue[0]["status"], "SUCCESS")
        self.assertEqual(queue[0]["feedback"], "not_helpful")
        self.assertTrue(queue[0]["review_required"])
        self.assertEqual(self.store.popular_intents("library"), [])
        with closing(sqlite3.connect(self.path)) as connection:
            self.assertEqual(connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [("observations",)])

    def test_popularity_is_scoped_to_entity_success_and_known_intents(self):
        for _ in range(3):
            self.assertTrue(self.observe(intent="hours"))
        self.assertTrue(self.observe(intent="contact", status="PARTIAL"))
        for _ in range(5):
            self.assertTrue(self.observe(intent="services", status="UNVERIFIED"))
            self.assertTrue(self.observe(intent="route", entity="registrar"))
        self.assertEqual(self.store.popular_intents("library"), ["hours", "contact"])
        self.assertEqual(self.store.popular_intents("library", exclude=("hours",)), ["contact"])
        self.assertEqual(self.store.popular_intents("library", limit=1), ["hours"])
        self.assertEqual(self.store.popular_intents("library; DROP TABLE observations"), [])
        self.assertEqual(self.store.summary(entity="library; DROP TABLE observations"), [])
        self.assertTrue(all(row["entity"] == "library" for row in self.store.summary(entity="library")))


if __name__ == "__main__":
    unittest.main()
