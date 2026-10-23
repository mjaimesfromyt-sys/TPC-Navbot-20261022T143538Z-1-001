"""Exercise actual student chat rendering with Streamlit's supported test harness."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is an optional test dependency")
class WebChatTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            "TPC_EMBEDDING_MODE": "lexical",
            "TPC_ENABLE_LLM_SELECTION": "0",
        })
        environment.start()
        self.addCleanup(environment.stop)

    def start_app(self):
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=40).run()
        self.assertFalse(app.exception)
        return app

    def test_languages_and_campus_scope(self):
        app = self.start_app()
        self.assertTrue(app.info, "The current unverified corpus must have a visible notice")
        cases = [
            ("Where is the library?", "UNVERIFIED", "english"),
            ("Explain quantum physics", "OFF_TOPIC", "english"),
            ("Unsaon pag-move on sa akong ex?", "OFF_TOPIC", "bisaya"),
            ("Pahingi ng sagot sa assignment ko sa Math.", "OFF_TOPIC", "tagalog"),
        ]
        for query, status, language in cases:
            with self.subTest(query=query):
                app.chat_input(key="campus_prompt").set_value(query).run()
                self.assertFalse(app.exception)
                message = app.session_state["messages"][-1]
                self.assertEqual(message["metadata"]["status"], status)
                self.assertEqual(message["metadata"]["language"], language)
                self.assertIn("TPC", message["content"])

    def test_quick_questions_submit_one_campus_turn(self):
        for key, destination, language in [
            ("quick_registrar", "registrar", "english"),
            ("quick_library", "library", "bisaya"),
            ("quick_guidance", "guidance", "tagalog"),
            ("quick_room", "203", "english"),
        ]:
            with self.subTest(button=key):
                app = self.start_app()
                app.button(key=key).click().run()
                self.assertFalse(app.exception)
                messages = app.session_state["messages"]
                self.assertEqual([message["role"] for message in messages], ["user", "assistant"])
                self.assertIn(destination, messages[0]["content"].lower())
                self.assertEqual(messages[1]["metadata"]["language"], language)
                self.assertEqual(messages[1]["metadata"]["status"], "UNVERIFIED")
                # A regular rerun must not submit the selected question again.
                app.run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.session_state["messages"]), 2)

    def test_new_chat_clears_transcript_and_backend_context(self):
        app = self.start_app()
        app.chat_input(key="campus_prompt").set_value("Directions to the library from Main Gate?").run()
        self.assertFalse(app.exception)
        bot = app.session_state["rag_bot"]
        session_id = app.session_state["session_id"]
        session = bot.memory_manager.get_session(session_id)
        self.assertTrue(session.history)
        self.assertEqual(session.last_entity, "library")
        self.assertTrue(session.starting_point)

        app.button(key="new_chat").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["messages"], [])
        self.assertEqual(session.history, [])
        self.assertIsNone(session.last_entity)
        self.assertIsNone(session.starting_point)
        self.assertEqual(session.pending_buildings, [])
        self.assertEqual(session.pending_starts, [])
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["messages"], [])

    def test_answer_displays_status_language_and_source_evidence(self):
        app = self.start_app()
        source = "SYNTHETIC TEST SOURCE: Student Services Guide, p. 12"
        response = {
            "answer": "Synthetic reviewed campus answer for this UI test.",
            "status": "SUCCESS", "language": "english", "sources": [source], "turn_count": 1,
        }
        with patch("src.llm_rag.TPCNavBotRAG.chat", return_value=response):
            app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
        self.assertFalse(app.exception)
        self.assertTrue(app.expander, "Answers must expose their supporting evidence")
        rendered = "\n".join(element.value for element in app.markdown)
        captions = "\n".join(element.value for element in app.caption)
        source_labels = "\n".join(element.value for element in app.text)
        self.assertIn(response["answer"], rendered)
        self.assertIn(source, source_labels)
        self.assertTrue(any("1 source" in element.label for element in app.expander))
        self.assertIn("verified campus information", rendered.lower())
        self.assertIn("English", captions)
        self.assertEqual(app.session_state["messages"][-1]["metadata"]["sources"], [source])

    def test_chat_failure_is_localized_and_next_request_can_recover(self):
        from src.llm_rag import MESSAGES

        app = self.start_app()
        bot = app.session_state["rag_bot"]
        with patch.object(bot, "chat", side_effect=RuntimeError("Synthetic retrieval failure")):
            app.chat_input(key="campus_prompt").set_value("Saan po ang library?").run()
        self.assertFalse(app.exception)
        failed_answer = app.session_state["messages"][-1]
        self.assertEqual(failed_answer["metadata"]["status"], "ERROR")
        self.assertEqual(failed_answer["metadata"]["language"], "tagalog")
        self.assertEqual(failed_answer["metadata"]["sources"], [])
        self.assertEqual(failed_answer["content"], MESSAGES["tagalog"]["error"])
        self.assertNotEqual(failed_answer["content"], MESSAGES["tagalog"]["unverified"])
        self.assertIn(failed_answer["content"], "\n".join(element.value for element in app.markdown))

        # A later turn reaches the real offline service after the failed request.
        app.chat_input(key="campus_prompt").set_value("Where is the Registrar's Office?").run()
        self.assertFalse(app.exception)
        messages = app.session_state["messages"]
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[-1]["metadata"]["status"], "UNVERIFIED")
        self.assertEqual(messages[-1]["metadata"]["language"], "english")
        self.assertEqual(messages[-1]["content"], MESSAGES["english"]["unverified"])

    def test_guide_question_and_about_navigation_preserve_conversation(self):
        app = self.start_app()
        app.button(key="nav_campus_guide").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "Campus guide")
        app.button(key="guide_book_0").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "Assistant")
        messages = [dict(message) for message in app.session_state["messages"]]
        self.assertEqual(len(messages), 2)
        self.assertIn("library", messages[0]["content"].lower())
        session_id = app.session_state["session_id"]
        backend_session = app.session_state["rag_bot"].memory_manager.get_session(session_id)
        history_length = len(backend_session.history)

        app.button(key="nav_about_navbot").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "About NavBot")
        self.assertEqual(app.session_state["messages"], messages)
        app.button(key="nav_assistant").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["view"], "Assistant")
        self.assertEqual(app.session_state["session_id"], session_id)
        self.assertEqual(app.session_state["messages"], messages)
        self.assertEqual(len(backend_session.history), history_length)
        self.assertTrue(app.chat_input(key="campus_prompt"))

    def test_initialization_failure_can_retry_without_reloading_page(self):
        from src.llm_rag import TPCNavBotRAG

        attempts = []

        def load_bot():
            attempts.append(True)
            if len(attempts) == 1:
                raise RuntimeError("Synthetic loader failure")
            return TPCNavBotRAG()

        with patch("src.llm_rag.TPCNavBotRAG", side_effect=load_bot):
            app = self.start_app()
            self.assertTrue(app.error, "A failed load must explain how students can recover")
            app.button(key="retry_load").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(attempts), 2)
        self.assertIsInstance(app.session_state["rag_bot"], TPCNavBotRAG)
        self.assertEqual(app.session_state["messages"], [])
        self.assertFalse(app.error)
        self.assertTrue(app.chat_input(key="campus_prompt"))


if __name__ == "__main__":
    unittest.main()
