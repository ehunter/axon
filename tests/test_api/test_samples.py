"""Tests for sample API endpoints.

Following TDD: tests written first, then implementation.
"""

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from axon.api.main import app
from axon.db.models import Sample


@pytest.fixture
async def sample_data(db_session):
    """Create test samples in the database."""
    samples = [
        Sample(
            source_bank="NIH Miami",
            external_id="NIH1001",
            donor_age=65,
            donor_sex="female",
            donor_race="White",
            primary_diagnosis="Alzheimer's disease",
            primary_diagnosis_code="G30.9",
            brain_region="Hippocampus, Frontal cortex",
            rin_score=Decimal("7.5"),
            postmortem_interval_hours=Decimal("12.0"),
            raw_data={"test": True},
        ),
        Sample(
            source_bank="NIH Miami",
            external_id="NIH1002",
            donor_age=70,
            donor_sex="male",
            donor_race="White",
            primary_diagnosis="Parkinson's disease",
            primary_diagnosis_code="G20",
            brain_region="Substantia nigra",
            rin_score=Decimal("6.8"),
            postmortem_interval_hours=Decimal("18.0"),
            raw_data={"test": True},
        ),
        Sample(
            source_bank="Harvard",
            external_id="H2001",
            donor_age=55,
            donor_sex="female",
            donor_race="Black or African-American",
            primary_diagnosis="ALS",
            primary_diagnosis_code="G12.21",
            brain_region="Motor cortex",
            rin_score=Decimal("8.2"),
            postmortem_interval_hours=Decimal("6.0"),
            raw_data={"test": True},
        ),
    ]
    
    for sample in samples:
        db_session.add(sample)
    await db_session.commit()
    
    # Refresh to get IDs
    for sample in samples:
        await db_session.refresh(sample)
    
    return samples


@pytest.fixture
async def client(db_session):
    """Create test client with database session override."""
    from axon.api.dependencies import get_db
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


class TestListSamples:
    """Tests for GET /api/v1/samples"""

    @pytest.mark.asyncio
    async def test_list_samples_empty(self, client):
        """Should return empty list when no samples exist."""
        response = await client.get("/api/v1/samples")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_samples_with_data(self, client, sample_data):
        """Should return list of samples."""
        response = await client.get("/api/v1/samples")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_list_samples_pagination(self, client, sample_data):
        """Should support pagination."""
        response = await client.get("/api/v1/samples?limit=2&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_samples_filter_by_source(self, client, sample_data):
        """Should filter by source_bank."""
        response = await client.get("/api/v1/samples?source_bank=Harvard")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["source_bank"] == "Harvard"

    @pytest.mark.asyncio
    async def test_list_samples_filter_by_diagnosis(self, client, sample_data):
        """Should filter by diagnosis (partial match)."""
        response = await client.get("/api/v1/samples?diagnosis=alzheimer")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "Alzheimer" in data["items"][0]["primary_diagnosis"]


class TestGetSample:
    """Tests for GET /api/v1/samples/{id}"""

    @pytest.mark.asyncio
    async def test_get_sample_by_id(self, client, sample_data):
        """Should return sample by ID."""
        sample_id = sample_data[0].id
        response = await client.get(f"/api/v1/samples/{sample_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_id
        assert data["external_id"] == "NIH1001"
        assert data["source_bank"] == "NIH Miami"

    @pytest.mark.asyncio
    async def test_get_sample_not_found(self, client):
        """Should return 404 for non-existent sample."""
        response = await client.get("/api/v1/samples/nonexistent-id")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sample_includes_all_fields(self, client, sample_data):
        """Should include all relevant fields."""
        sample_id = sample_data[0].id
        response = await client.get(f"/api/v1/samples/{sample_id}")
        
        data = response.json()
        
        # Check required fields are present
        assert "id" in data
        assert "source_bank" in data
        assert "external_id" in data
        assert "donor_age" in data
        assert "donor_sex" in data
        assert "primary_diagnosis" in data
        assert "brain_region" in data
        assert "rin_score" in data
        assert "postmortem_interval_hours" in data


class TestSearchSamples:
    """Tests for POST /api/v1/samples/search"""

    @pytest.mark.asyncio
    async def test_search_by_diagnosis(self, client, sample_data):
        """Should search samples by diagnosis."""
        response = await client.post(
            "/api/v1/samples/search",
            json={"diagnosis": "Parkinson"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "Parkinson" in data["items"][0]["primary_diagnosis"]

    @pytest.mark.asyncio
    async def test_search_by_brain_region(self, client, sample_data):
        """Should search samples by brain region."""
        response = await client.post(
            "/api/v1/samples/search",
            json={"brain_region": "hippocampus"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1

    @pytest.mark.asyncio
    async def test_search_by_age_range(self, client, sample_data):
        """Should filter by age range."""
        response = await client.post(
            "/api/v1/samples/search",
            json={"min_age": 60, "max_age": 75}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # 65 and 70 year olds

    @pytest.mark.asyncio
    async def test_search_by_rin_score(self, client, sample_data):
        """Should filter by minimum RIN score."""
        response = await client.post(
            "/api/v1/samples/search",
            json={"min_rin": 7.0}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2  # 7.5 and 8.2

    @pytest.mark.asyncio
    async def test_search_multiple_criteria(self, client, sample_data):
        """Should support multiple search criteria."""
        response = await client.post(
            "/api/v1/samples/search",
            json={
                "source_bank": "NIH Miami",
                "min_rin": 7.0,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["external_id"] == "NIH1001"


class TestSampleStats:
    """Tests for GET /api/v1/samples/stats"""

    @pytest.mark.asyncio
    async def test_get_stats(self, client, sample_data):
        """Should return sample statistics."""
        response = await client.get("/api/v1/samples/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_samples"] == 3
        assert "by_source" in data
        assert "by_diagnosis" in data

    @pytest.mark.asyncio
    async def test_stats_by_source(self, client, sample_data):
        """Should show counts by source."""
        response = await client.get("/api/v1/samples/stats")
        
        data = response.json()
        by_source = {s["source_bank"]: s["count"] for s in data["by_source"]}
        
        assert by_source["NIH Miami"] == 2
        assert by_source["Harvard"] == 1


class TestSampleFilters:
    """Tests for GET /api/v1/samples/filters"""

    @pytest.mark.asyncio
    async def test_get_available_filters(self, client, sample_data):
        """Should return available filter options."""
        response = await client.get("/api/v1/samples/filters")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include lists of available values for filtering
        assert "source_banks" in data
        assert "diagnoses" in data
        assert "brain_regions" in data
        
        assert "NIH Miami" in data["source_banks"]
        assert "Harvard" in data["source_banks"]

