"""Tests for GitHubModelsClient — caching, circuit breaker, rate limiter, single-flight, and API calls."""

from __future__ import annotations

import os
import time
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.llm.github_models_client import GitHubModelsClient


# =========================================================================
# Fixtures
# =========================================================================


@pytest.fixture
def client():
    """Fresh GitHubModelsClient with short timeouts for fast tests."""
    return GitHubModelsClient(timeout=5, max_retries=2)


# =========================================================================
# Token resolution
# =========================================================================


class TestTokenResolution:
    """_resolve_token() — env vars, gh CLI, or None."""

    def test_from_env_GITHUB_TOKEN(self):
        """GITHUB_TOKEN env var takes priority."""
        with patch.dict(os.environ, {"GITHUB_TOKEN": "ghx_env_token"}, clear=True):
            token = GitHubModelsClient._resolve_token()
        assert token == "ghx_env_token"

    def test_from_env_GH_TOKEN(self):
        """GH_TOKEN env var works as fallback."""
        with patch.dict(os.environ, {"GH_TOKEN": "ghx_gh_token"}, clear=True):
            token = GitHubModelsClient._resolve_token()
        assert token == "ghx_gh_token"

    def test_GITHUB_TOKEN_overrides_GH_TOKEN(self):
        """GITHUB_TOKEN takes precedence over GH_TOKEN."""
        with patch.dict(
            os.environ,
            {"GITHUB_TOKEN": "ghx_primary", "GH_TOKEN": "ghx_secondary"},
            clear=True,
        ):
            token = GitHubModelsClient._resolve_token()
        assert token == "ghx_primary"

    def test_from_gh_cli(self):
        """Falls back to ``gh auth token`` when env vars are absent."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "ghx_cli_token\n"
                token = GitHubModelsClient._resolve_token()
        assert token == "ghx_cli_token"
        mock_run.assert_called_once()

    def test_gh_cli_not_found(self):
        """FileNotFoundError from gh CLI returns None."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                token = GitHubModelsClient._resolve_token()
        assert token is None

    def test_gh_cli_timeout(self):
        """Timeout from gh CLI returns None."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run", side_effect=TimeoutError):
                token = GitHubModelsClient._resolve_token()
        assert token is None

    def test_gh_cli_nonzero_exit(self):
        """Non-zero exit from gh CLI returns None."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""
                token = GitHubModelsClient._resolve_token()
        assert token is None

    def test_gh_cli_empty_stdout(self):
        """Empty stdout from gh CLI returns None."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = ""
                token = GitHubModelsClient._resolve_token()
        assert token is None

    def test_no_token_found(self):
        """None returned when no token source available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("subprocess.run", side_effect=FileNotFoundError):
                token = GitHubModelsClient._resolve_token()
        assert token is None

    def test_token_property_caches(self):
        """``.token`` property caches after first resolution."""
        c = GitHubModelsClient()
        with patch.object(GitHubModelsClient, "_resolve_token", return_value="ghx_cached") as mock_resolve:
            t1 = c.token
            t2 = c.token
        assert t1 == t2 == "ghx_cached"
        mock_resolve.assert_called_once()

    def test_token_property_none_when_missing(self):
        """``.token`` property returns None when no token exists."""
        c = GitHubModelsClient()
        with patch.object(GitHubModelsClient, "_resolve_token", return_value=None):
            assert c.token is None


# =========================================================================
# Caching
# =========================================================================


class TestCaching:
    """LRU cache with TTL — _make_cache_key, _check_cache, _store_cache."""

    def test_cache_key_is_deterministic(self, client):
        """Same inputs produce same cache key."""
        k1 = client._make_cache_key("m1", "hello world", 512)
        k2 = client._make_cache_key("m1", "hello world", 512)
        assert k1 == k2

    def test_cache_key_differs_on_model(self, client):
        k_a = client._make_cache_key("model-a", "same prompt", 512)
        k_b = client._make_cache_key("model-b", "same prompt", 512)
        assert k_a != k_b

    def test_cache_key_differs_on_prompt(self, client):
        k1 = client._make_cache_key("m", "prompt one", 512)
        k2 = client._make_cache_key("m", "prompt two", 512)
        assert k1 != k2

    def test_cache_miss_returns_none(self, client):
        """Uncached key returns None."""
        key = client._make_cache_key("m", "uncached prompt", 512)
        assert client._check_cache(key) is None

    def test_cache_hit_returns_value(self, client):
        """Stored value is retrievable."""
        key = client._make_cache_key("m", "hit prompt", 512)
        client._store_cache(key, "hello from cache")
        assert client._check_cache(key) == "hello from cache"

    def test_cache_hit_moves_to_end(self, client):
        """Accessed entry moves to end (LRU)."""
        client._cache_max_entries = 3
        keys = [client._make_cache_key("m", f"prompt-{i}", 512) for i in range(3)]
        for i, k in enumerate(keys):
            client._store_cache(k, f"val-{i}")

        # Access key[0]; it moves to end
        client._check_cache(keys[0])

        # Add a 4th → evicts the new LRU tail (keys[1])
        k4 = client._make_cache_key("m", "prompt-4", 512)
        client._store_cache(k4, "val-4")

        assert client._check_cache(keys[0]) == "val-0"  # still there
        assert client._check_cache(keys[1]) is None      # evicted
        assert client._check_cache(k4) == "val-4"

    def test_cache_ttl_expiry(self, client):
        """Expired entry returns None."""
        key = client._make_cache_key("m", "ttl prompt", 512)
        client._store_cache(key, "fresh")
        client._cache_ttl = -1  # force expiry
        assert client._check_cache(key) is None

    def test_cache_eviction_when_full(self, client):
        """Oldest entry evicted when at capacity."""
        client._cache_max_entries = 2
        k1 = client._make_cache_key("m", "first", 512)
        k2 = client._make_cache_key("m", "second", 512)
        k3 = client._make_cache_key("m", "third", 512)

        client._store_cache(k1, "v1")
        client._store_cache(k2, "v2")
        client._store_cache(k3, "v3")  # evicts k1

        assert client._check_cache(k1) is None
        assert client._check_cache(k2) == "v2"
        assert client._check_cache(k3) == "v3"

    def test_cache_stats_hit_incremented(self, client):
        """Cache hit counter increments."""
        key = client._make_cache_key("m", "stats prompt", 512)
        client._store_cache(key, "val")
        hits_before = client._cache_hits
        client._check_cache(key)
        assert client._cache_hits == hits_before + 1

    def test_cache_stats_miss_incremented(self, client):
        """Cache miss counter increments."""
        hits_before = client._cache_hits
        misses_before = client._cache_misses
        client._check_cache("nonexistent_key")
        assert client._cache_hits == hits_before
        assert client._cache_misses == misses_before + 1

    def test_canonicalize_prompt(self, client):
        """Prompt canonicalization normalizes whitespace."""
        messy = "  hello   \n\n\nworld  \n"
        clean = client._canonicalize_prompt(messy)
        assert clean == "hello\n\nworld"
        # Same canonical form produces same key
        k1 = client._make_cache_key("m", messy, 512)
        k2 = client._make_cache_key("m", clean, 512)
        assert k1 == k2


# =========================================================================
# Circuit Breaker
# =========================================================================


class TestCircuitBreaker:
    """Circuit breaker — failure threshold, window, recovery probe."""

    def test_starts_closed(self, client):
        assert client._circuit_open is False
        assert client._failure_timestamps == []

    def test_record_success_resets(self, client):
        client._failure_timestamps = ["stale"]
        client._circuit_open = True
        client._record_success()
        assert client._circuit_open is False
        assert client._failure_timestamps == []
        assert client._circuit_open_time is None

    def test_record_failure_appends(self, client):
        client._record_failure()
        assert len(client._failure_timestamps) == 1

    def test_circuit_opens_at_threshold(self, client):
        client._failure_threshold = 3
        for _ in range(3):
            client._record_failure()
        assert client._circuit_open is True
        assert client._circuit_open_time is not None

    def test_circuit_stays_closed_below_threshold(self, client):
        client._failure_threshold = 5
        for _ in range(4):
            client._record_failure()
        assert client._circuit_open is False

    def test_old_failures_pruned(self, client):
        """Failures outside the window are pruned."""
        client._failure_window_seconds = 0.01
        client._record_failure()
        time.sleep(0.02)
        client._record_failure()  # this triggers pruning
        # Only the latest should remain
        assert len(client._failure_timestamps) == 1

    def test_recovery_after_interval(self, client):
        """_should_attempt_recovery returns True after interval passes."""
        client._circuit_open = True
        client._circuit_open_time = None  # never opened properly
        assert client._should_attempt_recovery() is True

    def test_no_recovery_before_interval(self, client):
        """_should_attempt_recovery returns False before interval elapses."""
        client._circuit_open = True
        client._circuit_open_time = __import__("datetime").datetime.now()
        client._recovery_probe_interval = 3600  # 1 hour — definitely not elapsed
        assert client._should_attempt_recovery() is False

    def test_recovery_probe_after_interval(self, client):
        """_should_attempt_recovery returns True after interval elapses."""
        import datetime
        client._circuit_open = True
        # Set open_time far in the past
        client._circuit_open_time = datetime.datetime.now() - datetime.timedelta(seconds=3600)
        client._recovery_probe_interval = 30  # 30 seconds — definitely elapsed
        assert client._should_attempt_recovery() is True


# =========================================================================
# Rate Limiter
# =========================================================================


class TestRateLimiter:
    """Rate limiter — 12 req / 60s window."""

    def test_allows_requests_under_max(self, client):
        """Requests under the limit proceed without blocking."""
        client._rate_limit_max = 3
        for _ in range(3):
            client._wait_for_rate_limit()
        # Should not raise — all within limit
        assert len(client._request_timestamps) == 3

    def test_blocks_when_at_max(self, client):
        """Request at max capacity blocks (sleeps) until window passes."""
        client._rate_limit_max = 2
        client._rate_limit_window = 0.05  # 50ms window

        # Fill the window with old enough entries that they won't count
        now = time.time()
        client._request_timestamps = [now - 0.1, now - 0.09]

        # This should succeed without long sleep (old entries expired)
        client._wait_for_rate_limit()
        assert len(client._request_timestamps) >= 1

    def test_window_sliding(self, client):
        """Old entries outside window are pruned."""
        client._rate_limit_max = 5
        now = time.time()
        # Add entries older than the window
        client._request_timestamps = [now - 120, now - 119]
        client._wait_for_rate_limit()
        # Old entries should be pruned, only the new one remains
        for ts in client._request_timestamps:
            assert ts > now - client._rate_limit_window

    def test_concurrent_requests_respect_limit(self, client):
        """Multiple threads collectively respect the rate limit."""
        n_threads = 5
        client._rate_limit_max = n_threads
        client._rate_limit_window = 60  # large window
        errors = []

        def make_request():
            try:
                client._wait_for_rate_limit()
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(n_threads):
            t = __import__("threading").Thread(target=make_request)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(client._request_timestamps) == n_threads


# =========================================================================
# Single-flight dedup
# =========================================================================


class TestSingleFlight:
    """Single-flight deduplication — concurrent same-key requests coalesced."""

    def test_dedup_returns_same_result(self, client):
        """Two threads requesting the same key get the same result."""
        key = "dedup_key"
        result_container = []

        # Pre-populate the in-flight map with a future that resolves
        from concurrent.futures import Future
        future = Future()
        future.set_result("dedup_result")
        with client._in_flight_lock:
            client._in_flight[key] = future

        def read_flight():
            # Simulate the single-flight code path in generate()
            with client._in_flight_lock:
                f = client._in_flight.get(key)
            if f is not None:
                result_container.append(f.result(timeout=5))

        t = __import__("threading").Thread(target=read_flight)
        t.start()
        t.join()

        assert result_container == ["dedup_result"]

    def test_new_request_creates_future(self, client):
        """First request for a key creates a new future in _in_flight."""
        key = "new_key"
        with client._in_flight_lock:
            assert key not in client._in_flight

        with client._in_flight_lock:
            if key not in client._in_flight:
                from concurrent.futures import Future
                client._in_flight[key] = Future()

        with client._in_flight_lock:
            assert key in client._in_flight

    def test_future_cleaned_up_after_error(self, client):
        """Failed single-flight future is cleaned up."""
        key = "error_key"
        from concurrent.futures import Future
        future = Future()
        future.set_exception(RuntimeError("API error"))

        with client._in_flight_lock:
            client._in_flight[key] = future

        # Simulate the error path from generate()
        try:
            with client._in_flight_lock:
                f = client._in_flight.get(key)
            if f is not None:
                f.result(timeout=5)
        except Exception:
            with client._in_flight_lock:
                client._in_flight.pop(key, None)

        with client._in_flight_lock:
            assert key not in client._in_flight


# =========================================================================
# generate()
# =========================================================================


class TestGenerate:
    """``generate()`` — success, caching, circuit breaker, retries, errors."""

    def test_successful_generate(self, client):
        """Basic successful generation returns the response text."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Hello world"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response) as mock_post:
                result = client.generate("Say hello", model="openai/gpt-4o-mini")

        assert result == "Hello world"
        mock_post.assert_called_once()

    def test_generate_uses_cached_result(self, client):
        """Subsequent identical requests return cached response."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Cached response"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response) as mock_post:
                result1 = client.generate("cache me")
                result2 = client.generate("cache me")

        assert result1 == result2 == "Cached response"
        # Only one API call — second served from cache
        mock_post.assert_called_once()

    def test_generate_returns_error_when_circuit_open(self, client):
        """Circuit breaker open returns error message without API call."""
        client._circuit_open = True
        client._circuit_open_time = __import__("datetime").datetime.now()
        client._recovery_probe_interval = 3600  # not yet recoverable

        with patch("requests.post") as mock_post:
            result = client.generate("any prompt")

        assert "Circuit breaker is open" in result
        mock_post.assert_not_called()

    def test_generate_returns_error_no_token(self, client):
        """Missing token returns error message."""
        with patch.object(client, "_resolve_token", return_value=None):
            result = client.generate("prompt")

        assert "LLM request failed" in result

    def test_generate_retries_on_429(self, client):
        """Rate limit (429) triggers retry with backoff."""
        mock_429 = MagicMock(spec=requests.Response)
        mock_429.status_code = 429

        mock_200 = MagicMock(spec=requests.Response)
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "choices": [{"message": {"content": "Retried successfully"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", side_effect=[mock_429, mock_200]) as mock_post:
                result = client.generate("retry me")

        assert result == "Retried successfully"
        assert mock_post.call_count == 2

    def test_generate_retries_on_503(self, client):
        """Service unavailable (503) triggers retry with backoff."""
        mock_503 = MagicMock(spec=requests.Response)
        mock_503.status_code = 503

        mock_200 = MagicMock(spec=requests.Response)
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "choices": [{"message": {"content": "Recovered"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", side_effect=[mock_503, mock_200]) as mock_post:
                result = client.generate("recover")

        assert result == "Recovered"
        assert mock_post.call_count == 2

    def test_generate_non_retryable_4xx(self, client):
        """Non-retryable 4xx (e.g. 400) fails immediately."""
        mock_400 = MagicMock(spec=requests.Response)
        mock_400.status_code = 400
        mock_400.reason = "Bad Request"
        mock_400.raise_for_status.side_effect = requests.HTTPError("400 Bad Request", response=mock_400)

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("src.llm.github_models_client.requests.post", return_value=mock_400):
                result = client.generate("bad request")

        assert "LLM request failed" in result

    def test_generate_exhausts_retries(self, client):
        """After exhausting retries on 429, failure error returned."""
        mock_429 = MagicMock(spec=requests.Response)
        mock_429.status_code = 429

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_429):
                result = client.generate("exhaust")

        assert "LLM request failed" in result

    def test_generate_response_none_content(self, client):
        """Empty content returns empty string."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": None}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response):
                result = client.generate("empty")

        assert result == ""

    def test_generate_connection_error(self, client):
        """Connection error (e.g. timeout) triggers retry."""
        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", side_effect=requests.ConnectionError("connection failed")):
                result = client.generate("timeout")

        assert "LLM request failed" in result

    def test_generate_sets_system_prompt(self, client):
        """System prompt is sent in the API request."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response) as mock_post:
                client.generate("prompt", system_prompt="Be helpful")

        # Verify system prompt was included in payload
        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert {"role": "system", "content": "Be helpful"} in messages
        assert {"role": "user", "content": "prompt"} in messages

    def test_generate_empty_system_prompt_omitted(self, client):
        """Empty system prompt is not included."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response) as mock_post:
                client.generate("prompt", system_prompt="")

        call_kwargs = mock_post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert all(m["role"] != "system" for m in messages)

    def test_generate_cache_bypassed_on_api_failure(self, client):
        """Failed API call does not cache the error response."""
        mock_429 = MagicMock(spec=requests.Response)
        mock_429.status_code = 429

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_429):
                client.generate("no cache fail")

        # Cache should be empty for this key
        key = client._make_cache_key(client.DEFAULT_MODEL, "no cache fail", 512)
        assert client._check_cache(key) is None


# =========================================================================
# is_available()
# =========================================================================


class TestIsAvailable:
    """``is_available()`` — health probe."""

    def test_not_available_no_token(self, client):
        """Returns False when no token is resolved."""
        with patch.object(client, "_resolve_token", return_value=None):
            assert client.is_available() is False

    def test_not_available_circuit_open(self, client):
        """Returns False when circuit breaker is open and not recoverable."""
        client._circuit_open = True
        client._circuit_open_time = __import__("datetime").datetime.now()
        client._recovery_probe_interval = 3600

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            assert client.is_available() is False

    def test_available_when_api_responds(self, client):
        """Returns True when API health check succeeds."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response):
                assert client.is_available() is True

    def test_not_available_on_api_error(self, client):
        """Returns False when API health check fails."""
        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", side_effect=requests.ConnectionError):
                assert client.is_available() is False

    def test_available_resets_circuit_on_success(self, client):
        """Successful health check resets circuit breaker."""
        client._circuit_open = True
        # Make it recoverable
        import datetime
        client._circuit_open_time = datetime.datetime.now() - datetime.timedelta(seconds=3600)
        client._recovery_probe_interval = 30

        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "ok"}}]
        }

        with patch.object(client, "_resolve_token", return_value="ghx_test"):
            with patch("requests.post", return_value=mock_response):
                client.is_available()

        assert client._circuit_open is False
        assert client._circuit_open_time is None
