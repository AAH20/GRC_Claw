"""Compliance mapper — cross-framework control mapping."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    Compliance,
    ComplianceControlMapping,
    ComplianceMapping,
    ComplianceStatus,
    Evidence,
    EvidenceType,
    FrameworkMapping,
    ObligationLevel,
)


class ComplianceMapper(ABC):
    """Abstract compliance mapper interface."""

    @abstractmethod
    def map_control(
        self,
        control_id: str,
        frameworks: Optional[list[str]] = None,
    ) -> ComplianceMapping:
        """Get the compliance mapping for a control."""
        ...

    @abstractmethod
    def get_framework_controls(
        self,
        framework: str,
        version: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get all controls for a specific framework."""
        ...

    @abstractmethod
    def generate_evidence_package(
        self,
        control_ids: list[str],
        framework: str,
    ) -> dict[str, Any]:
        """Generate an evidence package for a set of controls."""
        ...


class DefaultComplianceMapper(ComplianceMapper):
    """Default compliance mapper implementation."""

    def __init__(self):
        self._mappings: dict[str, ComplianceMapping] = {}
        self._frameworks: dict[str, dict[str, Any]] = {}
        self._initialize_default_frameworks()

    def map_control(
        self,
        control_id: str,
        frameworks: Optional[list[str]] = None,
    ) -> ComplianceMapping:
        """Get the compliance mapping for a control."""
        if control_id in self._mappings:
            mapping = self._mappings[control_id]
            if frameworks:
                # Filter by requested frameworks
                filtered = {
                    k: v for k, v in mapping.framework_mappings.items()
                    if k in frameworks
                }
                return ComplianceMapping(
                    mapping_id=mapping.mapping_id,
                    control_id=mapping.control_id,
                    control_name=mapping.control_name,
                    description=mapping.description,
                    framework_mappings=filtered,
                    evidence_requirements=mapping.evidence_requirements,
                    assessment_criteria=mapping.assessment_criteria,
                )
            return mapping

        # Create a default mapping
        return self._create_default_mapping(control_id, frameworks)

    def get_framework_controls(
        self,
        framework: str,
        version: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get all controls for a specific framework."""
        fw = self._frameworks.get(framework, {})
        return fw.get("controls", [])

    def generate_evidence_package(
        self,
        control_ids: list[str],
        framework: str,
    ) -> dict[str, Any]:
        """Generate an evidence package for a set of controls."""
        package_id = f"PKG-{uuid.uuid4().hex[:8].upper()}"

        controls = []
        for cid in control_ids:
            mapping = self.map_control(cid, [framework])
            controls.append({
                "control_id": cid,
                "control_name": mapping.control_name,
                "framework_mappings": {
                    k: {
                        "control_ids": v.control_ids,
                        "section_refs": v.section_refs,
                        "obligation_level": v.obligation_level.value,
                    }
                    for k, v in mapping.framework_mappings.items()
                },
                "evidence_requirements": [
                    {
                        "type": er.evidence_type.value,
                        "criteria": er.criteria,
                        "threshold": er.threshold,
                    }
                    for er in mapping.evidence_requirements
                ],
            })

        return {
            "package_id": package_id,
            "framework": framework,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "controls": controls,
            "oscal_version": "1.1",
        }

    def compute_compliance(
        self,
        organization_id: str,
        framework: str,
        evidence_items: list[Evidence],
        scope_type: str = "organization",
        scope_id: str = "",
    ) -> Compliance:
        """Compute compliance posture from evidence."""
        fw = self._frameworks.get(framework, {})
        controls = fw.get("controls", [])

        control_mappings: list[ComplianceControlMapping] = []
        compliant = 0
        partial = 0
        non_compliant = 0
        not_assessed = 0

        for ctrl in controls:
            ctrl_id = ctrl.get("id", "")
            ctrl_evidence = [
                e for e in evidence_items
                if ctrl_id in e.compliance_tags
            ]

            if not ctrl_evidence:
                status = ComplianceStatus.NOT_ASSESSED
                not_assessed += 1
            elif len(ctrl_evidence) >= 2:
                status = ComplianceStatus.COMPLIANT
                compliant += 1
            else:
                status = ComplianceStatus.PARTIALLY_COMPLIANT
                partial += 1

            control_mappings.append(ComplianceControlMapping(
                control_id=ctrl_id,
                control_title=ctrl.get("title", ""),
                control_family=ctrl.get("family", ""),
                status=status,
                evidence_ids=[e.evidence_id for e in ctrl_evidence],
            ))

        total = len(controls)
        score = 0.0
        if total > 0:
            score = round((compliant + partial * 0.5) / total, 4)

        if score >= 0.8:
            overall = ComplianceStatus.COMPLIANT
        elif score >= 0.5:
            overall = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall = ComplianceStatus.NON_COMPLIANT

        return Compliance(
            organization_id=organization_id,
            scope_type=scope_type,
            scope_id=scope_id,
            framework=framework,
            framework_name=fw.get("name", framework),
            overall_status=overall,
            compliance_score=score,
            control_mappings=control_mappings,
            total_controls=total,
            compliant_controls=compliant,
            partial_controls=partial,
            non_compliant_controls=non_compliant,
            not_assessed_controls=not_assessed,
            coverage_percentage=round((compliant + partial) / total * 100, 2) if total > 0 else 0.0,
            total_evidence_items=len(evidence_items),
        )

    def add_mapping(self, mapping: ComplianceMapping) -> None:
        """Add a compliance mapping."""
        self._mappings[mapping.control_id] = mapping

    def _create_default_mapping(
        self,
        control_id: str,
        frameworks: Optional[list[str]] = None,
    ) -> ComplianceMapping:
        """Create a default mapping for a control."""
        target_frameworks = frameworks or ["iso-42001", "nist-ai-rmf", "eu-ai-act"]

        framework_mappings: dict[str, FrameworkMapping] = {}
        for fw in target_frameworks:
            framework_mappings[fw] = FrameworkMapping(
                framework=fw,
                version="2023" if fw == "iso-42001" else "1.0",
                control_ids=[control_id],
                obligation_level=ObligationLevel.MANDATORY,
            )

        return ComplianceMapping(
            mapping_id=f"MAP-{uuid.uuid4().hex[:8].upper()}",
            control_id=control_id,
            control_name=f"Control {control_id}",
            description=f"Auto-generated mapping for {control_id}",
            framework_mappings=framework_mappings,
            evidence_requirements=[],
        )

    def _initialize_default_frameworks(self) -> None:
        """Initialize default framework definitions."""
        self._frameworks = {
            "iso-42001": {
                "name": "ISO/IEC 42001:2023",
                "version": "2023",
                "controls": [
                    {"id": "4", "title": "Context of the Organization", "family": "Context"},
                    {"id": "5", "title": "Leadership", "family": "Leadership"},
                    {"id": "6", "title": "Planning", "family": "Planning"},
                    {"id": "7", "title": "Support", "family": "Support"},
                    {"id": "8", "title": "Operation", "family": "Operation"},
                    {"id": "9", "title": "Performance Evaluation", "family": "Performance"},
                    {"id": "10", "title": "Improvement", "family": "Improvement"},
                ],
            },
            "nist-ai-rmf": {
                "name": "NIST AI RMF 1.0",
                "version": "1.0",
                "controls": [
                    {"id": "GOVERN", "title": "Govern", "family": "GOVERN"},
                    {"id": "MAP", "title": "Map", "family": "MAP"},
                    {"id": "MEASURE", "title": "Measure", "family": "MEASURE"},
                    {"id": "MANAGE", "title": "Manage", "family": "MANAGE"},
                ],
            },
            "eu-ai-act": {
                "name": "EU AI Act",
                "version": "2024",
                "controls": [
                    {"id": "Article 9", "title": "Risk Management", "family": "Risk"},
                    {"id": "Article 10", "title": "Data Governance", "family": "Data"},
                    {"id": "Article 11", "title": "Technical Documentation", "family": "Documentation"},
                    {"id": "Article 12", "title": "Record Keeping", "family": "Records"},
                    {"id": "Article 13", "title": "Transparency", "family": "Transparency"},
                    {"id": "Article 14", "title": "Human Oversight", "family": "Oversight"},
                    {"id": "Article 15", "title": "Accuracy and Robustness", "family": "Quality"},
                ],
            },
            "owasp-llm": {
                "name": "OWASP Top 10 for LLM Applications 2025",
                "version": "2025",
                "controls": [
                    {"id": "LLM01", "title": "Prompt Injection", "family": "Security"},
                    {"id": "LLM02", "title": "Insecure Output Handling", "family": "Security"},
                    {"id": "LLM03", "title": "Training Data Poisoning", "family": "Data"},
                    {"id": "LLM04", "title": "Model Denial of Service", "family": "Availability"},
                    {"id": "LLM05", "title": "Supply Chain Vulnerabilities", "family": "Supply Chain"},
                    {"id": "LLM06", "title": "Sensitive Information Disclosure", "family": "Privacy"},
                    {"id": "LLM07", "title": "Insecure Plugin Design", "family": "Security"},
                    {"id": "LLM08", "title": "Excessive Agency", "family": "Governance"},
                    {"id": "LLM09", "title": "Overreliance", "family": "Governance"},
                    {"id": "LLM10", "title": "Model Theft", "family": "Security"},
                ],
            },
        }
