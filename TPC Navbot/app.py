"""Student-facing campus assistant; factual grounding stays in the RAG service."""
from base64 import b64encode
from html import escape
import logging
import math
from pathlib import Path
import sys
import time
import traceback
from uuid import uuid4

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "assets" / "tpc-logo.png"
sys.path.insert(0, str(PROJECT_ROOT))
from src.llm_rag import MESSAGES, TPCNavBotRAG
from src.learning import LearningStore
from src.query_safety import MAX_QUERY_CHARS, evaluate_query
from src.request_limits import QueryRateLimiter

logger = logging.getLogger("tpc_navbot.app")

st.set_page_config(
    page_title="TPC NavBot · Your campus companion", page_icon=str(LOGO_PATH),
    layout="wide", initial_sidebar_state="auto",
)

STATUSES = {
    "SUCCESS": ("Verified campus information", "verified", "✓"),
    "PARTIAL": ("Some details still need confirmation", "pending", "!"),
    "RATE_LIMITED": ("Please wait before asking again", "pending", "!"),
    "UNVERIFIED": ("Needs campus confirmation", "pending", "!"),
    "OFF_TOPIC": ("Outside campus assistance", "neutral", "↗"),
    "CLARIFICATION": ("A little more detail needed", "neutral", "?"),
    "ERROR": ("Unable to complete this request", "error", "!"),
}


@st.cache_resource
def chat_request_limiter():
    return QueryRateLimiter()


def record_answer_feedback(message_index):
    message = st.session_state.messages[message_index]
    metadata = message.get("metadata", {})
    key = "feedback_" + metadata["feedback_id"]
    value = st.session_state.get(key)
    bot = st.session_state.get("rag_bot")
    if value is None or metadata.get("feedback_recorded") or bot is None or bot.learning_store is None:
        return
    bot.learning_store.observe(
        status=metadata.get("status"), entity=metadata.get("entity"),
        intent=metadata.get("intent"), language=metadata.get("language"),
        feedback="helpful" if value == 1 else "not_helpful",
    )
    metadata["feedback_recorded"] = True
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
            details = metadata.get("source_details") or []
            for index, source in enumerate(sources, 1):
                detail = details[index - 1] if index <= len(details) else None
                if isinstance(detail, dict):
                    st.text(f"{index:02d} · {detail.get('destination', 'Campus record')}")
                    st.text(f"Reference: {detail.get('official_source', source)}")
                    st.caption(
                        f"Reviewed by {detail.get('reviewed_by', 'Not supplied')} · "
                        f"{detail.get('reviewed_at', 'Date not supplied')}"
                    )
                    st.caption(f"Source file: {detail.get('source_doc', 'Not supplied')}")
                    for key, label in (
                        ('document_title', 'Document'), ('section', 'Section'), ('page', 'Page'),
                        ('document_version', 'Version'), ('publication_date', 'Published'),
                        ('effective_date', 'Effective'), ('valid_until', 'Valid until'),
                        ('source_url', 'Source URL'), ('review_method', 'Review method'),
                        ('supporting_sections', 'Supporting sections'), ('supporting_pages', 'Supporting pages'),
                    ):
                        if detail.get(key) not in (None, ''):
                            st.caption(f"{label}: {detail[key]}")
                else:
                    # Source strings are labels, not trusted URLs or HTML.
                    st.text(f"{index:02d} · {source}")
        else:
            st.caption("No verified source supports a factual answer to this question.")
        if metadata.get("latency_ms") is not None:
            st.caption(f"Checked in {metadata['latency_ms'] / 1000:.2f} seconds")


def show_helpful_followups(metadata, message_index, *, latest=False):
    tip = metadata.get("helpful_tip")
    if isinstance(tip, str) and tip.strip():
        st.caption(f"Tip: {tip.strip()}")
    questions = metadata.get("suggested_questions")
    if latest and isinstance(questions, list):
        questions = [question.strip() for question in questions
                     if isinstance(question, str) and question.strip()][:2]
        for question_index, question in enumerate(questions):
            st.button(
                question, key=f"suggested_{message_index}_{question_index}",
                use_container_width=True, on_click=ask_question, args=(question,),
            )


def render_sidebar():
    with st.sidebar:
        with st.container(key="brand"):
            seal, identity = st.columns([1, 3], gap="small", vertical_alignment="center")
            with seal:
                st.image(str(LOGO_PATH), width=52)
            with identity:
                html(
                    '<div class="brand-name">TPC <span>NavBot</span></div>'
                    '<div class="brand-subtitle">YOUR CAMPUS COMPANION</div>'
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
        st.checkbox(
            "Show answer details", key="show_answer_details", value=False,
            help="Show source references, review details, and answer status.",
        )
        with st.container(key="sidebar_footer"):
            html(
                '<div class="language-card"><span class="language-heading">A language that feels like home.</span>'
                '<div class="language-tags"><span>English</span><span>Bisaya</span><span>Tagalog</span></div>'
                '<p>Just ask. NavBot follows your language.</p></div>'
            )
            with st.container(key="college_identity"):
                seal, identity = st.columns([1, 5], gap="small", vertical_alignment="center")
                with seal:
                    st.image(str(LOGO_PATH), width=36)
                with identity:
                    html(
                        '<div class="college-signature">Talibon Polytechnic College'
                        '<br><small>Built for our campus community</small></div>'
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
    else:
        st.caption(
            f"{len(verified_docs)} reviewed campus source records · "
            "Details without reviewed evidence remain unavailable. Check each answer’s sources."
        )


def campus_revision():
    """Refresh session-local retrieval when source files or their reviews change."""
    from src.config import RAW_DATA_DIR, SOURCE_REGISTRY_PATH

    files = [Path(SOURCE_REGISTRY_PATH), *sorted(Path(RAW_DATA_DIR).glob("*.txt"))]
    revision = []
    for path in files:
        try:
            details = path.stat()
            revision.append((str(path), details.st_mtime_ns, details.st_size))
        except OSError:
            revision.append((str(path), None, None))
    return tuple(revision)


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
        ("03", "Know what’s supported", "Replies show the answer. Turn on Show answer details to inspect sources and review status. Missing facts stay unconfirmed."),
    ]):
        with column:
            with st.container(border=True):
                html(f'<div class="about-step">{number}</div><h3>{title}</h3><p class="about-description">{description}</p>')
    with st.expander("What does an answer status mean?", expanded=True):
        for label, tone, symbol in STATUSES.values():
            html(f'<div class="status-explanation"><span class="answer-status {tone}">{symbol} {label}</span></div>')
        st.caption("Verified locations do not automatically verify routes, walking times, or accessibility details. These need their own reviewed evidence.")
    st.caption("Conversations are held in this browser session. New conversation clears the active chat and its follow-up context. Anonymous topic counts and optional feedback help identify information to improve; questions and personal details are not saved in these counts. New school facts require review before use.")


def render_chat(bot):
    if st.session_state.messages:
        html('<div class="chat-heading"><div class="eyebrow">YOUR CAMPUS CONVERSATION</div><h1>Let’s find your way.</h1><p>Keep asking. You can follow up in your own language.</p></div>')
    else:
        render_welcome()
    render_verification_notice(bot)
    latest_assistant = max((index for index, message in enumerate(st.session_state.messages)
                            if message["role"] == "assistant"), default=-1)
    with st.container(key="conversation"):
        for message_index, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"], avatar=":material/person:" if message["role"] == "user" else str(LOGO_PATH)):
                st.caption("You" if message["role"] == "user" else "TPC NavBot")
                st.markdown(message["content"])
                if message["role"] == "assistant" and message.get("metadata"):
                    show_helpful_followups(message["metadata"], message_index,
                                          latest=message_index == latest_assistant)
                    metadata = message["metadata"]
                    if metadata.get("feedback_id") and metadata.get("status") in {"SUCCESS", "PARTIAL", "UNVERIFIED"}:
                        st.feedback("thumbs", key="feedback_" + metadata["feedback_id"],
                                    disabled=metadata.get("feedback_recorded", False),
                                    on_change=record_answer_feedback, args=(message_index,))
                if message.get("metadata") and st.session_state.get("show_answer_details", False):
                    show_evidence(message["metadata"])

    prompt = st.chat_input("Ask about a classroom, office, or campus service…", key="campus_prompt", max_chars=MAX_QUERY_CHARS)
    prompt = st.session_state.pop("preset_query", None) or prompt
    if prompt and prompt.strip():
        prompt = prompt.strip()
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar=":material/person:"):
            st.caption("You")
            st.markdown(prompt)
        with st.chat_message("assistant", avatar=str(LOGO_PATH)):
            st.caption("TPC NavBot")
            started = time.perf_counter()
            with st.spinner("Checking campus information…"):
                try:
                    allowance = chat_request_limiter().allow(st.session_state.browser_rate_id)
                    if allowance.allowed:
                        response = bot.chat(prompt, session_id=st.session_state.session_id)
                    else:
                        language = bot.detect_language(prompt[:MAX_QUERY_CHARS])
                        wait = math.ceil(allowance.retry_after_seconds)
                        answer = {
                            "english": f"Please wait {wait} seconds before asking again. You can ask up to 12 questions per minute.",
                            "bisaya": f"Palihug hulat og {wait} ka segundo sa dili pa mangutana pag-usab. Hangtod 12 ka pangutana matag minuto.",
                            "tagalog": f"Maghintay po ng {wait} segundo bago magtanong muli. Hanggang 12 tanong bawat minuto.",
                        }[language]
                        response = {"status": "RATE_LIMITED", "language": language, "sources": [], "answer": answer}
                except Exception:
                    language = bot.detect_language(prompt[:MAX_QUERY_CHARS])
                    response = {"status": "ERROR", "language": language, "sources": [], "answer": MESSAGES[language]["error"]}
            metadata = {
                "status": response.get("status", "ERROR"), "language": response.get("language", "english"),
                "sources": response.get("sources", []), "latency_ms": round((time.perf_counter() - started) * 1000),
                "source_details": response.get("source_details", []),
                "helpful_tip": response.get("helpful_tip", ""),
                "suggested_questions": response.get("suggested_questions", []),
                "turn_count": response.get("turn_count", 1),
                "intent": bot._intent(prompt) if evaluate_query(prompt).allowed else None,
                "entity": bot._entity(prompt) if evaluate_query(prompt).allowed else None,
                "feedback_id": str(uuid4()),
            }
            st.markdown(response["answer"])
            if st.session_state.get("show_answer_details", False):
                show_evidence(metadata)
        st.session_state.messages.append({"role": "assistant", "content": response["answer"], "metadata": metadata})
        st.session_state.messages = st.session_state.messages[-200:]
        # Redraw removes the empty state and refreshes the sidebar transcript.
        st.rerun()
    html('<div class="composer-note">Up to 600 characters · 3 school questions per message · 12 messages per minute</div>')


def main():
    html(f'<style>{(PROJECT_ROOT / "assets" / "styles.css").read_text(encoding="utf-8")}</style>')
    for key, default in [("messages", []), ("session_id", str(uuid4())), ("browser_rate_id", str(uuid4())), ("view", "Assistant")]:
        if key not in st.session_state:
            st.session_state[key] = default
    render_sidebar()
    render_header()
    revision = campus_revision()
    if "rag_bot" in st.session_state and st.session_state.get("knowledge_revision") != revision:
        # Keep the visible transcript; start fresh backend context against the
        # current evidence rather than carrying an outdated retrieval snapshot.
        del st.session_state.rag_bot
    if "rag_bot" not in st.session_state:
        try:
            with st.spinner("Getting your campus companion ready…"):
                st.session_state.rag_bot = TPCNavBotRAG()
                st.session_state.rag_bot.learning_store = LearningStore()
                st.session_state.knowledge_revision = revision
        except Exception:
            logger.exception("Campus information initialization failed")
            try:
                error_log = PROJECT_ROOT / "data" / "logs" / "startup.log"
                error_log.parent.mkdir(parents=True, exist_ok=True)
                with error_log.open("a", encoding="utf-8") as output:
                    output.write(traceback.format_exc() + "\n")
            except OSError:
                # A diagnostic log must never prevent the recovery UI rendering.
                pass
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
