"""
Integration test: resume-parser → candidate-matcher → content-moderation-pipeline.

Domain: Recruitment → UGC
Tests the workflow where a parsed resume is matched against a job, and the
resulting candidate profile content is moderated before publication.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from conftest import (
    CandidateMatcherStub,
    ContentModerationPipelineStub,
    FakeContentItem,
    FakeJobRequirement,
    ResumeParserStub,
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_resume_parses_successfully(
    resume_parser: ResumeParserStub, sample_resume_text: str
) -> None:
    """Resume parser should extract structured data from raw text."""
    resume = await resume_parser.parse(sample_resume_text)

    assert resume.candidate_id is not None
    assert resume.name == "Test Candidate"
    assert "Python" in resume.skills
    assert "FastAPI" in resume.skills
    assert resume.experience_years == 3.5
    assert len(resume.education) > 0
    assert resume_parser.call_count == 1


@pytest.mark.asyncio
async def test_candidate_matcher_scores_resume_against_job(
    resume_parser: ResumeParserStub,
    candidate_matcher: CandidateMatcherStub,
    sample_resume_text: str,
    sample_job: FakeJobRequirement,
) -> None:
    """Candidate matcher should score a parsed resume against a job requirement."""
    resume = await resume_parser.parse(sample_resume_text)
    match = await candidate_matcher.match(resume, sample_job)

    assert match.candidate_id == resume.candidate_id
    assert match.job_id == sample_job.job_id
    assert 0.0 <= match.score <= 1.0
    assert len(match.matched_skills) > 0
    assert "Python" in match.matched_skills


@pytest.mark.asyncio
async def test_moderation_approves_clean_content(
    content_moderation: ContentModerationPipelineStub,
) -> None:
    """Clean content should be approved by the moderation pipeline."""
    content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id="user-001",
        body="This is a helpful post about Python best practices.",
    )
    decision = await content_moderation.moderate(content)

    assert decision.content_id == content.content_id
    assert decision.action == "approve"
    assert decision.confidence > 0.9


@pytest.mark.asyncio
async def test_moderation_flags_inappropriate_content(
    content_moderation: ContentModerationPipelineStub,
) -> None:
    """Inappropriate content should be flagged for review."""
    content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id="user-002",
        body="This is spam and contains hate speech.",
    )
    decision = await content_moderation.moderate(content)

    assert decision.action == "flag_for_review"
    assert len(decision.reasons) > 0
    assert "spam" in decision.reasons or "hate" in decision.reasons


@pytest.mark.asyncio
async def test_full_recruitment_to_moderation_workflow(
    resume_parser: ResumeParserStub,
    candidate_matcher: CandidateMatcherStub,
    content_moderation: ContentModerationPipelineStub,
    sample_resume_text: str,
    sample_job: FakeJobRequirement,
) -> None:
    """
    End-to-end: parse resume → match against job → generate candidate
    profile content → moderate that content before publishing.
    """
    # Step 1: Parse the resume
    resume = await resume_parser.parse(sample_resume_text)
    assert resume.candidate_id is not None

    # Step 2: Match against the job
    match = await candidate_matcher.match(resume, sample_job)
    assert match.score > 0.0

    # Step 3: Generate candidate profile content from match result
    profile_content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=resume.candidate_id,
        body=(
            f"Candidate {resume.name} matched {match.score:.0%} for "
            f"role with skills: {', '.join(match.matched_skills)}"
        ),
        content_type="candidate_profile",
    )

    # Step 4: Moderate the generated profile content
    decision = await content_moderation.moderate(profile_content)
    assert decision.action == "approve"
    assert decision.content_id == profile_content.content_id

    # Verify the full chain was exercised
    assert resume_parser.call_count == 1
    assert candidate_matcher.call_count == 1
    assert content_moderation.call_count == 1


@pytest.mark.asyncio
async def test_low_score_match_still_moderated(
    resume_parser: ResumeParserStub,
    candidate_matcher: CandidateMatcherStub,
    content_moderation: ContentModerationPipelineStub,
    sample_job: FakeJobRequirement,
) -> None:
    """
    Even a low-scoring match should produce content that goes through
    moderation (quality gate applies regardless of match score).
    """
    # Create a weak resume
    weak_text = "Jane Smith\nSkills: HTML\nExperience: 0.5 years"
    resume = await resume_parser.parse(weak_text, candidate_id="weak-candidate")

    match = await candidate_matcher.match(resume, sample_job)
    assert match.score < 0.5  # Should be a poor match

    profile_content = FakeContentItem(
        content_id=str(uuid.uuid4()),
        author_id=resume.candidate_id,
        body=f"Low match: {match.score:.0%} — missing {match.missing_skills}",
        content_type="candidate_profile",
    )
    decision = await content_moderation.moderate(profile_content)
    assert decision.action == "approve"  # Still clean content


@pytest.mark.asyncio
async def test_moderation_pipeline_processes_multiple_candidates(
    resume_parser: ResumeParserStub,
    candidate_matcher: CandidateMatcherStub,
    content_moderation: ContentModerationPipelineStub,
    sample_job: FakeJobRequirement,
) -> None:
    """Multiple candidates should flow through the pipeline independently."""
    candidates = [
        ("Alice", "Python, FastAPI, SQL, Docker — 5 years"),
        ("Bob", "Python, Django — 2 years"),
        ("Charlie", "Java, Spring — 4 years"),
    ]

    results: list[dict[str, Any]] = []
    for name, text in candidates:
        resume = await resume_parser.parse(text, candidate_id=name.lower())
        match = await candidate_matcher.match(resume, sample_job)
        content = FakeContentItem(
            content_id=str(uuid.uuid4()),
            author_id=resume.candidate_id,
            body=f"Profile for {name}: score {match.score:.0%}",
        )
        decision = await content_moderation.moderate(content)
        results.append({
            "name": name,
            "score": match.score,
            "action": decision.action,
        })

    assert len(results) == 3
    assert all(r["action"] == "approve" for r in results)
    assert results[0]["score"] > results[2]["score"]  # Alice > Charlie
