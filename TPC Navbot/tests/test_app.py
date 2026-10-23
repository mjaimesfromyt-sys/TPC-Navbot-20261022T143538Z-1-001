"""Exercise actual student chat rendering with Streamlit's supported test harness."""
import importlib.util
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is an optional test dependency")
class WebChatTests(unittest.TestCase):
    def setUp(self):
        # UI refusal tests use their own unreviewed fixture. They must remain
        # stable as personnel approve records in the real campus corpus, and
        # must never write ingestion artifacts to the application's data folder.
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name)
        raw = base / "raw"
        raw.mkdir()
        self.raw = raw
        (raw / "synthetic_unverified.txt").write_text(
            "Building Name: Synthetic Test Hall\nLocation ID: TEST-ONLY\n\n"
            "Unreviewed test fixture only: library, Registrar's Office, Guidance Office, Room 203.\n",
            encoding="utf-8",
        )
        registry = base / "registry.json"
        registry.write_text(json.dumps({"documents": {}}), encoding="utf-8")
        paths = {
            "RAW_DATA_DIR": raw,
            "SOURCE_REGISTRY_PATH": registry,
            "PERSIST_DIRECTORY": base / "vectors",
            "MANIFEST_PATH": base / "manifest.json",
            "PROCESSED_CHUNKS_PATH": base / "processed" / "chunks.jsonl",
        }
        environment = patch.dict(os.environ, {
            "TPC_EMBEDDING_MODE": "lexical",
            "TPC_ENABLE_LLM_SELECTION": "0",
            "TPC_RAW_DATA_DIR": str(paths["RAW_DATA_DIR"]),
            "TPC_SOURCE_REGISTRY": str(paths["SOURCE_REGISTRY_PATH"]),
            "TPC_VECTOR_STORE_DIR": str(paths["PERSIST_DIRECTORY"]),
            "TPC_INGESTION_MANIFEST": str(paths["MANIFEST_PATH"]),
            "TPC_PROCESSED_CHUNKS": str(paths["PROCESSED_CHUNKS_PATH"]),
            "TPC_LEARNING_PATH": str(base / "learning.sqlite3"),
        })
        environment.start()
        self.addCleanup(environment.stop)
        # Other test modules may have imported these constants before setUp.
        for module_name in ("src.config", "src.preprocessing", "src.vector_store", "src.ingestion"):
            module = importlib.import_module(module_name)
            path_patch = patch.multiple(module, **{
                name: value for name, value in paths.items() if hasattr(module, name)
            })
            path_patch.start()
            self.addCleanup(path_patch.stop)
        from src.vector_store import VectorStore

        original_init = VectorStore.__init__

        def initialize_memory_store(instance, *args, **kwargs):
            # Chroma keeps file handles open on Windows; UI tests exercise the
            # same retrieval API without requiring a persistent database.
            kwargs["backend"] = "memory"
            original_init(instance, *args, **kwargs)

        backend_patch = patch.object(VectorStore, "__init__", initialize_memory_store)
        backend_patch.start()
        self.addCleanup(backend_patch.stop)

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

    def test_campus_data_change_refreshes_backend_and_preserves_transcript(self):
        app = self.start_app()
        app.chat_input(key="campus_prompt").set_value("Directions to the library from Main Gate?").run()
        self.assertFalse(app.exception)
        original_bot = app.session_state["rag_bot"]
        original_revision = app.session_state["knowledge_revision"]
        session_id = app.session_state["session_id"]
        transcript = [dict(message) for message in app.session_state["messages"]]
        original_session = original_bot.memory_manager.get_session(session_id)
        self.assertTrue(original_session.history)
        self.assertEqual(original_session.last_entity, "library")
        self.assertTrue(original_session.starting_point)

        (self.raw / "synthetic_added_after_load.txt").write_text(
            "Building Name: Additional Synthetic Hall\nLocation ID: TEST-ONLY-NEW\n\n"
            "Unreviewed synthetic fixture added while the student app is open.\n",
            encoding="utf-8",
        )
        app.run()
        self.assertFalse(app.exception)
        refreshed_bot = app.session_state["rag_bot"]
        self.assertIsNot(refreshed_bot, original_bot)
        self.assertNotEqual(app.session_state["knowledge_revision"], original_revision)
        self.assertEqual(app.session_state["session_id"], session_id)
        self.assertEqual(app.session_state["messages"], transcript)
        refreshed_session = refreshed_bot.memory_manager.get_session(session_id)
        self.assertEqual(refreshed_session.history, [])
        self.assertIsNone(refreshed_session.last_entity)
        self.assertIsNone(refreshed_session.starting_point)
        self.assertEqual(refreshed_session.pending_buildings, [])
        self.assertEqual(refreshed_session.pending_starts, [])

    def test_answer_displays_status_language_and_source_evidence(self):
        app = self.start_app()
        app.checkbox(key="show_answer_details").check().run()
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

    def test_structured_evidence_is_available_in_expander_without_cluttering_answer(self):
        app = self.start_app()
        app.checkbox(key="show_answer_details").check().run()
        source_doc = "reviewed-fixture.txt"
        reference = "Authorized campus test record"
        source = f"{source_doc} [{reference}]"
        details = [{
            "destination": "Library", "source_doc": source_doc,
            "official_source": reference, "reviewed_by": "Test reviewer",
            "reviewed_at": "2026-10-22",
        }]
        response = {
            "answer": "Destination: **Library**\n\nBuilding: Synthetic Learning Center",
            "status": "SUCCESS", "language": "english", "sources": [source],
            "source_details": details, "turn_count": 1,
        }
        with patch("src.llm_rag.TPCNavBotRAG.chat", return_value=response):
            app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
        self.assertFalse(app.exception)
        message = app.session_state["messages"][-1]
        self.assertEqual(message["content"], response["answer"])
        self.assertEqual(message["metadata"]["sources"], [source])
        self.assertEqual(message["metadata"]["source_details"], details)
        evidence = next(element for element in app.expander if "1 source" in element.label)
        evidence_text = "\n".join(
            element.value for kind in ("markdown", "caption", "text")
            for element in getattr(evidence, kind)
        )
        for value in ("Library", source_doc, reference, "Test reviewer", "2026-10-22"):
            with self.subTest(evidence=value):
                self.assertIn(value, evidence_text)
        all_rendered = "\n".join(
            element.value for kind in ("markdown", "caption", "text")
            for element in getattr(app, kind)
        )
        for value in (source_doc, reference, "Test reviewer", "2026-10-22"):
            with self.subTest(answer_excludes=value):
                self.assertNotIn(value, message["content"])
                self.assertEqual(all_rendered.count(value), evidence_text.count(value))

        # Review details survive the ordinary rerun that renders saved messages.
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["messages"][-1]["metadata"]["source_details"], details)
        evidence = next(element for element in app.expander if "1 source" in element.label)
        self.assertIn(source_doc, "\n".join(
            element.value for kind in ("markdown", "caption", "text")
            for element in getattr(evidence, kind)
        ))

    def test_answers_show_plain_text_by_default_and_keep_evidence_available_on_request(self):
        app = self.start_app()
        self.assertFalse(app.checkbox(key="show_answer_details").value)
        source_doc = "synthetic_registrar.txt"
        reference = "Synthetic reviewed campus reference"
        response = {
            "answer": "The Registrar's Office is in front of the main gate.",
            "status": "SUCCESS", "language": "english",
            "sources": [f"{source_doc} [{reference}]"],
            "source_details": [{
                "destination": "Registrar's Office", "source_doc": source_doc,
                "official_source": reference, "reviewed_by": "Test reviewer",
                "reviewed_at": "2026-10-22",
            }],
        }
        with patch("src.llm_rag.TPCNavBotRAG.chat", return_value=response):
            app.chat_input(key="campus_prompt").set_value("Where is the Registrar's Office?").run()
        self.assertFalse(app.exception)
        self.assertFalse(any("Sources & answer details" in element.label for element in app.expander))
        rendered = "\n".join(
            element.value for kind in ("markdown", "caption", "text")
            for element in getattr(app, kind)
        )
        self.assertIn(response["answer"], rendered)
        for value in (source_doc, reference, "Test reviewer", "2026-10-22", '<div class="answer-meta">'):
            with self.subTest(hidden_evidence=value):
                self.assertNotIn(value, rendered)
        self.assertEqual(app.session_state["messages"][-1]["metadata"]["sources"], response["sources"])

        # Students can opt into the existing answer's complete review details.
        app.checkbox(key="show_answer_details").check().run()
        self.assertFalse(app.exception)
        evidence = next(element for element in app.expander if "1 source" in element.label)
        self.assertIn(source_doc, "\n".join(
            element.value for kind in ("markdown", "caption", "text")
            for element in getattr(evidence, kind)
        ))
        self.assertEqual(len(app.session_state["messages"]), 2)
        self.assertEqual(app.session_state["messages"][-1]["content"], response["answer"])

    def test_helpful_tip_and_latest_suggested_question_submit_one_turn(self):
        app = self.start_app()
        question = "What are the library office hours?"
        first_response = {
            "answer": "Synthetic library location.", "status": "SUCCESS", "language": "english",
            "sources": ["Synthetic reviewed source"],
            "helpful_tip": "The library provides reading and book services.",
            "suggested_questions": [question, "What services does the library offer?", "An extra suggestion"],
        }
        second_response = {
            "answer": "Synthetic library office hours.", "status": "SUCCESS", "language": "english",
            "sources": ["Synthetic reviewed source"], "helpful_tip": "",
            "suggested_questions": ["Where is the library?"],
        }
        with patch("src.llm_rag.TPCNavBotRAG.chat", side_effect=[first_response, second_response]) as chat:
            app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state["messages"]), 2)
            self.assertIn("Tip: " + first_response["helpful_tip"],
                          "\n".join(element.value for element in app.caption))
            self.assertEqual(app.session_state["messages"][-1]["content"], first_response["answer"])
            self.assertEqual(app.session_state["messages"][-1]["metadata"]["helpful_tip"],
                             first_response["helpful_tip"])
            self.assertEqual(app.session_state["messages"][-1]["metadata"]["suggested_questions"],
                             first_response["suggested_questions"])
            self.assertEqual(app.button(key="suggested_1_0").label, question)
            self.assertEqual(len([button for button in app.button if button.key.startswith("suggested_")]), 2)
            self.assertFalse(any("Sources & answer details" in element.label for element in app.expander))

            app.button(key="suggested_1_0").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(chat.call_count, 2)
            self.assertEqual(chat.call_args.args[0], question)
            self.assertEqual(len(app.session_state["messages"]), 4)
            self.assertEqual(app.session_state["messages"][-2]["content"], question)
            self.assertEqual(app.session_state["messages"][-1]["content"], second_response["answer"])
            self.assertFalse(any(button.key.startswith("suggested_1_") for button in app.button))
            self.assertEqual(app.button(key="suggested_3_0").label, second_response["suggested_questions"][0])
            self.assertFalse(any("Sources & answer details" in element.label for element in app.expander))

            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(chat.call_count, 2)
            self.assertEqual(len(app.session_state["messages"]), 4)

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

    def test_rate_limit_rejects_before_chat_and_localized_request_can_recover(self):
        from src.request_limits import RateLimitDecision

        app = self.start_app()
        bot = app.session_state["rag_bot"]
        browser_id = app.session_state["browser_rate_id"]
        session_id = app.session_state["session_id"]
        session = bot.memory_manager.get_session(session_id)
        with patch("src.request_limits.QueryRateLimiter.allow", side_effect=[
            RateLimitDecision(False, 7.2), RateLimitDecision(True),
        ]) as allowance, patch.object(bot, "chat", wraps=bot.chat) as chat:
            app.chat_input(key="campus_prompt").set_value("Saan po ang library?").run()
            self.assertFalse(app.exception)
            chat.assert_not_called()
            allowance.assert_called_once_with(browser_id)
            refused = app.session_state["messages"][-1]
            self.assertEqual(refused["metadata"]["status"], "RATE_LIMITED")
            self.assertEqual(refused["metadata"]["language"], "tagalog")
            self.assertEqual(refused["metadata"]["sources"], [])
            self.assertIn("Maghintay po ng 8 segundo", refused["content"])
            self.assertIn(refused["content"], "\n".join(element.value for element in app.markdown))
            self.assertEqual(session.history, [], "A throttled request must not enter RAG memory")

            app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
            self.assertFalse(app.exception)
            chat.assert_called_once_with("Where is the library?", session_id=session_id)
            self.assertEqual(allowance.call_count, 2)
            recovered = app.session_state["messages"][-1]
            self.assertEqual(recovered["metadata"]["status"], "UNVERIFIED")
            self.assertEqual(recovered["metadata"]["language"], "english")
            self.assertEqual(len(app.session_state["messages"]), 4)
            self.assertEqual(len(session.history), 2)

    def test_new_conversation_preserves_browser_rate_quota(self):
        from src.request_limits import QueryRateLimiter

        app = self.start_app()
        bot = app.session_state["rag_bot"]
        browser_id = app.session_state["browser_rate_id"]
        conversation_id = app.session_state["session_id"]
        # Keep one deterministic real quota while intercepting the UI's shared
        # limiter. Changing conversation IDs must not restore browser allowance.
        limiter = QueryRateLimiter(session_limit=1, clock=lambda: 1000.0)
        enforce_quota = limiter.allow
        with patch("src.request_limits.QueryRateLimiter.allow", side_effect=enforce_quota) as allowance, \
                patch.object(bot, "chat", wraps=bot.chat) as chat:
            app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
            self.assertFalse(app.exception)
            self.assertEqual(chat.call_count, 1)
            self.assertEqual(app.session_state["messages"][-1]["metadata"]["status"], "UNVERIFIED")

            app.button(key="new_chat").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["messages"], [])
            self.assertNotEqual(app.session_state["session_id"], conversation_id)
            self.assertEqual(app.session_state["browser_rate_id"], browser_id)

            app.chat_input(key="campus_prompt").set_value("Where is the registrar?").run()
            self.assertFalse(app.exception)
            self.assertEqual(chat.call_count, 1, "A new conversation must not bypass the exhausted quota")
            self.assertEqual(allowance.call_count, 2)
            self.assertTrue(all(call.args == (browser_id,) for call in allowance.call_args_list))
            self.assertEqual(app.session_state["messages"][-1]["metadata"]["status"], "RATE_LIMITED")
            current_session = bot.memory_manager.get_session(app.session_state["session_id"])
            self.assertEqual(current_session.history, [])

    def test_answer_feedback_records_once_and_disables_submitted_widget(self):
        app = self.start_app()
        bot = app.session_state["rag_bot"]
        app.chat_input(key="campus_prompt").set_value("Where is the library?").run()
        self.assertFalse(app.exception)
        message = app.session_state["messages"][-1]
        metadata = message["metadata"]
        feedback_key = "feedback_" + metadata["feedback_id"]
        self.assertFalse(app.feedback(key=feedback_key).disabled)
        with patch.object(bot.learning_store, "observe") as observe:
            app.feedback(key=feedback_key).set_value(1).run()
            self.assertFalse(app.exception)
            observe.assert_called_once_with(
                status="UNVERIFIED", entity="library", intent="location",
                language="english", feedback="helpful",
            )
            self.assertTrue(app.session_state["messages"][-1]["metadata"]["feedback_recorded"])
            self.assertTrue(app.feedback(key=feedback_key).disabled)
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(observe.call_count, 1, "Rerendering feedback must not duplicate learning counts")
            self.assertEqual(len(app.session_state["messages"]), 2)

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
