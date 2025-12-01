"""ICD-10 code mapping for co-pathology detection.

Based on NIH NeuroBioBank diagnostic categorization:
https://neurobiobank.nih.gov/subjects/

Diagnoses are classified using the ICD-10 coding schema.
"""

from dataclasses import dataclass
from typing import Any
import re


@dataclass
class CopathologyInfo:
    """Structured co-pathology information for a sample."""
    icd_copathologies: list[dict[str, str]]  # {"code": "G30.1", "name": "Late-onset Alzheimer's"}
    neuropath_metrics: dict[str, str]  # {"ADNC": "High", "Lewy": "Limbic"}
    primary_pathology: str | None  # The main diagnosis
    summary: str  # Human-readable summary


# ICD-10 codes mapped to co-pathology categories
# Based on NIH NeuroBioBank categorization
ICD10_COPATHOLOGY_MAP = {
    # Alzheimer's Disease (G30.x)
    "G30": ("Alzheimer's Disease", "AD"),
    "G30.0": ("Early-onset Alzheimer's Disease", "AD"),
    "G30.1": ("Late-onset Alzheimer's Disease", "AD"),
    "G30.8": ("Other Alzheimer's Disease", "AD"),
    "G30.9": ("Alzheimer's Disease, unspecified", "AD"),
    
    # Parkinson's Disease / Lewy Body (G20, G31.83)
    "G20": ("Parkinson's Disease", "Lewy"),
    "G31.83": ("Lewy Body Dementia", "Lewy"),
    
    # Frontotemporal Dementia / TDP-43 (G31.0x)
    "G31.0": ("Frontotemporal Dementia", "FTD"),
    "G31.01": ("Pick's Disease", "FTD"),
    "G31.09": ("Other Frontotemporal Dementia", "FTD"),
    
    # ALS / Motor Neuron Disease (G12.2x)
    "G12.2": ("Motor Neuron Disease", "ALS"),
    "G12.21": ("Amyotrophic Lateral Sclerosis (ALS)", "ALS"),
    
    # Cerebral Amyloid Angiopathy (I68.0)
    "I68.0": ("Cerebral Amyloid Angiopathy", "CAA"),
    
    # Cerebrovascular Disease (I67.x)
    "I67": ("Cerebrovascular Disease", "Vascular"),
    "I67.2": ("Cerebral Atherosclerosis", "Vascular"),
    "I67.3": ("Progressive Vascular Leukoencephalopathy", "Vascular"),
    "I67.4": ("Hypertensive Encephalopathy", "Vascular"),
    "I67.9": ("Cerebrovascular Disease, unspecified", "Vascular"),
    
    # Vascular Dementia (F01.x)
    "F01": ("Vascular Dementia", "Vascular"),
    "F01.5": ("Vascular Dementia, unspecified", "Vascular"),
    "F01.50": ("Vascular Dementia without behavioral disturbance", "Vascular"),
    "F01.51": ("Vascular Dementia with behavioral disturbance", "Vascular"),
    
    # Huntington's Disease (G10)
    "G10": ("Huntington's Disease", "Huntington"),
    
    # Multiple Sclerosis (G35)
    "G35": ("Multiple Sclerosis", "MS"),
    
    # Prion Diseases (A81.x)
    "A81": ("Prion Disease", "Prion"),
    "A81.0": ("Creutzfeldt-Jakob Disease", "Prion"),
    "A81.01": ("Variant Creutzfeldt-Jakob Disease", "Prion"),
    "A81.09": ("Other Creutzfeldt-Jakob Disease", "Prion"),
    
    # Progressive Supranuclear Palsy (G23.1)
    "G23.1": ("Progressive Supranuclear Palsy", "PSP"),
    
    # Corticobasal Degeneration (G31.85)
    "G31.85": ("Corticobasal Degeneration", "CBD"),
    
    # Multiple System Atrophy (G90.3)
    "G90.3": ("Multiple System Atrophy", "MSA"),
    
    # Stroke / Infarction (I63.x, I61.x)
    "I63": ("Cerebral Infarction", "Stroke"),
    "I61": ("Intracerebral Hemorrhage", "Stroke"),
    
    # Epilepsy (G40.x)
    "G40": ("Epilepsy", "Epilepsy"),
    
    # Schizophrenia (F20.x) - Not a co-pathology but important context
    "F20": ("Schizophrenia", "Psychiatric"),
    
    # Major Depression (F32.x, F33.x)
    "F32": ("Major Depressive Disorder", "Psychiatric"),
    "F33": ("Recurrent Major Depressive Disorder", "Psychiatric"),
    
    # Bipolar Disorder (F31.x)
    "F31": ("Bipolar Disorder", "Psychiatric"),
}

# Categories that are typically considered co-pathologies in AD research
COPATHOLOGY_CATEGORIES = {
    "Lewy",      # Lewy body pathology
    "FTD",       # Frontotemporal/TDP-43
    "ALS",       # ALS/TDP-43
    "CAA",       # Cerebral Amyloid Angiopathy
    "Vascular",  # Vascular pathology
    "Prion",     # Prion diseases
    "PSP",       # Progressive Supranuclear Palsy
    "CBD",       # Corticobasal Degeneration
    "MSA",       # Multiple System Atrophy
    "Huntington", # Huntington's Disease
    "Stroke",    # Stroke/Infarction
}


def parse_icd_codes(code_string: str | None) -> list[str]:
    """Parse ICD codes from a comma-separated string.
    
    Args:
        code_string: String like "G30.9, I67.9" or "G30.1"
        
    Returns:
        List of individual ICD codes
    """
    if not code_string:
        return []
    
    # Split on comma, semicolon, or whitespace
    codes = re.split(r'[,;\s]+', code_string)
    
    # Clean up each code
    cleaned = []
    for code in codes:
        code = code.strip().upper()
        if code and re.match(r'^[A-Z]\d', code):  # Valid ICD format starts with letter + digit
            cleaned.append(code)
    
    return cleaned


def get_copathology_from_icd(icd_code: str) -> tuple[str, str] | None:
    """Look up co-pathology info from an ICD code.
    
    Handles partial matching (e.g., "G30.1" matches "G30" if exact not found).
    
    Args:
        icd_code: ICD-10 code like "G30.1"
        
    Returns:
        Tuple of (name, category) or None if not found
    """
    code = icd_code.upper().strip()
    
    # Try exact match first
    if code in ICD10_COPATHOLOGY_MAP:
        return ICD10_COPATHOLOGY_MAP[code]
    
    # Try prefix match (e.g., G30.1 -> G30)
    if '.' in code:
        prefix = code.split('.')[0]
        if prefix in ICD10_COPATHOLOGY_MAP:
            return ICD10_COPATHOLOGY_MAP[prefix]
    
    return None


def extract_copathology_info(
    sample_raw_data: dict[str, Any] | None,
    sample_extended_data: dict[str, Any] | None,
    primary_diagnosis_code: str | None,
) -> CopathologyInfo:
    """Extract comprehensive co-pathology information from a sample.
    
    Args:
        sample_raw_data: The sample's raw_data JSONB field
        sample_extended_data: The sample's extended_data JSONB field
        primary_diagnosis_code: The primary_diagnosis_code field
        
    Returns:
        CopathologyInfo with structured co-pathology data
    """
    icd_copathologies = []
    neuropath_metrics = {}
    primary_pathology = None
    
    # 1. Parse ICD codes from diagnosis fields
    all_codes = []
    
    # From primary_diagnosis_code
    if primary_diagnosis_code:
        all_codes.extend(parse_icd_codes(primary_diagnosis_code))
    
    # From neuropathology_diagnosis_code in extended_data
    if sample_extended_data:
        neuropath_code = sample_extended_data.get("neuropathology_diagnosis_code")
        if neuropath_code:
            all_codes.extend(parse_icd_codes(neuropath_code))
    
    # Map ICD codes to co-pathologies
    seen_categories = set()
    for code in all_codes:
        result = get_copathology_from_icd(code)
        if result:
            name, category = result
            # Avoid duplicates
            if category not in seen_categories:
                icd_copathologies.append({
                    "code": code,
                    "name": name,
                    "category": category,
                    "is_copathology": category in COPATHOLOGY_CATEGORIES
                })
                seen_categories.add(category)
                
                # First AD code is primary pathology
                if category == "AD" and primary_pathology is None:
                    primary_pathology = name
    
    # 2. Extract neuropathology metrics from raw_data
    if sample_raw_data:
        raw = sample_raw_data
        
        # ADNC level (Alzheimer Disease Neuropathologic Change)
        adnc = raw.get("ADNC") or raw.get("Level of ADNC") or raw.get("Level of Alzheimer's Disease Neuropathologic Change (ADNC)")
        if adnc and adnc not in ("No Results Reported", "Not Assessed", ""):
            neuropath_metrics["ADNC"] = adnc
        
        # Lewy Pathology
        lewy = raw.get("Lewy Pathology") or raw.get("Lewy Body Pathology")
        if lewy and lewy not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["Lewy_Pathology"] = lewy
        
        # Cerebral Amyloid Angiopathy
        caa = raw.get("Cerebral Amyloid Angiopathy")
        if caa and caa not in ("No Results Reported", "Not Assessed", "None", ""):
            caa_grade = raw.get("Cerebral Amyloid Angiopathy, Vonsattel Grade")
            if caa_grade and caa_grade not in ("No Results Reported", "Not Assessed", ""):
                neuropath_metrics["CAA"] = f"{caa} (Grade: {caa_grade})"
            else:
                neuropath_metrics["CAA"] = caa
        
        # TDP-43 Proteinopathy
        tdp43 = raw.get("TDP-43 Proteinopathy")
        if tdp43 and tdp43 not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["TDP-43"] = tdp43
        
        # LATE-NC (Limbic-predominant Age-related TDP-43 Encephalopathy)
        late = raw.get("LATE-NC")
        if late and late not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["LATE-NC"] = late
        
        # ALS-TDP
        als_tdp = raw.get("ALS-TDP")
        if als_tdp and als_tdp not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["ALS-TDP"] = als_tdp
        
        # Small Vessel Disease
        svd = raw.get("Small Vessel Disease/Arteriolar Sclerosis")
        if svd and svd not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["Small_Vessel_Disease"] = svd
        
        # Thal Phase
        thal = raw.get("Thal Phase") or raw.get("Thal Value")
        if thal and thal not in ("No Results Reported", "Not Assessed", ""):
            neuropath_metrics["Thal_Phase"] = thal
        
        # CERAD Score
        cerad = raw.get("CERAD Score") or raw.get("CERAD Value") or raw.get("CERAD Age-Related Neuritic Plaque Score")
        if cerad and cerad not in ("No Results Reported", "Not Assessed", ""):
            neuropath_metrics["CERAD"] = cerad
        
        # Huntington Disease Grade
        hd_grade = raw.get("Huntington Disease, Vonsattel Grade")
        if hd_grade and hd_grade not in ("No Results Reported", "Not Assessed", "None", ""):
            neuropath_metrics["Huntington_Grade"] = hd_grade
    
    # 3. Build summary
    summary = build_copathology_summary(icd_copathologies, neuropath_metrics)
    
    return CopathologyInfo(
        icd_copathologies=icd_copathologies,
        neuropath_metrics=neuropath_metrics,
        primary_pathology=primary_pathology,
        summary=summary,
    )


def build_copathology_summary(
    icd_copathologies: list[dict],
    neuropath_metrics: dict[str, str],
) -> str:
    """Build a human-readable summary of co-pathologies.
    
    Args:
        icd_copathologies: List of ICD-based co-pathologies
        neuropath_metrics: Dict of neuropathology metrics
        
    Returns:
        Human-readable summary string
    """
    parts = []
    
    # Add significant co-pathologies from ICD codes
    copaths = [c for c in icd_copathologies if c.get("is_copathology")]
    if copaths:
        copath_names = [c["name"] for c in copaths]
        parts.append(f"Co-pathologies: {', '.join(copath_names)}")
    
    # Add key neuropathology metrics
    key_metrics = []
    
    if "ADNC" in neuropath_metrics:
        key_metrics.append(f"ADNC: {neuropath_metrics['ADNC']}")
    
    if "Lewy_Pathology" in neuropath_metrics:
        key_metrics.append(f"Lewy: {neuropath_metrics['Lewy_Pathology']}")
    
    if "CAA" in neuropath_metrics:
        key_metrics.append(f"CAA: {neuropath_metrics['CAA']}")
    
    if "TDP-43" in neuropath_metrics:
        key_metrics.append(f"TDP-43: {neuropath_metrics['TDP-43']}")
    
    if "LATE-NC" in neuropath_metrics:
        key_metrics.append(f"LATE-NC: {neuropath_metrics['LATE-NC']}")
    
    if "Thal_Phase" in neuropath_metrics:
        key_metrics.append(f"Thal: {neuropath_metrics['Thal_Phase']}")
    
    if "CERAD" in neuropath_metrics:
        key_metrics.append(f"CERAD: {neuropath_metrics['CERAD']}")
    
    if key_metrics:
        parts.append("; ".join(key_metrics))
    
    if parts:
        return " | ".join(parts)
    
    return "No co-pathology data recorded"


def has_copathology(copathology_info: CopathologyInfo, categories: list[str]) -> bool:
    """Check if sample has any of the specified co-pathology categories.
    
    Args:
        copathology_info: The extracted co-pathology info
        categories: List of category names to check (e.g., ["Lewy", "CAA"])
        
    Returns:
        True if sample has any of the specified co-pathologies
    """
    # Check ICD-based co-pathologies
    for copath in copathology_info.icd_copathologies:
        if copath.get("category") in categories:
            return True
    
    # Check neuropathology metrics
    category_metric_map = {
        "Lewy": ["Lewy_Pathology"],
        "CAA": ["CAA"],
        "TDP-43": ["TDP-43", "LATE-NC", "ALS-TDP"],
        "Vascular": ["Small_Vessel_Disease"],
    }
    
    for category in categories:
        if category in category_metric_map:
            for metric in category_metric_map[category]:
                if metric in copathology_info.neuropath_metrics:
                    return True
    
    return False

