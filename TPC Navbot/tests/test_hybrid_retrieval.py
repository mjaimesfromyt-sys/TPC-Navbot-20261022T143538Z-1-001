"""Network-free retrieval contracts with synthetic evidence, never campus facts."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import EmbeddingGenerator
from src.preprocessing import TextPreprocessor
from src.vector_store import VectorStore


class CollidingEmbedder:
    """Deliberately indistinguishable vectors expose exact keyword recovery."""
    vector_dim = 2
    signature = 'synthetic-colliding-vectors-v1'
    backend = 'synthetic-collision-fixture'

    def embed_text(self, text):
        return [1.0, 0.0]

    cosine_similarity = staticmethod(EmbeddingGenerator.cosine_similarity)
    euclidean_distance = staticmethod(EmbeddingGenerator.euclidean_distance)
    dot_product = staticmethod(EmbeddingGenerator.dot_product)


class SeparatedSignalsEmbedder(CollidingEmbedder):
    """Synthetic signal geometry isolates document/chunk fusion behavior."""
    signature = 'synthetic-separated-signals-v1'

    def embed_text(self, text):
        similarity = (0.9 if 'SignalMiddle' in text else 0.8 if 'SignalOther' in text
                      else 0.1 if 'SignalKeyword' in text else 1.0)
        return [similarity, (1 - similarity ** 2) ** 0.5]


class HybridRetrievalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.raw = self.base / 'raw'
        self.raw.mkdir()
        self.registry = self.base / 'registry.json'
        self.entries = {}
        self.store = VectorStore(CollidingEmbedder(), backend='memory',
                                 persist_directory=self.base / 'vectors',
                                 raw_data_dir=self.raw, source_registry_path=self.registry)

    def source(self, filename, text, **review):
        path = self.raw / filename
        path.write_text(text, encoding='utf-8', newline='\n')
        entry = {
            'verified': True, 'source_type': 'official_document',
            'official_source': 'Synthetic authoritative fixture only',
            'reviewed_by': 'Synthetic test reviewer', 'reviewed_at': '2020-01-01',
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        entry.update(review)
        self.entries[filename] = entry
        self.registry.write_text(json.dumps({'documents': self.entries}), encoding='utf-8')
        chunks = TextPreprocessor(source_registry_path=self.registry).process_file(path)
        self.store.replace_document(filename, chunks)
        return path

    def test_exact_code_is_recovered_when_vectors_collide(self):
        self.source('a_unrelated.txt', 'Synthetic course code XYZ-111. Students study art.')
        self.source('z_relevant.txt', 'Synthetic course code QRS-909. Students study biology.')
        baseline = self.store.search('QRS-909', top_k=1, hybrid=False)
        hybrid = self.store.search('QRS-909', top_k=1)
        self.assertEqual(baseline[0]['metadata']['source_doc'], 'a_unrelated.txt')
        self.assertEqual(hybrid[0]['metadata']['source_doc'], 'z_relevant.txt')
        self.assertEqual(hybrid[0]['score'], baseline[0]['score'])
        self.assertGreater(hybrid[0]['rank_details']['bm25_score'], 0)
        self.assertEqual(hybrid[0]['rank_details']['embedding_backend'], 'synthetic-collision-fixture')

    def test_keyword_identifiers_keep_hyphens_and_academic_years(self):
        self.source('a_previous.txt', 'Synthetic QRS-908 schedule for academic year 2023-2024.')
        self.source('z_requested.txt', 'Synthetic QRS-909 schedule for academic year 2024-2025.')
        hit = self.store.search('QRS-909 2024-2025', top_k=1)[0]
        self.assertEqual(hit['metadata']['source_doc'], 'z_requested.txt')
        self.assertEqual(hit['rank_details']['keyword_rank'], 1)

    def test_metric_baselines_and_requested_metric_order_are_preserved(self):
        self.source('a.txt', 'Synthetic general student guidance.')
        self.source('z.txt', 'Synthetic guidance code QRS-909.')
        for metric in ('euclidean', 'dot_product'):
            with self.subTest(metric=metric):
                results = self.store.search('QRS-909', metric=metric)
                self.assertEqual(results[0]['metadata']['source_doc'], 'a.txt')
                self.assertNotIn('retrieval_score', results[0])
                self.assertEqual(results, self.store.search('QRS-909', metric=metric, hybrid=False))

    def test_nested_directory_and_route_identities_survive_facility_filter(self):
        self.source('generic_directory.txt', 'Synthetic reviewed directory of two campus places.',
                    location_data={'locations': [
                        {'destination': 'Library', 'room': 'SYN-1'},
                        {'destination': 'Clinic', 'room': 'SYN-2'},
                    ]})
        self.source('generic_route.txt', 'Synthetic reviewed route to a campus place.',
                    route_data={'routes': [{'destination': 'Registrar Office', 'start': 'Synthetic gate'}]})
        self.source('unrelated.txt', 'Library library library.',
                    location_data={'destination': 'Canteen', 'room': 'SYN-3'})
        for query, source in (('Where is the library?', 'generic_directory.txt'),
                              ('Where is the clinic?', 'generic_directory.txt'),
                              ('Directions to the registrar', 'generic_route.txt')):
            with self.subTest(query=query):
                hits = self.store.search(query)
                self.assertTrue(hits)
                self.assertTrue(all(hit['metadata']['source_doc'] == source for hit in hits))

    def test_unreviewed_stale_revoked_and_forged_evidence_stays_excluded(self):
        path = self.source('approved.txt', 'Synthetic exact QRS-909 evidence.')
        self.source('unreviewed.txt', 'QRS-909 ' * 20, verified=False)
        self.assertTrue(all(hit['metadata']['source_doc'] == 'approved.txt'
                            for hit in self.store.search('QRS-909')))
        path.write_text('Changed QRS-909 content.', encoding='utf-8')
        self.assertEqual(self.store.search('QRS-909'), [])
        self.source('approved.txt', 'Synthetic exact QRS-909 evidence.')
        self.entries['approved.txt']['verified'] = False
        self.registry.write_text(json.dumps({'documents': self.entries}), encoding='utf-8')
        self.assertEqual(self.store.search('QRS-909'), [])
        self.source('approved.txt', 'Synthetic exact QRS-909 evidence.')
        row = next(row for row in self.store._records.values()
                   if row['metadata']['source_doc'] == 'approved.txt')
        row['metadata']['source_authority'] = 1
        self.assertEqual(self.store.search('QRS-909'), [])

    def test_filter_errors_do_not_silently_broaden_retrieval(self):
        self.source('approved.txt', 'Synthetic evidence.')
        for filters in ({'unsupported': 'x'}, {'category': ['x']}, 'category=x'):
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                self.store.search('Synthetic', filters=filters)
        self.assertEqual(self.store.search('Synthetic', filters={'category': 'missing'}), [])

    def test_results_are_deterministic_and_never_relabel_lexical_as_semantic(self):
        self.source('a.txt', 'Synthetic first QRS-909 evidence.')
        self.source('b.txt', 'Synthetic second QRS-909 evidence.')
        self.assertEqual(self.store.search('QRS-909'), self.store.search('QRS-909'))
        self.assertTrue(all(hit['rank_details']['embedding_backend'] == 'synthetic-collision-fixture'
                            for hit in self.store.search('QRS-909')))

    def test_authority_breaks_true_relevance_ties_without_guessing_freshness(self):
        self.source('a_secondary.txt', 'Synthetic identical QRS-909 guidance.',
                    source_type='authorized_campus_record')
        self.source('z_official.txt', 'Synthetic identical QRS-909 guidance.',
                    source_type='official_document')
        hits = self.store.search('QRS-909')
        self.assertEqual(hits[0]['retrieval_score'], hits[1]['retrieval_score'])
        self.assertEqual(hits[0]['metadata']['source_doc'], 'z_official.txt')
        self.assertEqual(hits[0]['rank_details']['source_authority'], 2)
        self.assertEqual(hits[1]['rank_details']['source_authority'], 4)
        self.assertEqual(hits[0]['rank_details']['source_date'], '')
        self.assertEqual(VectorStore._source_rank({'reviewed_at': '2026-10-24'})[1], '')
        self.assertEqual(VectorStore._source_rank({'effective_date': '2024-08-01'})[1], '2024-08-01')
        self.assertEqual(VectorStore._source_rank({'effective_date': 'invalid'})[1], '')

    def test_validated_source_dates_and_categories_are_used_without_review_date_substitution(self):
        self.source('a_old.txt', 'Synthetic identical QRS-909 guidance.',
                    category='Enrollment', publication_date='2022-01-01',
                    effective_date='2023-01-01', reviewed_at='2026-01-01')
        self.source('z_new.txt', 'Synthetic identical QRS-909 guidance.',
                    category='Enrollment', publication_date='2024-01-01',
                    effective_date='2025-01-01', reviewed_at='2025-01-01')
        self.source('other.txt', 'Synthetic identical QRS-909 guidance.', category='Admissions')
        hits = self.store.search('QRS-909', filters={'category': 'enrollment'})
        self.assertEqual({hit['metadata']['source_doc'] for hit in hits}, {'a_old.txt', 'z_new.txt'})
        self.assertEqual(hits[0]['metadata']['source_doc'], 'z_new.txt')
        self.assertEqual(hits[0]['rank_details']['source_date'], '2025-01-01')

    def test_document_fusion_combines_signals_that_live_in_separate_chunks(self):
        self.store = VectorStore(SeparatedSignalsEmbedder(), backend='memory',
                                 persist_directory=self.base / 'signals',
                                 raw_data_dir=self.raw, source_registry_path=self.registry)
        paragraphs = ['SignalBest synthetic semantic explanation without an exact identifier.']
        paragraphs += [f'SignalOther synthetic supporting paragraph {index} without identifier.' for index in range(6)]
        paragraphs += ['SignalKeyword ' + 'QRS-909 ' * 20]
        self.source('a_strong.txt', '\n\n'.join(paragraphs))
        self.source('b_middle.txt', 'SignalMiddle synthetic middle relevance QRS-909.')
        hits = self.store.search('QRS-909', top_k=2)
        self.assertEqual(hits[0]['metadata']['source_doc'], 'a_strong.txt')
        self.assertEqual(hits[0]['rank_details']['document_vector_rank'], 1)
        self.assertEqual(hits[0]['rank_details']['document_keyword_rank'], 1)
        self.assertIn('QRS-909', hits[0]['text'])

    def test_long_source_cannot_hide_a_peer_from_small_context_limits(self):
        self.source('a_long.txt', '\n\n'.join(
            f'Synthetic QRS-909 guidance paragraph {index}. ' * 8 for index in range(12)))
        self.source('z_peer.txt', 'Synthetic peer QRS-909 guidance.')
        self.assertGreater(sum(row['metadata']['source_doc'] == 'a_long.txt'
                               for row in self.store._records.values()), 2)
        hits = self.store.search('QRS-909', top_k=2)
        self.assertEqual({hit['metadata']['source_doc'] for hit in hits}, {'a_long.txt', 'z_peer.txt'})
        self.assertEqual(len(self.store.search('QRS-909', top_k=100)), len(self.store.ids))


if __name__ == '__main__':
    unittest.main()
