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


def _is_positive_lewy(value: str | None) -> bool:
    """Check if Lewy body pathology value indicates POSITIVE finding.
    
    Examples of NEGATIVE values: "No Lewy Body Pathology", "None", "No Results Reported"
    Examples of POSITIVE values: "Limbic", "Brainstem", "Neocortical", "Amygdala-predominant"
    """
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Explicit negative indicators
    negative_phrases = ["no lewy", "no results", "not assessed", "not evaluated"]
    if any(neg in val for neg in negative_phrases):
        return False
    # Check for exact "none" (not as part of another word)
    if val == "none":
        return False
    return True


def _is_positive_tdp43(value: str | None) -> bool:
    """Check if TDP-43 value indicates POSITIVE finding.
    
    Examples of NEGATIVE values: "No", "None", "Not Assessed"
    Examples of POSITIVE values: "Yes", "Present"
    """
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Explicit positive indicators
    if val in ("yes", "present"):
        return True
    # Explicit negative indicators
    negative = ["no", "none", "not assessed", "not evaluated", "no results"]
    if val in negative:
        return False
    if any(neg in val for neg in negative):
        return False
    return True


def _is_positive_caa(value: str | None) -> bool:
    """Check if CAA value indicates POSITIVE finding (Grade > 0 or present).
    
    Examples of NEGATIVE values: "Grade 0", "None", "No Results Reported"
    Examples of POSITIVE values: "Grade 1", "Grade 2", "Mild", "Moderate", "Severe"
    """
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Explicit negative indicators
    if val in ("none", "no", "grade 0"):
        return False
    if "grade 0" in val or "no results" in val or "not assessed" in val:
        return False
    # Positive if contains grade > 0 or severity term
    if any(pos in val for pos in ["grade 1", "grade 2", "grade 3", "grade 4", "mild", "moderate", "severe"]):
        return True
    # If it has "grade" but not "grade 0", assume positive
    if "grade" in val:
        return True
    return False


def _is_positive_late_nc(value: str | None) -> bool:
    """Check if LATE-NC value indicates POSITIVE finding in any brain region.
    
    LATE-NC format: "Amygdala - Yes, Entorhinal Cortex - No, Hippocampus - No, Neocortex - No"
    Positive if ANY region shows "Yes"
    """
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Only positive if "yes" appears (indicating at least one region is affected)
    return "yes" in val


def _is_positive_vascular(value: str | None) -> bool:
    """Check if vascular/small vessel disease value indicates POSITIVE finding.
    
    Examples of NEGATIVE values: "None", "No Results Reported"
    Examples of POSITIVE values: "Mild", "Moderate", "Severe"
    """
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Explicit negative indicators
    negative = ["none", "no results", "not assessed", "not evaluated"]
    if val in negative:
        return False
    if any(neg in val for neg in negative):
        return False
    # Positive for severity terms
    return any(pos in val for pos in ["mild", "moderate", "severe", "present"])


def _is_positive_als_tdp(value: str | None) -> bool:
    """Check if ALS-TDP value indicates POSITIVE finding."""
    if not value:
        return False
    val = value.lower().strip()
    if not val:
        return False
    # Explicit negative indicators
    negative = ["no", "none", "not assessed", "not evaluated", "no results"]
    if val in negative:
        return False
    if any(neg in val for neg in negative):
        return False
    return True


def build_copathology_summary(
    icd_copathologies: list[dict],
    neuropath_metrics: dict[str, str],
) -> str:
    """Build a human-readable summary of TRUE co-pathologies only.
    
    IMPORTANT: This function only reports TRUE co-pathologies, NOT AD staging metrics.
    - AD Staging (NOT co-pathologies): ADNC, Thal Phase, CERAD, A/B/C scores
    - TRUE Co-pathologies: Lewy body, CAA, TDP-43, LATE-NC, Vascular, ALS-TDP
    
    Args:
        icd_copathologies: List of ICD-based co-pathologies
        neuropath_metrics: Dict of neuropathology metrics
        
    Returns:
        Human-readable summary string (e.g., "Lewy body (Limbic), CAA" or "None")
    """
    positive_copaths = []
    
    # 1. Check ICD-based co-pathologies (already filtered by is_copathology flag)
    for copath in icd_copathologies:
        if copath.get("is_copathology"):
            # Don't duplicate if we'll also detect from neuropath_metrics
            category = copath.get("category", "")
            # Skip categories we'll detect from metrics (avoids double-counting)
            if category not in ["Lewy", "CAA", "Vascular"]:
                positive_copaths.append(copath["name"])
    
    # 2. Check neuropathology metrics for POSITIVE findings only
    
    # Lewy body pathology
    if "Lewy_Pathology" in neuropath_metrics:
        lewy_val = neuropath_metrics["Lewy_Pathology"]
        if _is_positive_lewy(lewy_val):
            positive_copaths.append(f"Lewy body ({lewy_val})")
    
    # Cerebral Amyloid Angiopathy
    if "CAA" in neuropath_metrics:
        caa_val = neuropath_metrics["CAA"]
        if _is_positive_caa(caa_val):
            positive_copaths.append(f"CAA ({caa_val})")
    
    # TDP-43 Proteinopathy
    if "TDP-43" in neuropath_metrics:
        tdp_val = neuropath_metrics["TDP-43"]
        if _is_positive_tdp43(tdp_val):
            positive_copaths.append("TDP-43")
    
    # LATE-NC (Limbic-predominant Age-related TDP-43 Encephalopathy)
    if "LATE-NC" in neuropath_metrics:
        late_val = neuropath_metrics["LATE-NC"]
        if _is_positive_late_nc(late_val):
            positive_copaths.append("LATE-NC")
    
    # Small Vessel Disease / Vascular
    if "Small_Vessel_Disease" in neuropath_metrics:
        svd_val = neuropath_metrics["Small_Vessel_Disease"]
        if _is_positive_vascular(svd_val):
            positive_copaths.append(f"Vascular ({svd_val})")
    
    # ALS-TDP
    if "ALS-TDP" in neuropath_metrics:
        als_val = neuropath_metrics["ALS-TDP"]
        if _is_positive_als_tdp(als_val):
            positive_copaths.append("ALS-TDP")
    
    # Return summary
    if positive_copaths:
        return ", ".join(positive_copaths)
    
    return "None"


def has_copathology(copathology_info: CopathologyInfo, categories: list[str]) -> bool:
    """Check if sample has any of the specified co-pathology categories with POSITIVE findings.
    
    Args:
        copathology_info: The extracted co-pathology info
        categories: List of category names to check (e.g., ["Lewy", "CAA"])
        
    Returns:
        True if sample has any of the specified co-pathologies with POSITIVE findings
    """
    # Check ICD-based co-pathologies
    for copath in copathology_info.icd_copathologies:
        if copath.get("category") in categories and copath.get("is_copathology"):
            return True
    
    # Check neuropathology metrics - only if they indicate POSITIVE findings
    metrics = copathology_info.neuropath_metrics
    
    for category in categories:
        if category == "Lewy":
            if "Lewy_Pathology" in metrics and _is_positive_lewy(metrics["Lewy_Pathology"]):
                return True
        elif category == "CAA":
            if "CAA" in metrics and _is_positive_caa(metrics["CAA"]):
                return True
        elif category in ("TDP-43", "FTD"):
            if "TDP-43" in metrics and _is_positive_tdp43(metrics["TDP-43"]):
                return True
            if "LATE-NC" in metrics and _is_positive_late_nc(metrics["LATE-NC"]):
                return True
            if "ALS-TDP" in metrics and _is_positive_als_tdp(metrics["ALS-TDP"]):
                return True
        elif category == "Vascular":
            if "Small_Vessel_Disease" in metrics and _is_positive_vascular(metrics["Small_Vessel_Disease"]):
                return True
        elif category == "ALS":
            if "ALS-TDP" in metrics and _is_positive_als_tdp(metrics["ALS-TDP"]):
                return True
    
    return False

