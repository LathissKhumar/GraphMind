from __future__ import annotations

from typing import Optional


class TokenCounter:
    def __init__(self) -> None:
        self._encoder = self._load_encoder()

    def _load_encoder(self):
        try:
            import tiktoken  # type: ignore

            return tiktoken.get_encoding("cl100k_base")
        except Exception:
            return None

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        if self._encoder is not None:
            try:
                return len(self._encoder.encode(text))
            except Exception:
                pass
        return max(1, int(round(len(text.split()) * 1.3)))


if __name__ == "__main__":
    counter = TokenCounter()
    print(counter.count_tokens("hello world"))
