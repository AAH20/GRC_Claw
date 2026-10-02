"""ATS compatibility agent using LangChain DeepAgents."""

import json
from typing import Any

from job_description_optimizer.agents import BaseAgent
from job_description_optimizer.models import ATSReport, JobDescription


class ATSCompatibilityAgent(BaseAgent[JobDescription, ATSReport]):
    """Agent that ensures job descriptions are compatible with Applicant Tracking Systems.

    Uses LangChain DeepAgents to check formatting, keyword matching,
    and structural elements that affect ATS parsing.
    """

    @property
    def name(self) -> str:
        """Get the agent name."""
        return "ats_compatibility"

    @property
    def description(self) -> str:
        """Get the agent description."""
        return "Ensures job descriptions are compatible with Applicant Tracking Systems"

    def _build_system_prompt(self) -> str:
        """Build the system prompt for ATS compatibility checking.

        Returns:
            System prompt string.
        """
        return """You are an expert in Applicant Tracking Systems (ATS) and recruitment technology.

Your task is to analyze job descriptions for ATS compatibility. Common ATS systems include
Workday, Greenhouse, Lever, Taleo, iCIMS, and BambooHR. Focus on:

1. **Formatting Issues**: Tables, text boxes, headers/footers, images, and special characters
   that ATS cannot parse
2. **Keyword Matching**: Ensure important skills and qualifications are explicitly stated
   (not implied) for keyword matching algorithms
3. **Section Structure**: Clear, standard section headings (e.g., "Responsibilities",
   "Qualifications", "Requirements", "About Us")
4. **File Format Considerations**: Recommend plain text or simple formatting
5. **Acronym Handling**: Spell out acronyms at least once for better matching
6. **Date Formats**: Use standard date formats for experience requirements

Return your analysis in the following JSON format:
{
    "compatible_text": "the job description reformatted for ATS compatibility",
    "ats_score": 0.0-1.0,
    "issues": ["issue1", "issue2"],
    "warnings": ["warning1", "warning2"],
    "formatting_suggestions": ["suggestion1", "suggestion2"],
    "keyword_matches": {
        "keyword1": true,
        "keyword2": false
    }
}

Be specific about what will cause ATS parsing failures."""

    async def analyze(self, input_data: JobDescription) -> ATSReport:
        """Analyze job description for ATS compatibility.

        Args:
            input_data: Job description to analyze.

        Returns:
            ATSReport with compatibility analysis and suggestions.
        """
        prompt = f"""Check the following job description for ATS compatibility:

Title: {input_data.title}
Description: {input_data.description}
Company: {input_data.company or 'Not specified'}
Location: {input_data.location or 'Not specified'}
Skills: {', '.join(input_data.skills) if input_data.skills else 'Not specified'}
Responsibilities: {', '.join(input_data.responsibilities) if input_data.responsibilities else 'Not specified'}
Qualifications: {', '.join(input_data.qualifications) if input_data.qualifications else 'Not specified'}
Employment Type: {input_data.employment_type or 'Not specified'}
Experience Level: {input_data.experience_level or 'Not specified'}

Provide your analysis in the specified JSON format."""

        response = await self._invoke_llm(prompt)

        try:
            data: dict[str, Any] = json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(response[start:end])
            else:
                data = {
                    "compatible_text": input_data.description,
                    "ats_score": 0.5,
                    "issues": [],
                    "warnings": ["Unable to parse ATS analysis results"],
                    "formatting_suggestions": [],
                    "keyword_matches": {},
                }

        return ATSReport(
            original_text=input_data.description,
            compatible_text=data.get("compatible_text", input_data.description),
            ats_score=float(data.get("ats_score", 0.5)),
            issues=data.get("issues", []),
            warnings=data.get("warnings", []),
            formatting_suggestions=data.get("formatting_suggestions", []),
            keyword_matches=data.get("keyword_matches", {}),
        )

    def get_capabilities(self) -> list[str]:
        """Get list of agent capabilities.

        Returns:
            List of capability strings.
        """
        return [
            "ats_formatting_check",
            "keyword_matching",
            "section_structure_analysis",
            "parsing_optimization",
            "compatibility_scoring",
        ]
