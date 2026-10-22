import time
import re
from typing import List, Dict, Optional

class ConversationSession:
    """
    Maintains the state and turn history for a single chat session.
    Supports English, Bisaya (Cebuano/Boholano), and Tagalog (Filipino).
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[Dict[str, str]] = []
        self.last_entity: Optional[str] = None
        self.last_building: Optional[str] = None
        self.created_at = time.time()
        self.updated_at = time.time()

    def add_user_message(self, message: str):
        self.history.append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        self.updated_at = time.time()
        self._extract_entities(message)

    def add_ai_message(self, message: str, building: Optional[str] = None):
        self.history.append({
            "role": "assistant",
            "content": message,
            "timestamp": time.time()
        })
        if building:
            self.last_building = building
        self.updated_at = time.time()

    def _extract_entities(self, query: str):
        q_lower = query.lower()
        entity_keywords = {
            "bsis": "BSIS Department Office",
            "bsais": "BSAIS Department Office",
            "criminology": "Criminology Building",
            "bscrim": "Criminology Department Office",
            "pulis": "Criminology Department Office",
            "agriculture": "Agriculture Complex",
            "bsag": "Agriculture Department Office",
            "registrar": "Office of the College Registrar",
            "enrol": "Office of the College Registrar",
            "cashier": "Cashier & Finance Office",
            "tuition": "Cashier & Finance Office",
            "bayad": "Cashier & Finance Office",
            "bayranan": "Cashier & Finance Office",
            "matrikula": "Cashier & Finance Office",
            "clinic": "Health & Medical Clinic",
            "tambal": "Health & Medical Clinic",
            "tambalanan": "Health & Medical Clinic",
            "malipong": "Health & Medical Clinic",
            "library": "College Library",
            "libro": "College Library",
            "basahan": "College Library",
            "aklatan": "College Library",
            "gym": "Gymnasium & Cultural Center",
            "canteen": "Campus Canteen",
            "kaonan": "Campus Canteen",
            "kainan": "Campus Canteen",
            "saso": "Student Affairs & Services Office",
            "guidance": "Guidance & Counseling Center",
            "security": "Campus Security & Lost and Found",
            "gwardya": "Campus Security & Lost and Found",
            "nawala": "Campus Security & Lost and Found",
            "nawagtang": "Campus Security & Lost and Found",
            "ssg": "Supreme Student Government",
            "nstp": "NSTP & ROTC Office",
            "chapel": "Campus Ecumenical Chapel"
        }
        for kw, entity in entity_keywords.items():
            if kw in q_lower:
                self.last_entity = entity
                break

    def get_standalone_query(self, current_query: str) -> str:
        """
        Resolves co-references and pronouns in English, Bisaya, and Tagalog
        ('it', 'its', 'there', 'that office', 'kato', 'niya', 'doon', 'dun', 'yun')
        based on the preceding conversation turns.
        """
        if not self.history:
            self._extract_entities(current_query)
            return current_query

        q_lower = current_query.lower()

        # Check if the current query specifies a new concrete entity
        entity_keywords = [
            "bsis", "bsais", "criminology", "bscrim", "pulis", "agriculture", "bsag",
            "registrar", "enrol", "cashier", "tuition", "bayad", "bayranan", "matrikula",
            "clinic", "tambal", "tambalanan", "malipong", "library", "libro", "basahan",
            "aklatan", "gym", "canteen", "kaonan", "kainan", "saso", "guidance",
            "security", "gwardya", "nawala", "nawagtang", "ssg", "nstp", "chapel"
        ]
        has_explicit_new_entity = any(kw in q_lower for kw in entity_keywords)
        if has_explicit_new_entity:
            self._extract_entities(current_query)
            return current_query

        pronoun_patterns = [
            r'\b(it|its|there|that place|that building|that office|that room|the office)\b',
            r'\b(kato|adto|niya|niana|didto|dira|ana)\b',
            r'\b(doon|dun|iyon|yun|niyon|diyan|dito|iyon po|yun po)\b'
        ]
        has_pronoun = any(re.search(p, q_lower) for p in pronoun_patterns)

        # Detect short follow-up in English, Bisaya, or Tagalog
        short_followup_triggers = [
            "hours", "operating hours", "who is", "dean", "open", "schedule", "contact", "head", "chair",
            "oras", "orasa", "abli", "bukas", "kinsa", "sino", "paano", "unsa", "ano"
        ]
        is_short_followup = any(t in q_lower for t in short_followup_triggers) and len(current_query.split()) <= 8

        if (has_pronoun or is_short_followup) and (self.last_entity or self.last_building):
            entity_ref = self.last_entity or self.last_building
            return f"{current_query} regarding {entity_ref}"

        return current_query

    def get_formatted_history(self, max_turns: int = 5) -> str:
        recent = self.history[-(max_turns * 2):]
        if not recent:
            return "No previous conversation history."

        formatted_lines = []
        for msg in recent:
            role = "Student" if msg["role"] == "user" else "TPC NavBot"
            formatted_lines.append(f"{role}: {msg['content']}")
        return "\n".join(formatted_lines)

    def clear(self):
        self.history.clear()
        self.last_entity = None
        self.last_building = None
        self.updated_at = time.time()


class ConversationMemoryManager:
    """
    Manages active chat sessions across multiple users or interfaces.
    """
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}

    def get_session(self, session_id: str = "default_user") -> ConversationSession:
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationSession(session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str = "default_user"):
        if session_id in self.sessions:
            self.sessions[session_id].clear()
