"""SemanticMatcherAgent for computing semantic similarity between candidates and jobs."""

from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np

from candidate_matcher.agents.base import BaseAgent
from candidate_matcher.config.logging_config import get_logger
from candidate_matcher.integrations.embedding_client import (
    BaseEmbeddingClient,
    create_embedding_client,
)
from candidate_matcher.models.schemas import Candidate, JobPosting

logger = get_logger(__name__)


class SemanticMatcherAgent(BaseAgent[dict[str, Any]]):
    """Agent that computes semantic similarity between candidates and jobs.

    Uses embedding-based cosine similarity to measure how well a candidate's
    profile aligns with a job posting's requirements and description.
    """

    def __init__(
        self,
        embedding_client: Optional[BaseEmbeddingClient] = None,
        llm_client: Optional[Any] = None,
    ) -> None:
        """Initialize the semantic matcher agent.

        Args:
            embedding_client: Client for generating embeddings. Creates default if not provided.
            llm_client: LLM client for generating responses.
        """
        super().__init__(
            name="SemanticMatcherAgent",
            llm_client=llm_client,
            system_prompt=(
                "You are an expert at semantic matching between candidates and job postings. "
                "You analyze text to determine how well a candidate's profile aligns with "
                "job requirements, responsibilities, and company culture."
            ),
        )
        self._embedding_client = embedding_client or create_embedding_client()

    def _candidate_to_text(self, candidate: Candidate) -> str:
        """Convert a candidate profile to a text representation.

        Args:
            candidate: The candidate profile.

        Returns:
            Text representation of the candidate.
        """
        parts = [
            f"Candidate: {candidate.name}",
            f"Experience: {candidate.experience_years} years",
        ]
        if candidate.skills:
            skills_text = ", ".join(
                f"{s.name} ({s.level.value}, {s.years_experience}y)"
                for s in candidate.skills
            )
            parts.append(f"Skills: {skills_text}")
        if candidate.education:
            edu_text = "; ".join(
                f"{e.get('degree', 'N/A')} in {e.get('field', 'N/A')}"
                for e in candidate.education
            )
            parts.append(f"Education: {edu_text}")
        if candidate.work_history:
            work_text = "; ".join(
                f"{w.get('title', 'N/A')} at {w.get('company', 'N/A')}"
                for w in candidate.work_history
            )
            parts.append(f"Work History: {work_text}")
        return "\n".join(parts)

    def _job_to_text(self, job: JobPosting) -> str:
        """Convert a job posting to a text representation.

        Args:
            job: The job posting.

        Returns:
            Text representation of the job.
        """
        parts = [
            f"Job: {job.title}",
            f"Company: {job.company}",
            f"Description: {job.description}",
        ]
        if job.requirements:
            req_text = ", ".join(
                f"{r.skill_name} ({r.minimum_level.value})"
                for r in job.requirements
            )
            parts.append(f"Requirements: {req_text}")
        if job.responsibilities:
            resp_text = "; ".join(job.responsibilities)
            parts.append(f"Responsibilities: {resp_text}")
        if job.culture_values:
            culture_text = ", ".join(job.culture_values)
            parts.append(f"Culture Values: {culture_text}")
        return "\n".join(parts)

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec_a: First vector.
            vec_b: Second vector.

        Returns:
            Cosine similarity score between 0 and 1.
        """
        arr_a = np.array(vec_a)
        arr_b = np.array(vec_b)
        dot_product = np.dot(arr_a, arr_b)
        norm_a = np.linalg.norm(arr_a)
        norm_b = np.linalg.norm(arr_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        similarity = dot_product / (norm_a * norm_b)
        # Normalize from [-1, 1] to [0, 1]
        return float((similarity + 1) / 2)

    async def compute_similarity(
        self,
        candidate: Candidate,
        job: JobPosting,
    ) -> dict[str, Any]:
        """Compute semantic similarity between a candidate and job.

        Args:
            candidate: The candidate profile.
            job: The job posting.

        Returns:
            Dictionary with similarity scores and analysis.
        """
        candidate_text = self._candidate_to_text(candidate)
        job_text = self._job_to_text(job)

        # Generate embeddings
        candidate_embedding = await self._embedding_client.embed_query(candidate_text)
        job_embedding = await self._embedding_client.embed_query(job_text)

        # Compute cosine similarity
        similarity = self._cosine_similarity(candidate_embedding, job_embedding)

        # Use LLM for additional semantic analysis
        prompt = f"""Analyze the semantic alignment between this candidate and job posting.

Candidate:
{candidate_text}

Job:
{job_text}

Provide a JSON response with:
- "alignment_score": float (0-1) overall semantic alignment
- "key_themes": list of shared themes/topics
- "mismatches": list of areas where they don't align
- "summary": brief summary of semantic fit"""

        try:
            llm_analysis = await self._generate_structured(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "alignment_score": {"type": "number"},
                        "key_themes": {"type": "array", "items": {"type": "string"}},
                        "mismatches": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                    },
                    "required": ["alignment_score", "key_themes", "mismatches", "summary"],
                },
            )
        except Exception as e:
            logger.warning("llm_semantic_analysis_failed", error=str(e))
            llm_analysis = {
                "alignment_score": similarity,
                "key_themes": [],
                "mismatches": [],
                "summary": "LLM analysis unavailable; using embedding similarity only.",
            }

        # Combine embedding similarity with LLM analysis
        combined_score = (similarity + llm_analysis.get("alignment_score", similarity)) / 2

        return {
            "embedding_similarity": round(similarity, 4),
            "llm_alignment_score": round(llm_analysis.get("alignment_score", similarity), 4),
            "combined_score": round(combined_score, 4),
            "key_themes": llm_analysis.get("key_themes", []),
            "mismatches": llm_analysis.get("mismatches", []),
            "summary": llm_analysis.get("summary", ""),
        }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute semantic matching.

        Args:
            **kwargs: Must contain 'candidate' and 'job' keys.

        Returns:
            Semantic similarity analysis result.
        """
        candidate = kwargs.get("candidate")
        job = kwargs.get("job")
        if not candidate or not job:
            raise ValueError("Both 'candidate' and 'job' are required")
        return await self.compute_similarity(candidate, job)
