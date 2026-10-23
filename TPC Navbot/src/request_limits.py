"""Process-shared, bounded sliding-window limits for the public chat UI."""
from collections import deque
from dataclasses import dataclass
import math
import threading
import time


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: float = 0.0


class QueryRateLimiter:
    """Limit a browser session and the whole application without storing text.

    Cache one instance for all Streamlit sessions. Browser IDs are advisory; the
    global bucket also bounds requests when clients rotate their session IDs.
    This is process-local: multiple workers require a shared gateway or store.
    """

    def __init__(self, *, session_limit=12, global_limit=120, window_seconds=60,
                 session_ttl_seconds=600, max_sessions=2048, clock=time.monotonic):
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 1
               for value in (session_limit, global_limit, max_sessions)):
            raise ValueError("Request counts must be positive integers")
        if (not math.isfinite(window_seconds) or window_seconds <= 0
                or not math.isfinite(session_ttl_seconds) or session_ttl_seconds < window_seconds):
            raise ValueError("TTL must be finite and at least one positive window")
        self.session_limit = session_limit
        self.global_limit = global_limit
        self.window_seconds = float(window_seconds)
        self.session_ttl_seconds = float(session_ttl_seconds)
        self.max_sessions = max_sessions
        self._clock = clock
        self._global = deque()
        self._sessions = {}
        self._last_seen = {}
        self._lock = threading.Lock()
        self._last_time = float("-inf")

    def allow(self, session_id):
        """Consume one request if both limits permit; denials consume no quota."""
        if not isinstance(session_id, str) or not session_id or len(session_id) > 128:
            raise ValueError("A nonempty session ID of at most 128 characters is required")
        with self._lock:
            now = float(self._clock())
            if not math.isfinite(now):
                raise ValueError("Clock must return a finite number")
            now = max(now, self._last_time)
            self._last_time = now
            cutoff = now - self.window_seconds
            while self._global and self._global[0] <= cutoff:
                self._global.popleft()
            for key in list(self._sessions):
                bucket = self._sessions[key]
                while bucket and bucket[0] <= cutoff:
                    bucket.popleft()
                if not bucket and now - self._last_seen[key] >= self.session_ttl_seconds:
                    del self._sessions[key]
                    del self._last_seen[key]
            bucket = self._sessions.get(session_id)
            waits = []
            if len(self._global) >= self.global_limit:
                waits.append(self._global[0] + self.window_seconds - now)
            if bucket is not None and len(bucket) >= self.session_limit:
                waits.append(bucket[0] + self.window_seconds - now)
            if waits:
                return RateLimitDecision(False, max(waits))
            if bucket is None:
                if len(self._sessions) >= self.max_sessions:
                    empty = [key for key, value in self._sessions.items() if not value]
                    if empty:
                        oldest = min(empty, key=self._last_seen.get)
                        del self._sessions[oldest]
                        del self._last_seen[oldest]
                    else:
                        # Never evict an active bucket: rotating IDs must not
                        # clear another client's currently enforced quota.
                        retry = min(value[-1] + self.window_seconds - now for value in self._sessions.values())
                        return RateLimitDecision(False, max(0.0, retry))
                bucket = deque()
                self._sessions[session_id] = bucket
            bucket.append(now)
            self._last_seen[session_id] = now
            self._global.append(now)
            return RateLimitDecision(True)
