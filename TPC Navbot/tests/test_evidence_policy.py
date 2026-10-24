"""Fictional sources verify conflicts, periods, facets and exact citations."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.evidence import requested_period
from src.evidence import applicable
from test_guardrails import approved_hit, bot


def source(name, *, authority=4, **facts):
    hit = approved_hit(**facts)
    hit['id'] = name
    hit['metadata'].update(source_doc=name, source_authority=authority)
    return hit


class EvidencePolicyTests(unittest.TestCase):
    def test_same_room_number_in_separate_documents_needs_building_clarification(self):
        first = source('science-room.txt', building='Synthetic Science Hall', room='101')
        second = source('arts-room.txt', building='Synthetic Arts Hall', room='101')
        response = bot([first, second], use_llm=False).query('Where is Room 101?')
        self.assertEqual(response['status'], 'CLARIFICATION', response)
        self.assertIn('Synthetic Science Hall', response['answer'])
        self.assertIn('Synthetic Arts Hall', response['answer'])
        self.assertNotIn('conflict', response['answer'])

    def test_inferred_chunk_locator_cannot_cite_an_unrelated_structured_fact(self):
        hit = source('structured.txt')
        hit['metadata'].update(section='Unrelated rules', page=7, section_origin='document', page_origin='document')
        response = bot([hit], use_llm=False).query('Where is the library?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertNotIn('section', response['source_details'][0])
        self.assertNotIn('page', response['source_details'][0])
        hit['metadata'].update(section_origin='registry', page_origin='registry')
        response = bot([hit], use_llm=False).query('Where is the library?')
        self.assertEqual(response['source_details'][0]['page'], 7)

    def test_peer_conflicts_are_disclosed_with_both_supporting_sources(self):
        left = source('fictional-a.txt', hours={'english': '08:00 to 15:00'})
        right = source('fictional-b.txt', hours={'english': '09:00 to 17:00'})
        response = bot([left, right], use_llm=False).query('What are the library hours?')
        self.assertEqual(response['status'], 'UNVERIFIED', response)
        self.assertIn('conflict', response['answer'])
        self.assertIn('08:00', response['answer'])
        self.assertIn('09:00', response['answer'])
        self.assertEqual({detail['source_doc'] for detail in response['source_details']}, {'fictional-a.txt', 'fictional-b.txt'})
        self.assertTrue(all(detail['claim_fields'] == ['hours'] for detail in response['source_details']))

    def test_current_official_evidence_outranks_lower_authority_record(self):
        lower = source('lower.txt', hours={'english': 'LOWER CLAIM'})
        official = source('official.txt', authority=2, hours={'english': 'OFFICIAL CLAIM'})
        lower['score'] = 0.99
        response = bot([lower, official], use_llm=False).query('What are the library hours?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('OFFICIAL CLAIM', response['answer'])
        self.assertNotIn('LOWER CLAIM', response['answer'])
        self.assertEqual(response['source_details'][0]['source_doc'], 'official.txt')

    def test_authority_applies_to_the_requested_fact_not_an_unrelated_field(self):
        identity = source('official-location.txt', authority=2, hours={})
        hours = source('reviewed-hours.txt', hours={'english': 'REVIEWED HOURS'})
        response = bot([identity, hours], use_llm=False).query('What are the library hours?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('REVIEWED HOURS', response['answer'])
        self.assertEqual(response['source_details'][0]['source_doc'], 'reviewed-hours.txt')

    def test_academic_year_never_overrides_contradictory_validity_dates(self):
        for dates in ({'effective_date': '2027-01-01'}, {'valid_until': '2024-12-31'}):
            with self.subTest(dates=dates):
                self.assertFalse(applicable({'academic_year': '2025-2026', **dates}, 'Fees for school year 2025-2026'))

    def test_future_and_expired_sources_cannot_answer_current_question(self):
        for field, value in (('effective_date', '2099-01-01'), ('publication_date', '2099-01-01'), ('valid_until', '2020-01-01')):
            with self.subTest(field=field):
                hit = source('unavailable.txt')
                hit['metadata'][field] = value
                response = bot([hit], use_llm=False).query('Where is the library?')
                self.assertEqual(response['status'], 'UNVERIFIED', response)
                self.assertEqual(response['sources'], [])

    def test_historical_query_requires_explicit_period_not_review_date(self):
        current = source('current.txt', hours={'english': 'CURRENT HOURS'})
        current['metadata']['reviewed_at'] = '2025-01-01'
        response = bot([current], use_llm=False).query('What were the library hours in 2025?')
        self.assertEqual(response['status'], 'UNVERIFIED', response)
        self.assertNotIn('CURRENT HOURS', response['answer'])
        historical = source('historical.txt', hours={'english': 'HISTORICAL HOURS'})
        historical['metadata'].update(effective_date='2025-01-01', valid_until='2025-12-31')
        response = bot([current, historical], use_llm=False).query('What were the library hours in 2025?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('HISTORICAL HOURS', response['answer'])
        self.assertEqual(response['source_details'][0]['effective_date'], '2025-01-01')
        historical['metadata']['academic_year'] = '2025-2026'
        historical['metadata'].pop('valid_until')
        response = bot([historical], use_llm=False).query('What were the library hours in school year 2025-2026?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('HISTORICAL HOURS', response['answer'])

    def test_explicit_supersession_and_dated_version_resolve_current_conflicts(self):
        old = source('old.txt', hours={'english': 'OLD HOURS'})
        new = source('new.txt', hours={'english': 'NEW HOURS'})
        new['metadata']['supersedes'] = json.dumps(['old.txt'])
        response = bot([old, new], use_llm=False).query('What are the library hours?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('NEW HOURS', response['answer'])
        self.assertNotIn('OLD HOURS', response['answer'])
        old['metadata'].update(document_title='Synthetic library policy', document_version='1', effective_date='2024-01-01')
        new['metadata'].update(document_title='Synthetic library policy', document_version='2', effective_date='2026-01-01')
        del new['metadata']['supersedes']
        response = bot([old, new], use_llm=False).query('What are the library hours?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('NEW HOURS', response['answer'])

    def test_dataset_online_eligibility_and_schedules_need_specific_evidence(self):
        for core, category in (('Can I do this online?', 'library'), ('Who is eligible?', 'academic programs'), ('When is it scheduled?', 'class schedules')):
            with self.subTest(core=core):
                subject = 'Academic Programs and Departments' if category == 'academic programs' else 'Academic Calendar and School Schedule' if category == 'class schedules' else 'Library'
                hit = approved_hit(subject, services='GENERIC SERVICE MUST NOT ANSWER', hours={'english': 'OFFICE HOURS MUST NOT ANSWER'})
                response = bot([hit], use_llm=False).query(f'I am a new student at TPC. {core} About {category}.')
                self.assertEqual(response['status'], 'UNVERIFIED', response)
                self.assertNotIn('GENERIC SERVICE', response['answer'])
                self.assertNotIn('OFFICE HOURS', response['answer'])

    def test_reviewed_specific_dataset_facet_can_answer_and_cite_its_field(self):
        hit = approved_hit(details={'online_option': {'english': 'Synthetic online service approved in fixture only.'}})
        response = bot([hit], use_llm=False).query('I am a new student at TPC. Can I do this online? About library.')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('Synthetic online service', response['answer'])
        self.assertEqual(response['source_details'][0]['claim_fields'], ['details.online_option'])
        self.assertEqual(len(response['source_details'][0]['verified_fact_ids']), 1)

    def test_freshman_requirements_keep_the_reviewed_audience(self):
        hit = approved_hit('Enrollment Requirements and Documents', services=[
            'New students: Synthetic form A.', 'Transferees: Synthetic document B.'])
        response = bot([hit], use_llm=False).query('What are the requirements for freshman enrollment?')
        self.assertEqual(response['status'], 'SUCCESS', response)
        self.assertIn('Synthetic form A', response['answer'])
        self.assertNotIn('Synthetic document B', response['answer'])

    def test_submission_followup_does_not_infer_location_from_document_requirements(self):
        hit = approved_hit('Enrollment Requirements and Documents', services=['Synthetic enrollment form.'])
        nav = bot([hit], use_llm=False)
        nav.chat('What are the enrollment requirements?')
        response = nav.chat('Where do I submit them?')
        self.assertEqual(response['status'], 'UNVERIFIED', response)
        self.assertEqual(response['query_understanding']['facet'], 'submission')
        self.assertNotIn('Learning Center', response['answer'])
        self.assertEqual(response['sources'], [])
        response = bot([hit], use_llm=False).chat('Where do I submit them?')
        self.assertEqual(response['status'], 'CLARIFICATION', response)

    def test_three_contextual_requests_are_verified_independently(self):
        hit = approved_hit('Enrollment', services=['Synthetic enrollment procedure.'], details={'fees': {'english': 'Synthetic fee PHP 12.'}})
        nav = bot([hit], use_llm=False)
        nav.chat('Where is enrollment?')
        response = nav.chat('What are the requirements, how much is the fee, and when is the deadline?')
        self.assertEqual(response['status'], 'PARTIAL', response)
        self.assertEqual(len(response['parts']), 3)
        self.assertIn('Synthetic fee PHP 12', response['answer'])
        self.assertEqual(response['parts'][-1]['status'], 'UNVERIFIED')

    def test_false_premise_and_room_numbers_do_not_become_unrelated_facts(self):
        response = bot([], use_llm=False).query('TPC increased tuition by 20%. Why?')
        self.assertEqual(response['status'], 'UNVERIFIED', response)
        self.assertIn('claimed increase', response['answer'])
        self.assertIsNone(requested_period('Where is Room 2025?'))


if __name__ == '__main__':
    unittest.main()
