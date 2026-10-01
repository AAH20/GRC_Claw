"""
GRC_Claw Stakeholder Registry
=============================
Implements the stakeholder identification, classification, and register
management from the GRC_Claw Stakeholder Engagement Specification v2.0.

Covers:
- Stakeholder taxonomy (Internal / External / Regulator)
- Power/Interest matrix classification
- Stakeholder register CRUD operations
- Automated discovery and deduplication
- Data quality checks
- Register analytics and reporting
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class StakeholderCategory(str, Enum):
    INTERNAL = "internal"
    EXTERNAL = "external"
    REGULATOR = "regulator"


class InfluenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InterestLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Priority(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Standard


class EngagementStrategy(str, Enum):
    MANAGE_CLOSELY = "manage_closely"
    ENGAGE_DEEPLY = "engage_deeply"
    KEEP_INFORMED = "keep_informed"
    MONITOR = "monitor"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Data Model
# ---------------------------------------------------------------------------

@dataclass
class Stakeholder:
    """Single stakeholder record matching the register schema (Spec §2.3)."""

    stakeholder_id: str
    name: str
    category: StakeholderCategory
    role: str
    influence: InfluenceLevel
    interest: InterestLevel
    priority: Priority
    engagement_strategy: EngagementStrategy
    primary_contact: str
    communication_channel: str
    engagement_frequency: str
    current_sentiment: Sentiment = Sentiment.UNKNOWN
    key_concerns: list[str] = field(default_factory=list)
    last_engaged: Optional[str] = None
    next_planned: Optional[str] = None
    email: str = ""
    organization: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        # Convert enums to their values
        for key in ("category", "influence", "interest", "priority",
                    "engagement_strategy", "current_sentiment"):
            d[key] = getattr(self, key).value if isinstance(getattr(self, key), Enum) else getattr(self, key)
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Stakeholder:
        """Reconstruct a Stakeholder from a plain dict (e.g. from CSV/JSON)."""
        field_names = {f.name for f in cls.__dataclass_fields__.values()}
        clean = {}
        for k, v in data.items():
            if k not in field_names:
                continue
            # Convert string enums back to Enum members
            if k == "category":
                v = StakeholderCategory(v)
            elif k == "influence":
                v = InfluenceLevel(v)
            elif k == "interest":
                v = InterestLevel(v)
            elif k == "priority":
                v = Priority(v)
            elif k == "engagement_strategy":
                v = EngagementStrategy(v)
            elif k == "current_sentiment":
                v = Sentiment(v)
            elif k == "key_concerns" and isinstance(v, str):
                v = [t.strip() for t in v.split(";") if t.strip()]
            elif k == "tags" and isinstance(v, str):
                v = [t.strip() for t in v.split(";") if t.strip()]
            clean[k] = v
        return cls(**clean)


# ---------------------------------------------------------------------------
# Power / Interest Matrix
# ---------------------------------------------------------------------------

class PowerInterestMatrix:
    """
    Maps (influence, interest) → engagement strategy per Spec §2.2.

    HIGH INFLUENCE  + HIGH INTEREST  → ENGAGE_DEEPLY
    HIGH INFLUENCE  + LOW  INTEREST  → MANAGE_CLOSELY
    LOW  INFLUENCE  + HIGH INTEREST  → KEEP_INFORMED
    LOW  INFLUENCE  + LOW  INTEREST  → MONITOR
    """

    _MAP: dict[tuple[InfluenceLevel, InterestLevel], EngagementStrategy] = {
        (InfluenceLevel.HIGH, InterestLevel.HIGH): EngagementStrategy.ENGAGE_DEEPLY,
        (InfluenceLevel.HIGH, InterestLevel.MEDIUM): EngagementStrategy.ENGAGE_DEEPLY,
        (InfluenceLevel.HIGH, InterestLevel.LOW): EngagementStrategy.MANAGE_CLOSELY,
        (InfluenceLevel.MEDIUM, InterestLevel.HIGH): EngagementStrategy.ENGAGE_DEEPLY,
        (InfluenceLevel.MEDIUM, InterestLevel.MEDIUM): EngagementStrategy.KEEP_INFORMED,
        (InfluenceLevel.MEDIUM, InterestLevel.LOW): EngagementStrategy.KEEP_INFORMED,
        (InfluenceLevel.LOW, InterestLevel.HIGH): EngagementStrategy.KEEP_INFORMED,
        (InfluenceLevel.LOW, InterestLevel.MEDIUM): EngagementStrategy.MONITOR,
        (InfluenceLevel.LOW, InterestLevel.LOW): EngagementStrategy.MONITOR,
    }

    @classmethod
    def classify(cls, influence: InfluenceLevel, interest: InterestLevel) -> EngagementStrategy:
        return cls._MAP.get((influence, interest), EngagementStrategy.KEEP_INFORMED)

    @classmethod
    def quadrant(cls, influence: InfluenceLevel, interest: InterestLevel) -> str:
        if influence == InfluenceLevel.HIGH and interest == InterestLevel.HIGH:
            return "ENGAGE DEEPLY"
        if influence == InfluenceLevel.HIGH and interest != InterestLevel.HIGH:
            return "MANAGE CLOSELY"
        if influence != InfluenceLevel.HIGH and interest == InterestLevel.HIGH:
            return "KEEP INFORMED"
        return "MONITOR"


# ---------------------------------------------------------------------------
# Stakeholder Registry
# ---------------------------------------------------------------------------

class StakeholderRegistry:
    """
    In-memory stakeholder register with CSV/JSON persistence.

    Supports:
    - CRUD operations
    - Fuzzy deduplication on name/org/role
    - Automated classification from discovery signals
    - Data quality scoring
    - Coverage and completeness analytics
    """

    REQUIRED_FIELDS = (
        "stakeholder_id", "name", "category", "role",
        "influence", "interest", "priority",
        "engagement_strategy", "primary_contact",
        "communication_channel", "engagement_frequency",
    )

    def __init__(self, storage_path: str | Path | None = None):
        self._stakeholders: dict[str, Stakeholder] = {}
        self._storage_path = Path(storage_path) if storage_path else None
        if self._storage_path and self._storage_path.exists():
            self.load()

    # ---- CRUD ----

    def add(self, stakeholder: Stakeholder) -> Stakeholder:
        """Add a stakeholder. Raises ValueError on duplicate ID."""
        if stakeholder.stakeholder_id in self._stakeholders:
            raise ValueError(f"Stakeholder {stakeholder.stakeholder_id} already exists")
        self._stakeholders[stakeholder.stakeholder_id] = stakeholder
        return stakeholder

    def get(self, stakeholder_id: str) -> Optional[Stakeholder]:
        return self._stakeholders.get(stakeholder_id)

    def update(self, stakeholder_id: str, **kwargs) -> Stakeholder:
        s = self._stakeholders.get(stakeholder_id)
        if not s:
            raise KeyError(f"Stakeholder {stakeholder_id} not found")
        for key, value in kwargs.items():
            if hasattr(s, key):
                setattr(s, key, value)
        s.updated_at = datetime.utcnow().isoformat()
        return s

    def remove(self, stakeholder_id: str) -> None:
        self._stakeholders.pop(stakeholder_id, None)

    def all(self) -> list[Stakeholder]:
        return list(self._stakeholders.values())

    def find_by_category(self, category: StakeholderCategory) -> list[Stakeholder]:
        return [s for s in self._stakeholders.values() if s.category == category]

    def find_by_priority(self, priority: Priority) -> list[Stakeholder]:
        return [s for s in self._stakeholders.values() if s.priority == priority]

    def find_by_strategy(self, strategy: EngagementStrategy) -> list[Stakeholder]:
        return [s for s in self._stakeholders.values() if s.engagement_strategy == strategy]

    def find_stale(self, days: int = 90) -> list[Stakeholder]:
        """Return stakeholders not engaged within *days*."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        stale = []
        for s in self._stakeholders.values():
            if s.last_engaged:
                try:
                    last = datetime.fromisoformat(s.last_engaged.replace("Z", "+00:00"))
                    if last < cutoff:
                        stale.append(s)
                except (ValueError, AttributeError):
                    continue
            else:
                stale.append(s)  # Never engaged
        return stale

    # ---- Auto-classification ----

    def auto_classify(
        self,
        name: str,
        category: StakeholderCategory,
        role: str,
        influence: InfluenceLevel,
        interest: InterestLevel,
        **kwargs,
    ) -> Stakeholder:
        """
        Create a stakeholder with auto-derived priority and engagement strategy.

        Priority rules (Spec §2.1):
          P1 — Critical: High influence + High interest, or Regulator category
          P2 — High:     Medium influence + High interest, or High influence + Medium interest
          P3 — Standard: Everything else
        """
        strategy = PowerInterestMatrix.classify(influence, interest)

        if category == StakeholderCategory.REGULATOR:
            priority = Priority.P1
        elif influence == InfluenceLevel.HIGH and interest == InterestLevel.HIGH:
            priority = Priority.P1
        elif (influence == InfluenceLevel.HIGH and interest == InfluenceLevel.MEDIUM) or \
             (influence == InfluenceLevel.MEDIUM and interest == InterestLevel.HIGH):
            priority = Priority.P2
        else:
            priority = Priority.P3

        stk_id = self._next_id()
        return Stakeholder(
            stakeholder_id=stk_id,
            name=name,
            category=category,
            role=role,
            influence=influence,
            interest=interest,
            priority=priority,
            engagement_strategy=strategy,
            **kwargs,
        )

    def _next_id(self) -> str:
        """Generate next sequential stakeholder ID (STK-NNN)."""
        nums = []
        for sid in self._stakeholders:
            m = re.match(r"STK-(\d+)", sid)
            if m:
                nums.append(int(m.group(1)))
        next_num = max(nums, default=0) + 1
        return f"STK-{next_num:03d}"

    # ---- Deduplication ----

    def find_duplicate(self, name: str, organization: str = "", role: str = "",
                       threshold: float = 0.80) -> Optional[Stakeholder]:
        """
        Fuzzy-match a potential stakeholder against existing records.
        Returns the best match above *threshold* or None.
        """
        best_match: Optional[Stakeholder] = None
        best_score = 0.0

        for s in self._stakeholders.values():
            name_sim = SequenceMatcher(None, name.lower(), s.name.lower()).ratio()
            org_sim = SequenceMatcher(None, organization.lower(), s.organization.lower()).ratio() if organization else 0.0
            role_sim = SequenceMatcher(None, role.lower(), s.role.lower()).ratio() if role else 0.0

            # Weighted composite
            score = (name_sim * 0.5) + (org_sim * 0.3) + (role_sim * 0.2)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = s

        return best_match

    # ---- Data Quality ----

    def quality_check(self) -> dict:
        """
        Run data quality checks per Spec §10.4.2.

        Returns a report with completeness, accuracy, currency,
        consistency, uniqueness, and validity scores.
        """
        total = len(self._stakeholders)
        if total == 0:
            return {"total": 0, "completeness": 0, "accuracy": 0,
                    "currency": 0, "consistency": 0, "uniqueness": 0,
                    "validity": 0, "issues": []}

        issues: list[dict] = []
        complete = 0
        consistent = 0
        valid = 0
        unique_names: dict[str, int] = {}

        for s in self._stakeholders.values():
            # Completeness: all required fields populated
            missing = [f for f in self.REQUIRED_FIELDS
                       if not getattr(s, f, None)]
            if not missing:
                complete += 1
            else:
                issues.append({"stakeholder_id": s.stakeholder_id,
                               "check": "completeness",
                               "detail": f"Missing fields: {missing}"})

            # Consistency: strategy matches matrix
            expected = PowerInterestMatrix.classify(s.influence, s.interest)
            if s.engagement_strategy == expected:
                consistent += 1
            else:
                issues.append({"stakeholder_id": s.stakeholder_id,
                               "check": "consistency",
                               "detail": f"Strategy {s.engagement_strategy.value} "
                                         f"!= expected {expected.value}"})

            # Validity: email format
            if s.email and re.match(r"[^@]+@[^@]+\.[^@]+", s.email):
                valid += 1
            elif s.email:
                issues.append({"stakeholder_id": s.stakeholder_id,
                               "check": "validity",
                               "detail": f"Invalid email: {s.email}"})

            # Uniqueness
            key = f"{s.name.lower()}|{s.organization.lower()}"
            unique_names[key] = unique_names.get(key, 0) + 1

        duplicates = {k: v for k, v in unique_names.items() if v > 1}
        for dup_key in duplicates:
            issues.append({"stakeholder_id": "N/A",
                           "check": "uniqueness",
                           "detail": f"Duplicate: {dup_key}"})

        # Currency: engaged within 90 days
        stale = self.find_stale(90)
        currency = total - len(stale)

        return {
            "total": total,
            "completeness": round(complete / total * 100, 1),
            "accuracy": 100.0,  # Requires external verification
            "currency": round(currency / total * 100, 1),
            "consistency": round(consistent / total * 100, 1),
            "uniqueness": round((total - len(duplicates)) / total * 100, 1),
            "validity": round(valid / total * 100, 1),
            "issues": issues,
        }

    # ---- Analytics ----

    def coverage_report(self) -> dict:
        """Coverage analytics per Spec §7.4.2."""
        total = len(self._stakeholders)
        if total == 0:
            return {"total": 0}

        by_category = {}
        for cat in StakeholderCategory:
            by_category[cat.value] = len(self.find_by_category(cat))

        by_priority = {}
        for pri in Priority:
            by_priority[pri.value] = len(self.find_by_priority(pri))

        by_strategy = {}
        for strat in EngagementStrategy:
            by_strategy[strat.value] = len(self.find_by_strategy(strat))

        by_sentiment = {}
        for sent in Sentiment:
            by_sentiment[sent.value] = len(
                [s for s in self._stakeholders.values() if s.current_sentiment == sent]
            )

        return {
            "total": total,
            "by_category": by_category,
            "by_priority": by_priority,
            "by_strategy": by_strategy,
            "by_sentiment": by_sentiment,
            "stale_count": len(self.find_stale(90)),
        }

    # ---- Persistence ----

    def save(self, path: str | Path | None = None) -> None:
        """Persist register to CSV."""
        target = Path(path) if path else self._storage_path
        if not target:
            raise ValueError("No storage path specified")
        target.parent.mkdir(parents=True, exist_ok=True)

        if not self._stakeholders:
            target.write_text("")
            return

        # Use first record's keys as fieldnames
        sample = next(iter(self._stakeholders.values())).to_dict()
        fieldnames = list(sample.keys())

        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in self._stakeholders.values():
                row = s.to_dict()
                # Serialize lists as semicolon-delimited
                for k in ("key_concerns", "tags"):
                    if isinstance(row[k], list):
                        row[k] = ";".join(row[k])
                writer.writerow(row)

    def load(self, path: str | Path | None = None) -> None:
        """Load register from CSV."""
        target = Path(path) if path else self._storage_path
        if not target or not target.exists():
            return

        self._stakeholders.clear()
        with open(target, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s = Stakeholder.from_dict(row)
                self._stakeholders[s.stakeholder_id] = s

    def export_json(self, path: str | Path) -> None:
        """Export register as JSON."""
        data = [s.to_dict() for s in self._stakeholders.values()]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def __len__(self) -> int:
        return len(self._stakeholders)


# ---------------------------------------------------------------------------
# Demo / Self-test
# ---------------------------------------------------------------------------

def _demo():
    """Demonstrate registry functionality."""
    registry = StakeholderRegistry()

    # Add stakeholders from the spec taxonomy
    stakeholders_data = [
        {
            "name": "Executive Sponsors",
            "category": StakeholderCategory.INTERNAL,
            "role": "C-suite, VP Engineering, VP Product",
            "influence": InfluenceLevel.HIGH,
            "interest": InterestLevel.HIGH,
            "primary_contact": "exec-sponsor@grc-claw.internal",
            "communication_channel": "Executive dashboard; 1:1 briefings",
            "engagement_frequency": "Monthly + real-time",
            "key_concerns": ["Strategic alignment", "Risk posture", "ROI"],
        },
        {
            "name": "Governance Team",
            "category": StakeholderCategory.INTERNAL,
            "role": "AI governance committee, AIMS manager, risk owners",
            "influence": InfluenceLevel.HIGH,
            "interest": InterestLevel.HIGH,
            "primary_contact": "governance@grc-claw.internal",
            "communication_channel": "Steering committee; working groups",
            "engagement_frequency": "Weekly + monthly",
            "key_concerns": ["Policy compliance", "Control effectiveness", "Maturity"],
        },
        {
            "name": "Engineering Team",
            "category": StakeholderCategory.INTERNAL,
            "role": "Core developers, platform architects, SREs",
            "influence": InfluenceLevel.HIGH,
            "interest": InterestLevel.HIGH,
            "primary_contact": "engineering@grc-claw.internal",
            "communication_channel": "GitHub; Slack",
            "engagement_frequency": "Continuous",
            "key_concerns": ["Technical quality", "Architecture", "Delivery velocity"],
        },
        {
            "name": "EU AI Act Regulators",
            "category": StakeholderCategory.REGULATOR,
            "role": "European Commission, national market surveillance authorities",
            "influence": InfluenceLevel.HIGH,
            "interest": InterestLevel.MEDIUM,
            "primary_contact": "regulatory@grc-claw.internal",
            "communication_channel": "Formal letters; regulatory portals",
            "engagement_frequency": "As needed",
            "key_concerns": ["Compliance", "Transparency", "Risk management"],
        },
        {
            "name": "Open-Source Community",
            "category": StakeholderCategory.EXTERNAL,
            "role": "Contributors, maintainers, users on GitHub",
            "influence": InfluenceLevel.MEDIUM,
            "interest": InterestLevel.HIGH,
            "primary_contact": "community@grc-claw.dev",
            "communication_channel": "GitHub; Discord; mailing list",
            "engagement_frequency": "Continuous",
            "key_concerns": ["Code quality", "Documentation", "Onboarding"],
        },
        {
            "name": "Standards Bodies",
            "category": StakeholderCategory.EXTERNAL,
            "role": "ISO/IEC JTC 1/SC 42, NIST, IEEE, CMMI Institute",
            "influence": InfluenceLevel.HIGH,
            "interest": InterestLevel.MEDIUM,
            "primary_contact": "standards@grc-claw.dev",
            "communication_channel": "Direct email; working groups",
            "engagement_frequency": "Quarterly + as needed",
            "key_concerns": ["Standards alignment", "Contribution", "Compliance"],
        },
        {
            "name": "Media & Analysts",
            "category": StakeholderCategory.EXTERNAL,
            "role": "Tech press, Gartner, Forrester, 451 Research",
            "influence": InfluenceLevel.LOW,
            "interest": InterestLevel.LOW,
            "primary_contact": "pr@grc-claw.dev",
            "communication_channel": "Press releases; briefings",
            "engagement_frequency": "Per milestone",
            "key_concerns": ["Market positioning", "Announcements"],
        },
    ]

    for data in stakeholders_data:
        s = registry.auto_classify(**data)
        registry.add(s)
        print(f"  Added: {s.stakeholder_id} | {s.name} | "
              f"{s.priority.value} | {s.engagement_strategy.value}")

    print(f"\nTotal stakeholders: {len(registry)}")

    # Coverage report
    print("\n--- Coverage Report ---")
    report = registry.coverage_report()
    for key, val in report.items():
        print(f"  {key}: {val}")

    # Quality check
    print("\n--- Quality Check ---")
    quality = registry.quality_check()
    for key, val in quality.items():
        if key != "issues":
            print(f"  {key}: {val}")
    if quality["issues"]:
        print(f"  Issues found: {len(quality['issues'])}")
        for issue in quality["issues"][:5]:
            print(f"    - {issue['stakeholder_id']}: {issue['check']} — {issue['detail']}")

    # Deduplication test
    print("\n--- Deduplication Test ---")
    dup = registry.find_duplicate("Governance Team", role="AI governance committee")
    if dup:
        print(f"  Duplicate found: {dup.stakeholder_id} ({dup.name})")
    else:
        print("  No duplicate found")

    # Persistence test
    print("\n--- Persistence Test ---")
    registry.save("/tmp/grc-claw-stakeholder-register.csv")
    print("  Saved to /tmp/grc-claw-stakeholder-register.csv")

    registry2 = StakeholderRegistry("/tmp/grc-claw-stakeholder-register.csv")
    print(f"  Loaded {len(registry2)} stakeholders from CSV")

    # Export JSON
    registry.export_json("/tmp/grc-claw-stakeholder-register.json")
    print("  Exported to /tmp/grc-claw-stakeholder-register.json")

    print("\n✓ Stakeholder Registry demo complete")


if __name__ == "__main__":
    _demo()
