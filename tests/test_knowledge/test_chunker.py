"""Tests for the text chunker service."""

import pytest
from axon.knowledge.chunker import TextChunker, Chunk


class TestTextChunker:
    """Test suite for TextChunker."""

    def test_chunker_default_initialization(self):
        """Test chunker initializes with default settings."""
        chunker = TextChunker()
        assert chunker.chunk_size == 500
        assert chunker.chunk_overlap == 50

    def test_chunker_custom_initialization(self):
        """Test chunker initializes with custom settings."""
        chunker = TextChunker(chunk_size=1000, chunk_overlap=100)
        assert chunker.chunk_size == 1000
        assert chunker.chunk_overlap == 100

    def test_chunk_short_text_returns_single_chunk(self):
        """Test short text returns a single chunk."""
        chunker = TextChunker(chunk_size=500)
        text = "This is a short text."
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].index == 0

    def test_chunk_long_text_returns_multiple_chunks(self):
        """Test long text is split into multiple chunks."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        # Create text longer than chunk_size
        text = "This is a longer text. " * 20  # ~460 characters
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 1
        # Verify sequential indexing
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunk_preserves_sections(self):
        """Test chunker preserves section boundaries when possible."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        text = """# Section 1

This is the first section with some content.

# Section 2

This is the second section with different content.

# Section 3

This is the third section."""
        
        chunks = chunker.chunk_text(text)
        
        # Should try to split at section boundaries
        assert len(chunks) >= 1
        # First chunk should contain Section 1
        assert "Section 1" in chunks[0].content

    def test_chunk_with_markdown_headings(self):
        """Test chunker handles markdown headings properly."""
        chunker = TextChunker(chunk_size=200, chunk_overlap=20)
        text = """# Main Title

Introduction paragraph.

## Subsection A

Content for subsection A goes here with more detail.

## Subsection B

Content for subsection B goes here with more detail."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) >= 1
        # Should extract heading hierarchy
        first_chunk = chunks[0]
        assert first_chunk.section_title is not None or "Main Title" in first_chunk.content

    def test_chunk_extracts_heading_hierarchy(self):
        """Test chunker extracts heading hierarchy for each chunk."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=10)
        text = """# Level 1

## Level 2

### Level 3

Some content here that should have the full hierarchy."""
        
        chunks = chunker.chunk_text(text)
        
        # At least one chunk should have heading hierarchy
        assert any(chunk.heading_hierarchy for chunk in chunks)

    def test_chunk_estimates_token_count(self):
        """Test chunker estimates token count for each chunk."""
        chunker = TextChunker(chunk_size=500)
        text = "This is a test sentence with multiple words. " * 10
        
        chunks = chunker.chunk_text(text)
        
        # Each chunk should have an estimated token count
        for chunk in chunks:
            assert chunk.token_count is not None
            assert chunk.token_count > 0

    def test_chunk_empty_text_returns_empty_list(self):
        """Test empty text returns empty chunk list."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("")
        assert chunks == []

    def test_chunk_whitespace_only_returns_empty_list(self):
        """Test whitespace-only text returns empty chunk list."""
        chunker = TextChunker()
        chunks = chunker.chunk_text("   \n\n   \t  ")
        assert chunks == []


class TestChunkDataclass:
    """Test Chunk dataclass."""

    def test_chunk_creation(self):
        """Test basic chunk creation."""
        chunk = Chunk(
            index=0,
            content="Test content",
            section_title="Test Section",
            heading_hierarchy=["Level 1", "Level 2"],
            token_count=50
        )
        
        assert chunk.index == 0
        assert chunk.content == "Test content"
        assert chunk.section_title == "Test Section"
        assert chunk.heading_hierarchy == ["Level 1", "Level 2"]
        assert chunk.token_count == 50

    def test_chunk_optional_fields(self):
        """Test chunk with optional fields as None."""
        chunk = Chunk(
            index=0,
            content="Test content"
        )
        
        assert chunk.section_title is None
        assert chunk.heading_hierarchy is None
        assert chunk.token_count is None


class TestChunkerMarkdownParsing:
    """Test chunker's markdown parsing capabilities."""

    def test_parse_braak_staging_content(self):
        """Test parsing typical neuroscience content about Braak staging."""
        chunker = TextChunker(chunk_size=500, chunk_overlap=50)
        text = """# Neuropathology Metrics

## Braak Staging

Braak staging refers to two methods used to classify the degree of pathology in Parkinson's and Alzheimer's disease.

### Braak NFT Stages

- Stage 0: No tangles
- Stage I-II: Transentorhinal stages
- Stage III-IV: Limbic stages  
- Stage V-VI: Isocortical stages

The Braak stage indicates the anatomical progression of neurofibrillary tangles.

## Thal Phases

Thal phases describe the progression of amyloid-beta plaque deposition:

- Phase 0: No amyloid
- Phase 1: Isocortical
- Phase 2: Allocortical
- Phase 3: Subcortical
- Phase 4: Brainstem
- Phase 5: Cerebellum"""
        
        chunks = chunker.chunk_text(text)
        
        # Should create multiple chunks preserving the structure
        assert len(chunks) >= 1
        
        # Content should be preserved across chunks
        all_content = " ".join(c.content for c in chunks)
        assert "Braak staging" in all_content
        assert "Thal phases" in all_content.lower() or "Thal" in all_content

    def test_parse_tissue_processing_content(self):
        """Test parsing tissue processing best practices content."""
        chunker = TextChunker(chunk_size=400, chunk_overlap=40)
        text = """# Tissue Processing and Preparation

## Fixation Methods

Brain tissue can be preserved using several methods:

1. **Formalin Fixation**: Standard method for histology
2. **Flash Freezing**: Preserves RNA integrity for molecular studies
3. **OCT Embedding**: For cryosectioning

## Quality Control

### RNA Integrity Number (RIN)

The RIN value ranges from 1-10, with 10 being highest quality:
- RIN > 7: Suitable for RNA-seq
- RIN 5-7: May be suitable for some applications
- RIN < 5: Generally not recommended for RNA work

### pH Assessment

Brain tissue pH should typically be > 6.0 for quality research use."""
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) >= 1
        # Key terms should be preserved
        all_content = " ".join(c.content for c in chunks)
        assert "RIN" in all_content
        assert "fixation" in all_content.lower()

