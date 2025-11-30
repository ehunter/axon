"""Text chunking service for splitting documents into embeddable chunks."""

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """Represents a chunk of text from a document."""
    
    index: int
    content: str
    section_title: str | None = None
    heading_hierarchy: list[str] | None = None
    token_count: int | None = None


class TextChunker:
    """Service for chunking text documents while preserving structure."""
    
    # Regex patterns for markdown headings
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        respect_sections: bool = True
    ):
        """Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in characters (approximate).
            chunk_overlap: Overlap between chunks in characters.
            respect_sections: Try to split at section boundaries when possible.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.respect_sections = respect_sections
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (rough approximation).
        
        Uses ~4 characters per token as a rough estimate.
        """
        return len(text) // 4
    
    def _extract_headings(self, text: str) -> list[tuple[int, int, str]]:
        """Extract all headings with their positions and levels.
        
        Returns:
            List of (position, level, heading_text) tuples.
        """
        headings = []
        for match in self.HEADING_PATTERN.finditer(text):
            level = len(match.group(1))  # Number of # symbols
            heading_text = match.group(2).strip()
            headings.append((match.start(), level, heading_text))
        return headings
    
    def _get_heading_hierarchy(
        self,
        position: int,
        headings: list[tuple[int, int, str]]
    ) -> list[str]:
        """Get the heading hierarchy for a given position.
        
        Args:
            position: Character position in the text.
            headings: List of (position, level, text) tuples.
            
        Returns:
            List of heading texts forming the hierarchy.
        """
        # Find all headings before this position
        relevant = [h for h in headings if h[0] < position]
        if not relevant:
            return []
        
        # Build hierarchy by tracking the most recent heading at each level
        hierarchy_map: dict[int, str] = {}
        for _, level, text in relevant:
            # Clear lower-level headings when we hit a higher-level one
            hierarchy_map = {l: t for l, t in hierarchy_map.items() if l < level}
            hierarchy_map[level] = text
        
        # Return sorted by level
        return [hierarchy_map[l] for l in sorted(hierarchy_map.keys())]
    
    def _find_split_point(self, text: str, target: int) -> int:
        """Find a good split point near the target position.
        
        Tries to split at paragraph breaks, sentence ends, or word boundaries.
        """
        # Don't go beyond text length
        if target >= len(text):
            return len(text)
        
        # Look for paragraph break near target
        search_start = max(0, target - 100)
        search_end = min(len(text), target + 100)
        search_region = text[search_start:search_end]
        
        # Try to find paragraph break
        para_match = re.search(r'\n\n', search_region)
        if para_match:
            return search_start + para_match.end()
        
        # Try to find sentence end
        sentence_match = re.search(r'[.!?]\s+', search_region)
        if sentence_match:
            return search_start + sentence_match.end()
        
        # Try to find word boundary
        word_match = re.search(r'\s+', search_region[len(search_region)//2:])
        if word_match:
            return search_start + len(search_region)//2 + word_match.end()
        
        # Fall back to target position
        return target
    
    def _split_at_sections(self, text: str) -> list[tuple[str, str | None, list[str]]]:
        """Split text at section boundaries.
        
        Returns:
            List of (content, section_title, heading_hierarchy) tuples.
        """
        headings = self._extract_headings(text)
        
        if not headings:
            return [(text, None, [])]
        
        sections = []
        
        for i, (pos, level, title) in enumerate(headings):
            # Find end position (next heading or end of text)
            end_pos = headings[i + 1][0] if i + 1 < len(headings) else len(text)
            
            # Extract section content including the heading
            content = text[pos:end_pos].strip()
            
            if content:
                hierarchy = self._get_heading_hierarchy(pos + 1, headings)
                # Add current heading to hierarchy
                hierarchy.append(title)
                sections.append((content, title, hierarchy))
        
        # Handle content before first heading
        if headings[0][0] > 0:
            intro = text[:headings[0][0]].strip()
            if intro:
                sections.insert(0, (intro, None, []))
        
        return sections
    
    def chunk_text(self, text: str) -> list[Chunk]:
        """Split text into chunks while preserving structure.
        
        Args:
            text: The text to chunk.
            
        Returns:
            List of Chunk objects.
        """
        if not text or not text.strip():
            return []
        
        text = text.strip()
        chunks: list[Chunk] = []
        headings = self._extract_headings(text)
        
        if self.respect_sections and headings:
            # Split at sections first, then chunk large sections
            sections = self._split_at_sections(text)
            
            for section_content, section_title, hierarchy in sections:
                # If section is small enough, make it a single chunk
                if len(section_content) <= self.chunk_size * 1.2:  # Allow 20% overflow
                    chunks.append(Chunk(
                        index=len(chunks),
                        content=section_content,
                        section_title=section_title,
                        heading_hierarchy=hierarchy if hierarchy else None,
                        token_count=self._estimate_tokens(section_content)
                    ))
                else:
                    # Split large section into multiple chunks
                    sub_chunks = self._chunk_large_section(
                        section_content, section_title, hierarchy
                    )
                    for sub in sub_chunks:
                        sub.index = len(chunks)
                        chunks.append(sub)
        else:
            # Simple chunking without section awareness
            chunks = self._simple_chunk(text, headings)
        
        return chunks
    
    def _chunk_large_section(
        self,
        content: str,
        section_title: str | None,
        hierarchy: list[str]
    ) -> list[Chunk]:
        """Chunk a large section into smaller pieces with overlap."""
        chunks = []
        start = 0
        
        while start < len(content):
            # Find end point for this chunk
            end = start + self.chunk_size
            
            if end >= len(content):
                # Last chunk
                chunk_content = content[start:].strip()
            else:
                # Find a good split point
                end = self._find_split_point(content, end)
                chunk_content = content[start:end].strip()
            
            if chunk_content:
                chunks.append(Chunk(
                    index=0,  # Will be updated by caller
                    content=chunk_content,
                    section_title=section_title,
                    heading_hierarchy=hierarchy if hierarchy else None,
                    token_count=self._estimate_tokens(chunk_content)
                ))
            
            # Move start with overlap
            start = end - self.chunk_overlap if end < len(content) else len(content)
        
        return chunks
    
    def _simple_chunk(
        self,
        text: str,
        headings: list[tuple[int, int, str]]
    ) -> list[Chunk]:
        """Simple chunking without section awareness."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunk_content = text[start:].strip()
            else:
                end = self._find_split_point(text, end)
                chunk_content = text[start:end].strip()
            
            if chunk_content:
                # Get heading hierarchy for this position
                hierarchy = self._get_heading_hierarchy(start, headings)
                section = hierarchy[-1] if hierarchy else None
                
                chunks.append(Chunk(
                    index=len(chunks),
                    content=chunk_content,
                    section_title=section,
                    heading_hierarchy=hierarchy if hierarchy else None,
                    token_count=self._estimate_tokens(chunk_content)
                ))
            
            start = end - self.chunk_overlap if end < len(text) else len(text)
        
        return chunks

