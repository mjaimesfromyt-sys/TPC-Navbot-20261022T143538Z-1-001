"""Deterministic sliding-window, isolation and bounded-state rate limit tests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.request_limits import QueryRateLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class QueryRateLimiterTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.limiter = QueryRateLimiter(clock=self.clock)

    def test_default_per_session_limit_resets_at_exact_boundary(self):
        self.assertTrue(all(self.limiter.allow("browser-a").allowed for _ in range(12)))
        result = self.limiter.allow("browser-a")
        self.assertFalse(result.allowed)
        self.assertEqual(result.retry_after_seconds, 60)
        self.clock.now += 59.5
        self.assertEqual(self.limiter.allow("browser-a").retry_after_seconds, .5)
        self.clock.now += .5
        self.assertTrue(self.limiter.allow("browser-a").allowed)

    def test_global_limit_caps_new_session_ids(self):
        for number in range(120):
            self.assertTrue(self.limiter.allow(f"browser-{number}").allowed)
        result = self.limiter.allow("brand-new-id")
        self.assertFalse(result.allowed)
        self.assertEqual(result.retry_after_seconds, 60)
        self.assertNotIn("brand-new-id", self.limiter._sessions)
        self.clock.now += 60
        self.assertTrue(self.limiter.allow("brand-new-id").allowed)

    def test_one_students_quota_does_not_exhaust_another(self):
        for _ in range(12):
            self.limiter.allow("a")
        self.assertFalse(self.limiter.allow("a").allowed)
        self.assertTrue(self.limiter.allow("b").allowed)

    def test_denied_requests_do_not_extend_lockout(self):
        limiter = QueryRateLimiter(session_limit=1, clock=self.clock)
        self.assertTrue(limiter.allow("a").allowed)
        for _ in range(59):
            self.clock.now += 1
            self.assertFalse(limiter.allow("a").allowed)
        self.clock.now += 1
        self.assertTrue(limiter.allow("a").allowed)

    def test_window_is_sliding_rather_than_fixed(self):
        limiter = QueryRateLimiter(session_limit=2, clock=self.clock)
        self.assertTrue(limiter.allow("a").allowed)
        self.clock.now += 30
        self.assertTrue(limiter.allow("a").allowed)
        self.clock.now += 30
        self.assertTrue(limiter.allow("a").allowed)
        self.assertFalse(limiter.allow("a").allowed)
        self.assertEqual(limiter.allow("a").retry_after_seconds, 30)

    def test_retry_after_accounts_for_both_exhausted_limits(self):
        limiter = QueryRateLimiter(session_limit=1, global_limit=2, clock=self.clock)
        limiter.allow("a")
        self.clock.now += 30
        limiter.allow("b")
        self.assertEqual(limiter.allow("b").retry_after_seconds, 60)

    def test_buckets_are_bounded_without_evicting_active_sessions(self):
        limiter = QueryRateLimiter(max_sessions=2, clock=self.clock)
        limiter.allow("a")
        self.clock.now += 5
        limiter.allow("b")
        self.assertFalse(limiter.allow("c").allowed)
        self.assertEqual(set(limiter._sessions), {"a", "b"})
        self.clock.now += 55
        self.assertTrue(limiter.allow("c").allowed)
        self.assertEqual(set(limiter._sessions), {"b", "c"})

    def test_idle_session_buckets_expire(self):
        self.limiter.allow("a")
        self.clock.now += 601
        self.limiter.allow("b")
        self.assertEqual(set(self.limiter._sessions), {"b"})

    def test_concurrent_requests_cannot_overspend_session_quota(self):
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: self.limiter.allow("shared"), range(100)))
        self.assertEqual(sum(result.allowed for result in results), 12)
        self.assertEqual(len(self.limiter._global), 12)

    def test_concurrent_requests_cannot_overspend_global_quota(self):
        limiter = QueryRateLimiter(global_limit=30, clock=self.clock)
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda i: limiter.allow(str(i)), range(100)))
        self.assertEqual(sum(result.allowed for result in results), 30)

    def test_clock_regression_cannot_clear_recent_limits(self):
        limiter = QueryRateLimiter(session_limit=1, clock=self.clock)
        limiter.allow("a")
        self.clock.now -= 500
        result = limiter.allow("a")
        self.assertFalse(result.allowed)
        self.assertEqual(result.retry_after_seconds, 60)

    def test_invalid_ids_config_and_clock_values_are_rejected(self):
        for identity in (None, "", 1, "a" * 129):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                self.limiter.allow(identity)
        for kwargs in ({"session_limit": 0}, {"global_limit": -1}, {"max_sessions": 0},
                       {"window_seconds": 0}, {"session_ttl_seconds": 10},
                       {"window_seconds": float("nan")}, {"global_limit": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                QueryRateLimiter(**kwargs)
        with self.assertRaises(ValueError):
            QueryRateLimiter(clock=lambda: float("inf")).allow("a")


if __name__ == "__main__":
    unittest.main()
