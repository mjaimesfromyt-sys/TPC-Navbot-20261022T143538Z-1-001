"""Regression coverage for overlapping startup persistence on Windows."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Barrier, Lock
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion import IngestionPipeline
from src.storage_io import atomic_text_writer, atomic_write_text
from src.vector_store import VectorStore


class AtomicStorageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)

    def test_failed_write_preserves_destination_and_other_writers_temporary(self):
        destination = self.base / "snapshot.json"
        destination.write_text('{"previous": true}', encoding="utf-8")
        other_temporary = self.base / ".snapshot.json.other-writer.tmp"
        other_temporary.write_text("another writer owns this", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "writer failed"):
            with atomic_text_writer(destination) as output:
                output.write('{"incomplete":')
                raise ValueError("writer failed")
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"previous": True})
        self.assertEqual(other_temporary.read_text(encoding="utf-8"), "another writer owns this")
        self.assertEqual(set(self.base.iterdir()), {destination, other_temporary})

    def test_persistent_windows_access_denied_is_bounded_and_not_hidden(self):
        destination = self.base / "snapshot.json"
        destination.write_text('{"previous": true}', encoding="utf-8")
        denied = PermissionError("permanent access denied")
        denied.winerror = 5
        with patch("src.storage_io.os.replace", side_effect=denied) as replace, \
                patch("src.storage_io.time.sleep") as sleep:
            with self.assertRaises(PermissionError):
                atomic_write_text(destination, '{"next": true}')
        self.assertEqual(replace.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertLess(sum(call.args[0] for call in sleep.call_args_list), 1)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"previous": True})
        self.assertEqual(list(self.base.iterdir()), [destination])

    def test_unclassified_permission_error_is_not_retried(self):
        destination = self.base / "snapshot.json"
        with patch("src.storage_io.os.replace", side_effect=PermissionError("access denied")) as replace, \
                patch("src.storage_io.time.sleep") as sleep:
            with self.assertRaises(PermissionError):
                atomic_write_text(destination, "{}")
        replace.assert_called_once()
        sleep.assert_not_called()
        self.assertEqual(list(self.base.iterdir()), [])

    def test_brief_windows_access_denied_succeeds_on_retry(self):
        destination = self.base / "snapshot.json"
        destination.write_text('{"previous": true}', encoding="utf-8")
        replace_file = os.replace
        denied = PermissionError("destination is temporarily open")
        denied.winerror = 5
        attempts = []

        def replace(source, target):
            attempts.append(Path(source))
            if len(attempts) == 1:
                raise denied
            replace_file(source, target)

        with patch("src.storage_io.os.replace", side_effect=replace), \
                patch("src.storage_io.time.sleep") as sleep:
            atomic_write_text(destination, '{"next": true}')
        self.assertEqual(len(attempts), 2)
        sleep.assert_called_once_with(0.02)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"next": True})
        self.assertEqual(list(self.base.iterdir()), [destination])

    def test_brief_windows_sharing_violation_is_retried_after_closing_file(self):
        destination = self.base / "snapshot.json"
        replace_file = os.replace
        violation = OSError("file is temporarily shared")
        violation.winerror = 32
        attempted = []

        def replace(source, target):
            attempted.append(Path(source))
            # Reopening the complete temporary verifies it is ready to publish.
            self.assertEqual(json.loads(Path(source).read_text(encoding="utf-8")), {"label": "Mañana"})
            if len(attempted) == 1:
                raise violation
            replace_file(source, target)

        with patch("src.storage_io.os.replace", side_effect=replace), \
                patch("src.storage_io.time.sleep") as sleep:
            atomic_write_text(destination, json.dumps({"label": "Mañana"}, ensure_ascii=False))
        self.assertEqual(len(attempted), 2)
        self.assertEqual(attempted[0], attempted[1])
        sleep.assert_called_once_with(0.02)
        self.assertEqual(list(self.base.iterdir()), [destination])

    def test_windows_sharing_retries_are_bounded(self):
        destination = self.base / "snapshot.json"
        violation = OSError("persistent sharing violation")
        violation.winerror = 33
        with patch("src.storage_io.os.replace", side_effect=violation) as replace, \
                patch("src.storage_io.time.sleep") as sleep:
            with self.assertRaises(OSError):
                atomic_write_text(destination, "{}")
        self.assertEqual(replace.call_count, 6)
        self.assertEqual(sleep.call_count, 5)
        self.assertEqual(list(self.base.iterdir()), [])

    def _assert_overlapping_writes(self, destination, writers, expected, *, jsonl=False):
        def read(path):
            text = Path(path).read_text(encoding="utf-8")
            return [json.loads(line) for line in text.splitlines()] if jsonl else json.loads(text)

        previous = [{"previous": True}] if jsonl else {"previous": True}
        destination.write_text(json.dumps({"previous": True}) + "\n", encoding="utf-8")
        at_replace = Barrier(2)
        publication = Lock()
        replace_file = os.replace
        temporary_paths, staged, observed = [], [], []

        def overlap(source, target):
            self.assertEqual(Path(source).parent, destination.parent)
            self.assertEqual(Path(target), destination)
            temporary_paths.append(Path(source))
            staged.append(read(source))
            # Both writers must finish writing before either can publish. A
            # shared fixed temporary filename loses one writer at os.replace.
            at_replace.wait(timeout=10)
            with publication:
                observed.append(read(destination))
                replace_file(source, target)
                observed.append(read(destination))

        with patch("src.storage_io.os.replace", side_effect=overlap):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(writer) for writer in writers]
                for future in futures:
                    future.result(timeout=15)
        self.assertEqual(len(set(temporary_paths)), 2)
        self.assertCountEqual(staged, expected)
        self.assertIn(read(destination), expected)
        for snapshot in observed:
            self.assertIn(snapshot, [previous] + expected)
        self.assertEqual(list(destination.parent.iterdir()), [destination])

    def test_concurrent_manifest_publications_keep_complete_private_payloads(self):
        destination = self.base / "manifest.json"
        expected = [{"source-a.txt": "hash-a"}, {"source-b.txt": "hash-b"}]
        pipelines = []
        for manifest in expected:
            pipeline = object.__new__(IngestionPipeline)
            pipeline.manifest_path = str(destination)
            pipeline.manifest = manifest
            pipelines.append(pipeline)
        self._assert_overlapping_writes(destination, [p._save_manifest for p in pipelines], expected)

    def test_concurrent_processed_exports_keep_complete_private_payloads(self):
        destination = self.base / "chunks.jsonl"
        expected = [[{"text": f"Synthetic document {name}", "metadata": {"source_doc": name}}]
                    for name in ("a.txt", "b.txt")]
        pipelines = []
        for rows in expected:
            pipeline = object.__new__(IngestionPipeline)
            pipeline.processed_path = str(destination)
            pipeline.vector_store = SimpleNamespace(
                documents=[row["text"] for row in rows], metadatas=[row["metadata"] for row in rows])
            pipelines.append(pipeline)
        self._assert_overlapping_writes(destination, [p._export_processed for p in pipelines], expected, jsonl=True)

    def test_concurrent_vector_snapshots_keep_complete_private_payloads(self):
        destination = self.base / "vectors.json"
        stores, expected = [], []
        for name in ("a.txt", "b.txt"):
            row = {"id": name, "text": "Synthetic fixture", "metadata": {"source_doc": name}, "embedding": [1, 0]}
            store = object.__new__(VectorStore)
            store._persistent = True
            store._snapshot = destination
            store.embedding_signature = "synthetic-test-space"
            store._tracked_sources = {name}
            store._records = {name: row}
            stores.append(store)
            expected.append({"schema_version": 2, "embedding_signature": "synthetic-test-space",
                             "tracked_sources": [name], "source_chunk_counts": {name: 1}, "records": [row]})
        self._assert_overlapping_writes(destination, [s._save_snapshot for s in stores], expected)


if __name__ == "__main__":
    unittest.main()
