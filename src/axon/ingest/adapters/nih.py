"""NIH NeuroBioBank CSV adapter.

This adapter handles importing brain tissue sample data from the NIH
NeuroBioBank CSV export format. It normalizes the data to our schema
and handles the various quirks of the NIH data format.
"""

import csv
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterator


# NIH repository sites that should be prefixed with "NIH"
NIH_SITES = {
    "Miami",
    "Maryland",
    "Sepulveda",
    "Pittsburgh",
    "HBCC",
    "Maryland Psychiatric",
    "ADRC",
}

# Non-NIH brain banks (keep original names)
INDEPENDENT_BANKS = {
    "Harvard",
    "Mt. Sinai",
}

# RIN placeholder values that mean "not reported"
RIN_PLACEHOLDERS = {"99.99", "99.99, 99.99", "No Test Results Reported", ""}

# Neuropathology score columns
NEUROPATH_SCORE_COLUMNS = [
    ("Thal Phase", "thal_phase"),
    ("Thal Value", "thal_value"),
    ("Braak NFT Stage", "braak_nft_stage"),
    ("Braak NFT Value", "braak_nft_value"),
    ("CERAD Score", "cerad_score"),
    ("CERAD Value", "cerad_value"),
    ("A Score", "a_score"),
    ("A Score Value", "a_score_value"),
    ("B Score", "b_score"),
    ("B Score Value", "b_score_value"),
    ("C Score", "c_score"),
    ("C Score Value", "c_score_value"),
    ("ADNC", "adnc"),
    ("ADNC Value", "adnc_value"),
    ("Lewy Pathology", "lewy_pathology"),
    ("Lewy Pathology Value", "lewy_pathology_value"),
    ("Braak PD Stage", "braak_pd_stage"),
    ("Braak PD Value", "braak_pd_value"),
    ("Small Vessel Disease Severity", "small_vessel_disease"),
    ("Small Vessel Disease Value", "small_vessel_disease_value"),
    ("CAA Severity", "caa_severity"),
    ("CAA Value", "caa_value"),
    ("CAA, VonSattel Grade", "caa_vonsattel_grade"),
    ("CAA, VonSattel Value", "caa_vonsattel_value"),
    ("TDP-43 Proteinopathy", "tdp43_proteinopathy"),
    ("TDP-43 Proteinopathy Value", "tdp43_proteinopathy_value"),
    ("LATE-NC", "late_nc"),
    ("LATE-NC Value", "late_nc_value"),
    ("ALS-TDP", "als_tdp"),
    ("ALS-TDP Value", "als_tdp_value"),
    ("HD, VonSattel Grade", "hd_vonsattel_grade"),
    ("HD, VonSattel Value", "hd_vonsattel_value"),
]


@dataclass
class NIHRecord:
    """Parsed record from NIH CSV."""

    subject_id: str
    repository: str
    age: int | None
    sex: str | None
    race: str | None
    ethnicity: str | None
    clinical_diagnosis: str | None
    clinical_diagnosis_code: str | None
    neuropathology_diagnosis: str | None
    neuropathology_diagnosis_code: str | None
    brain_region: str | None
    hemisphere: str | None
    pmi_hours: Decimal | None
    rin_score: Decimal | None
    preservation_method: str | None
    manner_of_death: str | None
    genetic_diagnosis: str | None
    neuropathology_scores: dict[str, Any]
    raw_data: dict[str, Any]


class NIHAdapter:
    """Adapter for importing NIH NeuroBioBank CSV data."""

    def normalize_repository(self, repository: str) -> str:
        """Normalize repository name with NIH prefix where appropriate."""
        if not repository:
            return ""
        
        repo = repository.strip()
        
        if repo in NIH_SITES:
            return f"NIH {repo}"
        elif repo in INDEPENDENT_BANKS:
            return repo
        else:
            # Unknown repository - prefix with NIH to be safe
            return f"NIH {repo}"

    def parse_rin(self, value: str) -> Decimal | None:
        """Parse RIN score, handling placeholder values."""
        if not value or value.strip() in RIN_PLACEHOLDERS:
            return None
        
        # Handle "99.99, 99.99" format
        if "99.99" in value:
            return None
        
        try:
            return Decimal(value.strip())
        except InvalidOperation:
            return None

    def parse_pmi(self, value: str) -> Decimal | None:
        """Parse postmortem interval hours."""
        if not value or value.strip() in {"", "Not Reported"}:
            return None
        
        try:
            return Decimal(value.strip())
        except InvalidOperation:
            return None

    def parse_age(self, value: str) -> int | None:
        """Parse subject age."""
        if not value or value.strip() in {"", "Unknown", "Not Reported"}:
            return None
        
        try:
            return int(float(value.strip()))
        except (ValueError, TypeError):
            return None

    def parse_sex(self, value: str) -> str | None:
        """Normalize sex values to lowercase."""
        if not value:
            return None
        
        val = value.strip().lower()
        
        if val in {"male", "m"}:
            return "male"
        elif val in {"female", "f"}:
            return "female"
        elif val in {"other"}:
            return "other"
        elif val in {"unknown", "not reported", ""}:
            return None
        
        return None

    def parse_brain_regions(self, value: str) -> str | None:
        """Parse brain regions (kept as comma-separated string)."""
        if not value or value.strip() == "":
            return None
        return value.strip()

    def parse_hemisphere(self, value: str) -> str | None:
        """Parse hemisphere information."""
        if not value or value.strip() == "":
            return None
        
        val = value.strip().lower()
        
        if "left" in val and "right" in val:
            return "both"
        elif "left" in val:
            return "left"
        elif "right" in val:
            return "right"
        
        return None

    def parse_preservation(self, value: str) -> str | None:
        """Parse preparation/preservation method."""
        if not value or value.strip() == "":
            return None
        return value.strip()

    def parse_diagnosis(self, value: str) -> dict[str, str | None]:
        """Extract diagnosis and basis from combined field.
        
        Format: "Diagnosis text (Basis for diagnosis)"
        """
        if not value or value.strip() == "":
            return {"diagnosis": None, "basis": None}
        
        val = value.strip()
        
        # Try to extract basis in parentheses at the end
        match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", val)
        if match:
            return {
                "diagnosis": match.group(1).strip(),
                "basis": match.group(2).strip(),
            }
        
        return {"diagnosis": val, "basis": None}

    def parse_neuropathology_scores(self, row: dict[str, Any]) -> dict[str, Any]:
        """Extract neuropathology scores from row."""
        scores = {}
        
        for csv_col, field_name in NEUROPATH_SCORE_COLUMNS:
            value = row.get(csv_col, "")
            if value and value.strip() not in {"", "No Results Reported"}:
                scores[field_name] = value.strip()
        
        return scores

    def should_include(self, row: dict[str, Any]) -> bool:
        """Check if row should be included in import."""
        # Skip rows without Subject ID
        subject_id = row.get("Subject ID")
        if not subject_id or str(subject_id).strip() == "":
            return False
        
        # Skip non-brain tissue rows
        tissue_source = row.get("Tissue Source", "")
        if tissue_source and "Non-Brain" in str(tissue_source):
            return False
        
        return True

    def validate(self, row: dict[str, Any]) -> list[str]:
        """Validate row data and return list of errors."""
        errors = []
        
        # Required fields
        if not row.get("Subject ID"):
            errors.append("Missing required field: Subject ID")
        
        if not row.get("Repository"):
            errors.append("Missing required field: Repository")
        
        # Age range validation
        age_str = row.get("Subject Age", "")
        if age_str:
            age = self.parse_age(age_str)
            if age is not None and (age < 0 or age > 120):
                errors.append(f"Age out of valid range (0-120): {age}")
        
        return errors

    def parse_row(self, row: dict[str, Any]) -> NIHRecord:
        """Parse a CSV row into NIHRecord."""
        diag = self.parse_diagnosis(
            row.get("Clinical Brain Diagnosis (Basis for Clinical Diagnosis)", "")
        )
        
        return NIHRecord(
            subject_id=str(row.get("Subject ID", "")).strip(),
            repository=str(row.get("Repository", "")).strip(),
            age=self.parse_age(row.get("Subject Age", "")),
            sex=self.parse_sex(row.get("Subject Sex", "")),
            race=row.get("Race", "").strip() or None,
            ethnicity=row.get("Ethnicity", "").strip() or None,
            clinical_diagnosis=diag["diagnosis"],
            clinical_diagnosis_code=row.get("ICD for Clinical Brain Diagnosis", "").strip() or None,
            neuropathology_diagnosis=row.get("Neuropathology Diagnosis", "").strip() or None,
            neuropathology_diagnosis_code=row.get("ICD for Neuropathology Diagnosis", "").strip() or None,
            brain_region=self.parse_brain_regions(row.get("Brain Region", "")),
            hemisphere=self.parse_hemisphere(row.get("Brain Hemisphere", "")),
            pmi_hours=self.parse_pmi(row.get("PMI (hours)", "")),
            rin_score=self.parse_rin(row.get("RIN", "")),
            preservation_method=self.parse_preservation(row.get("Preparation", "")),
            manner_of_death=row.get("Manner of Death", "").strip() or None,
            genetic_diagnosis=row.get("Genetic Diagnosis", "").strip() or None,
            neuropathology_scores=self.parse_neuropathology_scores(row),
            raw_data=dict(row),
        )

    def to_sample_dict(self, row: dict[str, Any]) -> dict[str, Any]:
        """Convert a CSV row to a dict suitable for Sample model."""
        record = self.parse_row(row)
        
        # Build extended_data with neuropathology info
        extended_data: dict[str, Any] = {}
        
        if record.neuropathology_scores:
            extended_data["neuropathology_scores"] = record.neuropathology_scores
        
        if record.neuropathology_diagnosis:
            extended_data["neuropathology_diagnosis"] = record.neuropathology_diagnosis
        
        if record.neuropathology_diagnosis_code:
            extended_data["neuropathology_diagnosis_code"] = record.neuropathology_diagnosis_code
        
        if record.genetic_diagnosis and record.genetic_diagnosis != "None Reported":
            extended_data["genetic_diagnosis"] = record.genetic_diagnosis
        
        # Build searchable text for full-text search
        searchable_parts = [
            record.subject_id,
            record.clinical_diagnosis,
            record.neuropathology_diagnosis,
            record.brain_region,
            str(record.age) if record.age else None,
            record.sex,
            record.race,
        ]
        searchable_text = " ".join(p for p in searchable_parts if p)
        
        return {
            "source_bank": self.normalize_repository(record.repository),
            "external_id": record.subject_id,
            "donor_age": record.age,
            "donor_sex": record.sex,
            "donor_race": record.race,
            "donor_ethnicity": record.ethnicity,
            "primary_diagnosis": record.clinical_diagnosis,
            "primary_diagnosis_code": record.clinical_diagnosis_code,
            "brain_region": record.brain_region,
            "hemisphere": record.hemisphere,
            "postmortem_interval_hours": record.pmi_hours,
            "rin_score": record.rin_score,
            "preservation_method": record.preservation_method,
            "manner_of_death": record.manner_of_death,
            "raw_data": record.raw_data,
            "extended_data": extended_data if extended_data else None,
            "searchable_text": searchable_text,
            "is_available": True,
        }

    def _get_field(self, row: dict[str, Any], field_name: str) -> Any:
        """Get field value, handling BOM-corrupted column names."""
        # Direct lookup first
        if field_name in row:
            return row[field_name]
        
        # Handle BOM-corrupted first column (Subject ID)
        for key in row.keys():
            if field_name in key:
                return row[key]
        
        return None

    def process_csv(self, filepath: str) -> Iterator[dict[str, Any]]:
        """Process a CSV file and yield sample dicts.
        
        Args:
            filepath: Path to the CSV file
            
        Yields:
            Dict suitable for creating Sample model instances
        """
        # Use utf-8-sig to handle BOM (Byte Order Mark)
        with open(filepath, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Skip rows that shouldn't be included
                if not self.should_include(row):
                    continue
                
                # Validate
                errors = self.validate(row)
                if errors:
                    # Log errors but continue processing
                    # In production, might want to collect these
                    continue
                
                yield self.to_sample_dict(row)

