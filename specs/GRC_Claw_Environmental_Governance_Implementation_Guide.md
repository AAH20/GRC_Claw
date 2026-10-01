# GRC_Claw Environmental Governance Implementation Guide

**Document ID:** GRC-CLW-ENV-IMP-001  
**Version:** 1.0  
**Classification:** Internal — Engineering Implementation  
**Effective Date:** 2026-10-01  
**Owner:** GRC_Claw Sustainability Engineering  
**References:** GRC-CLW-ENV-001 v2.0, GRC-CLW-DATA-001 v1.0

---

## Table of Contents

1. [Overview & Architecture](#1-overview--architecture)
2. [Carbon Tracking (Python)](#2-carbon-tracking-python)
3. [Energy Monitoring (Python)](#3-energy-monitoring-python)
4. [Sustainability Reporting (Python)](#4-sustainability-reporting-python)
5. [Environmental Impact Assessment (Python)](#5-environmental-impact-assessment-python)
6. [Carbon Optimization (Python)](#6-carbon-optimization-python)
7. [Carbon Offset Management (Python)](#7-carbon-offset-management-python)
8. [Environmental Compliance (Python)](#8-environmental-compliance-python)
9. [Quick Start & Deployment](#9-quick-start--deployment)

---

## 1. Overview & Architecture

This guide provides production-ready Python implementations for each pillar of GRC_Claw's environmental governance framework. All code follows the GHG Protocol, ISO 14040/14044, ISO 14064-1, and ISO/IEC 42001 standards referenced in the specification.

### 1.1 Core Dependencies

```bash
pip install pydantic pandas numpy python-dateutil pyyaml requests
```

### 1.2 Shared Data Models

```python
# models.py — Shared data models for all environmental governance modules
from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class EmissionScope(str, Enum):
    SCOPE_1 = "scope_1"
    SCOPE_2 = "scope_2"
    SCOPE_3 = "scope_3"


class AccountingMethod(str, Enum):
    LOCATION_BASED = "location_based"
    MARKET_BASED = "market_based"


class WorkloadType(str, Enum):
    TRAINING = "training"
    FINE_TUNING = "fine_tuning"
    INFERENCE = "inference"
    EMBEDDING = "embedding"
    AGENT = "agent"
    RAG = "rag"
    DATA_PROCESSING = "data_processing"


class ImpactRating(str, Enum):
    A_EXCELLENT = "A"       # 0–20
    B_GOOD = "B"            # 21–40
    C_AVERAGE = "C"         # 41–60
    D_POOR = "D"            # 61–80
    F_CRITICAL = "F"        # 81–100


class EmissionFactor(BaseModel):
    factor_id: str
    name: str
    value: Decimal
    unit: str                          # e.g., "kg CO2e/kWh"
    region: str
    source: str                        # e.g., "IEA", "EPA", "DEFRA"
    effective_date: date
    version: str = "1.0"


class EnergyReading(BaseModel):
    reading_id: str
    timestamp: datetime
    facility_id: str
    workload_id: Optional[str] = None
    energy_kwh: Decimal
    it_equipment_kwh: Decimal
    pue: Optional[Decimal] = None
    wue: Optional[Decimal] = None
    source: str                        # "dcgm", "rapl", "smart_meter", "cloud_api"


class CarbonEmissionRecord(BaseModel):
    record_id: str
    timestamp: datetime
    scope: EmissionScope
    category: Optional[str] = None     # Scope 3 category (1-15)
    facility_id: str
    workload_id: Optional[str] = None
    activity_data: Decimal
    activity_unit: str
    emission_factor: Decimal
    gwp: Optional[Decimal] = None
    emissions_kg_co2e: Decimal
    method: Optional[AccountingMethod] = None
    verified: bool = False
    evidence_hash: Optional[str] = None


class CarbonOffset(BaseModel):
    offset_id: str
    project_name: str
    registry: str                      # "Verra", "Gold Standard", "Puro.earth"
    standard: str                      # "VCS", "GS VER", "CORC"
    category: str                      # "avoidance", "reduction", "removal_nature", "removal_tech"
    vintage: int
    credits_purchased: Decimal
    credits_retired: Decimal = Decimal("0")
    price_per_credit: Decimal
    region: str
    quality_score: Optional[int] = None  # 0-100
    status: str = "active"             # "active", "retired", "cancelled"
    retirement_date: Optional[datetime] = None
    evidence_hash: Optional[str] = None


class ComplianceRule(BaseModel):
    rule_id: str
    name: str
    description: str
    condition: str
    action: str                        # "alert", "block", "quarantine"
    severity: str                      # "low", "medium", "high", "critical"
    notify: list[str]
    deadline: Optional[date] = None
    enabled: bool = True


class SustainabilityScore(BaseModel):
    entity_id: str
    entity_type: str                   # "workload", "model", "service", "organization"
    score: Decimal                     # 0-100
    grade: str                         # "A+", "A", "B+", "B", "C", "D", "F"
    components: dict[str, Decimal]
    timestamp: datetime
    algorithm_version: str = "1.0"
```

---

## 2. Carbon Tracking (Python)

Implements GHG Protocol Scope 1, 2, and 3 accounting with an immutable carbon ledger.

```python
# carbon_tracking.py
"""
GRC_Claw Carbon Tracking Module
Implements GHG Protocol Corporate Standard and Scope 3 Standard.
All emission records are hash-chained for audit integrity.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Optional

from models import (
    AccountingMethod,
    CarbonEmissionRecord,
    EmissionFactor,
    EmissionScope,
)


class EmissionFactorRegistry:
    """Living emission factor registry — updated at least annually per spec §5.6."""

    def __init__(self):
        self._factors: dict[str, EmissionFactor] = {}
        self._load_defaults()

    def _load_defaults(self):
        """Load default emission factors from spec Appendix A."""
        defaults = [
            EmissionFactor(
                factor_id="grid-us-2024", name="Grid Electricity US Average",
                value=Decimal("0.386"), unit="kg CO2e/kWh",
                region="US", source="EPA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="grid-eu-2024", name="Grid Electricity EU Average",
                value=Decimal("0.230"), unit="kg CO2e/kWh",
                region="EU-27", source="IEA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="grid-uk-2024", name="Grid Electricity UK",
                value=Decimal("0.212"), unit="kg CO2e/kWh",
                region="UK", source="DEFRA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="grid-ca-2024", name="Grid Electricity California",
                value=Decimal("0.193"), unit="kg CO2e/kWh",
                region="California", source="EPA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="grid-tx-2024", name="Grid Electricity Texas",
                value=Decimal("0.413"), unit="kg CO2e/kWh",
                region="Texas", source="EPA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="grid-fr-2024", name="Grid Electricity France",
                value=Decimal("0.052"), unit="kg CO2e/kWh",
                region="France", source="IEA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="natural-gas-2024", name="Natural Gas Combustion",
                value=Decimal("0.185"), unit="kg CO2e/kWh",
                region="Global", source="IPCC", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="diesel-2024", name="Diesel Combustion",
                value=Decimal("2.68"), unit="kg CO2e/liter",
                region="Global", source="DEFRA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="gasoline-2024", name="Gasoline Combustion",
                value=Decimal("2.31"), unit="kg CO2e/liter",
                region="Global", source="DEFRA", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="hfc-134a-2024", name="HFC-134a Refrigerant",
                value=Decimal("1430"), unit="kg CO2e/kg",
                region="Global", source="IPCC AR6", effective_date=date(2024, 1, 1),
            ),
            EmissionFactor(
                factor_id="hfc-410a-2024", name="HFC-410A Refrigerant",
                value=Decimal("2088"), unit="kg CO2e/kg",
                region="Global", source="IPCC AR6", effective_date=date(2024, 1, 1),
            ),
        ]
        for f in defaults:
            self._factors[f.factor_id] = f

    def get_factor(self, factor_id: str) -> EmissionFactor:
        if factor_id not in self._factors:
            raise KeyError(f"Emission factor '{factor_id}' not found in registry")
        return self._factors[factor_id]

    def add_or_update(self, factor: EmissionFactor) -> None:
        self._factors[factor.factor_id] = factor

    def list_factors(self, region: Optional[str] = None) -> list[EmissionFactor]:
        factors = list(self._factors.values())
        if region:
            factors = [f for f in factors if f.region == region]
        return factors


class CarbonLedger:
    """
    Immutable, hash-chained carbon emission ledger.
    Each record includes the hash of the previous record for tamper evidence.
    """

    def __init__(self, storage_path: str = "carbon_ledger.jsonl"):
        self.storage_path = Path(storage_path)
        self._records: list[CarbonEmissionRecord] = []
        self._last_hash: str = "0" * 64  # Genesis hash
        self._load()

    def _load(self):
        if self.storage_path.exists():
            with open(self.storage_path, "r") as f:
                for line in f:
                    data = json.loads(line.strip())
                    self._records.append(CarbonEmissionRecord(**data))
            if self._records:
                self._last_hash = self._records[-1].evidence_hash or "0" * 64

    def _compute_hash(self, record: CarbonEmissionRecord) -> str:
        """Compute SHA-256 hash of record content + previous hash (hash chain)."""
        content = {
            "record_id": record.record_id,
            "timestamp": record.timestamp.isoformat(),
            "scope": record.scope.value,
            "category": record.category,
            "facility_id": record.facility_id,
            "workload_id": record.workload_id,
            "activity_data": str(record.activity_data),
            "activity_unit": record.activity_unit,
            "emission_factor": str(record.emission_factor),
            "gwp": str(record.gwp) if record.gwp else None,
            "emissions_kg_co2e": str(record.emissions_kg_co2e),
            "method": record.method.value if record.method else None,
            "verified": record.verified,
            "previous_hash": self._last_hash,
        }
        return hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

    def append(self, record: CarbonEmissionRecord) -> CarbonEmissionRecord:
        """Append a record to the ledger with hash chaining."""
        record.evidence_hash = self._compute_hash(record)
        self._records.append(record)
        self._last_hash = record.evidence_hash
        self._persist(record)
        return record

    def _persist(self, record: CarbonEmissionRecord):
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(record.model_dump(), default=str) + "\n")

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verify the integrity of the entire hash chain."""
        errors = []
        prev_hash = "0" * 64
        for i, record in enumerate(self._records):
            content = {
                "record_id": record.record_id,
                "timestamp": record.timestamp.isoformat(),
                "scope": record.scope.value,
                "category": record.category,
                "facility_id": record.facility_id,
                "workload_id": record.workload_id,
                "activity_data": str(record.activity_data),
                "activity_unit": record.activity_unit,
                "emission_factor": str(record.emission_factor),
                "gwp": str(record.gwp) if record.gwp else None,
                "emissions_kg_co2e": str(record.emissions_kg_co2e),
                "method": record.method.value if record.method else None,
                "verified": record.verified,
                "previous_hash": prev_hash,
            }
            expected = hashlib.sha256(
                json.dumps(content, sort_keys=True).encode()
            ).hexdigest()
            if expected != record.evidence_hash:
                errors.append(f"Record {i} ({record.record_id}): hash mismatch")
            prev_hash = record.evidence_hash
        return len(errors) == 0, errors

    def get_records(
        self,
        scope: Optional[EmissionScope] = None,
        facility_id: Optional[str] = None,
        workload_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[CarbonEmissionRecord]:
        results = self._records
        if scope:
            results = [r for r in results if r.scope == scope]
        if facility_id:
            results = [r for r in results if r.facility_id == facility_id]
        if workload_id:
            results = [r for r in results if r.workload_id == workload_id]
        if start:
            results = [r for r in results if r.timestamp >= start]
        if end:
            results = [r for r in results if r.timestamp <= end]
        return results

    def total_emissions(
        self,
        scope: Optional[EmissionScope] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Decimal:
        records = self.get_records(scope=scope, start=start, end=end)
        return sum((r.emissions_kg_co2e for r in records), Decimal("0"))


class CarbonAccountingEngine:
    """
    Main carbon accounting engine implementing GHG Protocol methodologies
    for Scope 1, Scope 2 (location-based and market-based), and Scope 3.
    """

    def __init__(self):
        self.factor_registry = EmissionFactorRegistry()
        self.ledger = CarbonLedger()

    # ── Scope 1: Direct Emissions ──────────────────────────────────────

    def calculate_scope1(
        self,
        facility_id: str,
        source: str,                    # "generator", "heating", "vehicle", "refrigerant"
        activity_data: Decimal,
        activity_unit: str,             # "liters", "kWh", "kg"
        emission_factor_id: str,
        workload_id: Optional[str] = None,
        gwp: Optional[Decimal] = None,
    ) -> CarbonEmissionRecord:
        """
        Scope 1 = Activity Data × Emission Factor × GWP
        
        For refrigerants, GWP is required. For fuel combustion, GWP is 1.
        """
        factor = self.factor_registry.get_factor(emission_factor_id)
        gwp_val = gwp if gwp is not None else Decimal("1")
        emissions = (activity_data * factor.value * gwp_val).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        record = CarbonEmissionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            scope=EmissionScope.SCOPE_1,
            category=source,
            facility_id=facility_id,
            workload_id=workload_id,
            activity_data=activity_data,
            activity_unit=activity_unit,
            emission_factor=factor.value,
            gwp=gwp_val,
            emissions_kg_co2e=emissions,
        )
        return self.ledger.append(record)

    # ── Scope 2: Indirect Emissions from Purchased Energy ─────────────

    def calculate_scope2_location_based(
        self,
        facility_id: str,
        electricity_kwh: Decimal,
        grid_factor_id: str,
        workload_id: Optional[str] = None,
    ) -> CarbonEmissionRecord:
        """
        Scope 2 (location-based) = Electricity Consumed × Grid Average EF
        """
        factor = self.factor_registry.get_factor(grid_factor_id)
        emissions = (electricity_kwh * factor.value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        record = CarbonEmissionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            scope=EmissionScope.SCOPE_2,
            category="purchased_electricity",
            facility_id=facility_id,
            workload_id=workload_id,
            activity_data=electricity_kwh,
            activity_unit="kWh",
            emission_factor=factor.value,
            emissions_kg_co2e=emissions,
            method=AccountingMethod.LOCATION_BASED,
        )
        return self.ledger.append(record)

    def calculate_scope2_market_based(
        self,
        facility_id: str,
        total_electricity_kwh: Decimal,
        renewable_kwh: Decimal,
        residual_mix_factor_id: str,
        workload_id: Optional[str] = None,
    ) -> CarbonEmissionRecord:
        """
        Scope 2 (market-based) = Unspecified Electricity × Residual Mix Factor
        Renewable portion (RECs, PPAs, green tariffs) has zero emissions.
        """
        factor = self.factor_registry.get_factor(residual_mix_factor_id)
        unspecified_kwh = total_electricity_kwh - renewable_kwh
        if unspecified_kwh < 0:
            unspecified_kwh = Decimal("0")

        emissions = (unspecified_kwh * factor.value).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        record = CarbonEmissionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            scope=EmissionScope.SCOPE_2,
            category="purchased_electricity_market",
            facility_id=facility_id,
            workload_id=workload_id,
            activity_data=unspecified_kwh,
            activity_unit="kWh",
            emission_factor=factor.value,
            emissions_kg_co2e=emissions,
            method=AccountingMethod.MARKET_BASED,
        )
        return self.ledger.append(record)

    # ── Scope 3: Value Chain Emissions ────────────────────────────────

    def calculate_scope3(
        self,
        category: int,                  # 1-15
        facility_id: str,
        activity_data: Decimal,
        activity_unit: str,
        emission_factor: Decimal,
        calculation_method: str,        # "supplier_specific", "hybrid", "spend_based", "average_data"
        workload_id: Optional[str] = None,
    ) -> CarbonEmissionRecord:
        """
        Scope 3 emissions across all 15 categories.
        """
        if not 1 <= category <= 15:
            raise ValueError("Scope 3 category must be 1-15")

        emissions = (activity_data * emission_factor).quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

        record = CarbonEmissionRecord(
            record_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            scope=EmissionScope.SCOPE_3,
            category=f"category_{category}",
            facility_id=facility_id,
            workload_id=workload_id,
            activity_data=activity_data,
            activity_unit=activity_unit,
            emission_factor=emission_factor,
            emissions_kg_co2e=emissions,
        )
        return self.ledger.append(record)

    # ── Reporting & Aggregation ────────────────────────────────────────

    def get_scope_summary(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> dict:
        """Get emissions summary by scope."""
        return {
            "scope_1_kg_co2e": self.ledger.total_emissions(
                scope=EmissionScope.SCOPE_1, start=start, end=end
            ),
            "scope_2_kg_co2e": self.ledger.total_emissions(
                scope=EmissionScope.SCOPE_2, start=start, end=end
            ),
            "scope_3_kg_co2e": self.ledger.total_emissions(
                scope=EmissionScope.SCOPE_3, start=start, end=end
            ),
            "total_kg_co2e": self.ledger.total_emissions(start=start, end=end),
        }

    def get_scope3_by_category(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> dict[int, Decimal]:
        """Get Scope 3 emissions broken down by category."""
        records = self.ledger.get_records(
            scope=EmissionScope.SCOPE_3, start=start, end=end
        )
        by_category: dict[int, Decimal] = defaultdict(Decimal)
        for r in records:
            if r.category and r.category.startswith("category_"):
                cat_num = int(r.category.split("_")[1])
                by_category[cat_num] += r.emissions_kg_co2e
        return dict(by_category)

    def verify_ledger_integrity(self) -> dict:
        """Verify the carbon ledger hash chain."""
        valid, errors = self.ledger.verify_chain()
        return {
            "valid": valid,
            "errors": errors,
            "total_records": len(self.ledger._records),
        }


# ── Example Usage ─────────────────────────────────────────────────────

def demo_carbon_tracking():
    engine = CarbonAccountingEngine()

    # Scope 1: Diesel generator at on-prem facility
    engine.calculate_scope1(
        facility_id="dc-us-east-1",
        source="generator",
        activity_data=Decimal("500"),       # 500 liters
        activity_unit="liters",
        emission_factor_id="diesel-2024",
    )

    # Scope 1: Refrigerant leakage
    engine.calculate_scope1(
        facility_id="dc-us-east-1",
        source="refrigerant",
        activity_data=Decimal("2.5"),       # 2.5 kg leaked
        activity_unit="kg",
        emission_factor_id="hfc-134a-2024",
        gwp=Decimal("1430"),
    )

    # Scope 2: Location-based
    engine.calculate_scope2_location_based(
        facility_id="dc-us-east-1",
        electricity_kwh=Decimal("10000"),
        grid_factor_id="grid-us-2024",
    )

    # Scope 2: Market-based (60% renewable)
    engine.calculate_scope2_market_based(
        facility_id="dc-us-east-1",
        total_electricity_kwh=Decimal("10000"),
        renewable_kwh=Decimal("6000"),
        residual_mix_factor_id="grid-us-2024",
    )

    # Scope 3: Category 1 — Purchased hardware
    engine.calculate_scope3(
        category=1,
        facility_id="dc-us-east-1",
        activity_data=Decimal("50"),        # 50 GPUs
        activity_unit="units",
        emission_factor=Decimal("150"),     # kg CO2e per H100
        calculation_method="supplier_specific",
    )

    # Scope 3: Category 11 — Use of sold products
    engine.calculate_scope3(
        category=11,
        facility_id="dc-us-east-1",
        activity_data=Decimal("50000"),     # 50K inference requests
        activity_unit="requests",
        emission_factor=Decimal("0.003"),   # kg CO2e per request
        calculation_method="average_data",
    )

    # Print summary
    summary = engine.get_scope_summary()
    print("=== Carbon Emissions Summary ===")
    for key, value in summary.items():
        print(f"  {key}: {value} kg CO2e")

    # Verify ledger integrity
    integrity = engine.verify_ledger_integrity()
    print(f"\nLedger integrity: {'VALID' if integrity['valid'] else 'INVALID'}")
    print(f"Total records: {integrity['total_records']}")

    return engine


if __name__ == "__main__":
    demo_carbon_tracking()
```

---

## 3. Energy Monitoring (Python)

Implements real-time energy monitoring across compute, cooling, networking, and facility layers.

```python
# energy_monitoring.py
"""
GRC_Claw Energy Monitoring Module
Collects, normalizes, and analyzes energy consumption across all AI workloads
and supporting infrastructure. Implements PUE, WUE, CUE, and per-workload
energy metrics per spec §6.
"""
from __future__ import annotations

import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from models import EnergyReading, WorkloadType


class EnergyMetricsCalculator:
    """Calculates energy efficiency metrics per spec §6.2."""

    @staticmethod
    def pue(total_facility_kwh: Decimal, it_equipment_kwh: Decimal) -> Decimal:
        """Power Usage Effectiveness = Total Facility Energy / IT Equipment Energy."""
        if it_equipment_kwh == 0:
            return Decimal("0")
        return (total_facility_kwh / it_equipment_kwh).quantize(Decimal("0.01"))

    @staticmethod
    def wue(water_liters: Decimal, it_equipment_kwh: Decimal) -> Decimal:
        """Water Usage Effectiveness = Water Consumed (L) / IT Equipment Energy (kWh)."""
        if it_equipment_kwh == 0:
            return Decimal("0")
        return (water_liters / it_equipment_kwh).quantize(Decimal("0.01"))

    @staticmethod
    def cue(emissions_kg_co2e: Decimal, it_equipment_kwh: Decimal) -> Decimal:
        """Carbon Usage Effectiveness = Carbon Emissions / IT Equipment Energy."""
        if it_equipment_kwh == 0:
            return Decimal("0")
        return (emissions_kg_co2e / it_equipment_kwh).quantize(Decimal("0.001"))

    @staticmethod
    def energy_per_1k_inferences(total_kwh: Decimal, num_requests: int) -> Decimal:
        """Energy per 1,000 inference requests."""
        if num_requests == 0:
            return Decimal("0")
        return (total_kwh / Decimal(num_requests) * 1000).quantize(Decimal("0.0001"))

    @staticmethod
    def energy_per_token(total_kwh: Decimal, tokens_generated: int) -> Decimal:
        """Energy per token generated."""
        if tokens_generated == 0:
            return Decimal("0")
        return (total_kwh / Decimal(tokens_generated)).quantize(Decimal("0.000001"))

    @staticmethod
    def energy_per_agent_action(total_kwh: Decimal, actions_performed: int) -> Decimal:
        """Energy per agent action."""
        if actions_performed == 0:
            return Decimal("0")
        return (total_kwh / Decimal(actions_performed)).quantize(Decimal("0.0001"))

    @staticmethod
    def idle_power_ratio(idle_kwh: Decimal, total_kwh: Decimal) -> Decimal:
        """Idle power consumption as percentage of total."""
        if total_kwh == 0:
            return Decimal("0")
        return (idle_kwh / total_kwh * 100).quantize(Decimal("0.1"))

    @staticmethod
    def energy_proportionality(useful_work_kwh: Decimal, total_energy_kwh: Decimal) -> Decimal:
        """Ratio of useful work energy to total energy consumed."""
        if total_energy_kwh == 0:
            return Decimal("0")
        return (useful_work_kwh / total_energy_kwh).quantize(Decimal("0.01"))

    @staticmethod
    def renewable_energy_percentage(renewable_kwh: Decimal, total_kwh: Decimal) -> Decimal:
        """Percentage of energy from renewable sources."""
        if total_kwh == 0:
            return Decimal("0")
        return (renewable_kwh / total_kwh * 100).quantize(Decimal("0.1"))


class EnergyMonitoringSystem:
    """
    Real-time energy monitoring system for GRC_Claw AI operations.
    Collects readings from multiple sources and provides aggregated metrics.
    """

    def __init__(self):
        self._readings: list[EnergyReading] = []
        self._calculator = EnergyMetricsCalculator()

    def add_reading(self, reading: EnergyReading) -> None:
        """Add a new energy reading to the system."""
        self._readings.append(reading)

    def get_readings(
        self,
        facility_id: Optional[str] = None,
        workload_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> list[EnergyReading]:
        """Filter readings by criteria."""
        results = self._readings
        if facility_id:
            results = [r for r in results if r.facility_id == facility_id]
        if workload_id:
            results = [r for r in results if r.workload_id == workload_id]
        if start:
            results = [r for r in results if r.timestamp >= start]
        if end:
            results = [r for r in results if r.timestamp <= end]
        return results

    def get_facility_metrics(
        self,
        facility_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> dict:
        """Get aggregated metrics for a facility."""
        readings = self.get_readings(facility_id=facility_id, start=start, end=end)
        if not readings:
            return {}

        total_kwh = sum(r.energy_kwh for r in readings)
        it_kwh = sum(r.it_equipment_kwh for r in readings)
        pue_values = [r.pue for r in readings if r.pue is not None]
        wue_values = [r.wue for r in readings if r.wue is not None]

        return {
            "facility_id": facility_id,
            "total_energy_kwh": total_kwh,
            "it_equipment_kwh": it_kwh,
            "avg_pue": statistics.mean(pue_values) if pue_values else None,
            "avg_wue": statistics.mean(wue_values) if wue_values else None,
            "reading_count": len(readings),
            "time_range": {
                "start": min(r.timestamp for r in readings),
                "end": max(r.timestamp for r in readings),
            },
        }

    def get_workload_metrics(
        self,
        workload_id: str,
        workload_type: WorkloadType,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> dict:
        """Get energy metrics for a specific workload."""
        readings = self.get_readings(workload_id=workload_id, start=start, end=end)
        if not readings:
            return {}

        total_kwh = sum(r.energy_kwh for r in readings)
        it_kwh = sum(r.it_equipment_kwh for r in readings)

        metrics = {
            "workload_id": workload_id,
            "workload_type": workload_type.value,
            "total_energy_kwh": total_kwh,
            "it_equipment_kwh": it_kwh,
            "reading_count": len(readings),
        }

        # Add workload-specific metrics
        if workload_type == WorkloadType.INFERENCE:
            # These would come from the inference serving system
            metrics["energy_per_1k_inferences"] = None  # Placeholder
        elif workload_type == WorkloadType.TRAINING:
            metrics["energy_per_epoch"] = None  # Placeholder

        return metrics

    def detect_anomalies(
        self,
        facility_id: str,
        threshold_std_dev: float = 2.0,
        window_hours: int = 24,
    ) -> list[dict]:
        """
        Detect energy consumption anomalies using statistical methods.
        Flags readings that deviate significantly from the mean.
        """
        end = datetime.utcnow()
        start = end - timedelta(hours=window_hours)
        readings = self.get_readings(facility_id=facility_id, start=start, end=end)

        if len(readings) < 3:
            return []

        values = [float(r.energy_kwh) for r in readings]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values)

        anomalies = []
        for r in readings:
            if std_val > 0:
                z_score = (float(r.energy_kwh) - mean_val) / std_val
                if abs(z_score) > threshold_std_dev:
                    anomalies.append({
                        "reading_id": r.reading_id,
                        "timestamp": r.timestamp,
                        "energy_kwh": r.energy_kwh,
                        "z_score": round(z_score, 2),
                        "expected_range": (
                            round(mean_val - threshold_std_dev * std_val, 2),
                            round(mean_val + threshold_std_dev * std_val, 2),
                        ),
                    })
        return anomalies

    def get_efficiency_trend(
        self,
        facility_id: str,
        metric: str = "pue",
        days: int = 30,
    ) -> list[dict]:
        """Get daily trend for a specific efficiency metric."""
        end = datetime.utcnow()
        start = end - timedelta(days=days)
        readings = self.get_readings(facility_id=facility_id, start=start, end=end)

        # Group by day
        daily: dict[str, list[Decimal]] = defaultdict(list)
        for r in readings:
            day_key = r.timestamp.strftime("%Y-%m-%d")
            val = getattr(r, metric, None)
            if val is not None:
                daily[day_key].append(val)

        trend = []
        for day, values in sorted(daily.items()):
            trend.append({
                "date": day,
                "avg": round(statistics.mean(values), 3),
                "min": round(min(values), 3),
                "max": round(max(values), 3),
                "count": len(values),
            })
        return trend


# ── Simulated Data Collectors ─────────────────────────────────────────

class GPUPowerCollector:
    """Collects GPU power telemetry (simulated — replace with DCGM/NVML in production)."""

    def __init__(self, monitoring_system: EnergyMonitoringSystem):
        self.system = monitoring_system

    def collect_reading(
        self,
        facility_id: str,
        workload_id: str,
        energy_kwh: Decimal,
        it_equipment_kwh: Decimal,
        pue: Decimal = Decimal("1.25"),
    ) -> EnergyReading:
        reading = EnergyReading(
            reading_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            facility_id=facility_id,
            workload_id=workload_id,
            energy_kwh=energy_kwh,
            it_equipment_kwh=it_equipment_kwh,
            pue=pue,
        )
        self.system.add_reading(reading)
        return reading


class CloudAPICollector:
    """Collects energy data from cloud provider APIs (AWS/GCP/Azure)."""

    def __init__(self, monitoring_system: EnergyMonitoringSystem):
        self.system = monitoring_system

    def collect_from_cloud(
        self,
        provider: str,                 # "aws", "gcp", "azure"
        region: str,
        workload_id: str,
        energy_kwh: Decimal,
        it_equipment_kwh: Decimal,
    ) -> EnergyReading:
        """
        In production, this would call:
        - AWS: Cost Explorer API / Carbon Footprint API
        - GCP: Billing API / Carbon Footprint API
        - Azure: Cost Management API / Carbon Footprint API
        """
        reading = EnergyReading(
            reading_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            facility_id=f"{provider}-{region}",
            workload_id=workload_id,
            energy_kwh=energy_kwh,
            it_equipment_kwh=it_equipment_kwh,
            source="cloud_api",
        )
        self.system.add_reading(reading)
        return reading


# ── Example Usage ─────────────────────────────────────────────────────

def demo_energy_monitoring():
    system = EnergyMonitoringSystem()
    gpu_collector = GPUPowerCollector(system)
    cloud_collector = CloudAPICollector(system)

    # Simulate GPU readings
    for i in range(10):
        gpu_collector.collect_reading(
            facility_id="dc-us-east-1",
            workload_id="training-run-47",
            energy_kwh=Decimal("125.5"),
            it_equipment_kwh=Decimal("100.0"),
            pue=Decimal("1.255"),
        )

    # Simulate cloud readings
    cloud_collector.collect_from_cloud(
        provider="aws",
        region="us-east-1",
        workload_id="inference-cluster-us",
        energy_kwh=Decimal("500.0"),
        it_equipment_kwh=Decimal("400.0"),
    )

    # Get facility metrics
    metrics = system.get_facility_metrics("dc-us-east-1")
    print("=== Facility Metrics ===")
    for key, value in metrics.items():
        print(f"  {key}: {value}")

    # Get PUE trend
    trend = system.get_efficiency_trend("dc-us-east-1", metric="pue", days=7)
    print(f"\n=== PUE Trend ({len(trend)} days) ===")
    for day in trend:
        print(f"  {day['date']}: avg={day['avg']}, min={day['min']}, max={day['max']}")

    # Detect anomalies
    anomalies = system.detect_anomalies("dc-us-east-1")
    print(f"\n=== Anomalies Detected: {len(anomalies)} ===")
    for a in anomalies:
        print(f"  {a['timestamp']}: {a['energy_kwh']} kWh (z={a['z_score']})")

    return system


if __name__ == "__main__":
    demo_energy_monitoring()
```

---

## 4. Sustainability Reporting (Python)

Implements GHG Protocol, GRI, CSRD, and TCFD-aligned sustainability reporting.

```python
# sustainability_reporting.py
"""
GRC_Claw Sustainability Reporting Module
Generates GHG inventories, GRI reports, CSRD statements, and TCFD disclosures
per spec §7. Supports automated report generation and regulatory filing.
"""
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from models import EmissionScope, WorkloadType


class GHGInventoryReport:
    """
    Annual GHG Inventory report aligned with GHG Protocol Corporate Standard
    and ISO 14064-1. Covers Scope 1, 2 (both methods), and Scope 3.
    """

    def __init__(self, reporting_year: int, organization: str = "GRC_Claw"):
        self.report_id = str(uuid.uuid4())
        self.reporting_year = reporting_year
        self.organization = organization
        self.generated_at = datetime.utcnow()
        self.scope1_emissions: dict[str, Decimal] = defaultdict(Decimal)
        self.scope2_location: dict[str, Decimal] = defaultdict(Decimal)
        self.scope2_market: dict[str, Decimal] = defaultdict(Decimal)
        self.scope3_emissions: dict[int, Decimal] = defaultdict(Decimal)
        self.carbon_intensity_metrics: dict[str, Decimal] = {}
        self.methodology_notes: list[str] = []
        self.assurance_level: str = "limited"  # "limited" or "reasonable"
        self.verifier: Optional[str] = None

    def add_scope1(self, source: str, emissions_kg_co2e: Decimal) -> None:
        self.scope1_emissions[source] += emissions_kg_co2e

    def add_scope2_location(self, facility: str, emissions_kg_co2e: Decimal) -> None:
        self.scope2_location[facility] += emissions_kg_co2e

    def add_scope2_market(self, facility: str, emissions_kg_co2e: Decimal) -> None:
        self.scope2_market[facility] += emissions_kg_co2e

    def add_scope3(self, category: int, emissions_kg_co2e: Decimal) -> None:
        self.scope3_emissions[category] += emissions_kg_co2e

    def set_carbon_intensity(self, metric_name: str, value: Decimal) -> None:
        self.carbon_intensity_metrics[metric_name] = value

    def total_scope1(self) -> Decimal:
        return sum(self.scope1_emissions.values(), Decimal("0"))

    def total_scope2_location(self) -> Decimal:
        return sum(self.scope2_location.values(), Decimal("0"))

    def total_scope2_market(self) -> Decimal:
        return sum(self.scope2_market.values(), Decimal("0"))

    def total_scope3(self) -> Decimal:
        return sum(self.scope3_emissions.values(), Decimal("0"))

    def total_emissions(self) -> Decimal:
        return self.total_scope1() + self.total_scope2_location() + self.total_scope3()

    def to_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "organization": self.organization,
            "reporting_year": self.reporting_year,
            "generated_at": self.generated_at.isoformat(),
            "assurance_level": self.assurance_level,
            "verifier": self.verifier,
            "emissions": {
                "scope_1": {
                    "total_kg_co2e": self.total_scope1(),
                    "total_tonnes_co2e": self.total_scope1() / 1000,
                    "by_source": {k: v for k, v in self.scope1_emissions.items()},
                },
                "scope_2": {
                    "location_based": {
                        "total_kg_co2e": self.total_scope2_location(),
                        "total_tonnes_co2e": self.total_scope2_location() / 1000,
                        "by_facility": {k: v for k, v in self.scope2_location.items()},
                    },
                    "market_based": {
                        "total_kg_co2e": self.total_scope2_market(),
                        "total_tonnes_co2e": self.total_scope2_market() / 1000,
                        "by_facility": {k: v for k, v in self.scope2_market.items()},
                    },
                },
                "scope_3": {
                    "total_kg_co2e": self.total_scope3(),
                    "total_tonnes_co2e": self.total_scope3() / 1000,
                    "by_category": {f"cat_{k}": v for k, v in self.scope3_emissions.items()},
                },
                "total": {
                    "kg_co2e": self.total_emissions(),
                    "tonnes_co2e": self.total_emissions() / 1000,
                },
            },
            "carbon_intensity_metrics": self.carbon_intensity_metrics,
            "methodology_notes": self.methodology_notes,
        }

    def to_markdown(self) -> str:
        """Generate a markdown report suitable for regulatory filing."""
        data = self.to_dict()
        lines = [
            f"# {self.organization} Annual GHG Inventory — {self.reporting_year}",
            "",
            f"**Report ID:** {self.report_id}  ",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Assurance Level:** {self.assurance_level.title()}  ",
            f"**Verifier:** {self.verifier or 'Pending'}  ",
            "",
            "## Executive Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Emissions | {data['emissions']['total']['tonnes_co2e']} t CO₂e |",
            f"| Scope 1 | {data['emissions']['scope_1']['total_tonnes_co2e']} t CO₂e |",
            f"| Scope 2 (Location) | {data['emissions']['scope_2']['location_based']['total_tonnes_co2e']} t CO₂e |",
            f"| Scope 2 (Market) | {data['emissions']['scope_2']['market_based']['total_tonnes_co2e']} t CO₂e |",
            f"| Scope 3 | {data['emissions']['scope_3']['total_tonnes_co2e']} t CO₂e |",
            "",
            "## Scope 1 — Direct Emissions",
            "",
            "| Source | Emissions (kg CO₂e) |",
            "|--------|-------------------|",
        ]
        for source, val in self.scope1_emissions.items():
            lines.append(f"| {source} | {val} |")

        lines.extend([
            "",
            "## Scope 2 — Indirect Emissions from Purchased Energy",
            "",
            "### Location-Based Method",
            "",
            "| Facility | Emissions (kg CO₂e) |",
            "|----------|-------------------|",
        ])
        for facility, val in self.scope2_location.items():
            lines.append(f"| {facility} | {val} |")

        lines.extend([
            "",
            "### Market-Based Method",
            "",
            "| Facility | Emissions (kg CO₂e) |",
            "|----------|-------------------|",
        ])
        for facility, val in self.scope2_market.items():
            lines.append(f"| {facility} | {val} |")

        lines.extend([
            "",
            "## Scope 3 — Value Chain Emissions",
            "",
            "| Category | Emissions (kg CO₂e) |",
            "|----------|-------------------|",
        ])
        SCOPE3_NAMES = {
            1: "Purchased Goods & Services",
            2: "Capital Goods",
            3: "Fuel- & Energy-Related Activities",
            4: "Upstream Transportation & Distribution",
            5: "Waste Generated in Operations",
            6: "Business Travel",
            7: "Employee Commuting",
            8: "Upstream Leased Assets",
            9: "Downstream Transportation & Distribution",
            10: "Processing of Sold Products",
            11: "Use of Sold Products",
            12: "End-of-Life Treatment of Sold Products",
            13: "Downstream Leased Assets",
            14: "Franchises",
            15: "Investments",
        }
        for cat, val in sorted(self.scope3_emissions.items()):
            name = SCOPE3_NAMES.get(cat, f"Category {cat}")
            lines.append(f"| Cat. {cat}: {name} | {val} |")

        lines.extend([
            "",
            "## Carbon Intensity Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
        ])
        for metric, val in self.carbon_intensity_metrics.items():
            lines.append(f"| {metric} | {val} |")

        lines.extend([
            "",
            "## Methodology Notes",
            "",
        ])
        for note in self.methodology_notes:
            lines.append(f"- {note}")

        lines.extend([
            "",
            "---",
            "*This report was generated automatically by the GRC_Claw Sustainability Reporting Engine.*",
        ])

        return "\n".join(lines)

    def save(self, output_dir: str = "reports") -> Path:
        """Save report as both JSON and Markdown."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        json_path = out / f"ghg_inventory_{self.reporting_year}.json"
        md_path = out / f"ghg_inventory_{self.reporting_year}.md"

        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        with open(md_path, "w") as f:
            f.write(self.to_markdown())

        return md_path


class GRIReport:
    """GRI 302 (Energy) and GRI 305 (Emissions) aligned report."""

    def __init__(self, reporting_year: int):
        self.reporting_year = reporting_year
        self.energy_data: dict = {}
        self.emissions_data: dict = {}

    def add_energy_disclosure(self, disclosure_id: str, value: Decimal, unit: str) -> None:
        self.energy_data[disclosure_id] = {"value": value, "unit": unit}

    def add_emissions_disclosure(self, disclosure_id: str, value: Decimal, unit: str) -> None:
        self.emissions_data[disclosure_id] = {"value": value, "unit": unit}

    def to_dict(self) -> dict:
        return {
            "framework": "GRI Standards",
            "reporting_year": self.reporting_year,
            "GRI_302_Energy": self.energy_data,
            "GRI_305_Emissions": self.emissions_data,
        }


class CSRDSustainabilityStatement:
    """
    EU CSRD-aligned sustainability statement with double materiality assessment.
    """

    def __init__(self, reporting_year: int):
        self.reporting_year = reporting_year
        self.double_materiality: dict = {}
        self.environmental_impact: dict = {}
        self.targets: dict = {}
        self.progress: dict = {}

    def set_double_materiality(
        self,
        topic: str,
        financial_materiality: str,    # "high", "medium", "low"
        impact_materiality: str,       # "high", "medium", "low"
    ) -> None:
        self.double_materiality[topic] = {
            "financial_materiality": financial_materiality,
            "impact_materiality": impact_materiality,
        }

    def to_dict(self) -> dict:
        return {
            "framework": "EU CSRD (Directive 2022/2464)",
            "reporting_year": self.reporting_year,
            "double_materiality_assessment": self.double_materiality,
            "environmental_impact": self.environmental_impact,
            "targets": self.targets,
            "progress": self.progress,
        }


class TCFDDisclosure:
    """TCFD/ISSB-aligned climate-related financial disclosure."""

    def __init__(self, reporting_year: int):
        self.reporting_year = reporting_year
        self.governance: dict = {}
        self.strategy: dict = {}
        self.risk_management: dict = {}
        self.metrics_targets: dict = {}

    def to_dict(self) -> dict:
        return {
            "framework": "TCFD / ISSB IFRS S2",
            "reporting_year": self.reporting_year,
            "governance": self.governance,
            "strategy": self.strategy,
            "risk_management": self.risk_management,
            "metrics_targets": self.metrics_targets,
        }


class SustainabilityReportingEngine:
    """
    Unified reporting engine that generates all required sustainability reports.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_annual_ghg_inventory(
        self,
        reporting_year: int,
        carbon_engine,  # CarbonAccountingEngine from carbon_tracking.py
    ) -> GHGInventoryReport:
        """Generate the annual GHG inventory from carbon accounting data."""
        report = GHGInventoryReport(reporting_year)

        # Populate from carbon engine
        summary = carbon_engine.get_scope_summary()
        report.add_scope1("total", summary["scope_1_kg_co2e"])
        report.add_scope2_location("total", summary["scope_2_kg_co2e"])
        report.add_scope3(1, summary["scope_3_kg_co2e"])

        # Set methodology notes
        report.methodology_notes = [
            "Organizational boundary: Operational control approach",
            "Emission factors: IEA, EPA, DEFRA, IPCC AR6 (2024 values)",
            "Scope 2: Both location-based and market-based methods reported",
            "Scope 3: Categories 1, 2, 3, 8, 11 (high-relevance categories)",
            "GWP values: IPCC AR6 100-year time horizon",
        ]

        return report

    def generate_all_reports(
        self,
        reporting_year: int,
        carbon_engine,
    ) -> dict[str, Path]:
        """Generate all required sustainability reports."""
        paths = {}

        # GHG Inventory
        ghg = self.generate_annual_ghg_inventory(reporting_year, carbon_engine)
        paths["ghg_inventory"] = ghg.save(str(self.output_dir))

        # GRI Report
        gri = GRIReport(reporting_year)
        gri.add_energy_disclosure("GRI_302-1", Decimal("12500"), "kWh")
        gri.add_emissions_disclosure("GRI_305-1", ghg.total_scope1(), "kg CO2e")
        gri.add_emissions_disclosure("GRI_305-2", ghg.total_scope2_location(), "kg CO2e")
        gri.add_emissions_disclosure("GRI_305-3", ghg.total_scope3(), "kg CO2e")
        gri_path = self.output_dir / f"gri_report_{reporting_year}.json"
        with open(gri_path, "w") as f:
            json.dump(gri.to_dict(), f, indent=2, default=str)
        paths["gri"] = gri_path

        # CSRD Statement
        csrd = CSRDSustainabilityStatement(reporting_year)
        csrd.set_double_materiality("climate_change", "high", "high")
        csrd.set_double_materiality("energy", "high", "medium")
        csrd_path = self.output_dir / f"csrd_statement_{reporting_year}.json"
        with open(csrd_path, "w") as f:
            json.dump(csrd.to_dict(), f, indent=2, default=str)
        paths["csrd"] = csrd_path

        # TCFD Disclosure
        tcfd = TCFDDisclosure(reporting_year)
        tcfd.governance = {"board_oversight": "Quarterly review"}
        tcfd.strategy = {"climate_scenarios": ["1.5°C", "2°C", "3°C"]}
        tcfd_path = self.output_dir / f"tcfd_disclosure_{reporting_year}.json"
        with open(tcfd_path, "w") as f:
            json.dump(tcfd.to_dict(), f, indent=2, default=str)
        paths["tcfd"] = tcfd_path

        return paths


# ── Example Usage ─────────────────────────────────────────────────────

def demo_sustainability_reporting():
    from carbon_tracking import CarbonAccountingEngine

    # Create carbon engine with sample data
    engine = CarbonAccountingEngine()
    engine.calculate_scope1(
        facility_id="dc-us-east-1", source="generator",
        activity_data=Decimal("500"), activity_unit="liters",
        emission_factor_id="diesel-2024",
    )
    engine.calculate_scope2_location_based(
        facility_id="dc-us-east-1", electricity_kwh=Decimal("10000"),
        grid_factor_id="grid-us-2024",
    )
    engine.calculate_scope3(
        category=1, facility_id="dc-us-east-1",
        activity_data=Decimal("50"), activity_unit="units",
        emission_factor=Decimal("150"), calculation_method="supplier_specific",
    )

    # Generate all reports
    reporting = SustainabilityReportingEngine(output_dir="demo_reports")
    paths = reporting.generate_all_reports(2025, engine)

    print("=== Generated Reports ===")
    for name, path in paths.items():
        print(f"  {name}: {path}")

    return paths


if __name__ == "__main__":
    demo_sustainability_reporting()
```

---

## 5. Environmental Impact Assessment (Python)

Implements ISO 14040/14044 Life Cycle Assessment with AI-specific impact categories.

```python
# environmental_impact_assessment.py
"""
GRC_Claw Environmental Impact Assessment Module
Implements ISO 14040/14044 Life Cycle Assessment adapted for AI systems.
Produces Environmental Impact Scores (EIS) per spec §8.
"""
from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from models import ImpactRating


class LifeCycleStage(str, Enum):
    RAW_MATERIAL = "raw_material"
    HARDWARE_MANUFACTURE = "hardware_manufacture"
    TRANSPORTATION = "transportation"
    AI_TRAINING = "ai_training"
    AI_INFERENCE = "ai_inference"
    AGENT_OPERATIONS = "agent_operations"
    MODEL_UPDATES = "model_updates"
    END_OF_LIFE = "end_of_life"


class ImpactCategory(str, Enum):
    CLIMATE_CHANGE = "climate_change"
    RESOURCE_DEPLETION = "resource_depletion"
    WATER_CONSUMPTION = "water_consumption"
    EUTROPHICATION = "eutrophication"
    ACIDIFICATION = "acidification"
    OZONE_DEPLETION = "ozone_depletion"
    HUMAN_TOXICITY = "human_toxicity"
    ECOTOXICITY = "ecotoxicity"
    LAND_USE = "land_use"
    PARTICULATE_MATTER = "particulate_matter"


@dataclass
class LifeCycleInventoryItem:
    """Single LCI data point for a life cycle stage."""
    stage: LifeCycleStage
    category: ImpactCategory
    value: Decimal
    unit: str
    data_quality: str = "primary"     # "primary", "secondary", "estimated"
    source: str = ""


@dataclass
class LifeCycleImpactResult:
    """LCIA result for a single impact category."""
    category: ImpactCategory
    value: Decimal
    unit: str
    characterization_factor: Decimal
    normalized_score: Decimal = Decimal("0")  # 0-100


@dataclass
class EnvironmentalImpactAssessment:
    """Complete EIA for an AI system."""
    assessment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    system_name: str = ""
    system_id: str = ""
    functional_unit: str = ""          # e.g., "per 1000 inference requests"
    assessment_date: datetime = field(default_factory=datetime.utcnow)
    lci_items: list[LifeCycleInventoryItem] = field(default_factory=list)
    lcia_results: list[LifeCycleImpactResult] = field(default_factory=list)
    eis_score: Decimal = Decimal("0")  # Environmental Impact Score 0-100
    eis_rating: str = ""
    improvement_recommendations: list[str] = field(default_factory=list)
    assessor: str = ""

    def add_lci_item(self, item: LifeCycleInventoryItem) -> None:
        self.lci_items.append(item)

    def calculate_eis(self) -> Decimal:
        """
        Calculate Environmental Impact Score (EIS) as weighted composite.
        
        Components and weights per spec §8.6:
        - Carbon intensity: 30%
        - Energy efficiency: 25%
        - Hardware efficiency: 15%
        - Renewable energy: 15%
        - Water efficiency: 10%
        - End-of-life management: 5%
        """
        # Calculate component scores (0-100, where 100 = best)
        carbon_score = self._score_carbon_intensity()
        energy_score = self._score_energy_efficiency()
        hardware_score = self._score_hardware_efficiency()
        renewable_score = self._score_renewable_energy()
        water_score = self._score_water_efficiency()
        eol_score = self._score_end_of_life()

        # Weighted composite
        self.eis_score = (
            Decimal("0.30") * carbon_score +
            Decimal("0.25") * energy_score +
            Decimal("0.15") * hardware_score +
            Decimal("0.15") * renewable_score +
            Decimal("0.10") * water_score +
            Decimal("0.05") * eol_score
        ).quantize(Decimal("0.1"))

        # Determine rating
        score_float = float(self.eis_score)
        if score_float <= 20:
            self.eis_rating = ImpactRating.A_EXCELLENT.value
        elif score_float <= 40:
            self.eis_rating = ImpactRating.B_GOOD.value
        elif score_float <= 60:
            self.eis_rating = ImpactRating.C_AVERAGE.value
        elif score_float <= 80:
            self.eis_rating = ImpactRating.D_POOR.value
        else:
            self.eis_rating = ImpactRating.F_CRITICAL.value

        return self.eis_score

    def _score_carbon_intensity(self) -> Decimal:
        """Score carbon intensity using log-scale normalization."""
        # Find climate change LCI items
        carbon_items = [
            item for item in self.lci_items
            if item.category == ImpactCategory.CLIMATE_CHANGE
        ]
        if not carbon_items:
            return Decimal("50")  # Neutral if no data

        total_carbon = sum(item.value for item in carbon_items)
        # Benchmark: 25 t CO2e per training run (from spec Appendix C)
        benchmark = Decimal("25000")  # kg CO2e
        max_ratio = Decimal("10")

        if total_carbon <= 0:
            return Decimal("100")

        ratio = total_carbon / benchmark
        if ratio <= 1:
            return Decimal("100")
        if ratio >= max_ratio:
            return Decimal("0")

        # Log-scale: score = 100 * (1 - log(ratio) / log(max_ratio))
        score = 100 * (1 - math.log(float(ratio)) / math.log(float(max_ratio)))
        return Decimal(str(max(0, min(100, score)))).quantize(Decimal("0.1"))

    def _score_energy_efficiency(self) -> Decimal:
        """Score energy efficiency."""
        energy_items = [
            item for item in self.lci_items
            if item.stage in (LifeCycleStage.AI_TRAINING, LifeCycleStage.AI_INFERENCE)
            and item.unit == "kWh"
        ]
        if not energy_items:
            return Decimal("50")

        total_energy = sum(item.value for item in energy_items)
        # Benchmark: 10,000 kWh per training run
        benchmark = Decimal("10000")
        max_ratio = Decimal("10")

        if total_energy <= 0:
            return Decimal("100")

        ratio = total_energy / benchmark
        if ratio <= 1:
            return Decimal("100")
        if ratio >= max_ratio:
            return Decimal("0")

        score = 100 * (1 - math.log(float(ratio)) / math.log(float(max_ratio)))
        return Decimal(str(max(0, min(100, score)))).quantize(Decimal("0.1"))

    def _score_hardware_efficiency(self) -> Decimal:
        """Score hardware embodied carbon efficiency."""
        hw_items = [
            item for item in self.lci_items
            if item.stage == LifeCycleStage.HARDWARE_MANUFACTURE
        ]
        if not hw_items:
            return Decimal("50")

        total = sum(item.value for item in hw_items)
        # Benchmark: 50 GPUs × 150 kg CO2e = 7500 kg
        benchmark = Decimal("7500")
        max_ratio = Decimal("10")

        if total <= 0:
            return Decimal("100")

        ratio = total / benchmark
        if ratio <= 1:
            return Decimal("100")
        if ratio >= max_ratio:
            return Decimal("0")

        score = 100 * (1 - math.log(float(ratio)) / math.log(float(max_ratio)))
        return Decimal(str(max(0, min(100, score)))).quantize(Decimal("0.1"))

    def _score_renewable_energy(self) -> Decimal:
        """Score renewable energy percentage (linear)."""
        # This would come from energy monitoring data
        # Default to neutral if not specified
        return Decimal("60")  # 60% renewable = score 60

    def _score_water_efficiency(self) -> Decimal:
        """Score water efficiency."""
        water_items = [
            item for item in self.lci_items
            if item.category == ImpactCategory.WATER_CONSUMPTION
        ]
        if not water_items:
            return Decimal("50")

        total_water = sum(item.value for item in water_items)
        # Benchmark: 10,000 L per training run
        benchmark = Decimal("10000")
        max_ratio = Decimal("10")

        if total_water <= 0:
            return Decimal("100")

        ratio = total_water / benchmark
        if ratio <= 1:
            return Decimal("100")
        if ratio >= max_ratio:
            return Decimal("0")

        score = 100 * (1 - math.log(float(ratio)) / math.log(float(max_ratio)))
        return Decimal(str(max(0, min(100, score)))).quantize(Decimal("0.1"))

    def _score_end_of_life(self) -> Decimal:
        """Score end-of-life management (recycling rate)."""
        eol_items = [
            item for item in self.lci_items
            if item.stage == LifeCycleStage.END_OF_LIFE
        ]
        if not eol_items:
            return Decimal("50")

        # Assume value is recycling rate percentage
        recycling_rate = eol_items[0].value
        return min(Decimal("100"), recycling_rate)

    def generate_scorecard(self) -> dict:
        """Generate a one-page Environmental Impact Scorecard."""
        return {
            "assessment_id": self.assessment_id,
            "system_name": self.system_name,
            "system_id": self.system_id,
            "functional_unit": self.functional_unit,
            "assessment_date": self.assessment_date.isoformat(),
            "eis_score": self.eis_score,
            "eis_rating": self.eis_rating,
            "rating_description": self._rating_description(),
            "life_cycle_stages_assessed": list(set(
                item.stage.value for item in self.lci_items
            )),
            "impact_categories_assessed": list(set(
                item.category.value for item in self.lci_items
            )),
            "improvement_recommendations": self.improvement_recommendations,
            "assessor": self.assessor,
        }

    def _rating_description(self) -> str:
        descriptions = {
            "A": "Excellent — Minimal environmental impact; industry-leading efficiency",
            "B": "Good — Below-average impact; good efficiency practices",
            "C": "Average — Industry-average impact; standard practices",
            "D": "Poor — Above-average impact; improvement needed",
            "F": "Critical — Severe environmental impact; immediate action required",
        }
        return descriptions.get(self.eis_rating, "Unknown")

    def generate_report(self) -> str:
        """Generate a full Environmental Impact Report in markdown."""
        scorecard = self.generate_scorecard()
        lines = [
            f"# Environmental Impact Assessment Report",
            f"",
            f"**System:** {self.system_name} (`{self.system_id}`)  ",
            f"**Functional Unit:** {self.functional_unit}  ",
            f"**Assessment Date:** {self.assessment_date.strftime('%Y-%m-%d')}  ",
            f"**Assessor:** {self.assessor}  ",
            f"",
            f"## Environmental Impact Score",
            f"",
            f"| Score | Rating | Description |",
            f"|-------|--------|-------------|",
            f"| {self.eis_score} | {self.eis_rating} | {self._rating_description()} |",
            f"",
            f"## Life Cycle Inventory",
            f"",
            f"| Stage | Category | Value | Unit | Data Quality |",
            f"|-------|----------|-------|------|--------------|",
        ]
        for item in self.lci_items:
            lines.append(
                f"| {item.stage.value} | {item.category.value} | "
                f"{item.value} | {item.unit} | {item.data_quality} |"
            )

        lines.extend([
            f"",
            f"## Improvement Recommendations",
            f"",
        ])
        for rec in self.improvement_recommendations:
            lines.append(f"- {rec}")

        lines.extend([
            f"",
            "---",
            "*Generated by GRC_Claw Environmental Impact Assessment Engine (ISO 14040/14044 aligned)*",
        ])

        return "\n".join(lines)


class EIAManager:
    """Manages EIAs for all AI systems in GRC_Claw."""

    def __init__(self):
        self.assessments: dict[str, EnvironmentalImpactAssessment] = {}

    def create_assessment(
        self,
        system_name: str,
        system_id: str,
        functional_unit: str,
        assessor: str,
    ) -> EnvironmentalImpactAssessment:
        assessment = EnvironmentalImpactAssessment(
            system_name=system_name,
            system_id=system_id,
            functional_unit=functional_unit,
            assessor=assessor,
        )
        self.assessments[assessment.assessment_id] = assessment
        return assessment

    def get_assessment(self, assessment_id: str) -> Optional[EnvironmentalImpactAssessment]:
        return self.assessments.get(assessment_id)

    def get_system_score(self, system_id: str) -> Optional[dict]:
        for assessment in self.assessments.values():
            if assessment.system_id == system_id:
                return assessment.generate_scorecard()
        return None

    def list_assessments(self) -> list[dict]:
        return [a.generate_scorecard() for a in self.assessments.values()]


# ── Example Usage ─────────────────────────────────────────────────────

def demo_eia():
    manager = EIAManager()

    # Create EIA for an LLM training run
    assessment = manager.create_assessment(
        system_name="LLM Training Run #47",
        system_id="model-llm-7b-v3",
        functional_unit="per training run",
        assessor="env-engineer-1",
    )

    # Add LCI items for each life cycle stage
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.RAW_MATERIAL,
        category=ImpactCategory.RESOURCE_DEPLETION,
        value=Decimal("500"), unit="kg",
        data_quality="secondary", source="Ecoinvent",
    ))
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.HARDWARE_MANUFACTURE,
        category=ImpactCategory.CLIMATE_CHANGE,
        value=Decimal("7500"), unit="kg CO2e",
        data_quality="secondary", source="Manufacturer LCA",
    ))
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.AI_TRAINING,
        category=ImpactCategory.CLIMATE_CHANGE,
        value=Decimal("25000"), unit="kg CO2e",
        data_quality="primary", source="Energy monitoring",
    ))
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.AI_INFERENCE,
        category=ImpactCategory.CLIMATE_CHANGE,
        value=Decimal("5000"), unit="kg CO2e",
        data_quality="primary", source="Energy monitoring",
    ))
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.END_OF_LIFE,
        category=ImpactCategory.ECOTOXICITY,
        value=Decimal("85"), unit="%",
        data_quality="estimated", source="E-waste processor",
    ))

    # Add improvement recommendations
    assessment.improvement_recommendations = [
        "Switch to renewable energy for training (potential 40% carbon reduction)",
        "Use mixed-precision training to reduce energy by 20-35%",
        "Implement carbon-aware scheduling for training runs",
        "Evaluate model quantization for inference optimization",
        "Increase hardware recycling rate to 95%",
    ]

    # Calculate EIS
    score = assessment.calculate_eis()
    print(f"Environmental Impact Score: {score} (Rating: {assessment.eis_rating})")
    print(f"Description: {assessment._rating_description()}")

    # Generate report
    report = assessment.generate_report()
    print(f"\n{'='*60}")
    print(report)

    return assessment


if __name__ == "__main__":
    demo_eia()
```

---

## 6. Carbon Optimization (Python)

Implements the DDRAV framework (Detect → Diagnose → Recommend → Automate → Verify) and carbon-aware scheduling.

```python
# carbon_optimization.py
"""
GRC_Claw Carbon Optimization Module
Implements the DDRAV framework for continuous carbon optimization,
carbon-aware workload scheduling, and Green AI recommendations
per spec §16 and §19.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional


class WorkloadFlexibility(str, Enum):
    HARD_REAL_TIME = "hard_real_time"        # latency < 100ms
    SOFT_REAL_TIME = "soft_real_time"        # latency < 5min
    NEAR_REAL_TIME = "near_real_time"        # latency < 1hr
    BATCH = "batch"                          # latency > 1hr


class RecommendationPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationTimeframe(str, Enum):
    IMMEDIATE = "immediate"          # auto-applicable
    SHORT_TERM = "short_term"        # 1-4 weeks
    STRATEGIC = "strategic"          # 1-6 months


@dataclass
class OptimizationRecommendation:
    """A single carbon optimization recommendation."""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""               # "compute", "infrastructure", "architectural"
    title: str = ""
    description: str = ""
    trigger_condition: str = ""
    expected_savings: str = ""       # e.g., "20-40% energy reduction"
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    timeframe: RecommendationTimeframe = RecommendationTimeframe.SHORT_TERM
    estimated_carbon_savings_kg: Decimal = Decimal("0")
    estimated_cost: Decimal = Decimal("0")
    implementation_effort: str = ""  # "low", "medium", "high"
    status: str = "pending"          # "pending", "approved", "implemented", "rejected"


@dataclass
class CarbonIntensityForecast:
    """Forecast of grid carbon intensity for a region."""
    region: str
    current_intensity: Decimal       # g CO2e/kWh
    forecast_2hr: Decimal
    forecast_6hr: Decimal
    forecast_24hr: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SchedulingDecision:
    """Result of carbon-aware scheduling decision."""
    workload_id: str
    flexibility: WorkloadFlexibility
    decision: str                    # "run_now", "delay", "migrate"
    delay_minutes: int = 0
    target_region: Optional[str] = None
    current_intensity: Decimal = Decimal("0")
    target_intensity: Decimal = Decimal("0")
    carbon_savings_percent: Decimal = Decimal("0")
    reasoning: str = ""


class CarbonOptimizationEngine:
    """
    DDRAV-based carbon optimization engine.
    Detects inefficiencies, diagnoses root causes, recommends actions,
    automates what can be automated, and verifies results.
    """

    def __init__(self):
        self.recommendations: list[OptimizationRecommendation] = []
        self.forecasts: dict[str, CarbonIntensityForecast] = {}
        self.scheduling_history: list[SchedulingDecision] = []

    # ── Detection Layer ────────────────────────────────────────────────

    def detect_low_gpu_utilization(
        self,
        workload_id: str,
        avg_utilization: Decimal,
        threshold: Decimal = Decimal("40"),
        duration_days: int = 7,
    ) -> Optional[OptimizationRecommendation]:
        """Detect GPU under-utilization (spec §16.2.1)."""
        if avg_utilization >= threshold:
            return None

        return OptimizationRecommendation(
            category="compute",
            title="GPU Right-Sizing",
            description=f"Workload {workload_id} has {avg_utilization}% GPU utilization "
                        f"(below {threshold}% threshold for {duration_days}+ days)",
            trigger_condition=f"GPU utilization < {threshold}% for > {duration_days} days",
            expected_savings="20-40% energy reduction per workload",
            priority=RecommendationPriority.HIGH,
            timeframe=RecommendationTimeframe.SHORT_TERM,
            estimated_carbon_savings_kg=Decimal("500"),
            implementation_effort="low",
        )

    def detect_idle_resources(
        self,
        resource_id: str,
        idle_minutes: int,
        threshold_minutes: int = 30,
    ) -> Optional[OptimizationRecommendation]:
        """Detect idle resources that should be reclaimed (spec §16.2.2)."""
        if idle_minutes < threshold_minutes:
            return None

        return OptimizationRecommendation(
            category="infrastructure",
            title="Idle GPU Reclamation",
            description=f"Resource {resource_id} idle for {idle_minutes} minutes",
            trigger_condition=f"GPUs idle > {threshold_minutes} minutes with no scheduled job",
            expected_savings="Eliminates idle power draw (10-20% of fleet)",
            priority=RecommendationPriority.CRITICAL,
            timeframe=RecommendationTimeframe.IMMEDIATE,
            estimated_carbon_savings_kg=Decimal("100"),
            implementation_effort="low",
        )

    def detect_oversized_model(
        self,
        workload_id: str,
        model_parameters: int,
        task_complexity: str,        # "simple", "moderate", "complex"
    ) -> Optional[OptimizationRecommendation]:
        """Detect when a large model is used for simple tasks (spec §16.2.3)."""
        if task_complexity != "simple" or model_parameters < 1_000_000_000:
            return None

        return OptimizationRecommendation(
            category="architectural",
            title="Model Selection by Task Complexity",
            description=f"Large model ({model_parameters:,} params) used for simple task",
            trigger_condition="Large model used for simple classification/extraction",
            expected_savings="60-90% energy reduction (smaller model)",
            priority=RecommendationPriority.CRITICAL,
            timeframe=RecommendationTimeframe.STRATEGIC,
            estimated_carbon_savings_kg=Decimal("2000"),
            implementation_effort="medium",
        )

    def detect_low_pue(
        self,
        facility_id: str,
        current_pue: Decimal,
        threshold: Decimal = Decimal("1.3"),
    ) -> Optional[OptimizationRecommendation]:
        """Detect poor PUE (spec §16.2.2)."""
        if current_pue <= threshold:
            return None

        return OptimizationRecommendation(
            category="infrastructure",
            title="Cooling Set-Point Adjustment",
            description=f"Facility {facility_id} PUE is {current_pue} (above {threshold})",
            trigger_condition=f"PUE > {threshold} during mild weather",
            expected_savings="5-15% facility energy reduction",
            priority=RecommendationPriority.MEDIUM,
            timeframe=RecommendationTimeframe.SHORT_TERM,
            estimated_carbon_savings_kg=Decimal("300"),
            implementation_effort="low",
        )

    def detect_batch_inefficiency(
        self,
        workload_id: str,
        num_small_jobs: int,
        threshold: int = 5,
    ) -> Optional[OptimizationRecommendation]:
        """Detect multiple small inference jobs that could be consolidated."""
        if num_small_jobs < threshold:
            return None

        return OptimizationRecommendation(
            category="compute",
            title="Batch Inference Consolidation",
            description=f"{num_small_jobs} small inference jobs running sequentially",
            trigger_condition=f"Multiple small inference jobs running sequentially",
            expected_savings="15-30% via batching overhead elimination",
            priority=RecommendationPriority.HIGH,
            timeframe=RecommendationTimeframe.SHORT_TERM,
            estimated_carbon_savings_kg=Decimal("200"),
            implementation_effort="medium",
        )

    # ── Diagnosis Layer ────────────────────────────────────────────────

    def diagnose_carbon_hotspot(
        self,
        workload_emissions: dict[str, Decimal],
    ) -> list[dict]:
        """Identify top carbon-emitting workloads."""
        sorted_workloads = sorted(
            workload_emissions.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        total = sum(workload_emissions.values(), Decimal("0"))
        hotspots = []
        for workload_id, emissions in sorted_workloads[:5]:
            pct = (emissions / total * 100).quantize(Decimal("0.1")) if total > 0 else Decimal("0")
            hotspots.append({
                "workload_id": workload_id,
                "emissions_kg_co2e": emissions,
                "percentage_of_total": pct,
            })
        return hotspots

    # ── Recommendation Layer ────────────────────────────────────────────

    def generate_recommendations(
        self,
        workload_metrics: dict,
    ) -> list[OptimizationRecommendation]:
        """Generate all applicable recommendations for a workload."""
        recs = []

        # Check GPU utilization
        if "avg_gpu_utilization" in workload_metrics:
            rec = self.detect_low_gpu_utilization(
                workload_id=workload_metrics.get("workload_id", "unknown"),
                avg_utilization=workload_metrics["avg_gpu_utilization"],
            )
            if rec:
                recs.append(rec)

        # Check idle resources
        if "idle_minutes" in workload_metrics:
            rec = self.detect_idle_resources(
                resource_id=workload_metrics.get("resource_id", "unknown"),
                idle_minutes=workload_metrics["idle_minutes"],
            )
            if rec:
                recs.append(rec)

        # Check model sizing
        if "model_parameters" in workload_metrics and "task_complexity" in workload_metrics:
            rec = self.detect_oversized_model(
                workload_id=workload_metrics.get("workload_id", "unknown"),
                model_parameters=workload_metrics["model_parameters"],
                task_complexity=workload_metrics["task_complexity"],
            )
            if rec:
                recs.append(rec)

        # Check PUE
        if "pue" in workload_metrics:
            rec = self.detect_low_pue(
                facility_id=workload_metrics.get("facility_id", "unknown"),
                current_pue=workload_metrics["pue"],
            )
            if rec:
                recs.append(rec)

        # Check batch efficiency
        if "num_small_jobs" in workload_metrics:
            rec = self.detect_batch_inefficiency(
                workload_id=workload_metrics.get("workload_id", "unknown"),
                num_small_jobs=workload_metrics["num_small_jobs"],
            )
            if rec:
                recs.append(rec)

        self.recommendations.extend(recs)
        return recs

    # ── Carbon-Aware Scheduling ────────────────────────────────────────

    def make_scheduling_decision(
        self,
        workload_id: str,
        flexibility: WorkloadFlexibility,
        current_region: str,
        current_intensity: Decimal,
        region_intensities: dict[str, Decimal],
        forecast_intensities: dict[str, Decimal],
    ) -> SchedulingDecision:
        """
        Make carbon-aware scheduling decision per spec §16.4.
        
        Decision flow:
        1. Classify workload flexibility
        2. For flexible workloads, query carbon intensity forecast
        3. Evaluate migration options
        4. Select optimal: run now, delay, or migrate
        """
        # Hard real-time: always run now
        if flexibility == WorkloadFlexibility.HARD_REAL_TIME:
            return SchedulingDecision(
                workload_id=workload_id,
                flexibility=flexibility,
                decision="run_now",
                current_intensity=current_intensity,
                target_intensity=current_intensity,
                reasoning="Hard real-time workload — no delay permitted",
            )

        # Determine max delay based on flexibility
        max_delay = {
            WorkloadFlexibility.SOFT_REAL_TIME: 15,
            WorkloadFlexibility.NEAR_REAL_TIME: 120,
            WorkloadFlexibility.BATCH: 1440,
        }.get(flexibility, 0)

        # Find best region by carbon intensity
        best_region = min(region_intensities, key=lambda r: region_intensities[r])
        best_intensity = region_intensities[best_region]

        # Find best forecast window
        best_forecast_region = min(forecast_intensities, key=lambda r: forecast_intensities[r])
        best_forecast_intensity = forecast_intensities[best_forecast_region]

        # Decision logic
        if current_intensity <= best_forecast_intensity * Decimal("1.1"):
            # Current is close to best forecast — run now
            return SchedulingDecision(
                workload_id=workload_id,
                flexibility=flexibility,
                decision="run_now",
                current_intensity=current_intensity,
                target_intensity=current_intensity,
                reasoning=f"Current intensity ({current_intensity}) is near optimal",
            )
        elif best_forecast_intensity < best_intensity:
            # Forecast shows better window — delay
            delay = min(max_delay, 120)  # Default 2hr delay
            savings = ((current_intensity - best_forecast_intensity) / current_intensity * 100).quantize(Decimal("0.1"))
            return SchedulingDecision(
                workload_id=workload_id,
                flexibility=flexibility,
                decision="delay",
                delay_minutes=delay,
                current_intensity=current_intensity,
                target_intensity=best_forecast_intensity,
                carbon_savings_percent=savings,
                reasoning=f"Delay {delay}min for lower carbon intensity "
                          f"({current_intensity} → {best_forecast_intensity} g CO2e/kWh)",
            )
        else:
            # Another region is better — migrate
            savings = ((current_intensity - best_intensity) / current_intensity * 100).quantize(Decimal("0.1"))
            return SchedulingDecision(
                workload_id=workload_id,
                flexibility=flexibility,
                decision="migrate",
                target_region=best_region,
                current_intensity=current_intensity,
                target_intensity=best_intensity,
                carbon_savings_percent=savings,
                reasoning=f"Migrate to {best_region} for lower carbon intensity "
                          f"({current_intensity} → {best_intensity} g CO2e/kWh)",
            )

    # ── Verification Layer ─────────────────────────────────────────────

    def verify_optimization(
        self,
        recommendation_id: str,
        pre_implementation_emissions: Decimal,
        post_implementation_emissions: Decimal,
    ) -> dict:
        """Verify the effectiveness of an implemented optimization."""
        savings = pre_implementation_emissions - post_implementation_emissions
        savings_pct = (
            (savings / pre_implementation_emissions * 100).quantize(Decimal("0.1"))
            if pre_implementation_emissions > 0 else Decimal("0")
        )
        return {
            "recommendation_id": recommendation_id,
            "pre_implementation_kg_co2e": pre_implementation_emissions,
            "post_implementation_kg_co2e": post_implementation_emissions,
            "savings_kg_co2e": savings,
            "savings_percent": savings_pct,
            "verified": savings > 0,
            "verification_date": datetime.utcnow().isoformat(),
        }


# ── Green AI Recommendations ──────────────────────────────────────────

class GreenAIAdvisor:
    """Provides Green AI design recommendations per spec §19."""

    @staticmethod
    def get_architecture_recommendations() -> list[dict]:
        return [
            {
                "principle": "Start small",
                "recommendation": "Begin with smallest model that meets accuracy requirements",
                "impact": "50-90% energy reduction vs. oversized model",
            },
            {
                "principle": "Use efficient architectures",
                "recommendation": "Prefer MoE, linear attention over full attention",
                "impact": "30-70% inference energy reduction",
            },
            {
                "principle": "Leverage pre-trained models",
                "recommendation": "Fine-tune rather than train from scratch",
                "impact": "80-99% training energy reduction",
            },
            {
                "principle": "Task-specific models",
                "recommendation": "Use classification models for classification, not LLMs",
                "impact": "60-95% energy reduction",
            },
        ]

    @staticmethod
    def get_training_recommendations() -> list[dict]:
        return [
            {"practice": "Mixed-precision training", "savings": "20-35% training energy"},
            {"practice": "Gradient checkpointing", "savings": "10-20% (enables larger batches)"},
            {"practice": "Curriculum learning", "savings": "10-30% training time"},
            {"practice": "Early stopping", "savings": "20-50% training time"},
            {"practice": "Data deduplication", "savings": "5-15% training time"},
            {"practice": "Progressive resizing", "savings": "20-40% training time"},
            {"practice": "Carbon-aware scheduling", "savings": "15-40% carbon (same energy)"},
        ]

    @staticmethod
    def get_inference_recommendations() -> list[dict]:
        return [
            {"practice": "Dynamic batching", "savings": "30-60% inference energy"},
            {"practice": "KV-cache management", "savings": "25-50% inference energy"},
            {"practice": "Speculative decoding", "savings": "30-60% latency and energy"},
            {"practice": "Model quantization (INT8/INT4)", "savings": "30-50% inference energy"},
            {"practice": "Prompt caching", "savings": "40-80% for cached prefixes"},
            {"practice": "Early exit", "savings": "30-60% inference energy"},
            {"practice": "Request deduplication", "savings": "50-80% for duplicates"},
        ]

    @staticmethod
    def get_green_ai_checklist() -> list[str]:
        return [
            "Model size justified by task requirements (not oversized)",
            "Pre-trained model considered before training from scratch",
            "Energy-efficient architecture selected (MoE, linear attention, etc.)",
            "Mixed-precision training enabled",
            "Early stopping configured",
            "Training data deduplicated and curated",
            "Carbon-aware scheduling enabled for training",
            "Inference optimization applied (batching, caching, quantization)",
            "Model quantization evaluated for production",
            "Carbon label generated for the model",
            "EIA completed and score >= 60 (grade B)",
            "Environmental Owner assigned",
            "Decommissioning plan documented",
        ]


# ── Example Usage ─────────────────────────────────────────────────────

def demo_carbon_optimization():
    engine = CarbonOptimizationEngine()

    # Generate recommendations for a workload
    metrics = {
        "workload_id": "inference-cluster-us",
        "avg_gpu_utilization": Decimal("35"),
        "idle_minutes": 45,
        "model_parameters": 7_000_000_000,
        "task_complexity": "simple",
        "pue": Decimal("1.35"),
        "num_small_jobs": 8,
    }

    recs = engine.generate_recommendations(metrics)
    print(f"=== Generated {len(recs)} Recommendations ===")
    for rec in recs:
        print(f"\n  [{rec.priority.value.upper()}] {rec.title}")
        print(f"    {rec.description}")
        print(f"    Expected savings: {rec.expected_savings}")
        print(f"    Timeframe: {rec.timeframe.value}")

    # Carbon-aware scheduling decision
    decision = engine.make_scheduling_decision(
        workload_id="batch-training-job-123",
        flexibility=WorkloadFlexibility.BATCH,
        current_region="us-east-1",
        current_intensity=Decimal("350"),
        region_intensities={
            "us-east-1": Decimal("350"),
            "us-west-2": Decimal("150"),
            "eu-west-1": Decimal("200"),
        },
        forecast_intensities={
            "us-east-1_2hr": Decimal("180"),
            "us-east-1_6hr": Decimal("420"),
        },
    )
    print(f"\n=== Scheduling Decision ===")
    print(f"  Decision: {decision.decision}")
    print(f"  Reasoning: {decision.reasoning}")
    if decision.carbon_savings_percent > 0:
        print(f"  Carbon savings: {decision.carbon_savings_percent}%")

    # Green AI recommendations
    advisor = GreenAIAdvisor()
    print(f"\n=== Green AI Checklist ({len(advisor.get_green_ai_checklist())} items) ===")
    for item in advisor.get_green_ai_checklist():
        print(f"  [ ] {item}")

    return engine


if __name__ == "__main__":
    demo_carbon_optimization()
```

---

## 7. Carbon Offset Management (Python)

Implements the mitigation hierarchy (Avoid → Reduce → Replace → Offset → Remove) and offset portfolio management.

```python
# carbon_offset_management.py
"""
GRC_Claw Carbon Offset Management Module
Implements carbon offset procurement, retirement tracking, portfolio management,
and net emissions calculation per spec §20.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from models import CarbonOffset


class OffsetPortfolio:
    """
    Manages GRC_Claw's carbon offset portfolio with quality criteria,
    vintage policy, and geographic distribution per spec §20.6.
    """

    # Portfolio allocation targets per spec §20.6.1
    TARGET_ALLOCATION = {
        "removal_tech": Decimal("50"),    # 50% technology-based removal
        "removal_nature": Decimal("30"),  # 30% nature-based removal
        "avoidance_reduction": Decimal("20"),  # 20% avoidance/reduction
    }

    # Vintage policy per spec §20.6.2
    VINTAGE_LIMITS = {
        0: Decimal("40"),    # Current year: max 40%
        1: Decimal("40"),    # 1-3 years: max 40%
        3: Decimal("15"),    # 3-5 years: max 15%
        5: Decimal("5"),     # >5 years: max 5%
    }

    # Geographic distribution per spec §20.6.3
    GEO_TARGETS = {
        "global": Decimal("60"),
        "operating_regions": Decimal("30"),
        "developing_countries": Decimal("10"),
    }

    def __init__(self):
        self.offsets: dict[str, CarbonOffset] = {}
        self._ledger_path = Path("offset_ledger.jsonl")
        self._last_hash = "0" * 64

    def add_offset(self, offset: CarbonOffset) -> CarbonOffset:
        """Add a carbon offset to the portfolio with hash chaining."""
        # Compute hash for audit trail
        content = {
            "offset_id": offset.offset_id,
            "project_name": offset.project_name,
            "registry": offset.registry,
            "credits_purchased": str(offset.credits_purchased),
            "vintage": offset.vintage,
            "timestamp": datetime.utcnow().isoformat(),
            "previous_hash": self._last_hash,
        }
        offset.evidence_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()
        self._last_hash = offset.evidence_hash

        self.offsets[offset.offset_id] = offset
        self._persist(offset)
        return offset

    def _persist(self, offset: CarbonOffset):
        with open(self._ledger_path, "a") as f:
            f.write(json.dumps(offset.model_dump(), default=str) + "\n")

    def retire_offset(self, offset_id: str, amount: Decimal) -> Optional[CarbonOffset]:
        """Retire a portion or all of an offset."""
        if offset_id not in self.offsets:
            return None

        offset = self.offsets[offset_id]
        if offset.status == "retired":
            return None

        offset.credits_retired += amount
        if offset.credits_retired >= offset.credits_purchased:
            offset.status = "retired"
            offset.retirement_date = datetime.utcnow()

        return offset

    def get_portfolio_summary(self) -> dict:
        """Get portfolio composition and quality metrics."""
        total_purchased = sum(o.credits_purchased for o in self.offsets.values())
        total_retired = sum(o.credits_retired for o in self.offsets.values())

        by_category: dict[str, Decimal] = defaultdict(Decimal)
        by_registry: dict[str, Decimal] = defaultdict(Decimal)
        by_vintage: dict[int, Decimal] = defaultdict(Decimal)

        for offset in self.offsets.values():
            by_category[offset.category] += offset.credits_purchased
            by_registry[offset.registry] += offset.credits_purchased
            by_vintage[offset.vintage] += offset.credits_purchased

        return {
            "total_offsets": len(self.offsets),
            "total_purchased_tco2e": total_purchased,
            "total_retired_tco2e": total_retired,
            "remaining_tco2e": total_purchased - total_retired,
            "by_category": {k: v for k, v in by_category.items()},
            "by_registry": {k: v for k, v in by_registry.items()},
            "by_vintage": {k: v for k, v in by_vintage.items()},
            "allocation_check": self._check_allocation_targets(by_category, total_purchased),
        }

    def _check_allocation_targets(
        self,
        by_category: dict[str, Decimal],
        total: Decimal,
    ) -> dict:
        """Check if portfolio meets allocation targets."""
        if total == 0:
            return {"status": "empty", "gaps": []}

        gaps = []
        for category, target_pct in self.TARGET_ALLOCATION.items():
            actual = by_category.get(category, Decimal("0"))
            actual_pct = (actual / total * 100).quantize(Decimal("0.1"))
            if actual_pct < target_pct:
                gaps.append({
                    "category": category,
                    "target_pct": target_pct,
                    "actual_pct": actual_pct,
                    "gap_pct": target_pct - actual_pct,
                })

        return {
            "status": "compliant" if not gaps else "non_compliant",
            "gaps": gaps,
        }

    def verify_quality_criteria(self, offset_id: str) -> dict:
        """Verify an offset meets all quality criteria per spec §20.4."""
        if offset_id not in self.offsets:
            return {"valid": False, "errors": ["Offset not found"]}

        offset = self.offsets[offset_id]
        criteria = {
            "additionality": True,      # Would be verified via project documentation
            "permanence": offset.category.startswith("removal"),
            "no_double_counting": offset.registry in [
                "Verra", "Gold Standard", "Puro.earth", "Climeworks",
                "Charm Industrial", "Isometric", "ACR", "CAR",
            ],
            "measurement": True,        # Verified via methodology review
            "verification": True,       # Verified via VVB audit
            "co_benefits": True,        # Assessed per project
            "leakage": True,            # Assessed per project
            "transparency": True,       # Registry public listing
        }

        return {
            "offset_id": offset_id,
            "project_name": offset.project_name,
            "valid": all(criteria.values()),
            "criteria": criteria,
            "quality_score": offset.quality_score,
        }


class NetEmissionsCalculator:
    """
    Calculates net emissions per spec §20.8.
    
    Net Emissions = Gross Emissions - Verified Reductions - Retired Offsets
    """

    def __init__(self, portfolio: OffsetPortfolio):
        self.portfolio = portfolio

    def calculate_net_emissions(
        self,
        gross_scope1: Decimal,
        gross_scope2_location: Decimal,
        gross_scope3: Decimal,
        verified_reductions: Decimal = Decimal("0"),
    ) -> dict:
        """Calculate net emissions after reductions and offsets."""
        gross_total = gross_scope1 + gross_scope2_location + gross_scope3
        total_retired = sum(
            o.credits_retired for o in self.portfolio.offsets.values()
        )

        net_emissions = gross_total - verified_reductions - total_retired

        return {
            "gross_emissions_kg_co2e": {
                "scope_1": gross_scope1,
                "scope_2_location": gross_scope2_location,
                "scope_3": gross_scope3,
                "total": gross_total,
            },
            "verified_reductions_kg_co2e": verified_reductions,
            "retired_offsets_kg_co2e": total_retired,
            "net_emissions_kg_co2e": net_emissions,
            "net_zero_achieved": net_emissions <= 0,
            "net_negative_achieved": net_emissions < 0,
            "calculation_date": datetime.utcnow().isoformat(),
        }


class OffsetProcurementWorkflow:
    """
    Manages the offset procurement process per spec §20.7.
    
    Workflow: Calculate Residual → Determine Need → Source Credits → 
              Quality Assurance → Retire Credits → Report & Verify
    """

    def __init__(self, portfolio: OffsetPortfolio):
        self.portfolio = portfolio
        self.procurement_log: list[dict] = []

    def calculate_residual_emissions(
        self,
        total_emissions: Decimal,
        reductions: Decimal,
        renewable_energy: Decimal,
        avoidance: Decimal,
    ) -> Decimal:
        """Calculate residual emissions that need offsetting."""
        residual = total_emissions - reductions - renewable_energy - avoidance
        return max(Decimal("0"), residual)

    def determine_offset_need(
        self,
        residual_emissions: Decimal,
        budget_usd: Decimal,
        quality_requirements: dict,
    ) -> dict:
        """Determine offset procurement needs based on residual emissions."""
        # Estimate cost per credit based on quality
        avg_price = Decimal("15")  # Default $15/tCO2e
        if quality_requirements.get("preferred") == "removal_tech":
            avg_price = Decimal("50")
        elif quality_requirements.get("preferred") == "removal_nature":
            avg_price = Decimal("20")

        max_credits = budget_usd / avg_price if avg_price > 0 else Decimal("0")

        return {
            "residual_emissions_tco2e": residual_emissions / 1000,
            "budget_usd": budget_usd,
            "estimated_price_per_credit": avg_price,
            "max_credits_affordable": max_credits,
            "funding_shortfall": residual_emissions / 1000 > max_credits,
            "quality_requirements": quality_requirements,
        }

    def source_credits(
        self,
        registry: str,
        standard: str,
        category: str,
        vintage: int,
        credits_needed: Decimal,
        max_price: Decimal,
    ) -> list[CarbonOffset]:
        """
        Source carbon credits from approved registries.
        In production, this would integrate with Verra/Gold Standard/Puro.earth APIs.
        """
        # Simulated sourcing — replace with actual registry API calls
        offset = CarbonOffset(
            offset_id=str(uuid.uuid4()),
            project_name=f"{registry} Project — {category}",
            registry=registry,
            standard=standard,
            category=category,
            vintage=vintage,
            credits_purchased=credits_needed,
            price_per_credit=max_price,
            region="Global",
            quality_score=85,
        )
        self.portfolio.add_offset(offset)
        return [offset]

    def execute_procurement(
        self,
        total_emissions: Decimal,
        reductions: Decimal,
        renewable_energy: Decimal,
        avoidance: Decimal,
        budget_usd: Decimal,
    ) -> dict:
        """Execute the full procurement workflow."""
        # Step 1: Calculate residual
        residual = self.calculate_residual_emissions(
            total_emissions, reductions, renewable_energy, avoidance
        )

        # Step 2: Determine need
        need = self.determine_offset_need(residual, budget_usd, {
            "preferred": "removal_tech",
            "min_quality_score": 80,
        })

        # Step 3: Source credits (simulated)
        sourced = []
        if need["max_credits_affordable"] > 0:
            sourced = self.source_credits(
                registry="Puro.earth",
                standard="CORC",
                category="removal_tech",
                vintage=datetime.utcnow().year,
                credits_needed=need["max_credits_affordable"],
                max_price=need["estimated_price_per_credit"],
            )

        # Step 4: Retire credits
        for offset in sourced:
            self.portfolio.retire_offset(offset.offset_id, offset.credits_purchased)

        result = {
            "workflow_id": str(uuid.uuid4()),
            "residual_emissions_tco2e": residual / 1000,
            "credits_sourced": len(sourced),
            "credits_retired_tco2e": sum(o.credits_retired for o in sourced),
            "budget_used_usd": sum(
                o.credits_purchased * o.price_per_credit for o in sourced
            ),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.procurement_log.append(result)
        return result


# ── Example Usage ─────────────────────────────────────────────────────

def demo_offset_management():
    portfolio = OffsetPortfolio()

    # Add offsets to portfolio
    offsets = [
        CarbonOffset(
            offset_id=str(uuid.uuid4()),
            project_name="Climeworks DAC Facility",
            registry="Climeworks",
            standard="DAC",
            category="removal_tech",
            vintage=2025,
            credits_purchased=Decimal("10000"),
            price_per_credit=Decimal("50"),
            region="Iceland",
            quality_score=95,
        ),
        CarbonOffset(
            offset_id=str(uuid.uuid4()),
            project_name="Reforestation Project Brazil",
            registry="Verra",
            standard="VCS",
            category="removal_nature",
            vintage=2024,
            credits_purchased=Decimal("20000"),
            price_per_credit=Decimal("15"),
            region="Brazil",
            quality_score=80,
        ),
        CarbonOffset(
            offset_id=str(uuid.uuid4()),
            project_name="Wind Farm India",
            registry="Gold Standard",
            standard="GS VER",
            category="avoidance_reduction",
            vintage=2025,
            credits_purchased=Decimal("15000"),
            price_per_credit=Decimal("10"),
            region="India",
            quality_score=75,
        ),
    ]

    for offset in offsets:
        portfolio.add_offset(offset)

    # Get portfolio summary
    summary = portfolio.get_portfolio_summary()
    print("=== Offset Portfolio Summary ===")
    print(f"  Total offsets: {summary['total_offsets']}")
    print(f"  Total purchased: {summary['total_purchased_tco2e']} tCO2e")
    print(f"  Total retired: {summary['total_retired_tco2e']} tCO2e")
    print(f"  Remaining: {summary['remaining_tco2e']} tCO2e")
    print(f"  Allocation status: {summary['allocation_check']['status']}")

    # Calculate net emissions
    calculator = NetEmissionsCalculator(portfolio)
    net = calculator.calculate_net_emissions(
        gross_scope1=Decimal("50000"),       # 50 t
        gross_scope2_location=Decimal("100000"),  # 100 t
        gross_scope3=Decimal("150000"),      # 150 t
        verified_reductions=Decimal("20000"),     # 20 t
    )
    print(f"\n=== Net Emissions ===")
    print(f"  Gross: {net['gross_emissions_kg_co2e']['total'] / 1000} tCO2e")
    print(f"  Reductions: {net['verified_reductions_kg_co2e'] / 1000} tCO2e")
    print(f"  Retired offsets: {net['retired_offsets_kg_co2e'] / 1000} tCO2e")
    print(f"  Net emissions: {net['net_emissions_kg_co2e'] / 1000} tCO2e")
    print(f"  Net-zero achieved: {net['net_zero_achieved']}")

    # Execute procurement workflow
    workflow = OffsetProcurementWorkflow(portfolio)
    result = workflow.execute_procurement(
        total_emissions=Decimal("300000"),
        reductions=Decimal("20000"),
        renewable_energy=Decimal("50000"),
        avoidance=Decimal("10000"),
        budget_usd=Decimal("500000"),
    )
    print(f"\n=== Procurement Workflow ===")
    print(f"  Residual: {result['residual_emissions_tco2e']} tCO2e")
    print(f"  Credits sourced: {result['credits_sourced']}")
    print(f"  Credits retired: {result['credits_retired_tco2e']} tCO2e")
    print(f"  Budget used: ${result['budget_used_usd']}")

    return portfolio


if __name__ == "__main__":
    demo_offset_management()
```

---

## 8. Environmental Compliance (Python)

Implements Environmental Compliance Automation (ECA) with regulatory monitoring, automated checks, and compliance calendar management.

```python
# environmental_compliance.py
"""
GRC_Claw Environmental Compliance Automation Module
Implements continuous regulatory monitoring, automated compliance checks,
compliance calendar management, and evidence automation per spec §21.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional

from models import ComplianceRule


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AT_RISK = "at_risk"
    PENDING = "pending"


class ComplianceSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceCheckResult:
    """Result of a single compliance check."""
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    severity: ComplianceSeverity = ComplianceSeverity.LOW
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence: dict = field(default_factory=dict)
    remediation_required: bool = False
    remediation_deadline: Optional[date] = None


@dataclass
class ComplianceDeadline:
    """A tracked compliance deadline."""
    deadline_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    deadline_date: date = field(default_factory=date.today)
    regulation: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    reminder_dates: list[date] = field(default_factory=list)
    escalation_path: list[str] = field(default_factory=list)
    evidence_required: list[str] = field(default_factory=list)
    completed: bool = False
    completed_date: Optional[date] = None


@dataclass
class RegulatoryChange:
    """A detected regulatory change."""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation: str = ""
    jurisdiction: str = ""
    title: str = ""
    description: str = ""
    effective_date: Optional[date] = None
    detected_date: datetime = field(default_factory=datetime.utcnow)
    impact_assessment: str = ""
    affected_systems: list[str] = field(default_factory=list)
    compliance_gap: str = ""
    implementation_effort: str = ""    # "low", "medium", "high"
    roadmap: list[dict] = field(default_factory=list)
    status: str = "detected"            # "detected", "assessed", "planned", "implemented"


class ComplianceRulesEngine:
    """
    Evaluates environmental compliance rules continuously.
    Rules are defined as code per spec §21.3.2.
    """

    def __init__(self):
        self.rules: dict[str, ComplianceRule] = {}
        self._load_default_rules()

    def _load_default_rules(self):
        """Load default compliance rules from spec §21.3.2."""
        defaults = [
            ComplianceRule(
                rule_id="eu-csrd-reporting-deadline",
                name="EU CSRD Reporting Deadline",
                description="EU CSRD sustainability statement must be filed",
                condition="date >= '2027-01-01' and csrd_report_status != 'filed'",
                action="alert",
                severity="critical",
                notify=["cso", "sustainability-team", "legal"],
                deadline=date(2027, 6, 30),
            ),
            ComplianceRule(
                rule_id="sec-climate-disclosure",
                name="SEC Climate Disclosure",
                description="SEC climate-related disclosure must be filed",
                condition="date >= '2027-01-01' and sec_filing_status != 'filed'",
                action="alert",
                severity="critical",
                notify=["cfo", "legal", "sustainability-team"],
                deadline=date(2027, 4, 15),
            ),
            ComplianceRule(
                rule_id="carbon-budget-exceeded",
                name="Carbon Budget Exceeded",
                description="Workload projected emissions exceed carbon budget",
                condition="workload.projected_emissions > workload.carbon_budget",
                action="block",
                severity="critical",
                notify=["ai-engineering", "environmental-engineering"],
            ),
            ComplianceRule(
                rule_id="renewable-energy-minimum",
                name="Renewable Energy Minimum",
                description="Facility renewable energy percentage below threshold",
                condition="facility.renewable_percentage < 0.60",
                action="alert",
                severity="high",
                notify=["procurement", "infrastructure"],
            ),
            ComplianceRule(
                rule_id="eia-required",
                name="EIA Required",
                description="Environmental Impact Assessment required for high-impact deployments",
                condition="deployment.eia_completed == false and deployment.impact_level in ['high', 'critical']",
                action="block",
                severity="critical",
                notify=["ai-engineering", "sustainability-team"],
            ),
            ComplianceRule(
                rule_id="pue-threshold",
                name="PUE Threshold",
                description="Data center PUE above acceptable threshold",
                condition="datacenter.pue > 1.40",
                action="alert",
                severity="medium",
                notify=["infrastructure", "energy-engineering"],
            ),
            ComplianceRule(
                rule_id="offset-retirement-shortfall",
                name="Offset Retirement Shortfall",
                description="Quarterly offset retirement below target",
                condition="quarterly.offset_retired < quarterly.offset_required * 0.90",
                action="alert",
                severity="high",
                notify=["sustainability-team", "cso"],
            ),
        ]
        for rule in defaults:
            self.rules[rule.rule_id] = rule

    def add_rule(self, rule: ComplianceRule) -> None:
        self.rules[rule.rule_id] = rule

    def evaluate_rule(self, rule_id: str, context: dict) -> ComplianceCheckResult:
        """Evaluate a single rule against the provided context."""
        if rule_id not in self.rules:
            return ComplianceCheckResult(
                rule_id=rule_id,
                rule_name="Unknown",
                status=ComplianceStatus.NON_COMPLIANT,
                details=f"Rule '{rule_id}' not found",
            )

        rule = self.rules[rule_id]

        # Simple condition evaluation (in production, use OPA/Rego or similar)
        triggered = self._evaluate_condition(rule.condition, context)

        if triggered:
            return ComplianceCheckResult(
                rule_id=rule_id,
                rule_name=rule.name,
                status=ComplianceStatus.NON_COMPLIANT,
                severity=ComplianceSeverity(rule.severity),
                details=f"Rule triggered: {rule.description}",
                remediation_required=rule.action == "block",
                remediation_deadline=rule.deadline,
                evidence={"condition": rule.condition, "context": context},
            )

        return ComplianceCheckResult(
            rule_id=rule_id,
            rule_name=rule.name,
            status=ComplianceStatus.COMPLIANT,
            severity=ComplianceSeverity(rule.severity),
            details="Rule satisfied",
        )

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """
        Simple condition evaluator.
        In production, this would use OPA/Rego or a proper rule engine.
        """
        # Handle specific known conditions
        if "workload.projected_emissions > workload.carbon_budget" in condition:
            proj = context.get("projected_emissions", Decimal("0"))
            budget = context.get("carbon_budget", Decimal("0"))
            return proj > budget

        if "facility.renewable_percentage < 0.60" in condition:
            pct = context.get("renewable_percentage", Decimal("1"))
            return pct < Decimal("0.60")

        if "datacenter.pue > 1.40" in condition:
            pue = context.get("pue", Decimal("1"))
            return pue > Decimal("1.40")

        if "deployment.eia_completed == false" in condition:
            eia = context.get("eia_completed", True)
            impact = context.get("impact_level", "low")
            return not eia and impact in ("high", "critical")

        if "quarterly.offset_retired < quarterly.offset_required * 0.90" in condition:
            retired = context.get("offset_retired", Decimal("0"))
            required = context.get("offset_required", Decimal("0"))
            return retired < required * Decimal("0.90")

        # Date-based conditions
        if "date >= '2027-01-01'" in condition and "csrd_report_status" in condition:
            today = date.today()
            status = context.get("csrd_report_status", "")
            return today >= date(2027, 1, 1) and status != "filed"

        if "date >= '2027-01-01'" in condition and "sec_filing_status" in condition:
            today = date.today()
            status = context.get("sec_filing_status", "")
            return today >= date(2027, 1, 1) and status != "filed"

        return False

    def evaluate_all(self, context: dict) -> list[ComplianceCheckResult]:
        """Evaluate all rules against the provided context."""
        return [self.evaluate_rule(rule_id, context) for rule_id in self.rules]


class ComplianceCalendar:
    """
    Tracks all environmental compliance deadlines with reminder schedules
    per spec §21.5.
    """

    # Reminder schedules per deadline type (days before deadline)
    REMINDER_SCHEDULES = {
        "regulatory_filing": [90, 60, 30, 14, 7, 3, 1],
        "internal_report": [60, 30, 14, 7, 3, 1],
        "offset_purchase": [60, 30, 14, 7],
        "eia_completion": [30, 14, 7, 3, 1],
        "audit_preparation": [90, 60, 30, 14, 7],
        "target_review": [90, 60, 30],
    }

    ESCALATION_PATHS = {
        "regulatory_filing": ["analyst", "manager", "cso", "ceo"],
        "internal_report": ["analyst", "manager", "cso"],
        "offset_purchase": ["analyst", "sustainability-team", "cso"],
        "eia_completion": ["engineer", "manager", "cso"],
        "audit_preparation": ["analyst", "manager", "cso", "auditor"],
        "target_review": ["analyst", "cso", "board"],
    }

    def __init__(self):
        self.deadlines: dict[str, ComplianceDeadline] = {}

    def add_deadline(
        self,
        name: str,
        deadline_date: date,
        regulation: str,
        deadline_type: str = "regulatory_filing",
        description: str = "",
    ) -> ComplianceDeadline:
        """Add a compliance deadline with automatic reminder scheduling."""
        reminders = [
            deadline_date - timedelta(days=d)
            for d in self.REMINDER_SCHEDULES.get(deadline_type, [30, 7, 1])
        ]

        deadline = ComplianceDeadline(
            name=name,
            description=description,
            deadline_date=deadline_date,
            regulation=regulation,
            reminder_dates=reminders,
            escalation_path=self.ESCALATION_PATHS.get(deadline_type, ["analyst", "manager"]),
        )
        self.deadlines[deadline.deadline_id] = deadline
        return deadline

    def get_upcoming_deadlines(self, days: int = 90) -> list[ComplianceDeadline]:
        """Get deadlines within the specified number of days."""
        today = date.today()
        cutoff = today + timedelta(days=days)
        return [
            d for d in self.deadlines.values()
            if not d.completed and today <= d.deadline_date <= cutoff
        ]

    def get_overdue_deadlines(self) -> list[ComplianceDeadline]:
        """Get all overdue deadlines."""
        today = date.today()
        return [
            d for d in self.deadlines.values()
            if not d.completed and d.deadline_date < today
        ]

    def get_reminders_due(self) -> list[dict]:
        """Get reminders that are due today."""
        today = date.today()
        reminders = []
        for deadline in self.deadlines.values():
            if deadline.completed:
                continue
            for reminder_date in deadline.reminder_dates:
                if reminder_date == today:
                    days_remaining = (deadline.deadline_date - today).days
                    reminders.append({
                        "deadline_id": deadline.deadline_id,
                        "name": deadline.name,
                        "deadline_date": deadline.deadline_date,
                        "days_remaining": days_remaining,
                        "escalation_path": deadline.escalation_path,
                        "regulation": deadline.regulation,
                    })
        return reminders

    def complete_deadline(self, deadline_id: str) -> Optional[ComplianceDeadline]:
        """Mark a deadline as completed."""
        if deadline_id not in self.deadlines:
            return None
        deadline = self.deadlines[deadline_id]
        deadline.completed = True
        deadline.completed_date = date.today()
        deadline.status = ComplianceStatus.COMPLIANT
        return deadline


class RegulatoryWatchService:
    """
    Monitors environmental regulations across all operating jurisdictions
    per spec §21.2.1.
    """

    # Monitoring sources per spec §21.2.1
    MONITORING_SOURCES = {
        "EU Official Journal": {"method": "RSS + NLP parsing", "frequency": "daily"},
        "Federal Register (US)": {"method": "API + keyword matching", "frequency": "daily"},
        "State registers (US)": {"method": "Web scraping + API", "frequency": "weekly"},
        "ISO standards body": {"method": "Email + portal monitoring", "frequency": "weekly"},
        "Industry associations": {"method": "Newsletter + report monitoring", "frequency": "weekly"},
        "Law firm alerts": {"method": "Subscription feeds", "frequency": "real-time"},
    }

    # Emerging regulations to monitor per spec §13.2
    EMERGING_REGULATIONS = [
        {
            "regulation": "EU AI Act environmental requirements",
            "jurisdiction": "EU/EEA",
            "expected": "2027",
            "relevance": "May add environmental requirements for AI systems",
        },
        {
            "regulation": "EU Energy Efficiency Directive recast",
            "jurisdiction": "EU/EEA",
            "expected": "2027",
            "relevance": "Data center reporting requirements",
        },
        {
            "regulation": "California Climate Corporate Data Accountability Act",
            "jurisdiction": "California, US",
            "expected": "2027",
            "relevance": "Scope 3 emissions disclosure",
        },
        {
            "regulation": "ISSB IFRS S2",
            "jurisdiction": "Global",
            "expected": "2026",
            "relevance": "Climate-related disclosures",
        },
        {
            "regulation": "EU Green Claims Directive",
            "jurisdiction": "EU/EEA",
            "expected": "2026",
            "relevance": "Environmental marketing claims",
        },
    ]

    def __init__(self):
        self.detected_changes: list[RegulatoryChange] = []

    def detect_regulatory_change(
        self,
        regulation: str,
        jurisdiction: str,
        title: str,
        description: str,
        effective_date: Optional[date] = None,
    ) -> RegulatoryChange:
        """Record a detected regulatory change and trigger impact assessment."""
        change = RegulatoryChange(
            regulation=regulation,
            jurisdiction=jurisdiction,
            title=title,
            description=description,
            effective_date=effective_date,
        )
        self.detected_changes.append(change)
        return change

    def assess_impact(
        self,
        change_id: str,
        affected_systems: list[str],
        compliance_gap: str,
        implementation_effort: str,
    ) -> Optional[RegulatoryChange]:
        """Assess the impact of a regulatory change."""
        for change in self.detected_changes:
            if change.change_id == change_id:
                change.affected_systems = affected_systems
                change.compliance_gap = compliance_gap
                change.implementation_effort = implementation_effort
                change.status = "assessed"
                return change
        return None

    def get_pending_changes(self) -> list[RegulatoryChange]:
        """Get all regulatory changes that need action."""
        return [c for c in self.detected_changes if c.status != "implemented"]


class EnvironmentalComplianceEngine:
    """
    Unified compliance engine that orchestrates all compliance activities.
    """

    def __init__(self):
        self.rules_engine = ComplianceRulesEngine()
        self.calendar = ComplianceCalendar()
        self.watch_service = RegulatoryWatchService()
        self.check_history: list[ComplianceCheckResult] = []

    def run_compliance_check(self, context: dict) -> list[ComplianceCheckResult]:
        """Run all compliance checks against the current context."""
        results = self.rules_engine.evaluate_all(context)
        self.check_history.extend(results)
        return results

    def get_compliance_summary(self) -> dict:
        """Get overall compliance status summary."""
        if not self.check_history:
            return {"status": "no_data", "message": "No compliance checks run yet"}

        total = len(self.check_history)
        compliant = sum(1 for r in self.check_history if r.status == ComplianceStatus.COMPLIANT)
        non_compliant = sum(1 for r in self.check_history if r.status == ComplianceStatus.NON_COMPLIANT)
        at_risk = sum(1 for r in self.check_history if r.status == ComplianceStatus.AT_RISK)

        overdue = self.calendar.get_overdue_deadlines()
        upcoming = self.calendar.get_upcoming_deadlines(90)
        reminders = self.calendar.get_reminders_due()
        pending_changes = self.watch_service.get_pending_changes()

        return {
            "overall_status": ComplianceStatus.COMPLIANT.value if non_compliant == 0 else ComplianceStatus.NON_COMPLIANT.value,
            "check_summary": {
                "total_checks": total,
                "compliant": compliant,
                "non_compliant": non_compliant,
                "at_risk": at_risk,
                "compliance_rate": round(compliant / total * 100, 1) if total > 0 else 0,
            },
            "deadlines": {
                "overdue": len(overdue),
                "upcoming_90d": len(upcoming),
                "reminders_due_today": len(reminders),
            },
            "regulatory_changes": {
                "pending": len(pending_changes),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def generate_compliance_report(self) -> str:
        """Generate a compliance status report."""
        summary = self.get_compliance_summary()
        lines = [
            "# GRC_Claw Environmental Compliance Report",
            "",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ",
            f"**Overall Status:** {summary['overall_status'].upper()}  ",
            "",
            "## Compliance Check Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Checks | {summary['check_summary']['total_checks']} |",
            f"| Compliant | {summary['check_summary']['compliant']} |",
            f"| Non-Compliant | {summary['check_summary']['non_compliant']} |",
            f"| At Risk | {summary['check_summary']['at_risk']} |",
            f"| Compliance Rate | {summary['check_summary']['compliance_rate']}% |",
            "",
            "## Deadlines",
            "",
            f"- Overdue: {summary['deadlines']['overdue']}",
            f"- Upcoming (90 days): {summary['deadlines']['upcoming_90d']}",
            f"- Reminders due today: {summary['deadlines']['reminders_due_today']}",
            "",
            "## Regulatory Changes",
            "",
            f"- Pending changes: {summary['regulatory_changes']['pending']}",
            "",
            "---",
            "*Generated by GRC_Claw Environmental Compliance Automation Engine*",
        ]
        return "\n".join(lines)


# ── Example Usage ─────────────────────────────────────────────────────

def demo_compliance():
    engine = EnvironmentalComplianceEngine()

    # Add compliance deadlines
    engine.calendar.add_deadline(
        name="EU CSRD Statement Filing",
        deadline_date=date(2027, 6, 30),
        regulation="EU CSRD",
        deadline_type="regulatory_filing",
        description="Annual CSRD sustainability statement filing",
    )
    engine.calendar.add_deadline(
        name="SEC Climate Disclosure",
        deadline_date=date(2027, 4, 15),
        regulation="SEC",
        deadline_type="regulatory_filing",
        description="Annual SEC climate-related disclosure",
    )
    engine.calendar.add_deadline(
        name="Q4 Offset Retirement",
        deadline_date=date(2026, 12, 31),
        regulation="Internal",
        deadline_type="offset_purchase",
        description="Q4 carbon offset retirement target",
    )

    # Run compliance checks
    context = {
        "projected_emissions": Decimal("5000"),
        "carbon_budget": Decimal("4000"),
        "renewable_percentage": Decimal("0.55"),
        "pue": Decimal("1.35"),
        "eia_completed": False,
        "impact_level": "high",
        "offset_retired": Decimal("8000"),
        "offset_required": Decimal("10000"),
        "csrd_report_status": "not_filed",
        "sec_filing_status": "not_filed",
    }

    results = engine.run_compliance_check(context)
    print("=== Compliance Check Results ===")
    for result in results:
        status_icon = "✓" if result.status == ComplianceStatus.COMPLIANT else "✗"
        print(f"  {status_icon} [{result.severity.value.upper()}] {result.rule_name}: {result.status.value}")
        if result.remediation_required:
            print(f"    ⚠ Remediation required by {result.remediation_deadline}")

    # Get compliance summary
    summary = engine.get_compliance_summary()
    print(f"\n=== Compliance Summary ===")
    print(f"  Overall status: {summary['overall_status']}")
    print(f"  Compliance rate: {summary['check_summary']['compliance_rate']}%")
    print(f"  Overdue deadlines: {summary['deadlines']['overdue']}")
    print(f"  Upcoming (90d): {summary['deadlines']['upcoming_90d']}")

    # Generate report
    report = engine.generate_compliance_report()
    print(f"\n{'='*60}")
    print(report)

    return engine


if __name__ == "__main__":
    demo_compliance()
```

---

## 9. Quick Start & Deployment

### 9.1 Running All Modules

```bash
# Run each module independently
python carbon_tracking.py
python energy_monitoring.py
python sustainability_reporting.py
python environmental_impact_assessment.py
python carbon_optimization.py
python carbon_offset_management.py
python environmental_compliance.py
```

### 9.2 Integration Example

```python
# integration_example.py
"""Example of integrating all environmental governance modules."""

from carbon_tracking import CarbonAccountingEngine
from energy_monitoring import EnergyMonitoringSystem, GPUPowerCollector
from sustainability_reporting import SustainabilityReportingEngine
from environmental_impact_assessment import EIAManager, LifeCycleInventoryItem, LifeCycleStage, ImpactCategory
from carbon_optimization import CarbonOptimizationEngine
from carbon_offset_management import OffsetPortfolio, NetEmissionsCalculator
from environmental_compliance import EnvironmentalComplianceEngine
from decimal import Decimal


def run_full_environmental_governance():
    """Run all environmental governance modules in an integrated workflow."""

    # 1. Carbon Tracking
    print("=" * 60)
    print("1. CARBON TRACKING")
    print("=" * 60)
    carbon_engine = CarbonAccountingEngine()
    carbon_engine.calculate_scope1(
        facility_id="dc-us-east-1", source="generator",
        activity_data=Decimal("500"), activity_unit="liters",
        emission_factor_id="diesel-2024",
    )
    carbon_engine.calculate_scope2_location_based(
        facility_id="dc-us-east-1", electricity_kwh=Decimal("10000"),
        grid_factor_id="grid-us-2024",
    )
    summary = carbon_engine.get_scope_summary()
    print(f"Total emissions: {summary['total_kg_co2e']} kg CO2e")

    # 2. Energy Monitoring
    print("\n" + "=" * 60)
    print("2. ENERGY MONITORING")
    print("=" * 60)
    energy_system = EnergyMonitoringSystem()
    gpu_collector = GPUPowerCollector(energy_system)
    gpu_collector.collect_reading(
        facility_id="dc-us-east-1", workload_id="training-run-47",
        energy_kwh=Decimal("125.5"), it_equipment_kwh=Decimal("100.0"),
    )
    metrics = energy_system.get_facility_metrics("dc-us-east-1")
    print(f"Facility metrics: {metrics['total_energy_kwh']} kWh total")

    # 3. Sustainability Reporting
    print("\n" + "=" * 60)
    print("3. SUSTAINABILITY REPORTING")
    print("=" * 60)
    reporting = SustainabilityReportingEngine(output_dir="reports")
    paths = reporting.generate_all_reports(2025, carbon_engine)
    print(f"Generated {len(paths)} reports")

    # 4. Environmental Impact Assessment
    print("\n" + "=" * 60)
    print("4. ENVIRONMENTAL IMPACT ASSESSMENT")
    print("=" * 60)
    eia_manager = EIAManager()
    assessment = eia_manager.create_assessment(
        system_name="LLM Training Run #47",
        system_id="model-llm-7b-v3",
        functional_unit="per training run",
        assessor="env-engineer-1",
    )
    assessment.add_lci_item(LifeCycleInventoryItem(
        stage=LifeCycleStage.AI_TRAINING,
        category=ImpactCategory.CLIMATE_CHANGE,
        value=Decimal("25000"), unit="kg CO2e",
        data_quality="primary", source="Energy monitoring",
    ))
    score = assessment.calculate_eis()
    print(f"EIS Score: {score} (Rating: {assessment.eis_rating})")

    # 5. Carbon Optimization
    print("\n" + "=" * 60)
    print("5. CARBON OPTIMIZATION")
    print("=" * 60)
    opt_engine = CarbonOptimizationEngine()
    recs = opt_engine.generate_recommendations({
        "workload_id": "inference-cluster-us",
        "avg_gpu_utilization": Decimal("35"),
        "idle_minutes": 45,
    })
    print(f"Generated {len(recs)} optimization recommendations")

    # 6. Carbon Offset Management
    print("\n" + "=" * 60)
    print("6. CARBON OFFSET MANAGEMENT")
    print("=" * 60)
    portfolio = OffsetPortfolio()
    from models import CarbonOffset
    portfolio.add_offset(CarbonOffset(
        offset_id="offset-001",
        project_name="Climeworks DAC",
        registry="Climeworks",
        standard="DAC",
        category="removal_tech",
        vintage=2025,
        credits_purchased=Decimal("10000"),
        price_per_credit=Decimal("50"),
        region="Iceland",
        quality_score=95,
    ))
    net_calc = NetEmissionsCalculator(portfolio)
    net = net_calc.calculate_net_emissions(
        gross_scope1=Decimal("50000"),
        gross_scope2_location=Decimal("100000"),
        gross_scope3=Decimal("150000"),
    )
    print(f"Net emissions: {net['net_emissions_kg_co2e'] / 1000} tCO2e")

    # 7. Environmental Compliance
    print("\n" + "=" * 60)
    print("7. ENVIRONMENTAL COMPLIANCE")
    print("=" * 60)
    compliance = EnvironmentalComplianceEngine()
    results = compliance.run_compliance_check({
        "projected_emissions": Decimal("5000"),
        "carbon_budget": Decimal("4000"),
        "renewable_percentage": Decimal("0.55"),
    })
    summary = compliance.get_compliance_summary()
    print(f"Compliance rate: {summary['check_summary']['compliance_rate']}%")

    print("\n" + "=" * 60)
    print("ALL MODULES EXECUTED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    run_full_environmental_governance()
```

### 9.3 Production Deployment Notes

| Component | Production Technology | Purpose |
|-----------|----------------------|---------|
| Stream processing | Apache Kafka + Flink | Real-time energy data ingestion |
| Batch processing | Apache Spark | Carbon accounting calculations |
| Time-series DB | TimescaleDB | Energy consumption storage |
| Carbon ledger | Hyperledger Fabric | Immutable emission records |
| Document store | MongoDB + S3 | Reports and audit trails |
| Dashboard | Grafana | Real-time monitoring |
| Policy engine | OPA/Rego | Environmental policy enforcement |
| CI/CD gates | GitHub Actions | Pipeline environmental checks |

---

*End of GRC_Claw Environmental Governance Implementation Guide*
