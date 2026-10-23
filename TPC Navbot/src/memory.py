"""Memory that resolves an allowlist of campus follow-ups, never arbitrary pronouns.

History is a transcript, not evidence or an instruction source. The orchestrator
commits destination context explicitly after checking each new turn.
"""
import re
import time
from typing import Dict, List, Optional


class ConversationSession:
    FOLLOWUPS = (
        r"(?:and\s+)?(?:what services (?:are there|are available|does it offer)|what (?:are|is) (?:its|the) requirements|what about (?:its|the) (?:hours|services|contact))",
        r"(?:and\s+)?(?:what (?:are|is) (?:its|the) (?:operating |opening )?hours|(?:its )?(?:operating |opening )?hours|when (?:does it open|is it open))",
        r"(?:and\s+)?(?:what (?:are|is) (?:its|the) (?:services|contact (?:number|details))|how (?:do i|can i) (?:get|go) there|how long (?:does it take|is the walk)(?: to (?:walk|get) there)?|is it (?:wheelchair )?accessible|is there (?:a ramp|an elevator))",
        r"(?:ug\s+)?(?:unsa(?:y| ang)? (?:iyang |ang )?(?:oras|orasa|serbisyo)|unsang orasa (?:abli|moabli)(?: didto)?|kanus a (?:abli|moabli)|unsaon (?:pag adto|pagadto)(?: didto)?|pila ka minuto(?: ang lakaw)?(?: padulong didto)?|naa bay (?:rampa|elevator)(?: didto)?)",
        r"(?:at\s+)?(?:ano(?: po)? (?:ang )?(?:oras|serbisyo)(?: nito|niya)?|anong oras (?:ito )?(?:bukas|nagbubukas)|kailan (?:ito )?bukas|paano(?: po)? (?:pumunta|makapunta)(?: doon)?|gaano katagal(?: ang lakad)?(?: papunta doon)?|may (?:rampa|elevator) ba(?: doon)?)",
    )

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict] = []
        self.last_entity: Optional[str] = None
        self.last_building: Optional[str] = None
        self.starting_point: Optional[str] = None
        self.language: Optional[str] = None
        self.pending_buildings: List[str] = []
        self.pending_starts: List[str] = []
        self.created_at = time.time()
        self.updated_at = self.created_at

    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message, "timestamp": time.time()})
        self.updated_at = time.time()

    def add_ai_message(self, message: str, building: Optional[str] = None):
        self.history.append({"role": "assistant", "content": message, "timestamp": time.time()})
        # Retain at most forty turns; history is never training material.
        self.history = self.history[-80:]
        if building:
            self.last_building = building
        self.updated_at = time.time()

    def set_context(self, entity: str, building=None, starting_point=None, language=None):
        self.last_entity = entity
        self.last_building = building
        if starting_point:
            self.starting_point = starting_point
        if language:
            self.language = language

    def clear_context(self):
        self.last_entity = None
        self.last_building = None
        self.starting_point = None
        self.pending_buildings = []
        self.pending_starts = []

    @classmethod
    def is_campus_followup(cls, query: str) -> bool:
        normalized = re.sub(r"[^\w\s]", " ", query.casefold())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return any(re.fullmatch(pattern, normalized) for pattern in cls.FOLLOWUPS)

    def get_standalone_query(self, current_query: str) -> str:
        if self.last_entity and self.is_campus_followup(current_query):
            return f"{current_query} [TPC destination: {self.last_entity}]"
        return current_query

    def get_formatted_history(self, max_turns: int = 5) -> str:
        recent = self.history[-(max_turns * 2):]
        return "\n".join(
            f"{'Student' if msg['role'] == 'user' else 'TPC NavBot'}: {msg['content']}"
            for msg in recent
        ) or "No previous conversation history."

    def clear(self):
        self.history.clear()
        self.clear_context()
        self.language = None
        self.updated_at = time.time()


class ConversationMemoryManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}

    def get_session(self, session_id: str = "default_user") -> ConversationSession:
        if session_id not in self.sessions:
            if len(self.sessions) >= 128:
                oldest = min(self.sessions, key=lambda key: self.sessions[key].updated_at)
                del self.sessions[oldest]
            self.sessions[session_id] = ConversationSession(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str = "default_user"):
        if session_id in self.sessions:
            self.sessions[session_id].clear()
