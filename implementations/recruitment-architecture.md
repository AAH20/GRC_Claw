# AI-Powered Recruitment Platform Architecture

**Version:** 1.0  
**Date:** 2026-10-02  
**Owner:** GRC_Claw Architecture Team  
**Status:** Implementation Ready  
**References:** [Core Agent Framework](./core-agent-framework.md) · [Agent Governance Spec](./grc-claw-agent-governance-implementation-guide.md) · [Model Governance Spec](./grc-claw-model-governance-implementation-guide.md) · [GRC_Claw Architecture](../ARCHITECTURE.md) · [Lead Scoring Architecture](./lead-scoring.md)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Agent Architecture](#3-agent-architecture)
4. [API Design](#4-api-design)
5. [Data Models](#5-data-models)
6. [Integration Patterns](#6-integration-patterns)
7. [Security & Compliance](#7-security--compliance)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Observability & Monitoring](#9-observability--monitoring)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

The AI-Powered Recruitment Platform is a GRC_Claw implementation that automates the full talent acquisition lifecycle — from resume parsing and candidate matching to interview scheduling, skills assessment, and bias detection. It operates as a governed multi-agent system within the GRC_Claw control plane, leveraging the platform's identity, policy, and audit infrastructure.

### 1.1 Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Governance-first** | All recruitment decisions pass through GRC_Claw policy engine |
| **Explainable AI** | Every match score, ranking, and rejection includes reasoning |
| **Bias-aware** | Continuous bias detection with demographic parity monitoring |
| **Human-in-the-loop** | No automated rejection without human review |
| **Real-time** | Sub-200ms matching API with streaming resume parsing |
| **Fail-closed** | Missing data defaults to lowest confidence, not highest |
| **Tamper-evident** | All decisions logged to Merkle audit chain |
| **Composable** | Agents plug into existing GRC_Claw agent framework |

### 1.2 Target Outcomes

| Metric | Target |
|--------|--------|
| Resume-to-structured-data accuracy | >95% |
| Candidate-job match precision | >85% |
| Time-to-screen reduction | 70% |
| Interview scheduling automation | 80% |
| Bias incident rate | <1% |
| Agent workflow error rate | <3% |

---

## 2. System Overview

### 2.1 System Context Diagram

```mermaid
graph TB
    subgraph External["External Systems"]
        LinkedIn[LinkedIn / Job Boards]
        Greenhouse[Greenhouse / ATS]
        Calendar[Google Calendar / Outlook]
        Slack[Slack / Teams]
        Email[Email Service]
    end

    subgraph Clients["Client Applications"]
        RecruiterPortal[Recruiter Portal]
        CandidatePortal[Candidate Portal]
        AdminDashboard[Admin Dashboard]
        MobileApp[Mobile App]
    end

    subgraph GRC["GRC_Claw Control Plane"]
        Identity[Identity Layer<br/>DID / OAuth2]
        Policy[Policy Engine<br/>OPA / Rego]
        Audit[Audit Trail<br/>Merkle Chain]
        AgentRegistry[Agent Registry<br/>Discovery & Health]
    end

    subgraph RecruitmentPlatform["AI Recruitment Platform"]
        APIGateway[API Gateway<br/>FastAPI + Uvicorn]
        Orchestrator[Recruitment Orchestrator<br/>LangChain DeepAgents]
        
        subgraph Agents["Specialized Agents"]
            ResumeParser[Resume Parser Agent]
            CandidateMatcher[Candidate Matcher Agent]
            InterviewScheduler[Interview Scheduler Agent]
            BiasDetector[Bias Detector Agent]
            SkillsAssessor[Skills Assessor Agent]
        end

        subgraph Services["Core Services"]
            MatchingEngine[Matching Engine<br/>Vector + Rules]
            WorkflowEngine[Workflow Engine<br/>Temporal.io]
            NotificationService[Notification Service]
            AnalyticsService[Analytics Service]
        end

        subgraph Data["Data Layer"]
            PostgreSQL[(PostgreSQL<br/>Primary Store)]
            Redis[(Redis<br/>Cache + Queue)]
            VectorDB[(pgvector<br/>Semantic Search)]
            ObjectStore[(S3 / MinIO<br/>Resumes & Docs)]
        end
    end

    subgraph ML["ML Infrastructure"]
        ModelRegistry[MLflow<br/>Model Registry]
        FeatureStore[Feature Store<br/>Feast]
        TrainingPipeline[Training Pipeline<br/>Airflow]
    end

    LinkedIn --> APIGateway
    Greenhouse --> APIGateway
    RecruiterPortal --> APIGateway
    CandidatePortal --> APIGateway
    AdminDashboard --> APIGateway
    MobileApp --> APIGateway

    APIGateway --> Orchestrator
    Orchestrator --> ResumeParser
    Orchestrator --> CandidateMatcher
    Orchestrator --> InterviewScheduler
    Orchestrator --> BiasDetector
    Orchestrator --> SkillsAssessor

    ResumeParser --> PostgreSQL
    ResumeParser --> ObjectStore
    CandidateMatcher --> VectorDB
    CandidateMatcher --> PostgreSQL
    InterviewScheduler --> Calendar
    InterviewScheduler --> PostgreSQL
    BiasDetector --> PostgreSQL
    SkillsAssessor --> PostgreSQL
    SkillsAssessor --> ModelRegistry

    MatchingEngine --> VectorDB
    MatchingEngine --> PostgreSQL
    WorkflowEngine --> PostgreSQL
    NotificationService --> Slack
    NotificationService --> Email
    NotificationService --> Calendar

    Orchestrator --> Identity
    Orchestrator --> Policy
    Orchestrator --> Audit
    Orchestrator --> AgentRegistry

    ModelRegistry --> CandidateMatcher
    ModelRegistry --> SkillsAssessor
    FeatureStore --> CandidateMatcher
    FeatureStore --> SkillsAssessor
```

### 2.2 High-Level Architecture

```mermaid
graph LR
    subgraph Edge["Edge Layer"]
        CDN[CDN / WAF]
        LB[Load Balancer]
    end

    subgraph API["API Layer"]
        REST[REST API<br/>FastAPI]
        WebSocket[WebSocket<br/>Real-time]
        Webhook[Webhook<br/>Integrations]
    end

    subgraph AgentLayer["Agent Orchestration Layer"]
        Orchestrator[Recruitment Orchestrator]
        Router[Task Router]
        StateMgr[State Manager]
    end

    subgraph Domain["Domain Agent Layer"]
        RP[Resume Parser]
        CM[Candidate Matcher]
        IS[Interview Scheduler]
        BD[Bias Detector]
        SA[Skills Assessor]
    end

    subgraph Infra["Infrastructure Layer"]
        Cache[Redis Cache]
        Queue[Message Queue<br/>Kafka]
        DB[(PostgreSQL)]
        VDB[(Vector DB)]
        Storage[(Object Storage)]
    end

    subgraph External["External Integrations"]
        ATS[ATS Systems]
        Calendar[Calendar APIs]
        Comms[Communication APIs]
        JobBoards[Job Boards]
    end

    CDN --> LB --> REST
    LB --> WebSocket
    LB --> Webhook

    REST --> Orchestrator
    WebSocket --> Orchestrator
    Webhook --> Orchestrator

    Orchestrator --> Router
    Router --> RP
    Router --> CM
    Router --> IS
    Router --> BD
    Router --> SA

    RP --> DB
    RP --> Storage
    CM --> VDB
    CM --> DB
    IS --> Calendar
    IS --> DB
    BD --> DB
    SA --> DB
    SA --> Queue

    Orchestrator --> Cache
    Orchestrator --> Queue
    Queue --> ATS
    Queue --> Comms
    Queue --> JobBoards
```

### 2.3 Request Flow

```mermaid
sequenceDiagram
    participant R as Recruiter
    participant GW as API Gateway
    participant O as Orchestrator
    participant RP as Resume Parser
    participant CM as Candidate Matcher
    participant BD as Bias Detector
    participant DB as Database
    participant VDB as Vector DB

    R->>GW: POST /api/v1/candidates (resume)
    GW->>O: Forward request
    O->>RP: Parse resume
    RP->>DB: Store structured data
    RP-->>O: Parsed candidate profile
    O->>CM: Match against open jobs
    CM->>VDB: Semantic search
    CM->>DB: Fetch job requirements
    CM-->>O: Ranked matches with scores
    O->>BD: Check for bias
    BD->>DB: Log bias check
    BD-->>O: Bias report
    O-->>GW: Enriched response
    GW-->>R: Candidate profile + matches + bias report
```

---

## 3. Agent Architecture

### 3.1 Agent Overview

```mermaid
graph TB
    subgraph Orchestration["Orchestration Layer"]
        O[Recruitment Orchestrator<br/>LangChain DeepAgent]
        TM[Task Manager]
        SM[Session Manager]
        CM[Context Manager]
    end

    subgraph Agents["Specialized Agents"]
        RP[Resume Parser Agent<br/>Document AI + NER]
        CM2[Candidate Matcher Agent<br/>Vector Search + Rules]
        IS[Interview Scheduler Agent<br/>Calendar + Optimization]
        BD[Bias Detector Agent<br/>Fairness Metrics + Audit]
        SA[Skills Assessor Agent<br/>Adaptive Testing + LLM]
    end

    subgraph Shared["Shared Services"]
        KB[Knowledge Base<br/>Job Descriptions + Policies]
        FS[Feature Store<br/>Candidate Features]
        MS[Model Server<br/>MLflow]
        Audit[Audit Logger<br/>Merkle Chain]
    end

    subgraph External["External Tools"]
        DocParser[Document Parser<br/>PDF/DOCX/TXT]
        CalendarAPI[Calendar API<br/>Google/Outlook]
        EmailAPI[Email API<br/>SendGrid]
        LinkedInAPI[LinkedIn API]
        JobBoardAPI[Job Board APIs]
    end

    O --> TM
    O --> SM
    O --> CM

    TM --> RP
    TM --> CM2
    TM --> IS
    TM --> BD
    TM --> SA

    RP --> DocParser
    RP --> KB
    CM2 --> FS
    CM2 --> MS
    IS --> CalendarAPI
    IS --> EmailAPI
    BD --> Audit
    SA --> MS
    SA --> KB

    RP --> Audit
    CM2 --> Audit
    IS --> Audit
    SA --> Audit
```

### 3.2 Resume Parser Agent

```mermaid
graph LR
    subgraph Input["Input Sources"]
        PDF[PDF Resume]
        DOCX[DOCX Resume]
        TXT[Plain Text]
        LinkedIn[LinkedIn Profile URL]
    end

    subgraph Processing["Processing Pipeline"]
        DocExtract[Document Extraction<br/>PyMuPDF / python-docx]
        OCR[OCR Engine<br/>Tesseract / AWS Textract]
        NER[NER Engine<br/>spaCy / LLM]
        Classifier[Document Classifier<br/>LayoutLM]
        Validator[Data Validator<br/>Pydantic]
    end

    subgraph Output["Output"]
        Structured[Structured Candidate JSON]
        Confidence[Confidence Scores]
        RawText[Raw Text Cache]
    end

    subgraph Storage["Storage"]
        PG[(PostgreSQL)]
        S3[(S3 / MinIO)]
        Cache[(Redis Cache)]
    end

    PDF --> DocExtract
    DOCX --> DocExtract
    TXT --> DocExtract
    LinkedIn --> NER

    DocExtract --> OCR
    OCR --> NER
    NER --> Classifier
    Classifier --> Validator

    Validator --> Structured
    Validator --> Confidence
    DocExtract --> RawText

    Structured --> PG
    RawText --> S3
    Structured --> Cache
```

#### 3.2.1 Resume Parser Agent Specification

```python
# agents/resume_parser/agent.py
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime

class ParseStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

@dataclass
class ParsedField:
    field_name: str
    value: str
    confidence: float  # 0.0 - 1.0
    source: str  # "ocr", "ner", "llm", "regex"
    raw_text: Optional[str] = None

@dataclass
class WorkExperience:
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    description: Optional[str] = None
    skills: list[str] = field(default_factory=list)

@dataclass
class Education:
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None

@dataclass
class ParsedResume:
    candidate_id: str
    full_name: ParsedField
    email: ParsedField
    phone: Optional[ParsedField] = None
    location: Optional[ParsedField] = None
    linkedin_url: Optional[ParsedField] = None
    summary: Optional[ParsedField] = None
    work_experience: list[WorkExperience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    skills: list[ParsedField] = field(default_factory=list)
    certifications: list[ParsedField] = field(default_factory=list)
    languages: list[ParsedField] = field(default_factory=list)
    parse_status: ParseStatus = ParseStatus.PENDING
    overall_confidence: float = 0.0
    parsing_version: str = "1.0"
    parsed_at: datetime = field(default_factory=datetime.utcnow)
    raw_text_path: Optional[str] = None  # S3 path
```

### 3.3 Candidate Matcher Agent

```mermaid
graph TB
    subgraph Input["Input"]
        Candidate[Candidate Profile<br/>Structured JSON]
        JobReq[Job Requirements<br/>JD + Skills + Experience]
    end

    subgraph FeatureEngineering["Feature Engineering"]
        TextEmbed[Text Embedding<br/>sentence-transformers]
        SkillExtract[Skill Extraction<br/>NER + Taxonomy]
        ExpNormalize[Experience Normalization<br/>Years + Level]
        EduScore[Education Scoring<br/>Ranking + Relevance]
    end

    subgraph Matching["Matching Engine"]
        SemanticMatch[Semantic Similarity<br/>Cosine + ANN]
        SkillMatch[Skill Matching<br/>Exact + Fuzzy + Synonym]
        ExpMatch[Experience Matching<br/>Range + Overlap]
        EduMatch[Education Matching<br/>Level + Field]
        CultureFit[Culture Fit<br/>Values + Preferences]
    end

    subgraph Scoring["Scoring & Ranking"]
        WeightedScore[Weighted Score<br/>Configurable Weights]
        Explanation[Explanation Generator<br/>SHAP + Rules]
        Ranking[Final Ranking<br/>Multi-objective]
    end

    subgraph Output["Output"]
        Matches[Ranked Match List]
        Scores[Match Scores]
        Explanations[Match Explanations]
    end

    Candidate --> TextEmbed
    Candidate --> SkillExtract
    Candidate --> ExpNormalize
    Candidate --> EduScore

    JobReq --> TextEmbed
    JobReq --> SkillExtract
    JobReq --> ExpNormalize
    JobReq --> EduScore

    TextEmbed --> SemanticMatch
    SkillExtract --> SkillMatch
    ExpNormalize --> ExpMatch
    EduScore --> EduMatch

    SemanticMatch --> WeightedScore
    SkillMatch --> WeightedScore
    ExpMatch --> WeightedScore
    EduMatch --> WeightedScore
    CultureFit --> WeightedScore

    WeightedScore --> Explanation
    Explanation --> Ranking

    Ranking --> Matches
    Ranking --> Scores
    Ranking --> Explanations
```

#### 3.3.1 Candidate Matcher Agent Specification

```python
# agents/candidate_matcher/agent.py
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class MatchTier(Enum):
    STRONG = "strong"       # Score >= 0.80
    GOOD = "good"           # Score >= 0.65
    MODERATE = "moderate"   # Score >= 0.50
    WEAK = "weak"           # Score >= 0.35
    POOR = "poor"           # Score < 0.35

@dataclass
class MatchFactor:
    factor_name: str
    weight: float
    raw_score: float  # 0.0 - 1.0
    weighted_score: float
    explanation: str
    evidence: dict = field(default_factory=dict)

@dataclass
class CandidateJobMatch:
    match_id: str
    candidate_id: str
    job_id: str
    overall_score: float  # 0.0 - 1.0
    match_tier: MatchTier
    factors: list[MatchFactor] = field(default_factory=list)
    skill_gaps: list[str] = field(default_factory=list)
    skill_overlaps: list[str] = field(default_factory=list)
    experience_alignment: Optional[str] = None
    education_alignment: Optional[str] = None
    culture_fit_score: Optional[float] = None
    recommendation: str = ""  # "strong_recommend", "recommend", "consider", "reject"
    confidence: float = 0.0
    matched_at: str = ""
    model_version: str = "1.0"
```

### 3.4 Interview Scheduler Agent

```mermaid
graph LR
    subgraph Input["Input"]
        Candidates[Candidate List<br/>Ranked Matches]
        Interviewers[Interviewer Pool<br/>Availability + Skills]
        Constraints[Constraints<br/>Time + Location + Format]
    end

    subgraph Scheduling["Scheduling Engine"]
        Availability[Availability Checker<br/>Calendar API]
        Optimizer[Schedule Optimizer<br/>Constraint Solver]
        ConflictResolver[Conflict Resolver<br/>Priority-based]
        Notifier[Notification Service<br/>Email + Slack]
    end

    subgraph Output["Output"]
        Schedule[Interview Schedule]
        Invites[Calendar Invites]
        Reminders[Reminder Queue]
    end

    subgraph External["External"]
        GoogleCal[Google Calendar]
        OutlookCal[Outlook Calendar]
        Zoom[Zoom / Meet]
        Slack[Slack API]
    end

    Candidates --> Availability
    Interviewers --> Availability
    Constraints --> Optimizer

    Availability --> Optimizer
    Optimizer --> ConflictResolver
    ConflictResolver --> Schedule

    Schedule --> Invites
    Schedule --> Reminders

    Invites --> GoogleCal
    Invites --> OutlookCal
    Invites --> Zoom
    Reminders --> Slack
```

#### 3.4.1 Interview Scheduler Agent Specification

```python
# agents/interview_scheduler/agent.py
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime

class InterviewType(Enum):
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    PANEL = "panel"
    FINAL = "final"
    CULTURE_FIT = "culture_fit"

class InterviewFormat(Enum):
    IN_PERSON = "in_person"
    VIDEO = "video"
    PHONE = "phone"
    ASYNC = "async"

class InterviewStatus(Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    timezone: str
    interviewer_ids: list[str] = field(default_factory=list)
    is_available: bool = True

@dataclass
class Interview:
    interview_id: str
    application_id: str
    candidate_id: str
    job_id: str
    interview_type: InterviewType
    format: InterviewFormat
    status: InterviewStatus
    scheduled_at: Optional[datetime] = None
    duration_minutes: int = 60
    interviewer_ids: list[str] = field(default_factory=list)
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    feedback_submitted: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
```

### 3.5 Bias Detector Agent

```mermaid
graph TB
    subgraph Input["Input"]
        Decision[Recruitment Decision<br/>Score / Ranking / Rejection]
        Demographics[Demographic Data<br/>Optional + Protected]
        Context[Decision Context<br/>Job + Stage + History]
    end

    subgraph Detection["Detection Engine"]
        ParityCheck[Demographic Parity<br/>Statistical Parity]
        EqualOpportunity[Equal Opportunity<br/>True Positive Rate]
        Calibration[Calibration Check<br/>Score Distribution]
        DisparateImpact[Disparate Impact<br/>4/5 Rule]
        LanguageBias[Language Bias<br/>Gendered + Cultural]
    end

    subgraph Analysis["Analysis"]
        RootCause[Root Cause Analysis<br/>Feature Attribution]
        Severity[Severity Scoring<br/>Low / Medium / High]
        Recommendation[Recommendation Engine<br/>Mitigation Steps]
    end

    subgraph Output["Output"]
        BiasReport[Bias Report]
        Alert[Bias Alert]
        AuditLog[Audit Log Entry]
    end

    Decision --> ParityCheck
    Demographics --> ParityCheck
    Context --> ParityCheck

    Decision --> EqualOpportunity
    Demographics --> EqualOpportunity

    Decision --> Calibration
    Demographics --> Calibration

    Decision --> DisparateImpact
    Demographics --> DisparateImpact

    Decision --> LanguageBias

    ParityCheck --> RootCause
    EqualOpportunity --> RootCause
    Calibration --> RootCause
    DisparateImpact --> RootCause
    LanguageBias --> RootCause

    RootCause --> Severity
    Severity --> Recommendation

    Severity --> BiasReport
    Severity --> Alert
    RootCause --> AuditLog
```

#### 3.5.1 Bias Detector Agent Specification

```python
# agents/bias_detector/agent.py
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum

class BiasType(Enum):
    GENDER = "gender"
    AGE = "age"
    RACE_ETHNICITY = "race_ethnicity"
    DISABILITY = "disability"
    SOCIOECONOMIC = "socioeconomic"
    EDUCATION_ELITISM = "education_elitism"
    NAME_BASED = "name_based"
    LANGUAGE = "language"
    NONE = "none"

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class BiasMetric:
    metric_name: str
    value: float
    threshold: float
    is_violation: bool
    demographic_group: Optional[str] = None
    sample_size: int = 0

@dataclass
class BiasFinding:
    finding_id: str
    bias_type: BiasType
    severity: SeverityLevel
    metric: BiasMetric
    description: str
    affected_attribute: str
    recommendation: str
    evidence: dict = field(default_factory=dict)

@dataclass
class BiasReport:
    report_id: str
    decision_id: str
    decision_type: str  # "ranking", "rejection", "scoring", "shortlisting"
    overall_bias_detected: bool
    findings: list[BiasFinding] = field(default_factory=list)
    metrics: list[BiasMetric] = field(default_factory=list)
    demographic_parity_ratio: Optional[float] = None
    equal_opportunity_diff: Optional[float] = None
    disparate_impact_ratio: Optional[float] = None
    generated_at: str = ""
    model_version: str = "1.0"
```

### 3.6 Skills Assessor Agent

```mermaid
graph TB
    subgraph Input["Input"]
        JobReq[Job Requirements<br/>Required Skills]
        Candidate[Candidate Profile<br/>Declared Skills]
        History[Assessment History<br/>Past Performance]
    end

    subgraph Assessment["Assessment Engine"]
        SkillGap[Skill Gap Analysis<br/>Required vs. Has]
        TestGen[Test Generator<br/>Adaptive Questions]
        Scoring[Response Scoring<br/>LLM + Rubric]
        Proctoring[Proctoring<br/>Integrity Checks]
    end

    subgraph Adaptive["Adaptive Logic"]
        Difficulty[Difficulty Adjustment<br/>IRT + Elo]
        Coverage[Coverage Optimization<br/>Skill Tree]
        TimeOpt[Time Optimization<br/>Pacing]
    end

    subgraph Output["Output"]
        Assessment[Assessment Report]
        SkillScores[Skill Scores]
        Recommendations[Learning Recommendations]
    end

    JobReq --> SkillGap
    Candidate --> SkillGap
    History --> Difficulty

    SkillGap --> TestGen
    TestGen --> Scoring
    Scoring --> Proctoring

    Scoring --> Difficulty
    Difficulty --> Coverage
    Coverage --> TimeOpt

    Proctoring --> Assessment
    Scoring --> SkillScores
    SkillGap --> Recommendations
```

#### 3.6.1 Skills Assessor Agent Specification

```python
# agents/skills_assessor/agent.py
from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum

class SkillLevel(Enum):
    NOVICE = 1
    BEGINNER = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

class AssessmentType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    CODING = "coding"
    CASE_STUDY = "case_study"
    BEHAVIORAL = "behavioral"
    TECHNICAL_QA = "technical_qa"
    PORTFOLIO_REVIEW = "portfolio_review"

class AssessmentStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EVALUATED = "evaluated"
    FLAGGED = "flagged"

@dataclass
class SkillAssessment:
    skill_name: str
    required_level: SkillLevel
    demonstrated_level: Optional[SkillLevel] = None
    score: Optional[float] = None  # 0.0 - 1.0
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    gap: Optional[str] = None

@dataclass
class Assessment:
    assessment_id: str
    candidate_id: str
    job_id: str
    application_id: str
    assessment_type: AssessmentType
    status: AssessmentStatus
    skill_assessments: list[SkillAssessment] = field(default_factory=list)
    overall_score: Optional[float] = None
    time_taken_minutes: Optional[int] = None
    integrity_score: Optional[float] = None  # Proctoring result
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    evaluated_at: Optional[str] = None
    evaluator_notes: Optional[str] = None
    created_at: str = ""
```

### 3.7 Agent Communication Protocol

```python
# agents/communication.py
from pydantic import BaseModel
from typing import Optional, Literal, Any
from datetime import datetime

class AgentMessage(BaseModel):
    message_id: str
    sender: str           # agent identifier
    receiver: str         # target agent or "broadcast"
    message_type: Literal[
        "parse_request", "parse_result",
        "match_request", "match_result",
        "schedule_request", "schedule_result",
        "bias_check_request", "bias_check_result",
        "assessment_request", "assessment_result",
        "status_update", "error",
    ]
    payload: dict[str, Any]
    correlation_id: str   # For request-response tracking
    timestamp: datetime = datetime.utcnow()
    priority: int = 5     # 1 (highest) - 10 (lowest)
    ttl_seconds: int = 300

class AgentEvent(BaseModel):
    event_id: str
    event_type: Literal[
        "agent_started", "agent_completed", "agent_failed",
        "decision_made", "bias_detected", "human_review_required",
        "escalation", "notification_sent",
    ]
    agent_id: str
    details: dict[str, Any]
    timestamp: datetime = datetime.utcnow()
```

---

## 4. API Design

### 4.1 API Overview

| Category | Endpoints | Description |
|----------|-----------|-------------|
| Candidates | 6 | CRUD + resume parsing + profile management |
| Jobs | 4 | Job postings + requirements management |
| Applications | 4 | Application lifecycle + status tracking |
| Interviews | 5 | Scheduling + feedback + management |
| Assessments | 4 | Skills testing + evaluation |
| Analytics | 3 | Reporting + metrics + dashboards |
| **Total** | **26** | |

### 4.2 Candidate Endpoints

#### 4.2.1 Create Candidate

```http
POST /api/v1/candidates
Content-Type: multipart/form-data

{
  "email": "jane.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "resume_file": <binary>,
  "source": "linkedin",
  "consent_given": true
}
```

**Response (201 Created):**
```json
{
  "candidate_id": "cand_abc123",
  "email": "jane.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "parse_status": "processing",
  "profile_completeness": 0.0,
  "created_at": "2026-10-02T10:30:00Z",
  "_links": {
    "self": "/api/v1/candidates/cand_abc123",
    "profile": "/api/v1/candidates/cand_abc123/profile",
    "matches": "/api/v1/candidates/cand_abc123/matches"
  }
}
```

#### 4.2.2 Get Candidate

```http
GET /api/v1/candidates/{candidate_id}
```

**Response (200 OK):**
```json
{
  "candidate_id": "cand_abc123",
  "email": "jane.doe@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "summary": "Senior software engineer with 8+ years...",
  "work_experience": [
    {
      "company": "Tech Corp",
      "title": "Senior Engineer",
      "start_date": "2020-01",
      "is_current": true,
      "skills": ["Python", "Kubernetes", "AWS"]
    }
  ],
  "education": [
    {
      "institution": "Stanford University",
      "degree": "M.S.",
      "field_of_study": "Computer Science",
      "graduation_year": 2018
    }
  ],
  "skills": [
    {"name": "Python", "level": "expert", "years": 8},
    {"name": "Kubernetes", "level": "advanced", "years": 5}
  ],
  "parse_status": "completed",
  "profile_completeness": 0.95,
  "created_at": "2026-10-02T10:30:00Z",
  "updated_at": "2026-10-02T10:30:05Z"
}
```

#### 4.2.3 Update Candidate

```http
PATCH /api/v1/candidates/{candidate_id}
Content-Type: application/json

{
  "phone": "+1-555-0456",
  "skills": [
    {"name": "Rust", "level": "intermediate", "years": 2}
  ]
}
```

#### 4.2.4 List Candidates

```http
GET /api/v1/candidates?page=1&limit=20&sort=created_at&order=desc&status=active&skill=python
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "candidate_id": "cand_abc123",
      "first_name": "Jane",
      "last_name": "Doe",
      "email": "jane.doe@example.com",
      "skills": ["Python", "Kubernetes"],
      "profile_completeness": 0.95,
      "created_at": "2026-10-02T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

#### 4.2.5 Parse Resume

```http
POST /api/v1/candidates/{candidate_id}/parse-resume
Content-Type: multipart/form-data

{
  "resume_file": <binary>,
  "parse_options": {
    "extract_skills": true,
    "extract_experience": true,
    "extract_education": true,
    "language": "en"
  }
}
```

**Response (202 Accepted):**
```json
{
  "parse_job_id": "parse_xyz789",
  "status": "processing",
  "estimated_completion": "2026-10-02T10:30:10Z",
  "_links": {
    "status": "/api/v1/parse-jobs/parse_xyz789"
  }
}
```

#### 4.2.6 Get Candidate Matches

```http
GET /api/v1/candidates/{candidate_id}/matches?job_id=job_123&min_score=0.6
```

**Response (200 OK):**
```json
{
  "candidate_id": "cand_abc123",
  "matches": [
    {
      "job_id": "job_123",
      "job_title": "Senior Software Engineer",
      "overall_score": 0.87,
      "match_tier": "strong",
      "skill_match": 0.92,
      "experience_match": 0.85,
      "education_match": 0.80,
      "recommendation": "strong_recommend",
      "explanation": "Strong match: 8/10 required skills, 8 years relevant experience..."
    }
  ]
}
```

### 4.3 Job Endpoints

#### 4.3.1 Create Job

```http
POST /api/v1/jobs
Content-Type: application/json

{
  "title": "Senior Software Engineer",
  "department": "Engineering",
  "location": "San Francisco, CA",
  "employment_type": "full_time",
  "description": "We are looking for a senior software engineer...",
  "requirements": {
    "required_skills": [
      {"name": "Python", "level": "advanced", "weight": 1.0},
      {"name": "Kubernetes", "level": "intermediate", "weight": 0.8}
    ],
    "preferred_skills": [
      {"name": "Rust", "level": "intermediate", "weight": 0.5}
    ],
    "min_experience_years": 5,
    "max_experience_years": 12,
    "education_requirements": [
      {"degree": "B.S.", "field": "Computer Science", "required": false}
    ]
  },
  "salary_range": {
    "min": 150000,
    "max": 200000,
    "currency": "USD"
  },
  "hiring_manager_id": "user_123",
  "recruiter_id": "user_456",
  "status": "draft"
}
```

**Response (201 Created):**
```json
{
  "job_id": "job_123",
  "title": "Senior Software Engineer",
  "status": "draft",
  "created_at": "2026-10-02T10:30:00Z",
  "_links": {
    "self": "/api/v1/jobs/job_123",
    "candidates": "/api/v1/jobs/job_123/candidates",
    "publish": "/api/v1/jobs/job_123/publish"
  }
}
```

#### 4.3.2 Get Job

```http
GET /api/v1/jobs/{job_id}
```

#### 4.3.3 Update Job

```http
PATCH /api/v1/jobs/{job_id}
Content-Type: application/json

{
  "status": "open",
  "description": "Updated job description..."
}
```

#### 4.3.4 List Jobs

```http
GET /api/v1/jobs?status=open&department=Engineering&location=San+Francisco&page=1&limit=20
```

### 4.4 Application Endpoints

#### 4.4.1 Create Application

```http
POST /api/v1/applications
Content-Type: application/json

{
  "candidate_id": "cand_abc123",
  "job_id": "job_123",
  "source": "linkedin",
  "cover_letter": "I am excited to apply...",
  "referral": null,
  "consent_given": true
}
```

**Response (201 Created):**
```json
{
  "application_id": "app_xyz789",
  "candidate_id": "cand_abc123",
  "job_id": "job_123",
  "status": "new",
  "match_score": 0.87,
  "bias_check_status": "pending",
  "created_at": "2026-10-02T10:30:00Z",
  "_links": {
    "self": "/api/v1/applications/app_xyz789",
    "interviews": "/api/v1/applications/app_xyz789/interviews",
    "assessments": "/api/v1/applications/app_xyz789/assessments"
  }
}
```

#### 4.4.2 Get Application

```http
GET /api/v1/applications/{application_id}
```

#### 4.4.3 Update Application Status

```http
PATCH /api/v1/applications/{application_id}
Content-Type: application/json

{
  "status": "screening",
  "notes": "Strong technical background, moving to screening."
}
```

#### 4.4.4 List Applications

```http
GET /api/v1/applications?job_id=job_123&status=new&page=1&limit=20
```

### 4.5 Interview Endpoints

#### 4.5.1 Schedule Interview

```http
POST /api/v1/interviews
Content-Type: application/json

{
  "application_id": "app_xyz789",
  "interview_type": "technical",
  "format": "video",
  "duration_minutes": 60,
  "interviewer_ids": ["user_123", "user_456"],
  "preferred_time_slots": [
    {
      "start_time": "2026-10-05T14:00:00Z",
      "end_time": "2026-10-05T15:00:00Z"
    }
  ],
  "timezone": "America/Los_Angeles",
  "notes": "Focus on system design and Kubernetes"
}
```

**Response (201 Created):**
```json
{
  "interview_id": "int_abc123",
  "application_id": "app_xyz789",
  "interview_type": "technical",
  "format": "video",
  "status": "scheduled",
  "scheduled_at": "2026-10-05T14:00:00Z",
  "duration_minutes": 60,
  "interviewer_ids": ["user_123", "user_456"],
  "meeting_link": "https://zoom.us/j/123456789",
  "created_at": "2026-10-02T10:30:00Z"
}
```

#### 4.5.2 Get Interview

```http
GET /api/v1/interviews/{interview_id}
```

#### 4.5.3 Reschedule Interview

```http
PATCH /api/v1/interviews/{interview_id}
Content-Type: application/json

{
  "scheduled_at": "2026-10-06T10:00:00Z",
  "reason": "Interviewer conflict"
}
```

#### 4.5.4 Submit Interview Feedback

```http
POST /api/v1/interviews/{interview_id}/feedback
Content-Type: application/json

{
  "overall_rating": 4,
  "skill_ratings": [
    {"skill": "Python", "rating": 5, "notes": "Excellent depth"},
    {"skill": "Kubernetes", "rating": 4, "notes": "Strong operational knowledge"}
  ],
  "recommendation": "advance",
  "notes": "Strong candidate, recommend for next round",
  "confidential_notes": "Salary expectations may be high"
}
```

#### 4.5.5 List Interviews

```http
GET /api/v1/interviews?application_id=app_xyz789&status=scheduled&from=2026-10-01&to=2026-10-31
```

### 4.6 Assessment Endpoints

#### 4.6.1 Create Assessment

```http
POST /api/v1/assessments
Content-Type: application/json

{
  "application_id": "app_xyz789",
  "assessment_type": "technical_qa",
  "skills_to_assess": ["Python", "Kubernetes", "System Design"],
  "difficulty_level": "adaptive",
  "time_limit_minutes": 90,
  "proctoring_enabled": true
}
```

**Response (201 Created):**
```json
{
  "assessment_id": "assess_xyz789",
  "application_id": "app_xyz789",
  "assessment_type": "technical_qa",
  "status": "pending",
  "skills_to_assess": ["Python", "Kubernetes", "System Design"],
  "time_limit_minutes": 90,
  "proctoring_enabled": true,
  "created_at": "2026-10-02T10:30:00Z",
  "_links": {
    "self": "/api/v1/assessments/assess_xyz789",
    "start": "/api/v1/assessments/assess_xyz789/start"
  }
}
```

#### 4.6.2 Get Assessment

```http
GET /api/v1/assessments/{assessment_id}
```

#### 4.6.3 Submit Assessment Response

```http
POST /api/v1/assessments/{assessment_id}/submit
Content-Type: application/json

{
  "responses": [
    {
      "question_id": "q_123",
      "answer": "Kubernetes uses a declarative API...",
      "time_spent_seconds": 120
    }
  ],
  "time_taken_minutes": 75
}
```

#### 4.6.4 Get Assessment Results

```http
GET /api/v1/assessments/{assessment_id}/results
```

**Response (200 OK):**
```json
{
  "assessment_id": "assess_xyz789",
  "status": "evaluated",
  "overall_score": 0.82,
  "skill_scores": [
    {"skill": "Python", "score": 0.90, "level": "expert"},
    {"skill": "Kubernetes", "score": 0.75, "level": "advanced"},
    {"skill": "System Design", "score": 0.80, "level": "advanced"}
  ],
  "integrity_score": 0.98,
  "time_taken_minutes": 75,
  "evaluated_at": "2026-10-02T11:45:00Z"
}
```

### 4.7 Analytics Endpoints

#### 4.7.1 Recruitment Funnel

```http
GET /api/v1/analytics/funnel?job_id=job_123&from=2026-09-01&to=2026-10-01
```

**Response (200 OK):**
```json
{
  "job_id": "job_123",
  "stages": [
    {"stage": "applied", "count": 150},
    {"stage": "screening", "count": 80},
    {"stage": "interview", "count": 40},
    {"stage": "assessment", "count": 25},
    {"stage": "offer", "count": 10},
    {"stage": "hired", "count": 5}
  ],
  "conversion_rates": {
    "applied_to_screening": 0.53,
    "screening_to_interview": 0.50,
    "interview_to_assessment": 0.63,
    "assessment_to_offer": 0.40,
    "offer_to_hired": 0.50
  },
  "time_to_hire_days": 28
}
```

#### 4.7.2 Bias Metrics

```http
GET /api/v1/analytics/bias?job_id=job_123&from=2026-09-01&to=2026-10-01
```

**Response (200 OK):**
```json
{
  "job_id": "job_123",
  "demographic_parity": {
    "gender": {"male": 0.55, "female": 0.45, "ratio": 0.82},
    "ethnicity": {"white": 0.50, "asian": 0.30, "other": 0.20}
  },
  "equal_opportunity": {
    "gender": {"male_tpr": 0.75, "female_tpr": 0.72, "diff": 0.03}
  },
  "disparate_impact": {
    "gender_ratio": 0.82,
    "threshold": 0.80,
    "is_violation": false
  },
  "bias_findings_count": 2,
  "last_updated": "2026-10-02T10:30:00Z"
}
```

#### 4.7.3 Recruiter Performance

```http
GET /api/v1/analytics/recruiter-performance?recruiter_id=user_456&from=2026-09-01&to=2026-10-01
```

### 4.8 WebSocket Events

```javascript
// WebSocket connection
const ws = new WebSocket('wss://api.grc-claw.com/ws/v1/recruitment');

// Events
{
  "event": "candidate.created",
  "data": { "candidate_id": "cand_abc123", "timestamp": "..." }
}

{
  "event": "resume.parsed",
  "data": { "candidate_id": "cand_abc123", "parse_status": "completed", "confidence": 0.95 }
}

{
  "event": "match.found",
  "data": { "candidate_id": "cand_abc123", "job_id": "job_123", "score": 0.87 }
}

{
  "event": "interview.scheduled",
  "data": { "interview_id": "int_abc123", "scheduled_at": "2026-10-05T14:00:00Z" }
}

{
  "event": "bias.detected",
  "data": { "application_id": "app_xyz789", "severity": "medium", "bias_type": "gender" }
}

{
  "event": "application.status_changed",
  "data": { "application_id": "app_xyz789", "old_status": "new", "new_status": "screening" }
}
```

---

## 5. Data Models

### 5.1 Entity Relationship Diagram

```mermaid
erDiagram
    CANDIDATE ||--o{ APPLICATION : applies
    JOB ||--o{ APPLICATION : receives
    CANDIDATE ||--o| RESUME : has
    JOB ||--o| JOB_REQUIREMENT : defines
    APPLICATION ||--o{ INTERVIEW : schedules
    APPLICATION ||--o{ ASSESSMENT : takes
    INTERVIEW ||--o{ INTERVIEW_FEEDBACK : receives
    ASSESSMENT ||--o{ SKILL_ASSESSMENT : evaluates
    CANDIDATE ||--o{ SKILL : possesses
    JOB ||--o{ SKILL : requires
    USER ||--o{ INTERVIEW : conducts
    USER ||--o{ JOB : manages

    CANDIDATE {
        uuid candidate_id PK
        string email UK
        string first_name
        string last_name
        string phone
        string location
        string linkedin_url
        string summary
        jsonb skills
        jsonb work_experience
        jsonb education
        jsonb certifications
        jsonb languages
        string parse_status
        float profile_completeness
        string source
        boolean consent_given
        timestamp created_at
        timestamp updated_at
    }

    RESUME {
        uuid resume_id PK
        uuid candidate_id FK
        string file_path
        string file_type
        text raw_text
        jsonb parsed_data
        float parse_confidence
        string parse_status
        string parsing_version
        timestamp parsed_at
        timestamp created_at
    }

    JOB {
        uuid job_id PK
        string title
        string department
        string location
        string employment_type
        text description
        jsonb requirements
        jsonb salary_range
        uuid hiring_manager_id FK
        uuid recruiter_id FK
        string status
        timestamp posted_at
        timestamp closed_at
        timestamp created_at
        timestamp updated_at
    }

    JOB_REQUIREMENT {
        uuid requirement_id PK
        uuid job_id FK
        string requirement_type
        string skill_name
        string skill_level
        float weight
        boolean is_required
        int min_years
        int max_years
    }

    APPLICATION {
        uuid application_id PK
        uuid candidate_id FK
        uuid job_id FK
        string source
        text cover_letter
        string referral
        string status
        float match_score
        string bias_check_status
        timestamp applied_at
        timestamp created_at
        timestamp updated_at
    }

    INTERVIEW {
        uuid interview_id PK
        uuid application_id FK
        string interview_type
        string format
        string status
        timestamp scheduled_at
        int duration_minutes
        jsonb interviewer_ids
        string location
        string meeting_link
        text notes
        boolean feedback_submitted
        timestamp created_at
        timestamp updated_at
    }

    INTERVIEW_FEEDBACK {
        uuid feedback_id PK
        uuid interview_id FK
        uuid interviewer_id FK
        int overall_rating
        jsonb skill_ratings
        string recommendation
        text notes
        text confidential_notes
        timestamp submitted_at
    }

    ASSESSMENT {
        uuid assessment_id PK
        uuid application_id FK
        string assessment_type
        string status
        jsonb skills_to_assess
        float overall_score
        int time_taken_minutes
        float integrity_score
        timestamp started_at
        timestamp completed_at
        timestamp evaluated_at
        timestamp created_at
    }

    SKILL_ASSESSMENT {
        uuid skill_assessment_id PK
        uuid assessment_id FK
        string skill_name
        int required_level
        int demonstrated_level
        float score
        float confidence
        jsonb evidence
    }

    SKILL {
        uuid skill_id PK
        string name UK
        string category
        string description
        jsonb synonyms
        jsonb related_skills
    }

    USER {
        uuid user_id PK
        string email UK
        string first_name
        string last_name
        string role
        string department
        jsonb calendar_settings
        timestamp created_at
    }
```

### 5.2 Candidate Model

```python
# models/candidate.py
from sqlalchemy import Column, String, DateTime, Float, Boolean, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

class Candidate(Base):
    __tablename__ = "candidates"

    candidate_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    location = Column(String(200))
    linkedin_url = Column(String(500))
    summary = Column(String(5000))
    
    # Structured data (populated by Resume Parser)
    skills = Column(JSON, default=list)  # [{"name": "Python", "level": "expert", "years": 8}]
    work_experience = Column(JSON, default=list)  # [{"company": "...", "title": "...", ...}]
    education = Column(JSON, default=list)  # [{"institution": "...", "degree": "...", ...}]
    certifications = Column(JSON, default=list)
    languages = Column(JSON, default=list)
    
    # Parsing metadata
    parse_status = Column(String(20), default="pending", index=True)
    profile_completeness = Column(Float, default=0.0)
    
    # Source tracking
    source = Column(String(50), index=True)  # "linkedin", "referral", "job_board", etc.
    consent_given = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate")
    
    def to_dict(self):
        return {
            "candidate_id": str(self.candidate_id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "summary": self.summary,
            "skills": self.skills,
            "work_experience": self.work_experience,
            "education": self.education,
            "certifications": self.certifications,
            "languages": self.languages,
            "parse_status": self.parse_status,
            "profile_completeness": self.profile_completeness,
            "source": self.source,
            "consent_given": self.consent_given,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
```

### 5.3 Job Model

```python
# models/job.py
class Job(Base):
    __tablename__ = "jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False, index=True)
    department = Column(String(100), index=True)
    location = Column(String(200), index=True)
    employment_type = Column(String(50))  # "full_time", "part_time", "contract"
    description = Column(String(10000))
    
    # Structured requirements
    requirements = Column(JSON, default=dict)  # {"required_skills": [...], "min_experience_years": 5, ...}
    salary_range = Column(JSON)  # {"min": 150000, "max": 200000, "currency": "USD"}
    
    # Team
    hiring_manager_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    
    # Status
    status = Column(String(20), default="draft", index=True)  # "draft", "open", "paused", "closed"
    posted_at = Column(DateTime)
    closed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    applications = relationship("Application", back_populates="job")
    job_requirements = relationship("JobRequirement", back_populates="job", cascade="all, delete-orphan")
```

### 5.4 Application Model

```python
# models/application.py
class Application(Base):
    __tablename__ = "applications"

    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.candidate_id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.job_id"), nullable=False)
    
    # Application details
    source = Column(String(50), index=True)
    cover_letter = Column(String(10000))
    referral = Column(String(200))
    
    # Status workflow
    status = Column(String(30), default="new", index=True)
    # "new" -> "screening" -> "interview" -> "assessment" -> "offer" -> "hired" / "rejected"
    
    # AI-generated scores
    match_score = Column(Float)
    bias_check_status = Column(String(20), default="pending")  # "pending", "completed", "flagged"
    
    # Timestamps
    applied_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    interviews = relationship("Interview", back_populates="application", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="application", cascade="all, delete-orphan")
```

### 5.5 Interview Model

```python
# models/interview.py
class Interview(Base):
    __tablename__ = "interviews"

    interview_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.application_id"), nullable=False)
    
    # Interview details
    interview_type = Column(String(30), nullable=False)  # "phone_screen", "technical", "behavioral", "panel", "final"
    format = Column(String(20), nullable=False)  # "in_person", "video", "phone", "async"
    status = Column(String(20), default="scheduled", index=True)
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    interviewer_ids = Column(ARRAY(UUID(as_uuid=True)))
    location = Column(String(500))
    meeting_link = Column(String(500))
    notes = Column(String(5000))
    
    # Feedback
    feedback_submitted = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="interviews")
    feedback = relationship("InterviewFeedback", back_populates="interview", cascade="all, delete-orphan")
```

### 5.6 Assessment Model

```python
# models/assessment.py
class Assessment(Base):
    __tablename__ = "assessments"

    assessment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.application_id"), nullable=False)
    
    # Assessment details
    assessment_type = Column(String(30), nullable=False)  # "technical_qa", "coding", "case_study", "behavioral"
    status = Column(String(20), default="pending", index=True)
    
    # Configuration
    skills_to_assess = Column(ARRAY(String))
    difficulty_level = Column(String(20), default="adaptive")  # "easy", "medium", "hard", "adaptive"
    time_limit_minutes = Column(Integer, default=60)
    proctoring_enabled = Column(Boolean, default=True)
    
    # Results
    overall_score = Column(Float)
    time_taken_minutes = Column(Integer)
    integrity_score = Column(Float)  # Proctoring result
    
    # Timestamps
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    evaluated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    application = relationship("Application", back_populates="assessments")
    skill_assessments = relationship("SkillAssessment", back_populates="assessment", cascade="all, delete-orphan")
```

---

## 6. Integration Patterns

### 6.1 GRC_Claw Infrastructure Integration

```mermaid
graph TB
    subgraph Recruitment["Recruitment Platform"]
        Agents[Recruitment Agents]
        API[Recruitment API]
        Events[Event Publishers]
    end

    subgraph GRC["GRC_Claw Control Plane"]
        Identity[Identity Service<br/>DID + OAuth2]
        Policy[Policy Engine<br/>OPA / Rego]
        Audit[Audit Service<br/>Merkle Chain]
        AgentReg[Agent Registry<br/>Discovery + Health]
        EventBus[Event Bus<br/>Kafka]
        Notification[Notification Service]
        Config[Config Service<br/>YAML + Secrets]
    end

    subgraph Shared["Shared Infrastructure"]
        DB[(PostgreSQL)]
        Cache[(Redis)]
        Storage[(S3 / MinIO)]
        Queue[Message Queue]
        Search[Vector DB]
    end

    subgraph External["External Integrations"]
        ATS[Greenhouse / Lever]
        Calendar[Google / Outlook]
        Email[SendGrid / SES]
        Slack[Slack API]
        LinkedIn[LinkedIn API]
        JobBoards[Indeed / Glassdoor]
    end

    Agents --> Identity
    Agents --> Policy
    Agents --> Audit
    Agents --> AgentReg

    API --> Identity
    API --> Policy
    API --> Audit

    Agents --> Events
    Events --> EventBus
    EventBus --> Notification
    Notification --> Email
    Notification --> Slack

    Agents --> DB
    API --> DB
    Agents --> Cache
    Agents --> Storage
    Agents --> Search

    API --> ATS
    Agents --> Calendar
    Agents --> LinkedIn
    API --> JobBoards

    Config --> Agents
    Config --> API
```

### 6.2 Identity & Access Integration

```python
# integrations/grc_claw_identity.py
from fastapi import Depends, HTTPException
from typing import Optional

class GRCClawIdentityProvider:
    """Integrates with GRC_Claw Identity Service for authentication and authorization."""
    
    def __init__(self, identity_service_url: str):
        self.identity_url = identity_service_url
    
    async def authenticate(self, token: str) -> dict:
        """Validate JWT token against GRC_Claw Identity Service."""
        # Verify token signature, expiry, and issuer
        # Return user context with roles and permissions
        pass
    
    async def authorize(self, user: dict, resource: str, action: str) -> bool:
        """Check if user has permission to perform action on resource."""
        # Query GRC_Claw Policy Engine (OPA)
        # Return allow/deny decision
        pass
    
    async def get_agent_identity(self, agent_id: str) -> dict:
        """Get DID and capabilities for an agent."""
        # Return agent's decentralized identity
        pass

# FastAPI dependency
async def get_current_user(token: str = Depends(oauth2_scheme)):
    identity = GRCClawIdentityProvider(settings.IDENTITY_SERVICE_URL)
    user = await identity.authenticate(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

async def require_permission(resource: str, action: str):
    async def checker(user: dict = Depends(get_current_user)):
        identity = GRCClawIdentityProvider(settings.IDENTITY_SERVICE_URL)
        if not await identity.authorize(user, resource, action):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker
```

### 6.3 Policy Engine Integration

```python
# integrations/grc_claw_policy.py
import httpx
from typing import Any

class GRCPolicyEngine:
    """Integrates with GRC_Claw OPA Policy Engine for governance."""
    
    def __init__(self, opa_url: str):
        self.opa_url = opa_url
    
    async def evaluate(self, policy_name: str, input_data: dict) -> dict:
        """Evaluate a policy against input data."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.opa_url}/v1/data/recruitment/{policy_name}",
                json={"input": input_data}
            )
            return response.json()
    
    async def check_match_allowed(self, candidate_id: str, job_id: str) -> dict:
        """Check if candidate matching is allowed by policy."""
        return await self.evaluate("matching", {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "action": "match"
        })
    
    async def check_bias_threshold(self, bias_report: dict) -> dict:
        """Check if bias report exceeds policy thresholds."""
        return await self.evaluate("bias", {
            "bias_report": bias_report,
            "action": "evaluate"
        })
    
    async def check_data_retention(self, candidate_id: str) -> dict:
        """Check data retention policy for candidate."""
        return await self.evaluate("data_retention", {
            "candidate_id": candidate_id,
            "action": "check"
        })
```

### 6.4 Audit Trail Integration

```python
# integrations/grc_claw_audit.py
import hashlib
import json
from datetime import datetime
from typing import Any

class GRCAuditLogger:
    """Integrates with GRC_Claw Merkle Audit Chain for tamper-evident logging."""
    
    def __init__(self, audit_service_url: str):
        self.audit_url = audit_service_url
        self.local_chain = []
    
    async def log_decision(self, decision_type: str, context: dict, outcome: dict) -> str:
        """Log a recruitment decision to the audit chain."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision_type": decision_type,  # "match", "rank", "reject", "schedule"
            "context": context,
            "outcome": outcome,
            "previous_hash": self._get_last_hash(),
        }
        
        # Calculate hash for tamper evidence
        entry_hash = self._calculate_hash(entry)
        entry["hash"] = entry_hash
        
        # Submit to GRC_Claw Audit Service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.audit_url}/api/v1/audit/log",
                json=entry
            )
            result = response.json()
        
        self.local_chain.append(entry)
        return result["audit_id"]
    
    def _calculate_hash(self, entry: dict) -> str:
        """Calculate SHA-256 hash of audit entry."""
        data = json.dumps(entry, sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _get_last_hash(self) -> str:
        """Get hash of last entry in chain."""
        if not self.local_chain:
            return "0" * 64  # Genesis hash
        return self.local_chain[-1]["hash"]
    
    async def verify_chain(self) -> bool:
        """Verify integrity of local audit chain."""
        for i in range(1, len(self.local_chain)):
            current = self.local_chain[i]
            previous = self.local_chain[i - 1]
            if current["previous_hash"] != previous["hash"]:
                return False
            if self._calculate_hash(current) != current["hash"]:
                return False
        return True
```

### 6.5 Event Bus Integration

```python
# integrations/event_bus.py
from confluent_kafka import Producer, Consumer, KafkaError
from typing import Callable
import json

class RecruitmentEventBus:
    """Kafka-based event bus for recruitment platform events."""
    
    def __init__(self, bootstrap_servers: str):
        self.producer = Producer({
            "bootstrap.servers": bootstrap_servers,
            "client.id": "recruitment-platform",
        })
        
        self.consumer = Consumer({
            "bootstrap.servers": bootstrap_servers,
            "group.id": "recruitment-platform",
            "auto.offset.reset": "earliest",
        })
    
    def publish(self, topic: str, event: dict):
        """Publish event to Kafka topic."""
        self.producer.produce(
            topic=topic,
            key=event.get("event_id", ""),
            value=json.dumps(event),
            callback=self._delivery_callback
        )
        self.producer.flush()
    
    def subscribe(self, topics: list[str], handler: Callable):
        """Subscribe to topics and process events."""
        self.consumer.subscribe(topics)
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise Exception(msg.error())
            event = json.loads(msg.value().decode("utf-8"))
            handler(event)
    
    def _delivery_callback(self, err, msg):
        if err:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()}")
```

### 6.6 ATS Integration

```python
# integrations/ats_connector.py
from abc import ABC, abstractmethod
from typing import Optional

class ATSConnector(ABC):
    """Abstract base class for ATS integrations."""
    
    @abstractmethod
    async def sync_candidate(self, candidate: dict) -> str:
        """Sync candidate to ATS, return ATS candidate ID."""
        pass
    
    @abstractmethod
    async def sync_job(self, job: dict) -> str:
        """Sync job to ATS, return ATS job ID."""
        pass
    
    @abstractmethod
    async def update_application_status(self, ats_application_id: str, status: str):
        """Update application status in ATS."""
        pass
    
    @abstractmethod
    async def fetch_candidates(self, filters: dict) -> list[dict]:
        """Fetch candidates from ATS."""
        pass

class GreenhouseConnector(ATSConnector):
    """Greenhouse ATS integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://harvest.greenhouse.io/v1"
    
    async def sync_candidate(self, candidate: dict) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/candidates",
                json={
                    "first_name": candidate["first_name"],
                    "last_name": candidate["last_name"],
                    "email_addresses": [{"value": candidate["email"], "type": "personal"}],
                    "applications": []
                },
                headers={"Authorization": f"Basic {self.api_key}"}
            )
            result = response.json()
            return result["id"]
    
    async def sync_job(self, job: dict) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/jobs",
                json={
                    "title": job["title"],
                    "location": {"name": job["location"]},
                    "notes": job["description"]
                },
                headers={"Authorization": f"Basic {self.api_key}"}
            )
            result = response.json()
            return result["id"]

class LeverConnector(ATSConnector):
    """Lever ATS integration."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.lever.co/v1"
    
    async def sync_candidate(self, candidate: dict) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/candidates",
                json={
                    "name": f"{candidate['first_name']} {candidate['last_name']}",
                    "emails": [candidate["email"]],
                    "phones": [{"value": candidate.get("phone", "")}],
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            result = response.json()
            return result["data"]["id"]
```

### 6.7 Calendar Integration

```python
# integrations/calendar_connector.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta

class CalendarConnector:
    """Google Calendar / Outlook integration for interview scheduling."""
    
    def __init__(self, credentials: Credentials):
        self.service = build("calendar", "v3", credentials=credentials)
    
    async def get_availability(
        self,
        user_ids: list[str],
        start_time: datetime,
        end_time: datetime,
        duration_minutes: int = 60
    ) -> list[dict]:
        """Get available time slots for interviewers."""
        # Query free/busy for all interviewers
        freebusy_request = {
            "timeMin": start_time.isoformat(),
            "timeMax": end_time.isoformat(),
            "items": [{"id": user_id} for user_id in user_ids]
        }
        
        response = self.service.freebusy().query(body=freebusy_request).execute()
        
        # Find overlapping free slots
        available_slots = self._find_common_free_slots(
            response["calendars"],
            start_time,
            end_time,
            duration_minutes
        )
        
        return available_slots
    
    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str],
        description: str = "",
        location: str = "",
        conference_data: dict = None
    ) -> dict:
        """Create calendar event with video conference link."""
        event = {
            "summary": title,
            "start": {"dateTime": start_time.isoformat()},
            "end": {"dateTime": end_time.isoformat()},
            "attendees": [{"email": email} for email in attendees],
            "description": description,
            "location": location,
        }
        
        if conference_data:
            event["conferenceData"] = conference_data
        
        result = self.service.events().insert(
            calendarId="primary",
            body=event,
            conferenceDataVersion=1
        ).execute()
        
        return result
    
    async def update_event(self, event_id: str, updates: dict) -> dict:
        """Update existing calendar event."""
        event = self.service.events().get(
            calendarId="primary",
            eventId=event_id
        ).execute()
        
        for key, value in updates.items():
            event[key] = value
        
        result = self.service.events().update(
            calendarId="primary",
            eventId=event_id,
            body=event
        ).execute()
        
        return result
    
    async def delete_event(self, event_id: str):
        """Delete calendar event."""
        self.service.events().delete(
            calendarId="primary",
            eventId=event_id
        ).execute()
```

---

## 7. Security & Compliance

### 7.1 Security Architecture

```mermaid
graph TB
    subgraph Edge["Edge Security"]
        WAF[WAF / CDN]
        DDoS[DDoS Protection]
        RateLimit[Rate Limiting]
    end

    subgraph Auth["Authentication & Authorization"]
        OAuth[OAuth 2.0 / OIDC]
        MFA[Multi-Factor Auth]
        RBAC[Role-Based Access]
        ABAC[Attribute-Based Access]
    end

    subgraph API["API Security"]
        InputVal[Input Validation]
        OutputSan[Output Sanitization]
        CORS[CORS Policy]
        CSP[Content Security Policy]
    end

    subgraph Data["Data Security"]
        Encryption[Encryption at Rest<br/>AES-256]
        TLS[TLS 1.3 in Transit]
        Tokeniz[Tokenization<br/>PII Fields]
        Masking[Data Masking<br/>Non-prod]
    end

    subgraph Audit["Audit & Monitoring"]
        AuditLog[Audit Logging<br/>Merkle Chain]
        Anomaly[Anomaly Detection]
        Alerting[Security Alerting]
        Compliance[Compliance Reports<br/>GDPR / CCPA]
    end

    WAF --> DDoS --> RateLimit --> OAuth
    OAuth --> MFA --> RBAC --> ABAC
    ABAC --> InputVal --> OutputSan --> CORS --> CSP
    CSP --> Encryption --> TLS --> Tokeniz --> Masking
    Masking --> AuditLog --> Anomaly --> Alerting --> Compliance
```

### 7.2 Data Privacy

```python
# security/data_privacy.py
from cryptography.fernet import Fernet
from typing import Optional

class DataPrivacyManager:
    """Manages PII data encryption, tokenization, and anonymization."""
    
    def __init__(self, encryption_key: bytes):
        self.cipher = Fernet(encryption_key)
        self.pii_fields = [
            "email", "phone", "first_name", "last_name",
            "address", "date_of_birth", "ssn"
        ]
    
    def encrypt_pii(self, data: dict) -> dict:
        """Encrypt PII fields in data."""
        encrypted = data.copy()
        for field in self.pii_fields:
            if field in encrypted and encrypted[field]:
                encrypted[field] = self.cipher.encrypt(
                    encrypted[field].encode()
                ).decode()
        return encrypted
    
    def decrypt_pii(self, data: dict) -> dict:
        """Decrypt PII fields in data."""
        decrypted = data.copy()
        for field in self.pii_fields:
            if field in decrypted and decrypted[field]:
                decrypted[field] = self.cipher.decrypt(
                    decrypted[field].encode()
                ).decode()
        return decrypted
    
    def tokenize(self, value: str) -> str:
        """Create reversible token for PII."""
        return self.cipher.encrypt(value.encode()).decode()
    
    def detokenize(self, token: str) -> str:
        """Reverse token to original value."""
        return self.cipher.decrypt(token.encode()).decode()
    
    def anonymize(self, data: dict) -> dict:
        """Anonymize data for analytics (irreversible)."""
        anonymized = data.copy()
        for field in self.pii_fields:
            if field in anonymized:
                anonymized[field] = self._hash(anonymized[field])
        return anonymized
    
    def _hash(self, value: str) -> str:
        """One-way hash for anonymization."""
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()[:16]
```

### 7.3 GDPR Compliance

```python
# security/gdpr_compliance.py
from datetime import datetime, timedelta
from typing import Optional

class GDPRComplianceManager:
    """Manages GDPR compliance for candidate data."""
    
    def __init__(self, db_session, audit_logger):
        self.db = db_session
        self.audit = audit_logger
    
    async def handle_data_export_request(self, candidate_id: str) -> dict:
        """Handle GDPR data portability request (Article 20)."""
        # Gather all candidate data
        candidate = await self.db.get_candidate(candidate_id)
        applications = await self.db.get_applications(candidate_id)
        interviews = await self.db.get_interviews(candidate_id)
        assessments = await self.db.get_assessments(candidate_id)
        
        export_data = {
            "candidate": candidate,
            "applications": applications,
            "interviews": interviews,
            "assessments": assessments,
            "export_date": datetime.utcnow().isoformat(),
            "format": "JSON"
        }
        
        # Log the export
        await self.audit.log_decision(
            "gdpr_data_export",
            {"candidate_id": candidate_id},
            {"status": "completed"}
        )
        
        return export_data
    
    async def handle_deletion_request(self, candidate_id: str) -> bool:
        """Handle GDPR right to erasure request (Article 17)."""
        # Anonymize instead of delete to preserve analytics integrity
        await self.db.anonymize_candidate(candidate_id)
        
        # Delete PII fields
        await self.db.delete_candidate_pii(candidate_id)
        
        # Log the deletion
        await self.audit.log_decision(
            "gdpr_data_deletion",
            {"candidate_id": candidate_id},
            {"status": "completed", "method": "anonymization"}
        )
        
        return True
    
    async def check_consent(self, candidate_id: str, purpose: str) -> bool:
        """Check if candidate has given consent for data processing."""
        consent = await self.db.get_consent(candidate_id, purpose)
        return consent is not None and consent.get("granted", False)
    
    async def record_consent(self, candidate_id: str, purpose: str, granted: bool):
        """Record candidate consent for data processing."""
        await self.db.record_consent({
            "candidate_id": candidate_id,
            "purpose": purpose,
            "granted": granted,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": "recorded",  # Actual IP from request
            "user_agent": "recorded"   # Actual UA from request
        })
```

---

## 8. Deployment Architecture

### 8.1 Kubernetes Deployment

```mermaid
graph TB
    subgraph Ingress["Ingress Layer"]
        Ingress[NGINX Ingress Controller]
        CertManager[Cert Manager]
    end

    subgraph API["API Layer"]
        APIPod1[API Pod 1]
        APIPod2[API Pod 2]
        APIPod3[API Pod 3]
    end

    subgraph Agents["Agent Layer"]
        Orchestrator[Orchestrator Pod]
        ResumeParser[Resume Parser Pod]
        Matcher[Candidate Matcher Pod]
        Scheduler[Interview Scheduler Pod]
        BiasDetector[Bias Detector Pod]
        Assessor[Skills Assessor Pod]
    end

    subgraph Workers["Worker Layer"]
        CeleryWorker1[Celery Worker 1]
        CeleryWorker2[Celery Worker 2]
        CeleryBeat[Celery Beat]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>Primary + Replicas)]
        Redis[(Redis Cluster)]
        Kafka[(Kafka Cluster)]
        MinIO[(MinIO / S3)]
        VectorDB[(pgvector)]
    end

    subgraph ML["ML Infrastructure"]
        MLflow[MLflow Server]
        ModelServing[Model Serving<br/>Triton / TorchServe]
        Airflow[Airflow]
    end

    subgraph Monitoring["Monitoring"]
        Prometheus[Prometheus]
        Grafana[Grafana]
        Jaeger[Jaeger Tracing]
        ELK[ELK Stack]
    end

    Ingress --> APIPod1
    Ingress --> APIPod2
    Ingress --> APIPod3

    APIPod1 --> Orchestrator
    APIPod2 --> Orchestrator
    APIPod3 --> Orchestrator

    Orchestrator --> ResumeParser
    Orchestrator --> Matcher
    Orchestrator --> Scheduler
    Orchestrator --> BiasDetector
    Orchestrator --> Assessor

    ResumeParser --> CeleryWorker1
    Matcher --> CeleryWorker2
    Scheduler --> CeleryWorker1

    APIPod1 --> PG
    APIPod2 --> PG
    APIPod3 --> PG

    Orchestrator --> Redis
    Orchestrator --> Kafka
    Orchestrator --> MinIO
    Matcher --> VectorDB

    Matcher --> MLflow
    Assessor --> MLflow
    Matcher --> ModelServing
    Assessor --> ModelServing

    Airflow --> MLflow

    Prometheus --> APIPod1
    Prometheus --> Orchestrator
    Prometheus --> PG
    Prometheus --> Redis
    Prometheus --> Kafka
```

### 8.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - MLFLOW_TRACKING_URI=http://mlflow:5000
      - IDENTITY_SERVICE_URL=http://identity:8080
      - POLICY_ENGINE_URL=http://opa:8181
      - AUDIT_SERVICE_URL=http://audit:8081
    depends_on:
      - db
      - redis
      - kafka
      - mlflow
    volumes:
      - ./src:/app/src
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - db
      - redis
      - kafka
    command: python -m agents.orchestrator

  resume-parser:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - S3_ENDPOINT=http://minio:9000
    depends_on:
      - db
      - redis
      - minio
    command: python -m agents.resume_parser

  candidate-matcher:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - db
      - redis
      - mlflow
    command: python -m agents.candidate_matcher

  interview-scheduler:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: python -m agents.interview_scheduler

  bias-detector:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: python -m agents.bias_detector

  skills-assessor:
    build:
      context: .
      dockerfile: Dockerfile.agents
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - db
      - redis
      - mlflow
    command: python -m agents.skills_assessor

  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A src.tasks worker --loglevel=info

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/recruitment
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: celery -A src.tasks beat --loglevel=info

  db:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=recruitment
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    ports:
      - "9092:9092"
    environment:
      - KAFKA_BROKER_ID=1
      - KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
      - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      - ZOOKEEPER_CLIENT_PORT=2181

  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      - MINIO_ROOT_USER=minioadmin
      - MINIO_ROOT_PASSWORD=minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  mlflow:
    image: mlflow/mlflow:latest
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://postgres:postgres@db:5432/mlflow
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=s3://mlflow-artifacts
      - AWS_ACCESS_KEY_ID=minioadmin
      - AWS_SECRET_ACCESS_KEY=minioadmin
      - MLFLOW_S3_ENDPOINT_URL=http://minio:9000
    depends_on:
      - db
      - minio

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  minio_data:
  grafana_data:
```

---

## 9. Observability & Monitoring

### 9.1 Monitoring Stack

```mermaid
graph LR
    subgraph Apps["Applications"]
        API[API Services]
        Agents[Agent Services]
        Workers[Worker Services]
    end

    subgraph Collection["Collection"]
        Prom[Prometheus]
        OTel[OpenTelemetry]
        Jaeger[Jaeger]
    end

    subgraph Storage["Storage"]
        TSDB[(Prometheus TSDB)]
        TraceStore[(Jaeger Storage)]
        LogStore[(ELK / Loki)]
    end

    subgraph Visualization["Visualization"]
        Grafana[Grafana]
        Dashboards[Dashboards]
        Alerts[Alert Manager]
    end

    subgraph Notification["Notification"]
        PagerDuty[PagerDuty]
        Slack[Slack Alerts]
        Email[Email Alerts]
    end

    API --> Prom
    Agents --> Prom
    Workers --> Prom

    API --> OTel
    Agents --> OTel
    Workers --> OTel

    OTel --> Jaeger

    Prom --> TSDB
    Jaeger --> TraceStore
    API --> LogStore
    Agents --> LogStore

    TSDB --> Grafana
    TraceStore --> Grafana
    LogStore --> Grafana

    Grafana --> Dashboards
    Grafana --> Alerts

    Alerts --> PagerDuty
    Alerts --> Slack
    Alerts --> Email
```

### 9.2 Key Metrics

| Category | Metric | Description |
|----------|--------|-------------|
| **API** | `recruitment_api_requests_total` | Total API requests |
| **API** | `recruitment_api_latency_seconds` | API response latency |
| **API** | `recruitment_api_errors_total` | API error count |
| **Agents** | `recruitment_agent_tasks_total` | Agent tasks processed |
| **Agents** | `recruitment_agent_task_duration_seconds` | Agent task duration |
| **Agents** | `recruitment_agent_errors_total` | Agent error count |
| **Matching** | `recruitment_match_score_avg` | Average match score |
| **Matching** | `recruitment_match_precision` | Match precision |
| **Bias** | `recruitment_bias_detections_total` | Bias detections |
| **Bias** | `recruitment_bias_severity_high` | High severity bias count |
| **Pipeline** | `recruitment_funnel_conversion` | Funnel conversion rate |
| **Pipeline** | `recruitment_time_to_hire_days` | Time to hire |

### 9.3 Alerting Rules

```yaml
# monitoring/alerts.yml
groups:
  - name: recruitment_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(recruitment_api_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate in recruitment API"
          description: "Error rate is {{ $value }}% for the last 5 minutes"

      - alert: AgentTaskBacklog
        expr: recruitment_agent_tasks_pending > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent task backlog detected"
          description: "{{ $value }} tasks pending in queue"

      - alert: BiasDetected
        expr: recruitment_bias_detections_total > 0
        for: 1m
        labels:
          severity: high
        annotations:
          summary: "Bias detected in recruitment decisions"
          description: "Bias detection count: {{ $value }}"

      - alert: HighLatency
        expr: recruitment_api_latency_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "95th percentile latency is {{ $value }}s"

      - alert: LowMatchPrecision
        expr: recruitment_match_precision < 0.7
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low match precision"
          description: "Match precision dropped to {{ $value }}"
```

---

## 10. Implementation Roadmap

### 10.1 Phase 1: Foundation (Weeks 1-4)

| Week | Deliverable | Status |
|------|-------------|--------|
| 1 | Project scaffolding + DB schema | Planned |
| 1 | Candidate CRUD API | Planned |
| 2 | Resume Parser Agent (basic) | Planned |
| 2 | GRC_Claw Identity integration | Planned |
| 3 | Job CRUD API | Planned |
| 3 | Application API | Planned |
| 4 | Basic matching engine | Planned |
| 4 | Audit logging integration | Planned |

### 10.2 Phase 2: Core Agents (Weeks 5-8)

| Week | Deliverable | Status |
|------|-------------|--------|
| 5 | Resume Parser Agent (advanced) | Planned |
| 5 | Candidate Matcher Agent | Planned |
| 6 | Interview Scheduler Agent | Planned |
| 6 | Skills Assessor Agent | Planned |
| 7 | Bias Detector Agent | Planned |
| 7 | WebSocket real-time events | Planned |
| 8 | ATS integration (Greenhouse) | Planned |
| 8 | Calendar integration | Planned |

### 10.3 Phase 3: Production Hardening (Weeks 9-12)

| Week | Deliverable | Status |
|------|-------------|--------|
| 9 | GDPR compliance features | Planned |
| 9 | Security hardening | Planned |
| 10 | Performance optimization | Planned |
| 10 | Load testing | Planned |
| 11 | Monitoring + alerting | Planned |
| 11 | CI/CD pipeline | Planned |
| 12 | Documentation + runbooks | Planned |
| 12 | Production deployment | Planned |

---

## Appendix A: Configuration

```yaml
# config/recruitment.yaml
recruitment:
  api:
    host: "0.0.0.0"
    port: 8000
    workers: 4
    cors_origins: ["https://recruitment.grc-claw.com"]
    
  database:
    url: "postgresql://user:pass@localhost:5432/recruitment"
    pool_size: 20
    max_overflow: 10
    
  redis:
    url: "redis://localhost:6379/0"
    
  kafka:
    bootstrap_servers: "localhost:9092"
    topics:
      - "recruitment.candidates"
      - "recruitment.applications"
      - "recruitment.interviews"
      - "recruitment.assessments"
      
  agents:
    resume_parser:
      model: "layoutlm-v3"
      confidence_threshold: 0.85
      max_file_size_mb: 10
      
    candidate_matcher:
      embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
      match_threshold: 0.6
      max_results: 50
      
    interview_scheduler:
      default_duration_minutes: 60
      max_interviewers: 5
      scheduling_window_days: 14
      
    bias_detector:
      demographic_parity_threshold: 0.8
      equal_opportunity_threshold: 0.05
      disparate_impact_threshold: 0.8
      
    skills_assessor:
      adaptive_difficulty: true
      proctoring_enabled: true
      max_questions: 30
      
  integrations:
    greenhouse:
      enabled: false
      api_key: "${GREENHOUSE_API_KEY}"
      
    lever:
      enabled: false
      api_key: "${LEVER_API_KEY}"
      
    google_calendar:
      enabled: false
      credentials_path: "/secrets/google-calendar.json"
      
    linkedin:
      enabled: false
      client_id: "${LINKEDIN_CLIENT_ID}"
      client_secret: "${LINKEDIN_CLIENT_SECRET}"
      
  grc_claw:
    identity_service_url: "http://identity:8080"
    policy_engine_url: "http://opa:8181"
    audit_service_url: "http://audit:8081"
    agent_registry_url: "http://agent-registry:8082"
```

---

*Document generated by GRC_Claw Architecture Team*  
*Last updated: 2026-10-02*
