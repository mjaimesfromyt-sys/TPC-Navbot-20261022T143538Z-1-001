"""Offline tests: synthetic fixtures are test data, never real campus verification."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.embedding import EmbeddingGenerator
from src.ingestion import IngestionPipeline
from src.preprocessing import SourceRegistry, TextPreprocessor
from src.vector_store import VectorStore


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.raw = self.base / "raw"
        self.raw.mkdir()
        self.registry = self.base / "registry.json"
        self.file = self.raw / "test_library.txt"
        self.file.write_text("Building Name: Synthetic Test Library\nLocation ID: TEST-001\n\n" +
                             "Synthetic library books and study services. " * 50, encoding="utf-8")
        self.embedder = EmbeddingGenerator(mode="lexical")
        self.processor = TextPreprocessor(source_registry_path=self.registry)

    def approve(self, **changes):
        entry = {"verified": True, "source_type": "official_document", "official_source": "TEST FIXTURE ONLY",
                 "reviewed_by": "Automated synthetic fixture", "reviewed_at": "2020-01-01",
                 "sha256": hashlib.sha256(self.file.read_bytes()).hexdigest()}
        entry.update(changes)
        self.registry.write_text(json.dumps({"documents": {self.file.name: entry}}), encoding="utf-8")

    def store(self, backend="memory", **options):
        return VectorStore(self.embedder, persist_directory=self.base / "vectors", backend=backend,
                           raw_data_dir=self.raw, source_registry_path=self.registry, **options)

    def pipeline(self, store):
        return IngestionPipeline(self.raw, self.base / "manifest.json", store, self.registry,
                                 processed_path=self.base / "processed" / "chunks.jsonl")

    def test_missing_registry_and_direct_chunking_fail_closed(self):
        chunks = self.processor.process_file(self.file)
        self.assertTrue(chunks)
        self.assertTrue(all(c["metadata"]["verified_source"] is False for c in chunks))
        direct = self.processor.chunk_text("Library location test", self.processor.extract_metadata("", "test.txt"))
        self.assertFalse(direct[0]["metadata"]["verified_source"])

    def test_chunks_are_bounded_and_ids_are_repeatable(self):
        chunks = self.processor.process_file(self.file)
        self.assertTrue(all(len(c["text"]) <= 400 for c in chunks))
        self.assertEqual(chunks, self.processor.process_file(self.file))
        self.assertEqual(len(chunks), len({c["metadata"]["chunk_id"] for c in chunks}))
        text = "x" * 2400
        chunks = self.processor.chunk_text(text, self.processor.extract_metadata(text, "long.txt"))
        self.assertGreater(len(chunks), 5)
        self.assertTrue(all(len(c["text"]) <= 400 for c in chunks))

    def test_real_review_fields_and_hash_are_required(self):
        for changes in ({"verified": "true"}, {"official_source": None}, {"reviewed_by": ""},
                        {"reviewed_at": "not-a-date"}, {"reviewed_at": "2999-01-01"},
                        {"sha256": "wrong"}, {"source_type": "generated_sample"}):
            with self.subTest(changes=changes):
                self.approve(**changes)
                self.assertFalse(self.processor.process_file(self.file)[0]["metadata"]["verified_source"])
        self.approve()
        self.assertTrue(self.processor.process_file(self.file)[0]["metadata"]["verified_source"])

    def test_malformed_registry_does_not_confer_trust(self):
        for payload in ("not json", "null", "[]", '{"documents": []}', '{"documents": {"test_library.txt": true}}'):
            self.registry.write_text(payload, encoding="utf-8")
            self.assertFalse(self.processor.process_file(self.file)[0]["metadata"]["verified_source"])

    def test_structured_route_data_only_from_validated_review(self):
        route = {"destination": "Synthetic library", "start": "Synthetic gate", "walking_minutes": 2}
        self.approve(route_data=route)
        metadata = self.processor.process_file(self.file)[0]["metadata"]
        self.assertEqual(json.loads(metadata["route_data"]), route)
        self.approve(verified=False, route_data=route)
        self.assertNotIn("route_data", self.processor.process_file(self.file)[0]["metadata"])

    def test_lexical_fallback_is_explicit_and_deterministic(self):
        a = self.embedder.embed_text("synthetic library books")
        b = EmbeddingGenerator(mode="lexical").embed_text("synthetic library books")
        self.assertEqual(a, b)
        self.assertEqual(len(a), 384)
        self.assertFalse(self.embedder.is_semantic)
        self.assertIn("not semantic", self.embedder.description)
        self.assertAlmostEqual(sum(x*x for x in a), 1.0)

    def test_prepared_local_model_is_default_but_explicit_overrides_win(self):
        model_dir = self.base / "data" / "models" / "all-MiniLM-L6-v2"
        model_dir.mkdir(parents=True)
        (model_dir / "modules.json").write_text("[]", encoding="utf-8")
        (model_dir / "config.json").write_text("{}", encoding="utf-8")
        with patch("src.embedding.PROJECT_ROOT", self.base), patch.dict("os.environ", {"TPC_EMBEDDING_MODEL": ""}):
            self.assertEqual(EmbeddingGenerator(mode="lexical").model_name, str(model_dir))
            self.assertEqual(EmbeddingGenerator(mode="lexical", model_name="explicit-local").model_name, "explicit-local")
        with patch("src.embedding.PROJECT_ROOT", self.base), patch.dict("os.environ", {"TPC_EMBEDDING_MODEL": "env-local"}):
            self.assertEqual(EmbeddingGenerator(mode="lexical").model_name, "env-local")

    def test_similarity_metrics_and_dimension_validation(self):
        self.assertEqual(self.embedder.cosine_similarity([1, 0], [1, 0]), 1)
        self.assertEqual(self.embedder.euclidean_distance([1, 0], [0, 1]), 2**0.5)
        self.assertEqual(self.embedder.dot_product([1, 0], [0, 1]), 0)
        with self.assertRaises(ValueError):
            self.embedder.cosine_similarity([1, 0], [1])

    def test_unverified_is_hidden_by_default_and_visible_in_diagnostics(self):
        store = self.store()
        store.add_chunks(self.processor.process_file(self.file))
        self.assertEqual(store.search("library"), [])
        self.assertTrue(store.search("library", verified_only=False))

    def test_multilingual_destination_identity_filters_unrelated_documents(self):
        store = self.store()
        chunks = self.processor.process_file(self.file)
        store.add_chunks(chunks)
        fake = {"text": "aklatan library books " * 40, "metadata": {
            "source_doc": "canteen.txt", "building": "Canteen", "chunk_id": "canteen_1"}}
        store.add_chunks([fake])
        for query in ("Where is the library?", "Saan po ang aklatan?", "Asa ang basahanan?"):
            hits = store.search(query, verified_only=False)
            self.assertTrue(hits)
            self.assertTrue(all(h["metadata"]["source_doc"] == self.file.name for h in hits))
        self.assertEqual(store.search("Where is the registrar?", verified_only=False), [])
        # Avoid accidental alias substrings such as 'cashier' inside another word.
        from src.vector_store import canonical_destinations
        self.assertEqual(canonical_destinations("cashierless"), set())

    def test_upsert_does_not_duplicate_and_replace_prunes_shrunk_chunks(self):
        self.approve()
        store = self.store()
        chunks = self.processor.process_file(self.file)
        store.add_chunks(chunks)
        store.add_chunks(chunks)
        self.assertEqual(len(store.ids), len(chunks))
        self.file.write_text("Building Name: Synthetic Test Library\nLocation ID: TEST-001\n\nLibrary books.", encoding="utf-8")
        self.approve()
        new_chunks = self.processor.process_file(self.file)
        store.replace_document(self.file.name, new_chunks)
        self.assertEqual(len(store.ids), len(new_chunks))
        self.assertEqual(len(store.search("library", top_k=100)), len(new_chunks))

    def test_current_raw_edit_invalidates_stored_review_immediately(self):
        self.approve()
        store = self.store()
        store.add_chunks(self.processor.process_file(self.file))
        self.assertTrue(store.search("library"))
        self.file.write_text(self.file.read_text(encoding="utf-8") + "Changed.", encoding="utf-8")
        self.assertEqual(store.search("library"), [])

    def test_each_search_reads_one_fresh_registry_and_revalidates_each_source(self):
        self.approve()
        second_file = self.raw / "other_library.txt"
        second_file.write_text("Building Name: Other Synthetic Library\nLocation ID: TEST-002\nLibrary books.", encoding="utf-8")
        documents = json.loads(self.registry.read_text(encoding="utf-8"))["documents"]
        documents[second_file.name] = {
            **documents[self.file.name],
            "sha256": hashlib.sha256(second_file.read_bytes()).hexdigest(),
        }
        self.registry.write_text(json.dumps({"documents": documents}), encoding="utf-8")
        store = self.store()
        store.add_chunks(self.processor.process_directory(self.raw))
        with patch.object(SourceRegistry, "entries", autospec=True,
                          side_effect=SourceRegistry.entries) as registry_reads:
            hits = store.search("library", top_k=100)
            self.assertEqual({hit["metadata"]["source_doc"] for hit in hits},
                             {self.file.name, second_file.name})
            self.assertEqual(registry_reads.call_count, 1)

            documents[self.file.name]["verified"] = False
            self.registry.write_text(json.dumps({"documents": documents}), encoding="utf-8")
            hits = store.search("library", top_k=100)
            self.assertEqual({hit["metadata"]["source_doc"] for hit in hits}, {second_file.name})
            self.assertEqual(registry_reads.call_count, 2)

            second_file.write_text("Changed source content.", encoding="utf-8")
            self.assertEqual(store.search("library", top_k=100), [])
            self.assertEqual(registry_reads.call_count, 3)

    def test_review_revocation_invalidates_stored_chunks_immediately(self):
        self.approve()
        store = self.store()
        store.add_chunks(self.processor.process_file(self.file))
        self.approve(verified=False)
        self.assertEqual(store.search("library"), [])

    def test_forged_text_or_added_route_metadata_cannot_use_valid_review(self):
        self.approve()
        for forgery in ("text", "metadata"):
            with self.subTest(forgery=forgery):
                chunks = self.processor.process_file(self.file)
                if forgery == "text":
                    chunks[0]["text"] = "Invented directions, 42 steps, 6 minutes."
                else:
                    chunks[0]["metadata"]["route_data"] = '{"walking_minutes": 6}'
                store = self.store()
                store.add_chunks([chunks[0]])
                self.assertEqual(store.search("library"), [])

    def test_persistence_reloads_vectors_without_legacy_data(self):
        self.approve()
        persistent = self.store("json")
        persistent.add_chunks(self.processor.process_file(self.file))
        # A legacy-looking file must remain untouched and never be treated as input.
        legacy = self.base / "vectors" / "chroma.sqlite3"
        legacy.write_bytes(b"untrusted legacy fixture")
        reloaded = self.store("json")
        self.assertEqual(reloaded.ids, persistent.ids)
        self.assertTrue(reloaded.search("library"))
        self.assertEqual(legacy.read_bytes(), b"untrusted legacy fixture")

    def test_embedding_spaces_are_separate(self):
        persistent = self.store("json")
        persistent.add_chunks(self.processor.process_file(self.file))
        other = VectorStore(EmbeddingGenerator(vector_dim=32, mode="lexical"), backend="json",
                            persist_directory=self.base / "vectors", raw_data_dir=self.raw,
                            source_registry_path=self.registry)
        self.assertEqual(other.documents, [])
        self.assertNotEqual(other.collection_name, persistent.collection_name)

    def test_incremental_restart_processed_export_and_review_update(self):
        self.approve()
        pipeline = self.pipeline(self.store("json"))
        first = pipeline.run()
        self.assertEqual(first["documents_updated_or_added"], 1)
        exported = Path(first["processed_chunks_path"]).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(exported), len(pipeline.vector_store.ids))
        self.assertTrue(json.loads(exported[0])["metadata"]["verified_source"])
        second = self.pipeline(self.store("json"))
        self.assertEqual(second.run()["documents_updated_or_added"], 0)
        self.approve(verified=False)
        self.assertEqual(second.run()["documents_updated_or_added"], 1)
        self.assertEqual(second.vector_store.search("library"), [])

    def test_manifest_does_not_hide_missing_store(self):
        self.pipeline(self.store()).run()
        rebuilt = self.pipeline(self.store())
        self.assertEqual(rebuilt.run()["documents_updated_or_added"], 1)
        self.assertTrue(rebuilt.vector_store.ids)

    def test_incomplete_snapshot_triggers_document_rebuild(self):
        store = self.store("json")
        self.pipeline(store).run()
        snapshot = json.loads(store._snapshot.read_text(encoding="utf-8"))
        snapshot["records"].pop()
        store._snapshot.write_text(json.dumps(snapshot), encoding="utf-8")
        rebuilt = self.pipeline(self.store("json"))
        self.assertEqual(rebuilt.run()["documents_updated_or_added"], 1)

    def test_deleted_and_empty_documents_are_handled_incrementally(self):
        pipeline = self.pipeline(self.store("json"))
        pipeline.run()
        self.file.write_text("", encoding="utf-8")
        self.assertEqual(pipeline.run()["documents_updated_or_added"], 1)
        self.assertEqual(pipeline.vector_store.documents, [])
        restarted = self.pipeline(self.store("json"))
        self.assertEqual(restarted.run()["documents_updated_or_added"], 0)
        self.file.unlink()
        self.assertEqual(restarted.run()["documents_removed"], 1)
        self.assertFalse(restarted.vector_store.has_document(self.file.name))


if __name__ == "__main__":
    unittest.main()
