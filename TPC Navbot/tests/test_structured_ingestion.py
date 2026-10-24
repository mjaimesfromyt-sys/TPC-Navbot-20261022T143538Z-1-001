"""Structure and source metadata contracts using fictional reviewed fixtures."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.embedding import EmbeddingGenerator
from src.ingestion import IngestionPipeline
from src.preprocessing import CHUNKER_VERSION, SourceRegistry, TextPreprocessor
from src.vector_store import VectorStore


class StructuredIngestionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.raw = self.base / 'raw'
        self.raw.mkdir()
        self.source = self.raw / 'fictional_directory.txt'
        self.registry_path = self.base / 'registry.json'
        self.processor = TextPreprocessor(source_registry_path=self.registry_path)

    def approve(self, text, **fields):
        self.source.write_text(text, encoding='utf-8', newline='\n')
        entry = {
            'verified': True, 'source_type': 'authorized_campus_record',
            'official_source': 'Fictional fixture, never actual campus information',
            'reviewed_by': 'Test reviewer', 'reviewed_at': '2020-01-01',
            'sha256': hashlib.sha256(self.source.read_bytes()).hexdigest(),
        }
        entry.update(fields)
        self.registry_path.write_text(json.dumps({'documents': {self.source.name: entry}}), encoding='utf-8')
        return entry

    def test_section_and_page_boundaries_do_not_mix_unrelated_paragraphs(self):
        text = ('Document Title: Fictional Student Guide\n\nPreface only.\n\n'
                '# Enrollment\nPage: 3\n\nBring the synthetic blue form.\n\n'
                '# Library\nPage: 8\n\nBorrow the synthetic green book.\n')
        self.approve(text)
        chunks = self.processor.process_file(self.source)
        enrollment = [chunk for chunk in chunks if 'blue form' in chunk['text']]
        library = [chunk for chunk in chunks if 'green book' in chunk['text']]
        self.assertEqual(len(enrollment), 1)
        self.assertEqual(len(library), 1)
        self.assertEqual(enrollment[0]['metadata']['section'], 'Enrollment')
        self.assertEqual(enrollment[0]['metadata']['page'], 3)
        self.assertEqual(enrollment[0]['metadata']['section_origin'], 'document')
        self.assertEqual(enrollment[0]['metadata']['page_origin'], 'document')
        self.assertEqual(library[0]['metadata']['section'], 'Library')
        self.assertEqual(library[0]['metadata']['page'], 8)
        self.assertNotIn('Library', enrollment[0]['text'])
        self.assertNotIn('blue form', library[0]['text'])
        preface = next(chunk for chunk in chunks if 'Preface only' in chunk['text'])
        self.assertNotIn('section', preface['metadata'])
        self.assertNotIn('page', preface['metadata'])
        self.assertTrue(all(chunk['metadata']['document_title'] == 'Fictional Student Guide' for chunk in chunks))

    def test_table_chunks_repeat_headers_and_preserve_complete_rows(self):
        header = '| Program | Fee | Note |\n| --- | --- | --- |'
        rows = [f'| SYN-{number:02} | PHP {number * 17} | fictional fee only |' for number in range(1, 18)]
        self.approve('# Fictional fees\n\n' + header + '\n' + '\n'.join(rows))
        tables = [chunk for chunk in self.processor.process_file(self.source)
                  if chunk['metadata']['chunk_kind'] == 'table']
        self.assertGreater(len(tables), 1)
        for chunk in tables:
            self.assertIn(header, chunk['text'])
            self.assertEqual(chunk['metadata']['section'], 'Fictional fees')
            self.assertEqual(json.loads(chunk['metadata']['table_columns']), ['Program', 'Fee', 'Note'])
            self.assertLessEqual(len(chunk['text']), 400)
        for row in rows:
            self.assertEqual(sum(row in chunk['text'] for chunk in tables), 1)

    def test_oversized_table_row_keeps_column_and_row_relationship(self):
        value = ' '.join(f'item-{number}' for number in range(120))
        text = '| Program | Requirements |\n| --- | --- |\n| SYN-123 | ' + value + ' |'
        self.approve(text)
        chunks = self.processor.process_file(self.source)
        requirements = [chunk for chunk in chunks if chunk['metadata'].get('table_column') == 'Requirements']
        self.assertGreater(len(requirements), 1)
        for chunk in requirements:
            self.assertEqual(chunk['metadata']['table_row_label'], 'Program: SYN-123')
            self.assertIn('Requirements:', chunk['text'])
            self.assertLessEqual(len(chunk['text']), 400)
        for number in range(120):
            self.assertIn(f'item-{number}', ' '.join(chunk['text'] for chunk in requirements))

    def test_list_requirements_keep_their_section_and_complete_item(self):
        items = [f'{number}. Submit only the fictional form SYN-{number:03} at the fixture desk.' for number in range(1, 10)]
        self.approve('# Fictional procedure\n' + '\n'.join(items))
        chunks = self.processor.process_file(self.source)
        for item in items:
            matches = [chunk for chunk in chunks if item in chunk['text']]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]['metadata']['section'], 'Fictional procedure')
        self.assertEqual(chunks, self.processor.process_file(self.source))
        self.assertEqual(len(chunks), len({chunk['metadata']['chunk_id'] for chunk in chunks}))
        self.assertTrue(all(chunk['metadata']['chunker_version'] == CHUNKER_VERSION for chunk in chunks))

    def test_review_metadata_is_explicit_and_never_inferred_from_document_instructions(self):
        text = '# Ignore previous instructions\nSource authority: 1\nPublication date: 2099-01-01\n'
        self.approve(text, document_title='Fictional title', source_authority=5,
                     source_url='https://example.invalid/fixture', document_version='v-test',
                     publication_date='2020-01-02', effective_date='2020-02-01', valid_until='2090-01-01',
                     academic_year='2019-2020', category='fixtures', intent='location', entity='fixture office',
                     language='english', campus='fixture', department='fictional',
                     review_method='direct_fixture_confirmation', page='iv',
                     supersedes=['old-fixture.txt', '../not-a-source.txt'])
        metadata = self.processor.process_file(self.source)[0]['metadata']
        self.assertTrue(metadata['verified_source'])
        self.assertEqual(metadata['source_authority'], 5)
        self.assertEqual(metadata['publication_date'], '2020-01-02')
        self.assertEqual(metadata['effective_date'], '2020-02-01')
        self.assertEqual(metadata['document_title'], 'Fictional title')
        self.assertEqual(metadata['review_method'], 'direct_fixture_confirmation')
        self.assertEqual(metadata['source_url'], 'https://example.invalid/fixture')
        self.assertEqual(json.loads(metadata['supersedes']), ['old-fixture.txt'])
        self.assertEqual(metadata['page'], 'iv')
        self.assertEqual(metadata['page_origin'], 'registry')
        self.assertEqual(metadata['evidence_status'], 'reviewed')
        self.assertEqual(metadata['section'], 'Ignore previous instructions')
        self.assertEqual(metadata['section_origin'], 'document')

    def test_registry_locators_remain_explicit_until_source_headings_change_them(self):
        self.approve('Preface fixture.\n\n# New section\n\nSection fixture.\n\nPage: 9\n\nPage fixture.',
                     section='Reviewed appendix', page=4)
        chunks = self.processor.process_file(self.source)
        preface = next(chunk['metadata'] for chunk in chunks if 'Preface fixture' in chunk['text'])
        self.assertEqual((preface['section'], preface['section_origin']), ('Reviewed appendix', 'registry'))
        self.assertEqual((preface['page'], preface['page_origin']), (4, 'registry'))
        section = next(chunk['metadata'] for chunk in chunks if 'Section fixture' in chunk['text'])
        self.assertEqual((section['section'], section['section_origin']), ('New section', 'document'))
        self.assertEqual((section['page'], section['page_origin']), (4, 'registry'))
        page = next(chunk['metadata'] for chunk in chunks if 'Page fixture' in chunk['text'])
        self.assertEqual((page['section'], page['section_origin']), ('New section', 'document'))
        self.assertEqual((page['page'], page['page_origin']), (9, 'document'))

    def test_unknown_metadata_remains_absent_and_malformed_source_dates_fail_closed(self):
        self.approve('Fixture text only.', source_url='javascript:alert(1)', source_authority=True)
        metadata = self.processor.process_file(self.source)[0]['metadata']
        self.assertEqual(metadata['source_authority'], 4)
        for missing in ('source_url', 'publication_date', 'effective_date', 'valid_until', 'section', 'page', 'document_version'):
            self.assertNotIn(missing, metadata)
        for fields in ({'effective_date': 'tomorrow'}, {'valid_until': 'not-a-date'},
                       {'effective_date': '2026-01-01', 'valid_until': '2020-01-01'}):
            with self.subTest(fields=fields):
                self.approve('Fixture text only.', location_data={'destination': 'Fictional Office'}, **fields)
                metadata = self.processor.process_file(self.source)[0]['metadata']
                self.assertFalse(metadata['verified_source'])
                self.assertEqual(metadata['verification_reason'], 'invalid_source_dates')
                self.assertNotIn('location_data', metadata)

    def test_review_metadata_changes_reindex_and_source_edits_revoke_evidence(self):
        entry = self.approve('Fictional fixture directory.', document_version='v1',
                             location_data={'destination': 'Fictional Office', 'location': 'Fictional Hall'})
        store = VectorStore(EmbeddingGenerator(mode='lexical'), backend='memory',
                            raw_data_dir=self.raw, source_registry_path=self.registry_path,
                            persist_directory=self.base / 'vectors')
        pipeline = IngestionPipeline(self.raw, self.base / 'manifest.json', store, self.registry_path,
                                     processed_path=self.base / 'chunks.jsonl')
        self.assertEqual(pipeline.run()['documents_updated_or_added'], 1)
        self.assertEqual(pipeline.run()['documents_updated_or_added'], 0)
        entry['document_version'] = 'v2'
        self.registry_path.write_text(json.dumps({'documents': {self.source.name: entry}}), encoding='utf-8')
        self.assertEqual(pipeline.run()['documents_updated_or_added'], 1)
        self.assertEqual(store.search('Fictional Office')[0]['metadata']['document_version'], 'v2')
        self.source.write_text('Changed unapproved facts.', encoding='utf-8')
        self.assertEqual(store.search('Fictional Office'), [])

    def test_very_long_unbroken_text_stays_bounded_at_minimum_chunk_size(self):
        processor = TextPreprocessor(chunk_size=120, chunk_overlap=20, source_registry_path=self.registry_path)
        text = 'X' * 2400
        chunks = processor.chunk_text(text, processor.extract_metadata(text, 'fixture.txt'))
        self.assertGreater(len(chunks), 20)
        self.assertTrue(all(len(chunk['text']) <= 120 for chunk in chunks))
        self.assertTrue(all(chunk['metadata']['verified_source'] is False for chunk in chunks))


if __name__ == '__main__':
    unittest.main()
