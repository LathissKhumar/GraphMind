from __future__ import annotations

import re
from typing import List


class SemanticChunker:
    """Semantic-aware chunking that respects code and text boundaries."""
    
    def __init__(self, max_chunk_size: int = 2048, overlap: int = 256):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
        
        # Regex patterns for code boundaries
        self.code_boundary_patterns = [
            r'^(def |async def )',  # Function definitions
            r'^(class )',  # Class definitions
            r'^(import |from )',  # Import statements
        ]
        
        # Sentence ending patterns
        self.sentence_endings = ['. ', '! ', '? ', '.', '!', '?']
    
    def chunk_code(self, code: str, max_chunk_size: int = None, overlap: int = None) -> List[str]:
        """Chunk code by respecting function/class boundaries."""
        max_chunk_size = max_chunk_size or self.max_chunk_size
        overlap = overlap or self.overlap
        
        if not code:
            return []
        
        lines = code.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            # Check if this line starts a new code block
            is_boundary = any(re.match(pattern, line.lstrip()) for pattern in self.code_boundary_patterns)
            
            # If we hit a boundary and current chunk is substantial, start new chunk
            if is_boundary and current_chunk and current_size > overlap:
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) > overlap:  # Ensure chunk is meaningful
                    chunks.append(chunk_text)
                
                # Start new chunk with overlap from previous
                if overlap > 0 and len(current_chunk) > 0:
                    overlap_lines = self._get_overlap_lines(current_chunk, overlap)
                    current_chunk = overlap_lines
                    current_size = sum(len(l) + 1 for l in current_chunk)
                else:
                    current_chunk = []
                    current_size = 0
            
            # Add line to current chunk
            current_chunk.append(line)
            current_size += line_size
            
            # If chunk exceeds max size, try to split at previous boundary
            if current_size > max_chunk_size:
                split_point = self._find_split_point(current_chunk, max_chunk_size)
                if split_point > 0:
                    # Add chunk up to split point
                    chunk_lines = current_chunk[:split_point]
                    chunk_text = '\n'.join(chunk_lines)
                    if len(chunk_text) > overlap:
                        chunks.append(chunk_text)
                    
                    # Start new chunk with overlap
                    if overlap > 0:
                        overlap_lines = self._get_overlap_lines(chunk_lines, overlap)
                        current_chunk = overlap_lines + current_chunk[split_point:]
                    else:
                        current_chunk = current_chunk[split_point:]
                    
                    current_size = sum(len(l) + 1 for l in current_chunk)
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > overlap:
                chunks.append(chunk_text)
        
        return chunks
    
    def chunk_text(self, text: str, max_chunk_size: int = None, overlap: int = None) -> List[str]:
        """Chunk text by semantic boundaries (paragraphs -> sentences -> words)."""
        max_chunk_size = max_chunk_size or self.max_chunk_size
        overlap = overlap or self.overlap
        
        if not text:
            return []
        
        chunks = []
        
        # First try: split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(paragraph) <= max_chunk_size:
                chunks.append(paragraph)
            else:
                # Second try: split by sentences
                sentence_chunks = self._split_by_sentences(paragraph, max_chunk_size, overlap)
                chunks.extend(sentence_chunks)
        
        return chunks
    
    def auto_chunk(self, content: str, max_chunk_size: int = None, overlap: int = None) -> List[str]:
        """Auto-detect content type and chunk accordingly."""
        max_chunk_size = max_chunk_size or self.max_chunk_size
        overlap = overlap or self.overlap
        
        if self._is_code_content(content):
            return self.chunk_code(content, max_chunk_size, overlap)
        else:
            return self.chunk_text(content, max_chunk_size, overlap)
    
    def _is_code_content(self, content: str) -> bool:
        """Detect if content is code by checking for Python keywords at line starts."""
        lines = content.split('\n')[:50]  # Check first 50 lines
        code_indicators = 0
        
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(keyword) for keyword in ['def ', 'class ', 'import ', 'from ', 'async def ']):
                code_indicators += 1
                if code_indicators >= 2:  # At least 2 code indicators
                    return True
        
        return False
    
    def _find_split_point(self, lines: List[str], max_size: int) -> int:
        """Find optimal split point in lines based on code boundaries."""
        current_size = 0
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1
            
            if current_size + line_size > max_size:
                # Try to split at previous boundary
                for j in range(i - 1, max(0, i - 10), -1):
                    if any(re.match(pattern, lines[j].lstrip()) for pattern in self.code_boundary_patterns):
                        return j
                # If no boundary found, split at current position
                return i
            
            current_size += line_size
        
        return len(lines)
    
    def _get_overlap_lines(self, lines: List[str], overlap_size: int) -> List[str]:
        """Get lines for overlap from the end of a chunk."""
        overlap_lines = []
        current_size = 0
        
        for line in reversed(lines):
            line_size = len(line) + 1
            if current_size + line_size <= overlap_size:
                overlap_lines.insert(0, line)
                current_size += line_size
            else:
                break
        
        return overlap_lines
    
    def _split_by_sentences(self, text: str, max_size: int, overlap: int) -> List[str]:
        """Split text by sentences, falling back to words if needed."""
        chunks = []
        
        # Split by sentence endings
        sentences = []
        current = text
        
        while current:
            split_pos = -1
            for ending in self.sentence_endings:
                pos = current.find(ending)
                if pos != -1:
                    split_pos = pos + len(ending)
                    break
            
            if split_pos == -1:
                sentences.append(current)
                break
            else:
                sentences.append(current[:split_pos])
                current = current[split_pos:].lstrip()
        
        # Build chunks from sentences
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size <= max_size:
                current_chunk.append(sentence)
                current_size += sentence_size
            else:
                # If single sentence is too long, split by words
                if not current_chunk:
                    word_chunks = self._split_by_words(sentence, max_size, overlap)
                    chunks.extend(word_chunks)
                else:
                    # Add current chunk
                    chunks.append(' '.join(current_chunk))
                    
                    # Start new chunk with overlap
                    if overlap > 0:
                        overlap_text = ' '.join(current_chunk)[-overlap:]
                        current_chunk = [overlap_text + sentence]
                        current_size = len(overlap_text) + sentence_size
                    else:
                        current_chunk = [sentence]
                        current_size = sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_by_words(self, text: str, max_size: int, overlap: int) -> List[str]:
        """Split text by words as final fallback."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size <= max_size:
                current_chunk.append(word)
                current_size += word_size
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # Start new chunk
                current_chunk = [word]
                current_size = word_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
