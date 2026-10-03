# Recruitment Platform Architecture Diagram

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Web[Web Dashboard]
        Mobile[Mobile App]
        API[External API Clients]
    end

    subgraph "API Gateway"
        GW[NGINX Ingress]
    end

    subgraph "Recruitment Platform"
        subgraph "API Layer"
            Health[Health Endpoints]
            RP[Resume Parser API]
            CM[Candidate Matcher API]
            IS[Interview Scheduler API]
            SA[Skills Assessor API]
            BD[Bias Detector API]
            TPM[Talent Pool API]
            RA[Analytics API]
            OA[Onboarding API]
            JDO[Job Description API]
            EB[Employer Branding API]
        end

        subgraph "Agent Layer"
            direction TB
            subgraph "Resume Parser Agents"
                RPA1[ResumeParserAgent]
                RPA2[ContactExtractor]
                RPA3[EducationExtractor]
                RPA4[ExperienceExtractor]
                RPA5[SkillsExtractor]
            end
            subgraph "Candidate Matcher Agents"
                CMA1[BiasAwareRanker]
                CMA2[CultureFitAssessor]
                CMA3[MatchExplainer]
                CMA4[SemanticMatcher]
                CMA5[SkillsGapAnalyzer]
            end
            subgraph "Interview Scheduler Agents"
                ISA1[AvailabilityOptimizer]
                ISA2[CalendarSync]
                ISA3[ConflictDetector]
                ISA4[Reminder]
                ISA5[TimezoneResolver]
            end
            subgraph "Skills Assessor Agents"
                SAA1[GapAnalyzer]
                SAA2[LearningPathRecommender]
                SAA3[ProficiencyScorer]
                SAA4[SkillExtractor]
                SAA5[SkillValidator]
            end
            subgraph "Bias Detector Agents"
                BDA1[DemographicAnalyzer]
                BDA2[FairnessScorer]
                BDA3[LanguageBiasDetector]
                BDA4[PatternDetector]
                BDA5[Recommendation]
            end
            subgraph "Talent Pool Agents"
                TPMA1[CandidateSourcer]
                TPMA2[EngagementTracker]
                TPMA3[PoolAnalyzer]
                TPMA4[TalentRecommender]
                TPMA5[TalentTagger]
            end
            subgraph "Analytics Agents"
                RAA1[CostAnalyzer]
                RAA2[DiversityAnalyzer]
                RAA3[FunnelAnalyzer]
                RAA4[PredictiveHiring]
                RAA5[SourceTracker]
            end
            subgraph "Onboarding Agents"
                OAA1[ComplianceChecker]
                OAA2[DocumentGenerator]
                OAA3[ProgressTracker]
                OAA4[TaskScheduler]
                OAA5[WelcomeMessage]
            end
            subgraph "Job Description Agents"
                JDA1[ATSCompatibility]
                JDA2[BiasRemover]
                JDA3[KeywordOptimizer]
                JDA4[SEOOptimizer]
                JDA5[ToneAnalyzer]
            end
            subgraph "Employer Branding Agents"
                EBA1[BrandStrategy]
                EBA2[ContentGenerator]
                EBA3[ReputationManager]
                EBA4[ReviewAnalyzer]
                EBA5[SentimentAnalyzer]
            end
        end

        subgraph "Service Layer"
            AR[Agent Registry]
            PS[Parsing Service]
        end

        subgraph "Integration Layer"
            LLM[LLM Client]
            EMB[Embedding Client]
            VS[Vector Store]
            FP[File Parser]
            ST[Storage]
            CAL[Calendar]
            OAI[OpenAI]
            ATS[ATS Client]
            HRMS[HRMS Client]
            GD[Glassdoor]
            IND[Indeed]
            LI[LinkedIn]
            SDB[Skill Database]
        end

        subgraph "Config Layer"
            SET[Settings]
            LOG[Logging Config]
            EXC[Exceptions]
        end
    end

    subgraph "Data Layer"
        PG[(PostgreSQL)]
        RD[(Redis)]
        S3[(Object Storage)]
    end

    subgraph "External Services"
        OAI_EXT[OpenAI API]
        GC[Google Calendar]
        OL[Outlook]
    end

    Web --> GW
    Mobile --> GW
    API --> GW

    GW --> Health
    GW --> RP
    GW --> CM
    GW --> IS
    GW --> SA
    GW --> BD
    GW --> TPM
    GW --> RA
    GW --> OA
    GW --> JDO
    GW --> EB

    RP --> RPA1 & RPA2 & RPA3 & RPA4 & RPA5
    CM --> CMA1 & CMA2 & CMA3 & CMA4 & CMA5
    IS --> ISA1 & ISA2 & ISA3 & ISA4 & ISA5
    SA --> SAA1 & SAA2 & SAA3 & SAA4 & SAA5
    BD --> BDA1 & BDA2 & BDA3 & BDA4 & BDA5
    TPM --> TPMA1 & TPMA2 & TPMA3 & TPMA4 & TPMA5
    RA --> RAA1 & RAA2 & RAA3 & RAA4 & RAA5
    OA --> OAA1 & OAA2 & OAA3 & OAA4 & OAA5
    JDO --> JDA1 & JDA2 & JDA3 & JDA4 & JDA5
    EB --> EBA1 & EBA2 & EBA3 & EBA4 & EBA5

    RPA1 & RPA2 & RPA3 & RPA4 & RPA5 --> AR
    CMA1 & CMA2 & CMA3 & CMA4 & CMA5 --> AR
    ISA1 & ISA2 & ISA3 & ISA4 & ISA5 --> AR
    SAA1 & SAA2 & SAA3 & SAA4 & SAA5 --> AR
    BDA1 & BDA2 & BDA3 & BDA4 & BDA5 --> AR
    TPMA1 & TPMA2 & TPMA3 & TPMA4 & TPMA5 --> AR
    RAA1 & RAA2 & RAA3 & RAA4 & RAA5 --> AR
    OAA1 & OAA2 & OAA3 & OAA4 & OAA5 --> AR
    JDA1 & JDA2 & JDA3 & JDA4 & JDA5 --> AR
    EBA1 & EBA2 & EBA3 & EBA4 & EBA5 --> AR

    AR --> PS
    AR --> LLM
    AR --> EMB
    AR --> VS
    AR --> FP
    AR --> ST
    AR --> CAL
    AR --> OAI
    AR --> ATS
    AR --> HRMS
    AR --> GD
    AR --> IND
    AR --> LI
    AR --> SDB

    LLM --> OAI_EXT
    EMB --> OAI_EXT
    OAI --> OAI_EXT
    CAL --> GC
    CAL --> OL

    AR --> PG
    AR --> RD
    ST --> S3
```

## Agent Interaction Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Layer
    participant AR as Agent Registry
    participant A as Agent
    participant I as Integration
    participant D as Database

    C->>API: POST /api/v1/resume-parser/parse
    API->>AR: get("resume_parser")
    AR->>A: execute(resume_data)
    A->>I: parse_file(resume.pdf)
    I-->>A: extracted_text
    A->>A: extract_contact()
    A->>A: extract_education()
    A->>A: extract_experience()
    A->>A: extract_skills()
    A-->>AR: structured_data
    AR-->>API: AgentResponse
    API-->>C: JSON Response
```

## Deployment Architecture

```mermaid
graph LR
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: recruitment-platform"
            ING[Ingress] --> SVC[Service]
            SVC --> P1[Pod 1]
            SVC --> P2[Pod 2]
            SVC --> P3[Pod 3]
            
            HPA[HPA] -.-> P1
            HPA -.-> P2
            HPA -.-> P3
            
            PDB[PDB] -.-> P1
            PDB -.-> P2
            PDB -.-> P3
        end
        
        subgraph "Data Services"
            PG[(PostgreSQL)]
            RD[(Redis)]
        end
    end
    
    P1 --> PG
    P2 --> PG
    P3 --> PG
    P1 --> RD
    P2 --> RD
    P3 --> RD
```

## CI/CD Pipeline

```mermaid
graph LR
    A[Push to Main] --> B[CI Pipeline]
    B --> C[Lint & Type Check]
    C --> D[Run Tests]
    D --> E[Security Scan]
    E --> F[Build Docker Image]
    F --> G[Push to Registry]
    G --> H[Deploy to Staging]
    H --> I[Integration Tests]
    I --> J[Deploy to Production]
```
