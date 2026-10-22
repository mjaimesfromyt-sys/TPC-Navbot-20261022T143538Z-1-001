"""Repeatable live-corpus demonstration; no sample source is promoted to verified."""
from pathlib import Path
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.llm_rag import TPCNavBotRAG


def run_checkpoint3_demo():
    bot = TPCNavBotRAG(use_llm=False)
    cases = [
        ("Where is the Registrar's Office?", "UNVERIFIED", "english"),
        ("What are its operating hours?", "UNVERIFIED", "english"),
        ("Asa dapit ang Guidance Office?", "UNVERIFIED", "bisaya"),
        ("Saan po ang library?", "UNVERIFIED", "tagalog"),
        ("Explain quantum physics", "OFF_TOPIC", "english"),
        ("Unsaon pag-move on sa akong ex?", "OFF_TOPIC", "bisaya"),
        ("Pahingi ng sagot sa assignment ko sa Math.", "OFF_TOPIC", "tagalog"),
        ("Where is the TPC campus swimming pool?", "UNVERIFIED", "english"),
    ]
    passed = 0
    print("TPC NavBot: actual unverified-corpus behavior (no paid API calls)")
    print("Verified-source success, route and clarification cases use isolated fixtures in the test suite.")
    print(f"Orchestration: {bot.orchestration_backend}")
    for number, (query, expected_status, language) in enumerate(cases, 1):
        started = time.perf_counter()
        result = bot.chat(query, session_id="checkpoint_demo")
        ok = result["status"] == expected_status and result["language"] == language
        passed += int(ok)
        print(f"\n{number}. {query}")
        print(f"{'PASS' if ok else 'FAIL'} | {result['status']} | {result['language']} | {(time.perf_counter()-started)*1000:.1f}ms")
        print(result["answer"])
    print(f"\nMeasured results: {passed}/{len(cases)} expected responses.")
    return passed == len(cases)


if __name__ == "__main__":
    sys.exit(0 if run_checkpoint3_demo() else 1)
