# Database Seeders

This directory contains factory_boy factories, seeder scripts, and pytest fixtures for generating realistic test data for the gated-communities platform.

## Files

| File | Purpose |
|------|---------|
| `factories.py` | factory_boy factories for all Pydantic models across all 10 services |
| `seeders.py` | Seeder functions that use factories to generate batches of test data |
| `conftest.py` | Pytest fixtures wrapping factories and seeders for test suites |
| `README.md` | This file |

## Quick Start

### Using Factories Directly

```python
from database.seeders.factories import TierFactory, EscalationFactory

# Create a single instance
tier = TierFactory()
print(tier.name)  # "Tier 1"

# Override fields
tier = TierFactory(level="platinum", monthly_fee=99.99)

# Create a batch
tiers = TierFactory.create_batch(10)
```

### Using Seeders

```python
from database.seeders.seeders import seed_tiers, seed_escalations, seed_all

# Seed specific entities
tiers = seed_tiers(count=5)
escalations = seed_escalations(count=10)

# Seed everything
all_data = seed_all()
print(f"Seeded {sum(len(v) for v in all_data.values())} records")
```

### Using Pytest Fixtures

```python
# conftest.py
from database.seeders.conftest import *  # noqa: F401,F403

# test_something.py
def test_tier_creation(tier_factory):
    tier = tier_factory()
    assert tier.name
    assert tier.level in ["bronze", "silver", "gold", "platinum", "diamond"]

def test_escalation_workflow(escalation_factory, resolution_factory):
    escalation = escalation_factory()
    resolution = resolution_factory(escalation_id=escalation.id)
    assert resolution.escalation_id == escalation.id
```

## Services Covered

| Service | Models | Factory Count |
|---------|--------|---------------|
| Tier Management | Tier, TierEvaluation, UpgradeRequest, AccessPolicy, Benefit, TierAnalytics | 6 |
| Community Governance | Policy, Rule, Dispute, GovernanceAction, Analytics | 8 |
| Escalation Workflow | Escalation, Resolution, SLA, Priority, Analysis | 8 |
| Access Control | Permission, Role, AccessRequest, AccessResult, AccessAudit | 6 |
| Reputation System | ReputationScore, Badge, TrustTier, ReputationHistory | 5 |
| Compliance Monitor | Policy, Violation, AuditReport, ComplianceScore, RemediationAction | 6 |
| Member Verification | IdentityData, DocumentData, VerificationRequest, VerificationResult, TrustScore, FraudReport | 8 |
| Moderation Queue | ModerationItem, Queue, PriorityScore, ReviewDecision, Escalation | 6 |
| Moderation Analytics | ModerationAnalytics, Trend, ModeratorPerformance, PolicyEffectiveness | 5 |
| Community Health Scorer | EngagementMetrics, ToxicityReport, GrowthAnalysis, ChurnPrediction, HealthScore | 6 |

**Total: 64 factories**

## Architecture

```
database/seeders/
├── factories.py    # factory_boy PydanticModelFactory subclasses
├── seeders.py      # High-level seeder functions
├── conftest.py     # Pytest fixtures (factory + seeder wrappers)
└── README.md       # This file
```

### Factory Pattern

Each factory uses:
- `factory.Faker` for realistic fake data (names, emails, sentences, etc.)
- `factory.fuzzy.FuzzyChoice` for enum fields
- `factory.fuzzy.FuzzyFloat/FuzzyInteger` for numeric ranges
- `factory.LazyFunction` for dynamic defaults (UUIDs, timestamps)
- `factory.Sequence` for unique names
- `factory.SubFactory` for nested model relationships

### Model Wiring

Factories use a two-phase initialization pattern:
1. Factory classes are defined with `model = Any` placeholder
2. `_wire_models()` is called at import time to assign real Pydantic model classes

This avoids circular imports while keeping the factory definitions clean and readable.

## Configuration

### Customizing Seed Counts

```python
from database.seeders.seeders import seed_all

# Override default counts
data = seed_all(
    tiers=10,
    escalations=20,
    moderation_items=100,
)
```

### Persisting to Database

The seeders return Pydantic model instances. To persist them:

```python
from database.seeders.seeders import seed_tiers
from sqlalchemy.orm import Session

def seed_database(db: Session):
    tiers = seed_tiers(count=5)
    for tier in tiers:
        db_tier = TierModel(**tier.model_dump())
        db.add(db_tier)
    db.commit()
```

## Running Seeders

```bash
# Run all seeders (prints summary)
python -m database.seeders.seeders

# Run specific seeder
python -c "from database.seeders.seeders import seed_tiers; print(seed_tiers(3))"
```

## Testing

```bash
# Run tests that use the fixtures
pytest src/gated_communities/tests/ -v

# Run with coverage
pytest --cov=src/gated_communities --cov-report=term-missing
```
