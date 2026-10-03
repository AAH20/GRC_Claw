"""
Talent Pool Manager Agent for Recruitment Platform.

Manages talent pools — curated collections of candidates organized by
skill set, role, or recruitment campaign. Provides pool CRUD operations,
candidate-to-pool assignment, and cross-pool search with filtering.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PoolVisibility(str, Enum):
    """Visibility level for a talent pool."""
    PRIVATE = "private"
    TEAM = "team"
    ORGANIZATION = "organization"


class CandidateStatus(str, Enum):
    """Status of a candidate within a talent pool."""
    NEW = "new"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    HIRED = "hired"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class PoolActivityType(str, Enum):
    """Types of activities tracked in a talent pool."""
    CANDIDATE_ADDED = "candidate_added"
    CANDIDATE_REMOVED = "candidate_removed"
    CANDIDATE_UPDATED = "candidate_updated"
    POOL_CREATED = "pool_created"
    POOL_UPDATED = "pool_updated"
    POOL_DELETED = "pool_deleted"
    NOTE_ADDED = "note_added"
    TAG_ADDED = "tag_added"
    TAG_REMOVED = "tag_removed"
    STAGE_CHANGED = "stage_changed"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """Represents a candidate in the recruitment platform."""
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    experience_years: float = 0.0
    current_title: Optional[str] = None
    current_company: Optional[str] = None
    location: Optional[str] = None
    desired_salary_min: Optional[int] = None
    desired_salary_max: Optional[int] = None
    availability: Optional[str] = None
    source: Optional[str] = None
    rating: int = 0  # 1-5
    tags: List[str] = field(default_factory=list)
    notes: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PoolMembership:
    """Represents a candidate's membership in a talent pool."""
    candidate_id: str
    pool_id: str
    status: CandidateStatus = CandidateStatus.NEW
    added_at: datetime = field(default_factory=datetime.utcnow)
    added_by: Optional[str] = None
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TalentPool:
    """Represents a talent pool — a curated collection of candidates."""
    id: str
    name: str
    description: Optional[str] = None
    visibility: PoolVisibility = PoolVisibility.TEAM
    owner_id: Optional[str] = None
    team_id: Optional[str] = None
    memberships: Dict[str, PoolMembership] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    criteria: Dict[str, Any] = field(default_factory=dict)
    activity_log: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_archived: bool = False


@dataclass
class PoolSearchResult:
    """Result item from a talent pool search."""
    pool: TalentPool
    matched_candidates: List[Candidate]
    match_score: float
    match_reasons: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mock Data
# ---------------------------------------------------------------------------

def _generate_mock_candidates() -> Dict[str, Candidate]:
    """Generate realistic mock candidate data."""
    now = datetime.utcnow()
    candidates: Dict[str, Candidate] = {}

    mock_data: List[Dict[str, Any]] = [
        {
            "id": "cand_001",
            "full_name": "Sarah Chen",
            "email": "sarah.chen@email.com",
            "phone": "+1-415-555-0101",
            "skills": ["Python", "Machine Learning", "TensorFlow", "AWS", "Docker"],
            "experience_years": 7.5,
            "current_title": "Senior ML Engineer",
            "current_company": "TechCorp",
            "location": "San Francisco, CA",
            "desired_salary_min": 180000,
            "desired_salary_max": 220000,
            "availability": "2 weeks",
            "source": "LinkedIn",
            "rating": 5,
            "tags": ["ml", "python", "senior", "referral"],
        },
        {
            "id": "cand_002",
            "full_name": "Marcus Johnson",
            "email": "marcus.j@email.com",
            "phone": "+1-212-555-0202",
            "skills": ["Java", "Spring Boot", "Microservices", "Kubernetes", "PostgreSQL"],
            "experience_years": 9.0,
            "current_title": "Staff Software Engineer",
            "current_company": "FinanceHub",
            "location": "New York, NY",
            "desired_salary_min": 200000,
            "desired_salary_max": 250000,
            "availability": "1 month",
            "source": "Indeed",
            "rating": 4,
            "tags": ["java", "backend", "staff-level"],
        },
        {
            "id": "cand_003",
            "full_name": "Priya Patel",
            "email": "priya.patel@email.com",
            "phone": "+1-206-555-0303",
            "skills": ["React", "TypeScript", "Node.js", "GraphQL", "Figma"],
            "experience_years": 5.0,
            "current_title": "Frontend Engineer",
            "current_company": "DesignStudio",
            "location": "Seattle, WA",
            "desired_salary_min": 140000,
            "desired_salary_max": 170000,
            "availability": "Immediate",
            "source": "Portfolio",
            "rating": 4,
            "tags": ["frontend", "react", "ui-ux"],
        },
        {
            "id": "cand_004",
            "full_name": "David Kim",
            "email": "david.kim@email.com",
            "phone": "+1-312-555-0404",
            "skills": ["Go", "Rust", "Distributed Systems", "gRPC", "etcd"],
            "experience_years": 11.0,
            "current_title": "Principal Engineer",
            "current_company": "CloudScale",
            "location": "Chicago, IL",
            "desired_salary_min": 250000,
            "desired_salary_max": 300000,
            "availability": "2 months",
            "source": "GitHub",
            "rating": 5,
            "tags": ["systems", "go", "principal", "low-level"],
        },
        {
            "id": "cand_005",
            "full_name": "Elena Rodriguez",
            "email": "elena.r@email.com",
            "phone": "+1-512-555-0505",
            "skills": ["Product Management", "Agile", "SQL", "A/B Testing", "Jira"],
            "experience_years": 6.0,
            "current_title": "Senior Product Manager",
            "current_company": "StartupXYZ",
            "location": "Austin, TX",
            "desired_salary_min": 160000,
            "desired_salary_max": 190000,
            "availability": "3 weeks",
            "source": "Referral",
            "rating": 4,
            "tags": ["product", "agile", "senior"],
        },
        {
            "id": "cand_006",
            "full_name": "James O'Brien",
            "email": "james.obrien@email.com",
            "phone": "+1-617-555-0606",
            "skills": ["Python", "Django", "PostgreSQL", "Redis", "Celery"],
            "experience_years": 4.0,
            "current_title": "Backend Developer",
            "current_company": "WebAgency",
            "location": "Boston, MA",
            "desired_salary_min": 120000,
            "desired_salary_max": 150000,
            "availability": "2 weeks",
            "source": "Stack Overflow",
            "rating": 3,
            "tags": ["python", "backend", "mid-level"],
        },
        {
            "id": "cand_007",
            "full_name": "Aisha Mohammed",
            "email": "aisha.m@email.com",
            "phone": "+1-404-555-0707",
            "skills": ["Data Engineering", "Spark", "Airflow", "Python", "Snowflake"],
            "experience_years": 8.0,
            "current_title": "Lead Data Engineer",
            "current_company": "DataDriven Inc",
            "location": "Atlanta, GA",
            "desired_salary_min": 190000,
            "desired_salary_max": 230000,
            "availability": "1 month",
            "source": "LinkedIn",
            "rating": 5,
            "tags": ["data", "spark", "lead"],
        },
        {
            "id": "cand_008",
            "full_name": "Tom Mueller",
            "email": "tom.mueller@email.com",
            "phone": "+1-303-555-0808",
            "skills": ["DevOps", "Terraform", "AWS", "CI/CD", "Ansible"],
            "experience_years": 6.5,
            "current_title": "DevOps Engineer",
            "current_company": "InfraCore",
            "location": "Denver, CO",
            "desired_salary_min": 150000,
            "desired_salary_max": 180000,
            "availability": "Immediate",
            "source": "Indeed",
            "rating": 4,
            "tags": ["devops", "aws", "infrastructure"],
        },
        {
            "id": "cand_009",
            "full_name": "Lisa Wang",
            "email": "lisa.wang@email.com",
            "phone": "+1-650-555-0909",
            "skills": ["Security", "Penetration Testing", "SIEM", "Python", "OSCP"],
            "experience_years": 10.0,
            "current_title": "Security Engineer",
            "current_company": "CyberShield",
            "location": "Palo Alto, CA",
            "desired_salary_min": 210000,
            "desired_salary_max": 260000,
            "availability": "2 months",
            "source": "Conference",
            "rating": 5,
            "tags": ["security", "senior", "offensive"],
        },
        {
            "id": "cand_010",
            "full_name": "Carlos Mendez",
            "email": "carlos.m@email.com",
            "phone": "+1-305-555-1010",
            "skills": ["Mobile", "Swift", "Kotlin", "React Native", "Firebase"],
            "experience_years": 5.5,
            "current_title": "Mobile Engineer",
            "current_company": "AppFactory",
            "location": "Miami, FL",
            "desired_salary_min": 145000,
            "desired_salary_max": 175000,
            "availability": "3 weeks",
            "source": "GitHub",
            "rating": 4,
            "tags": ["mobile", "ios", "android"],
        },
        {
            "id": "cand_011",
            "full_name": "Rachel Green",
            "email": "rachel.g@email.com",
            "phone": "+1-212-555-1111",
            "skills": ["UX Research", "User Testing", "Figma", "Design Systems", "Accessibility"],
            "experience_years": 7.0,
            "current_title": "Senior UX Researcher",
            "current_company": "DesignFirst",
            "location": "Brooklyn, NY",
            "desired_salary_min": 155000,
            "desired_salary_max": 185000,
            "availability": "1 month",
            "source": "Portfolio",
            "rating": 4,
            "tags": ["ux", "research", "senior"],
        },
        {
            "id": "cand_012",
            "full_name": "Ahmed Hassan",
            "email": "ahmed.hassan@email.com",
            "phone": "+1-415-555-1212",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
            "experience_years": 8.0,
            "current_title": "Senior Backend Engineer",
            "current_company": "RecruitmentPlatform",
            "location": "San Francisco, CA",
            "desired_salary_min": 190000,
            "desired_salary_max": 230000,
            "availability": "2 weeks",
            "source": "Internal",
            "rating": 5,
            "tags": ["python", "backend", "senior", "full-stack"],
        },
    ]

    for data in mock_data:
        candidate = Candidate(
            id=data["id"],
            full_name=data["full_name"],
            email=data["email"],
            phone=data.get("phone"),
            skills=data.get("skills", []),
            experience_years=data.get("experience_years", 0.0),
            current_title=data.get("current_title"),
            current_company=data.get("current_company"),
            location=data.get("location"),
            desired_salary_min=data.get("desired_salary_min"),
            desired_salary_max=data.get("desired_salary_max"),
            availability=data.get("availability"),
            source=data.get("source"),
            rating=data.get("rating", 0),
            tags=data.get("tags", []),
            created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=5),
        )
        candidates[candidate.id] = candidate

    return candidates


def _generate_mock_pools() -> Dict[str, TalentPool]:
    """Generate realistic mock talent pool data."""
    now = datetime.utcnow()
    pools: Dict[str, TalentPool] = {}

    mock_pools: List[Dict[str, Any]] = [
        {
            "id": "pool_001",
            "name": "Senior Backend Engineers",
            "description": "Top-tier backend engineering talent for platform team",
            "visibility": PoolVisibility.TEAM,
            "owner_id": "user_001",
            "team_id": "team_engineering",
            "tags": ["backend", "senior", "platform"],
            "criteria": {"min_experience": 7, "required_skills": ["Python", "Go", "Java"]},
        },
        {
            "id": "pool_002",
            "name": "ML/AI Talent Pipeline",
            "description": "Machine learning and AI candidates for research and product teams",
            "visibility": PoolVisibility.ORGANIZATION,
            "owner_id": "user_002",
            "team_id": "team_ml",
            "tags": ["ml", "ai", "data-science"],
            "criteria": {"min_experience": 4, "required_skills": ["Python", "TensorFlow", "PyTorch"]},
        },
        {
            "id": "pool_003",
            "name": "Frontend React Specialists",
            "description": "React and TypeScript experts for UI team",
            "visibility": PoolVisibility.TEAM,
            "owner_id": "user_003",
            "team_id": "team_frontend",
            "tags": ["frontend", "react", "typescript"],
            "criteria": {"min_experience": 3, "required_skills": ["React", "TypeScript"]},
        },
        {
            "id": "pool_004",
            "name": "DevOps & Infrastructure",
            "description": "DevOps, SRE, and infrastructure engineering candidates",
            "visibility": PoolVisibility.TEAM,
            "owner_id": "user_004",
            "team_id": "team_infra",
            "tags": ["devops", "sre", "infrastructure"],
            "criteria": {"min_experience": 4, "required_skills": ["AWS", "Terraform", "Kubernetes"]},
        },
        {
            "id": "pool_005",
            "name": "Product Managers",
            "description": "Product management talent for B2B SaaS products",
            "visibility": PoolVisibility.ORGANIZATION,
            "owner_id": "user_005",
            "team_id": "team_product",
            "tags": ["product", "b2b", "saas"],
            "criteria": {"min_experience": 4, "required_skills": ["Product Management", "Agile"]},
        },
        {
            "id": "pool_006",
            "name": "Security Engineers",
            "description": "Application and infrastructure security specialists",
            "visibility": PoolVisibility.PRIVATE,
            "owner_id": "user_006",
            "team_id": "team_security",
            "tags": ["security", "appsec", "infosec"],
            "criteria": {"min_experience": 5, "required_skills": ["Security", "Penetration Testing"]},
        },
        {
            "id": "pool_007",
            "name": "Data Engineers",
            "description": "Data pipeline and analytics engineering talent",
            "visibility": PoolVisibility.TEAM,
            "owner_id": "user_007",
            "team_id": "team_data",
            "tags": ["data", "engineering", "analytics"],
            "criteria": {"min_experience": 5, "required_skills": ["Python", "Spark", "SQL"]},
        },
        {
            "id": "pool_008",
            "name": "Mobile Engineers",
            "description": "iOS, Android, and cross-platform mobile developers",
            "visibility": PoolVisibility.TEAM,
            "owner_id": "user_008",
            "team_id": "team_mobile",
            "tags": ["mobile", "ios", "android"],
            "criteria": {"min_experience": 3, "required_skills": ["Swift", "Kotlin", "React Native"]},
        },
    ]

    for data in mock_pools:
        pool = TalentPool(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            visibility=data.get("visibility", PoolVisibility.TEAM),
            owner_id=data.get("owner_id"),
            team_id=data.get("team_id"),
            tags=data.get("tags", []),
            criteria=data.get("criteria", {}),
            created_at=now - timedelta(days=60),
            updated_at=now - timedelta(days=10),
        )
        pools[pool.id] = pool

    # Populate memberships
    membership_map: Dict[str, List[Tuple[str, CandidateStatus]]] = {
        "pool_001": [
            ("cand_001", CandidateStatus.INTERVIEWING),
            ("cand_002", CandidateStatus.SCREENING),
            ("cand_004", CandidateStatus.NEW),
            ("cand_012", CandidateStatus.INTERVIEWING),
        ],
        "pool_002": [
            ("cand_001", CandidateStatus.OFFERED),
            ("cand_007", CandidateStatus.SCREENING),
        ],
        "pool_003": [
            ("cand_003", CandidateStatus.INTERVIEWING),
            ("cand_011", CandidateStatus.NEW),
        ],
        "pool_004": [
            ("cand_008", CandidateStatus.SCREENING),
            ("cand_004", CandidateStatus.NEW),
        ],
        "pool_005": [
            ("cand_005", CandidateStatus.INTERVIEWING),
        ],
        "pool_006": [
            ("cand_009", CandidateStatus.SCREENING),
        ],
        "pool_007": [
            ("cand_007", CandidateStatus.OFFERED),
            ("cand_001", CandidateStatus.NEW),
        ],
        "pool_008": [
            ("cand_010", CandidateStatus.NEW),
        ],
    }

    for pool_id, members in membership_map.items():
        pool = pools[pool_id]
        for cand_id, status in members:
            membership = PoolMembership(
                candidate_id=cand_id,
                pool_id=pool_id,
                status=status,
                added_at=now - timedelta(days=15),
                added_by="user_001",
            )
            pool.memberships[cand_id] = membership

    return pools


# ---------------------------------------------------------------------------
# Talent Pool Manager
# ---------------------------------------------------------------------------

class TalentPoolManager:
    """
    Manages talent pools for the recruitment platform.

    Provides operations to create, update, and search talent pools,
    add/remove candidates, and query across pools with flexible filtering.
    """

    def __init__(self) -> None:
        """Initialize the talent pool manager with mock data."""
        self._candidates: Dict[str, Candidate] = _generate_mock_candidates()
        self._pools: Dict[str, TalentPool] = _generate_mock_pools()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_to_pool(
        self,
        candidate_id: str,
        pool_id: str,
        *,
        added_by: Optional[str] = None,
        status: CandidateStatus = CandidateStatus.NEW,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> PoolMembership:
        """
        Add a candidate to a talent pool.

        Args:
            candidate_id: The unique identifier of the candidate to add.
            pool_id: The unique identifier of the target talent pool.
            added_by: Optional identifier of the user adding the candidate.
            status: Initial status of the candidate in the pool.
            custom_fields: Optional custom field values for this membership.

        Returns:
            The created PoolMembership object.

        Raises:
            ValueError: If the candidate_id or pool_id does not exist.
            RuntimeError: If the candidate is already in the pool.
        """
        if candidate_id not in self._candidates:
            raise ValueError(
                f"Candidate with id '{candidate_id}' does not exist. "
                f"Available candidates: {list(self._candidates.keys())}"
            )

        if pool_id not in self._pools:
            raise ValueError(
                f"Talent pool with id '{pool_id}' does not exist. "
                f"Available pools: {list(self._pools.keys())}"
            )

        pool = self._pools[pool_id]

        if candidate_id in pool.memberships:
            raise RuntimeError(
                f"Candidate '{candidate_id}' is already a member of pool '{pool_id}'. "
                f"Current status: {pool.memberships[candidate_id].status.value}"
            )

        membership = PoolMembership(
            candidate_id=candidate_id,
            pool_id=pool_id,
            status=status,
            added_by=added_by,
            custom_fields=custom_fields or {},
        )

        pool.memberships[candidate_id] = membership
        pool.updated_at = datetime.utcnow()

        # Log activity
        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.CANDIDATE_ADDED,
            details={
                "candidate_id": candidate_id,
                "candidate_name": self._candidates[candidate_id].full_name,
                "added_by": added_by,
                "initial_status": status.value,
            },
        )

        return membership

    def search_pools(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[PoolSearchResult]:
        """
        Search across talent pools using a text query and optional filters.

        The search matches against pool names, descriptions, tags, and
        candidate attributes (name, skills, title, company). Results are
        ranked by relevance score.

        Args:
            query: The search query string. Matches pool metadata and
                candidate attributes.
            filters: Optional dictionary of filters to narrow results.
                Supported keys:
                - pool_ids: List[str] — restrict to specific pools
                - visibility: PoolVisibility — filter by visibility level
                - tags: List[str] — pools must have at least one of these tags
                - skills: List[str] — candidates must have at least one skill
                - min_experience: float — minimum candidate experience years
                - max_experience: float — maximum candidate experience years
                - locations: List[str] — filter by candidate location
                - min_rating: int — minimum candidate rating (1-5)
                - statuses: List[CandidateStatus] — filter by membership status
                - min_pool_size: int — minimum candidates in pool
                - max_pool_size: int — maximum candidates in pool
                - owner_id: str — filter by pool owner
                - team_id: str — filter by team
                - include_archived: bool — include archived pools (default False)

        Returns:
            A list of PoolSearchResult objects sorted by match_score descending.
            Each result contains the pool, matched candidates, score, and reasons.

        Raises:
            ValueError: If the query is empty or filters contain invalid values.
        """
        if not query or not query.strip():
            raise ValueError("Search query must be a non-empty string.")

        filters = filters or {}
        query_lower = query.lower().strip()
        query_terms = set(query_lower.split())

        results: List[PoolSearchResult] = []

        for pool in self._pools.values():
            # Apply pool-level filters
            if not self._passes_pool_filters(pool, filters):
                continue

            # Score pool-level match
            pool_score, pool_reasons = self._score_pool_match(pool, query_terms, query_lower)

            # Find matching candidates within the pool
            matched_candidates: List[Candidate] = []
            candidate_score = 0.0

            for cand_id, membership in pool.memberships.items():
                candidate = self._candidates[cand_id]

                # Apply candidate-level filters
                if not self._passes_candidate_filters(candidate, membership, filters):
                    continue

                cand_score, cand_reasons = self._score_candidate_match(
                    candidate, query_terms, query_lower
                )

                if cand_score > 0:
                    matched_candidates.append(candidate)
                    candidate_score += cand_score
                    pool_reasons.extend(cand_reasons)

            # Combine scores
            total_score = pool_score + candidate_score

            if total_score > 0 or matched_candidates:
                # Deduplicate reasons
                unique_reasons = list(dict.fromkeys(pool_reasons))
                results.append(
                    PoolSearchResult(
                        pool=pool,
                        matched_candidates=matched_candidates,
                        match_score=round(total_score, 2),
                        match_reasons=unique_reasons,
                    )
                )

        # Sort by score descending
        results.sort(key=lambda r: r.match_score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Pool CRUD
    # ------------------------------------------------------------------

    def create_pool(
        self,
        name: str,
        description: Optional[str] = None,
        visibility: PoolVisibility = PoolVisibility.TEAM,
        owner_id: Optional[str] = None,
        team_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        criteria: Optional[Dict[str, Any]] = None,
    ) -> TalentPool:
        """Create a new talent pool."""
        pool_id = f"pool_{uuid.uuid4().hex[:8]}"
        pool = TalentPool(
            id=pool_id,
            name=name,
            description=description,
            visibility=visibility,
            owner_id=owner_id,
            team_id=team_id,
            tags=tags or [],
            criteria=criteria or {},
        )
        self._pools[pool_id] = pool

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.POOL_CREATED,
            details={"name": name, "owner_id": owner_id},
        )

        return pool

    def get_pool(self, pool_id: str) -> Optional[TalentPool]:
        """Retrieve a talent pool by ID."""
        return self._pools.get(pool_id)

    def update_pool(
        self,
        pool_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[PoolVisibility] = None,
        tags: Optional[List[str]] = None,
        criteria: Optional[Dict[str, Any]] = None,
    ) -> TalentPool:
        """Update an existing talent pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if name is not None:
            pool.name = name
        if description is not None:
            pool.description = description
        if visibility is not None:
            pool.visibility = visibility
        if tags is not None:
            pool.tags = tags
        if criteria is not None:
            pool.criteria = criteria

        pool.updated_at = datetime.utcnow()

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.POOL_UPDATED,
            details={"updated_fields": [k for k, v in {
                "name": name, "description": description, "visibility": visibility,
                "tags": tags, "criteria": criteria,
            }.items() if v is not None]},
        )

        return pool

    def delete_pool(self, pool_id: str) -> bool:
        """Delete a talent pool. Returns True if deleted, False if not found."""
        if pool_id not in self._pools:
            return False

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.POOL_DELETED,
            details={"pool_name": self._pools[pool_id].name},
        )

        del self._pools[pool_id]
        return True

    def list_pools(
        self,
        *,
        visibility: Optional[PoolVisibility] = None,
        owner_id: Optional[str] = None,
        team_id: Optional[str] = None,
        include_archived: bool = False,
    ) -> List[TalentPool]:
        """List all talent pools with optional filtering."""
        pools = list(self._pools.values())

        if not include_archived:
            pools = [p for p in pools if not p.is_archived]
        if visibility is not None:
            pools = [p for p in pools if p.visibility == visibility]
        if owner_id is not None:
            pools = [p for p in pools if p.owner_id == owner_id]
        if team_id is not None:
            pools = [p for p in pools if p.team_id == team_id]

        return pools

    # ------------------------------------------------------------------
    # Candidate-to-Pool Operations
    # ------------------------------------------------------------------

    def remove_from_pool(self, candidate_id: str, pool_id: str) -> bool:
        """Remove a candidate from a talent pool. Returns True if removed."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if candidate_id not in pool.memberships:
            return False

        del pool.memberships[candidate_id]
        pool.updated_at = datetime.utcnow()

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.CANDIDATE_REMOVED,
            details={"candidate_id": candidate_id},
        )

        return True

    def update_membership_status(
        self,
        candidate_id: str,
        pool_id: str,
        new_status: CandidateStatus,
    ) -> PoolMembership:
        """Update a candidate's status within a talent pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if candidate_id not in pool.memberships:
            raise ValueError(
                f"Candidate '{candidate_id}' is not a member of pool '{pool_id}'."
            )

        membership = pool.memberships[candidate_id]
        old_status = membership.status
        membership.status = new_status

        membership.stage_history.append({
            "from_status": old_status.value,
            "to_status": new_status.value,
            "changed_at": datetime.utcnow().isoformat(),
        })

        pool.updated_at = datetime.utcnow()

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.STAGE_CHANGED,
            details={
                "candidate_id": candidate_id,
                "from_status": old_status.value,
                "to_status": new_status.value,
            },
        )

        return membership

    def get_pool_candidates(
        self,
        pool_id: str,
        *,
        status: Optional[CandidateStatus] = None,
    ) -> List[Candidate]:
        """Get all candidates in a talent pool, optionally filtered by status."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]
        candidates: List[Candidate] = []

        for cand_id, membership in pool.memberships.items():
            if status is not None and membership.status != status:
                continue
            candidates.append(self._candidates[cand_id])

        return candidates

    def get_candidate_pools(self, candidate_id: str) -> List[TalentPool]:
        """Get all talent pools that a candidate belongs to."""
        if candidate_id not in self._candidates:
            raise ValueError(f"Candidate '{candidate_id}' does not exist.")

        return [
            pool for pool in self._pools.values()
            if candidate_id in pool.memberships
        ]

    def is_candidate_in_pool(self, candidate_id: str, pool_id: str) -> bool:
        """Check if a candidate is a member of a specific pool."""
        if pool_id not in self._pools:
            return False
        return candidate_id in self._pools[pool_id].memberships

    # ------------------------------------------------------------------
    # Tagging & Notes
    # ------------------------------------------------------------------

    def add_tag_to_candidate(
        self,
        candidate_id: str,
        pool_id: str,
        tag: str,
    ) -> PoolMembership:
        """Add a tag to a candidate within a specific pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if candidate_id not in pool.memberships:
            raise ValueError(
                f"Candidate '{candidate_id}' is not a member of pool '{pool_id}'."
            )

        membership = pool.memberships[candidate_id]

        if tag not in membership.custom_fields.get("tags", []):
            if "tags" not in membership.custom_fields:
                membership.custom_fields["tags"] = []
            membership.custom_fields["tags"].append(tag)

            self._log_activity(
                pool_id=pool_id,
                activity_type=PoolActivityType.TAG_ADDED,
                details={"candidate_id": candidate_id, "tag": tag},
            )

        return membership

    def remove_tag_from_candidate(
        self,
        candidate_id: str,
        pool_id: str,
        tag: str,
    ) -> PoolMembership:
        """Remove a tag from a candidate within a specific pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if candidate_id not in pool.memberships:
            raise ValueError(
                f"Candidate '{candidate_id}' is not a member of pool '{pool_id}'."
            )

        membership = pool.memberships[candidate_id]
        tags = membership.custom_fields.get("tags", [])

        if tag in tags:
            tags.remove(tag)
            self._log_activity(
                pool_id=pool_id,
                activity_type=PoolActivityType.TAG_REMOVED,
                details={"candidate_id": candidate_id, "tag": tag},
            )

        return membership

    def add_note_to_candidate(
        self,
        candidate_id: str,
        pool_id: str,
        note: str,
        author_id: Optional[str] = None,
    ) -> PoolMembership:
        """Add a note to a candidate within a specific pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]

        if candidate_id not in pool.memberships:
            raise ValueError(
                f"Candidate '{candidate_id}' is not a member of pool '{pool_id}'."
            )

        membership = pool.memberships[candidate_id]

        if "notes" not in membership.custom_fields:
            membership.custom_fields["notes"] = []

        membership.custom_fields["notes"].append({
            "text": note,
            "author_id": author_id,
            "created_at": datetime.utcnow().isoformat(),
        })

        self._log_activity(
            pool_id=pool_id,
            activity_type=PoolActivityType.NOTE_ADDED,
            details={"candidate_id": candidate_id, "author_id": author_id},
        )

        return membership

    # ------------------------------------------------------------------
    # Analytics & Insights
    # ------------------------------------------------------------------

    def get_pool_statistics(self, pool_id: str) -> Dict[str, Any]:
        """Get statistics for a talent pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]
        memberships = list(pool.memberships.values())

        status_counts: Dict[str, int] = {}
        for m in memberships:
            status_counts[m.status.value] = status_counts.get(m.status.value, 0) + 1

        all_skills: List[str] = []
        total_experience = 0.0
        for cand_id in pool.memberships:
            candidate = self._candidates[cand_id]
            all_skills.extend(candidate.skills)
            total_experience += candidate.experience_years

        skill_counts: Dict[str, int] = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "pool_id": pool_id,
            "pool_name": pool.name,
            "total_candidates": len(memberships),
            "status_breakdown": status_counts,
            "average_experience": round(total_experience / len(memberships), 1) if memberships else 0,
            "top_skills": [{"skill": s, "count": c} for s, c in top_skills],
            "visibility": pool.visibility.value,
            "created_at": pool.created_at.isoformat(),
            "last_updated": pool.updated_at.isoformat(),
        }

    def get_pool_activity_log(
        self,
        pool_id: str,
        *,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get the activity log for a talent pool."""
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        log = self._pools[pool_id].activity_log
        return log[-limit:] if limit > 0 else log

    def get_trending_skills(self, *, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get the most common skills across all talent pools."""
        skill_counts: Dict[str, int] = {}

        for pool in self._pools.values():
            for cand_id in pool.memberships:
                candidate = self._candidates[cand_id]
                for skill in candidate.skills:
                    skill_counts[skill] = skill_counts.get(skill, 0) + 1

        sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"skill": s, "count": c} for s, c in sorted_skills[:top_n]]

    def get_suggested_candidates(
        self,
        pool_id: str,
        *,
        limit: int = 10,
    ) -> List[Candidate]:
        """
        Get candidate suggestions for a pool based on pool criteria.

        Suggests candidates not already in the pool whose skills and
        experience match the pool's criteria.
        """
        if pool_id not in self._pools:
            raise ValueError(f"Talent pool '{pool_id}' does not exist.")

        pool = self._pools[pool_id]
        criteria = pool.criteria
        required_skills = set(criteria.get("required_skills", []))
        min_experience = criteria.get("min_experience", 0)

        suggestions: List[Tuple[float, Candidate]] = []

        for candidate in self._candidates.values():
            if candidate.id in pool.memberships:
                continue

            score = 0.0

            # Skill match
            candidate_skills = set(s.lower() for s in candidate.skills)
            required_lower = set(s.lower() for s in required_skills)
            skill_overlap = candidate_skills & required_lower
            if required_skills:
                score += len(skill_overlap) / len(required_skills) * 10

            # Experience match
            if min_experience > 0:
                if candidate.experience_years >= min_experience:
                    score += 5
                else:
                    score -= 2

            # Rating bonus
            score += candidate.rating

            if score > 0:
                suggestions.append((score, candidate))

        suggestions.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in suggestions[:limit]]

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def bulk_add_to_pool(
        self,
        candidate_ids: List[str],
        pool_id: str,
        *,
        added_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add multiple candidates to a talent pool.

        Returns a summary with successful additions and failures.
        """
        added: List[str] = []
        already_in_pool: List[str] = []
        not_found: List[str] = []

        for cand_id in candidate_ids:
            try:
                self.add_to_pool(cand_id, pool_id, added_by=added_by)
                added.append(cand_id)
            except ValueError as e:
                if "does not exist" in str(e):
                    not_found.append(cand_id)
                else:
                    raise
            except RuntimeError:
                already_in_pool.append(cand_id)

        return {
            "pool_id": pool_id,
            "added": added,
            "already_in_pool": already_in_pool,
            "not_found": not_found,
            "total_requested": len(candidate_ids),
            "total_added": len(added),
        }

    def bulk_remove_from_pool(
        self,
        candidate_ids: List[str],
        pool_id: str,
    ) -> Dict[str, Any]:
        """Remove multiple candidates from a talent pool."""
        removed: List[str] = []
        not_in_pool: List[str] = []

        for cand_id in candidate_ids:
            if self.remove_from_pool(cand_id, pool_id):
                removed.append(cand_id)
            else:
                not_in_pool.append(cand_id)

        return {
            "pool_id": pool_id,
            "removed": removed,
            "not_in_pool": not_in_pool,
            "total_requested": len(candidate_ids),
            "total_removed": len(removed),
        }

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _passes_pool_filters(
        self,
        pool: TalentPool,
        filters: Dict[str, Any],
    ) -> bool:
        """Check if a pool passes the pool-level filters."""
        if not filters.get("include_archived", False) and pool.is_archived:
            return False

        pool_ids = filters.get("pool_ids")
        if pool_ids and pool.id not in pool_ids:
            return False

        visibility = filters.get("visibility")
        if visibility and pool.visibility != visibility:
            return False

        tags = filters.get("tags")
        if tags and not any(t in pool.tags for t in tags):
            return False

        owner_id = filters.get("owner_id")
        if owner_id and pool.owner_id != owner_id:
            return False

        team_id = filters.get("team_id")
        if team_id and pool.team_id != team_id:
            return False

        min_size = filters.get("min_pool_size")
        if min_size is not None and len(pool.memberships) < min_size:
            return False

        max_size = filters.get("max_pool_size")
        if max_size is not None and len(pool.memberships) > max_size:
            return False

        return True

    def _passes_candidate_filters(
        self,
        candidate: Candidate,
        membership: PoolMembership,
        filters: Dict[str, Any],
    ) -> bool:
        """Check if a candidate passes the candidate-level filters."""
        skills = filters.get("skills")
        if skills:
            candidate_skills_lower = set(s.lower() for s in candidate.skills)
            filter_skills_lower = set(s.lower() for s in skills)
            if not candidate_skills_lower & filter_skills_lower:
                return False

        min_exp = filters.get("min_experience")
        if min_exp is not None and candidate.experience_years < min_exp:
            return False

        max_exp = filters.get("max_experience")
        if max_exp is not None and candidate.experience_years > max_exp:
            return False

        locations = filters.get("locations")
        if locations:
            if not candidate.location:
                return False
            location_lower = candidate.location.lower()
            if not any(loc.lower() in location_lower for loc in locations):
                return False

        min_rating = filters.get("min_rating")
        if min_rating is not None and candidate.rating < min_rating:
            return False

        statuses = filters.get("statuses")
        if statuses and membership.status not in statuses:
            return False

        return True

    def _score_pool_match(
        self,
        pool: TalentPool,
        query_terms: Set[str],
        query_lower: str,
    ) -> Tuple[float, List[str]]:
        """Score how well a pool matches the query at the pool level."""
        score = 0.0
        reasons: List[str] = []

        name_lower = pool.name.lower()
        if query_lower in name_lower:
            score += 10.0
            reasons.append(f"Pool name matches '{query_lower}'")

        for term in query_terms:
            if term in name_lower:
                score += 3.0
                reasons.append(f"Pool name contains '{term}'")

        if pool.description:
            desc_lower = pool.description.lower()
            if query_lower in desc_lower:
                score += 5.0
                reasons.append(f"Pool description matches '{query_lower}'")
            for term in query_terms:
                if term in desc_lower:
                    score += 1.5

        for tag in pool.tags:
            tag_lower = tag.lower()
            if query_lower == tag_lower:
                score += 4.0
                reasons.append(f"Pool tag '{tag}' matches")
            elif any(term in tag_lower for term in query_terms):
                score += 2.0
                reasons.append(f"Pool tag '{tag}' partially matches")

        return score, reasons

    def _score_candidate_match(
        self,
        candidate: Candidate,
        query_terms: Set[str],
        query_lower: str,
    ) -> Tuple[float, List[str]]:
        """Score how well a candidate matches the query."""
        score = 0.0
        reasons: List[str] = []

        name_lower = candidate.full_name.lower()
        if query_lower in name_lower:
            score += 8.0
            reasons.append(f"Candidate name matches '{query_lower}'")
        for term in query_terms:
            if term in name_lower:
                score += 2.5

        email_lower = candidate.email.lower()
        if query_lower in email_lower:
            score += 3.0

        for skill in candidate.skills:
            skill_lower = skill.lower()
            if query_lower == skill_lower:
                score += 6.0
                reasons.append(f"Skill '{skill}' exact match")
            elif any(term in skill_lower for term in query_terms):
                score += 3.0
                reasons.append(f"Skill '{skill}' partial match")

        if candidate.current_title:
            title_lower = candidate.current_title.lower()
            if query_lower in title_lower:
                score += 5.0
                reasons.append(f"Title '{candidate.current_title}' matches")
            for term in query_terms:
                if term in title_lower:
                    score += 2.0

        if candidate.current_company:
            company_lower = candidate.current_company.lower()
            if query_lower in company_lower:
                score += 4.0
                reasons.append(f"Company '{candidate.current_company}' matches")
            for term in query_terms:
                if term in company_lower:
                    score += 1.5

        if candidate.location:
            location_lower = candidate.location.lower()
            if query_lower in location_lower:
                score += 3.0
                reasons.append(f"Location '{candidate.location}' matches")

        for tag in candidate.tags:
            tag_lower = tag.lower()
            if query_lower == tag_lower:
                score += 3.5
                reasons.append(f"Tag '{tag}' matches")
            elif any(term in tag_lower for term in query_terms):
                score += 1.5

        return score, reasons

    def _log_activity(
        self,
        pool_id: str,
        activity_type: PoolActivityType,
        details: Dict[str, Any],
    ) -> None:
        """Log an activity event to a pool's activity log."""
        if pool_id not in self._pools:
            return

        self._pools[pool_id].activity_log.append({
            "type": activity_type.value,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        })


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_manager: Optional[TalentPoolManager] = None


def get_manager() -> TalentPoolManager:
    """Get or create the default TalentPoolManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = TalentPoolManager()
    return _default_manager


def add_to_pool(
    candidate_id: str,
    pool_id: str,
    *,
    added_by: Optional[str] = None,
    status: CandidateStatus = CandidateStatus.NEW,
    custom_fields: Optional[Dict[str, Any]] = None,
) -> PoolMembership:
    """
    Add a candidate to a talent pool.

    Convenience function that uses the default manager instance.

    Args:
        candidate_id: The unique identifier of the candidate to add.
        pool_id: The unique identifier of the target talent pool.
        added_by: Optional identifier of the user adding the candidate.
        status: Initial status of the candidate in the pool.
        custom_fields: Optional custom field values for this membership.

    Returns:
        The created PoolMembership object.

    Raises:
        ValueError: If the candidate_id or pool_id does not exist.
        RuntimeError: If the candidate is already in the pool.
    """
    return get_manager().add_to_pool(
        candidate_id,
        pool_id,
        added_by=added_by,
        status=status,
        custom_fields=custom_fields,
    )


def search_pools(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
) -> List[PoolSearchResult]:
    """
    Search across talent pools using a text query and optional filters.

    Convenience function that uses the default manager instance.

    Args:
        query: The search query string.
        filters: Optional dictionary of filters to narrow results.

    Returns:
        A list of PoolSearchResult objects sorted by match_score descending.
    """
    return get_manager().search_pools(query, filters)
