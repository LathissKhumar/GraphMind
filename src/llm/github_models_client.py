from __future__ import annotations

import os
import subprocess
import time
from collections import OrderedDict
from concurrent.futures import Future
from datetime import datetime
from hashlib import sha256
from threading import Lock
from typing import Optional

import requests


class GitHubModelsClient:
    """GitHub Models free inference API client with caching and circuit breaker.

    Uses the GitHub Models API at https://models.github.ai/inference/chat/completions.
    Authentication via ``gh auth token`` (preferred) or ``GITHUB_TOKEN`` env var.
    """

    BASE_URL = "https://models.github.ai/inference/chat/completions"
    DEFAULT_MODEL = "openai/gpt-4o-mini"

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self._token: str | None = None

        # Circuit breaker
        self._circuit_open = False
        self._failure_timestamps: list[datetime] = []
        self._circuit_open_time: Optional[datetime] = None
        self._failure_threshold = 5
        self._failure_window_seconds = 60
        self._recovery_probe_interval = 30

        # Response cache: LRU with max 100 entries, 300s TTL
        self._cache_max_entries = 100
        self._response_cache: OrderedDict[str, tuple[str, float]] = OrderedDict()
        self._cache_lock = Lock()
        self._cache_ttl = 300.0

        # Single-flight dedup
        self._in_flight: dict[str, "Future[str]"] = {}
        self._in_flight_lock = Lock()

        # Rate limiter: GitHub free tier = 15 req/min
        self._rate_limit_max = 12
        self._rate_limit_window = 60.0
        self._request_timestamps: list[float] = []
        self._rate_limit_lock = Lock()

        # Cache stats
        self._cache_hits = 0
        self._cache_misses = 0
        self._api_call_latency = 0.0

    # ------------------------------------------------------------------
    # Token resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_token() -> str | None:
        """Fetch the GitHub token from env or ``gh auth token``."""
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            return token
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                t = result.stdout.strip()
                if t:
                    return t
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            pass
        return None

    @property
    def token(self) -> str | None:
        if self._token is None:
            self._token = self._resolve_token()
        return self._token

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    @staticmethod
    def _canonicalize_prompt(prompt: str) -> str:
        result = prompt.strip()
        result = "\n".join(line.rstrip() for line in result.split("\n"))
        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")
        return result

    def _make_cache_key(self, model: str, formatted_prompt: str, max_new_tokens: int) -> str:
        canonical = self._canonicalize_prompt(formatted_prompt)
        key_input = f"gh:{model}\u0000{canonical}\u0000{max_new_tokens}"
        return sha256(key_input.encode("utf-8")).hexdigest()

    def _check_cache(self, key: str) -> Optional[str]:
        now = time.time()
        with self._cache_lock:
            if key in self._response_cache:
                response, timestamp = self._response_cache[key]
                if now - timestamp < self._cache_ttl:
                    self._response_cache.move_to_end(key)
                    self._cache_hits += 1
                    return response
                del self._response_cache[key]
            self._cache_misses += 1
            return None

    def _store_cache(self, key: str, response: str) -> None:
        now = time.time()
        with self._cache_lock:
            self._response_cache[key] = (response, now)
            self._response_cache.move_to_end(key)
            if len(self._response_cache) > self._cache_max_entries:
                self._response_cache.popitem(last=False)

    # ------------------------------------------------------------------
    # Circuit breaker
    # ------------------------------------------------------------------

    def _record_success(self) -> None:
        self._failure_timestamps = []
        self._circuit_open = False
        self._circuit_open_time = None

    def _record_failure(self) -> None:
        now = datetime.now()
        self._failure_timestamps.append(now)
        self._failure_timestamps = [
            ts for ts in self._failure_timestamps
            if (now - ts).total_seconds() < self._failure_window_seconds
        ]
        if len(self._failure_timestamps) >= self._failure_threshold:
            self._circuit_open = True
            self._circuit_open_time = now

    def _should_attempt_recovery(self) -> bool:
        if not self._circuit_open_time:
            return True
        return (datetime.now() - self._circuit_open_time).total_seconds() >= self._recovery_probe_interval

    # ------------------------------------------------------------------
    # API call
    # ------------------------------------------------------------------

    def _wait_for_rate_limit(self) -> None:
        """Block until a request slot opens within the rate limit window."""
        with self._rate_limit_lock:
            now = time.time()
            cutoff = now - self._rate_limit_window
            self._request_timestamps = [ts for ts in self._request_timestamps if ts > cutoff]

            if len(self._request_timestamps) >= self._rate_limit_max:
                sleep_time = self._request_timestamps[0] + self._rate_limit_window - now
                if sleep_time > 0:
                    time.sleep(sleep_time + 0.5)
                self._request_timestamps = [ts for ts in self._request_timestamps if ts > time.time() - self._rate_limit_window]

            self._request_timestamps.append(time.time())

    def _post_chat(
        self,
        model: str,
        system_prompt: str,
        prompt: str,
        max_tokens: int = 512,
    ) -> str:
        """Make a single chat completion call to GitHub Models API."""
        self._wait_for_rate_limit()

        token = self.token
        if not token:
            raise RuntimeError(
                "GitHub token not found. Set GITHUB_TOKEN env var or run 'gh auth login'."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        resp = requests.post(
            self.BASE_URL,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        if resp.status_code == 429:
            raise requests.HTTPError("Rate limited", response=resp)
        if resp.status_code == 503:
            raise requests.HTTPError("Service temporarily unavailable", response=resp)
        resp.raise_for_status()

        data = resp.json()
        choice = data["choices"][0]
        content = choice["message"]["content"]
        return content.strip() if content else ""

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        model: str | None = None,
    ) -> str:
        """Generate a response using GitHub Models chat completion.

        Args:
            prompt: User prompt text.
            system_prompt: Optional system instruction.
            model: Model to use (default: ``openai/gpt-4o-mini``).

        Returns:
            Generated text, or an error message string on failure.
        """
        if self._circuit_open and not self._should_attempt_recovery():
            return "LLM request failed: Circuit breaker is open"

        model = model or self.DEFAULT_MODEL
        max_new_tokens = 512
        key = self._make_cache_key(model, prompt, max_new_tokens)

        # Check cache
        cached = self._check_cache(key)
        if cached is not None:
            self._record_success()
            return cached

        # Single-flight dedup
        in_flight_future: Optional["Future[str]"] = None
        with self._in_flight_lock:
            if key in self._in_flight:
                in_flight_future = self._in_flight[key]
            else:
                future: "Future[str]" = Future()
                self._in_flight[key] = future

        if in_flight_future is not None:
            try:
                result = in_flight_future.result(timeout=60)
                self._record_success()
                return result
            except Exception:
                with self._in_flight_lock:
                    self._in_flight.pop(key, None)

        # Make the API call with retries
        last_error: str | None = None
        try:
            for attempt in range(self.max_retries):
                try:
                    api_start = time.time()
                    resp_text = self._post_chat(model, system_prompt, prompt, max_new_tokens)
                    self._api_call_latency += time.time() - api_start

                    self._store_cache(key, resp_text)
                    with self._in_flight_lock:
                        if key in self._in_flight:
                            self._in_flight[key].set_result(resp_text)
                            self._in_flight.pop(key, None)

                    self._record_success()
                    return resp_text

                except requests.HTTPError as e:
                    status = e.response.status_code if e.response is not None else 0
                    if status in (429, 503):
                        delay = 2 ** attempt
                        time.sleep(delay)
                        last_error = f"HTTP {status}"
                    else:
                        last_error = f"HTTP {status}: {e}"
                        break
                except Exception as e:
                    last_error = str(e)
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                    continue
        finally:
            with self._in_flight_lock:
                self._in_flight.pop(key, None)

        self._record_failure()
        return f"LLM request failed: {last_error or 'Unknown error'}"

    def is_available(self) -> bool:
        """Probe whether GitHub Models is reachable (fast token + API check)."""
        token = self.token
        if not token:
            return False

        if self._circuit_open and not self._should_attempt_recovery():
            return False

        try:
            self._post_chat(
                self.DEFAULT_MODEL,
                "",
                "health check",
                max_tokens=1,
            )
            self._record_success()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    client = GitHubModelsClient()
    if client.token:
        print(f"GitHub token resolved (len={len(client.token)})")
        print(f"Available: {client.is_available()}")
        resp = client.generate("Say hello in 3 words.", model="openai/gpt-4o-mini")
        print(f"Test response: {resp}")
    else:
        print("No GitHub token found.")
