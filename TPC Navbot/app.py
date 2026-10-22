import os
import sys
import time
import streamlit as st

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.llm_rag import TPCNavBotRAG

# Page Configuration
st.set_page_config(
    page_title="TPC NavBot | Campus AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1E3A8A;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #4B5563;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .lang-badge {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 3px 8px;
        border-radius: 12px;
        border: 1px solid #FDE68A;
        margin-bottom: 8px;
    }
    .guardrail-success {
        color: #15803D;
        font-weight: 600;
    }
    .guardrail-unverified {
        color: #B45309;
        font-weight: 600;
    }
    .guardrail-offtopic {
        color: #B91C1C;
        font-weight: 600;
    }
    .source-tag {
        background-color: #EFF6FF;
        border: 1px solid #DBEAFE;
        color: #1D4ED8;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 0.82rem;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{int(time.time())}"

if "rag_bot" not in st.session_state:
    with st.spinner("Initializing ChromaDB Vector Store & Knowledge Base..."):
        st.session_state.rag_bot = TPCNavBotRAG()

bot = st.session_state.rag_bot

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/graduation-cap.png", width=64)
    st.title("TPC NavBot")
    st.markdown('<div class="lang-badge">🗣️ Bisaya • English • Tagalog</div>', unsafe_allow_html=True)
    st.markdown("**Campus**: Talibon Polytechnic College  \n**Location**: San Isidro, Talibon, Bohol")
    
    st.divider()
    
    st.subheader("⚡ Quick Navigation Shortcuts")
    quick_queries = [
        "Where is the BSIS Department Office?",
        "Asa dapit ang opisina sa BSIS?",
        "Asa ko magbayad sa akong tuition fee ug exam permit?",
        "Saan po ang Registrar para sa transcript of records?",
        "Asa ang clinic kung malipong ko?",
        "Saan magre-report kung nawala ang student ID?",
        "What are the Library operating hours?"
    ]
    
    for q in quick_queries:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.session_state.preset_query = q

    st.divider()
    
    st.subheader("⚙️ System Status")
    api_key_present = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    st.write(f"**Gemini AI Engine**: {'🟢 Active (.env)' if api_key_present else '🟡 Fallback Mode'}")
    st.write(f"**Vector Database**: ChromaDB Persistent")
    st.write(f"**Indexed Chunks**: {len(bot.vector_store.documents)} chunks (30 docs)")
    st.write(f"**Languages Supported**: Bisaya, Tagalog, English")
    
    if st.button("🗑️ Clear Conversation History", use_container_width=True):
        st.session_state.messages = []
        bot.reset_conversation(st.session_state.session_id)
        st.rerun()

# Main Header
st.markdown('<div class="main-header">🎓 TPC NavBot: Campus Navigation & RAG Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Pangutana mahitungod sa mga lawak, opisina, bayranan sa tuition, clinic, ug polisiya sa TPC sa <b>Bisaya</b>, <b>English</b>, o <b>Tagalog</b>.</div>', unsafe_allow_html=True)

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "metadata" in msg and msg["metadata"]:
            meta = msg["metadata"]
            with st.expander("🔍 Retrieval & Grounding Inspector"):
                col1, col2 = st.columns(2)
                with col1:
                    status = meta.get("status", "SUCCESS")
                    if status == "SUCCESS":
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-success'>✅ {status} (Verified Grounded)</span>", unsafe_allow_html=True)
                    elif status == "UNVERIFIED":
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-unverified'>⚠️ {status} (Not in Knowledge Base)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-offtopic'>🛑 {status} (Blocked Off-Topic)</span>", unsafe_allow_html=True)
                    st.write(f"**Language Detected**: {meta.get('language', 'english').title()}")
                    st.write(f"**Latency**: {meta.get('latency_ms', 0)} ms")
                with col2:
                    sources = meta.get("sources", [])
                    st.write("**Citations**:")
                    if sources:
                        for s in sources:
                            st.markdown(f"<span class='source-tag'>📄 {s}</span>", unsafe_allow_html=True)
                    else:
                        st.write("No source documents retrieved.")

# Handle Input
prompt = st.chat_input("Ask in Bisaya, Tagalog, or English (e.g. 'Asa dapit ang BSIS?', 'Saan ang Cashier?')...")

if hasattr(st.session_state, "preset_query") and st.session_state.preset_query:
    prompt = st.session_state.preset_query
    st.session_state.preset_query = None

if prompt:
    # Add User Message to UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process via TPC NavBot Multilingual RAG
    with st.chat_message("assistant"):
        with st.spinner("Searching ChromaDB & synthesizing verified answer..."):
            start_t = time.time()
            response = bot.chat(prompt, session_id=st.session_state.session_id)
            latency_ms = int((time.time() - start_t) * 1000)

            st.markdown(response["answer"])

            # Metadata Display
            meta = {
                "status": response.get("status"),
                "sources": response.get("sources", []),
                "latency_ms": latency_ms,
                "turn_count": response.get("turn_count", 1),
                "language": response.get("language", "english")
            }
            with st.expander("🔍 Retrieval & Grounding Inspector"):
                col1, col2 = st.columns(2)
                with col1:
                    status = meta["status"]
                    if status == "SUCCESS":
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-success'>✅ {status} (Verified Grounded)</span>", unsafe_allow_html=True)
                    elif status == "UNVERIFIED":
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-unverified'>⚠️ {status} (Not in Knowledge Base)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Guardrail Status**: <span class='guardrail-offtopic'>🛑 {status} (Blocked Off-Topic)</span>", unsafe_allow_html=True)
                    st.write(f"**Language Detected**: {meta['language'].title()}")
                    st.write(f"**Latency**: {latency_ms} ms")
                    st.write(f"**Session Turn Count**: {meta['turn_count']}")
                with col2:
                    sources = meta["sources"]
                    st.write("**Citations**:")
                    if sources:
                        for s in sources:
                            st.markdown(f"<span class='source-tag'>📄 {s}</span>", unsafe_allow_html=True)
                    else:
                        st.write("None (Blocked by Guardrail or Unverified)")

    # Save to Chat History
    st.session_state.messages.append({
        "role": "assistant",
        "content": response["answer"],
        "metadata": meta
    })
