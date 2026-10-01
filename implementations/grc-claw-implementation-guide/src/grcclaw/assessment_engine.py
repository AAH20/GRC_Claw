"""Assessment engine — evaluates AI systems against technical criteria."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    Assessment,
    AssessmentCriterion,
    AssessmentResult,
    AssessmentStatus,
    AssessmentType,
    ComplianceStatus,
    Evidence,
    EvidenceContext,
    EvidenceDecision,
    EvidenceSubject,
    EvidenceType,
)
from .evidence_generator import DefaultEvidenceGenerator, EvidenceGenerator


class AssessmentEngine(ABC):
    """Abstract assessment engine interface."""

    @abstractmethod
    def run_assessment(
        self,
        system_id: str,
        assessment_type: AssessmentType,
        config: dict[str, Any],
    ) -> Assessment:
        """Run a technical assessment on an AI system."""
        ...

    @abstractmethod
    def get_assessment(self, assessment_id: str) -> Assessment:
        """Retrieve a completed assessment."""
        ...

    @abstractmethod
    def compare_assessments(
        self,
        assessment_id_1: str,
        assessment_id_2: str,
    ) -> dict[str, Any]:
        """Compare two assessments."""
        ...


class DefaultAssessmentEngine(AssessmentEngine):
    """Default assessment engine implementation."""

    def __init__(self, evidence_generator: Optional[EvidenceGenerator] = None):
        self.evidence_generator = evidence_generator or DefaultEvidenceGenerator()
        self._assessments: dict[str, Assessment] = {}

    def run_assessment(
        self,
        system_id: str,
        assessment_type: AssessmentType,
        config: dict[str, Any],
    ) -> Assessment:
        """Run a technical assessment on an AI system."""
        assessment_id = f"ASSESS-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:8].upper()}"

        # Build criteria from config
        criteria = self._build_criteria(assessment_type, config)

        # Evaluate each criterion
        results: list[AssessmentResult] = []
        evidence_list: list[Evidence] = []

        for criterion in criteria:
            result = self._evaluate_criterion(criterion, system_id, config)
            results.append(result)

            # Generate evidence for this result
            if result.passed or result.score > 0:
                evidence = self.evidence_generator.generate(
                    event_type=EvidenceType.ASSESSMENT_RESULT,
                    subject=EvidenceSubject(
                        agent_id=system_id,
                        action="assessment",
                        resource=system_id,
                    ),
                    decision=EvidenceDecision(
                        effect="allow" if result.passed else "warn",
                        reason=f"Criterion '{criterion.name}': score {result.score:.2f}",
                        confidence=result.score,
                    ),
                    context=EvidenceContext(
                        environment=config.get("environment", "production"),
                        trace_id=config.get("trace_id", ""),
                    ),
                    compliance_tags=list(criterion.framework_mapping.values()),
                )
                evidence_list.append(evidence)

        # Compute overall score
        overall_score = 0.0
        if results:
            total_weight = sum(c.weight for c in criteria)
            if total_weight > 0:
                overall_score = sum(
                    r.score * next((c.weight for c in criteria if c.criterion_id == r.criterion_id), 1.0)
                    for r in results
                ) / total_weight
            else:
                overall_score = sum(r.score for r in results) / len(results)

        # Determine overall result
        if overall_score >= 0.8:
            overall_result = ComplianceStatus.COMPLIANT
        elif overall_score >= 0.5:
            overall_result = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_result = ComplianceStatus.NON_COMPLIANT

        assessment = Assessment(
            assessment_id=assessment_id,
            system_id=system_id,
            assessment_type=assessment_type,
            criteria=criteria,
            results=results,
            overall_score=round(overall_score, 4),
            overall_result=overall_result,
            evidence=evidence_list,
            assessor="assessment-engine",
            status=AssessmentStatus.COMPLETED,
            framework=config.get("framework", ""),
            control_ids=config.get("control_ids", []),
            assessment_period_start=datetime.now(timezone.utc),
            assessment_period_end=datetime.now(timezone.utc),
            methodology=config.get("methodology", "automated"),
            assessor_type="automated",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        self._assessments[assessment_id] = assessment
        return assessment

    def get_assessment(self, assessment_id: str) -> Assessment:
        """Retrieve a completed assessment."""
        if assessment_id not in self._assessments:
            raise KeyError(f"Assessment not found: {assessment_id}")
        return self._assessments[assessment_id]

    def compare_assessments(
        self,
        assessment_id_1: str,
        assessment_id_2: str,
    ) -> dict[str, Any]:
        """Compare two assessments."""
        a1 = self.get_assessment(assessment_id_1)
        a2 = self.get_assessment(assessment_id_2)

        score_diff = a2.overall_score - a1.overall_score

        return {
            "assessment_1": assessment_id_1,
            "assessment_2": assessment_id_2,
            "score_1": a1.overall_score,
            "score_2": a2.overall_score,
            "score_difference": round(score_diff, 4),
            "improved": score_diff > 0,
            "criteria_changes": [
                {
                    "criterion_id": r1.criterion_id,
                    "score_1": r1.score,
                    "score_2": next(
                        (r2.score for r2 in a2.results if r2.criterion_id == r1.criterion_id),
                        0.0,
                    ),
                }
                for r1 in a1.results
            ],
        }

    def _build_criteria(
        self,
        assessment_type: AssessmentType,
        config: dict[str, Any],
    ) -> list[AssessmentCriterion]:
        """Build assessment criteria from config."""
        criteria_config = config.get("criteria", [])
        if criteria_config:
            return [
                AssessmentCriterion(
                    criterion_id=c.get("id", f"crit-{i}"),
                    name=c.get("name", f"Criterion {i}"),
                    description=c.get("description", ""),
                    framework_mapping=c.get("framework_mapping", {}),
                    test_method=c.get("test_method", "default"),
                    threshold=c.get("threshold", 0.8),
                    weight=c.get("weight", 1.0),
                )
                for i, c in enumerate(criteria_config)
            ]

        # Default criteria based on assessment type
        return self._default_criteria(assessment_type)

    def _default_criteria(self, assessment_type: AssessmentType) -> list[AssessmentCriterion]:
        """Get default criteria for an assessment type."""
        defaults = {
            AssessmentType.FAIRNESS: [
                AssessmentCriterion(
                    criterion_id="fairness-demographic-parity",
                    name="Demographic Parity",
                    description="Demographic parity ratio across groups",
                    framework_mapping={"iso-42001": "6.1", "nist-ai-rmf": "MEASURE"},
                    test_method="fairlearn.MetricFrame",
                    threshold=0.8,
                    weight=1.0,
                ),
                AssessmentCriterion(
                    criterion_id="fairness-equal-opportunity",
                    name="Equal Opportunity",
                    description="Equal opportunity across groups",
                    framework_mapping={"iso-42001": "6.1"},
                    test_method="fairlearn.MetricFrame",
                    threshold=0.8,
                    weight=1.0,
                ),
            ],
            AssessmentType.ROBUSTNESS: [
                AssessmentCriterion(
                    criterion_id="robustness-adversarial",
                    name="Adversarial Robustness",
                    description="Robustness against adversarial inputs",
                    framework_mapping={"iso-42001": "8.1", "nist-ai-rmf": "MEASURE"},
                    test_method="promptfoo",
                    threshold=0.7,
                    weight=1.0,
                ),
            ],
            AssessmentType.SECURITY: [
                AssessmentCriterion(
                    criterion_id="security-prompt-injection",
                    name="Prompt Injection Resistance",
                    description="Resistance to prompt injection attacks",
                    framework_mapping={"owasp-llm": "LLM01"},
                    test_method="custom",
                    threshold=0.9,
                    weight=1.0,
                ),
            ],
        }
        return defaults.get(assessment_type, [
            AssessmentCriterion(
                criterion_id="generic-assessment",
                name="Generic Assessment",
                description="Generic assessment criterion",
                framework_mapping={},
                test_method="default",
                threshold=0.8,
                weight=1.0,
            )
        ])

    def _evaluate_criterion(
        self,
        criterion: AssessmentCriterion,
        system_id: str,
        config: dict[str, Any],
    ) -> AssessmentResult:
        """Evaluate a single criterion.

        In production, this invokes the actual test method (fairlearn, SHAP, etc.).
        This is a reference implementation that returns simulated results.
        """
        # Reference implementation — production runs actual tests
        import random
        random.seed(hash(criterion.criterion_id + system_id))
        score = round(random.uniform(0.6, 1.0), 4)

        return AssessmentResult(
            criterion_id=criterion.criterion_id,
            score=score,
            passed=score >= criterion.threshold,
            details={
                "test_method": criterion.test_method,
                "threshold": criterion.threshold,
                "system_id": system_id,
            },
            evidence_refs=[],
        )
