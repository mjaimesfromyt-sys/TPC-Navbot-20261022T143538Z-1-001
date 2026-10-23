"""A student-facing benchmark on the actual reviewed corpus, with no network."""
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_school_qa import Case, build_cases, evaluate


class SchoolQACoverageTests(unittest.TestCase):
    def test_school_questions_grounding_languages_scope_and_completeness(self):
        cases = build_cases()
        # A reviewed record may have only an unknown-fact case; records 26 and
        # 28 intentionally contain no approved emergency/parking factual fields.
        self.assertGreaterEqual(len(cases), 190)
        self.assertEqual(len({case.id for case in cases}), len(cases))
        self.assertEqual({case.language for case in cases}, {"english", "bisaya", "tagalog"})
        report = evaluate(cases)
        self.assertEqual(report["approved_records"], 30)
        for result in report["results"]:
            with self.subTest(case=result["id"], query=result["query"]):
                self.assertEqual(result["problems"], [], result["response"])

    def test_other_student_workflows_do_not_borrow_enrollment_or_new_id_facts(self):
        cases = [
            Case("scholarship-documents", "workflow_specificity", "What documents do new students need for a scholarship?",
                 expected_status="UNVERIFIED", forbidden=("New students: Accomplished enrollment form",)),
            Case("replacement-documents", "workflow_specificity", "What documents do transferees need for student ID replacement?",
                 expected_status="UNVERIFIED", forbidden=("Transferees: Transcript",)),
            Case("renewal-id-cost", "workflow_specificity", "How much is student ID renewal?",
                 expected_status="UNVERIFIED", forbidden=("free",)),
            Case("exam-phone", "workflow_specificity", "What is the phone number for exam policies?",
                 expected_status="UNVERIFIED", facts=("instructor",), source_groups=((22,),)),
            Case("admission-email", "workflow_specificity", "What is the email for admission requirements?",
                 expected_status="UNVERIFIED", facts=("Registrar",), source_groups=((19,),)),
        ]
        for result in evaluate(cases)["results"]:
            with self.subTest(case=result["id"], query=result["query"]):
                self.assertEqual(result["problems"], [], result["response"])

    def test_specific_programs_and_known_new_id_fee_do_not_lose_reviewed_facts(self):
        cases = [
            Case("specific-bsis", "specific_facts", "Does TPC offer BSIS?",
                 facts=("Bachelor of Science in Information Systems",), source_groups=((20,),),
                 forbidden=("Bachelor of Science in Accounting Information Systems",)),
            Case("specific-bsais", "specific_facts", "Does TPC offer BSAIS?",
                 facts=("Bachelor of Science in Accounting Information Systems",), source_groups=((20,),),
                 forbidden=("Bachelor of Science in Information Systems",)),
            Case("new-id-cost", "specific_facts", "How much is a new student ID?",
                 facts=("free",), source_groups=((16,),)),
        ]
        for result in evaluate(cases)["results"]:
            with self.subTest(case=result["id"], query=result["query"]):
                self.assertEqual(result["problems"], [], result["response"])


if __name__ == "__main__":
    unittest.main()
