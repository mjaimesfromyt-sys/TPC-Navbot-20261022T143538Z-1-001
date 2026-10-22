"""Student-facing chat; scope and verification are enforced by the RAG service."""
from pathlib import Path
import sys
import time
from uuid import uuid4

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.llm_rag import TPCNavBotRAG

st.set_page_config(page_title="TPC NavBot | Campus assistant", page_icon="🎓", layout="wide")


def show_evidence(metadata):
    statuses = {
        "SUCCESS": "Answered from reviewed campus information",
        "UNVERIFIED": "Campus information needs confirmation",
        "OFF_TOPIC": "Outside TPC campus assistance",
        "CLARIFICATION": "A little more information is needed",
        "ERROR": "The request could not be completed",
    }
    with st.expander("Sources and answer status"):
        st.write(statuses.get(metadata.get("status"), "Information unavailable"))
        st.caption(f"Language: {metadata.get('language', 'english').title()}")
        sources = metadata.get("sources", [])
        if sources:
            for source in sources:
                st.write(f"• {source}")
        else:
            st.caption("No verified source supports a factual answer to this question.")


if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "rag_bot" not in st.session_state:
    try:
        with st.spinner("Loading campus information…"):
            st.session_state.rag_bot = TPCNavBotRAG()
    except Exception:
        st.error("Campus information could not be loaded. Please try again later.")
        st.stop()

bot = st.session_state.rag_bot
with st.sidebar:
    st.title("🎓 TPC NavBot")
    st.caption("Talibon Polytechnic College")
    st.write("Bisaya · English · Tagalog")
    st.write("Ask about campus locations, offices, facilities, and supported TPC services.")
    st.divider()
    st.subheader("Try a campus question")
    for index, question in enumerate([
        "Where is the Registrar's Office?",
        "Asa dapit ang library?",
        "Saan po ang Guidance Office?",
        "Where is Room 203?",
    ]):
        if st.button(question, key=f"quick_{index}", use_container_width=True):
            st.session_state.preset_query = question
    st.divider()
    st.caption("Routes, walking times, and accessibility details are shown only when verified.")
    if st.button("Clear conversation", use_container_width=True):
        bot.reset_conversation(st.session_state.session_id)
        st.session_state.messages = []
        st.session_state.pop("preset_query", None)
        st.rerun()

st.title("Find your way around TPC")
st.write("Pangutana sa Bisaya. Ask in English. Magtanong sa Tagalog.")
metadatas = getattr(bot.vector_store, "metadatas", [])
verified_docs = {meta.get("source_doc") for meta in metadatas if meta.get("verified_source") is True}
if not verified_docs:
    st.info(
        "Campus details are awaiting verification. I can help identify what you need, "
        "but I will ask you to confirm locations with TPC personnel instead of guessing. "
        "Wala pa makumpirma ang mga detalye sa campus. "
        "Hindi pa beripikado ang mga detalye ng campus."
    )
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("metadata"):
            show_evidence(message["metadata"])

prompt = st.chat_input("Ask about a TPC classroom, office, or service…", max_chars=2000)
prompt = st.session_state.pop("preset_query", None) or prompt
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        started = time.perf_counter()
        with st.spinner("Checking campus information…"):
            try:
                response = bot.chat(prompt, session_id=st.session_state.session_id)
            except Exception:
                language = bot.detect_language(prompt)
                response = {"status": "ERROR", "language": language, "sources": [],
                            "answer": bot.get_unverified_refusal(language)}
        st.markdown(response["answer"])
        metadata = {
            "status": response.get("status", "ERROR"),
            "language": response.get("language", "english"),
            "sources": response.get("sources", []),
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "turn_count": response.get("turn_count", 1),
        }
        show_evidence(metadata)
    st.session_state.messages.append({"role": "assistant", "content": response["answer"], "metadata": metadata})
