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
        "description": "Add a sample to the current selection by its ID. The sample must exist in the database.",
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
                }
            },
            "required": ["sample_id", "group"]
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
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.selection = SampleSelection()
    
    async def handle_tool_call(self, tool_name: str, tool_input: dict) -> str:
        """Route tool calls to appropriate handlers."""
        handlers = {
            "search_samples": self._search_samples,
            "get_current_selection": self._get_current_selection,
            "add_to_selection": self._add_to_selection,
            "remove_from_selection": self._remove_from_selection,
            "get_selection_statistics": self._get_selection_statistics,
            "clear_selection": self._clear_selection,
            "get_sample_details": self._get_sample_details,
            "get_database_statistics": self._get_database_statistics,
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
        
        # Require valid data for matching
        query = query.where(
            Sample.donor_age.isnot(None),
            Sample.rin_score.isnot(None),
            Sample.postmortem_interval_hours.isnot(None),
        )
        
        limit = params.get("limit", 20)
        query = query.limit(limit)
        
        result = await self.db_session.execute(query)
        samples = result.scalars().all()
        
        if not samples:
            return "No samples found matching the specified criteria."
        
        # Format results
        lines = [f"## Search Results\n\nFound {len(samples)} samples:\n"]
        
        for i, s in enumerate(samples, 1):
            rin_str = f"{float(s.rin_score):.1f}" if s.rin_score else "N/A"
            pmi_str = f"{float(s.postmortem_interval_hours):.1f}h" if s.postmortem_interval_hours else "N/A"
            braak = self._extract_braak(s)
            
            lines.append(f"{i}. **{s.external_id}**")
            lines.append(f"   - Repository: {s.source_bank or 'N/A'}")
            lines.append(f"   - Diagnosis: {s.primary_diagnosis or 'N/A'}")
            lines.append(f"   - Age: {s.donor_age or 'N/A'}, Sex: {s.donor_sex or 'N/A'}")
            lines.append(f"   - RIN: {rin_str}, PMI: {pmi_str}")
            if braak:
                lines.append(f"   - Braak Stage: {braak}")
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
        
        if not sample_id or not group:
            return "Error: sample_id and group are required."
        
        # Verify sample exists in database
        query = select(Sample).where(Sample.external_id == sample_id)
        result = await self.db_session.execute(query)
        sample = result.scalar_one_or_none()
        
        if not sample:
            return f"Error: Sample '{sample_id}' not found in database. Cannot add non-existent samples."
        
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
        )
        
        if group == "cases":
            if self.selection.add_case(selected):
                return f"Added {sample_id} to cases. Current selection: {len(self.selection.cases)} cases, {len(self.selection.controls)} controls."
            else:
                return f"Sample {sample_id} is already in cases."
        else:
            if self.selection.add_control(selected):
                return f"Added {sample_id} to controls. Current selection: {len(self.selection.cases)} cases, {len(self.selection.controls)} controls."
            else:
                return f"Sample {sample_id} is already in controls."
    
    async def _remove_from_selection(self, params: dict) -> str:
        """Remove a sample from the selection."""
        sample_id = params.get("sample_id")
        if not sample_id:
            return "Error: sample_id is required."
        
        if self.selection.remove(sample_id):
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
        """Extract Braak stage from extended_data if available."""
        if sample.extended_data:
            return sample.extended_data.get("braak_stage") or sample.extended_data.get("braak")
        return None

