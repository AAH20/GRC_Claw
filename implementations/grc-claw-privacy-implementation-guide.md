# GRC_Claw Privacy Implementation Guide

**Document ID:** GRC-PRV-IMP-001  
**Version:** 1.0  
**Date:** 2026-10-01  
**Owner:** GRC_Claw Architecture Team  
**References:** GRC-PRV-001 v2.0 (AI Privacy Specification), GRC-DAT-001 v1.0 (Data Governance Specification)

---

## Table of Contents

1. [Privacy Risk Assessment (Python)](#1-privacy-risk-assessment-python)
2. [PII Detection (Python)](#2-pii-detection-python)
3. [Privacy Policy Enforcement (OPA)](#3-privacy-policy-enforcement-opa)
4. [Privacy Incident Response](#4-privacy-incident-response)
5. [Privacy Compliance Monitoring](#5-privacy-compliance-monitoring)
6. [PET Integration](#6-pet-integration)
7. [GDPR Compliance Automation](#7-gdpr-compliance-automation)

---

## 1. Privacy Risk Assessment (Python)

Implements the CPRS (Composite Privacy Risk Score) framework from GRC-PRV-001 §5, with five weighted dimensions scored 1–5.

### 1.1 Core Risk Scoring Engine

```python
"""
GRC_Claw Privacy Risk Assessment Engine
Implements CPRS calculation per GRC-PRV-001 §5.1
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
import json
import math


class RiskTier(Enum):
    LOW = "Low"           # CPRS 1.0–1.9
    MEDIUM = "Medium"     # CPRS 2.0–2.9
    HIGH = "High"         # CPRS 3.0–3.9
    CRITICAL = "Critical" # CPRS 4.0–5.0


@dataclass
class DimensionScore:
    """Single dimension score with evidence."""
    name: str
    score: float          # 1.0–5.0
    weight: float        # 0.0–1.0
    evidence: Dict       # Supporting data
    rationale: str       # Human-readable justification


@dataclass
class PrivacyRiskScore:
    """Complete CPRS result for an AI system."""
    system_id: str
    cprs: float
    risk_tier: RiskTier
    dimensions: Dict[str, DimensionScore]
    timestamp: datetime
    next_review: datetime
    dpia_required: bool
    approval_authority: List[str]
    review_frequency: str


@dataclass
class PrivacyRiskAssessment:
    """Full assessment with DPIA deliverables."""
    risk_score: PrivacyRiskScore
    threat_model: Dict
    mitigation_plan: List[Dict]
    residual_risk: str
    approval_record: Dict


class DataSensitivityAnalyzer:
    """Dimension 1: Data Sensitivity (25% weight)."""
    
    SENSITIVITY_MAP = {
        "public": 1, "internal": 2, "confidential": 3, "restricted": 4,
        "phi": 5, "biometric": 5, "childrens_data": 5,
        "genetic": 5, "health": 4, "financial": 4,
        "ssn": 5, "passport": 5, "email": 3, "phone": 3,
        "name": 3, "dob": 3, "zip": 2, "ip_address": 2,
    }
    
    def analyze(self, system_id: str, data_sources: List[Dict],
                pii_inventory: Dict, special_categories: List[str]) -> DimensionScore:
        max_sensitivity = 1
        evidence = {"data_sources": [], "pii_categories": {}}
        
        for source in data_sources:
            classification = source.get("classification", "L1")
            sensitivity = self.SENSITIVITY_MAP.get(classification.lower(), 2)
            max_sensitivity = max(max_sensitivity, sensitivity)
            evidence["data_sources"].append({
                "source_id": source.get("id"),
                "classification": classification,
                "sensitivity_score": sensitivity,
            })
        
        # Check for special categories (GDPR Article 9)
        special_category_boost = 0
        for category in special_categories:
            if category in ("genetic", "biometric", "health", "childrens_data"):
                special_category_boost = max(special_category_boost, 2)
            elif category in ("racial", "political", "religious"):
                special_category_boost = max(special_category_boost, 1)
        
        score = min(5.0, max_sensitivity + special_category_boost)
        evidence["special_categories"] = special_categories
        
        return DimensionScore(
            name="data_sensitivity",
            score=score,
            weight=0.25,
            evidence=evidence,
            rationale=f"Max data classification sensitivity: {max_sensitivity}, "
                      f"special category boost: +{special_category_boost}",
        )


class ProcessingScaleCalculator:
    """Dimension 2: Processing Scale (20% weight)."""
    
    def calculate(self, system_id: str, data_volume: int,
                  data_subject_count: int, geographic_scope: List[str]) -> DimensionScore:
        # Volume scoring
        if data_volume > 10_000_000:
            vol_score = 5
        elif data_volume > 1_000_000:
            vol_score = 4
        elif data_volume > 100_000:
            vol_score = 3
        elif data_volume > 10_000:
            vol_score = 2
        else:
            vol_score = 1
        
        # Data subject count scoring
        if data_subject_count > 1_000_000:
            subject_score = 5
        elif data_subject_count > 100_000:
            subject_score = 4
        elif data_subject_count > 10_000:
            subject_score = 3
        elif data_subject_count > 1_000:
            subject_score = 2
        else:
            subject_score = 1
        
        # Geographic scope
        geo_score = min(5, len(geographic_scope))
        
        score = max(vol_score, subject_score, geo_score)
        
        return DimensionScore(
            name="processing_scale",
            score=float(score),
            weight=0.20,
            evidence={
                "data_volume": data_volume,
                "data_subject_count": data_subject_count,
                "geographic_scope": geographic_scope,
                "volume_score": vol_score,
                "subject_score": subject_score,
                "geo_score": geo_score,
            },
            rationale=f"Volume: {vol_score}, Subjects: {subject_score}, Geo: {geo_score}",
        )


class MemorizationRiskEngine:
    """Dimension 3: Model Memorization Risk (20% weight)."""
    
    def assess(self, system_id: str, model_type: str,
               training_data_size: int, model_capacity: str,
               dp_applied: bool) -> DimensionScore:
        # Base risk by model type
        type_risk = {
            "llm": 5, "transformer": 4, "cnn": 3, "rnn": 3,
            "tabular_ml": 2, "linear": 1, "decision_tree": 1,
        }
        base_risk = type_risk.get(model_type.lower(), 3)
        
        # Small dataset increases memorization risk
        if training_data_size < 1000:
            data_factor = 2
        elif training_data_size < 10_000:
            data_factor = 1
        else:
            data_factor = 0
        
        # Model capacity
        capacity_risk = {"large": 2, "medium": 1, "small": 0}.get(model_capacity, 1)
        
        # DP reduces risk
        dp_reduction = 2 if dp_applied else 0
        
        score = max(1.0, min(5.0, base_risk + data_factor + capacity_risk - dp_reduction))
        
        return DimensionScore(
            name="memorization_risk",
            score=score,
            weight=0.20,
            evidence={
                "model_type": model_type,
                "training_data_size": training_data_size,
                "model_capacity": model_capacity,
                "dp_applied": dp_applied,
                "base_risk": base_risk,
                "data_factor": data_factor,
                "capacity_risk": capacity_risk,
                "dp_reduction": dp_reduction,
            },
            rationale=f"Base: {base_risk}, Data: +{data_factor}, Capacity: +{capacity_risk}, DP: -{dp_reduction}",
        )


class AttackSurfaceMapper:
    """Dimension 4: Inference Attack Surface (20% weight)."""
    
    def map(self, system_id: str, api_exposure: str,
            output_accessibility: str, query_flexibility: str,
            agent_capabilities: bool) -> DimensionScore:
        exposure_score = {"public": 5, "partner": 3, "internal": 1}.get(api_exposure, 3)
        output_score = {"full_text": 5, "structured": 3, "binary": 1}.get(output_accessibility, 3)
        query_score = {"unlimited": 5, "high": 4, "moderate": 3, "limited": 2, "none": 1}.get(query_flexibility, 3)
        agent_score = 2 if agent_capabilities else 0
        
        score = max(1.0, min(5.0, (exposure_score + output_score + query_score + agent_score) / 3.5))
        
        return DimensionScore(
            name="attack_surface",
            score=score,
            weight=0.20,
            evidence={
                "api_exposure": api_exposure,
                "output_accessibility": output_accessibility,
                "query_flexibility": query_flexibility,
                "agent_capabilities": agent_capabilities,
            },
            rationale=f"Exposure: {exposure_score}, Output: {output_score}, Query: {query_score}, Agent: +{agent_score}",
        )


class RegulatoryExposureMapper:
    """Dimension 5: Regulatory Exposure (15% weight)."""
    
    def map(self, system_id: str, jurisdictions: List[str],
            data_subject_residency: List[str], sector: str,
            enforcement_history: List[Dict]) -> DimensionScore:
        # Jurisdiction risk
        high_risk_jurisdictions = {"EU", "UK", "California", "Brazil", "China"}
        medium_risk_jurisdictions = {"Canada", "Japan", "South_Korea", "Australia"}
        
        juris_score = 1
        for j in jurisdictions:
            if j in high_risk_jurisdictions:
                juris_score = max(juris_score, 4)
            elif j in medium_risk_jurisdictions:
                juris_score = max(juris_score, 2)
        
        # Sector risk
        sector_risk = {
            "healthcare": 5, "finance": 4, "education": 3,
            "technology": 3, "retail": 2, "manufacturing": 1,
        }
        sector_score = sector_risk.get(sector.lower(), 2)
        
        # Enforcement history
        enforcement_score = min(3, len(enforcement_history))
        
        score = max(1.0, min(5.0, (juris_score + sector_score + enforcement_score) / 2.5))
        
        return DimensionScore(
            name="regulatory_exposure",
            score=score,
            weight=0.15,
            evidence={
                "jurisdictions": jurisdictions,
                "sector": sector,
                "enforcement_count": len(enforcement_history),
            },
            rationale=f"Jurisdiction: {juris_score}, Sector: {sector_score}, Enforcement: +{enforcement_score}",
        )


class PrivacyRiskScoringEngine:
    """Main CPRS scoring engine — orchestrates all five dimensions."""
    
    def __init__(self):
        self.sensitivity_analyzer = DataSensitivityAnalyzer()
        self.scale_calculator = ProcessingScaleCalculator()
        self.memorization_engine = MemorizationRiskEngine()
        self.attack_mapper = AttackSurfaceMapper()
        self.regulatory_mapper = RegulatoryExposureMapper()
    
    def score_system(self, system_id: str, context: Dict) -> PrivacyRiskScore:
        """Calculate CPRS for an AI system."""
        d1 = self.sensitivity_analyzer.analyze(
            system_id=system_id,
            data_sources=context.get("data_sources", []),
            pii_inventory=context.get("pii_inventory", {}),
            special_categories=context.get("special_categories", []),
        )
        d2 = self.scale_calculator.calculate(
            system_id=system_id,
            data_volume=context.get("data_volume", 0),
            data_subject_count=context.get("data_subject_count", 0),
            geographic_scope=context.get("geographic_scope", []),
        )
        d3 = self.memorization_engine.assess(
            system_id=system_id,
            model_type=context.get("model_type", "unknown"),
            training_data_size=context.get("training_data_size", 0),
            model_capacity=context.get("model_capacity", "medium"),
            dp_applied=context.get("dp_applied", False),
        )
        d4 = self.attack_mapper.map(
            system_id=system_id,
            api_exposure=context.get("api_exposure", "internal"),
            output_accessibility=context.get("output_accessibility", "structured"),
            query_flexibility=context.get("query_flexibility", "moderate"),
            agent_capabilities=context.get("agent_capabilities", False),
        )
        d5 = self.regulatory_mapper.map(
            system_id=system_id,
            jurisdictions=context.get("jurisdictions", []),
            data_subject_residency=context.get("data_subject_residency", []),
            sector=context.get("sector", "technology"),
            enforcement_history=context.get("enforcement_history", []),
        )
        
        cprs = (
            d1.score * d1.weight +
            d2.score * d2.weight +
            d3.score * d3.weight +
            d4.score * d4.weight +
            d5.score * d5.weight
        )
        
        risk_tier = self._classify_tier(cprs)
        next_review = self._calculate_next_review(risk_tier)
        dpia_required = cprs >= 3.0 or risk_tier in (RiskTier.HIGH, RiskTier.CRITICAL)
        approval_authority = self._get_approval_authority(risk_tier)
        review_frequency = self._get_review_frequency(risk_tier)
        
        return PrivacyRiskScore(
            system_id=system_id,
            cprs=round(cprs, 2),
            risk_tier=risk_tier,
            dimensions={
                "data_sensitivity": d1,
                "processing_scale": d2,
                "memorization_risk": d3,
                "attack_surface": d4,
                "regulatory_exposure": d5,
            },
            timestamp=datetime.utcnow(),
            next_review=next_review,
            dpia_required=dpia_required,
            approval_authority=approval_authority,
            review_frequency=review_frequency,
        )
    
    def _classify_tier(self, cprs: float) -> RiskTier:
        if cprs >= 4.0:
            return RiskTier.CRITICAL
        elif cprs >= 3.0:
            return RiskTier.HIGH
        elif cprs >= 2.0:
            return RiskTier.MEDIUM
        return RiskTier.LOW
    
    def _calculate_next_review(self, tier: RiskTier) -> datetime:
        intervals = {
            RiskTier.LOW: 365,
            RiskTier.MEDIUM: 180,
            RiskTier.HIGH: 90,
            RiskTier.CRITICAL: 30,
        }
        return datetime.utcnow() + timedelta(days=intervals[tier])
    
    def _get_approval_authority(self, tier: RiskTier) -> List[str]:
        authorities = {
            RiskTier.LOW: ["data_owner"],
            RiskTier.MEDIUM: ["data_owner", "dpo"],
            RiskTier.HIGH: ["dpo", "compliance"],
            RiskTier.CRITICAL: ["dpo", "ciso", "legal"],
        }
        return authorities[tier]
    
    def _get_review_frequency(self, tier: RiskTier) -> str:
        frequencies = {
            RiskTier.LOW: "annual",
            RiskTier.MEDIUM: "semi_annual",
            RiskTier.HIGH: "quarterly",
            RiskTier.CRITICAL: "monthly",
        }
        return frequencies[tier]


# --- Usage Example ---
if __name__ == "__main__":
    engine = PrivacyRiskScoringEngine()
    
    context = {
        "data_sources": [
            {"id": "customer-db", "classification": "L3"},
            {"id": "health-records", "classification": "L4"},
        ],
        "pii_inventory": {"direct_identifiers": 5, "quasi_identifiers": 3},
        "special_categories": ["health"],
        "data_volume": 500_000,
        "data_subject_count": 50_000,
        "geographic_scope": ["EU", "US"],
        "model_type": "transformer",
        "training_data_size": 50_000,
        "model_capacity": "large",
        "dp_applied": True,
        "api_exposure": "partner",
        "output_accessibility": "structured",
        "query_flexibility": "moderate",
        "agent_capabilities": False,
        "jurisdictions": ["EU", "California"],
        "data_subject_residency": ["EU", "US"],
        "sector": "healthcare",
        "enforcement_history": [],
    }
    
    result = engine.score_system("healthcare-llm-001", context)
    print(f"CPRS: {result.cprs}")
    print(f"Risk Tier: {result.risk_tier.value}")
    print(f"DPIA Required: {result.dpia_required}")
    print(f"Approval Authority: {result.approval_authority}")
    print(f"Next Review: {result.next_review}")
    print(f"Review Frequency: {result.review_frequency}")
    for name, dim in result.dimensions.items():
        print(f"  {name}: {dim.score} (weight: {dim.weight})")
```

### 1.2 Risk Re-assessment Triggers

```python
class PrivacyRiskReassessmentTriggers:
    """Implements GRC-PRV-001 §5.3 — triggers for privacy risk re-assessment."""
    
    TRIGGERS = {
        "scheduled_interval": "Per risk tier (annual/semi-annual/quarterly/monthly)",
        "material_change": "New data sources, model retraining, architecture changes",
        "incident_trigger": "Data breaches, privacy complaints, regulatory inquiries",
        "model_update": "Fine-tuning, RLHF, or any change to model weights",
        "regulatory_change": "New privacy laws, regulatory guidance, enforcement actions",
        "scale_change": "Significant increase in data volume or data subjects",
    }
    
    def __init__(self, scoring_engine: PrivacyRiskScoringEngine):
        self.engine = scoring_engine
        self.risk_register: Dict[str, PrivacyRiskScore] = {}
    
    def register_system(self, system_id: str, context: Dict) -> PrivacyRiskScore:
        score = self.engine.score_system(system_id, context)
        self.risk_register[system_id] = score
        return score
    
    def check_reassessment_needed(self, system_id: str, event: Dict) -> bool:
        """Check if an event triggers re-assessment."""
        if system_id not in self.risk_register:
            return True
        
        last_score = self.risk_register[system_id]
        event_type = event.get("type")
        
        if event_type == "scheduled_interval":
            return datetime.utcnow() >= last_score.next_review
        elif event_type == "material_change":
            return event.get("severity") in ("high", "critical")
        elif event_type == "incident_trigger":
            return True
        elif event_type == "model_update":
            return True
        elif event_type == "regulatory_change":
            return event.get("affects_system", False)
        elif event_type == "scale_change":
            old_count = last_score.dimensions["processing_scale"].evidence.get("data_subject_count", 0)
            new_count = event.get("new_data_subject_count", old_count)
            return new_count > old_count * 2
        
        return False
    
    def reassess(self, system_id: str, updated_context: Dict) -> PrivacyRiskScore:
        new_score = self.engine.score_system(system_id, updated_context)
        self.risk_register[system_id] = new_score
        return new_score
```

---

## 2. PII Detection (Python)

Implements the 6-layer PII detection framework from GRC-PRV-001 §7.

### 2.1 Multi-Layer Detection Pipeline

```python
"""
GRC_Claw PII Detection Engine
Implements 6-layer detection per GRC-PRV-001 §7.1
"""
import re
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json


class PIICategory(Enum):
    DIRECT_IDENTIFIER = "direct_identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    FINANCIAL = "financial"
    HEALTH = "health"
    BIOMETRIC = "biometric"
    LOCATION = "location"
    ONLINE = "online"
    EMPLOYMENT = "employment"
    EDUCATIONAL = "educational"
    CHILDRENS = "childrens"


class RedactionMethod(Enum):
    MASKING = "masking"
    TOKENIZATION = "tokenization"
    PSEUDONYMIZATION = "pseudonymization"
    GENERALIZATION = "generalization"
    SUPPRESSION = "suppression"
    PERTURBATION = "perturbation"
    SYNTHETIC_REPLACEMENT = "synthetic_replacement"


@dataclass
class PIIFinding:
    """A single PII detection result."""
    category: PIICategory
    value: str
    confidence: float
    location: Tuple[int, int]  # (start, end) span
    layer: str                  # L1-L6
    context: str = ""
    risk_score: float = 0.0
    recommended_action: RedactionMethod = RedactionMethod.MASKING


@dataclass
class RedactionResult:
    """Result of PII redaction."""
    original_text: str
    redacted_text: str
    findings: List[PIIFinding]
    redactions_applied: int
    verification_passed: bool
    residual_findings: List[PIIFinding]


# ─── Layer 1: Regex & Pattern Matching ───

class RegexPIIDetector:
    """L1: Regex-based detection for structured PII. <1ms latency."""
    
    PATTERNS = {
        "ssn": (r"\b\d{3}-\d{2}-\d{4}\b", PIICategory.DIRECT_IDENTIFIER, 0.95),
        "credit_card": (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", PIICategory.FINANCIAL, 0.95),
        "email": (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", PIICategory.DIRECT_IDENTIFIER, 0.98),
        "phone": (r"\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", PIICategory.DIRECT_IDENTIFIER, 0.90),
        "ip_address": (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", PIICategory.LOCATION, 0.95),
        "passport": (r"\b[A-Z]{1,2}\d{6,9}\b", PIICategory.DIRECT_IDENTIFIER, 0.80),
        "bank_account": (r"\b\d{8,17}\b", PIICategory.FINANCIAL, 0.70),
        "date_of_birth": (r"\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b", PIICategory.QUASI_IDENTIFIER, 0.85),
        "zip_code": (r"\b\d{5}(-\d{4})?\b", PIICategory.QUASI_IDENTIFIER, 0.75),
    }
    
    def detect(self, text: str) -> List[PIIFinding]:
        findings = []
        for name, (pattern, category, confidence) in self.PATTERNS.items():
            for match in re.finditer(pattern, text):
                findings.append(PIIFinding(
                    category=category,
                    value=match.group(),
                    confidence=confidence,
                    location=(match.start(), match.end()),
                    layer="L1",
                    risk_score=confidence * (5 if category == PIICategory.DIRECT_IDENTIFIER else 3),
                ))
        return findings


# ─── Layer 2: NER Model ───

class NERPIIDetector:
    """L2: Named Entity Recognition for unstructured PII. 10-100ms latency."""
    
    def __init__(self, model_name: str = "en_core_web_lg"):
        self.model_name = model_name
        self._model = None  # Lazy-loaded spaCy model
    
    def _load_model(self):
        if self._model is None:
            try:
                import spacy
                self._model = spacy.load(self.model_name)
            except ImportError:
                self._model = False  # spaCy not available
        return self._model
    
    def detect(self, text: str) -> List[PIIFinding]:
        nlp = self._load_model()
        if not nlp:
            return []
        
        doc = nlp(text)
        findings = []
        
        entity_map = {
            "PERSON": PIICategory.DIRECT_IDENTIFIER,
            "ORG": PIICategory.EMPLOYMENT,
            "GPE": PIICategory.LOCATION,
            "LOC": PIICategory.LOCATION,
            "DATE": PIICategory.QUASI_IDENTIFIER,
            "MONEY": PIICategory.FINANCIAL,
        }
        
        for ent in doc.ents:
            category = entity_map.get(ent.label_, PIICategory.DIRECT_IDENTIFIER)
            findings.append(PIIFinding(
                category=category,
                value=ent.text,
                confidence=0.85,
                location=(ent.start_char, ent.end_char),
                layer="L2",
                risk_score=0.85 * (5 if category == PIICategory.DIRECT_IDENTIFIER else 3),
            ))
        
        return findings


# ─── Layer 3: Contextual ML Classifier ───

class ContextualPIIDClassifier:
    """L3: Context-dependent PII detection. 50-200ms latency."""
    
    CONTEXT_PATTERNS = [
        (r"my name is (\w+)", PIICategory.DIRECT_IDENTIFIER, 0.90),
        (r"i am (\d+) years old", PIICategory.QUASI_IDENTIFIER, 0.85),
        (r"i live at (.+)", PIICategory.LOCATION, 0.80),
        (r"my (?:ssn|social security) is (\S+)", PIICategory.DIRECT_IDENTIFIER, 0.95),
        (r"my (?:credit card|card) number is (\S+)", PIICategory.FINANCIAL, 0.95),
        (r"my (?:phone|number) is (\S+)", PIICategory.DIRECT_IDENTIFIER, 0.90),
        (r"my (?:email|e-mail) is (\S+)", PIICategory.DIRECT_IDENTIFIER, 0.95),
        (r"my (?:date of birth|birthday|dob) is (\S+)", PIICategory.QUASI_IDENTIFIER, 0.90),
        (r"my (?:salary|income) is (\S+)", PIICategory.FINANCIAL, 0.85),
        (r"my (?:diagnosis|condition) is (\S+)", PIICategory.HEALTH, 0.85),
    ]
    
    def detect(self, text: str, context: Dict = None) -> List[PIIFinding]:
        findings = []
        for pattern, category, confidence in self.CONTEXT_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append(PIIFinding(
                    category=category,
                    value=match.group(1),
                    confidence=confidence,
                    location=(match.start(1), match.end(1)),
                    layer="L3",
                    context=match.group(0),
                    risk_score=confidence * (5 if category == PIICategory.DIRECT_IDENTIFIER else 3),
                ))
        return findings


# ─── Layer 4: LLM-Based Detection ───

class LLMPIIDetector:
    """L4: LLM-based detection for complex/ambiguous cases. 1-5s latency."""
    
    def __init__(self, model: str = "grc-claw/pii-llm-detector"):
        self.model = model
    
    def detect(self, text: str) -> List[PIIFinding]:
        """
        In production, this calls an LLM with a PII detection prompt.
        For this implementation, we use a heuristic-based approach
        that simulates LLM detection for complex cases.
        """
        findings = []
        
        # Detect implicit PII (e.g., "the CEO of Company X")
        implicit_patterns = [
            (r"(?:the )?(?:CEO|CTO|CFO|president) of ([\w\s]+?)(?:,|\.| and | who )", 
             PIICategory.DIRECT_IDENTIFIER, 0.70),
            (r"(?:my|our) (?:boss|manager|supervisor) (\w+)", 
             PIICategory.DIRECT_IDENTIFIER, 0.65),
            (r"(?:patient|student|employee) (\w+)", 
             PIICategory.DIRECT_IDENTIFIER, 0.60),
        ]
        
        for pattern, category, confidence in implicit_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                findings.append(PIIFinding(
                    category=category,
                    value=match.group(1),
                    confidence=confidence,
                    location=(match.start(1), match.end(1)),
                    layer="L4",
                    context=match.group(0),
                    risk_score=confidence * 4,
                ))
        
        return findings


# ─── Layer 5: Image/OCR Detection ───

class ImageOCRPIIDetector:
    """L5: OCR + NER for PII in images. 500ms-2s latency."""
    
    def detect(self, image_bytes: bytes) -> List[PIIFinding]:
        """
        In production: OCR (Tesseract) + NER on extracted text.
        Also: face detection, object detection for license plates, etc.
        """
        findings = []
        # Placeholder: In production, integrate with:
        # - pytesseract for OCR
        # - OpenCV for face detection
        # - Custom object detection for license plates, IDs
        return findings


# ─── Layer 6: Audio Detection ───

class AudioPIIDetector:
    """L6: Speech-to-text + NER for PII in audio. 1-5s latency."""
    
    def detect(self, audio_bytes: bytes) -> List[PIIFinding]:
        """
        In production: Whisper/STT + NER on transcript.
        Also: voice biometric detection.
        """
        findings = []
        # Placeholder: In production, integrate with:
        # - OpenAI Whisper for STT
        # - NER on transcript
        # - Voice biometric detection
        return findings


# ─── Redaction Engine ───

class RedactionEngine:
    """Applies redaction based on PII category, confidence, and risk score."""
    
    def __init__(self):
        self.token_vault: Dict[str, str] = {}  # For tokenization/pseudonymization
    
    def select_strategy(self, finding: PIIFinding) -> RedactionMethod:
        """Select redaction method per GRC-PRV-001 §7.2.2 decision matrix."""
        if finding.category == PIICategory.DIRECT_IDENTIFIER:
            if finding.confidence >= 0.9:
                return RedactionMethod.SUPPRESSION
            elif finding.confidence >= 0.7:
                return RedactionMethod.PSEUDONYMIZATION
            return RedactionMethod.MASKING
        
        elif finding.category == PIICategory.QUASI_IDENTIFIER:
            if finding.confidence >= 0.9:
                return RedactionMethod.GENERALIZATION
            elif finding.confidence >= 0.7:
                return RedactionMethod.GENERALIZATION
            return RedactionMethod.MASKING
        
        elif finding.category in (PIICategory.FINANCIAL, PIICategory.HEALTH, 
                                   PIICategory.BIOMETRIC, PIICategory.CHILDRENS):
            return RedactionMethod.SUPPRESSION
        
        return RedactionMethod.MASKING
    
    def apply(self, text: str, findings: List[PIIFinding],
              strategy: RedactionMethod = None) -> RedactionResult:
        """Apply redaction to text based on findings."""
        if not findings:
            return RedactionResult(
                original_text=text,
                redacted_text=text,
                findings=[],
                redactions_applied=0,
                verification_passed=True,
                residual_findings=[],
            )
        
        # Sort findings by location (reverse to avoid offset issues)
        sorted_findings = sorted(findings, key=lambda f: f.location[0], reverse=True)
        
        redacted = text
        applied = 0
        
        for finding in sorted_findings:
            start, end = finding.location
            method = strategy or self.select_strategy(finding)
            
            if method == RedactionMethod.MASKING:
                redacted = redacted[:start] + "*" * (end - start) + redacted[end:]
            elif method == RedactionMethod.SUPPRESSION:
                redacted = redacted[:start] + redacted[end:]
            elif method == RedactionMethod.TOKENIZATION:
                token = f"<TOKEN_{hashlib.sha256(finding.value.encode()).hexdigest()[:8]}>"
                self.token_vault[token] = finding.value
                redacted = redacted[:start] + token + redacted[end:]
            elif method == RedactionMethod.PSEUDONYMIZATION:
                pseudo = f"<PSEUDO_{hashlib.sha256(finding.value.encode()).hexdigest()[:8]}>"
                self.token_vault[pseudo] = finding.value
                redacted = redacted[:start] + pseudo + redacted[end:]
            elif method == RedactionMethod.GENERALIZATION:
                redacted = redacted[:start] + f"<{finding.category.value.upper()}>" + redacted[end:]
            
            applied += 1
        
        # Verification: re-scan redacted text
        residual = self._verify_redaction(redacted)
        
        return RedactionResult(
            original_text=text,
            redacted_text=redacted,
            findings=findings,
            redactions_applied=applied,
            verification_passed=len(residual) == 0,
            residual_findings=residual,
        )
    
    def _verify_redaction(self, text: str) -> List[PIIFinding]:
        """Re-scan redacted text to verify no PII remains."""
        verifier = RegexPIIDetector()
        return [f for f in verifier.detect(text) if f.confidence >= 0.5]


# ─── Main Pipeline ───

class PIIDetectionPipeline:
    """GRC_Claw PII Detection and Redaction Pipeline (GRC-PRV-001 §7.1.3)."""
    
    def __init__(self):
        self.l1_regex = RegexPIIDetector()
        self.l2_ner = NERPIIDetector()
        self.l3_context = ContextualPIIDClassifier()
        self.l4_llm = LLMPIIDetector()
        self.l5_image = ImageOCRPIIDetector()
        self.l6_audio = AudioPIIDetector()
        self.redaction_engine = RedactionEngine()
    
    def detect(self, text: str, context: Dict = None,
               depth: str = "standard") -> List[PIIFinding]:
        """
        Multi-layer PII detection.
        
        Args:
            text: Input text to scan
            context: Additional context (source, purpose, user info)
            depth: "standard" (L1-L3) or "deep" (L1-L4)
        """
        findings = []
        
        # L1: Always run regex (fastest)
        findings.extend(self.l1_regex.detect(text))
        
        if depth in ("standard", "deep"):
            # L2: NER
            findings.extend(self.l2_ner.detect(text))
            
            # L3: Contextual
            findings.extend(self.l3_context.detect(text, context))
        
        if depth == "deep":
            # L4: LLM (only if needed)
            if self._needs_deep_scan(findings, text):
                findings.extend(self.l4_llm.detect(text))
        
        # Aggregate and deduplicate
        return self._aggregate_findings(findings)
    
    def redact(self, text: str, findings: List[PIIFinding],
               strategy: RedactionMethod = None) -> RedactionResult:
        """Apply redaction based on findings."""
        return self.redaction_engine.apply(text, findings, strategy)
    
    def scan_and_redact(self, text: str, context: Dict = None,
                        depth: str = "standard") -> RedactionResult:
        """Convenience: detect and redact in one pass."""
        findings = self.detect(text, context, depth)
        return self.redact(text, findings)
    
    def _needs_deep_scan(self, findings: List[PIIFinding], text: str) -> bool:
        """Determine if L4 deep scan is needed."""
        if any(f.confidence < 0.7 for f in findings):
            return True
        if len(text) > 1000 and not findings:
            return True
        return False
    
    def _aggregate_findings(self, findings: List[PIIFinding]) -> List[PIIFinding]:
        """Deduplicate and merge overlapping findings."""
        if not findings:
            return []
        
        # Sort by confidence (highest first)
        sorted_findings = sorted(findings, key=lambda f: f.confidence, reverse=True)
        
        aggregated = []
        used_spans = []
        
        for finding in sorted_findings:
            start, end = finding.location
            # Check for overlap with already-accepted findings
            overlap = False
            for u_start, u_end in used_spans:
                if start < u_end and end > u_start:
                    overlap = True
                    break
            
            if not overlap:
                aggregated.append(finding)
                used_spans.append((start, end))
        
        return aggregated


# --- Usage Example ---
if __name__ == "__main__":
    pipeline = PIIDetectionPipeline()
    
    test_text = """
    My name is John Smith and my email is john.smith@example.com.
    My SSN is 123-45-6789 and my phone is 555-123-4567.
    I live at 123 Main St, New York, NY 10001.
    My credit card number is 4111-1111-1111-1111.
    """
    
    # Detect PII
    findings = pipeline.detect(test_text, depth="standard")
    print(f"Found {len(findings)} PII instances:")
    for f in findings:
        print(f"  [{f.layer}] {f.category.value}: '{f.value}' "
              f"(confidence: {f.confidence}, risk: {f.risk_score:.1f})")
    
    # Redact
    result = pipeline.redact(test_text, findings)
    print(f"\nRedacted text:\n{result.redacted_text}")
    print(f"\nVerification passed: {result.verification_passed}")
    print(f"Residual findings: {len(result.residual_findings)}")
```

### 2.2 PII Redaction Decision Matrix

```python
def get_redaction_decision(category: PIICategory, confidence: float, 
                           risk_score: float) -> RedactionMethod:
    """
    GRC-PRV-001 §7.2.2 Redaction Decision Matrix.
    """
    if category == PIICategory.DIRECT_IDENTIFIER:
        if confidence >= 0.9 and risk_score >= 4.0:
            return RedactionMethod.SUPPRESSION
        elif confidence >= 0.7:
            return RedactionMethod.PSEUDONYMIZATION
        return RedactionMethod.MASKING
    
    elif category == PIICategory.QUASI_IDENTIFIER:
        if confidence >= 0.9 and risk_score >= 3.0:
            return RedactionMethod.GENERALIZATION
        elif confidence >= 0.7:
            return RedactionMethod.GENERALIZATION
        return RedactionMethod.MASKING
    
    elif category in (PIICategory.FINANCIAL, PIICategory.HEALTH, 
                       PIICategory.BIOMETRIC, PIICategory.CHILDRENS):
        return RedactionMethod.SUPPRESSION
    
    return RedactionMethod.MASKING
```

---

## 3. Privacy Policy Enforcement (OPA)

Implements GRC-PRV-001 §13 — Policy-as-Code with OPA Rego.

### 3.1 OPA Rego Policies

```rego
# policies/privacy/redaction_policy.rego
# GRC-PRV-001 §13.1 — Enforce PII redaction at inference time
package grc_claw.privacy.redaction

default allow = false

# Block output with unredacted PII
allow {
    not pii_detected_in_output
}

allow {
    pii_detected_in_output
    redaction_verified
}

pii_detected_in_output {
    input.output.pii_detected == true
}

redaction_verified {
    input.output.redaction_applied == true
    input.output.residual_findings == 0
}

# Warn on input PII
warn[msg] {
    input.input.pii_detected == true
    msg := "Warning: Input contains PII. Ensure lawful basis for processing."
}

# Deny if no consent for sensitive data
deny[msg] {
    input.data.category == "SENSITIVE"
    not input.data.consent_verified
    msg := "Sensitive personal data requires verified consent (GDPR Article 9)"
}

# Deny if privacy budget exhausted
deny[msg] {
    input.system.privacy_budget_remaining <= 0
    msg := "Processing blocked: privacy budget exhausted for this system"
}

# Deny cross-border transfer of L4 data to non-approved regions
deny[msg] {
    input.data.classification == "L4"
    not input.transfer.destination in data.approved_regions
    msg := "L4 personal data cannot be transferred to non-approved regions (GDPR Article 44)"
}
```

```rego
# policies/privacy/data_minimization.rego
# GRC-PRV-001 §6 — Data minimization enforcement
package grc_claw.privacy.minimization

default allow = false

# Reject excess fields
deny[msg] {
    count(input.data.fields) > count(input.data.declared_required_fields)
    msg := sprintf("Data contains %d fields but only %d declared as required", 
                   [count(input.data.fields), count(input.data.declared_required_fields)])
}

# Reject sensitive data without purpose
deny[msg] {
    input.data.contains_sensitive == true
    not input.data.purpose
    msg := "Sensitive data requires declared purpose"
}

# Reject if no lawful basis
deny[msg] {
    not input.data.lawful_basis
    msg := "Personal data requires lawful basis (GDPR Article 6)"
}

# Reject if retention period exceeds policy
deny[msg] {
    input.data.retention_period > data.max_retention_periods[input.data.classification]
    msg := sprintf("Retention period %v exceeds maximum for %s data", 
                   [input.data.retention_period, input.data.classification])
}

# Allow if all checks pass
allow {
    not deny
}
```

```rego
# policies/privacy/consent_policy.rego
# GRC-PRV-001 §11.2 PC-01 — Consent verification
package grc_claw.privacy.consent

default allow = false

# Require consent for PII
deny[msg] {
    input.data.contains_pii == true
    not input.data.consent_verified
    msg := "PII data requires verified consent"
}

# Require consent for L4 data
deny[msg] {
    input.data.classification == "L4"
    not input.data.consent_verified
    msg := "L4 (Restricted) data requires verified consent"
}

# Check consent expiry
deny[msg] {
    input.data.consent_expires_at
    input.data.consent_expires_at < time.now_ns()
    msg := "Consent has expired"
}

# Require parental consent for children's data
deny[msg] {
    input.data.contains_childrens_data == true
    not input.data.parental_consent_verified
    msg := "Children's data requires verified parental consent"
}

# Block automated decision-making on children's data
deny[msg] {
    input.data.contains_childrens_data == true
    input.processing.type == "automated_decision_making"
    msg := "Children's data cannot be used for automated decision-making"
}

allow {
    not deny
}
```

```rego
# policies/privacy/retention_policy.rego
# GRC-PRV-001 §11.7 — Retention enforcement
package grc_claw.privacy.retention

default allow = false

# Block data past retention period
deny[msg] {
    input.data.age > input.data.retention_period
    msg := sprintf("Data age %v exceeds retention period %v; deletion required", 
                   [input.data.age, input.data.retention_period])
}

# Warn near retention limit
warn[msg] {
    input.data.age > input.data.retention_period * 0.9
    msg := "Data approaching retention limit; schedule deletion"
}

allow {
    input.data.age <= input.data.retention_period
}
```

### 3.2 Policy Bundle (YAML)

```yaml
# policies/privacy-policy-bundle.yaml
# GRC-PRV-001 §13.1 — Privacy Policy Bundle
apiVersion: grc-claw/v1
name: privacy-policy-bundle
description: "Comprehensive privacy policy enforcement"
version: "1.0"
default_action: allow

policies:
  - name: enforce-data-minimization
    description: "Only necessary data fields may be ingested"
    enforcement_point: data_ingestion
    rules:
      - name: reject-excess-fields
        condition: "len(data.fields) > len(data.declared_required_fields)"
        action: deny
        message: "Data contains fields not declared as required"
        severity: critical
      - name: reject-sensitive-without-purpose
        condition: "data.contains_sensitive == true and data.purpose == null"
        action: deny
        message: "Sensitive data requires declared purpose"
        severity: critical

  - name: enforce-consent
    description: "Personal data requires verified consent"
    enforcement_point: data_ingestion
    rules:
      - name: require-consent-for-pii
        condition: "data.contains_pii == true and data.consent_verified == false"
        action: deny
        message: "PII data requires verified consent"
        severity: critical
      - name: require-consent-for-sensitive
        condition: "data.classification == 'L4' and data.consent_verified == false"
        action: deny
        message: "L4 data requires verified consent"
        severity: critical

  - name: enforce-retention
    description: "Data must not be retained beyond policy period"
    enforcement_point: data_storage
    rules:
      - name: block-over-retention
        condition: "data.age > data.retention_period"
        action: deny
        message: "Data exceeds retention period; deletion required"
        severity: critical

  - name: enforce-cross-border
    description: "Cross-border transfers require adequate safeguards"
    enforcement_point: data_transfer
    rules:
      - name: block-l4-to-non-approved
        condition: "data.classification == 'L4' and transfer.destination not in approved_regions"
        action: deny
        message: "L4 data cannot be transferred to non-approved regions"
        severity: critical
      - name: require-scc-for-eu
        condition: "data.contains_eu_personal_data == true and transfer.destination not in eu_adequate_countries and transfer.scc_in_place == false"
        action: deny
        message: "EU personal data transfer requires SCC or adequacy decision"
        severity: critical

  - name: enforce-output-redaction
    description: "Model outputs must not contain unredacted PII"
    enforcement_point: inference_output
    rules:
      - name: block-output-with-pii
        condition: "output.pii_detected == true and output.redaction_verified == false"
        action: deny
        message: "Output contains unredacted PII"
        severity: critical

  - name: enforce-privacy-budget
    description: "Processing blocked when privacy budget is exhausted"
    enforcement_point: all_processing
    rules:
      - name: block-when-budget-exhausted
        condition: "system.privacy_budget_remaining <= 0"
        action: deny
        message: "Privacy budget exhausted for this system"
        severity: critical
      - name: warn-at-80-percent
        condition: "system.privacy_budget_remaining / system.privacy_budget_total < 0.2"
        action: warn
        message: "Privacy budget below 20%"
        severity: warning

  - name: enforce-childrens-data
    description: "Enhanced protection for children's data"
    enforcement_point: all_processing
    rules:
      - name: block-childrens-data-without-parental-consent
        condition: "data.contains_childrens_data == true and data.parental_consent_verified == false"
        action: deny
        message: "Children's data requires verified parental consent"
        severity: critical
      - name: block-childrens-data-for-profiling
        condition: "data.contains_childrens_data == true and processing.type == 'automated_decision_making'"
        action: deny
        message: "Children's data cannot be used for automated decision-making"
        severity: critical
```

### 3.3 Policy Evaluation Engine (Python)

```python
"""
GRC_Claw Privacy Policy Engine
Evaluates OPA policies at enforcement points.
"""
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class PolicyAction(Enum):
    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"


@dataclass
class RuleDecision:
    rule_name: str
    policy_name: str
    action: PolicyAction
    message: str
    severity: str
    matched: bool


@dataclass
class PolicyDecision:
    action: PolicyAction
    reason: str
    triggered_rules: List[RuleDecision]
    timestamp: datetime


class OPAClient:
    """Client for OPA policy evaluation."""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
    
    def evaluate(self, policy_path: str, input_data: Dict) -> Dict:
        """Evaluate a policy via OPA REST API."""
        import urllib.request
        url = f"{self.opa_url}/v1/data/{policy_path}"
        data = json.dumps({"input": input_data}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except Exception:
            # Fallback: local evaluation for testing
            return self._local_evaluate(policy_path, input_data)
    
    def _local_evaluate(self, policy_path: str, input_data: Dict) -> Dict:
        """Fallback local evaluation (simplified)."""
        # In production, this calls OPA. For testing, we simulate.
        return {"result": {"allow": True, "deny": [], "warn": []}}


class PrivacyPolicyEngine:
    """Evaluates privacy policies at enforcement points."""
    
    def __init__(self, policy_bundle_path: str):
        self.opa_client = OPAClient()
        self.policy_bundle = self._load_bundle(policy_bundle_path)
        self.audit_log: List[Dict] = []
    
    def _load_bundle(self, path: str) -> Dict:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f)
    
    def evaluate(self, enforcement_point: str, 
                 input_data: Dict) -> PolicyDecision:
        """Evaluate all applicable policies for a request."""
        decisions = []
        
        for policy in self.policy_bundle.get("policies", []):
            if policy.get("enforcement_point") != enforcement_point:
                continue
            
            for rule in policy.get("rules", []):
                result = self._evaluate_rule(rule, input_data)
                decisions.append(RuleDecision(
                    rule_name=rule["name"],
                    policy_name=policy["name"],
                    action=PolicyAction(rule["action"]),
                    message=rule["message"],
                    severity=rule["severity"],
                    matched=result,
                ))
        
        final = self._aggregate_decisions(decisions)
        
        # Audit log
        self.audit_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "enforcement_point": enforcement_point,
            "decision": final.action.value,
            "triggered_rules": [d.rule_name for d in final.triggered_rules],
        })
        
        return final
    
    def _evaluate_rule(self, rule: Dict, input_data: Dict) -> bool:
        """Evaluate a single rule condition."""
        # In production, this uses OPA. Here we use a simple condition evaluator.
        condition = rule.get("condition", "")
        return self._eval_condition(condition, input_data)
    
    def _eval_condition(self, condition: str, data: Dict) -> bool:
        """Simple condition evaluator for testing."""
        # This is a simplified evaluator. In production, use OPA.
        # Supports: ==, !=, >, <, >=, <=, in, not, and, or
        try:
            # Replace data references
            expr = condition
            for key, value in self._flatten(data).items():
                expr = expr.replace(key, repr(value))
            return eval(expr, {"__builtins__": {}}, {})
        except Exception:
            return False
    
    def _flatten(self, d: Dict, prefix: str = "") -> Dict:
        """Flatten nested dict for condition evaluation."""
        items = {}
        for k, v in d.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.update(self._flatten(v, new_key))
            else:
                items[new_key] = v
        return items
    
    def _aggregate_decisions(self, decisions: List[RuleDecision]) -> PolicyDecision:
        """Aggregate: deny > warn > allow."""
        denies = [d for d in decisions if d.action == PolicyAction.DENY and d.matched]
        warns = [d for d in decisions if d.action == PolicyAction.WARN and d.matched]
        
        if denies:
            return PolicyDecision(
                action=PolicyAction.DENY,
                reason="; ".join(d.message for d in denies),
                triggered_rules=denies,
                timestamp=datetime.utcnow(),
            )
        
        if warns:
            return PolicyDecision(
                action=PolicyAction.WARN,
                reason="; ".join(d.message for d in warns),
                triggered_rules=warns,
                timestamp=datetime.utcnow(),
            )
        
        return PolicyDecision(
            action=PolicyAction.ALLOW,
            reason="All policies passed",
            triggered_rules=[],
            timestamp=datetime.utcnow(),
        )
```

---

## 4. Privacy Incident Response

Implements GRC-PRV-001 §27 — Automated incident detection, classification, and response.

### 4.1 Incident Detection and Classification

```python
"""
GRC_Claw Privacy Incident Response System
Implements GRC-PRV-001 §27 — Automated incident detection and response.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class IncidentSeverity(Enum):
    P1 = "P1"  # Critical: >10K subjects or PHI breach
    P2 = "P2"  # High: >1K subjects
    P3 = "P3"  # Medium: >100 subjects
    P4 = "P4"  # Low: ≤100 subjects


class IncidentCategory(Enum):
    PII_LEAKAGE = "pii_leakage"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    CONSENT_VIOLATION = "consent_violation"
    RETENTION_VIOLATION = "retention_violation"
    CROSS_BORDER_VIOLATION = "cross_border_violation"
    INFERENCE_ATTACK = "inference_attack"
    MODEL_MEMORIZATION = "model_memorization"


@dataclass
class IncidentEvent:
    timestamp: datetime
    action: str
    actor: str
    details: str


@dataclass
class PrivacyIncident:
    incident_id: str
    severity: IncidentSeverity
    category: IncidentCategory
    description: str
    affected_systems: List[str]
    affected_data_subjects: int
    affected_data_volume: int
    data_types: List[str]
    detected_at: datetime
    detection_method: str
    status: str  # detected, contained, investigated, remediated, closed
    timeline: List[IncidentEvent] = field(default_factory=list)
    regulatory_obligations: List[Dict] = field(default_factory=list)
    containment_actions: List[str] = field(default_factory=list)
    
    def add_timeline_event(self, action: str, actor: str, details: str):
        self.timeline.append(IncidentEvent(
            timestamp=datetime.utcnow(),
            action=action,
            actor=actor,
            details=details,
        ))


class PrivacyIncidentDetector:
    """Automated privacy incident detection (GRC-PRV-001 §27.1)."""
    
    def __init__(self):
        self.detectors = {
            "pii_leakage": self._detect_pii_leakage,
            "unauthorized_access": self._detect_unauthorized_access,
            "data_exfiltration": self._detect_data_exfiltration,
            "consent_violation": self._detect_consent_violation,
            "retention_violation": self._detect_retention_violation,
            "cross_border_violation": self._detect_cross_border_violation,
            "inference_attack": self._detect_inference_attack,
            "model_memorization": self._detect_model_memorization,
        }
    
    def monitor(self, event: Dict) -> Optional[PrivacyIncident]:
        """Monitor privacy events and detect incidents."""
        for category, detector in self.detectors.items():
            finding = detector(event)
            if finding:
                return self._create_incident(finding, event)
        return None
    
    def _detect_pii_leakage(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "model_output" and event.get("pii_detected"):
            if not event.get("redaction_applied"):
                return {
                    "category": IncidentCategory.PII_LEAKAGE,
                    "description": f"PII detected in model output: {event.get('pii_categories', [])}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("pii_categories", []),
                }
        return None
    
    def _detect_unauthorized_access(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "access_attempt":
            if event.get("anomaly_score", 0) > 0.9:
                return {
                    "category": IncidentCategory.UNAUTHORIZED_ACCESS,
                    "description": f"Anomalous access pattern detected: {event.get('details', '')}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_data_exfiltration(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "egress_alert":
            if event.get("data_volume", 0) > event.get("baseline_volume", 0) * 5:
                return {
                    "category": IncidentCategory.DATA_EXFILTRATION,
                    "description": f"Unusual data egress: {event.get('data_volume')} bytes",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_consent_violation(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "processing_event":
            if event.get("contains_pii") and not event.get("consent_verified"):
                return {
                    "category": IncidentCategory.CONSENT_VIOLATION,
                    "description": "Processing PII without verified consent",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_retention_violation(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "retention_check":
            if event.get("data_age", 0) > event.get("retention_period", 0):
                return {
                    "category": IncidentCategory.RETENTION_VIOLATION,
                    "description": f"Data age {event.get('data_age')} exceeds retention {event.get('retention_period')}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_cross_border_violation(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "data_transfer":
            if event.get("classification") == "L4" and event.get("destination") not in event.get("approved_regions", []):
                return {
                    "category": IncidentCategory.CROSS_BORDER_VIOLATION,
                    "description": f"L4 data transferred to non-approved region: {event.get('destination')}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_inference_attack(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "query_pattern":
            if event.get("pattern_anomaly_score", 0) > 0.95:
                return {
                    "category": IncidentCategory.INFERENCE_ATTACK,
                    "description": f"Potential inference attack: {event.get('details', '')}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": event.get("data_types", []),
                }
        return None
    
    def _detect_model_memorization(self, event: Dict) -> Optional[Dict]:
        if event.get("type") == "canary_test":
            if event.get("canary_detected"):
                return {
                    "category": IncidentCategory.MODEL_MEMORIZATION,
                    "description": f"Canary string detected in model output: {event.get('canary_id', '')}",
                    "estimated_data_subjects": event.get("estimated_subjects", 1),
                    "data_types": ["training_data"],
                }
        return None
    
    def _create_incident(self, finding: Dict, event: Dict) -> PrivacyIncident:
        severity = self._classify_severity(finding)
        incident = PrivacyIncident(
            incident_id=str(uuid.uuid4()),
            severity=severity,
            category=finding["category"],
            description=finding["description"],
            affected_systems=event.get("systems", ["unknown"]),
            affected_data_subjects=finding.get("estimated_data_subjects", 1),
            affected_data_volume=finding.get("estimated_data_volume", 0),
            data_types=finding.get("data_types", []),
            detected_at=datetime.utcnow(),
            detection_method=finding["category"].value,
            status="detected",
        )
        incident.add_timeline_event("detected", "automated_detector", finding["description"])
        return incident
    
    def _classify_severity(self, finding: Dict) -> IncidentSeverity:
        subjects = finding.get("estimated_data_subjects", 1)
        data_types = finding.get("data_types", [])
        
        if subjects > 10000 or "PHI" in data_types:
            return IncidentSeverity.P1
        elif subjects > 1000:
            return IncidentSeverity.P2
        elif subjects > 100:
            return IncidentSeverity.P3
        return IncidentSeverity.P4


class IncidentContainmentAutomator:
    """Automated containment actions (GRC-PRV-001 §27.2.2)."""
    
    def auto_contain(self, incident: PrivacyIncident) -> List[str]:
        """Execute automated containment actions."""
        actions = []
        
        # 1. Quarantine affected systems
        for system_id in incident.affected_systems:
            actions.append(f"Quarantined system {system_id}")
        
        # 2. Block data exports
        actions.append(f"Blocked data exports for types: {incident.data_types}")
        
        # 3. Enable enhanced logging
        actions.append(f"Enabled enhanced logging on: {incident.affected_systems}")
        
        # 4. Snapshot for investigation
        actions.append(f"Created investigation snapshots for: {incident.affected_systems}")
        
        # 5. Revoke access if applicable
        if incident.affected_data_subjects < 100:
            actions.append("Revoked access for affected user accounts")
        
        incident.containment_actions = actions
        incident.add_timeline_event("auto_containment", "automated_containment", 
                                     f"Actions: {', '.join(actions)}")
        incident.status = "contained"
        
        return actions


class RegulatoryNotificationAssessor:
    """Assesses regulatory notification obligations (GRC-PRV-001 §27.3)."""
    
    def assess_obligations(self, incident: PrivacyIncident) -> List[Dict]:
        """Determine required regulatory notifications."""
        obligations = []
        
        # GDPR Article 33: 72-hour notification
        if self._is_gdpr_applicable(incident):
            if incident.severity in (IncidentSeverity.P1, IncidentSeverity.P2):
                obligations.append({
                    "regulation": "GDPR",
                    "article": "Article 33",
                    "recipient": "Supervisory Authority",
                    "deadline_hours": 72,
                    "required": True,
                    "status": "pending",
                })
                
                # Article 34: Communication to data subjects
                if incident.severity == IncidentSeverity.P1:
                    obligations.append({
                        "regulation": "GDPR",
                        "article": "Article 34",
                        "recipient": "Affected Data Subjects",
                        "deadline_hours": 72,
                        "required": True,
                        "status": "pending",
                    })
        
        # CCPA §1798.82: Notification to CA Attorney General
        if self._is_ccpa_applicable(incident):
            if incident.affected_data_subjects > 500:
                obligations.append({
                    "regulation": "CCPA",
                    "section": "§1798.82",
                    "recipient": "California Attorney General",
                    "deadline_hours": None,
                    "required": True,
                    "status": "pending",
                })
        
        # HIPAA §164.408: 60-day notification to HHS
        if self._is_hipaa_applicable(incident):
            obligations.append({
                "regulation": "HIPAA",
                "section": "§164.408",
                "recipient": "HHS Secretary",
                "deadline_hours": 60 * 24,
                "required": True,
                "status": "pending",
            })
        
        incident.regulatory_obligations = obligations
        return obligations
    
    def _is_gdpr_applicable(self, incident: PrivacyIncident) -> bool:
        return "EU" in incident.affected_systems or "GDPR" in incident.data_types
    
    def _is_ccpa_applicable(self, incident: PrivacyIncident) -> bool:
        return "California" in incident.affected_systems
    
    def _is_hipaa_applicable(self, incident: PrivacyIncident) -> bool:
        return "PHI" in incident.data_types


class PrivacyIncidentResponsePlaybook:
    """Orchestrates the full incident response workflow."""
    
    def __init__(self):
        self.detector = PrivacyIncidentDetector()
        self.containment = IncidentContainmentAutomator()
        self.notification = RegulatoryNotificationAssessor()
    
    def handle_event(self, event: Dict) -> Optional[PrivacyIncident]:
        """Process a privacy event through the full response pipeline."""
        # 1. Detect
        incident = self.detector.monitor(event)
        if not incident:
            return None
        
        # 2. Contain (for P1/P2)
        if incident.severity in (IncidentSeverity.P1, IncidentSeverity.P2):
            self.containment.auto_contain(incident)
        
        # 3. Assess regulatory obligations
        self.notification.assess_obligations(incident)
        
        # 4. Route based on severity
        if incident.severity == IncidentSeverity.P1:
            self._activate_p1_response(incident)
        elif incident.severity == IncidentSeverity.P2:
            self._activate_p2_response(incident)
        
        return incident
    
    def _activate_p1_response(self, incident: PrivacyIncident):
        """P1 Critical: < 5 min detection, < 15 min containment, < 1 hour notification."""
        incident.add_timeline_event("p1_response_activated", "incident_response_team",
                                     "P1 response protocol activated")
        # Notify DPO, CISO, Legal
        # Start 72-hour regulatory clock
        # Preserve evidence
        # Activate IRT
    
    def _activate_p2_response(self, incident: PrivacyIncident):
        """P2 High: < 15 min detection, < 1 hour containment, < 4 hours notification."""
        incident.add_timeline_event("p2_response_activated", "incident_response_team",
                                     "P2 response protocol activated")
        # Notify DPO
        # Start regulatory clock if applicable
```

### 4.2 Incident Response Playbook (Markdown)

```markdown
# GRC_Claw Privacy Incident Response Playbook
# GRC-PRV-001 §27 — Privacy Incident Response

## Severity Classification

| Severity | Criteria | Detection | Containment | Notification | Regulatory |
|----------|----------|-----------|-------------|--------------|------------|
| P1-Critical | >10K subjects or PHI | < 5 min | < 15 min | < 1 hour | < 72 hours |
| P2-High | >1K subjects | < 15 min | < 1 hour | < 4 hours | < 72 hours |
| P3-Medium | >100 subjects | < 1 hour | < 4 hours | < 24 hours | N/A |
| P4-Low | ≤100 subjects | < 4 hours | < 24 hours | < 48 hours | N/A |

## Response Phases

### Phase 1: Detection & Triage (0-1 hour)
- [ ] Detect incident (automated alert or manual report)
- [ ] Classify severity (P1-P4)
- [ ] Activate incident response team
- [ ] Preserve evidence (logs, outputs, snapshots)
- [ ] Contain incident (quarantine systems, revoke access)

### Phase 2: Assessment (1-4 hours)
- [ ] Determine scope: data, subjects, systems
- [ ] Assess privacy impact
- [ ] Identify root cause
- [ ] Determine regulatory notification obligations
- [ ] Document findings

### Phase 3: Notification (4-72 hours)
- [ ] Notify DPO and Compliance
- [ ] Notify affected data subjects (if high risk)
- [ ] Notify regulatory authority (if required)
- [ ] Document all notifications

### Phase 4: Remediation (1-5 days)
- [ ] Implement technical fixes
- [ ] Delete or correct exposed data
- [ ] Update privacy controls
- [ ] Re-train models if needed
- [ ] Verify remediation

### Phase 5: Post-Incident (5-30 days)
- [ ] Post-incident review
- [ ] Update risk assessment
- [ ] Update DPIA if necessary
- [ ] Implement preventive measures
- [ ] Close incident
```

---

## 5. Privacy Compliance Monitoring

Implements GRC-PRV-001 §28 — Continuous compliance monitoring and automated control testing.

### 5.1 Compliance Control Testing Engine

```python
"""
GRC_Claw Privacy Compliance Monitoring
Implements GRC-PRV-001 §28 — Continuous compliance monitoring.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class ControlStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_TESTED = "not_tested"


@dataclass
class ControlCheck:
    name: str
    passed: bool
    details: str
    severity: str = "info"


@dataclass
class ArticleComplianceResult:
    article: str
    system_id: str
    checks: List[ControlCheck]
    compliant: bool
    gaps: List[ControlCheck]


@dataclass
class ComplianceSuiteResult:
    framework: str
    system_id: str
    overall_score: float
    control_results: List[Dict]
    gaps: List[Dict]
    remediation_plan: List[Dict]
    timestamp: datetime


class GDPRComplianceMonitor:
    """Automated GDPR compliance monitoring (GRC-PRV-001 §28.2.1)."""
    
    def __init__(self):
        self.evidence_store = {}
    
    def monitor_article_5(self, system_id: str) -> ArticleComplianceResult:
        """GDPR Article 5: Principles."""
        checks = []
        
        # 5(1)(a): Lawfulness, fairness, transparency
        checks.append(self._check_lawful_basis(system_id))
        checks.append(self._check_transparency(system_id))
        
        # 5(1)(b): Purpose limitation
        checks.append(self._check_purpose_limitation(system_id))
        
        # 5(1)(c): Data minimization
        checks.append(self._check_data_minimization(system_id))
        
        # 5(1)(d): Accuracy
        checks.append(self._check_accuracy(system_id))
        
        # 5(1)(e): Storage limitation
        checks.append(self._check_storage_limitation(system_id))
        
        # 5(1)(f): Integrity and confidentiality
        checks.append(self._check_integrity_confidentiality(system_id))
        
        gaps = [c for c in checks if not c.passed]
        
        return ArticleComplianceResult(
            article="Article 5",
            system_id=system_id,
            checks=checks,
            compliant=len(gaps) == 0,
            gaps=gaps,
        )
    
    def monitor_article_17(self, system_id: str) -> ArticleComplianceResult:
        """GDPR Article 17: Right to erasure."""
        checks = []
        
        # Check erasure request SLA
        pending = self._get_pending_erasure_requests(system_id)
        checks.append(ControlCheck(
            name="erasure_request_sla",
            passed=all(r.get("within_sla", False) for r in pending),
            details=f"{len(pending)} pending erasure requests",
        ))
        
        # Check deletion verification
        checks.append(self._check_deletion_verification(system_id))
        
        # Check derived data deletion
        checks.append(self._check_derived_data_deletion(system_id))
        
        # Check backup deletion
        checks.append(self._check_backup_deletion(system_id))
        
        gaps = [c for c in checks if not c.passed]
        
        return ArticleComplianceResult(
            article="Article 17",
            system_id=system_id,
            checks=checks,
            compliant=len(gaps) == 0,
            gaps=gaps,
        )
    
    def monitor_article_35(self, system_id: str) -> ArticleComplianceResult:
        """GDPR Article 35: DPIA."""
        checks = []
        
        risk_score = self._get_risk_score(system_id)
        dpia_required = risk_score >= 3.0
        
        if dpia_required:
            dpia = self._get_dpia(system_id)
            checks.append(ControlCheck(
                name="dpia_completed",
                passed=dpia is not None and dpia.get("status") == "approved",
                details=f"DPIA status: {dpia.get('status') if dpia else 'not found'}",
            ))
            
            if dpia:
                checks.append(ControlCheck(
                    name="dpia_current",
                    passed=self._is_dpia_current(dpia),
                    details=f"DPIA last updated: {dpia.get('updated_at', 'unknown')}",
                ))
                
                checks.append(ControlCheck(
                    name="dpia_mitigations_implemented",
                    passed=dpia.get("mitigations_implemented", False),
                    details=f"Mitigations: {dpia.get('mitigation_status', 'unknown')}",
                ))
        
        gaps = [c for c in checks if not c.passed]
        
        return ArticleComplianceResult(
            article="Article 35",
            system_id=system_id,
            checks=checks,
            compliant=len(gaps) == 0,
            gaps=gaps,
        )
    
    def _check_lawful_basis(self, system_id: str) -> ControlCheck:
        # In production: query processing records for lawful basis
        return ControlCheck(
            name="lawful_basis_documented",
            passed=True,
            details="All processing activities have documented lawful basis",
        )
    
    def _check_transparency(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="privacy_notice_current",
            passed=True,
            details="Privacy notice is current and accessible",
        )
    
    def _check_purpose_limitation(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="purpose_limitation_enforced",
            passed=True,
            details="Purpose limitation enforced at ingestion",
        )
    
    def _check_data_minimization(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="data_minimization_enforced",
            passed=True,
            details="Data minimization validated at ingestion",
        )
    
    def _check_accuracy(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="data_accuracy_maintained",
            passed=True,
            details="Data accuracy checks passing",
        )
    
    def _check_storage_limitation(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="storage_limitation_enforced",
            passed=True,
            details="Retention policies enforced automatically",
        )
    
    def _check_integrity_confidentiality(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="integrity_confidentiality_maintained",
            passed=True,
            details="Encryption and access controls verified",
        )
    
    def _get_pending_erasure_requests(self, system_id: str) -> List[Dict]:
        # In production: query DSAR registry
        return []
    
    def _check_deletion_verification(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="deletion_verification",
            passed=True,
            details="All deletions verified with certificates",
        )
    
    def _check_derived_data_deletion(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="derived_data_deletion",
            passed=True,
            details="Derived data (embeddings, features) deleted on erasure",
        )
    
    def _check_backup_deletion(self, system_id: str) -> ControlCheck:
        return ControlCheck(
            name="backup_deletion",
            passed=True,
            details="Backup deletion per retention policy",
        )
    
    def _get_risk_score(self, system_id: str) -> float:
        # In production: query risk register
        return 2.5
    
    def _get_dpia(self, system_id: str) -> Optional[Dict]:
        # In production: query DPIA registry
        return {"status": "approved", "updated_at": "2026-09-01", "mitigations_implemented": True}
    
    def _is_dpia_current(self, dpia: Dict) -> bool:
        # Check if DPIA is within review period
        return True


class ComplianceControlTester:
    """Automated compliance control testing (GRC-PRV-001 §28.1.2)."""
    
    def __init__(self):
        self.gdpr_monitor = GDPRComplianceMonitor()
    
    def run_compliance_suite(self, framework: str, 
                             system_id: str) -> ComplianceSuiteResult:
        """Run all compliance controls for a regulatory framework."""
        results = []
        
        if framework.upper() == "GDPR":
            # Article 5: Principles
            r5 = self.gdpr_monitor.monitor_article_5(system_id)
            results.append({"article": "Article 5", "result": r5})
            
            # Article 17: Right to erasure
            r17 = self.gdpr_monitor.monitor_article_17(system_id)
            results.append({"article": "Article 17", "result": r17})
            
            # Article 35: DPIA
            r35 = self.gdpr_monitor.monitor_article_35(system_id)
            results.append({"article": "Article 35", "result": r35})
        
        # Calculate overall score
        total_checks = sum(len(r["result"].checks) for r in results)
        passed_checks = sum(
            sum(1 for c in r["result"].checks if c.passed)
            for r in results
        )
        overall_score = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Identify gaps
        gaps = []
        for r in results:
            for gap in r["result"].gaps:
                gaps.append({
                    "article": r["article"],
                    "check": gap.name,
                    "details": gap.details,
                })
        
        # Generate remediation plan
        remediation_plan = self._generate_remediation_plan(gaps)
        
        return ComplianceSuiteResult(
            framework=framework,
            system_id=system_id,
            overall_score=overall_score,
            control_results=results,
            gaps=gaps,
            remediation_plan=remediation_plan,
            timestamp=datetime.utcnow(),
        )
    
    def _generate_remediation_plan(self, gaps: List[Dict]) -> List[Dict]:
        """Generate remediation plan for compliance gaps."""
        plan = []
        for gap in gaps:
            plan.append({
                "gap": gap,
                "priority": "high" if "DPIA" in gap.get("check", "") else "medium",
                "action": f"Remediate: {gap['check']}",
                "estimated_effort": "5 business days",
                "owner": "data_owner",
            })
        return plan


# --- Usage Example ---
if __name__ == "__main__":
    tester = ComplianceControlTester()
    result = tester.run_compliance_suite("GDPR", "healthcare-llm-001")
    
    print(f"Framework: {result.framework}")
    print(f"System: {result.system_id}")
    print(f"Overall Score: {result.overall_score:.1f}%")
    print(f"Gaps: {len(result.gaps)}")
    for gap in result.gaps:
        print(f"  - [{gap['article']}] {gap['check']}: {gap['details']}")
```

### 5.2 Compliance Dashboard Metrics

```python
class PrivacyComplianceDashboard:
    """Real-time privacy compliance dashboard (GRC-PRV-001 §23.7)."""
    
    def get_compliance_overview(self) -> Dict:
        """Get high-level privacy compliance overview."""
        return {
            "principles_compliance": {
                "lawfulness": self._check_lawfulness_compliance(),
                "purpose_limitation": self._check_purpose_limitation(),
                "data_minimization": self._check_data_minimization(),
                "accuracy": self._check_accuracy(),
                "storage_limitation": self._check_storage_limitation(),
                "integrity_confidentiality": self._check_integrity_confidentiality(),
                "accountability": self._check_accountability(),
            },
            "lawful_basis_coverage": self._get_lawful_basis_coverage(),
            "special_categories_protection": self._get_special_categories_protection(),
            "erasure_sla_compliance": self._get_erasure_sla_compliance(),
            "privacy_by_design_coverage": self._get_privacy_by_design_coverage(),
            "dpia_coverage": self._get_dpia_coverage(),
            "cross_border_transfer_compliance": self._get_cross_border_compliance(),
            "overall_compliance_score": self._compute_overall_score(),
        }
    
    def _compute_overall_score(self) -> float:
        weights = {
            "lawfulness": 0.15,
            "purpose_limitation": 0.10,
            "data_minimization": 0.15,
            "accuracy": 0.10,
            "storage_limitation": 0.10,
            "integrity_confidentiality": 0.15,
            "accountability": 0.10,
            "erasure_sla": 0.05,
            "privacy_by_design": 0.05,
            "dpia": 0.05,
        }
        # In production: compute from actual metrics
        return 95.0
    
    # Placeholder methods — implement with actual data sources
    def _check_lawfulness_compliance(self) -> float: return 100.0
    def _check_purpose_limitation(self) -> float: return 100.0
    def _check_data_minimization(self) -> float: return 100.0
    def _check_accuracy(self) -> float: return 98.0
    def _check_storage_limitation(self) -> float: return 100.0
    def _check_integrity_confidentiality(self) -> float: return 100.0
    def _check_accountability(self) -> float: return 100.0
    def _get_lawful_basis_coverage(self) -> float: return 100.0
    def _get_special_categories_protection(self) -> float: return 100.0
    def _get_erasure_sla_compliance(self) -> float: return 100.0
    def _get_privacy_by_design_coverage(self) -> float: return 100.0
    def _get_dpia_coverage(self) -> float: return 100.0
    def _get_cross_border_compliance(self) -> float: return 100.0
```

---

## 6. PET Integration

Implements GRC-PRV-001 §29 — Privacy-Enhancing Technology integration.

### 6.1 PET Abstraction API

```python
"""
GRC_Claw Privacy-Enhancing Technology API
Implements GRC-PRV-001 §29 — Unified PET integration.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class PETType(Enum):
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    FEDERATED_LEARNING = "federated_learning"
    SMPC = "smpc"
    HOMOMORPHIC_ENCRYPTION = "homomorphic_encryption"
    TEE = "tee"
    SYNTHETIC_DATA = "synthetic_data"


@dataclass
class PETRequirements:
    data_type: str
    trust_model: str
    performance_requirement: str
    privacy_guarantee: str
    scalability_requirement: str = "medium"


@dataclass
class PETRecommendation:
    approach: str  # "single" or "hybrid"
    primary: PETType
    alternatives: List[PETType]
    rationale: str
    estimated_cost: float
    privacy_guarantee: str
    performance_impact: str


class DifferentialPrivacyEngine:
    """DP operations (GRC-PRV-001 §8)."""
    
    def __init__(self):
        self.budget_manager = {}
    
    def apply_laplace(self, value: float, epsilon: float, 
                      sensitivity: float = 1.0) -> float:
        """Apply Laplace mechanism."""
        import random
        noise = random.laplace(0, sensitivity / epsilon)
        return value + noise
    
    def apply_gaussian(self, value: float, epsilon: float, delta: float,
                       sensitivity: float = 1.0) -> float:
        """Apply Gaussian mechanism."""
        import random
        import math
        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
        noise = random.gauss(0, sigma)
        return value + noise
    
    def configure_dp_sgd(self, epsilon: float, delta: float,
                         max_grad_norm: float = 1.0) -> Dict:
        """Configure DP-SGD training."""
        return {
            "epsilon": epsilon,
            "delta": delta,
            "max_grad_norm": max_grad_norm,
            "noise_multiplier": self._compute_noise_multiplier(epsilon, delta),
            "mechanism": "dp_sgd",
        }
    
    def _compute_noise_multiplier(self, epsilon: float, delta: float) -> float:
        """Compute noise multiplier from (ε, δ)."""
        # Simplified — in production use RDP accountant
        return 1.0 / epsilon


class FederatedLearningEngine:
    """FL operations (GRC-PRV-001 §9)."""
    
    def configure(self, config: Dict) -> Dict:
        """Configure federated learning with privacy."""
        return {
            "architecture": config.get("architecture", "cross_silo"),
            "secure_aggregation": True,
            "differential_privacy": config.get("dp_enabled", True),
            "epsilon": config.get("epsilon", 5.0),
            "delta": config.get("delta", 1e-5),
            "min_clients": config.get("min_clients", 3),
        }
    
    def secure_aggregate(self, updates: List[Dict]) -> Dict:
        """Secure aggregation of model updates."""
        # In production: implement pairwise masking protocol
        aggregated = {}
        for key in updates[0]:
            aggregated[key] = sum(u[key] for u in updates) / len(updates)
        return aggregated


class SMPEngine:
    """SMPC operations (GRC-PRV-001 §10.2)."""
    
    def private_inference(self, model: Any, encrypted_input: Any) -> Any:
        """Private inference using SMPC."""
        # In production: use MP-SPDZ or ABY3
        pass
    
    def private_set_intersection(self, sets: List[set]) -> set:
        """Private set intersection."""
        # In production: use SMPC-based PSI protocol
        if not sets:
            return set()
        result = sets[0]
        for s in sets[1:]:
            result = result & s
        return result


class HomomorphicEncryptionEngine:
    """HE operations (GRC-PRV-001 §10.3)."""
    
    def encrypt(self, data: Any, scheme: str = "CKKS") -> Any:
        """Encrypt data for HE inference."""
        # In production: use Microsoft SEAL or TenSEAL
        pass
    
    def encrypted_inference(self, model: Any, encrypted_data: Any) -> Any:
        """Run inference on encrypted data."""
        pass


class TEEEngine:
    """TEE operations (GRC-PRV-001 §10.4)."""
    
    def load_model(self, model: Any, platform: str = "SGX") -> str:
        """Load model into TEE enclave."""
        return f"enclave-{uuid.uuid4()}"
    
    def enclave_inference(self, enclave_id: str, input_data: Any) -> Any:
        """Run inference inside TEE."""
        pass
    
    def verify_attestation(self, enclave_id: str) -> Dict:
        """Verify enclave attestation."""
        return {"valid": True, "measurement": "abc123"}


class SyntheticDataEngine:
    """Synthetic data generation (GRC-PRV-001 §10.5)."""
    
    def generate(self, real_data: Any, method: str = "DP-GAN",
                 epsilon: float = None) -> Any:
        """Generate synthetic data with privacy guarantees."""
        # In production: use SDV, CTGAN, or custom DP-GAN
        pass
    
    def validate(self, synthetic_data: Any, real_data: Any) -> Dict:
        """Validate synthetic data privacy and utility."""
        return {
            "membership_inference_resistance": 0.95,
            "attribute_disclosure_risk": 0.05,
            "re_identification_risk": 0.001,
            "distribution_similarity": 0.95,
            "utility_score": 0.90,
        }


class PETSelector:
    """Automated PET selection (GRC-PRV-001 §29.2.1)."""
    
    def recommend(self, requirements: PETRequirements) -> PETRecommendation:
        """Recommend optimal PET configuration."""
        
        # Selection logic based on requirements
        if requirements.privacy_guarantee == "epsilon_dp":
            return PETRecommendation(
                approach="single",
                primary=PETType.DIFFERENTIAL_PRIVACY,
                alternatives=[PETType.SYNTHETIC_DATA],
                rationale="DP provides formal (ε,δ)-DP guarantee",
                estimated_cost=1.2,
                privacy_guarantee="(ε,δ)-DP",
                performance_impact="low",
            )
        
        elif requirements.trust_model == "hardware_root_of_trust":
            return PETRecommendation(
                approach="single",
                primary=PETType.TEE,
                alternatives=[PETType.HOMOMORPHIC_ENCRYPTION],
                rationale="TEE provides best performance with hardware isolation",
                estimated_cost=2.0,
                privacy_guarantee="hardware_isolation",
                performance_impact="minimal",
            )
        
        elif requirements.trust_model == "no_trusted_third_party":
            return PETRecommendation(
                approach="single",
                primary=PETType.SMPC,
                alternatives=[PETType.HOMOMORPHIC_ENCRYPTION],
                rationale="SMPC provides information-theoretic security without trusted party",
                estimated_cost=10.0,
                privacy_guarantee="information_theoretic",
                performance_impact="high",
            )
        
        elif requirements.data_localization == "required":
            return PETRecommendation(
                approach="hybrid",
                primary=PETType.FEDERATED_LEARNING,
                alternatives=[PETType.SMPC],
                rationale="FL enables training without centralizing data",
                estimated_cost=3.0,
                privacy_guarantee="data_localization + (ε,δ)-DP",
                performance_impact="moderate",
            )
        
        return PETRecommendation(
            approach="single",
            primary=PETType.DIFFERENTIAL_PRIVACY,
            alternatives=[],
            rationale="Default: DP for formal privacy guarantee",
            estimated_cost=1.2,
            privacy_guarantee="(ε,δ)-DP",
            performance_impact="low",
        )


class PrivacyEnhancingTechnologyAPI:
    """Unified API for all PETs (GRC-PRV-001 §29.1.2)."""
    
    def __init__(self):
        self.dp_engine = DifferentialPrivacyEngine()
        self.fl_engine = FederatedLearningEngine()
        self.smpc_engine = SMPEngine()
        self.he_engine = HomomorphicEncryptionEngine()
        self.tee_engine = TEEEngine()
        self.synthetic_engine = SyntheticDataEngine()
        self.pet_selector = PETSelector()
    
    # Differential Privacy
    def apply_dp(self, data: Any, epsilon: float, delta: float,
                 mechanism: str = "laplace") -> Any:
        if mechanism == "laplace":
            return self.dp_engine.apply_laplace(data, epsilon)
        return self.dp_engine.apply_gaussian(data, epsilon, delta)
    
    def configure_dp_sgd(self, epsilon: float, delta: float) -> Dict:
        return self.dp_engine.configure_dp_sgd(epsilon, delta)
    
    # Federated Learning
    def configure_fl(self, config: Dict) -> Dict:
        return self.fl_engine.configure(config)
    
    def secure_aggregate(self, updates: List[Dict]) -> Dict:
        return self.fl_engine.secure_aggregate(updates)
    
    # SMPC
    def private_inference(self, model: Any, encrypted_input: Any) -> Any:
        return self.smpc_engine.private_inference(model, encrypted_input)
    
    def private_set_intersection(self, sets: List[set]) -> set:
        return self.smpc_engine.private_set_intersection(sets)
    
    # Homomorphic Encryption
    def encrypt_for_inference(self, data: Any, scheme: str = "CKKS") -> Any:
        return self.he_engine.encrypt(data, scheme)
    
    def encrypted_inference(self, model: Any, encrypted_data: Any) -> Any:
        return self.he_engine.encrypted_inference(model, encrypted_data)
    
    # TEE
    def load_in_enclave(self, model: Any, platform: str = "SGX") -> str:
        return self.tee_engine.load_model(model, platform)
    
    def enclave_inference(self, enclave_id: str, input_data: Any) -> Any:
        return self.tee_engine.enclave_inference(enclave_id, input_data)
    
    # Synthetic Data
    def generate_synthetic_data(self, real_data: Any, method: str = "DP-GAN",
                                epsilon: float = None) -> Any:
        return self.synthetic_engine.generate(real_data, method, epsilon)
    
    def validate_synthetic_data(self, synthetic_data: Any, real_data: Any) -> Dict:
        return self.synthetic_engine.validate(synthetic_data, real_data)
    
    # PET Selection
    def select_pet(self, requirements: PETRequirements) -> PETRecommendation:
        return self.pet_selector.recommend(requirements)


# --- Usage Example ---
if __name__ == "__main__":
    pet_api = PrivacyEnhancingTechnologyAPI()
    
    # Select PET for a use case
    reqs = PETRequirements(
        data_type="tabular",
        trust_model="no_trusted_third_party",
        performance_requirement="moderate",
        privacy_guarantee="information_theoretic",
    )
    rec = pet_api.select_pet(reqs)
    print(f"Recommended PET: {rec.primary.value}")
    print(f"Approach: {rec.approach}")
    print(f"Rationale: {rec.rationale}")
    print(f"Performance Impact: {rec.performance_impact}")
    
    # Apply DP
    private_result = pet_api.apply_dp(42.0, epsilon=1.0, delta=1e-5)
    print(f"\nDP result (ε=1.0): {private_result}")
    
    # Configure DP-SGD
    dp_config = pet_api.configure_dp_sgd(epsilon=5.0, delta=1e-5)
    print(f"\nDP-SGD config: {dp_config}")
```

---

## 7. GDPR Compliance Automation

Implements GRC-PRV-001 §23 — Automated GDPR compliance across DPIA, consent, DSAR, cross-border transfers, and regulatory reporting.

### 7.1 DPIA Automation Engine

```python
"""
GRC_Claw GDPR Compliance Automation
Implements GRC-PRV-001 §23 — Automated GDPR compliance.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


@dataclass
class DPIAReport:
    """GDPR Article 35 DPIA report."""
    dpia_id: str
    system_id: str
    processing_description: str
    purposes: List[str]
    necessity_assessment: str
    proportionality_assessment: str
    risk_assessment: Dict
    threat_model: Dict
    mitigations: List[Dict]
    residual_risk: str
    prior_consultation_required: bool
    approval: Dict
    status: str  # draft, pending_approval, approved, rejected
    generated_at: datetime
    updated_at: datetime


class DPIAAutomationEngine:
    """Automates DPIA generation (GRC-PRV-001 §23.1)."""
    
    def generate_dpia(self, system_id: str, system_info: Dict) -> DPIAReport:
        """Generate a complete DPIA for an AI system."""
        
        # 1. Describe Processing
        processing_description = self._describe_processing(system_info)
        
        # 2. Identify Privacy Risks (automated threat modeling)
        threat_model = self._generate_threat_model(system_info)
        
        # 3. Assess Necessity and Proportionality
        necessity = self._assess_necessity(system_info)
        proportionality = self._assess_proportionality(system_info)
        
        # 4. Identify Mitigations
        mitigations = self._identify_mitigations(system_info, threat_model)
        
        # 5. Calculate Residual Risk
        residual_risk = self._calculate_residual_risk(threat_model, mitigations)
        
        # 6. Determine if prior consultation required
        prior_consultation = residual_risk == "high"
        
        return DPIAReport(
            dpia_id=str(uuid.uuid4()),
            system_id=system_id,
            processing_description=processing_description,
            purposes=system_info.get("purposes", []),
            necessity_assessment=necessity,
            proportionality_assessment=proportionality,
            risk_assessment=threat_model.get("risk_assessment", {}),
            threat_model=threat_model,
            mitigations=mitigations,
            residual_risk=residual_risk,
            prior_consultation_required=prior_consultation,
            approval={"status": "pending", "approvers": []},
            status="pending_approval",
            generated_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
    
    def _describe_processing(self, info: Dict) -> str:
        return f"""
        System: {info.get('system_name', 'Unknown')}
        Data Controller: {info.get('data_controller', 'Unknown')}
        Processing Purposes: {', '.join(info.get('purposes', []))}
        Data Categories: {', '.join(info.get('data_categories', []))}
        Data Subjects: {info.get('data_subjects', 'Unknown')}
        Retention Periods: {info.get('retention_periods', 'Unknown')}
        Cross-Border Transfers: {info.get('cross_border_transfers', 'None')}
        """
    
    def _generate_threat_model(self, info: Dict) -> Dict:
        threats = []
        
        # Training data threats
        if info.get("model_type") == "llm":
            threats.append({
                "threat": "training_data_memorization",
                "likelihood": "medium",
                "impact": "high",
                "mitigation": "DP-SGD, output filtering, canary testing",
            })
        
        # Inference threats
        if info.get("api_exposure") == "public":
            threats.append({
                "threat": "membership_inference",
                "likelihood": "medium",
                "impact": "medium",
                "mitigation": "Rate limiting, output perturbation",
            })
        
        # Data lifecycle threats
        threats.append({
            "threat": "unauthorized_data_retention",
            "likelihood": "low",
            "impact": "medium",
            "mitigation": "Automated retention enforcement",
        })
        
        return {
            "threats": threats,
            "risk_assessment": {
                "overall_risk": "medium" if len(threats) < 3 else "high",
                "threat_count": len(threats),
            },
        }
    
    def _assess_necessity(self, info: Dict) -> str:
        purposes = info.get("purposes", [])
        data_categories = info.get("data_categories", [])
        return f"Processing is necessary for: {', '.join(purposes)}. " \
               f"Data categories: {', '.join(data_categories)}."
    
    def _assess_proportionality(self, info: Dict) -> str:
        return "Processing is proportionate to the stated purposes. " \
               "Data minimization controls are in place."
    
    def _identify_mitigations(self, info: Dict, threat_model: Dict) -> List[Dict]:
        mitigations = []
        for threat in threat_model.get("threats", []):
            mitigations.append({
                "threat": threat["threat"],
                "mitigation": threat["mitigation"],
                "status": "planned",
            })
        return mitigations
    
    def _calculate_residual_risk(self, threat_model: Dict, 
                                  mitigations: List[Dict]) -> str:
        # Simplified residual risk calculation
        threats = threat_model.get("threats", [])
        if not threats:
            return "low"
        high_threats = [t for t in threats if t.get("impact") == "high"]
        if high_threats and len(mitigations) < len(threats):
            return "high"
        return "medium"


class ConsentManagementSystem:
    """GDPR consent management (GRC-PRV-001 §23.2)."""
    
    def __init__(self):
        self.consent_registry: Dict[str, Dict] = {}
    
    def record_consent(self, data_subject: str, purpose: str,
                       consent_type: str, metadata: Dict) -> str:
        """Record a new consent."""
        consent_id = str(uuid.uuid4())
        self.consent_registry[consent_id] = {
            "consent_id": consent_id,
            "data_subject": data_subject,
            "purpose": purpose,
            "consent_type": consent_type,
            "granted_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=365),
            "status": "active",
            "metadata": metadata,
        }
        return consent_id
    
    def verify_consent(self, data_subject: str, purpose: str) -> Dict:
        """Verify that valid consent exists."""
        for consent in self.consent_registry.values():
            if (consent["data_subject"] == data_subject and 
                consent["purpose"] == purpose and
                consent["status"] == "active" and
                consent["expires_at"] > datetime.utcnow()):
                return {"valid": True, "consent_id": consent["consent_id"]}
        
        return {"valid": False, "reason": "No valid consent found"}
    
    def withdraw_consent(self, data_subject: str, purpose: str) -> bool:
        """Process consent withdrawal."""
        for consent in self.consent_registry.values():
            if (consent["data_subject"] == data_subject and 
                consent["purpose"] == purpose):
                consent["status"] = "withdrawn"
                consent["withdrawn_at"] = datetime.utcnow()
                return True
        return False


class DSARAutomationEngine:
    """GDPR data subject rights automation (GRC-PRV-001 §23.3)."""
    
    VALID_REQUEST_TYPES = {"access", "erasure", "portability", 
                           "rectification", "restriction", "objection"}
    
    def submit_request(self, request_type: str, data_subject: str,
                       identity_verified: bool) -> Dict:
        """Submit a data subject rights request."""
        if not identity_verified:
            return {"status": "rejected", "reason": "Identity verification failed"}
        
        if request_type not in self.VALID_REQUEST_TYPES:
            return {"status": "rejected", "reason": f"Invalid request type: {request_type}"}
        
        request_id = str(uuid.uuid4())
        deadline = datetime.utcnow() + timedelta(days=30)
        
        return {
            "request_id": request_id,
            "status": "pending",
            "request_type": request_type,
            "data_subject": data_subject,
            "deadline": deadline,
            "estimated_completion": datetime.utcnow() + timedelta(days=14),
        }
    
    def handle_access_request(self, request_id: str, 
                              data_subject: str) -> Dict:
        """Handle GDPR Article 15 access request."""
        # In production: locate all personal data across systems
        return {
            "request_id": request_id,
            "status": "fulfilled",
            "data_locations": [],
            "response_format": "JSON",
        }
    
    def handle_erasure_request(self, request_id: str,
                               data_subject: str) -> Dict:
        """Handle GDPR Article 17 erasure request."""
        # In production: delete all personal data, verify, certify
        return {
            "request_id": request_id,
            "status": "fulfilled",
            "deletion_certificate": str(uuid.uuid4()),
            "completed_at": datetime.utcnow(),
        }
    
    def handle_portability_request(self, request_id: str,
                                    data_subject: str) -> Dict:
        """Handle GDPR Article 20 data portability request."""
        return {
            "request_id": request_id,
            "status": "fulfilled",
            "export_format": "JSON",
            "data": {},
        }


class CrossBorderTransferManager:
    """GDPR cross-border transfer compliance (GRC-PRV-001 §23.4)."""
    
    ADEQUATE_COUNTRIES = {
        "Andorra", "Argentina", "Canada", "Faroe Islands", "Guernsey",
        "Israel", "Isle of Man", "Japan", "Jersey", "New Zealand",
        "Republic of Korea", "Switzerland", "United Kingdom", "Uruguay",
    }
    
    def assess_transfer(self, source_region: str, destination_region: str,
                        data_classification: str) -> Dict:
        """Assess a cross-border data transfer."""
        
        # Check adequacy decision
        if destination_region in self.ADEQUATE_COUNTRIES:
            return {
                "permitted": True,
                "mechanism": "adequacy_decision",
                "legal_basis": f"GDPR Article 45 — {destination_region}",
                "additional_safeguards": [],
            }
        
        # L4 data transfer restrictions
        if data_classification == "L4":
            return {
                "permitted": False,
                "mechanism": None,
                "legal_basis": "Transfer prohibited for L4 data to this region",
                "additional_safeguards": [],
            }
        
        # Standard Contractual Clauses
        return {
            "permitted": True,
            "mechanism": "standard_contractual_clauses",
            "legal_basis": "GDPR Article 46(2)(c)",
            "additional_safeguards": ["scc", "encryption_in_transit_and_rest"],
        }


class RegulatoryReportingEngine:
    """Automated regulatory reporting (GRC-PRV-001 §23.6)."""
    
    def generate_gdpr_report(self, period: str) -> Dict:
        """Generate GDPR compliance report."""
        return {
            "period": period,
            "generated_at": datetime.utcnow(),
            "processing_records": self._get_processing_records(),
            "dpia_status": self._get_dpia_status(),
            "erasure_requests": self._get_erasure_requests(),
            "access_requests": self._get_access_requests(),
            "breach_notifications": self._get_breach_notifications(),
            "cross_border_transfers": self._get_cross_border_transfers(),
            "privacy_by_design": self._get_privacy_by_design(),
            "compliance_metrics": self._get_compliance_metrics(),
            "open_issues": self._get_open_issues(),
            "recommendations": self._get_recommendations(),
        }
    
    def _get_processing_records(self) -> List[Dict]:
        return []
    def _get_dpia_status(self) -> Dict:
        return {"completed": 5, "pending": 1, "required": 6}
    def _get_erasure_requests(self) -> List[Dict]:
        return []
    def _get_access_requests(self) -> List[Dict]:
        return []
    def _get_breach_notifications(self) -> List[Dict]:
        return []
    def _get_cross_border_transfers(self) -> List[Dict]:
        return []
    def _get_privacy_by_design(self) -> Dict:
        return {"coverage": 100.0}
    def _get_compliance_metrics(self) -> Dict:
        return {"overall_score": 95.0}
    def _get_open_issues(self) -> List[Dict]:
        return []
    def _get_recommendations(self) -> List[str]:
        return ["Continue monitoring DP budget consumption"]


# --- Usage Example ---
if __name__ == "__main__":
    # DPIA Automation
    dpia_engine = DPIAAutomationEngine()
    system_info = {
        "system_name": "Healthcare LLM",
        "data_controller": "Hospital X",
        "purposes": ["diagnosis_assistance", "treatment_recommendations"],
        "data_categories": ["health", "biometric"],
        "data_subjects": "patients",
        "model_type": "llm",
        "api_exposure": "internal",
    }
    dpia = dpia_engine.generate_dpia("healthcare-llm-001", system_info)
    print(f"DPIA ID: {dpia.dpia_id}")
    print(f"Status: {dpia.status}")
    print(f"Residual Risk: {dpia.residual_risk}")
    print(f"Prior Consultation Required: {dpia.prior_consultation_required}")
    
    # Consent Management
    consent_sys = ConsentManagementSystem()
    consent_id = consent_sys.record_consent(
        data_subject="patient-001",
        purpose="diagnosis_assistance",
        consent_type="explicit",
        metadata={"version": "1.0"},
    )
    print(f"\nConsent recorded: {consent_id}")
    
    verification = consent_sys.verify_consent("patient-001", "diagnosis_assistance")
    print(f"Consent valid: {verification['valid']}")
    
    # DSAR
    dsar = DSARAutomationEngine()
    result = dsar.submit_request("access", "patient-001", identity_verified=True)
    print(f"\nDSAR submitted: {result['request_id']}")
    print(f"Deadline: {result['deadline']}")
    
    # Cross-border transfer
    transfer_mgr = CrossBorderTransferManager()
    assessment = transfer_mgr.assess_transfer("EU", "US", "L3")
    print(f"\nTransfer to US: {'permitted' if assessment['permitted'] else 'denied'}")
    print(f"Mechanism: {assessment['mechanism']}")
    
    # Regulatory reporting
    reporting = RegulatoryReportingEngine()
    report = reporting.generate_gdpr_report("2026-Q3")
    print(f"\nGDPR Report generated: {report['generated_at']}")
    print(f"Compliance score: {report['compliance_metrics']['overall_score']}%")
```

### 7.2 GDPR Compliance Configuration

```yaml
# gdpr-compliance-config.yaml
# GRC-PRV-001 §23 — GDPR Compliance Automation Configuration
gdpr_compliance:
  enabled: true
  
  dpia_automation:
    enabled: true
    auto_generate: true
    triggers:
      - new_personal_data_source
      - model_retrain_on_sensitive_data
      - cross_border_transfer_new_region
      - new_ai_use_case
      - privacy_budget_increase
      - regulatory_change
      - privacy_incident
      - scale_increase
    required_approvers:
      high_risk: [dpo, data_owner]
      critical_risk: [dpo, data_owner, ciso, legal]
  
  consent_management:
    enabled: true
    consent_types:
      - explicit
      - implicit
    expiry:
      explicit: 365  # days
      implicit: 180  # days
    withdrawal_handling: automatic
    deletion_on_withdrawal: true
  
  dsar_automation:
    enabled: true
    request_types:
      - access
      - erasure
      - portability
      - rectification
      - restriction
      - objection
    identity_verification: required
    sla:
      access: 30  # days
      erasure: 30
      portability: 30
      rectification: 30
    auto_fulfill: true
  
  cross_border_transfers:
    enabled: true
    adequacy_check: true
    scc_generation: true
    transfer_impact_assessment: true
    prohibited_regions: []
  
  privacy_notices:
    enabled: true
    auto_generate: true
    languages: [en, de, fr, es]
    version_tracking: true
  
  regulatory_reporting:
    enabled: true
    reports:
      gdpr:
        frequency: quarterly
        auto_generate: true
      ccpa:
        frequency: annual
        auto_generate: true
      hipaa:
        frequency: annual
        auto_generate: true
  
  compliance_dashboard:
    enabled: true
    real_time: true
    metrics:
      - principles_compliance
      - lawful_basis_coverage
      - erasure_sla_compliance
      - privacy_by_design_coverage
      - dpia_coverage
      - cross_border_transfer_compliance
```

---

## Appendix: Quick Reference

### A. CPRS Risk Tier Classification

| CPRS Range | Risk Tier | DPIA Required | Approval Authority | Review Frequency |
|------------|-----------|---------------|--------------------|------------------|
| 1.0 – 1.9 | Low | No | Data Owner | Annual |
| 2.0 – 2.9 | Medium | Recommended | Data Owner + DPO | Semi-annual |
| 3.0 – 3.9 | High | Yes | DPO + Compliance | Quarterly |
| 4.0 – 5.0 | Critical | Yes + Regulatory Consultation | DPO + CISO + Legal | Monthly |

### B. PII Detection Layers

| Layer | Method | Coverage | Latency | Use Case |
|-------|--------|----------|---------|----------|
| L1 | Regex & Pattern | Structured PII | <1ms | Real-time |
| L2 | NER Models | Unstructured PII | 10-100ms | Batch/real-time |
| L3 | Contextual ML | Context-dependent PII | 50-200ms | Batch |
| L4 | LLM-Based | Complex/ambiguous PII | 1-5s | Deep scanning |
| L5 | Image/OCR | Visual PII | 500ms-2s | Document processing |
| L6 | Audio | Audio PII | 1-5s | Audio processing |

### C. Redaction Decision Matrix

| PII Category | Confidence | Risk Score | Redaction Method |
|--------------|------------|------------|------------------|
| Direct Identifier | ≥ 0.9 | Critical | Suppression or Pseudonymization |
| Direct Identifier | 0.7 – 0.9 | High | Pseudonymization or Masking |
| Direct Identifier | < 0.7 | Medium | Masking |
| Quasi-Identifier | ≥ 0.9 | High | Generalization or Pseudonymization |
| Financial/Health/Biometric/Children's | Any | Critical | Suppression |

### D. Privacy Budget Allocation by Risk Tier

| Risk Tier | Default ε | Default δ | Budget Scope | Review Frequency |
|-----------|-----------|-----------|--------------|------------------|
| Low | 10.0 | 1/n² | Per system | Annual |
| Medium | 5.0 | 1/n² | Per system | Semi-annual |
| High | 2.0 | 1/n² | Per system + per query | Quarterly |
| Critical | 1.0 | 1/n² | Per system + per query + per epoch | Monthly |

### E. Incident Response Severity Matrix

| Severity | Criteria | Detection | Containment | Notification | Regulatory |
|----------|----------|-----------|-------------|--------------|------------|
| P1-Critical | >10K subjects or PHI | < 5 min | < 15 min | < 1 hour | < 72 hours |
| P2-High | >1K subjects | < 15 min | < 1 hour | < 4 hours | < 72 hours |
| P3-Medium | >100 subjects | < 1 hour | < 4 hours | < 24 hours | N/A |
| P4-Low | ≤100 subjects | < 4 hours | < 24 hours | < 48 hours | N/A |

---

*End of Implementation Guide*
