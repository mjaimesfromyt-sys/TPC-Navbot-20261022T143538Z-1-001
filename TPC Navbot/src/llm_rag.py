import os
import sys
import re
import math
from typing import Dict, List, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing import TextPreprocessor
from src.vector_store import VectorStore
from src.memory import ConversationMemoryManager, ConversationSession

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

NAVIGATION_METRICS = {
    "computer studies": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "ccis": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "bsis": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "bsais": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "comlab": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "criminology": {"time": "2.0 minutes (120 seconds)", "steps": "~190 steps", "distance": "150 meters"},
    "bscrim": {"time": "2.0 minutes (120 seconds)", "steps": "~190 steps", "distance": "150 meters"},
    "academic": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "mab": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "beced": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "polsci": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "baps": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "english": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "agriculture": {"time": "2.5 minutes (150 seconds)", "steps": "~230 steps", "distance": "180 meters"},
    "bsag": {"time": "2.5 minutes (150 seconds)", "steps": "~230 steps", "distance": "180 meters"},
    "administration": {"time": "30 seconds", "steps": "~50 steps", "distance": "40 meters"},
    "cashier": {"time": "30 seconds", "steps": "~50 steps", "distance": "40 meters"},
    "registrar": {"time": "30 seconds", "steps": "~50 steps", "distance": "40 meters"},
    "clinic": {"time": "45 seconds", "steps": "~65 steps", "distance": "50 meters"},
    "gymnasium": {"time": "2.1 minutes (125 seconds)", "steps": "~200 steps", "distance": "160 meters"},
    "library": {"time": "1.2 minutes (75 seconds)", "steps": "~120 steps", "distance": "95 meters"},
    "cafeteria": {"time": "1.1 minutes (65 seconds)", "steps": "~110 steps", "distance": "85 meters"},
    "canteen": {"time": "1.1 minutes (65 seconds)", "steps": "~110 steps", "distance": "85 meters"},
    "saso": {"time": "45 seconds", "steps": "~70 steps", "distance": "60 meters"},
    "student affairs": {"time": "45 seconds", "steps": "~70 steps", "distance": "60 meters"},
    "student center": {"time": "45 seconds", "steps": "~70 steps", "distance": "60 meters"},
    "guidance": {"time": "50 seconds", "steps": "~75 steps", "distance": "65 meters"},
    "security": {"time": "10 seconds", "steps": "~15 steps", "distance": "10 meters"},
    "gate 1": {"time": "10 seconds", "steps": "~15 steps", "distance": "10 meters"},
    "lost and found": {"time": "10 seconds", "steps": "~15 steps", "distance": "10 meters"},
    "ssg": {"time": "1.5 minutes (90 seconds)", "steps": "~140 steps", "distance": "110 meters"},
    "nstp": {"time": "1.8 minutes (110 seconds)", "steps": "~180 steps", "distance": "140 meters"},
    "rotc": {"time": "1.8 minutes (110 seconds)", "steps": "~180 steps", "distance": "140 meters"},
    "avr": {"time": "1.0 minute (60 seconds)", "steps": "~90 steps", "distance": "70 meters"},
    "chapel": {"time": "1.7 minutes (100 seconds)", "steps": "~170 steps", "distance": "130 meters"},
    "sports": {"time": "2.2 minutes (135 seconds)", "steps": "~220 steps", "distance": "170 meters"},
    "oval": {"time": "2.2 minutes (135 seconds)", "steps": "~220 steps", "distance": "170 meters"},
    "farm": {"time": "2.8 minutes (170 seconds)", "steps": "~280 steps", "distance": "220 meters"}
}

class TPCNavBotRAG:
    """
    Multilingual RAG Orchestrator for Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol.
    Supports Bisaya (Cebuano/Boholano), English, and Tagalog (Filipino).
    Integrates ChromaDB persistent vector retrieval, multi-turn conversational memory, and Google Gemini API.
    """
    def __init__(self, raw_data_dir: str = r"c:\Users\ranz\Desktop\TPC Navbot\data\raw"):
        self.processor = TextPreprocessor()
        self.vector_store = VectorStore()
        self.memory_manager = ConversationMemoryManager()
        self._initialize_knowledge_base(raw_data_dir)
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    def _initialize_knowledge_base(self, raw_data_dir: str):
        chunks = self.processor.process_directory(raw_data_dir)
        self.vector_store.add_chunks(chunks)

    def detect_language(self, query: str) -> str:
        q_lower = query.lower()
        bisaya_markers = [
            'asa', 'hain', 'dapit', 'unsa', 'unsay', 'kinsa', 'orasa', 'pila',
            'bayranan', 'bayaran', 'mukuha', 'akong', 'kato', 'didto', 'diin',
            'nawagtang', 'malipong', 'tambalanan', 'kaonan', 'sanina', 'dulaan',
            'tanom', 'tulunghaan', 'lawak', 'palihug', 'sulod', 'mosulod',
            'adto', 'moadto', 'padulong', 'pud', 'pod', 'kaha', 'unta', 'ug'
        ]
        tagalog_markers = [
            'saan', 'nasaan', 'ano', 'anong', 'sino', 'paano', 'magkano', 'bakit',
            'magbabayad', 'kumuha', 'makukuha', 'po', 'opo', 'meron', 'kailan',
            'aking', 'namin', 'silid', 'aklatan', 'paaralan', 'pumunta', 'papasok',
            'pwede', 'para sa', 'ng'
        ]
        bisaya_score = sum(1 for m in bisaya_markers if re.search(rf'\b{re.escape(m)}\b', q_lower))
        tagalog_score = sum(1 for m in tagalog_markers if re.search(rf'\b{re.escape(m)}\b', q_lower))

        if bisaya_score > tagalog_score and bisaya_score > 0:
            return "bisaya"
        elif tagalog_score > bisaya_score and tagalog_score > 0:
            return "tagalog"
        elif bisaya_score > 0 and bisaya_score == tagalog_score:
            if any(re.search(rf'\b{m}\b', q_lower) for m in ['po', 'opo', 'saan', 'nasaan', 'ano']):
                return "tagalog"
            return "bisaya"

        return "english"

    def get_off_topic_refusal(self, lang: str) -> str:
        if lang == "bisaya":
            return "Ako si TPC NavBot, usa ka AI assistant alang lamang sa Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol campus navigation, lokasyon sa mga lawak, opisina, ug serbisyo sa mga estudyante. Dili ako makatabang sa mga hilisgutan gawas sa atong campus."
        elif lang == "tagalog":
            return "Ako po si TPC NavBot, opisyal na AI assistant para lamang sa Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol campus navigation, lokasyon ng mga silid, opisina, at serbisyo sa mga estudyante. Hindi po ako makakatulong sa mga paksang labas sa ating campus."
        return "I am TPC NavBot, specialized exclusively in Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol campus navigation, room locations, office hours, and student services. I cannot assist with non-campus topics."

    def get_unverified_refusal(self, lang: str) -> str:
        if lang == "bisaya":
            return "Pasayloa, apan wala akoy nakitang opisyal nga impormasyon sa TPC kabahin niana sa akong knowledge base. Palihug bisitaha o pangutana sa Campus Security HQ sa Main Gate 1, San Isidro, Talibon, Bohol."
        elif lang == "tagalog":
            return "Paumanhin po, ngunit wala po akong nakitang opisyal na impormasyon sa TPC patungkol diyan sa aking knowledge base. Mangyaring magtanong po sa Campus Security HQ sa Main Gate 1 sa San Isidro, Talibon, Bohol."
        return "I am sorry, but I do not have verified TPC campus information regarding that query in my knowledge base. Please check with Campus Security HQ at Main Gate 1 in San Isidro, Talibon, Bohol."

    def is_in_scope(self, query: str) -> bool:
        campus_keywords = [
            # English
            'where', 'bldg', 'building', 'room', 'floor', 'office', 'dean', 'registrar', 
            'cashier', 'tuition', 'fee', 'library', 'clinic', 'gym', 'cafeteria', 'canteen', 
            'security', 'id', 'wifi', 'lms', 'portal', 'parking', 'dorm', 'lab', 'comlab', 'hours', 
            'tpc', 'faculty', 'admission', 'schedule', 'lost', 'permit', 'chapel',
            'cr', 'crs', 'restroom', 'comfort room', 'toilet', 'program', 'dept', 'department',
            'criminology', 'bscrim', 'engineering', 'business', 'nursing', 'science', 'arts', 'psychology',
            'auditorium', 'bookstore', 'finance', 'scholarship', 'guidance', 'nstp', 'alumni',
            'bsis', 'bsais', 'polsci', 'baps', 'political', 'agriculture', 'agri', 'english', 'education', 'beced', 'accountancy',
            'saso', 'ssg', 'rotc', 'cwts', 'handbook', 'dress code', 'grades', 'grading', 'exam', 'examination', 'helpdesk',
            # Bisaya / Cebuano
            'asa', 'hain', 'dapit', 'unsa', 'unsay', 'kinsa', 'orasa', 'pila',
            'magbayad', 'bayaran', 'bayranan', 'bayad', 'mukuha', 'kuha', 'palit', 'sakto',
            'sulod', 'mosulod', 'padulong', 'adto', 'moadto', 'mangutana',
            'opisina', 'lawak', 'eskwelahan', 'tulunghaan', 'tambalanan', 'tambal', 'malipong',
            'sakit', 'gwardya', 'bantay', 'nawala', 'nawagtang', 'sanina', 'uniporme', 'matrikula',
            'libro', 'kaonan', 'pagkaon', 'dulaan', 'pulis', 'tanom', 'uma', 'grado',
            # Tagalog / Filipino
            'saan', 'nasaan', 'ano', 'anong', 'sino', 'paano', 'magkano',
            'magbabayad', 'kumuha', 'makukuha', 'pumunta', 'papasok', 'nawalan',
            'magtanong', 'silid', 'paaralan', 'gamot', 'masakit', 'doktor', 'aklatan', 'kainan', 'suot'
        ]
        q_lower = query.lower()
        return any(k in q_lower for k in campus_keywords)

    def get_nav_metrics(self, query: str, building: str) -> dict:
        q_lower = (query + " " + building).lower()
        for key, metrics in NAVIGATION_METRICS.items():
            if key in q_lower:
                return metrics
        return {"time": "1.2 minutes (70 seconds)", "steps": "~110 steps", "distance": "85 meters"}

    def clean_line(self, line: str) -> str:
        return re.sub(r'^[*\-#=]+\s*', '', line).strip()

    def verify_grounding(self, user_query: str, hits: list) -> bool:
        if not hits:
            return False

        stop_words = {
            # English
            'where', 'is', 'the', 'are', 'located', 'location', 'can', 'i', 'find', 'how', 'to',
            'get', 'a', 'an', 'in', 'at', 'on', 'of', 'for', 'tpc', 'campus', 'building', 'bldg',
            'room', 'office', 'department', 'dept', 'details', 'tell', 'me', 'about', 'what', 'which',
            'show', 'please', 'know', 'way', 'route', 'go', 'near', 'by', 'there', 'any',
            # Bisaya
            'asa', 'hain', 'dapit', 'ang', 'sa', 'ug', 'og', 'ko', 'ako', 'akong', 'nga', 'ni',
            'ka', 'ba', 'naa', 'may', 'unsa', 'unsay', 'kinsa', 'orasa', 'palihug', 'para',
            'diri', 'didto', 'kato', 'niini', 'unta', 'gud', 'man', 'pod', 'pud', 'ra', 'kaha',
            # Tagalog
            'saan', 'nasaan', 'po', 'ng', 'mga', 'aking', 'ano', 'anong', 'sino', 'meron',
            'paki', 'dito', 'doon', 'dun', 'ito', 'iyon', 'naman', 'kaya'
        }

        raw_tokens = re.sub(r'[^a-z0-9\s]', ' ', user_query.lower()).split()
        key_tokens = [t for t in raw_tokens if len(t) > 1 and t not in stop_words]

        if not key_tokens:
            return hits[0]['score'] >= 0.45

        context_str = " ".join([
            f"{h['text']} {h['metadata'].get('building', '')} {h['metadata'].get('source_doc', '')}".lower()
            for h in hits[:3]
        ])

        synonyms = {
            'criminology': ['bscrim', 'criminology', 'crime', 'pulis'],
            'bscrim': ['bscrim', 'criminology', 'pulis'],
            'pulis': ['bscrim', 'criminology', 'crime'],
            'bsis': ['bsis', 'computer', 'comlab'],
            'bsais': ['bsais', 'accounting', 'accountancy'],
            'polsci': ['polsci', 'political', 'science'],
            'baps': ['baps', 'political'],
            'beced': ['beced', 'early', 'childhood', 'education'],
            'agri': ['agriculture', 'agri', 'bsag', 'uma', 'tanom'],
            'agriculture': ['agriculture', 'agri', 'bsag', 'uma', 'tanom'],
            'tanom': ['agriculture', 'agri', 'bsag', 'crop', 'demo'],
            'uma': ['agriculture', 'agri', 'bsag', 'farm'],
            'comlab': ['comlab', 'computer', 'lab'],
            'clinic': ['clinic', 'medical', 'nurse', 'doctor', 'health', 'tambal', 'tambalanan', 'malipong', 'sakit'],
            'tambal': ['clinic', 'medical', 'nurse', 'doctor', 'health', 'medicine'],
            'tambalanan': ['clinic', 'medical', 'nurse', 'doctor', 'health'],
            'sakit': ['clinic', 'medical', 'nurse', 'health', 'consultation'],
            'malipong': ['clinic', 'medical', 'nurse', 'health'],
            'gym': ['gym', 'gymnasium', 'sports', 'court', 'dulaan'],
            'cafeteria': ['cafeteria', 'canteen', 'food', 'dining', 'kaon', 'kaonan', 'kainan', 'pagkaon'],
            'canteen': ['canteen', 'cafeteria', 'food', 'dining', 'kaon', 'kaonan', 'kainan', 'pagkaon'],
            'kaonan': ['canteen', 'cafeteria', 'food', 'dining'],
            'kainan': ['canteen', 'cafeteria', 'food', 'dining'],
            'pagkaon': ['canteen', 'cafeteria', 'food', 'meal'],
            'library': ['library', 'books', 'reading', 'libro', 'basahan', 'aklatan'],
            'libro': ['library', 'books', 'reading', 'circulation'],
            'basahan': ['library', 'books', 'reading', 'study'],
            'aklatan': ['library', 'books', 'reading'],
            'cashier': ['cashier', 'finance', 'payment', 'tuition', 'fee', 'permit', 'bayad', 'bayranan', 'bayaran', 'matrikula', 'magbayad'],
            'pay': ['payment', 'cashier', 'finance', 'tuition', 'fee', 'bayad', 'bayaran', 'bayranan', 'magbayad'],
            'bayad': ['payment', 'cashier', 'finance', 'tuition', 'fee', 'permit'],
            'bayranan': ['payment', 'cashier', 'finance', 'tuition', 'fee', 'permit'],
            'bayaran': ['payment', 'cashier', 'finance', 'tuition', 'fee', 'permit'],
            'magbayad': ['payment', 'cashier', 'finance', 'tuition', 'fee', 'permit'],
            'matrikula': ['tuition', 'fee', 'payment', 'cashier', 'installment'],
            'tuition': ['tuition', 'fee', 'payment', 'cashier', 'installment', 'installments', 'bayad', 'matrikula'],
            'fee': ['fee', 'tuition', 'payment', 'cashier', 'bayad'],
            'permit': ['permit', 'permits', 'exam', 'examination', 'cashier'],
            'installments': ['installment', 'installments', 'tuition', 'payment', 'cashier'],
            'registrar': ['registrar', 'records', 'transcript', 'enrollment', 'grado', 'enrol'],
            'grado': ['grades', 'grading', 'transcript', 'registrar'],
            'enrol': ['enrollment', 'registrar', 'admissions'],
            'admin': ['administration', 'admin', 'office'],
            'opisina': ['office', 'department', 'building', 'bldg', 'dean', 'chair'],
            'security': ['security', 'gate', 'guard', 'lost', 'found', 'gwardya', 'bantay'],
            'gwardya': ['security', 'guard', 'gate', 'lost', 'found'],
            'bantay': ['security', 'guard', 'gate'],
            'lost': ['lost', 'found', 'security', 'guard', 'gate', 'nawala', 'nawagtang'],
            'nawala': ['lost', 'found', 'security', 'guard', 'id'],
            'nawagtang': ['lost', 'found', 'security', 'guard', 'id'],
            'saso': ['saso', 'student affairs', 'student services'],
            'guidance': ['guidance', 'counseling', 'psychological'],
            'ssg': ['ssg', 'student government'],
            'nstp': ['nstp', 'cwts', 'rotc'],
            'chapel': ['chapel', 'prayer', 'ecumenical'],
            'handbook': ['handbook', 'policies', 'rules', 'conduct', 'uniform', 'dress', 'sanina', 'uniporme'],
            'uniporme': ['uniform', 'dress', 'code', 'handbook', 'attire'],
            'sanina': ['uniform', 'dress', 'code', 'handbook', 'attire'],
            'suot': ['uniform', 'dress', 'code', 'handbook', 'attire'],
            'wifi': ['wifi', 'network', 'portal', 'lms', 'internet']
        }

        matched_count = 0
        for token in key_tokens:
            matched = token in context_str
            if not matched and token in synonyms:
                matched = any(syn in context_str for syn in synonyms[token])
            if matched:
                matched_count += 1

        if matched_count == 0:
            return False

        if hits[0]['score'] < 0.25 and matched_count < math.ceil(len(key_tokens) / 2):
            return False

        return True

    def _call_gemini_api(self, user_query: str, retrieved_context: str, building: str, nav: dict, sources: list, conversation_history: str = "") -> Optional[str]:
        api_key = self.api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            return None

        prompt = f"""You are TPC NavBot, the official multilingual AI campus navigation & student services assistant for Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol.

CONVERSATION HISTORY (Previous turns in this session):
{conversation_history}

CURRENT STUDENT QUESTION:
{user_query}

RETRIEVED GROUNDED CAMPUS CONTEXT:
{retrieved_context}

TARGET LOCATION & ROUTE METRICS (From TPC Main Gate 1, San Isidro, Talibon, Bohol):
- Building: {building}
- Walking Directions: Enter through TPC Main Gate 1, proceed along the main entrance walkway towards the central grounds, then follow signs for {building}.
- Estimated Walking Time: {nav['time']}
- Estimated Step Count: {nav['steps']} ({nav['distance']})

SOURCES:
{', '.join(sources)}

CRITICAL MULTILINGUAL INSTRUCTIONS:
1. Detect whether the student's question is in BISAYA (Cebuano/Boholano), TAGALOG (Filipino), or ENGLISH (or Taglish/Bislish).
2. You MUST respond in the EXACT SAME LANGUAGE as the student's query:
   - If asked in BISAYA (e.g., using "Asa dapit", "magbayad", "akong", "unsa orasa"): Respond in natural, warm, polite Bisaya/Cebuano.
   - If asked in TAGALOG (e.g., using "Saan po", "magkano", "nasaan"): Respond in natural, polite Tagalog with "po/opo".
   - If asked in ENGLISH: Respond in clear, friendly English.
3. Organize response cleanly using Markdown:
   - 📍 **LOCATION DETAILS** (Building name, room numbers, office hours, and specific services).
   - 🗺️ **NAVIGATION & ESTIMATED ROUTE** (Walking route from Main Gate 1 with estimated time, steps, and distance).
   - **Source Cited** (Exact citations).
4. Strictly ground answers in the retrieved campus context. Do not hallucinate.
"""
        # Google GenAI SDK (Client API)
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response and hasattr(response, 'text') and response.text:
                return response.text.strip()
        except Exception:
            pass

        # Legacy google.generativeai fallback
        try:
            import google.generativeai as ggenai
            ggenai.configure(api_key=api_key)
            model = ggenai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and hasattr(response, 'text') and response.text:
                return response.text.strip()
        except Exception:
            pass

        return None

    def chat(self, user_query: str, session_id: str = "default_user", top_k: int = 3, metric: str = "cosine") -> dict:
        """
        Multilingual multi-turn conversational interface.
        Tracks session history, resolves contextual co-references across languages,
        retrieves grounded context, and generates an LLM-synthesized response.
        """
        session = self.memory_manager.get_session(session_id)
        standalone_query = session.get_standalone_query(user_query)
        detected_lang = self.detect_language(user_query)

        # In-Scope Check
        if not self.is_in_scope(standalone_query):
            refusal = self.get_off_topic_refusal(detected_lang)
            session.add_user_message(user_query)
            session.add_ai_message(refusal)
            return {
                "status": "OFF_TOPIC",
                "answer": refusal,
                "sources": [],
                "session_id": session_id,
                "turn_count": len(session.history) // 2,
                "language": detected_lang
            }

        # Vector Retrieval from ChromaDB
        hits = self.vector_store.search(standalone_query, top_k=top_k * 2, metric=metric)
        # Prioritize specific building chunk over general FAQ if relevance is strong
        specific_hits = [h for h in hits if "faq" not in h['metadata']['source_doc'].lower()]
        if specific_hits and specific_hits[0]['score'] >= 0.30:
            hits = specific_hits

        # Grounding & Domain Verification
        if not hits or hits[0]['score'] < 0.15 or not self.verify_grounding(standalone_query, hits):
            unverified_refusal = self.get_unverified_refusal(detected_lang)
            session.add_user_message(user_query)
            session.add_ai_message(unverified_refusal)
            return {
                "status": "UNVERIFIED",
                "answer": unverified_refusal,
                "sources": [],
                "session_id": session_id,
                "turn_count": len(session.history) // 2,
                "language": detected_lang
            }

        top_hit = hits[0]
        building = top_hit['metadata']['building']
        nav = self.get_nav_metrics(standalone_query, building)

        lines = [self.clean_line(line) for line in top_hit['text'].split('\n') if line.strip() and not line.startswith('Context Source:') and not line.startswith('Location ID:') and not line.startswith('TALIBON')]
        bullet_points = "\n".join([f"- {line}" for line in lines[:6]])
        sources = list(set([f"{hit['metadata']['building']} [{hit['metadata']['source_doc']}]" for hit in hits[:2]]))

        context_block = "\n".join([h['text'] for h in hits[:3]])
        conv_history_str = session.get_formatted_history(max_turns=3)

        # Gemini API Generation with Multilingual Instructions
        gemini_answer = self._call_gemini_api(user_query, context_block, building, nav, sources, conv_history_str)

        if gemini_answer:
            final_answer = gemini_answer
        else:
            # Multilingual Fallback Formatting
            if detected_lang == "bisaya":
                final_answer = (
                    f"📍 **MGA DETALYE SA LOKASYON**:\n"
                    f"Gusali/Building: **{building}**\n"
                    f"Campus: **Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol**\n\n"
                    f"{bullet_points}\n\n"
                    f"🗺️ **DIREKSYON UG ESTIMATED ROUTE** (Gikan sa TPC Main Gate 1, San Isidro, Talibon, Bohol):\n"
                    f"- **Direksyon sa Paglakaw**: Pagsulod sa TPC Main Gate 1, lakaw subay sa main entrance agianan padulong sa sentro sa campus, dayon sunda ang mga karatula alang sa {building}.\n"
                    f"- ⏱️ **Gibanabanang Oras**: {nav['time']}\n"
                    f"- 👣 **Gibanabanang Lakang**: {nav['steps']} ({nav['distance']})\n\n"
                    f"**Source Cited**: {', '.join(sources)}"
                )
            elif detected_lang == "tagalog":
                final_answer = (
                    f"📍 **MGA DETALYE NG LOKASYON**:\n"
                    f"Gusali/Building: **{building}**\n"
                    f"Campus: **Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol**\n\n"
                    f"{bullet_points}\n\n"
                    f"🗺️ **DIREKSYON AT ESTIMATED ROUTE** (Mula sa TPC Main Gate 1, San Isidro, Talibon, Bohol):\n"
                    f"- **Direksyon sa Paglalakad**: Pumasok sa TPC Main Gate 1, maglakad sa main entrance walkway patungo sa gitna ng campus, at sundan ang mga karatula para sa {building}.\n"
                    f"- ⏱️ **Tinatayang Oras**: {nav['time']}\n"
                    f"- 👣 **Tinatayang Hakbang**: {nav['steps']} ({nav['distance']})\n\n"
                    f"**Source Cited**: {', '.join(sources)}"
                )
            else:
                final_answer = (
                    f"📍 **LOCATION DETAILS**:\n"
                    f"Building: **{building}**\n"
                    f"Campus: **Talibon Polytechnic College (TPC), San Isidro, Talibon, Bohol**\n\n"
                    f"{bullet_points}\n\n"
                    f"🗺️ **NAVIGATION & ESTIMATED ROUTE** (From TPC Main Gate 1, San Isidro, Talibon, Bohol):\n"
                    f"- **Walking Directions**: Enter through TPC Main Gate 1, proceed along the main entrance walkway towards the central grounds, then follow signs for {building}.\n"
                    f"- ⏱️ **Estimated Time**: {nav['time']}\n"
                    f"- 👣 **Estimated Steps**: {nav['steps']} ({nav['distance']})\n\n"
                    f"**Source Cited**: {', '.join(sources)}"
                )

        # Update Conversation Memory State
        session.add_user_message(user_query)
        session.add_ai_message(final_answer, building=building)

        return {
            "status": "SUCCESS",
            "answer": final_answer,
            "sources": sources,
            "retrieved_chunks": hits,
            "session_id": session_id,
            "turn_count": len(session.history) // 2,
            "language": detected_lang
        }

    def query(self, user_query: str, top_k: int = 3, metric: str = "cosine") -> dict:
        """
        Backwards-compatible single-turn query method.
        """
        return self.chat(user_query, session_id="single_turn_eval", top_k=top_k, metric=metric)

    def reset_conversation(self, session_id: str = "default_user"):
        self.memory_manager.reset_session(session_id)
