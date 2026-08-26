from __future__ import annotations

class Chunker:
    def __init__(self, chunk_size: int = 2048, overlap_size: int = 256, threshold: float = 0.95):
        self.chunk_size: int = chunk_size
        self.overlap_size: int = overlap_size
        self.threshold: float = threshold

    def chunk_text(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            if end < text_len:
                chunk_content = text[start:end]
                split_positions: list[int] = []

                idx = chunk_content.rfind('\n\n')
                if idx != -1:
                    split_positions.append(start + idx + 2)

                idx = chunk_content.rfind('\n')
                if idx != -1:
                    split_positions.append(start + idx + 1)

                for punct in ['. ', '! ', '? ', '.', '!', '?']:
                    idx = chunk_content.rfind(punct)
                    if idx != -1:
                        split_positions.append(start + idx + len(punct))

                valid_splits = [p for p in split_positions if p <= end]
                if valid_splits:
                    end = max(valid_splits)

            chunks.append(text[start:end])

            next_start = end - self.overlap_size
            if next_start <= start:
                next_start = start + 1
            start = next_start

            if start >= text_len:
                break

        return chunks
