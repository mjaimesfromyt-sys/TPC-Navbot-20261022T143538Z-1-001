"""Verified Q&A exports derive only from content-bound approved source fields."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.build_verified_qa import build_verified_qa, write_verified_qa


class VerifiedQAExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.raw = self.folder / 'raw'
        self.raw.mkdir()
        self.registry = self.folder / 'registry.json'
        self.entries = {}

    def source(self, filename='library.txt', *, fields=None, **review):
        record = {'destination': 'Library', 'building': 'Synthetic Library Hall',
                  'location': 'Beside the fictional test courtyard.',
                  'hours': 'Synthetic Monday, 08:00-17:00.',
                  'services': ['Borrow fictional test books.'],
                  'contact': 'Ask the fictional library desk.'}
        record.update(fields or {})
        content = ('Synthetic fixture, never actual campus facts.\n' + json.dumps(record) + '\n').encode('utf-8')
        (self.raw / filename).write_bytes(content)
        self.entries[filename] = {
            'verified': True, 'source_type': 'authorized_campus_record',
            'sha256': hashlib.sha256(content).hexdigest(),
            'official_source': 'Synthetic approved source for testing only',
            'reviewed_by': 'Fixture reviewer', 'reviewed_at': '2026-10-23',
            'review_method': 'school_confirmation_reported_by_user',
            'location_data': record, **review,
        }
        self.registry.write_text(json.dumps({'documents': self.entries}), encoding='utf-8')
        return record

    def build(self):
        return build_verified_qa(raw_data_dir=self.raw, source_registry_path=self.registry)

    def test_every_qa_has_the_required_source_traceability_and_matching_fact_id(self):
        self.source()
        result = self.build()
        self.assertEqual(len(result['facts']), 5)
        facts = {row['verified_fact_id']: row for row in result['facts']}
        required = {'record_id', 'language', 'category', 'intent', 'question', 'answer',
                    'verified_fact_id', 'evidence_status', 'source', 'source_url',
                    'document', 'page_or_section', 'publication_date', 'effective_date',
                    'confidence', 'referral_guidance', 'last_verified'}
        for row in result['qa']:
            with self.subTest(record_id=row['record_id']):
                self.assertTrue(required <= set(row))
                fact = facts[row['verified_fact_id']]
                expected = hashlib.sha256(f"{fact['source_sha256']}|{fact['entity']}|{fact['field']}".encode('utf-8')).hexdigest()[:24]
                self.assertEqual(expected, row['verified_fact_id'])
                self.assertEqual(row['verified_fact_ids'], [expected])
                self.assertEqual(row['document'], fact['document'])
                self.assertEqual(row['source_sha256'], fact['source_sha256'])
                values = fact['value'] if isinstance(fact['value'], list) else [fact['value']]
                for value in values:
                    self.assertIn(str(value).rstrip('.').casefold(), row['answer'].casefold())
        self.assertEqual(result['manifest']['approved_document_count'], 1)
        self.assertFalse(result['manifest']['model_weight_updates'])

    def test_unknown_urls_pages_and_publication_dates_are_not_fabricated_from_review_date(self):
        self.source()
        for row in self.build()['qa']:
            self.assertEqual(row['source_url'], '')
            self.assertEqual(row['page_or_section'], '')
            self.assertEqual(row['publication_date'], '')
            self.assertEqual(row['effective_date'], '')
            self.assertEqual(row['last_verified'], '2026-10-23')
            self.assertEqual(row['evidence_status'], 'reviewed_user_reported')
            self.assertEqual(row['confidence'], 'reviewed source; not independently authenticated')

    def test_raw_source_change_revokes_derived_facts_and_answers(self):
        self.source()
        self.assertTrue(self.build()['facts'])
        (self.raw / 'library.txt').write_text('FACT-POISON: Library now uses a secret tunnel.', encoding='utf-8')
        result = self.build()
        self.assertEqual(result['facts'], [])
        self.assertEqual(result['qa'], [])
        self.assertEqual(result['manifest']['excluded_documents'], {'content_changed': 1})

    def test_csv_answers_and_unreviewed_generated_sources_are_not_imported(self):
        self.source()
        self.source('generated_sample.txt', verified=False)
        (self.raw / 'student_questions.csv').write_text(
            'question,answer\nWhere is the library?,FACT-POISON approved by CSV\n', encoding='utf-8')
        result = self.build()
        serialized = json.dumps(result)
        self.assertNotIn('FACT-POISON', serialized)
        self.assertNotIn('generated_sample.txt', result['manifest']['current_documents'])
        self.assertFalse(result['manifest']['question_dataset_answers_used'])
        self.assertEqual(result['manifest']['approved_document_count'], 1)

    def test_translated_questions_preserve_same_supplied_fact_and_honest_review_status(self):
        self.source(review_method='location_confirmation_reported_by_user')
        result = self.build()
        self.assertEqual({row['language'] for row in result['qa']}, {'english', 'tagalog', 'bisaya', 'mixed'})
        locations = [row for row in result['qa'] if row['field'] == 'location']
        self.assertEqual(len({row['verified_fact_id'] for row in locations}), 1)
        for row in locations:
            self.assertIn('fictional test courtyard', row['answer'])
            self.assertEqual(row['evidence_status'], 'direct_user_confirmation')
            self.assertIn('missing translation is not invented', row['answer_language_note'])

    def test_expired_and_conflicting_facts_are_not_published_as_verified_answers(self):
        self.source('expired.txt', valid_until='2025-12-31')
        self.assertEqual(self.build()['facts'], [])
        self.source('peer-a.txt', fields={'hours': 'Synthetic hours A.'})
        self.source('peer-b.txt', fields={'hours': 'Synthetic hours B.'})
        result = self.build()
        self.assertTrue(result['manifest']['conflicts'])
        self.assertFalse(any(row['field'] == 'hours' for row in result['facts']))
        self.assertFalse(any(row['field'] == 'hours' for row in result['qa']))
        self.assertNotIn('expired.txt', result['manifest']['current_documents'])

    def test_authority_is_selected_for_each_fact_instead_of_discarding_missing_fields(self):
        self.source('official.txt', fields={'hours': None}, source_type='official_document')
        self.source('structured.txt', fields={'hours': 'Reviewed hours from a separate record.'})
        result = self.build()
        hours = [fact for fact in result['facts'] if fact['field'] == 'hours']
        self.assertEqual(len(hours), 1)
        self.assertEqual(hours[0]['document'], 'structured.txt')
        self.assertFalse(result['manifest']['conflicts'])
        self.source('official.txt', fields={'hours': 'New official hours.'}, source_type='official_document')
        result = self.build()
        hours = [fact for fact in result['facts'] if fact['field'] == 'hours']
        self.assertEqual(len(hours), 1)
        self.assertEqual(hours[0]['document'], 'official.txt')

    def test_jsonl_export_matches_manifest_and_preserves_fact_values(self):
        self.source(source_url='https://example.invalid/synthetic-library', section='Fictional section', page=3)
        result = write_verified_qa(self.folder / 'output', raw_data_dir=self.raw, source_registry_path=self.registry)
        facts = [json.loads(line) for line in (self.folder / 'output/facts.jsonl').read_text(encoding='utf-8').splitlines()]
        qa = [json.loads(line) for line in (self.folder / 'output/qa.jsonl').read_text(encoding='utf-8').splitlines()]
        manifest = json.loads((self.folder / 'output/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(facts, result['facts'])
        self.assertEqual(qa, result['qa'])
        self.assertEqual(manifest['facts'], len(facts))
        self.assertEqual(manifest['qa_records'], len(qa))
        self.assertTrue(all(row['page_or_section'] == 'page 3; Fictional section' for row in qa))
        self.assertTrue(all(row['source_url'] == 'https://example.invalid/synthetic-library' for row in qa))


if __name__ == '__main__':
    unittest.main()
