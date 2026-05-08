from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import List, Optional

from .prompts import build_llm_full_prompt


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODELS = [
    "github/qwen-coder",
    "github/claude-sonnet-4",
    "openai/gpt-4o-mini",
]


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    status_code: int


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        models: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.models = models or list(DEFAULT_MODELS)
        self.timeout = timeout

    def generate(self, prompt: str, context: str = "") -> str:
        """Generate text using OpenRouter."""
        payload_prompt = build_llm_full_prompt(prompt, context)

        last_error: Optional[str] = None
        for model in self.models:
            try:
                response = self._request(model, payload_prompt)
                if response.text.strip():
                    return response.text.strip()
                last_error = f"Empty response from {model}"
            except Exception as exc:
                last_error = str(exc)

        if last_error:
            return f"OpenRouter request failed: {last_error}"
        return "OpenRouter request failed: no models configured"

    def is_available(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return bool(self.api_key)

    def _request(self, model: str, prompt: str) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured")

        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful code assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        request = urllib.request.Request(
            OPENROUTER_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "HTTP-Referer": "https://graphmind.local",
                "X-Title": "GraphMind",
            },
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            status_code = getattr(response, "status", 200)
            payload = json.loads(response.read().decode("utf-8"))
            text = payload["choices"][0]["message"]["content"]
            return LLMResponse(text=text, model=model, status_code=status_code)


if __name__ == "__main__":
    client = LLMClient()
    print(client.generate("Hello"))
