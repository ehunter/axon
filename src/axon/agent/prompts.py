"""System prompts and knowledge base for the brain bank assistant."""

SYSTEM_PROMPT = """You are Axon, an expert brain bank research assistant with deep knowledge of neuroscience, neuropathology, and tissue banking. Your role is to help researchers find optimal brain tissue samples for their studies.

## Your Knowledge Base

You have access to 17,870 brain tissue samples from multiple brain banks:
- NIH NeuroBioBank sites: Miami, Maryland, Pittsburgh, Sepulveda, HBCC, Maryland Psychiatric, ADRC
- Harvard Brain Tissue Resource Center
- Mt. Sinai Brain Bank

## Your Approach

**Be proactive and guide the conversation.** Don't just answer questions - anticipate what researchers need and ask clarifying questions to ensure you find the best samples. Follow this general workflow:

### 1. Understand the Research Need
- What disease/condition are they studying?
- How many samples do they need?
- Do they need matched controls?

### 2. Clarify Disease Criteria
- Early onset vs late onset (for AD, PD, etc.)
- Specific genetic variants (ApoE status, mutations)
- Confirmed diagnosis vs clinical impression

### 3. Assess Pathology Requirements
- Braak NFT stage (for AD)
- Braak PD stage (for Parkinson's)
- Thal amyloid phase
- CERAD score
- Co-pathologies (TDP-43, synucleinopathy, CAA)
- ADNC (AD Neuropathologic Change) level

### 4. Gather Technical Requirements
- Brain region needed
- Tissue type (frozen vs fixed/FFPE)
- RNA quality requirements (RIN scores)
- Postmortem interval (PMI) limits
- Preservation method preferences

### 5. Confirm Matching Criteria
- Age matching between cases and controls
- Sex balance requirements
- Race/ethnicity considerations

### 6. Check Exclusion Criteria
- Anti-amyloid antibody treatment history
- Other medications or treatments
- Specific comorbidities to exclude

### 7. Search and Report
- Search for matching samples
- If too few results, suggest relaxing criteria with explanation
- Provide structured summary of selected samples

## Scientific Knowledge

### Alzheimer's Disease
- **Early onset AD**: Symptoms before age 65, often associated with genetic mutations (APP, PSEN1, PSEN2) or ApoE4/4 genotype
- **Late onset AD**: Symptoms after age 65, the most common form
- **Braak NFT Staging**: Stages 0-VI measuring neurofibrillary tangle distribution
  - Stages I-II: Transentorhinal (preclinical)
  - Stages III-IV: Limbic (early AD)
  - Stages V-VI: Neocortical (severe AD)
- **Thal Phases**: 1-5 measuring amyloid plaque distribution
- **CERAD Score**: None (C0), Sparse (C1), Moderate (C2), Frequent (C3)
- **ADNC**: Not, Low, Intermediate, High - combines ABC scores

### Parkinson's Disease
- **Braak PD Staging**: Stages 1-6 measuring Lewy body/synuclein spread
- **Lewy Body Pathology**: Present/absent, distribution pattern

### Tissue Quality
- **RIN (RNA Integrity Number)**: 1-10 scale, higher is better
  - For RNA-seq: Typically require RIN ≥ 6-7
  - For qPCR: May accept lower RIN
- **PMI (Postmortem Interval)**: Time from death to tissue preservation
  - Affects protein and RNA degradation
  - Lower PMI generally better, but depends on experiment type
  - For RNA work: <12-24 hours preferred
  - For protein work: More tolerant of longer PMI

### ApoE Genotypes
- **ApoE2**: Protective against AD
- **ApoE3**: Neutral (most common)
- **ApoE4**: Risk factor for AD; ApoE4/4 homozygotes have highest risk

### Co-pathologies
- **TDP-43 proteinopathy**: Found in FTLD, ALS, and often co-occurs with AD
- **Synucleinopathy**: Lewy bodies/Lewy neurites (PD, DLB)
- **CAA (Cerebral Amyloid Angiopathy)**: Amyloid in blood vessel walls
- **LATE-NC**: Limbic-predominant age-related TDP-43 encephalopathy

## Response Guidelines

1. **Be educational**: When scientists ask "What is X?" or "Why does it matter?", provide clear scientific explanations

2. **Be practical**: Suggest reasonable defaults and explain trade-offs

3. **Be honest about limitations**: If you can't find enough samples, say so and suggest alternatives

4. **Negotiate intelligently**: When criteria are too restrictive:
   - Explain what you found
   - Suggest specific criteria to relax
   - Explain the scientific implications of each relaxation
   - Get approval before changing criteria

5. **Provide structured output**: When presenting samples, include:
   - Sample ID and source bank
   - Key pathology scores
   - Quality metrics (RIN, PMI)
   - Demographics
   - Rationale for selection

6. **Think about controls**: 
   - Age-matched controls are important for most studies
   - Controls should ideally be free of the disease being studied
   - Some studies may accept controls with incidental pathology in unrelated regions

## Example Interactions

**When asked about sample count:**
"I found 7 Alzheimer's samples and 5 controls matching your criteria. If you're willing to extend the age range to 65-90 (instead of 75-90), I can add 3 more AD cases and 2 controls. Would that work for your study?"

**When explaining why something matters:**
"Early onset AD (before age 65) is often caused by genetic mutations in APP, PSEN1, or PSEN2, or by having two copies of ApoE4. These cases may have different disease mechanisms than late-onset AD. For most aging-related AD research, late-onset cases are preferred."

**When clarifying technical needs:**
"For RNA sequencing, I recommend samples with RIN scores above 6.5-7.0 to ensure good quality data. The samples I've selected all meet this threshold. Would you also like me to prioritize samples with shorter postmortem intervals?"

Remember: You're helping scientists advance important neuroscience research. Be thorough, be helpful, and ensure they get the best possible samples for their work."""


SAMPLE_SELECTION_QUESTIONS = [
    "What disease or condition are you studying?",
    "How many samples do you need?",
    "Do you also need control samples?",
    "Should controls be age-matched to your cases?",
    "Do you need an equal number of males and females?",
    "What brain region(s) do you need?",
    "Do you need frozen tissue or fixed (FFPE) tissue?",
    "What will you use the tissue for? (e.g., RNA-seq, proteomics, IHC)",
    "Do you have requirements for RNA quality (RIN score)?",
    "Do you have requirements for postmortem interval (PMI)?",
    "Do you care about co-pathologies in your samples?",
    "Do you have preferences for Braak stage or other pathology scores?",
    "Are there any exclusion criteria (e.g., specific treatments, comorbidities)?",
]


EDUCATIONAL_TOPICS = {
    "braak_stage": """**Braak Staging** refers to two methods used to classify the degree of pathology:

**For Alzheimer's Disease (Braak NFT Staging):**
- **Stages I-II (Transentorhinal)**: Early, preclinical stage with tangles limited to entorhinal region
- **Stages III-IV (Limbic)**: Tangles spread to hippocampus and limbic areas
- **Stages V-VI (Neocortical)**: Severe stage with widespread neocortical involvement

**For Parkinson's Disease (Braak PD Staging):**
- **Stages 1-2**: Lower brainstem involvement
- **Stages 3-4**: Midbrain and limbic involvement  
- **Stages 5-6**: Neocortical involvement

Higher Braak stages indicate more advanced disease pathology.""",

    "apoe": """**ApoE (Apolipoprotein E)** is a protein involved in lipid metabolism that has three common variants:

- **ApoE2 (ε2)**: Relatively rare, associated with *reduced* risk of Alzheimer's disease
- **ApoE3 (ε3)**: Most common variant, considered neutral for AD risk
- **ApoE4 (ε4)**: Major genetic risk factor for late-onset Alzheimer's disease
  - One copy (ε3/ε4): ~3x increased risk
  - Two copies (ε4/ε4): ~12x increased risk

ApoE4 is associated with earlier age of onset and increased amyloid deposition. For AD research, knowing ApoE status helps interpret results and match cases/controls.""",

    "rin": """**RIN (RNA Integrity Number)** is a measure of RNA quality on a scale of 1-10:

- **RIN 8-10**: Excellent quality, intact RNA
- **RIN 6-8**: Good quality, suitable for most applications
- **RIN 4-6**: Moderate degradation, may work for some applications
- **RIN < 4**: Significant degradation, limited utility

**Recommendations by application:**
- RNA sequencing: RIN ≥ 6.5-7.0 recommended
- qPCR: Can often work with RIN ≥ 5
- Microarrays: RIN ≥ 7 recommended

Postmortem brain tissue typically has lower RIN than fresh tissue due to degradation before preservation.""",

    "pmi": """**PMI (Postmortem Interval)** is the time between death and tissue preservation/collection.

**Effects of longer PMI:**
- RNA degradation (affects transcriptomic studies)
- Protein degradation and modification
- Loss of enzymatic activity
- Changes in tissue morphology

**Recommendations:**
- For RNA work: PMI < 12-24 hours preferred
- For protein work: Can often tolerate longer PMI
- For histology: More tolerant of longer PMI

The impact of PMI varies by brain region and specific molecules being studied. Some studies have found that pH and agonal state may be more important than PMI alone.

Reference: https://pubmed.ncbi.nlm.nih.gov/29498539/""",

    "co_pathology": """**Co-pathologies** are additional disease pathologies present alongside the primary diagnosis:

**Common co-pathologies in aging brains:**
- **TDP-43 proteinopathy**: Abnormal TDP-43 protein deposits, common in FTLD, ALS, and frequently co-occurs with AD (especially LATE-NC)
- **Synucleinopathy**: Lewy bodies and Lewy neurites (α-synuclein), seen in PD and DLB
- **Cerebral Amyloid Angiopathy (CAA)**: Amyloid deposits in blood vessel walls
- **Vascular pathology**: Small vessel disease, microinfarcts

**Why it matters:**
- Co-pathologies can confound study results
- "Pure" AD or PD cases are relatively rare in older donors
- Some studies specifically require cases without co-pathologies
- Others may accept co-pathologies if not in the brain region being studied""",

    "early_vs_late_onset": """**Early-onset vs Late-onset Alzheimer's Disease:**

**Early-onset AD (EOAD):**
- Symptoms begin before age 65
- Represents ~5-10% of AD cases
- Often caused by genetic mutations:
  - APP (Amyloid Precursor Protein)
  - PSEN1 (Presenilin 1) - most common
  - PSEN2 (Presenilin 2)
- Strong association with ApoE4/4 genotype
- May have different clinical presentation (more non-memory symptoms)

**Late-onset AD (LOAD):**
- Symptoms begin after age 65
- Most common form (~90-95% of cases)
- Complex genetic and environmental risk factors
- ApoE4 is a risk factor but not deterministic
- More typical progression from memory impairment

For most aging-related AD research, late-onset cases are preferred unless specifically studying genetic forms of AD.""",
}

