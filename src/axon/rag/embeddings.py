"""Embedding service for semantic search using OpenAI."""

from typing import Sequence

from openai import AsyncOpenAI

from axon.db.models import Sample


class EmbeddingService:
    """Service for generating embeddings using OpenAI's API."""
    
    # OpenAI text-embedding-3-small produces 1536-dimensional vectors
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    
    def __init__(
        self,
        api_key: str,
        batch_size: int = 2000,  # OpenAI allows up to 2048 per request
    ):
        """Initialize the embedding service.
        
        Args:
            api_key: OpenAI API key
            batch_size: Maximum texts per API call
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.batch_size = batch_size
    
    async def embed_text(self, text: str) -> list[float]:
        """Create embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Cannot create embedding for empty text")
        
        response = await self.client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=text,
        )
        
        return response.data[0].embedding
    
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts in a single API call.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        
        response = await self.client.embeddings.create(
            model=self.EMBEDDING_MODEL,
            input=valid_texts,
        )
        
        return [item.embedding for item in response.data]
    
    def generate_sample_text(self, sample: Sample) -> str:
        """Generate searchable text representation of a sample.
        
        Creates a natural language description of the sample that captures
        all relevant information for semantic search.
        
        Args:
            sample: Sample to generate text for
            
        Returns:
            Text representation of the sample
        """
        parts = []
        
        # Diagnosis (most important for search)
        if sample.primary_diagnosis:
            parts.append(f"Diagnosis: {sample.primary_diagnosis}")
        
        if sample.secondary_diagnoses:
            secondary = ", ".join(
                d.get("diagnosis", "") for d in sample.secondary_diagnoses
                if d.get("diagnosis")
            )
            if secondary:
                parts.append(f"Secondary diagnoses: {secondary}")
        
        # Brain regions
        if sample.brain_region:
            parts.append(f"Brain regions: {sample.brain_region}")
        
        # Demographics
        demographics = []
        if sample.donor_age:
            demographics.append(f"{sample.donor_age} years old")
        if sample.donor_sex:
            demographics.append(sample.donor_sex)
        if sample.donor_race:
            demographics.append(sample.donor_race)
        if demographics:
            parts.append(f"Donor: {', '.join(demographics)}")
        
        # Quality metrics
        quality = []
        if sample.rin_score:
            quality.append(f"RIN score {sample.rin_score}")
        if sample.postmortem_interval_hours:
            quality.append(f"PMI {sample.postmortem_interval_hours} hours")
        if quality:
            parts.append(f"Quality: {', '.join(quality)}")
        
        # Tissue details
        tissue = []
        if sample.hemisphere:
            tissue.append(f"{sample.hemisphere} hemisphere")
        if sample.preservation_method:
            tissue.append(sample.preservation_method)
        if sample.tissue_type:
            tissue.append(sample.tissue_type)
        if tissue:
            parts.append(f"Tissue: {', '.join(tissue)}")
        
        # Source
        if sample.source_bank:
            parts.append(f"Source: {sample.source_bank}")
        
        # Cause of death
        if sample.cause_of_death:
            parts.append(f"Cause of death: {sample.cause_of_death}")
        
        return ". ".join(parts) if parts else f"Sample from {sample.source_bank}"
    
    async def embed_sample(self, sample: Sample) -> list[float]:
        """Generate embedding for a single sample.
        
        Args:
            sample: Sample to embed
            
        Returns:
            Embedding vector
        """
        text = self.generate_sample_text(sample)
        return await self.embed_text(text)
    
    async def embed_samples(
        self,
        samples: Sequence[Sample],
    ) -> list[list[float]]:
        """Generate embeddings for multiple samples.
        
        Processes samples in batches to respect API rate limits.
        
        Args:
            samples: Samples to embed
            
        Returns:
            List of embedding vectors in the same order as input samples
        """
        if not samples:
            return []
        
        texts = [self.generate_sample_text(s) for s in samples]
        
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            embeddings = await self.embed_batch(batch)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
    
    async def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector for the query
        """
        return await self.embed_text(query)

