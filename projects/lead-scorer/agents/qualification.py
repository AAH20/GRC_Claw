"""Qualification agent — applies BANT/MEDDIC criteria to qualify leads."""

from __future__ import annotations

from langchain_core.language_models import BaseLanguageModel
from pydantic import BaseModel, Field

from agents.base import AgentConfig, AgentContext, AgentResult, BaseAgent


class QualificationInput(BaseModel):
    """Input for the Qualification agent."""

    lead_id: str = Field(..., description="Lead identifier")
    company_name: str = Field(..., description="Company name")
    framework: str = Field(
        default="BANT",
        description="Qualification framework: BANT, MEDDIC, or CHAMP",
    )
    budget: str | None = Field(None, description="Budget information")
    authority: str | None = Field(None, description="Decision maker info")
    need: str | None = Field(None, description="Pain points / needs")
    timeline: str | None = Field(None, description="Purchase timeline")
    metrics: str | None = Field(None, description="Success metrics (MEDDIC)")
    economic_buyer: str | None = Field(None, description="Economic buyer (MEDDIC)")
    decision_criteria: str | None = Field(None, description="Decision criteria (MEDDIC)")
    decision_process: str | None = Field(None, description="Decision process (MEDDIC)")
    identify_pain: str | None = Field(None, description="Pain identification (MEDDIC)")
    champion: str | None = Field(None, description="Internal champion (MEDDIC/CHAMP)")


class CriterionScore(BaseModel):
    """Score for a single qualification criterion."""

    criterion: str
    status: str = Field(..., description="met, partial, unknown, or unmet")
    score: float = Field(ge=0.0, le=1.0)
    evidence: str = ""
    notes: str = ""


class QualificationOutput(BaseModel):
    """Output from the Qualification agent."""

    lead_id: str
    framework: str
    qualified: bool
    qualification_score: float = Field(ge=0.0, le=1.0)
    criteria: list[CriterionScore] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    summary: str = ""


class QualificationAgent(BaseAgent[QualificationInput, QualificationOutput]):
    """Applies BANT/MEDDIC/CHAMP qualification criteria to leads.

    Evaluates leads against a structured qualification framework
    to determine sales readiness.
    """

    name = "qualification"
    description = "Applies BANT/MEDDIC criteria to qualify/disqualify leads"

    FRAMEWORK_CRITERIA: dict[str, list[str]] = {
        "BANT": ["budget", "authority", "need", "timeline"],
        "MEDDIC": [
            "metrics", "economic_buyer", "decision_criteria",
            "decision_process", "identify_pain", "champion",
        ],
        "CHAMP": ["challenges", "authority", "money", "priority"],
    }

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        config: AgentConfig | None = None,
    ) -> None:
        default_config = AgentConfig(
            enabled=True,
            timeout_seconds=30.0,
            max_retries=1,
        )
        if config:
            default_config = config
        super().__init__(llm=llm, config=default_config)

    @property
    def input_model(self) -> type[QualificationInput]:
        return QualificationInput

    @property
    def output_model(self) -> type[QualificationOutput]:
        return QualificationOutput

    async def run(
        self, input_data: QualificationInput, context: AgentContext
    ) -> AgentResult[QualificationOutput]:
        """Run qualification assessment.

        Args:
            input_data: Lead qualification data.
            context: Execution context.

        Returns:
            Qualification output with criteria scores and overall assessment.
        """
        try:
            framework = input_data.framework.upper()
            if framework not in self.FRAMEWORK_CRITERIA:
                return AgentResult(
                    success=False,
                    error=f"Unsupported framework: {framework}. "
                           f"Use BANT, MEDDIC, or CHAMP.",
                )

            criteria = self._evaluate_criteria(input_data, framework)
            qual_score = self._compute_qualification_score(criteria)
            qualified = qual_score >= 0.6  # 60% threshold

            next_steps = self._generate_next_steps(criteria, qualified)
            risk_factors = self._identify_risks(criteria)

            output = QualificationOutput(
                lead_id=input_data.lead_id,
                framework=framework,
                qualified=qualified,
                qualification_score=round(qual_score, 2),
                criteria=criteria,
                next_steps=next_steps,
                risk_factors=risk_factors,
                summary=self._build_summary(qualified, qual_score, criteria),
            )
            return AgentResult(success=True, data=output)

        except Exception as exc:
            return AgentResult(
                success=False,
                error=f"Qualification failed: {exc}",
            )

    def _evaluate_criteria(
        self, data: QualificationInput, framework: str
    ) -> list[CriterionScore]:
        """Evaluate each criterion in the framework.

        Args:
            data: Lead qualification data.
            framework: Framework name.

        Returns:
            List of criterion scores.
        """
        criteria_names = self.FRAMEWORK_CRITERIA[framework]
        data_dict = data.model_dump()

        results: list[CriterionScore] = []
        for criterion in criteria_names:
            value = data_dict.get(criterion)
            if value and str(value).strip():
                status = "met"
                score = 1.0
                evidence = str(value)[:200]
            else:
                status = "unknown"
                score = 0.0
                evidence = ""

            results.append(
                CriterionScore(
                    criterion=criterion,
                    status=status,
                    score=score,
                    evidence=evidence,
                )
            )
        return results

    def _compute_qualification_score(
        self, criteria: list[CriterionScore]
    ) -> float:
        """Compute overall qualification score.

        Args:
            criteria: List of criterion scores.

        Returns:
            Average score across all criteria.
        """
        if not criteria:
            return 0.0
        return sum(c.score for c in criteria) / len(criteria)

    def _generate_next_steps(
        self, criteria: list[CriterionScore], qualified: bool
    ) -> list[str]:
        """Generate recommended next steps.

        Args:
            criteria: Criterion scores.
            qualified: Whether the lead is qualified.

        Returns:
            List of next step recommendations.
        """
        steps: list[str] = []
        unmet = [c for c in criteria if c.status != "met"]

        if qualified:
            steps.append("Lead is qualified — route to sales for follow-up")
            if unmet:
                steps.append(
                    f"Address {len(unmet)} remaining criteria: "
                    f"{', '.join(c.criterion for c in unmet)}"
                )
        else:
            steps.append("Lead is not yet qualified — continue nurturing")
            for c in unmet:
                steps.append(f"Gather information on: {c.criterion}")

        return steps

    def _identify_risks(self, criteria: list[CriterionScore]) -> list[str]:
        """Identify qualification risk factors.

        Args:
            criteria: Criterion scores.

        Returns:
            List of risk factor descriptions.
        """
        risks: list[str] = []
        unmet = [c for c in criteria if c.status == "unknown"]

        if len(unmet) > len(criteria) / 2:
            risks.append("Majority of qualification criteria are unknown")

        critical = {"budget", "authority", "economic_buyer", "champion"}
        critical_unmet = [c for c in unmet if c.criterion in critical]
        if critical_unmet:
            risks.append(
                f"Critical criteria missing: {', '.join(c.criterion for c in critical_unmet)}"
            )

        return risks

    def _build_summary(
        self, qualified: bool, score: float, criteria: list[CriterionScore]
    ) -> str:
        """Build qualification summary.

        Args:
            qualified: Whether qualified.
            score: Qualification score.
            criteria: Criterion scores.

        Returns:
            Summary string.
        """
        status = "QUALIFIED" if qualified else "NOT QUALIFIED"
        met = sum(1 for c in criteria if c.status == "met")
        total = len(criteria)
        return (
            f"Lead is {status} with score {score:.0%}. "
            f"{met}/{total} criteria met."
        )
