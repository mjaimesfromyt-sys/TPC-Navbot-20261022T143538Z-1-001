"""Helpful tips and follow-ups must use the selected reviewed campus record."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import test_query_understanding as fixtures
from src.llm_rag import TPCNavBotRAG


class ProactiveHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.CampusQueryUnderstandingTests.setUpClass.__func__(cls)

    def setUp(self):
        self.bot = TPCNavBotRAG(vector_store=self.store, initialize_knowledge_base=False, use_llm=False)

    def test_library_tip_quotes_reviewed_borrowing_advice_and_keeps_answer_plain(self):
        result = self.bot.query("library")
        self.assertEqual(result["answer"], "The Library is on the right side when facing the canteen.")
        self.assertIn("library card", result["helpful_tip"])
        self.assertIn("Ask the librarian", result["helpful_tip"])
        self.assertNotIn(result["helpful_tip"], result["answer"])
        self.assertEqual(result["suggested_questions"], [
            "What are the Library hours?", "What services does the Library offer?",
        ])

    def test_suggestions_are_answerable_from_the_same_destination_in_three_languages(self):
        for question in ("library", "Asa ang library?", "Nasaan ang library?", "student ID", "enrollment"):
            with self.subTest(question=question):
                first = self.bot.query(question)
                self.assertEqual(first["status"], "SUCCESS", first)
                self.assertLessEqual(len(first["suggested_questions"]), 2)
                for suggestion in first["suggested_questions"]:
                    followup = self.bot.query(suggestion)
                    self.assertEqual(followup["status"], "SUCCESS", (suggestion, followup))
                    self.assertEqual(first["source_details"][0]["destination"],
                                     followup["source_details"][0]["destination"])

    def test_unknown_fields_do_not_become_tips_or_suggestions(self):
        result = self.bot.query("crim building")
        self.assertEqual(result["helpful_tip"], "")
        self.assertEqual(result["suggested_questions"], [
            "What services does the Criminology Building offer?",
        ])
        for query in ("What is the library phone?", "Where is the Science Library?", "Write a poem"):
            with self.subTest(query=query):
                result = self.bot.query(query)
                self.assertEqual(result["helpful_tip"], "")
                self.assertEqual(result["suggested_questions"], [])

    def test_common_student_tasks_use_the_school_process_without_inventing_steps(self):
        for query, expected, source in (
            ("How do I enroll?", "enrollment form", "enrollment_procedures"),
            ("Unsaon pag enroll?", "enrollment form", "enrollment_procedures"),
            ("How can I borrow books?", "library card", "library"),
            ("Unsaon maghulam og libro?", "library card", "library"),
            ("Paano manghiram ng libro?", "library card", "library"),
            ("Can I use the computer lab?", "class", "computer_laborator"),
        ):
            with self.subTest(query=query):
                result = self.bot.query(query)
                self.assertEqual(result["status"], "SUCCESS", result)
                self.assertIn(expected, result["answer"].casefold())
                self.assertIn(source, result["source_details"][0]["source_doc"])


if __name__ == "__main__":
    unittest.main()
