"""Student-facing campus assistant; factual grounding stays in the RAG service."""
from base64 import b64encode
from html import escape
from pathlib import Path
import sys
import time
from uuid import uuid4

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.llm_rag import MESSAGES, TPCNavBotRAG

st.set_page_config(
    page_title="TPC NavBot · Your campus companion", page_icon="🌿",
    layout="wide", initial_sidebar_state="auto",
)

STATUSES = {
    "SUCCESS": ("Verified campus information", "verified", "✓"),
    "UNVERIFIED": ("Needs campus confirmation", "pending", "!"),
    "OFF_TOPIC": ("Outside campus assistance", "neutral", "↗"),
    "CLARIFICATION": ("A little more detail needed", "neutral", "?"),
    "ERROR": ("Unable to complete this request", "error", "!"),
}
STARTERS = [
    ("registrar", "office", "Find an office", "Registrar’s Office", "Where is the Registrar's Office?"),
    ("library", "book", "Explore a facility", "Campus library", "Asa dapit ang library?"),
    ("guidance", "chat", "Get student support", "Guidance Office", "Saan po ang Guidance Office?"),
    ("room", "door", "Locate a classroom", "Rooms & buildings", "Where is Room 203?"),
]
ICON_PATHS = {
    "office": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 21v-4h6v4M9 7h1m4 0h1M9 11h1m4 0h1"/>',
    "book": '<path d="M12 5C8 2 3 4 3 4v15s5-2 9 1c4-3 9-1 9-1V4s-5-2-9 1Zm0 0v15"/>',
    "chat": '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5A8.5 8.5 0 0 1 10.5 3h2a8.5 8.5 0 0 1 8.5 8.5Z"/><path d="M7 11h.01M12 11h.01M17 11h.01"/>',
    "door": '<path d="M4 21h16M6 21V3h12v18M14 12h.01"/>',
    "compass": '<circle cx="12" cy="12" r="9"/><path d="m16 8-2.5 5.5L8 16l2.5-5.5L16 8Z"/>',
}


def icon(name, css_class="line-icon"):
    return (
        f'<svg class="{css_class}" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{ICON_PATHS[name]}</svg>'
    )


def html(markup):
    st.markdown(markup, unsafe_allow_html=True)


def select_view(view):
    st.session_state.view = view


def ask_question(question):
    st.session_state.preset_query = question
    st.session_state.view = "Assistant"


def new_conversation():
    bot = st.session_state.get("rag_bot")
    if bot is not None:
        bot.reset_conversation(st.session_state.session_id)
    st.session_state.messages = []
    st.session_state.session_id = str(uuid4())
    st.session_state.pop("preset_query", None)
    st.session_state.view = "Assistant"


def show_evidence(metadata):
    label, tone, symbol = STATUSES.get(metadata.get("status"), ("Status unavailable", "neutral", "?"))
    language = str(metadata.get("language", "english")).title()
    html(
        f'<div class="answer-meta"><span class="answer-status {tone}">'
        f'<span aria-hidden="true">{symbol}</span> {label}</span>'
        f'<span class="answer-language">{escape(language)}</span></div>'
    )
    sources = metadata.get("sources") or []
    title = f"Sources & answer details · {len(sources)} source{'s' if len(sources) != 1 else ''}"
    with st.expander(title):
        st.write(label)
        st.caption(f"Response language: {language}")
        if sources:
            for index, source in enumerate(sources, 1):
                # Source strings are labels, not trusted URLs or HTML.
                st.text(f"{index:02d} · {source}")
        else:
            st.caption("No verified source supports a factual answer to this question.")
        if metadata.get("latency_ms") is not None:
            st.caption(f"Checked in {metadata['latency_ms'] / 1000:.2f} seconds")


def render_sidebar():
    with st.sidebar:
        html(
            '<div class="brand"><div class="brand-symbol">' + icon("compass") + '</div>'
            '<div><div class="brand-name">TPC <span>NavBot</span></div>'
            '<div class="brand-subtitle">YOUR CAMPUS COMPANION</div></div></div>'
        )
        st.button(
            "New conversation", key="new_chat", icon=":material/add:",
            use_container_width=True, on_click=new_conversation, type="primary",
        )
        html('<div class="sidebar-label">WORKSPACE</div>')
        for view, material_icon in [
            ("Assistant", "chat_bubble_outline"), ("Campus guide", "explore"), ("About NavBot", "info"),
        ]:
            st.button(
                view, key=f"nav_{view.lower().replace(' ', '_')}",
                icon=f":material/{material_icon}:", use_container_width=True,
                type="primary" if st.session_state.view == view else "secondary",
                on_click=select_view, args=(view,),
            )
        html('<div class="sidebar-label conversation-label">THIS CONVERSATION</div>')
        user_messages = [message for message in st.session_state.messages if message["role"] == "user"]
        if user_messages:
            for message in user_messages[-3:]:
                html(f'<div class="conversation-item"><span aria-hidden="true">↳</span> {escape(message["content"])}</div>')
        else:
            html('<div class="sidebar-empty">A fresh start.<br>Your questions will appear here.</div>')
        with st.container(key="sidebar_footer"):
            html(
                '<div class="language-card"><span class="language-heading">A language that feels like home.</span>'
                '<div class="language-tags"><span>English</span><span>Bisaya</span><span>Tagalog</span></div>'
                '<p>Just ask. NavBot follows your language.</p></div>'
                '<div class="college-signature"><span class="college-monogram">TPC</span>'
                '<span>Talibon Polytechnic College<br><small>Built for our campus community</small></span></div>'
            )


def render_header():
    html(
        '<div class="topbar"><div class="breadcrumb">Workspace <span>/</span> '
        f'<strong>{escape(st.session_state.view)}</strong></div>'
        '<div class="topbar-tag"><span class="small-spark">✧</span> A little help goes a long way</div></div>'
    )


def render_verification_notice(bot):
    metadatas = getattr(bot.vector_store, "metadatas", [])
    verified_docs = {meta.get("source_doc") for meta in metadatas if meta.get("verified_source") is True}
    if not verified_docs:
        with st.container(key="verification_notice"):
            st.info(
                "**Campus details are awaiting verification.** I’ll help you find what to ask, "
                "but please confirm locations and services with authorized TPC personnel.",
                icon=":material/info:",
            )


def render_starters():
    html('<div class="section-heading"><h2>A good place to start</h2><span>Pick a question or ask your own below</span></div>')
    for column, (key, icon_name, eyebrow, title, question) in zip(st.columns(4, gap="small"), STARTERS):
        with column:
            with st.container(key=f"starter_{key}", border=True):
                html(
                    f'<div class="starter-icon {key}">{icon(icon_name)}</div>'
                    f'<div class="starter-eyebrow">{eyebrow}</div><h3 class="starter-title">{title}</h3>'
                )
                st.button(question + "  ↗", key=f"quick_{key}", use_container_width=True, on_click=ask_question, args=(question,))


def render_welcome():
    illustration = b64encode((PROJECT_ROOT / "assets" / "campus.svg").read_bytes()).decode("ascii")
    html(
        '<div class="welcome"><div class="welcome-copy">'
        '<div class="eyebrow"><span></span> A FRIENDLIER WAY TO FIND YOUR WAY</div>'
        '<h1>A little guidance.<br>A better <em>campus day.</em></h1>'
        '<p>From your next classroom to the right office,<br class="desktop-break"> '
        'let’s find your way around TPC. What do you need?</p>'
        '<div class="welcome-languages">Pangutana. <span>Ask.</span> Magtanong.</div></div>'
        f'<img class="campus-illustration" src="data:image/svg+xml;base64,{illustration}" '
        'alt="Decorative illustration of a college building, trees, and a navigation pin"></div>'
    )
    render_starters()
    html(
        '<div class="help-strip"><span class="help-strip-icon">' + icon("compass") + '</span>'
        '<div><strong>Your campus, a little less confusing.</strong>'
        '<p>Ask about offices, classrooms, facilities, and student services.</p></div>'
        '<span class="help-strip-note">Campus questions welcome</span></div>'
    )


def render_guide(bot):
    html('<div class="page-intro"><div class="eyebrow">EXPLORE WHAT YOU CAN ASK</div><h1>Start with a place.<br><em>We’ll take it from there.</em></h1><p>Choose a topic to ask NavBot. Locations and services are shared only when verified.</p></div>')
    groups = [
        ("office", "Offices & student support", [
            ("Registrar’s Office", "Where is the Registrar's Office?"),
            ("Guidance Office", "Where is the Guidance Office?"),
            ("Admissions", "What services does the admissions office offer?"),
            ("Cashier", "Where is the cashier?"),
        ]),
        ("book", "Spaces for campus life", [
            ("Library", "Where is the library?"), ("Classrooms", "Where is Room 203?"),
            ("Canteen", "Asa dapit ang canteen?"), ("Gymnasium", "Where is the gymnasium?"),
        ]),
    ]
    for column, (icon_name, title, questions) in zip(st.columns(2, gap="medium"), groups):
        with column:
            with st.container(border=True):
                html(f'<div class="guide-heading">{icon(icon_name)}<h2>{title}</h2></div>')
                for index, (label, question) in enumerate(questions):
                    st.button(label + "  ↗", key=f"guide_{icon_name}_{index}", use_container_width=True, on_click=ask_question, args=(question,))
    render_verification_notice(bot)
    st.caption("These topics help you start a conversation. Campus details need reviewed sources.")


def render_about():
    html('<div class="page-intro"><div class="eyebrow">MEET YOUR CAMPUS COMPANION</div><h1>Helpful answers.<br><em>Grounded in trust.</em></h1><p>NavBot helps the Talibon Polytechnic College community ask about campus locations and supported services in English, Bisaya, or Tagalog.</p></div>')
    for column, (number, title, description) in zip(st.columns(3, gap="medium"), [
        ("01", "Ask naturally", "Use your own words and language. For directions, include where you’re starting from."),
        ("02", "Check campus sources", "NavBot retrieves relevant campus records and checks whether the facts have been reviewed."),
        ("03", "Know what’s supported", "Every answer includes a status and source details. Missing facts stay unconfirmed."),
    ]):
        with column:
            with st.container(border=True):
                html(f'<div class="about-step">{number}</div><h3>{title}</h3><p class="about-description">{description}</p>')
    with st.expander("What does an answer status mean?", expanded=True):
        for label, tone, symbol in STATUSES.values():
            html(f'<div class="status-explanation"><span class="answer-status {tone}">{symbol} {label}</span></div>')
        st.caption("Verified locations do not automatically verify routes, walking times, or accessibility details. These need their own reviewed evidence.")
    st.caption("Conversations are held in this browser session. New conversation clears the active chat and its follow-up context.")


def render_chat(bot):
    if st.session_state.messages:
        html('<div class="chat-heading"><div class="eyebrow">YOUR CAMPUS CONVERSATION</div><h1>Let’s find your way.</h1><p>Keep asking. You can follow up in your own language.</p></div>')
    else:
        render_welcome()
    render_verification_notice(bot)
    with st.container(key="conversation"):
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar=":material/person:" if message["role"] == "user" else ":material/explore:"):
                st.caption("You" if message["role"] == "user" else "TPC NavBot")
                st.markdown(message["content"])
                if message.get("metadata"):
                    show_evidence(message["metadata"])

    prompt = st.chat_input("Ask about a classroom, office, or campus service…", key="campus_prompt", max_chars=2000)
    prompt = st.session_state.pop("preset_query", None) or prompt
    if prompt and prompt.strip():
        prompt = prompt.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=":material/person:"):
            st.caption("You")
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=":material/explore:"):
            st.caption("TPC NavBot")
            started = time.perf_counter()
            with st.spinner("Checking campus information…"):
                try:
                    response = bot.chat(prompt, session_id=st.session_state.session_id)
                except Exception:
                    language = bot.detect_language(prompt)
                    response = {"status": "ERROR", "language": language, "sources": [], "answer": MESSAGES[language]["error"]}
            metadata = {
                "status": response.get("status", "ERROR"), "language": response.get("language", "english"),
                "sources": response.get("sources", []), "latency_ms": round((time.perf_counter() - started) * 1000),
                "turn_count": response.get("turn_count", 1),
            }
            st.markdown(response["answer"])
            show_evidence(metadata)
        st.session_state.messages.append({"role": "assistant", "content": response["answer"], "metadata": metadata})
        # Redraw removes the empty state and refreshes the sidebar transcript.
        st.rerun()
    html('<div class="composer-note">Made for campus questions. Always check the answer status and sources.</div>')


def main():
    html(f'<style>{(PROJECT_ROOT / "assets" / "styles.css").read_text(encoding="utf-8")}</style>')
    for key, default in [("messages", []), ("session_id", str(uuid4())), ("view", "Assistant")]:
        if key not in st.session_state:
            st.session_state[key] = default
    render_sidebar()
    render_header()
    if "rag_bot" not in st.session_state:
        try:
            with st.spinner("Getting your campus companion ready…"):
                st.session_state.rag_bot = TPCNavBotRAG()
        except Exception:
            st.error("Campus information could not be loaded. Please try again.")
            if st.button("Try again", key="retry_load", icon=":material/refresh:"):
                st.rerun()
            st.stop()
    bot = st.session_state.rag_bot
    if st.session_state.view == "Campus guide":
        render_guide(bot)
    elif st.session_state.view == "About NavBot":
        render_about()
    else:
        render_chat(bot)


if __name__ == "__main__":
    main()
