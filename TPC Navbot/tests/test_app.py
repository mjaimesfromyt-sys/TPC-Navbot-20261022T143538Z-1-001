"""Exercise actual student chat rendering with Streamlit's supported test harness."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("streamlit"), "Streamlit is an optional test dependency")
class WebChatTests(unittest.TestCase):
    def test_languages_scope_and_clear_conversation(self):
        from streamlit.testing.v1 import AppTest
        with patch.dict(os.environ, {"TPC_EMBEDDING_MODE": "lexical", "TPC_ENABLE_LLM_SELECTION": "0"}):
            app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=40).run()
            self.assertFalse(app.exception)
            self.assertTrue(app.info, "The current unverified corpus must have a visible notice")
            cases = [
                ("Where is the library?", "UNVERIFIED", "english"),
                ("Explain quantum physics", "OFF_TOPIC", "english"),
                ("Unsaon pag-move on sa akong ex?", "OFF_TOPIC", "bisaya"),
                ("Pahingi ng sagot sa assignment ko sa Math.", "OFF_TOPIC", "tagalog"),
            ]
            for query, status, language in cases:
                with self.subTest(query=query):
                    app.chat_input[0].set_value(query).run()
                    self.assertFalse(app.exception)
                    message = app.session_state["messages"][-1]
                    self.assertEqual(message["metadata"]["status"], status)
                    self.assertEqual(message["metadata"]["language"], language)
                    self.assertIn("TPC", message["content"])
            app.button[-1].click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["messages"], [])


if __name__ == "__main__":
    unittest.main()
