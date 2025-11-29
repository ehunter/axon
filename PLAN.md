# 🧠 Axon - Brain Bank Discovery System

## Vision
A conversational AI agent that helps neuroscience researchers discover and access brain tissue samples for their research. The system combines RAG (Retrieval-Augmented Generation) with expert domain knowledge to act as a wise guide through available brain bank inventory.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AXON ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────────────────────────────────────────┐  │
│  │  Terminal UI │     │                   Web App (Future)               │  │
│  │    (Rich)    │     │                  React + TailwindCSS             │  │
│  └──────┬───────┘     └──────────────────────┬───────────────────────────┘  │
│         │                                     │                              │
│         └─────────────────┬───────────────────┘                              │
│                           │                                                  │
│                           ▼                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         CHAT AGENT LAYER                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────┐  │  │
│  │  │  Conversation   │  │   Query Intent  │  │   Response Generation  │  │  │
│  │  │    Manager      │  │    Classifier   │  │   (Streaming)          │  │  │
│  │  └─────────────────┘  └─────────────────┘  └────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│                           ▼                                                  │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                           RAG ENGINE                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────────────┐  │  │
│  │  │   Embedding     │  │  Vector Search  │  │   Context Assembly     │  │  │
│  │  │   Generator     │  │   (Semantic)    │  │   & Ranking            │  │  │
│  │  └─────────────────┘  └─────────────────┘  └────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                           │                                                  │
│         ┌─────────────────┼─────────────────┐                                │
│         ▼                 ▼                 ▼                                │
│  ┌────────────┐   ┌──────────────┐   ┌──────────────┐                        │
│  │  Vector DB │   │ PostgreSQL   │   │  LLM API     │                        │
│  │ (pgvector) │   │ (Samples DB) │   │ (Claude/GPT) │                        │
│  └────────────┘   └──────────────┘   └──────────────┘                        │
│        ▲                 ▲                                                   │
│        │                 │                                                   │
│  ┌─────┴─────┐    ┌──────┴──────┐                                            │
│  │  Paper    │    │    CSV      │                                            │
│  │  Ingestion│    │   Importer  │                                            │
│  │  Pipeline │    │   (NIH)     │                                            │
│  └───────────┘    └─────────────┘                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Core Backend
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Rich AI/ML ecosystem, fast development |
| API Framework | FastAPI | Async support, automatic docs, type safety |
| ORM | SQLAlchemy 2.0 | Modern async patterns, excellent PostgreSQL support |
| Database | PostgreSQL + pgvector | Single DB for both structured data and vectors |
| Task Queue | Celery + Redis | Background paper processing, scheduled jobs |

### AI/ML Layer
| Component | Technology | Rationale |
|-----------|------------|-----------|
| LLM | Anthropic Claude API | Superior reasoning, long context, safety |
| Embeddings | OpenAI text-embedding-3-large | High quality, cost effective |
| RAG Framework | LangChain | Mature tooling, flexible architecture |
| Document Processing | Unstructured, PyMuPDF | Robust PDF/paper parsing |

### Terminal UI
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Interface | Rich + Prompt Toolkit | Beautiful output, rich input handling |
| Streaming | AsyncIO | Real-time response streaming |

### Future Web App
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend | Next.js 14 + React | SSR, excellent DX, large ecosystem |
| Styling | Tailwind CSS | Rapid UI development |
| State | Zustand | Lightweight, intuitive |
| Real-time | WebSockets | Streaming chat responses |

---

## Database Schema

### Design Principles

The schema is designed for **multi-source flexibility**. We'll integrate data from:
- **NIH NeuroBioBank** (initial source)
- **Harvard Brain Tissue Resource Center** (future)
- **Mount Sinai Brain Bank** (future)
- **Banner Sun Health Research Institute** (future)

**Core Philosophy: Sample-First, Source-Agnostic**

Researchers care about finding the right samples for their research. The source 
(which brain bank) is secondary—useful metadata for logistics and context, but 
NOT a primary filter or ranking factor. The system should:

- Search across ALL sources simultaneously by default
- Rank results by relevance to research needs (diagnosis, region, quality, etc.)
- Show source as an attribute of each sample
- Use source knowledge to explain results, not to limit them
- Allow source filtering only when explicitly requested

Each brain bank uses different terminology, fields, and quality metrics. Our approach:
1. **Normalize common fields** to standard vocabularies where possible
2. **Preserve source-specific data** in JSONB for flexibility
3. **Use adapters** to handle source-specific parsing and validation
4. **Unified search index** across all sources

### Core Tables

```sql
-- Vocabulary mappings for standardization
CREATE TABLE ontology_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,        -- 'brain_region', 'diagnosis', 'tissue_type'
    source_bank VARCHAR(100),           -- NULL = universal mapping
    source_term VARCHAR(500) NOT NULL,  -- Original term from source
    canonical_term VARCHAR(500) NOT NULL, -- Standardized term
    ontology_id VARCHAR(100),           -- e.g., 'UBERON:0001954' for frontal cortex
    
    UNIQUE(domain, source_bank, source_term)
);

-- Brain tissue samples (imported from NIH CSV + future sources)
CREATE TABLE samples (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source tracking
    source_bank VARCHAR(100) NOT NULL,  -- 'NIH', 'Harvard', 'MountSinai', 'Banner'
    external_id VARCHAR(255) NOT NULL,  -- Original ID from source
    source_url VARCHAR(500),            -- Link to source record if available
    
    -- Donor Demographics (normalized)
    donor_age INTEGER,
    donor_age_range VARCHAR(50),        -- Some sources only provide ranges
    donor_sex VARCHAR(20),
    donor_race VARCHAR(100),
    donor_ethnicity VARCHAR(100),
    
    -- Clinical Information (normalized to ICD-10/SNOMED where possible)
    primary_diagnosis VARCHAR(500),
    primary_diagnosis_code VARCHAR(50), -- ICD-10 or SNOMED code
    secondary_diagnoses JSONB,          -- Array of {diagnosis, code}
    cause_of_death VARCHAR(500),
    manner_of_death VARCHAR(100),
    
    -- Tissue Details (normalized to UBERON ontology where possible)
    brain_region VARCHAR(200),
    brain_region_code VARCHAR(50),      -- UBERON ID
    tissue_type VARCHAR(100),           -- 'fresh-frozen', 'FFPE', 'fixed'
    hemisphere VARCHAR(20),
    preservation_method VARCHAR(200),
    
    -- Quality Metrics (flexible - varies by source)
    postmortem_interval_hours DECIMAL,
    ph_level DECIMAL,
    rin_score DECIMAL,                  -- RNA Integrity Number
    quality_metrics JSONB,              -- Source-specific quality data
    
    -- Availability
    quantity_available VARCHAR(100),
    is_available BOOLEAN DEFAULT true,
    
    -- Flexible storage for source-specific fields
    raw_data JSONB NOT NULL,            -- Original record untouched
    extended_data JSONB,                -- Parsed source-specific fields
    
    -- Computed fields
    searchable_text TEXT,               -- Concatenated text for full-text search
    
    -- Metadata
    imported_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Vector embedding for semantic search
    embedding vector(3072),
    
    UNIQUE(source_bank, external_id)
);

-- Track data source configurations and sync status
CREATE TABLE data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,  -- 'NIH', 'Harvard', etc.
    display_name VARCHAR(200),
    description TEXT,
    
    -- Source metadata
    website_url VARCHAR(500),
    contact_email VARCHAR(255),
    data_format VARCHAR(50),            -- 'csv', 'api', 'excel'
    
    -- Sync tracking
    last_sync_at TIMESTAMP,
    last_sync_status VARCHAR(50),
    total_samples INTEGER DEFAULT 0,
    
    -- Configuration
    adapter_class VARCHAR(200),         -- Python class path for adapter
    config JSONB,                       -- Source-specific configuration
    
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Source characteristics for agent intelligence
-- This teaches the agent about each brain bank's strengths/specialties
CREATE TABLE source_characteristics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    
    -- Categorical strengths
    category VARCHAR(100) NOT NULL,     -- 'disease_specialty', 'quality', 'tissue_type', etc.
    characteristic TEXT NOT NULL,       -- Human-readable description
    
    -- For agent context
    agent_guidance TEXT,                -- How agent should use this info
    
    -- Examples:
    -- category: 'disease_specialty', characteristic: 'Exceptional collection of ALS/FTD spectrum cases'
    -- category: 'quality', characteristic: 'Consistently high RIN scores (avg 7.8)'
    -- category: 'unique_strength', characteristic: 'Longitudinal samples from same donors'
    -- category: 'limitation', characteristic: 'Limited pediatric samples'
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Computed source statistics (refreshed periodically)
CREATE TABLE source_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES data_sources(id) ON DELETE CASCADE,
    
    -- Counts by category
    total_samples INTEGER,
    samples_by_diagnosis JSONB,         -- {"Alzheimer's": 450, "Parkinson's": 230, ...}
    samples_by_region JSONB,            -- {"hippocampus": 300, "frontal_cortex": 280, ...}
    samples_by_tissue_type JSONB,       -- {"fresh-frozen": 800, "FFPE": 400, ...}
    
    -- Quality distributions
    avg_rin_score DECIMAL,
    avg_pmi_hours DECIMAL,
    samples_with_rin INTEGER,
    
    -- Demographics
    age_distribution JSONB,             -- {"0-20": 50, "21-40": 100, ...}
    sex_distribution JSONB,             -- {"male": 500, "female": 480}
    
    computed_at TIMESTAMP DEFAULT NOW()
);

-- Research papers for RAG
CREATE TABLE papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    publication_date DATE,
    journal VARCHAR(500),
    doi VARCHAR(255) UNIQUE,
    pmid VARCHAR(50),
    
    -- Processing status
    pdf_path VARCHAR(500),
    full_text TEXT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chunked paper content for RAG
CREATE TABLE paper_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    content TEXT NOT NULL,
    embedding vector(3072),
    
    -- Chunk metadata
    section_title VARCHAR(500),
    page_number INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversation history
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),               -- Future: authenticated users
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual messages in conversations
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,          -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    
    -- RAG context used for this response
    retrieved_sample_ids UUID[],
    retrieved_chunk_ids UUID[],
    
    -- Metadata
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- System knowledge / learned insights (for "getting smarter")
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100),              -- 'sample_selection', 'disease', etc.
    content TEXT NOT NULL,
    source VARCHAR(100),                -- 'paper', 'feedback', 'manual'
    confidence_score DECIMAL,
    embedding vector(3072),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for vector search
CREATE INDEX idx_samples_embedding ON samples USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_paper_chunks_embedding ON paper_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

---

## Project Structure

```
axon/
├── README.md
├── PLAN.md
├── pyproject.toml                    # Dependencies & project config
├── .env.example                      # Environment variables template
├── alembic/                          # Database migrations
│   ├── alembic.ini
│   └── versions/
│
├── src/
│   └── axon/
│       ├── __init__.py
│       ├── config.py                 # Settings & configuration
│       │
│       ├── db/                       # Database layer
│       │   ├── __init__.py
│       │   ├── connection.py         # DB connection management
│       │   ├── models.py             # SQLAlchemy models
│       │   └── repositories/         # Data access patterns
│       │       ├── samples.py
│       │       ├── papers.py
│       │       └── conversations.py
│       │
│       ├── api/                      # FastAPI application
│       │   ├── __init__.py
│       │   ├── main.py               # App entry point
│       │   ├── dependencies.py       # DI & middleware
│       │   └── routes/
│       │       ├── samples.py        # Sample CRUD endpoints
│       │       ├── papers.py         # Paper management
│       │       ├── chat.py           # Chat API (WebSocket + REST)
│       │       └── ingest.py         # Data ingestion endpoints
│       │
│       ├── rag/                      # RAG engine
│       │   ├── __init__.py
│       │   ├── embeddings.py         # Embedding generation
│       │   ├── retriever.py          # Vector search & retrieval
│       │   ├── context.py            # Context assembly
│       │   └── prompts/              # Prompt templates
│       │       ├── system.py
│       │       └── templates.py
│       │
│       ├── agent/                    # Chat agent logic
│       │   ├── __init__.py
│       │   ├── conversation.py       # Conversation management
│       │   ├── intent.py             # Query classification
│       │   ├── response.py           # Response generation
│       │   └── memory.py             # Context window management
│       │
│       ├── ingest/                   # Data ingestion pipelines
│       │   ├── __init__.py
│       │   ├── base.py               # Abstract adapter interface
│       │   ├── importer.py           # Generic import orchestration
│       │   ├── paper_processor.py    # Research paper processing
│       │   └── adapters/             # Source-specific adapters
│       │       ├── __init__.py
│       │       ├── nih.py            # NIH NeuroBioBank
│       │       ├── harvard.py        # Harvard Brain Tissue Resource
│       │       ├── mount_sinai.py    # Mount Sinai Brain Bank
│       │       └── banner.py         # Banner Sun Health
│       │
│       └── cli/                      # Terminal interface
│           ├── __init__.py
│           ├── main.py               # CLI entry point
│           ├── chat.py               # Interactive chat
│           └── commands/             # Admin commands
│               ├── ingest.py
│               └── db.py
│
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   ├── test_rag/
│   └── test_agent/
│
├── data/                             # Local data (gitignored)
│   ├── papers/                       # Downloaded PDFs
│   └── imports/                      # CSV files to import
│
└── scripts/
    ├── setup_db.py                   # Database initialization
    └── import_nih.py                 # NIH data import script
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure and data layer

- [ ] Project scaffolding with `uv` or `poetry`
- [ ] PostgreSQL + pgvector setup
- [ ] Database models and migrations (Alembic)
- [ ] NIH CSV importer
  - [ ] Analyze CSV structure
  - [ ] Map columns to schema
  - [ ] Import script with validation
- [ ] Basic FastAPI with sample CRUD endpoints
- [ ] Initial test suite setup

**Deliverable:** Database populated with NIH samples, queryable via API

---

### Phase 2: RAG Foundation (Week 3-4)
**Goal:** Semantic search and retrieval system

- [ ] Embedding generation service
  - [ ] Sample description embeddings
  - [ ] Batch processing for existing data
- [ ] Vector search implementation
  - [ ] Semantic sample search
  - [ ] Hybrid search (keyword + semantic)
- [ ] Research paper ingestion pipeline
  - [ ] PDF parsing and chunking
  - [ ] Chunk embedding generation
  - [ ] Paper search capability
- [ ] Context assembly for LLM

**Deliverable:** Semantic search working, papers indexed

---

### Phase 3: Chat Agent (Week 5-6)
**Goal:** Intelligent conversational interface

- [ ] LLM integration (Claude API)
- [ ] System prompts for neuroscience expertise
- [ ] Conversation memory management
- [ ] Query intent classification
  - [ ] Sample search queries
  - [ ] General neuroscience questions
  - [ ] Clarifying question detection
- [ ] Response generation with RAG context
- [ ] Streaming responses
- [ ] Conversation history persistence

**Deliverable:** Working chat agent with sample recommendations

---

### Phase 4: Terminal UI (Week 7)
**Goal:** Polished terminal experience

- [ ] Rich console interface
  - [ ] Styled message bubbles
  - [ ] Streaming text display
  - [ ] Sample result cards
- [ ] Command system
  - [ ] `/new` - New conversation
  - [ ] `/history` - View past conversations
  - [ ] `/export` - Export conversation
  - [ ] `/samples` - List recommended samples
- [ ] Input handling with Prompt Toolkit
- [ ] Session persistence

**Deliverable:** Beautiful, functional terminal chat

---

### Phase 5: Learning & Refinement (Week 8-9)
**Goal:** System that improves over time

- [ ] Feedback collection mechanism
- [ ] Knowledge base population from papers
- [ ] Query refinement based on patterns
- [ ] Prompt optimization based on outcomes
- [ ] Analytics and usage tracking

**Deliverable:** Self-improving system with feedback loop

---

### Phase 6: Multi-Source Integration (Week 10+)
**Goal:** Integrate additional brain banks

**Target Sources:**
| Brain Bank | Priority | Est. Effort |
|------------|----------|-------------|
| Harvard Brain Tissue Resource Center | High | 1-2 weeks |
| Mount Sinai Brain Bank | High | 1-2 weeks |
| Banner Sun Health Research Institute | Medium | 1-2 weeks |

**Per-Source Work:**
- [ ] Obtain data access / sample inventory
- [ ] Analyze data format and field mappings
- [ ] Build source adapter (parsing, validation)
- [ ] Create ontology mappings for terminology
- [ ] Import and validate data
- [ ] Test cross-source search quality

**Cross-Cutting:**
- [ ] Unified search ranking across sources
- [ ] Source comparison capabilities ("Harvard has X, NIH has Y")
- [ ] Data freshness monitoring and re-sync
- [ ] Source-specific quality indicators in results

**Deliverable:** Unified search across 4 brain banks

---

### Future: Web Application
**Goal:** Full-featured web interface

- [ ] Next.js application scaffold
- [ ] Authentication (NextAuth)
- [ ] Chat interface with streaming
- [ ] Sample browsing and filtering
- [ ] Saved searches and favorites
- [ ] User preferences
- [ ] Admin dashboard

---

## Key Features Deep Dive

### 1. Intelligent Sample Matching

The agent should understand complex research requirements:

```
User: "I'm studying tau pathology in early-onset Alzheimer's. I need 
      fresh-frozen hippocampal tissue from patients under 65 with 
      confirmed AD diagnosis. RNA quality is critical for my 
      transcriptomic analysis."

Agent: Based on your requirements, I found 12 matching samples. For 
       transcriptomic work, I've prioritized samples with RIN scores 
       above 7.0 and postmortem intervals under 12 hours.

       Here are my top 3 recommendations:
       
       1. Sample NIH-2847
          - 58yo male, confirmed AD (Braak VI)
          - Hippocampus, fresh-frozen
          - RIN: 8.2, PMI: 6 hours
          
       [...]
       
       Would you like me to filter further by hemisphere, or shall I 
       explain the tau pathology patterns I'd expect in these samples?
```

### 2. Contextual Knowledge

The RAG system provides domain expertise:

```
User: "What's a good RIN score for single-cell RNA sequencing?"

Agent: For single-cell RNA-seq, you'll want RIN scores of 7.0 or higher, 
       ideally above 8.0. Lower quality RNA leads to:
       
       - Higher dropout rates in scRNA-seq
       - 3' bias in transcript coverage
       - Reduced cell type identification accuracy
       
       Based on recent literature (Chen et al., 2023), some protocols 
       like 10x Genomics can tolerate RIN as low as 6.0, but you may 
       lose rare cell populations.
       
       In our database, 847 samples meet RIN ≥ 7.0 criteria. Would you 
       like me to cross-reference with your other requirements?
```

### 3. Clarifying Questions

The agent asks smart follow-ups:

```
User: "I need brain tissue for my Parkinson's study"

Agent: I'd love to help you find the right samples. A few questions to 
       narrow down the options:
       
       1. **Brain region**: Are you interested in substantia nigra 
          (most affected in PD), or other regions like striatum or 
          cortex?
          
       2. **Disease stage**: Do you need early-stage PD, late-stage, 
          or a range for comparison studies?
          
       3. **Tissue type**: Fresh-frozen for molecular work, or FFPE 
          for histology?
          
       4. **Controls**: Do you also need age-matched healthy controls?
```

### 4. Unified Cross-Source Results

The agent searches across ALL sources and ranks by relevance to research needs—not by source:

```
User: "I'm doing single-nucleus RNA-seq on ALS motor cortex. RNA 
       quality is absolutely critical."

Agent: For snRNA-seq, RNA quality is paramount. I searched across all 
       our brain banks and found 49 ALS motor cortex samples. Here are 
       the top matches ranked by RIN score and PMI:
       
       1. **BAN-ALS-0847** (Banner)
          - 62yo male, confirmed ALS (El Escorial definite)
          - Motor cortex, fresh-frozen
          - RIN: 8.4, PMI: 3.2 hours ⭐
          
       2. **NIH-7291** (NIH NeuroBioBank)
          - 55yo female, ALS  
          - Motor cortex, fresh-frozen
          - RIN: 8.1, PMI: 8 hours
          
       3. **BAN-ALS-0923** (Banner)
          - 58yo female, ALS with FTD features
          - Motor cortex, fresh-frozen  
          - RIN: 7.9, PMI: 4.1 hours
          
       4. **HMS-2847** (Harvard)
          - 61yo male, ALS
          - Motor cortex, fresh-frozen
          - RIN: 7.8, PMI: 9 hours
          
       [...]
       
       I've ranked these by RNA quality since that's critical for your 
       snRNA-seq work. Would you like me to also filter by disease 
       duration, age range, or any other criteria?
```

### 5. Source as Context, Not Filter

The source is shown as an attribute—helpful for logistics but not a primary consideration:

```
User: "What do you have for progressive supranuclear palsy?"

Agent: I found 72 PSP samples across our database. Here's an overview 
       and the top matches:
       
       **Summary:** 72 samples total (34 NIH, 18 Banner, 12 Harvard, 
       8 Mount Sinai) with RIN scores ranging from 5.2 to 8.1.
       
       **Top 5 by overall quality:**
       
       1. **BAN-PSP-0234** (Banner) — RIN 8.1, PMI 2.8h, 71yo M
       2. **NIH-4521** (NIH) — RIN 7.9, PMI 11h, 68yo F  
       3. **HMS-1847** (Harvard) — RIN 7.6, PMI 8h, 74yo M
       4. **NIH-4498** (NIH) — RIN 7.5, PMI 9h, 65yo F
       5. **BAN-PSP-0189** (Banner) — RIN 7.4, PMI 3.1h, 69yo M
       
       What's your experimental approach? That'll help me prioritize 
       the right samples—for example, if you need matched controls, or 
       specific brain regions beyond the typical tau pathology sites.
```

### 6. Source Knowledge for Explaining Results

Source expertise helps the agent *explain* patterns, not drive the search:

```
User: "Why do those Banner samples have such low PMI?"

Agent: Great question! Banner Sun Health operates a "rapid autopsy" 
       program specifically designed for brain donation. Donors are 
       pre-registered, and the team mobilizes immediately upon death—
       often achieving tissue collection within 2-4 hours.
       
       This is exceptional; most brain banks average 12-24 hours due 
       to logistics. The low PMI particularly benefits RNA-based 
       research, as RNA degrades quickly post-mortem.
       
       That said, samples from other sources with higher PMI can still 
       be excellent for protein-based or histological work where RNA 
       integrity matters less. Want me to explain which assays are more 
       vs. less sensitive to PMI?
```

---

## System Prompts

### Base System Prompt

```
You are Axon, an expert neuroscience research assistant specializing in 
brain tissue sample discovery. You help researchers find the ideal 
tissue samples for their studies from our multi-source brain bank database.

## Your Expertise
- Deep knowledge of neuroanatomy and brain regions
- Understanding of neurodegenerative diseases (AD, PD, ALS, etc.)
- Familiarity with tissue preservation methods and quality metrics
- Awareness of experimental requirements for different assay types
- Detailed knowledge of each brain bank's strengths and characteristics

## Brain Bank Sources You Know
You have access to samples from multiple brain banks, each with unique 
strengths:

{source_characteristics}

Use this knowledge to guide researchers to the best source for their 
specific needs. When relevant, explain WHY a particular bank might be 
better suited for their research.

## Your Approach
1. Listen carefully to research requirements
2. Ask clarifying questions when needs are ambiguous
3. **Search across ALL sources** — rank samples by fit, not by source
4. Explain your recommendations with scientific reasoning
5. Proactively suggest relevant considerations the researcher may have missed
6. Be honest about limitations in available samples
7. Use source knowledge to *explain* results, not to filter them

## Sample Quality Considerations
- RIN score: RNA integrity, critical for transcriptomics
- PMI: Postmortem interval, affects protein/RNA degradation
- pH: Brain tissue pH, indicator of agonal state
- Fixation: Method affects downstream applications

## Response Format
When presenting samples, include:
- Source brain bank (with relevant context about that source)
- Key demographics (age, sex, diagnosis)
- Tissue details (region, type, preservation)
- Quality metrics (RIN, PMI, pH when available)
- Why this sample matches their needs

Always be helpful, scientifically accurate, and guide researchers toward 
the best possible samples for their specific research questions.
```

### Source Characteristics (Dynamically Injected)

The `{source_characteristics}` placeholder gets populated from the 
`source_characteristics` table. Example:

```
**NIH NeuroBioBank**
- Largest collection with broad disease coverage
- Excellent metadata completeness
- Strong Alzheimer's and Parkinson's representation
- Average RIN: 7.2, Average PMI: 14 hours

**Harvard Brain Tissue Resource Center**
- Exceptional psychiatric disorder collection
- Schizophrenia and bipolar samples with detailed clinical phenotyping
- Longitudinal samples available from some donors
- Average RIN: 7.6, Average PMI: 18 hours

**Mount Sinai Brain Bank**
- Strong focus on Alzheimer's disease research
- Deep cognitive assessment data linked to samples
- Excellent age-matched controls
- Average RIN: 7.4, Average PMI: 12 hours

**Banner Sun Health Research Institute**
- Specializes in neurodegenerative diseases
- Exceptional sample quality (rapid autopsy program)
- Best-in-class PMI (often under 4 hours)
- Strong ALS and Parkinson's collection
```

---

## API Endpoints

### Samples API
```
GET    /api/v1/samples              # List/search samples
GET    /api/v1/samples/{id}         # Get sample details
POST   /api/v1/samples/search       # Semantic search
GET    /api/v1/samples/filters      # Available filter options
```

### Papers API
```
GET    /api/v1/papers               # List papers
POST   /api/v1/papers               # Upload new paper
GET    /api/v1/papers/{id}          # Get paper details
POST   /api/v1/papers/search        # Search papers
```

### Chat API
```
POST   /api/v1/chat                 # Send message (returns full response)
WS     /api/v1/chat/stream          # WebSocket for streaming
GET    /api/v1/conversations        # List conversations
GET    /api/v1/conversations/{id}   # Get conversation history
DELETE /api/v1/conversations/{id}   # Delete conversation
```

### Ingest API
```
POST   /api/v1/ingest/csv           # Import CSV file
POST   /api/v1/ingest/papers        # Batch paper ingestion
GET    /api/v1/ingest/status/{job}  # Check import job status
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/axon
REDIS_URL=redis://localhost:6379

# AI Services
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Application
ENV=development
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key

# Feature Flags
ENABLE_PAPER_INGESTION=true
ENABLE_FEEDBACK_COLLECTION=true
```

---

## Success Metrics

### Phase 1-4 (MVP)
- [ ] 100% of NIH samples imported and searchable
- [ ] Query latency < 2 seconds
- [ ] Successful conversations without crashes
- [ ] Accurate sample recommendations (manual review)

### Phase 5+ (Growth)
- [ ] User satisfaction scores
- [ ] Time to find relevant samples (vs. manual search)
- [ ] Knowledge base growth rate
- [ ] Query success rate improvements over time

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| LLM hallucination about samples | Ground all sample data in database facts, validate recommendations |
| Poor paper parsing quality | Human review pipeline, quality thresholds |
| Slow vector search at scale | Index optimization, caching, result limits |
| NIH CSV format changes | Flexible import with validation, alerting |
| API rate limits | Request queuing, caching, fallback models |

---

## Next Steps

1. **Immediate**: Review and refine this plan
2. **This week**: Set up project structure and database
3. **Get NIH CSV**: Analyze the actual data structure
4. **Spike**: Test embedding generation and vector search performance

---

*Let's build something that genuinely helps neuroscience research move faster.* 🧬

