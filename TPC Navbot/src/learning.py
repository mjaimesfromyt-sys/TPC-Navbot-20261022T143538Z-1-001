"""Privacy-preserving question trends for a human-reviewed improvement loop.

This is aggregate product feedback, not model training or school evidence. Only
fixed categories reach SQLite: no questions, answers, claims, names, identifiers,
session IDs, or prompt text. Unrecognized category values become ``unknown``.
Administrators use the review queue to request school confirmation, then update
the normal provenance-reviewed source registry. Nothing here can publish facts.
"""
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3

from src.campus_entities import ENTITY_ALIASES
from src.config import project_path


INTENTS = frozenset({"location", "route", "hours", "contact", "services", "accessibility"})
ENTITIES = frozenset(ENTITY_ALIASES) | {"campus room"}
STATUSES = frozenset({
    "SUCCESS", "PARTIAL", "UNVERIFIED", "CLARIFICATION", "OFF_TOPIC", "BLOCKED",
    "RATE_LIMITED", "INVALID_INPUT", "ERROR",
})
LANGUAGES = frozenset({"english", "bisaya", "tagalog"})
FEEDBACK = frozenset({"helpful", "not_helpful"})
REVIEW_STATUSES = ("UNVERIFIED", "CLARIFICATION", "PARTIAL", "ERROR")
UNKNOWN = "unknown"
MAX_COUNT = 1_000_000_000
MAX_ROWS = 5_000


def _today():
    # Campus reporting uses Philippine dates; fixed UTC+8 requires no tzdata.
    return datetime.now(timezone(timedelta(hours=8))).date()


def _category(value, allowed, default=UNKNOWN):
    # No coercion or fuzzy matching: an identifier containing personal text or
    # an instruction must never enter either a row or an error message.
    return value if isinstance(value, str) and value in allowed else default


def _limit(value, maximum):
    return max(1, min(value, maximum)) if type(value) is int else min(20, maximum)


class LearningStore:
    """Durable, bounded daily counters, isolated from all retrieval sources.

    Writes are lazy and each operation owns its connection, so one instance can
    be used across Streamlit threads or processes. A short SQLite busy timeout
    bounds waiting. Unavailable/full/read-only storage returns False or [] and
    must never prevent a school answer. Retention defaults to 90 days, up to
    2,000 category combinations; counts saturate rather than overflow.
    """

    def __init__(self, path=None, *, retention_days=90, max_rows=2_000):
        self.path = Path(path) if path is not None else project_path(
            "TPC_LEARNING_PATH", "data/learning/question_metrics.sqlite3")
        self.retention_days = _limit(retention_days, 365)
        self.max_rows = _limit(max_rows, MAX_ROWS)

    def _connect(self, *, readonly=False):
        if readonly:
            return sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True, timeout=0.5)
        connection = sqlite3.connect(str(self.path), timeout=0.5)
        # Bound the database to roughly 4 MiB even if damaged or misconfigured.
        try:
            connection.execute("PRAGMA max_page_count = 1024")
        except sqlite3.Error:
            connection.close()
            raise
        return connection

    def _cutoff(self):
        return (_today() - timedelta(days=self.retention_days - 1)).isoformat()

    def observe(self, *, status, intent=None, entity=None, language="english", feedback=None):
        """Count category metadata, returning whether storage succeeded.

        Call once for an answer, and optionally once for explicit feedback.
        These are observations, not unique people or an accuracy measurement.
        Callers must rate-limit feedback and must not pass raw question text.
        """
        values = (
            _today().isoformat(), _category(intent, INTENTS),
            _category(entity, ENTITIES), _category(status, STATUSES),
            _category(language, LANGUAGES), _category(feedback, FEEDBACK, "none"),
        )
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(self._connect()) as connection:
                with connection:
                    connection.execute("BEGIN IMMEDIATE")
                    connection.execute("""
                        CREATE TABLE IF NOT EXISTS observations (
                            day TEXT NOT NULL, intent TEXT NOT NULL,
                            entity TEXT NOT NULL, status TEXT NOT NULL,
                            language TEXT NOT NULL, feedback TEXT NOT NULL,
                            count INTEGER NOT NULL CHECK(count BETWEEN 1 AND 1000000000),
                            PRIMARY KEY(day, intent, entity, status, language, feedback)
                        ) WITHOUT ROWID
                    """)
                    connection.execute("DELETE FROM observations WHERE day < ?", (self._cutoff(),))
                    connection.execute("""
                        INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, 1)
                        ON CONFLICT(day, intent, entity, status, language, feedback)
                        DO UPDATE SET count = MIN(observations.count + 1, ?)
                    """, values + (MAX_COUNT,))
                    # Keep recent, repeated categories when the cap is reached.
                    connection.execute("""
                        DELETE FROM observations WHERE
                            (day, intent, entity, status, language, feedback) IN (
                                SELECT day, intent, entity, status, language, feedback
                                FROM observations
                                ORDER BY day DESC, count DESC, entity, intent, status, language, feedback
                                LIMIT -1 OFFSET ?
                            )
                    """, (self.max_rows,))
            return True
        except (OSError, sqlite3.Error):
            # Metrics are optional, and errors must not echo input or paths.
            return False

    def summary(self, *, limit=20, gaps_only=False, entity=None):
        """Return bounded aggregate trends for authorized administrative review.

        Counts indicate demand and unresolved requests, never factual accuracy.
        A malicious user can increase counters but cannot add evidence or text.
        The application must not expose this report as a public chat command.
        """
        conditions, parameters = ["day >= ?"], [self._cutoff()]
        if gaps_only:
            conditions.append("(status IN (?, ?, ?, ?) OR feedback = 'not_helpful')")
            parameters.extend(REVIEW_STATUSES)
        if entity is not None:
            if not isinstance(entity, str) or entity not in ENTITIES:
                return []
            conditions.append("entity = ?")
            parameters.append(entity)
        parameters.append(_limit(limit, self.max_rows))
        try:
            with closing(self._connect(readonly=True)) as connection:
                rows = connection.execute("""
                    SELECT entity, intent, status, language, feedback, SUM(count), MIN(day), MAX(day)
                    FROM observations WHERE """ + " AND ".join(conditions) + """
                    GROUP BY entity, intent, status, language, feedback
                    ORDER BY SUM(count) DESC, MAX(day) DESC, entity, intent, status, language, feedback
                    LIMIT ?
                """, parameters).fetchall()
        except (OSError, sqlite3.Error):
            return []
        return [{
            "entity": row[0], "intent": row[1], "status": row[2], "language": row[3],
            "feedback": row[4], "observations": row[5], "first_day": row[6],
            "last_day": row[7],
            "review_required": row[2] in REVIEW_STATUSES or row[4] == "not_helpful",
        } for row in rows]

    def popular_intents(self, entity, *, limit=3, exclude=()):
        """Rank observed interests; callers must intersect verified answer fields.

        Frequency cannot prove that a fact exists or that an answer is correct.
        Exclude feedback observations so clicking feedback cannot boost a topic.
        """
        if not isinstance(entity, str) or entity not in ENTITIES:
            return []
        excluded = {item for item in exclude if isinstance(item, str) and item in INTENTS}
        try:
            with closing(self._connect(readonly=True)) as connection:
                rows = connection.execute("""
                    SELECT intent, SUM(count) FROM observations
                    WHERE day >= ? AND entity = ? AND status IN ('SUCCESS', 'PARTIAL')
                        AND feedback = 'none'
                    GROUP BY intent ORDER BY SUM(count) DESC, intent
                """, (self._cutoff(), entity)).fetchall()
        except (OSError, sqlite3.Error):
            return []
        return [intent for intent, _ in rows if intent in INTENTS and intent not in excluded][:_limit(limit, 6)]
