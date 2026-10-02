# AI-Powered Onboarding & Training Implementation Plan

**Document ID:** GRC-AI-OT-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Implementation Ready  
**Framework:** LangChain DeepAgents v0.6+  
**Parent Documents:** GRC_Claw Training Implementation Guide v1.0, GRC_Claw AI Training Framework v1.0

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Content Creation Agent](#2-content-creation-agent)
3. [Delivery Agent](#3-delivery-agent)
4. [Assessment Agent](#4-assessment-agent)
5. [Optimization Agent](#5-optimization-agent)
6. [Performance Analytics Agent](#6-performance-analytics-agent)
7. [Code Examples & Snippets](#7-code-examples--snippets)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered onboarding and training system uses LangChain DeepAgents as the foundational harness, orchestrating five specialized sub-agents through a supervisor agent. Each sub-agent handles a distinct phase of the training lifecycle: content creation, delivery, assessment, optimization, and analytics.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AI-Powered Onboarding & Training System                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Supervisor Agent (Orchestrator)                    │    │
│  │  • Routes training requests to specialized sub-agents                │    │
│  │  • Manages training pipeline state via write_todos                    │    │
│  │  • Coordinates parallel content generation                           │    │
│  │  • Enforces human-in-the-loop gates for content approval             │    │
│  └──────────┬──────────┬──────────┬──────────┬──────────┬───────────────┘    │
│             │          │          │          │          │                     │
│     ┌───────▼──┐ ┌─────▼────┐ ┌───▼─────┐ ┌──▼──────┐ ┌─▼──────────────┐    │
│     │ Content  │ │ Delivery │ │Assessment│ │Optimize │ │  Analytics     │    │
│     │ Creation │ │  Agent   │ │  Agent   │ │  Agent  │ │    Agent       │    │
│     │  Agent   │ │          │ │          │ │         │ │                │    │
│     │          │ │          │ │          │ │         │ │                │    │
│     │• Generate│ │• Schedule│ │• Quiz    │ │• A/B    │ │• Kirkpatrick  │    │
│     │• Curate  │ │• Adapt   │ │• Grade   │ │• Refine │ │• Predictive   │    │
│     │• Validate│ │• Notify  │ │• Gap     │ │• Recomm │ │• ROI          │    │
│     │• Version │ │• Track   │ │• Certify │ │• Personal│ │• Compliance   │    │
│     └──────────┘ └──────────┘ └──────────┘ └─────────┘ └────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Shared Infrastructure Layer                        │    │
│  │  • Virtual Filesystem (content artifacts, assessments, evidence)     │    │
│  │  • LangGraph Checkpointer (durable execution, crash recovery)         │    │
│  │  • LangSmith Tracing (observability, evaluation)                     │    │
│  │  • Memory Store (cross-session learner context)                      │    │
│  │  • Skills System (reusable training patterns)                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 DeepAgents Configuration

The system leverages DeepAgents' four core primitives:

| Primitive | Usage in Training System |
|-----------|------------------------|
| **Planning (`write_todos`)** | Supervisor decomposes training pipelines into trackable steps; each sub-agent plans its own work |
| **Filesystem** | Content artifacts, assessment rubrics, learner progress records, and evidence stored as files |
| **Sub-agents** | Five specialized agents spawned via the `task` tool with isolated context windows |
| **Context Management** | Auto-summarization for long training sessions; large content offloaded to filesystem |

### 1.3 Agent Topology

```python
# Supervisor agent with specialized sub-agents
from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent

# Sub-agent definitions
content_creator = SubAgent(
    name="content_creator",
    description="Generates training content, modules, and learning materials",
    prompt="You are a training content specialist...",
    tools=[content_search, content_template, media_generator],
    subagents=[]  # Leaf agent
)

delivery_agent = SubAgent(
    name="delivery_agent",
    description="Manages content delivery, scheduling, and learner notifications",
    prompt="You are a training delivery coordinator...",
    tools=[scheduler, notification_service, progress_tracker],
    subagents=[]
)

assessment_agent = SubAgent(
    name="assessment_agent",
    description="Creates assessments, grades submissions, and identifies competency gaps",
    prompt="You are an assessment and evaluation specialist...",
    tools=[quiz_generator, rubric_scorer, gap_analyzer],
    subagents=[]
)

optimization_agent = SubAgent(
    name="optimization_agent",
    description="Optimizes training paths, A/B tests content, and personalizes learning",
    prompt="You are a learning optimization specialist...",
    tools=[ab_test_engine, path_optimizer, recommender],
    subagents=[]
)

analytics_agent = SubAgent(
    name="analytics_agent",
    description="Produces Kirkpatrick evaluations, predictive analytics, and compliance reports",
    prompt="You are a training analytics and compliance specialist...",
    tools=[kirkpatrick_eval, predictive_model, report_generator],
    subagents=[]
)

# Supervisor agent
training_supervisor = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=TRAINING_SUPERVISOR_PROMPT,
    tools=[training_catalog, learner_registry, compliance_checker],
    subagents=[content_creator, delivery_agent, assessment_agent, optimization_agent, analytics_agent],
    memory=["./training_memory.md"],
    skills=["./skills/content-creation/", "./skills/assessment/", "./skills/delivery/"],
)
```

### 1.4 Middleware Stack

```python
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.memory import MemoryMiddleware
from langchain.agents.middleware import SummarizationMiddleware, HumanInTheLoopMiddleware

middleware = [
    # Filesystem: content artifacts stored in versioned workspace
    FilesystemMiddleware(
        workspace_root="./training_artifacts/",
        tools=["read_file", "write_file", "edit_file", "ls", "glob", "grep"],
    ),
    # Summarization: compress long training sessions
    SummarizationMiddleware(
        model="openai:gpt-4o-mini",
        max_tokens=8000,
        messages_to_keep=20,
    ),
    # Human-in-the-loop: content approval before publication
    HumanInTheLoopMiddleware(
        interrupt_on={"write_file": True, "edit_file": True},
        description="Content changes require human approval",
    ),
    # Memory: cross-session learner context
    MemoryMiddleware(
        store=memory_store,
        recall_scope="user",
    ),
]
```

### 1.5 State Management

```python
# Training pipeline state schema
from typing import TypedDict, List, Optional
from enum import Enum

class PipelinePhase(str, Enum):
    CONTENT_CREATION = "content_creation"
    DELIVERY = "delivery"
    ASSESSMENT = "assessment"
    OPTIMIZATION = "optimization"
    ANALYTICS = "analytics"

class TrainingPipelineState(TypedDict):
    pipeline_id: str
    learner_id: str
    role_tier: int
    current_phase: PipelinePhase
    content_artifacts: List[str]  # File paths in virtual filesystem
    assessment_results: dict
    delivery_schedule: dict
    optimization_recommendations: List[dict]
    kirkpatrick_levels: dict
    human_approvals: List[dict]
    todo_plan: List[dict]  # write_todos state
```

---

## 2. Content Creation Agent

### 2.1 Responsibilities

- Generate role-specific training modules aligned to the 14-module curriculum (M01-M14)
- Create multimedia content (text, diagrams, interactive scenarios)
- Validate content against ISO 42001 Clause 7.2/7.3 requirements
- Version and maintain content artifacts in the virtual filesystem
- Curate content from external sources (regulatory updates, best practices)

### 2.2 Implementation

```python
# agents/content_creation.py
from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent
from langchain_core.tools import tool
from typing import List, Dict, Optional
import json

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def search_training_catalog(query: str, tier: Optional[int] = None) -> List[Dict]:
    """Search existing training content catalog.
    
    Args:
        query: Search keywords (e.g., "AI governance fundamentals")
        tier: Optional role tier filter (0-4)
    
    Returns:
        List of matching content items with metadata
    """
    # Implementation: Elasticsearch query against content catalog
    pass

@tool
def generate_learning_objective(competency: str, level: str) -> str:
    """Generate a measurable learning objective using Bloom's taxonomy.
    
    Args:
        competency: Competency code (C1-C10)
        level: Target level (aware, working, expert)
    
    Returns:
        Measurable learning objective statement
    """
    pass

@tool
def create_content_artifact(
    module_code: str,
    content_type: str,  # "video_script", "interactive_scenario", "reading", "quiz"
    target_tier: int,
    competencies: List[str],
    output_path: str,
) -> Dict:
    """Create a training content artifact and write to filesystem.
    
    Args:
        module_code: Module identifier (M01-M14)
        content_type: Type of content to generate
        target_tier: Role tier (0-4)
        competencies: Target competency codes
        output_path: Filesystem path for the artifact
    
    Returns:
        Artifact metadata including version, hash, and validation status
    """
    pass

@tool
def validate_content_compliance(
    artifact_path: str,
    clause: str,  # "7.2" or "7.3"
) -> Dict:
    """Validate content artifact against ISO 42001 requirements.
    
    Args:
        artifact_path: Path to content artifact
        clause: ISO 42001 clause reference
    
    Returns:
        Compliance validation report with pass/fail and gaps
    """
    pass

@tool
def curate_external_content(
    topic: str,
    source_types: List[str],  # ["regulation", "standard", "best_practice"]
    max_items: int = 5,
) -> List[Dict]:
    """Curate external content from regulatory and standards sources.
    
    Args:
        topic: Content topic
        source_types: Types of sources to search
        max_items: Maximum items to return
    
    Returns:
        Curated content items with source attribution
    """
    pass

# ── Agent Definition ───────────────────────────────────────────────────────

CONTENT_CREATION_PROMPT = """You are a training content creation specialist for GRC_Claw.

Your responsibilities:
1. Generate role-specific training content aligned to the 14-module curriculum
2. Create measurable learning objectives using Bloom's taxonomy
3. Validate all content against ISO 42001 Clause 7.2 (Competence) and 7.3 (Awareness)
4. Version and maintain content artifacts in the virtual filesystem
5. Curate external regulatory and standards content

Content creation workflow:
1. Analyze the target role tier and competency requirements
2. Search existing catalog to avoid duplication
3. Generate learning objectives for each competency
4. Create content artifacts (scripts, scenarios, readings, quizzes)
5. Validate compliance with ISO 42001
6. Write artifacts to filesystem with version metadata
7. Report creation summary with artifact paths

Always:
- Align content to the GRC_Claw competence matrix (C1-C10)
- Include diverse learning modalities (visual, auditory, kinesthetic)
- Reference specific ISO 42001 clauses where applicable
- Generate assessment questions alongside content
- Tag artifacts with metadata for searchability"""

content_creation_agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=CONTENT_CREATION_PROMPT,
    tools=[
        search_training_catalog,
        generate_learning_objective,
        create_content_artifact,
        validate_content_compliance,
        curate_external_content,
    ],
    subagents=[],  # Leaf agent - no further delegation
    middleware=[
        FilesystemMiddleware(workspace_root="./content_artifacts/"),
    ],
)
```

### 2.3 Content Creation Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Content Creation Pipeline                    │
│                                                          │
│  1. Input: Role tier + Competency gaps                   │
│     ↓                                                    │
│  2. Search existing catalog (deduplication)               │
│     ↓                                                    │
│  3. Generate learning objectives (Bloom's taxonomy)      │
│     ↓                                                    │
│  4. Create content artifacts (parallel sub-agents)       │
│     ├── Video script generator                           │
│     ├── Interactive scenario builder                     │
│     ├── Reading material composer                        │
│     └── Assessment question generator                    │
│     ↓                                                    │
│  5. Validate ISO 42001 compliance                        │
│     ↓                                                    │
│  6. Human review gate (interrupt_on write_file)           │
│     ↓                                                    │
│  7. Version and publish to content repository            │
│     ↓                                                    │
│  8. Output: Artifact paths + metadata + compliance report │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Delivery Agent

### 3.1 Responsibilities

- Schedule and deliver training content to learners
- Adapt delivery format based on learner preferences and role
- Send notifications and reminders
- Track learner progress in real-time
- Handle rescheduling and catch-up sessions

### 3.2 Implementation

```python
# agents/delivery.py
from deepagents import create_deep_agent
from langchain_core.tools import tool
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def get_learner_profile(learner_id: str) -> Dict:
    """Retrieve learner profile including role, tier, preferences, and history.
    
    Args:
        learner_id: Unique learner identifier
    
    Returns:
        Learner profile with role, tier, learning preferences, and progress
    """
    pass

@tool
def schedule_training_session(
    learner_id: str,
    module_code: str,
    format: str,  # "self-paced", "instructor-led", "lab", "workshop"
    preferred_times: List[str],
    duration_minutes: int,
) -> Dict:
    """Schedule a training session for a learner.
    
    Args:
        learner_id: Target learner
        module_code: Module to deliver
        format: Delivery format
        preferred_times: Learner's preferred time slots
        duration_minutes: Session duration
    
    Returns:
        Scheduled session details with calendar integration
    """
    pass

@tool
def send_training_notification(
    learner_id: str,
    notification_type: str,  # "reminder", "overdue", "completion", "new_content"
    message: str,
    channel: str = "email",  # "email", "slack", "teams", "in_app"
) -> Dict:
    """Send a training notification to a learner.
    
    Args:
        learner_id: Target learner
        notification_type: Type of notification
        message: Notification content
        channel: Delivery channel
    
    Returns:
        Delivery confirmation with timestamp
    """
    pass

@tool
def track_progress(
    learner_id: str,
    module_code: str,
    progress_percent: int,
    time_spent_minutes: int,
) -> Dict:
    """Update learner progress for a module.
    
    Args:
        learner_id: Learner identifier
        module_code: Module being tracked
        progress_percent: Completion percentage (0-100)
        time_spent_minutes: Time spent on module
    
    Returns:
        Updated progress record with milestones
    """
    pass

@tool
def adapt_delivery_format(
    learner_id: str,
    module_code: str,
    performance_data: Dict,
) -> Dict:
    """Adapt delivery format based on learner performance and preferences.
    
    Args:
        learner_id: Learner identifier
        module_code: Current module
        performance_data: Recent performance metrics
    
    Returns:
        Adapted delivery plan with format recommendations
    """
    pass

@tool
def generate_catch_up_plan(
    learner_id: str,
    overdue_modules: List[str],
) -> Dict:
    """Generate a catch-up plan for overdue training.
    
    Args:
        learner_id: Learner identifier
        overdue_modules: List of overdue module codes
    
    Returns:
        Prioritized catch-up schedule
    """
    pass

# ── Agent Definition ───────────────────────────────────────────────────────

DELIVERY_PROMPT = """You are a training delivery coordinator for GRC_Claw.

Your responsibilities:
1. Schedule and deliver training content to learners
2. Adapt delivery format based on learner preferences and role
3. Send notifications and reminders at optimal times
4. Track learner progress and identify at-risk learners
5. Handle rescheduling and catch-up sessions

Delivery principles:
- Respect learner time zones and working hours
- Adapt format to role tier (executives get concise briefings, practitioners get hands-on labs)
- Send reminders 48h and 24h before scheduled sessions
- Escalate overdue training to managers after 7 days
- Offer multiple delivery formats for accessibility

Notification cadence:
- New enrollment: Welcome message with learning path overview
- 48h before: Session reminder with preparation materials
- 24h before: Final reminder with join link
- Overdue 3 days: Gentle reminder
- Overdue 7 days: Manager escalation
- Completion: Congratulations + next steps"""

delivery_agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=DELIVERY_PROMPT,
    tools=[
        get_learner_profile,
        schedule_training_session,
        send_training_notification,
        track_progress,
        adapt_delivery_format,
        generate_catch_up_plan,
    ],
    subagents=[],
    middleware=[
        FilesystemMiddleware(workspace_root="./delivery_schedules/"),
    ],
)
```

### 3.3 Delivery Workflow

```
┌─────────────────────────────────────────────────────────┐
│               Delivery Pipeline                           │
│                                                          │
│  1. Input: Enrolled learner + assigned modules           │
│     ↓                                                    │
│  2. Retrieve learner profile (role, tier, preferences)   │
│     ↓                                                    │
│  3. Determine optimal delivery format                    │
│     ├── Tier 0-1: Self-paced reading + short videos      │
│     ├── Tier 2: Interactive scenarios + quizzes          │
│     ├── Tier 3: Workshops + case studies                 │
│     └── Tier 4: Executive briefings + strategy sessions  │
│     ↓                                                    │
│  4. Schedule sessions (respect time zones, preferences)  │
│     ↓                                                    │
│  5. Send welcome notification with learning path         │
│     ↓                                                    │
│  6. Track progress in real-time                          │
│     ↓                                                    │
│  7. Send reminders (48h, 24h before)                     │
│     ↓                                                    │
│  8. Adapt format if learner is struggling                │
│     ↓                                                    │
│  9. Escalate overdue to manager (7+ days)                │
│     ↓                                                    │
│  10. Output: Delivery schedule + progress + notifications │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Assessment Agent

### 4.1 Responsibilities

- Generate assessments aligned to learning objectives
- Grade submissions using rubric-based scoring
- Identify competency gaps and recommend remediation
- Manage certification preparation and tracking
- Produce audit-ready evidence for ISO 42001 Clause 7.2

### 4.2 Implementation

```python
# agents/assessment.py
from deepagents import create_deep_agent
from langchain_core.tools import tool
from typing import List, Dict, Optional

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def generate_assessment_questions(
    module_code: str,
    competency: str,
    difficulty: str,  # "foundational", "intermediate", "advanced"
    question_types: List[str],  # ["multiple_choice", "scenario", "short_answer", "practical"]
    count: int = 10,
) -> List[Dict]:
    """Generate assessment questions aligned to learning objectives.
    
    Args:
        module_code: Module identifier
        competency: Target competency code
        difficulty: Difficulty level
        question_types: Types of questions to generate
        count: Number of questions
    
    Returns:
        List of assessment questions with answer keys and rubrics
    """
    pass

@tool
def grade_submission(
    assessment_id: str,
    learner_id: str,
    responses: List[Dict],
    rubric: Dict,
) -> Dict:
    """Grade a learner's assessment submission.
    
    Args:
        assessment_id: Assessment identifier
        learner_id: Learner identifier
        responses: Learner's responses
        rubric: Grading rubric
    
    Returns:
        Graded result with score, feedback, and competency mapping
    """
    pass

@tool
def identify_competency_gaps(
    learner_id: str,
    assessment_results: List[Dict],
    required_competencies: List[str],
) -> Dict:
    """Identify competency gaps based on assessment results.
    
    Args:
        learner_id: Learner identifier
        assessment_results: Recent assessment results
        required_competencies: Required competency codes
    
    Returns:
        Gap analysis with severity and recommended remediation
    """
    pass

@tool
def generate_rubric(
    learning_objective: str,
    competency: str,
    max_score: int = 100,
) -> Dict:
    """Generate a grading rubric for an assessment.
    
    Args:
        learning_objective: Target learning objective
        competency: Target competency
        max_score: Maximum possible score
    
    Returns:
        Structured rubric with criteria and scoring levels
    """
    pass

@tool
def create_certification_prep_plan(
    learner_id: str,
    certification_type: str,  # "GAICC_Foundation", "GAICC_Lead_Implementer", etc.
    current_competency_levels: Dict[str, str],
) -> Dict:
    """Create a certification preparation plan.
    
    Args:
        learner_id: Learner identifier
        certification_type: Target certification
        current_competency_levels: Current competency levels
    
    Returns:
        Personalized certification prep plan with study schedule
    """
    pass

@tool
def record_evidence(
    learner_id: str,
    clause: str,  # "7.2" or "7.3"
    artifact_type: str,
    content: Dict,
) -> Dict:
    """Record audit-ready evidence for ISO 42001 compliance.
    
    Args:
        learner_id: Learner identifier
        clause: ISO 42001 clause (7.2 or 7.3)
        artifact_type: Type of evidence
        content: Evidence content
    
    Returns:
        Evidence record with hash and retention metadata
    """
    pass

# ── Agent Definition ───────────────────────────────────────────────────────

ASSESSMENT_PROMPT = """You are an assessment and evaluation specialist for GRC_Claw.

Your responsibilities:
1. Generate assessments aligned to learning objectives and Bloom's taxonomy
2. Grade submissions using consistent, fair rubric-based scoring
3. Identify competency gaps and recommend targeted remediation
4. Manage certification preparation and tracking
5. Produce audit-ready evidence for ISO 42001 Clause 7.2 and 7.3

Assessment principles:
- Align every question to a specific learning objective
- Use diverse question types (MCQ, scenario, short answer, practical)
- Provide constructive feedback, not just scores
- Map results to the GRC_Claw competence matrix (C1-C10)
- Maintain audit trail for all assessments (Clause 7.2 evidence)
- Flag potential academic integrity issues for review

Grading standards:
- 90-100%: Expert level (can design, lead, evaluate others)
- 70-89%: Working level (can apply independently)
- 50-69%: Aware level (understands concepts, needs supervision)
- Below 50%: Not yet competent - remediation required

Evidence requirements:
- Every assessment must produce a completion record
- Scores must be linked to specific competencies
- Assessor identity must be recorded
- Timestamps must be immutable
- Evidence must be retained per retention policy"""

assessment_agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=ASSESSMENT_PROMPT,
    tools=[
        generate_assessment_questions,
        grade_submission,
        identify_competency_gaps,
        generate_rubric,
        create_certification_prep_plan,
        record_evidence,
    ],
    subagents=[],
    middleware=[
        FilesystemMiddleware(workspace_root="./assessments/"),
        HumanInTheLoopMiddleware(
            interrupt_on={"record_evidence": True},
            description="Evidence recording requires human verification",
        ),
    ],
)
```

### 4.3 Assessment Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Assessment Pipeline                          │
│                                                          │
│  1. Input: Module completion + competency requirements   │
│     ↓                                                    │
│  2. Generate assessment questions (aligned to objectives) │
│     ├── Multiple choice (knowledge check)                │
│     ├── Scenario-based (application)                     │
│     ├── Short answer (analysis)                          │
│     └── Practical exercise (synthesis)                   │
│     ↓                                                    │
│  3. Generate grading rubric                              │
│     ↓                                                    │
│  4. Administer assessment to learner                     │
│     ↓                                                    │
│  5. Grade submission (rubric-based)                     │
│     ↓                                                    │
│  6. Map results to competence matrix                     │
│     ↓                                                    │
│  7. Identify competency gaps                             │
│     ↓                                                    │
│  8. Recommend remediation (if needed)                    │
│     ↓                                                    │
│  9. Record evidence (ISO 42001 Clause 7.2/7.3)          │
│     ↓                                                    │
│  10. Output: Score + feedback + gaps + evidence record   │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Optimization Agent

### 5.1 Responsibilities

- A/B test training content effectiveness
- Personalize learning paths based on learner data
- Optimize content delivery timing and format
- Recommend content updates based on assessment performance
- Continuously improve training effectiveness

### 5.2 Implementation

```python
# agents/optimization.py
from deepagents import create_deep_agent
from langchain_core.tools import tool
from typing import List, Dict, Optional

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def run_ab_test(
    content_variant_a: str,
    content_variant_b: str,
    metric: str,  # "completion_rate", "assessment_score", "time_to_complete"
    sample_size: int = 100,
) -> Dict:
    """Run an A/B test between two content variants.
    
    Args:
        content_variant_a: Path to variant A content
        content_variant_b: Path to variant B content
        metric: Success metric to compare
        sample_size: Number of learners per variant
    
    Returns:
        A/B test results with statistical significance
    """
    pass

@tool
def personalize_learning_path(
    learner_id: str,
    current_competencies: Dict[str, str],
    role_requirements: Dict[str, str],
    learning_preferences: Dict,
) -> Dict:
    """Generate a personalized learning path for a learner.
    
    Args:
        learner_id: Learner identifier
        current_competencies: Current competency levels
        role_requirements: Required competencies for role
        learning_preferences: Preferred formats, pace, schedule
    
    Returns:
        Personalized learning path with module sequence
    """
    pass

@tool
def analyze_content_effectiveness(
    module_code: str,
    time_period: str = "last_90_days",
) -> Dict:
    """Analyze the effectiveness of a training module.
    
    Args:
        module_code: Module to analyze
        time_period: Analysis time window
    
    Returns:
        Effectiveness metrics with recommendations
    """
    pass

@tool
def recommend_content_updates(
    module_code: str,
    performance_data: Dict,
    feedback_data: List[Dict],
) -> List[Dict]:
    """Recommend content updates based on performance and feedback.
    
    Args:
        module_code: Module to evaluate
        performance_data: Assessment and completion data
        feedback_data: Learner feedback
    
    Returns:
        Prioritized list of content update recommendations
    """
    pass

@tool
def optimize_delivery_timing(
    learner_cohort: str,
    module_code: str,
) -> Dict:
    """Optimize delivery timing for a learner cohort.
    
    Args:
        learner_cohort: Cohort identifier
        module_code: Module to optimize
    
    Returns:
        Optimal timing recommendations
    """
    pass

@tool
def generate_remediation_plan(
    learner_id: str,
    competency_gaps: Dict[str, str],
) -> Dict:
    """Generate a targeted remediation plan for competency gaps.
    
    Args:
        learner_id: Learner identifier
        competency_gaps: Identified competency gaps
    
    Returns:
        Remediation plan with targeted content and exercises
    """
    pass

# ── Agent Definition ───────────────────────────────────────────────────────

OPTIMIZATION_PROMPT = """You are a learning optimization specialist for GRC_Claw.

Your responsibilities:
1. A/B test training content to identify most effective variants
2. Personalize learning paths based on learner data and role requirements
3. Optimize content delivery timing and format
4. Recommend content updates based on assessment performance
5. Continuously improve training effectiveness through data-driven iteration

Optimization principles:
- Use data, not assumptions, to drive decisions
- Test one variable at a time in A/B tests
- Personalize based on role, tier, learning style, and pace
- Prioritize remediation for critical competency gaps
- Balance standardization with personalization
- Measure impact at all four Kirkpatrick levels

A/B testing methodology:
- Minimum sample size: 30 per variant for statistical power
- Run tests for at least 2 weeks to account for timing effects
- Measure both leading (completion, engagement) and lagging (assessment, behavior) metrics
- Document all test results for organizational learning

Personalization dimensions:
- Role tier (0-4): Content depth and format
- Competency level: Starting point and pace
- Learning style: Visual, auditory, reading/writing, kinesthetic
- Time availability: Self-paced vs. scheduled
- Prior experience: Accelerated paths for experienced learners"""

optimization_agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=OPTIMIZATION_PROMPT,
    tools=[
        run_ab_test,
        personalize_learning_path,
        analyze_content_effectiveness,
        recommend_content_updates,
        optimize_delivery_timing,
        generate_remediation_plan,
    ],
    subagents=[],
    middleware=[
        FilesystemMiddleware(workspace_root="./optimization/"),
    ],
)
```

### 5.3 Optimization Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Optimization Pipeline                        │
│                                                          │
│  1. Input: Training performance data + learner feedback │
│     ↓                                                    │
│  2. Analyze content effectiveness                        │
│     ├── Completion rates by module                       │
│     ├── Assessment scores by competency                  │
│     ├── Time-to-complete distributions                   │
│     └── Learner satisfaction scores                      │
│     ↓                                                    │
│  3. Identify underperforming content                     │
│     ↓                                                    │
│  4. Generate A/B test hypotheses                        │
│     ↓                                                    │
│  5. Run A/B tests (parallel sub-agents)                  │
│     ├── Variant A: Current content                       │
│     └── Variant B: Modified content                      │
│     ↓                                                    │
│  6. Analyze test results (statistical significance)      │
│     ↓                                                    │
│  7. Recommend content updates                            │
│     ↓                                                    │
│  8. Personalize learning paths                           │
│     ↓                                                    │
│  9. Generate remediation plans for struggling learners    │
│     ↓                                                    │
│  10. Output: Updated content + personalized paths + A/B   │
│            test results + recommendations                │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Performance Analytics Agent

### 6.1 Responsibilities

- Produce Kirkpatrick Level 1-4 evaluations
- Generate predictive analytics for learner success
- Create compliance reports for ISO 27001/42001 audits
- Calculate training ROI and effectiveness metrics
- Provide real-time dashboards and alerts

### 6.2 Implementation

```python
# agents/analytics.py
from deepagents import create_deep_agent
from langchain_core.tools import tool
from typing import List, Dict, Optional

# ── Tools ──────────────────────────────────────────────────────────────────

@tool
def evaluate_kirkpatrick_level1(
    module_code: str,
    time_period: str = "last_90_days",
) -> Dict:
    """Evaluate Kirkpatrick Level 1: Reaction.
    
    Args:
        module_code: Module to evaluate
        time_period: Analysis time window
    
    Returns:
        L1 metrics: satisfaction, relevance, engagement scores
    """
    pass

@tool
def evaluate_kirkpatrick_level2(
    module_code: str,
    time_period: str = "last_90_days",
) -> Dict:
    """Evaluate Kirkpatrick Level 2: Learning.
    
    Args:
        module_code: Module to evaluate
        time_period: Analysis time window
    
    Returns:
        L2 metrics: knowledge gain, skill improvement, competency changes
    """
    pass

@tool
def evaluate_kirkpatrick_level3(
    module_code: str,
    time_period: str = "last_90_days",
) -> Dict:
    """Evaluate Kirkpatrick Level 3: Behavior.
    
    Args:
        module_code: Module to evaluate
        time_period: Analysis time window
    
    Returns:
        L3 metrics: on-the-job application, behavior change indicators
    """
    pass

@tool
def evaluate_kirkpatrick_level4(
    module_code: str,
    time_period: str = "last_90_days",
) -> Dict:
    """Evaluate Kirkpatrick Level 4: Results.
    
    Args:
        module_code: Module to evaluate
        time_period: Analysis time window
    
    Returns:
        L4 metrics: business impact, risk reduction, compliance improvement
    """
    pass

@tool
def predict_learner_success(
    learner_id: str,
    module_code: str,
) -> Dict:
    """Predict likelihood of learner success in a module.
    
    Args:
        learner_id: Learner identifier
        module_code: Target module
    
    Returns:
        Success probability with risk factors and recommendations
    """
    pass

@tool
def calculate_training_roi(
    program_id: str,
    time_period: str = "last_12_months",
) -> Dict:
    """Calculate training program ROI.
    
    Args:
        program_id: Training program identifier
        time_period: Analysis time window
    
    Returns:
        ROI metrics: cost per learner, effectiveness gain, risk reduction value
    """
    pass

@tool
def generate_compliance_report(
    clause: str,  # "7.2" or "7.3"
    time_period: str,
    format: str = "oscal",  # "oscal", "pdf", "json"
) -> Dict:
    """Generate ISO 42001 compliance report.
    
    Args:
        clause: ISO 42001 clause
        time_period: Reporting period
        format: Output format
    
    Returns:
        Compliance report with evidence inventory and gaps
    """
    pass

@tool
def generate_executive_dashboard(
    dashboard_type: str,  # "overview", "compliance", "effectiveness", "risk"
    time_period: str = "last_30_days",
) -> Dict:
    """Generate executive dashboard data.
    
    Args:
        dashboard_type: Type of dashboard
        time_period: Analysis time window
    
    Returns:
        Dashboard data with KPIs, trends, and alerts
    """
    pass

# ── Agent Definition ───────────────────────────────────────────────────────

ANALYTICS_PROMPT = """You are a training analytics and compliance specialist for GRC_Claw.

Your responsibilities:
1. Produce Kirkpatrick Level 1-4 evaluations for all training programs
2. Generate predictive analytics for learner success and risk
3. Create compliance reports for ISO 27001/42001 audits
4. Calculate training ROI and effectiveness metrics
5. Provide real-time dashboards and alerts for stakeholders

Analytics principles:
- Measure at all four Kirkpatrick levels, not just satisfaction
- Use control groups where possible for causal inference
- Segment data by role tier, department, and cohort
- Identify leading indicators of training success
- Maintain data privacy and confidentiality
- Ensure all reports are audit-ready

Kirkpatrick evaluation framework:
- Level 1 (Reaction): Did learners find the training engaging and relevant?
- Level 2 (Learning): Did learners acquire the intended knowledge and skills?
- Level 3 (Behavior): Are learners applying what they learned on the job?
- Level 4 (Results): Did the training improve business outcomes and reduce risk?

Predictive analytics:
- Identify at-risk learners before they fail
- Forecast training completion rates
- Predict certification exam success
- Estimate time-to-competency for new hires

Compliance reporting:
- Map all evidence to ISO 42001 Clause 7.2 and 7.3
- Maintain complete audit trail
- Flag compliance gaps proactively
- Generate OSCAL-compatible evidence packages"""

analytics_agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=ANALYTICS_PROMPT,
    tools=[
        evaluate_kirkpatrick_level1,
        evaluate_kirkpatrick_level2,
        evaluate_kirkpatrick_level3,
        evaluate_kirkpatrick_level4,
        predict_learner_success,
        calculate_training_roi,
        generate_compliance_report,
        generate_executive_dashboard,
    ],
    subagents=[],
    middleware=[
        FilesystemMiddleware(workspace_root="./analytics/"),
    ],
)
```

### 6.3 Analytics Workflow

```
┌─────────────────────────────────────────────────────────┐
│              Analytics Pipeline                           │
│                                                          │
│  1. Input: Training data + assessment results + feedback │
│     ↓                                                    │
│  2. Kirkpatrick Evaluation (all 4 levels)                │
│     ├── L1: Reaction (satisfaction surveys)              │
│     ├── L2: Learning (assessment score deltas)           │
│     ├── L3: Behavior (on-the-job application)            │
│     └── L4: Results (business impact, risk reduction)    │
│     ↓                                                    │
│  3. Predictive Analytics                                 │
│     ├── Learner success prediction                       │
│     ├── At-risk learner identification                   │
│     └── Completion rate forecasting                      │
│     ↓                                                    │
│  4. ROI Calculation                                      │
│     ├── Cost per learner                                 │
│     ├── Effectiveness gain (competency improvement)      │
│     └── Risk reduction value                             │
│     ↓                                                    │
│  5. Compliance Reporting                                 │
│     ├── ISO 42001 Clause 7.2/7.3 evidence inventory     │
│     ├── Gap analysis                                     │
│     └── OSCAL-compatible report generation               │
│     ↓                                                    │
│  6. Executive Dashboard                                  │
│     ├── KPI summaries                                    │
│     ├── Trend analysis                                   │
│     └── Alerts and recommendations                       │
│     ↓                                                    │
│  7. Output: Kirkpatrick report + predictions + ROI +     │
│            compliance report + dashboard data             │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Code Examples & Snippets

### 7.1 Complete Training Pipeline Orchestration

```python
# pipeline/training_pipeline.py
from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent
from langchain_core.runnables import RunnableConfig
import asyncio

async def run_training_pipeline(
    learner_id: str,
    role_tier: int,
    required_competencies: List[str],
) -> Dict:
    """Execute the complete training pipeline for a learner.
    
    Args:
        learner_id: Target learner
        role_tier: Role tier (0-4)
        required_competencies: Required competency codes
    
    Returns:
        Complete training pipeline results
    """
    # Initialize supervisor with all sub-agents
    supervisor = create_deep_agent(
        model="openai:gpt-5.5",
        system_prompt=TRAINING_SUPERVISOR_PROMPT,
        tools=[training_catalog, learner_registry, compliance_checker],
        subagents=[
            content_creator,
            delivery_agent,
            assessment_agent,
            optimization_agent,
            analytics_agent,
        ],
        memory=["./training_memory.md"],
        skills=["./skills/"],
    )
    
    # Execute pipeline
    result = await supervisor.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                    Execute the complete training pipeline for learner {learner_id}.
                    
                    Context:
                    - Role tier: {role_tier}
                    - Required competencies: {required_competencies}
                    
                    Pipeline phases:
                    1. Content Creation: Generate training materials for missing competencies
                    2. Delivery: Schedule and deliver content
                    3. Assessment: Evaluate learning and identify gaps
                    4. Optimization: Personalize and improve
                    5. Analytics: Measure effectiveness and compliance
                    
                    Use write_todos to track progress through each phase.
                    """,
                }
            ]
        },
        config=RunnableConfig(
            configurable={"thread_id": f"training-{learner_id}"},
            recursion_limit=100,
        ),
    )
    
    return result
```

### 7.2 Sub-Agent Communication Pattern

```python
# agents/supervisor.py
from deepagents import create_deep_agent
from deepagents.middleware.subagents import SubAgent

# Define sub-agents with specific capabilities
content_subagent = SubAgent(
    name="content_specialist",
    description="Creates and curates training content",
    prompt="You are a content specialist...",
    tools=[content_tools],
    subagents=[],
)

assessment_subagent = SubAgent(
    name="assessment_specialist",
    description="Creates and grades assessments",
    prompt="You are an assessment specialist...",
    tools=[assessment_tools],
    subagents=[],
)

# Supervisor delegates to sub-agents via the task tool
supervisor = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt="""You are the training pipeline supervisor.
    
    Delegate work to specialized sub-agents:
    - content_specialist: For content creation and curation
    - assessment_specialist: For assessment generation and grading
    
    Use write_todos to track pipeline progress.
    Use the task tool to delegate to sub-agents.
    """,
    tools=[pipeline_tools],
    subagents=[content_subagent, assessment_subagent],
)
```

### 7.3 Human-in-the-Loop Content Approval

```python
# middleware/content_approval.py
from langchain.agents.middleware import HumanInTheLoopMiddleware
from typing import Dict, Any

class ContentApprovalMiddleware(HumanInTheLoopMiddleware):
    """Custom middleware for content approval workflow."""
    
    def __init__(self):
        super().__init__(
            interrupt_on={"write_file": True, "edit_file": True},
            description="Content changes require human approval",
        )
    
    async def approve_content(
        self,
        file_path: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> bool:
        """Request human approval for content changes.
        
        Args:
            file_path: Path to the content file
            content: Proposed content
            metadata: Content metadata (module, tier, competencies)
        
        Returns:
            True if approved, False if rejected
        """
        # Implementation: Send approval request to human reviewer
        # Wait for response (approve/reject with feedback)
        pass

# Usage in agent creation
agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=CONTENT_CREATION_PROMPT,
    tools=[content_tools],
    middleware=[
        ContentApprovalMiddleware(),
        FilesystemMiddleware(workspace_root="./content/"),
    ],
)
```

### 7.4 Memory and Context Management

```python
# memory/training_memory.py
from deepagents.middleware.memory import MemoryMiddleware
from langgraph.store.memory import InMemoryStore

# Configure memory store for cross-session learner context
memory_store = InMemoryStore()

memory_middleware = MemoryMiddleware(
    store=memory_store,
    recall_scope="user",  # Recall memories for the current user
    search_kwargs={"k": 5},  # Return top 5 relevant memories
)

# Agent with memory
agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=TRAINING_SUPERVISOR_PROMPT,
    tools=[tools],
    subagents=[subagents],
    memory=["./training_memory.md"],  # File-based memory
    middleware=[memory_middleware],  # Store-based memory
)
```

### 7.5 Skills System for Reusable Training Patterns

```python
# skills/content-creation/SKILL.md
# ---
# name: content-creation
# description: Create training content for GRC_Claw modules
# ---

# Content Creation Skill

## When to use
- Generating new training modules
- Updating existing content
- Creating assessments
- Developing certification prep materials

## Workflow
1. Analyze target role tier and competency requirements
2. Search existing content catalog for reuse opportunities
3. Generate measurable learning objectives
4. Create content in multiple modalities
5. Validate against ISO 42001 requirements
6. Submit for human review and approval

## Output format
- Content artifacts stored in ./content_artifacts/
- Metadata in JSON format with version control
- Compliance validation report
- Assessment questions with answer keys

# skills/assessment/SKILL.md
# ---
# name: assessment
# description: Create and grade assessments for GRC_Claw
# ---

# Assessment Skill

## When to use
- Creating quizzes and exams
- Grading learner submissions
- Identifying competency gaps
- Generating certification prep plans

## Workflow
1. Align questions to learning objectives
2. Generate diverse question types
3. Create grading rubrics
4. Grade submissions consistently
5. Map results to competence matrix
6. Record audit-ready evidence

## Output format
- Assessment questions with answer keys
- Grading rubrics with criteria
- Score reports with competency mapping
- Evidence records for ISO 42001
```

### 7.6 LangSmith Tracing and Observability

```python
# observability/tracing.py
import os
from langsmith import Client

# Configure LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "grc-claw-training"

# Tracing is automatic with DeepAgents + LangGraph
# All agent invocations, tool calls, and sub-agent delegations are traced

# Custom evaluation
from langsmith.evaluation import evaluate

def training_effectiveness_evaluator(run, example):
    """Custom evaluator for training effectiveness."""
    # Evaluate the quality of training content generated
    # Score based on alignment to objectives, clarity, and completeness
    pass

# Run evaluation
results = evaluate(
    run_training_pipeline,
    data="training-eval-dataset",
    evaluators=[training_effectiveness_evaluator],
)
```

### 7.7 Deployment Configuration

```python
# deployment/config.py
from deepagents import create_deep_agent
from langgraph.checkpoint.postgres import PostgresSaver

# Production deployment configuration
def create_production_agent():
    """Create a production-ready training agent."""
    
    # Configure checkpointer for durable execution
    checkpointer = PostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost/training"
    )
    
    # Create agent with production settings
    agent = create_deep_agent(
        model="openai:gpt-5.5",
        system_prompt=TRAINING_SUPERVISOR_PROMPT,
        tools=[production_tools],
        subagents=[production_subagents],
        middleware=[
            FilesystemMiddleware(workspace_root="/data/training_artifacts/"),
            SummarizationMiddleware(model="openai:gpt-4o-mini"),
            HumanInTheLoopMiddleware(interrupt_on={"write_file": True}),
            MemoryMiddleware(store=production_memory_store),
        ],
    )
    
    return agent

# Deployment via LangGraph
# langgraph up --config langgraph.json
```

---

## 8. Testing Strategy

### 8.1 Testing Pyramid

```
┌─────────────────────────────────────────────────────────┐
│                    E2E Tests (10%)                       │
│  • Full pipeline execution                               │
│  • Multi-agent coordination                              │
│  • Production-like scenarios                             │
├─────────────────────────────────────────────────────────┤
│              Integration Tests (30%)                     │
│  • Agent-to-agent communication                         │
│  • Tool integration                                      │
│  • Middleware behavior                                   │
│  • State management                                      │
├─────────────────────────────────────────────────────────┤
│                Unit Tests (60%)                          │
│  • Individual tool functions                             │
│  • Agent decision logic                                  │
│  • Content generation quality                            │
│  • Assessment grading accuracy                           │
└─────────────────────────────────────────────────────────┘
```

### 8.2 Unit Tests

```python
# tests/test_content_creation.py
import pytest
from agents.content_creation import (
    generate_learning_objective,
    create_content_artifact,
    validate_content_compliance,
)

@pytest.mark.asyncio
async def test_generate_learning_objective():
    """Test learning objective generation."""
    result = await generate_learning_objective.ainvoke({
        "competency": "C1",
        "level": "working",
    })
    
    assert isinstance(result, str)
    assert len(result) > 20
    # Bloom's taxonomy verbs
    assert any(verb in result.lower() for verb in [
        "define", "explain", "describe", "identify",
        "apply", "demonstrate", "implement", "analyze"
    ])

@pytest.mark.asyncio
async def test_create_content_artifact():
    """Test content artifact creation."""
    result = await create_content_artifact.ainvoke({
        "module_code": "M01",
        "content_type": "reading",
        "target_tier": 1,
        "competencies": ["C1"],
        "output_path": "./test_artifacts/m01_reading.md",
    })
    
    assert result["module_code"] == "M01"
    assert result["version"] is not None
    assert result["hash"] is not None
    assert result["validation_status"] in ["passed", "warning"]

@pytest.mark.asyncio
async def test_validate_content_compliance():
    """Test ISO 42001 compliance validation."""
    result = await validate_content_compliance.ainvoke({
        "artifact_path": "./test_artifacts/m01_reading.md",
        "clause": "7.2",
    })
    
    assert "compliant" in result
    assert "gaps" in result
    assert isinstance(result["gaps"], list)

# tests/test_assessment.py
@pytest.mark.asyncio
async def test_generate_assessment_questions():
    """Test assessment question generation."""
    result = await generate_assessment_questions.ainvoke({
        "module_code": "M01",
        "competency": "C1",
        "difficulty": "intermediate",
        "question_types": ["multiple_choice", "scenario"],
        "count": 5,
    })
    
    assert len(result) == 5
    for question in result:
        assert "question" in question
        assert "answer_key" in question
        assert "competency" in question

@pytest.mark.asyncio
async def test_grade_submission():
    """Test assessment grading."""
    result = await grade_submission.ainvoke({
        "assessment_id": "test-assessment-001",
        "learner_id": "test-learner-001",
        "responses": [
            {"question_id": "q1", "answer": "A"},
            {"question_id": "q2", "answer": "B"},
        ],
        "rubric": {"passing_score": 70, "max_score": 100},
    })
    
    assert "score" in result
    assert "feedback" in result
    assert "competency_mapping" in result
    assert 0 <= result["score"] <= 100

# tests/test_optimization.py
@pytest.mark.asyncio
async def test_personalize_learning_path():
    """Test learning path personalization."""
    result = await personalize_learning_path.ainvoke({
        "learner_id": "test-learner-001",
        "current_competencies": {"C1": "aware", "C2": "aware"},
        "role_requirements": {"C1": "working", "C2": "working", "C3": "aware"},
        "learning_preferences": {
            "format": "interactive",
            "pace": "self_paced",
            "time_availability": "evenings",
        },
    })
    
    assert "learning_path" in result
    assert "modules" in result
    assert len(result["modules"]) > 0
    # Should include modules for C1, C2, C3
    module_codes = [m["module_code"] for m in result["modules"]]
    assert any("C1" in str(m.get("competencies", [])) for m in result["modules"])
```

### 8.3 Integration Tests

```python
# tests/integration/test_agent_coordination.py
import pytest
from deepagents import create_deep_agent
from agents.supervisor import training_supervisor

@pytest.mark.asyncio
async def test_supervisor_delegates_to_content_creator():
    """Test that supervisor correctly delegates content creation tasks."""
    result = await training_supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Create training content for M01 targeting tier 1 learners",
        }]
    })
    
    # Verify sub-agent was invoked
    assert result["messages"] is not None
    # Verify content artifact was created
    assert any(
        "content_artifact" in str(msg).lower()
        for msg in result["messages"]
    )

@pytest.mark.asyncio
async def test_pipeline_state_management():
    """Test that pipeline state is correctly maintained across phases."""
    result = await training_supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": """
            Execute training pipeline for learner test-learner-001:
            1. Create content for M01
            2. Schedule delivery
            3. Generate assessment
            """,
        }]
    }, config=RunnableConfig(configurable={"thread_id": "test-pipeline-001"}))
    
    # Verify todo plan was created
    assert "todo_plan" in str(result).lower() or "write_todos" in str(result).lower()

@pytest.mark.asyncio
async def test_human_in_the_loop_gate():
    """Test that content approval gate is enforced."""
    # This test verifies that write_file operations trigger approval
    result = await training_supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Create and save a new training module M15",
        }]
    })
    
    # Should contain approval request
    assert "approval" in str(result).lower() or "interrupt" in str(result).lower()

# tests/integration/test_memory_persistence.py
@pytest.mark.asyncio
async def test_cross_session_memory():
    """Test that learner context persists across sessions."""
    # First session: learner completes M01
    result1 = await training_supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": "Enroll learner test-learner-001 in M01 and track completion",
        }]
    }, config=RunnableConfig(configurable={"thread_id": "test-memory-001"}))
    
    # Second session: check if M01 completion is remembered
    result2 = await training_supervisor.ainvoke({
        "messages": [{
            "role": "user",
            "content": "What modules has learner test-learner-001 completed?",
        }]
    }, config=RunnableConfig(configurable={"thread_id": "test-memory-001"}))
    
    # Should reference M01 completion from previous session
    assert "M01" in str(result2)
```

### 8.4 End-to-End Tests

```python
# tests/e2e/test_full_training_pipeline.py
import pytest
from pipeline.training_pipeline import run_training_pipeline

@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minute timeout
async def test_complete_onboarding_pipeline():
    """Test the complete onboarding pipeline from content creation to analytics."""
    
    result = await run_training_pipeline(
        learner_id="e2e-test-learner-001",
        role_tier=2,  # Practitioner
        required_competencies=["C1", "C2", "C3"],
    )
    
    # Verify all pipeline phases completed
    assert "content_artifacts" in result
    assert "delivery_schedule" in result
    assert "assessment_results" in result
    assert "optimization_recommendations" in result
    assert "kirkpatrick_levels" in result
    
    # Verify content was created
    assert len(result["content_artifacts"]) > 0
    
    # Verify delivery was scheduled
    assert result["delivery_schedule"] is not None
    
    # Verify assessment was completed
    assert result["assessment_results"] is not None
    
    # Verify Kirkpatrick evaluation
    assert "level_1" in result["kirkpatrick_levels"]
    assert "level_2" in result["kirkpatrick_levels"]

@pytest.mark.asyncio
async def test_compliance_evidence_generation():
    """Test that compliance evidence is generated for ISO 42001."""
    
    result = await run_training_pipeline(
        learner_id="e2e-test-learner-002",
        role_tier=3,  # Governance
        required_competencies=["C1", "C2"],
    )
    
    # Verify evidence was recorded
    assert "evidence_records" in result
    for evidence in result["evidence_records"]:
        assert evidence["clause"] in ["7.2", "7.3"]
        assert evidence["hash"] is not None
        assert evidence["captured_at"] is not None
```

### 8.5 Evaluation Tests

```python
# tests/evaluation/test_content_quality.py
from langsmith.evaluation import evaluate

def content_quality_evaluator(run, example):
    """Evaluate the quality of generated training content."""
    content = run.outputs.get("content", "")
    
    scores = {
        "alignment": score_objective_alignment(content, example["objectives"]),
        "clarity": score_content_clarity(content),
        "completeness": score_content_completeness(content, example["requirements"]),
        "compliance": score_iso_compliance(content, example["clause"]),
    }
    
    return {
        "key": "content_quality",
        "score": sum(scores.values()) / len(scores),
        "comment": f"Alignment: {scores['alignment']}, Clarity: {scores['clarity']}",
    }

# Run evaluation
results = evaluate(
    run_training_pipeline,
    data="training-content-eval-dataset",
    evaluators=[content_quality_evaluator],
    experiment_prefix="training-content-quality",
)

# tests/evaluation/test_assessment_accuracy.py
def assessment_accuracy_evaluator(run, example):
    """Evaluate the accuracy of assessment grading."""
    graded = run.outputs.get("graded_responses", [])
    expected = example["expected_scores"]
    
    accuracy = calculate_grading_accuracy(graded, expected)
    
    return {
        "key": "assessment_accuracy",
        "score": accuracy,
        "comment": f"Grading accuracy: {accuracy:.2%}",
    }
```

### 8.6 Performance Tests

```python
# tests/performance/test_agent_performance.py
import pytest
import time
from pipeline.training_pipeline import run_training_pipeline

@pytest.mark.asyncio
async def test_content_creation_performance():
    """Test that content creation completes within acceptable time."""
    start = time.time()
    
    result = await run_training_pipeline(
        learner_id="perf-test-learner-001",
        role_tier=1,
        required_competencies=["C1"],
    )
    
    elapsed = time.time() - start
    
    # Content creation should complete within 2 minutes
    assert elapsed < 120, f"Content creation took {elapsed:.1f}s (limit: 120s)"

@pytest.mark.asyncio
async def test_concurrent_learner_processing():
    """Test that multiple learners can be processed concurrently."""
    learners = [f"concurrent-learner-{i}" for i in range(10)]
    
    start = time.time()
    
    results = await asyncio.gather(*[
        run_training_pipeline(
            learner_id=learner_id,
            role_tier=2,
            required_competencies=["C1", "C2"],
        )
        for learner_id in learners
    ])
    
    elapsed = time.time() - start
    
    # 10 learners should complete within 5 minutes (parallel processing)
    assert elapsed < 300, f"Concurrent processing took {elapsed:.1f}s (limit: 300s)"
    assert len(results) == 10
```

### 8.7 Test Data Fixtures

```python
# tests/conftest.py
import pytest
from typing import Dict, List

@pytest.fixture
def sample_learner() -> Dict:
    """Sample learner profile for testing."""
    return {
        "id": "test-learner-001",
        "email": "test@company.com",
        "name": "Test Learner",
        "role": "Data Analyst",
        "tier": 1,
        "department": "Finance",
        "competence_levels": {"C1": "aware", "C2": "aware"},
        "learning_preferences": {
            "format": "interactive",
            "pace": "self_paced",
        },
    }

@pytest.fixture
def sample_module() -> Dict:
    """Sample training module for testing."""
    return {
        "code": "M01",
        "title": "AI Awareness & Policy",
        "tier": 0,
        "competencies": ["C1"],
        "clause": "7.3",
        "format": "self-paced",
        "duration_minutes": 30,
        "passing_score": 70,
    }

@pytest.fixture
def sample_assessment() -> Dict:
    """Sample assessment for testing."""
    return {
        "id": "test-assessment-001",
        "module_code": "M01",
        "questions": [
            {
                "id": "q1",
                "type": "multiple_choice",
                "question": "What is the primary purpose of ISO 42001?",
                "options": [
                    "A) Certify AI systems",
                    "B) Establish AI management systems",
                    "C) Regulate AI development",
                    "D) Standardize AI terminology",
                ],
                "answer": "B",
                "competency": "C1",
            },
        ],
        "passing_score": 70,
    }

@pytest.fixture
def sample_training_dataset() -> List[Dict]:
    """Sample dataset for evaluation tests."""
    return [
        {
            "learner_id": f"eval-learner-{i}",
            "role_tier": i % 5,
            "required_competencies": [f"C{i % 10 + 1}"],
            "expected_outcomes": {
                "completion": True,
                "score": 70 + (i % 30),
            },
        }
        for i in range(50)
    ]
```

### 8.8 CI/CD Integration

```yaml
# .github/workflows/training-tests.yml
name: Training System Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest tests/unit/ -v --cov=agents --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
      redis:
        image: redis:7
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql://postgres:test@localhost/test
          REDIS_URL: redis://localhost:6379

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest tests/e2e/ -v --timeout=300
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}

  evaluation:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[test]"
      - run: pytest tests/evaluation/ -v
        env:
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
```

---

## Appendix A: Environment Setup

```bash
# Install dependencies
pip install -U deepagents langchain-openai langchain-anthropic
pip install -U langgraph langsmith langchain-mcp-adapters
pip install -U pytest pytest-asyncio pytest-timeout

# Set environment variables
export OPENAI_API_KEY="your-key"
export LANGCHAIN_API_KEY="your-key"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="grc-claw-training"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agents --cov-report=html
```

## Appendix B: Configuration Reference

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `openai:gpt-5.5` | LLM for agent reasoning |
| `recursion_limit` | 100 | Maximum agent loop iterations |
| `max_tokens` | 8000 | Context window threshold for summarization |
| `messages_to_keep` | 20 | Messages retained after summarization |
| `checkpointer` | `PostgresSaver` | Durable execution state store |
| `memory_store` | `InMemoryStore` | Cross-session memory backend |
| `workspace_root` | `./training_artifacts/` | Virtual filesystem root |
| `interrupt_on` | `write_file`, `edit_file` | Human-in-the-loop gates |

---

*End of Implementation Plan*
