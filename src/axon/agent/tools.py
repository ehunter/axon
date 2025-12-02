"""Tool definitions and handlers for the brain bank assistant.

These tools are the ONLY way Claude can access sample data.
This architectural constraint prevents hallucination.
"""

from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from axon.db.models import Sample
from axon.matching.matcher import SampleMatcher
from axon.matching.statistics import run_balance_tests
from axon.agent.icd_mapping import (
    extract_copathology_info,
    has_copathology,
    CopathologyInfo,
    COPATHOLOGY_CATEGORIES,
)


# Tool definitions for Anthropic API
TOOL_DEFINITIONS = [
    {
        "name": "search_samples",
        "description": "Search for brain tissue samples in the database. Use this to find samples matching specific criteria. Returns actual samples from the database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "diagnosis": {
                    "type": "string",
                    "description": "Disease/condition to search for (e.g., 'Alzheimer', 'Parkinson', 'control')"
                },
                "min_age": {
                    "type": "integer",
                    "description": "Minimum donor age"
                },
                "max_age": {
                    "type": "integer",
                    "description": "Maximum donor age"
                },
                "sex": {
                    "type": "string",
                    "enum": ["male", "female"],
                    "description": "Donor sex filter"
                },
                "brain_region": {
                    "type": "string",
                    "description": "Brain region (e.g., 'frontal', 'hippocampus', 'temporal')"
                },
                "min_rin": {
                    "type": "number",
                    "description": "Minimum RNA Integrity Number"
                },
                "max_pmi": {
                    "type": "number",
                    "description": "Maximum postmortem interval in hours"
                },
                "source_bank": {
                    "type": "string",
                    "description": "Filter by brain bank source"
                },
                "has_braak_data": {
                    "type": "boolean",
                    "description": "Only return samples that have Braak stage data available"
                },
                "min_braak_stage": {
                    "type": "integer",
                    "description": "Minimum Braak NFT stage (0-6). Samples must have Braak data to match."
                },
                "exclude_copathologies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Exclude samples with these co-pathology categories: Lewy, CAA, TDP-43, Vascular, FTD, ALS, Prion, Huntington, Stroke"
                },
                "require_no_copathologies": {
                    "type": "boolean",
                    "description": "Only return samples without any significant co-pathologies"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of samples to return (default 20)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_current_selection",
        "description": "Get the currently selected samples for this session. Returns the list of samples that have been added to the selection.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "add_to_selection",
        "description": "Add a sample to the current selection by its ID. The sample must exist in the database. If multiple tissue samples exist for the same subject, the one with best RIN is selected.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sample_id": {
                    "type": "string",
                    "description": "The external ID of the sample to add"
                },
                "group": {
                    "type": "string",
                    "enum": ["cases", "controls"],
                    "description": "Whether this is a case or control sample"
                },
                "brain_region": {
                    "type": "string",
                    "description": "Optional: filter by brain region if multiple samples exist for this subject"
                }
            },
            "required": ["sample_id", "group"]
        }
    },
    {
        "name": "add_samples_to_selection",
        "description": "Add multiple samples to the selection at once. More efficient than calling add_to_selection multiple times. Use this when recommending a set of samples to the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of external IDs for case samples to add"
                },
                "control_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of external IDs for control samples to add"
                }
            },
            "required": []
        }
    },
    {
        "name": "remove_from_selection",
        "description": "Remove a sample from the current selection by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sample_id": {
                    "type": "string",
                    "description": "The external ID of the sample to remove"
                }
            },
            "required": ["sample_id"]
        }
    },
    {
        "name": "get_selection_statistics",
        "description": "Get statistical summary of the current selection including age, PMI, RIN comparisons between cases and controls.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "clear_selection",
        "description": "Clear all samples from the current selection.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_sample_details",
        "description": "Get detailed information about a specific sample by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sample_id": {
                    "type": "string",
                    "description": "The external ID of the sample"
                }
            },
            "required": ["sample_id"]
        }
    },
    {
        "name": "get_database_statistics",
        "description": "Get aggregate statistics about the entire database (total samples, breakdown by diagnosis, source, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "stat_type": {
                    "type": "string",
                    "enum": ["total", "by_diagnosis", "by_source", "by_sex", "by_race"],
                    "description": "Type of statistics to retrieve"
                }
            },
            "required": ["stat_type"]
        }
    },
    {
        "name": "search_knowledge",
        "description": "Search the knowledge base for information about brain banking, tissue quality, experimental techniques, and neuroscience concepts. Use this to answer questions like 'What RIN is needed for RNA-seq?' or 'What is Braak staging?'",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for in the knowledge base"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default 3)"
                }
            },
            "required": ["query"]
        }
    }
]


@dataclass
class SelectedSample:
    """A sample that has been selected."""
    id: str
    external_id: str
    diagnosis: str | None
    age: int | None
    sex: str | None
    rin: float | None
    pmi: float | None
    brain_region: str | None
    source_bank: str | None
    braak_stage: str | None
    copathologies: str | None = None
    
    @property
    def repository(self) -> str | None:
        """Alias for source_bank for export compatibility."""
        return self.source_bank


@dataclass
class SampleSelection:
    """Server-side storage for selected samples.
    
    This ensures Claude cannot fabricate samples - it can only
    work with samples that have been verified against the database.
    """
    cases: list[SelectedSample] = field(default_factory=list)
    controls: list[SelectedSample] = field(default_factory=list)
    
    def add_case(self, sample: SelectedSample) -> bool:
        """Add a case sample to the selection."""
        if not any(s.external_id == sample.external_id for s in self.cases):
            self.cases.append(sample)
            return True
        return False
    
    def add_control(self, sample: SelectedSample) -> bool:
        """Add a control sample to the selection."""
        if not any(s.external_id == sample.external_id for s in self.controls):
            self.controls.append(sample)
            return True
        return False
    
    def remove(self, sample_id: str) -> bool:
        """Remove a sample from the selection."""
        for i, s in enumerate(self.cases):
            if s.external_id == sample_id:
                self.cases.pop(i)
                return True
        for i, s in enumerate(self.controls):
            if s.external_id == sample_id:
                self.controls.pop(i)
                return True
        return False
    
    def clear(self) -> None:
        """Clear all selections."""
        self.cases.clear()
        self.controls.clear()
    
    def get_all_ids(self) -> set[str]:
        """Get all selected sample IDs."""
        return {s.external_id for s in self.cases} | {s.external_id for s in self.controls}
    
    def to_summary(self) -> str:
        """Generate a summary of the current selection."""
        if not self.cases and not self.controls:
            return "No samples currently selected."
        
        lines = ["## Current Sample Selection\n"]
        
        if self.cases:
            lines.append(f"**Cases ({len(self.cases)}):**\n")
            for s in self.cases:
                rin_str = f"{s.rin:.1f}" if s.rin else "N/A"
                pmi_str = f"{s.pmi:.1f}h" if s.pmi else "N/A"
                braak_str = f", Braak {s.braak_stage}" if s.braak_stage else ""
                lines.append(f"- **{s.external_id}** | Repository: {s.source_bank} | {s.diagnosis} | Age {s.age}, {s.sex} | RIN {rin_str}, PMI {pmi_str}{braak_str}")
        
        if self.controls:
            lines.append(f"\n**Controls ({len(self.controls)}):**\n")
            for s in self.controls:
                rin_str = f"{s.rin:.1f}" if s.rin else "N/A"
                pmi_str = f"{s.pmi:.1f}h" if s.pmi else "N/A"
                lines.append(f"- **{s.external_id}** | Repository: {s.source_bank} | Age {s.age}, {s.sex} | RIN {rin_str}, PMI {pmi_str}")
        
        return "\n".join(lines)


class ToolHandler:
    """Handles tool calls from Claude.
    
    All data access goes through these methods, ensuring
    Claude can only present data that actually exists.
    """
    
    def __init__(
        self, 
        db_session: AsyncSession,
        embedding_api_key: str | None = None,
        persistence_service: "ConversationService | None" = None,
        conversation_id: str | None = None,
    ):
        self.db_session = db_session
        self.selection = SampleSelection()
        self.persistence_service = persistence_service
        self.conversation_id = conversation_id
        
        # Initialize RAG retriever for knowledge search if API key provided
        self.retriever = None
        if embedding_api_key:
            from axon.rag.retrieval import RAGRetriever
            self.retriever = RAGRetriever(db_session, embedding_api_key)
    
    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Route tool calls to appropriate handlers."""
        handlers = {
            "search_samples": self._search_samples,
            "get_current_selection": self._get_current_selection,
            "add_to_selection": self._add_to_selection,
            "add_samples_to_selection": self._add_samples_to_selection,
            "remove_from_selection": self._remove_from_selection,
            "get_selection_statistics": self._get_selection_statistics,
            "clear_selection": self._clear_selection,
            "get_sample_details": self._get_sample_details,
            "get_database_statistics": self._get_database_statistics,
            "search_knowledge": self._search_knowledge,
        }
        
        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown tool '{tool_name}'"
        
        try:
            return await handler(tool_input)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    async def _search_samples(self, params: dict) -> str:
        """Search for samples in the database."""
        query = select(Sample)
        
        # Apply filters
        if params.get("diagnosis"):
            diagnosis = params["diagnosis"]
            if diagnosis.lower() == "control":
                query = query.where(or_(
                    Sample.primary_diagnosis.ilike("%control%"),
                    Sample.primary_diagnosis.ilike("%normal%"),
                    Sample.primary_diagnosis.ilike("%no clinical%"),
                ))
            else:
                query = query.where(Sample.primary_diagnosis.ilike(f"%{diagnosis}%"))
        
        if params.get("min_age"):
            query = query.where(Sample.donor_age >= params["min_age"])
        
        if params.get("max_age"):
            query = query.where(Sample.donor_age <= params["max_age"])
        
        if params.get("sex"):
            query = query.where(Sample.donor_sex.ilike(f"%{params['sex']}%"))
        
        if params.get("brain_region"):
            query = query.where(Sample.brain_region.ilike(f"%{params['brain_region']}%"))
        
        if params.get("min_rin"):
            query = query.where(Sample.rin_score >= params["min_rin"])
        
        if params.get("max_pmi"):
            query = query.where(Sample.postmortem_interval_hours <= params["max_pmi"])
        
        if params.get("source_bank"):
            query = query.where(Sample.source_bank.ilike(f"%{params['source_bank']}%"))
        
        # Require valid data for matching (age is always required)
        query = query.where(Sample.donor_age.isnot(None))
        
        # If filtering by Braak, relax RIN/PMI requirements since Mt. Sinai has Braak but no RIN
        braak_filter = params.get("has_braak_data") or params.get("min_braak_stage") is not None
        
        if not braak_filter:
            # For regular searches, require RIN and PMI for quality matching
            query = query.where(
                Sample.rin_score.isnot(None),
                Sample.postmortem_interval_hours.isnot(None),
            )
        
        limit = params.get("limit", 20)
        
        # Fetch more samples if we'll be filtering by Braak or co-pathologies
        copath_filter = params.get("exclude_copathologies") or params.get("require_no_copathologies")
        if braak_filter or copath_filter:
            query = query.limit(500)  # Fetch more to filter
        else:
            query = query.limit(limit)
        
        result = await self.db_session.execute(query)
        samples = result.scalars().all()
        
        # Post-filter for Braak stage if requested (JSONB filtering is complex, do it in Python)
        if braak_filter:
            filtered_samples = []
            min_stage = params.get("min_braak_stage", 0)
            
            for s in samples:
                braak_str = self._extract_braak(s)
                if braak_str:
                    # Extract numeric stage from strings like "NFT Stage VI (B3)" or "Stage III (B2)"
                    stage_num = self._parse_braak_stage_number(braak_str)
                    if stage_num is not None and stage_num >= min_stage:
                        filtered_samples.append(s)
            
            samples = filtered_samples
            
            if not samples:
                return f"No samples found with Braak stage data{' >= ' + str(min_stage) if min_stage > 0 else ''}. Try searching Mt. Sinai samples which have better Braak staging data."
        
        # Post-filter for co-pathology exclusions
        exclude_copaths = params.get("exclude_copathologies")
        require_no_copaths = params.get("require_no_copathologies", False)
        
        if exclude_copaths or require_no_copaths:
            filtered_samples = []
            excluded_count = 0
            
            for s in samples:
                if not self._sample_has_excluded_copathologies(s, exclude_copaths, require_no_copaths):
                    filtered_samples.append(s)
                else:
                    excluded_count += 1
            
            samples = filtered_samples
            
            if not samples:
                filter_desc = "without co-pathologies" if require_no_copaths else f"excluding {', '.join(exclude_copaths)}"
                return f"No samples found {filter_desc}. {excluded_count} samples were excluded due to co-pathologies. Consider relaxing co-pathology requirements."
        
        # Apply limit after all filtering
        samples = samples[:limit]
        
        if not samples:
            return "No samples found matching the specified criteria."
        
        # Format results
        lines = [f"## Search Results\n\nFound {len(samples)} samples:\n"]
        
        for i, s in enumerate(samples, 1):
            rin_str = f"{float(s.rin_score):.1f}" if s.rin_score else "N/A"
            pmi_str = f"{float(s.postmortem_interval_hours):.1f}h" if s.postmortem_interval_hours else "N/A"
            braak = self._extract_braak(s)
            copathologies = self._extract_copathologies(s)
            
            lines.append(f"{i}. **{s.external_id}**")
            lines.append(f"   - Repository: {s.source_bank or 'N/A'}")
            lines.append(f"   - Diagnosis: {s.primary_diagnosis or 'N/A'}")
            lines.append(f"   - Age: {s.donor_age or 'N/A'}, Sex: {s.donor_sex or 'N/A'}")
            lines.append(f"   - RIN: {rin_str}, PMI: {pmi_str}")
            if braak:
                lines.append(f"   - Braak Stage: {braak}")
            lines.append(f"   - Co-pathologies: {copathologies}")
            lines.append(f"   - Brain Region: {s.brain_region or 'N/A'}")
            lines.append("")
        
        return "\n".join(lines)
    
    async def _get_current_selection(self, params: dict) -> str:
        """Get the current sample selection."""
        return self.selection.to_summary()
    
    async def _add_to_selection(self, params: dict) -> str:
        """Add a sample to the selection."""
        sample_id = params.get("sample_id")
        group = params.get("group")
        brain_region = params.get("brain_region")  # Optional filter
        
        if not sample_id or not group:
            return "Error: sample_id and group are required."
        
        # Verify sample exists in database
        query = select(Sample).where(Sample.external_id == sample_id)
        
        # If brain region specified, filter by it
        if brain_region:
            query = query.where(Sample.brain_region.ilike(f"%{brain_region}%"))
        
        # Also prefer samples with RIN data for quality
        query = query.order_by(Sample.rin_score.desc().nullslast())
        
        result = await self.db_session.execute(query)
        samples = result.scalars().all()
        
        if not samples:
            return f"Error: Sample '{sample_id}' not found in database. Cannot add non-existent samples."
        
        # If multiple matches, take the best one (highest RIN) and note it
        sample = samples[0]
        multiple_note = ""
        if len(samples) > 1:
            multiple_note = f" (Note: {len(samples)} tissue samples exist for this subject; selected the one with best RIN)"
        
        # Create selected sample
        selected = SelectedSample(
            id=sample.id,
            external_id=sample.external_id,
            diagnosis=sample.primary_diagnosis,
            age=sample.donor_age,
            sex=sample.donor_sex,
            rin=float(sample.rin_score) if sample.rin_score else None,
            pmi=float(sample.postmortem_interval_hours) if sample.postmortem_interval_hours else None,
            brain_region=sample.brain_region,
            source_bank=sample.source_bank,
            braak_stage=self._extract_braak(sample),
            copathologies=self._extract_copathologies(sample),
        )
        
        if group == "cases":
            if self.selection.add_case(selected):
                # Persist to database if persistence is enabled
                await self._persist_sample_add(selected, "case")
                return f"Added {sample_id} to cases.{multiple_note} Current selection: {len(self.selection.cases)} cases, {len(self.selection.controls)} controls."
            else:
                return f"Sample {sample_id} is already in cases."
        else:
            if self.selection.add_control(selected):
                # Persist to database if persistence is enabled
                await self._persist_sample_add(selected, "control")
                return f"Added {sample_id} to controls.{multiple_note} Current selection: {len(self.selection.cases)} cases, {len(self.selection.controls)} controls."
            else:
                return f"Sample {sample_id} is already in controls."
    
    async def _add_samples_to_selection(self, params: dict) -> str:
        """Add multiple samples to the selection at once."""
        case_ids = params.get("case_ids", [])
        control_ids = params.get("control_ids", [])
        
        if not case_ids and not control_ids:
            return "Error: Please provide case_ids and/or control_ids."
        
        added_cases = []
        added_controls = []
        failed = []
        
        # Add cases
        for sample_id in case_ids:
            result = await self._add_single_sample(sample_id, "cases")
            if result["success"]:
                added_cases.append(sample_id)
            else:
                failed.append(f"{sample_id}: {result['error']}")
        
        # Add controls
        for sample_id in control_ids:
            result = await self._add_single_sample(sample_id, "controls")
            if result["success"]:
                added_controls.append(sample_id)
            else:
                failed.append(f"{sample_id}: {result['error']}")
        
        # Build response
        lines = ["## Samples Added to Selection\n"]
        
        if added_cases:
            lines.append(f"**Cases added:** {len(added_cases)} ({', '.join(added_cases)})")
        if added_controls:
            lines.append(f"**Controls added:** {len(added_controls)} ({', '.join(added_controls)})")
        
        lines.append(f"\n**Current selection:** {len(self.selection.cases)} cases, {len(self.selection.controls)} controls")
        
        if failed:
            lines.append(f"\n**Failed to add:** {len(failed)}")
            for f in failed[:5]:  # Show first 5 failures
                lines.append(f"  - {f}")
        
        return "\n".join(lines)
    
    async def _add_single_sample(self, sample_id: str, group: str) -> dict:
        """Helper to add a single sample without returning a string."""
        # Verify sample exists in database
        query = select(Sample).where(Sample.external_id == sample_id)
        query = query.order_by(Sample.rin_score.desc().nullslast())
        
        result = await self.db_session.execute(query)
        samples = result.scalars().all()
        
        if not samples:
            return {"success": False, "error": "not found"}
        
        sample = samples[0]
        
        selected = SelectedSample(
            id=sample.id,
            external_id=sample.external_id,
            diagnosis=sample.primary_diagnosis,
            age=sample.donor_age,
            sex=sample.donor_sex,
            rin=float(sample.rin_score) if sample.rin_score else None,
            pmi=float(sample.postmortem_interval_hours) if sample.postmortem_interval_hours else None,
            brain_region=sample.brain_region,
            source_bank=sample.source_bank,
            braak_stage=self._extract_braak(sample),
            copathologies=self._extract_copathologies(sample),
        )
        
        if group == "cases":
            if self.selection.add_case(selected):
                await self._persist_sample_add(selected, "case")
                return {"success": True}
            return {"success": False, "error": "already in cases"}
        else:
            if self.selection.add_control(selected):
                await self._persist_sample_add(selected, "control")
                return {"success": True}
            return {"success": False, "error": "already in controls"}
    
    async def _remove_from_selection(self, params: dict) -> str:
        """Remove a sample from the selection."""
        sample_id = params.get("sample_id")
        if not sample_id:
            return "Error: sample_id is required."
        
        if self.selection.remove(sample_id):
            # Persist removal to database if persistence is enabled
            await self._persist_sample_remove(sample_id)
            return f"Removed {sample_id}. Current selection: {len(self.selection.cases)} cases, {len(self.selection.controls)} controls."
        else:
            return f"Sample {sample_id} was not in the selection."
    
    async def _get_selection_statistics(self, params: dict) -> str:
        """Get statistics for the current selection."""
        if not self.selection.cases and not self.selection.controls:
            return "No samples selected. Add samples first to see statistics."
        
        # Convert to dicts for statistics
        case_dicts = [
            {"age": s.age, "pmi": s.pmi, "rin": s.rin}
            for s in self.selection.cases if s.age and s.pmi and s.rin
        ]
        control_dicts = [
            {"age": s.age, "pmi": s.pmi, "rin": s.rin}
            for s in self.selection.controls if s.age and s.pmi and s.rin
        ]
        
        lines = ["## Selection Statistics\n"]
        lines.append(f"- **Cases:** {len(self.selection.cases)}")
        lines.append(f"- **Controls:** {len(self.selection.controls)}")
        
        if case_dicts and control_dicts:
            report = run_balance_tests(case_dicts, control_dicts)
            lines.append(f"\n{report.to_summary()}")
        elif case_dicts:
            # Just case statistics
            ages = [d["age"] for d in case_dicts]
            rins = [d["rin"] for d in case_dicts]
            pmis = [d["pmi"] for d in case_dicts]
            lines.append(f"\n**Case Statistics:**")
            lines.append(f"- Age: {sum(ages)/len(ages):.1f} (range {min(ages)}-{max(ages)})")
            lines.append(f"- RIN: {sum(rins)/len(rins):.1f} (range {min(rins):.1f}-{max(rins):.1f})")
            lines.append(f"- PMI: {sum(pmis)/len(pmis):.1f}h (range {min(pmis):.1f}-{max(pmis):.1f})")
        
        return "\n".join(lines)
    
    async def _clear_selection(self, params: dict) -> str:
        """Clear the current selection."""
        self.selection.clear()
        # Persist to database if persistence is enabled
        await self._persist_selection_clear()
        return "Selection cleared. No samples currently selected."
    
    async def _get_sample_details(self, params: dict) -> str:
        """Get details for a specific sample."""
        sample_id = params.get("sample_id")
        if not sample_id:
            return "Error: sample_id is required."
        
        query = select(Sample).where(Sample.external_id == sample_id)
        result = await self.db_session.execute(query)
        sample = result.scalar_one_or_none()
        
        if not sample:
            return f"Sample '{sample_id}' not found in database."
        
        rin_str = f"{float(sample.rin_score):.1f}" if sample.rin_score else "Not available"
        pmi_str = f"{float(sample.postmortem_interval_hours):.1f}h" if sample.postmortem_interval_hours else "Not available"
        braak = self._extract_braak(sample) or "Not available"
        copathologies = self._extract_copathologies(sample)
        
        lines = [
            f"## Sample Details: {sample.external_id}\n",
            f"- **Source:** {sample.source_bank or 'Not available'}",
            f"- **Diagnosis:** {sample.primary_diagnosis or 'Not available'}",
            f"- **Age:** {sample.donor_age or 'Not available'}",
            f"- **Sex:** {sample.donor_sex or 'Not available'}",
            f"- **Race:** {sample.donor_race or 'Not available'}",
            f"- **RIN:** {rin_str}",
            f"- **PMI:** {pmi_str}",
            f"- **Brain Region:** {sample.brain_region or 'Not available'}",
            f"- **Braak Stage:** {braak}",
            f"- **Co-pathologies:** {copathologies}",
        ]
        
        return "\n".join(lines)
    
    async def _get_database_statistics(self, params: dict) -> str:
        """Get aggregate database statistics."""
        stat_type = params.get("stat_type", "total")
        
        if stat_type == "total":
            query = select(func.count(Sample.id))
            result = await self.db_session.execute(query)
            total = result.scalar()
            return f"**Total samples in database:** {total:,}"
        
        elif stat_type == "by_diagnosis":
            query = (
                select(Sample.primary_diagnosis, func.count(Sample.id).label("count"))
                .where(Sample.primary_diagnosis.isnot(None))
                .group_by(Sample.primary_diagnosis)
                .order_by(func.count(Sample.id).desc())
                .limit(20)
            )
            result = await self.db_session.execute(query)
            
            lines = ["**Top Diagnoses:**\n"]
            for row in result:
                lines.append(f"- {row.primary_diagnosis}: {row.count:,}")
            return "\n".join(lines)
        
        elif stat_type == "by_source":
            query = (
                select(Sample.source_bank, func.count(Sample.id).label("count"))
                .where(Sample.source_bank.isnot(None))
                .group_by(Sample.source_bank)
                .order_by(func.count(Sample.id).desc())
            )
            result = await self.db_session.execute(query)
            
            lines = ["**Samples by Source Bank:**\n"]
            for row in result:
                lines.append(f"- {row.source_bank}: {row.count:,}")
            return "\n".join(lines)
        
        elif stat_type == "by_sex":
            query = (
                select(Sample.donor_sex, func.count(Sample.id).label("count"))
                .where(Sample.donor_sex.isnot(None))
                .group_by(Sample.donor_sex)
            )
            result = await self.db_session.execute(query)
            
            lines = ["**Samples by Sex:**\n"]
            for row in result:
                lines.append(f"- {row.donor_sex}: {row.count:,}")
            return "\n".join(lines)
        
        elif stat_type == "by_race":
            query = (
                select(Sample.donor_race, func.count(Sample.id).label("count"))
                .where(Sample.donor_race.isnot(None))
                .group_by(Sample.donor_race)
                .order_by(func.count(Sample.id).desc())
            )
            result = await self.db_session.execute(query)
            
            lines = ["**Samples by Race:**\n"]
            for row in result:
                lines.append(f"- {row.donor_race}: {row.count:,}")
            return "\n".join(lines)
        
        return f"Unknown stat_type: {stat_type}"
    
    def _extract_braak(self, sample: Sample) -> str | None:
        """Extract Braak stage from raw_data if available."""
        if not sample.raw_data:
            return None
        
        # Check for Braak NFT Stage (Alzheimer's)
        braak_nft = sample.raw_data.get("Braak NFT Stage")
        if braak_nft and braak_nft not in ("No Results Reported", "Not Assessed", ""):
            return f"NFT {braak_nft}"
        
        # Check for Braak PD Stage (Parkinson's)
        braak_pd = sample.raw_data.get("Braak PD Stage")
        if braak_pd and braak_pd not in ("No Results Reported", "Not Assessed", "", "PD Stage 0"):
            return f"PD {braak_pd}"
        
        # Also check extended_data as fallback
        if sample.extended_data:
            return sample.extended_data.get("braak_stage") or sample.extended_data.get("braak")
        
        return None
    
    def _parse_braak_stage_number(self, braak_str: str) -> int | None:
        """Parse numeric Braak stage from strings like 'NFT Stage VI (B3)' or 'Stage III (B2)'."""
        if not braak_str:
            return None
        
        import re
        braak_upper = braak_str.upper()
        
        # Try to find Roman numeral stage patterns
        # Order matters: check longer patterns first (VI before V, III before II before I)
        stage_match = re.search(r'STAGE\s+(VI|IV|V|III|II|I|0)', braak_upper)
        if stage_match:
            roman = stage_match.group(1)
            roman_to_int = {'0': 0, 'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
            return roman_to_int.get(roman)
        
        # Try PD stage patterns like "PD Stage 4"
        pd_match = re.search(r'PD\s+STAGE\s+(\d)', braak_upper)
        if pd_match:
            return int(pd_match.group(1))
        
        return None
    
    def _extract_copathologies(self, sample: Sample) -> str:
        """Extract co-pathology information using ICD codes and neuropathology metrics.
        
        Uses NIH NeuroBioBank ICD-10 categorization system.
        """
        copath_info = self._get_copathology_info(sample)
        return copath_info.summary
    
    def _get_copathology_info(self, sample: Sample) -> CopathologyInfo:
        """Get structured co-pathology information for a sample."""
        return extract_copathology_info(
            sample_raw_data=sample.raw_data,
            sample_extended_data=sample.extended_data,
            primary_diagnosis_code=sample.primary_diagnosis_code,
        )
    
    def _sample_has_excluded_copathologies(
        self, 
        sample: Sample, 
        exclude_categories: list[str] | None,
        require_no_copathologies: bool = False,
    ) -> bool:
        """Check if sample should be excluded based on co-pathology filters."""
        copath_info = self._get_copathology_info(sample)
        
        if require_no_copathologies:
            # Check if sample has ANY significant co-pathology
            return has_copathology(copath_info, list(COPATHOLOGY_CATEGORIES))
        
        if exclude_categories:
            return has_copathology(copath_info, exclude_categories)
        
        return False
    
    async def _search_knowledge(self, params: dict) -> str:
        """Search the knowledge base for relevant information.
        
        Args:
            params: dict with 'query' (required) and 'limit' (optional)
            
        Returns:
            Formatted string with relevant knowledge chunks
        """
        query = params.get("query")
        if not query:
            return "Error: query parameter is required."
        
        # Check if retriever is available
        if not self.retriever:
            return "Knowledge search is not configured. The embedding API key was not provided."
        
        limit = params.get("limit", 3)
        
        try:
            results = await self.retriever.retrieve_knowledge(
                query=query,
                limit=limit,
            )
        except Exception as e:
            return f"Error searching knowledge base: {str(e)}"
        
        if not results:
            return f"No relevant information found for: '{query}'. Try rephrasing your question or ask about brain banking, tissue quality, or neuroscience concepts."
        
        # Format results
        lines = [f"## Knowledge Base Results\n\nFound {len(results)} relevant items for: '{query}'\n"]
        
        for i, item in enumerate(results, 1):
            lines.append(f"### Reference {i}")
            if item.document_title:
                lines.append(f"**Source:** {item.source_name} - {item.document_title}")
            else:
                lines.append(f"**Source:** {item.source_name}")
            
            if item.chunk.section_title:
                lines.append(f"**Section:** {item.chunk.section_title}")
            
            lines.append(f"**Relevance:** {item.score:.0%}")
            lines.append("")
            lines.append(item.chunk.content)
            lines.append("")
        
        return "\n".join(lines)
    
    # === Selection Persistence Methods ===
    
    async def _persist_sample_add(self, sample: SelectedSample, group: str) -> None:
        """Persist a sample addition to the database.
        
        Silently handles errors to avoid breaking the main flow if
        the conversation_samples table doesn't exist or there's a DB issue.
        """
        if not self.persistence_service or not self.conversation_id:
            return
        
        try:
            await self.persistence_service.save_sample_to_selection(
                conversation_id=self.conversation_id,
                sample_external_id=sample.external_id,
                sample_group=group,
                diagnosis=sample.diagnosis,
                age=sample.age,
                sex=sample.sex,
                source_bank=sample.source_bank,
            )
        except Exception as e:
            # Log but don't fail - selection persistence is non-critical
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist sample add: {e}")
            # Rollback to clear the failed transaction
            try:
                await self.db_session.rollback()
            except Exception:
                pass
    
    async def _persist_sample_remove(self, sample_external_id: str) -> None:
        """Persist a sample removal to the database.
        
        Silently handles errors to avoid breaking the main flow.
        """
        if not self.persistence_service or not self.conversation_id:
            return
        
        try:
            await self.persistence_service.remove_sample_from_selection(
                conversation_id=self.conversation_id,
                sample_external_id=sample_external_id,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist sample remove: {e}")
            try:
                await self.db_session.rollback()
            except Exception:
                pass
    
    async def _persist_selection_clear(self) -> None:
        """Persist clearing the selection to the database.
        
        Silently handles errors to avoid breaking the main flow.
        """
        if not self.persistence_service or not self.conversation_id:
            return
        
        try:
            await self.persistence_service.clear_selection(self.conversation_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist selection clear: {e}")
            try:
                await self.db_session.rollback()
            except Exception:
                pass
    
    async def load_selection_from_db(self) -> None:
        """Load the sample selection from the database.
        
        Call this after setting conversation_id to restore a previous session's selection.
        Silently handles errors if the table doesn't exist.
        """
        if not self.persistence_service or not self.conversation_id:
            return
        
        try:
            self.selection = await self.persistence_service.load_selection(
                self.conversation_id
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to load selection from DB: {e}")
            try:
                await self.db_session.rollback()
            except Exception:
                pass

