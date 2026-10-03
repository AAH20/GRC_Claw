"""Unit tests for the CandidateMatcher module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.agents.candidate_matcher import CandidateMatcher, MatchResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def matcher():
    """Return a fresh CandidateMatcher instance."""
    return CandidateMatcher()


@pytest.fixture
def sample_job():
    """Return a sample job requisition dict."""
    return {
        "id": "job-001",
        "title": "Senior Python Engineer",
        "required_skills": ["python", "fastapi", "postgresql", "docker"],
        "preferred_skills": ["kubernetes", "aws", "redis"],
        "min_experience_years": 5,
        "max_experience_years": 12,
        "location": "Remote",
        "salary_min": 120_000,
        "salary_max": 180_000,
    }


@pytest.fixture
def sample_candidates():
    """Return a list of sample candidate dicts."""
    return [
        {
            "id": "cand-001",
            "name": "Alice Johnson",
            "skills": ["python", "fastapi", "postgresql", "docker", "kubernetes"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
            "availability": "immediate",
        },
        {
            "id": "cand-002",
            "name": "Bob Smith",
            "skills": ["python", "django", "mysql"],
            "experience_years": 3,
            "location": "New York, NY",
            "expected_salary": 110_000,
            "availability": "two_weeks",
        },
        {
            "id": "cand-003",
            "name": "Carol White",
            "skills": ["python", "fastapi", "postgresql", "docker", "aws", "redis"],
            "experience_years": 10,
            "location": "Remote",
            "expected_salary": 170_000,
            "availability": "one_month",
        },
        {
            "id": "cand-004",
            "name": "David Brown",
            "skills": ["java", "spring", "oracle"],
            "experience_years": 8,
            "location": "Remote",
            "expected_salary": 140_000,
            "availability": "immediate",
        },
    ]


@pytest.fixture
def empty_candidates():
    """Return an empty candidate list."""
    return []


@pytest.fixture
def single_candidate(sample_candidates):
    """Return a list with a single candidate."""
    return [sample_candidates[0]]


# ---------------------------------------------------------------------------
# Tests — match_candidates
# ---------------------------------------------------------------------------


class TestMatchCandidates:
    """Tests for CandidateMatcher.match_candidates."""

    def test_match_candidates_returns_list(self, matcher, sample_job, sample_candidates):
        """match_candidates should return a list."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        assert isinstance(result, list)

    def test_match_candidates_returns_match_results(
        self, matcher, sample_job, sample_candidates
    ):
        """Every element in the result should be a MatchResult."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        for item in result:
            assert isinstance(item, MatchResult)

    def test_match_candidates_all_candidates_returned(
        self, matcher, sample_job, sample_candidates
    ):
        """All candidates should appear in the results."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        result_ids = {r.candidate_id for r in result}
        input_ids = {c["id"] for c in sample_candidates}
        assert result_ids == input_ids

    def test_match_candidates_empty_list(self, matcher, sample_job, empty_candidates):
        """An empty candidate list should yield an empty result."""
        result = matcher.match_candidates(sample_job, empty_candidates)
        assert result == []

    def test_match_candidates_single_candidate(
        self, matcher, sample_job, single_candidate
    ):
        """A single candidate should produce a single MatchResult."""
        result = matcher.match_candidates(sample_job, single_candidate)
        assert len(result) == 1
        assert result[0].candidate_id == single_candidate[0]["id"]

    def test_match_candidates_score_range(self, matcher, sample_job, sample_candidates):
        """All match scores should be between 0.0 and 1.0 inclusive."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        for r in result:
            assert 0.0 <= r.score <= 1.0

    def test_match_candidates_includes_matched_skills(
        self, matcher, sample_job, sample_candidates
    ):
        """Each MatchResult should expose a matched_skills list."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        for r in result:
            assert hasattr(r, "matched_skills")
            assert isinstance(r.matched_skills, list)

    def test_match_candidates_better_candidate_scores_higher(
        self, matcher, sample_job, sample_candidates
    ):
        """A candidate with more matching skills should score higher than one with fewer."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        scores = {r.candidate_id: r.score for r in result}
        # Alice (5 matching skills) should outscore Bob (1 matching skill)
        assert scores["cand-001"] > scores["cand-002"]

    def test_match_candidates_no_match_returns_zero_score(
        self, matcher, sample_job, sample_candidates
    ):
        """A candidate with no matching skills should receive a score of 0."""
        result = matcher.match_candidates(sample_job, sample_candidates)
        david_result = next(r for r in result if r.candidate_id == "cand-004")
        assert david_result.score == 0.0

    def test_match_candidates_does_not_mutate_inputs(
        self, matcher, sample_job, sample_candidates
    ):
        """match_candidates should not mutate the job or candidate dicts."""
        job_before = {k: v for k, v in sample_job.items()}
        cands_before = [
            {k: v for k, v in c.items()} for c in sample_candidates
        ]
        matcher.match_candidates(sample_job, sample_candidates)
        assert sample_job == job_before
        assert sample_candidates == cands_before


# ---------------------------------------------------------------------------
# Tests — calculate_match_score
# ---------------------------------------------------------------------------


class TestCalculateMatchScore:
    """Tests for CandidateMatcher.calculate_match_score."""

    def test_calculate_match_score_perfect_match(self, matcher, sample_job):
        """A candidate matching all required skills should score 1.0."""
        candidate = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        score = matcher.calculate_match_score(sample_job, candidate)
        assert score == pytest.approx(1.0)

    def test_calculate_match_score_no_match(self, matcher, sample_job):
        """A candidate with zero matching skills should score 0.0."""
        candidate = {
            "skills": ["c++", "embedded"],
            "experience_years": 2,
            "location": "Berlin",
            "expected_salary": 80_000,
        }
        score = matcher.calculate_match_score(sample_job, candidate)
        assert score == pytest.approx(0.0)

    def test_calculate_match_score_partial_match(self, matcher, sample_job):
        """A candidate matching some (but not all) required skills should score between 0 and 1."""
        candidate = {
            "skills": ["python", "fastapi"],
            "experience_years": 6,
            "location": "Remote",
            "expected_salary": 130_000,
        }
        score = matcher.calculate_match_score(sample_job, candidate)
        assert 0.0 < score < 1.0

    def test_calculate_match_score_returns_float(self, matcher, sample_job):
        """The return value should always be a float."""
        candidate = {
            "skills": ["python"],
            "experience_years": 5,
            "location": "Remote",
            "expected_salary": 120_000,
        }
        score = matcher.calculate_match_score(sample_job, candidate)
        assert isinstance(score, float)

    def test_calculate_match_score_preferred_skills_boost(
        self, matcher, sample_job
    ):
        """Preferred skills should increase the score relative to required-only."""
        base_candidate = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        boosted_candidate = {
            "skills": [
                "python",
                "fastapi",
                "postgresql",
                "docker",
                "kubernetes",
                "aws",
            ],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        base_score = matcher.calculate_match_score(sample_job, base_candidate)
        boosted_score = matcher.calculate_match_score(sample_job, boosted_candidate)
        assert boosted_score >= base_score

    def test_calculate_match_score_experience_penalty(self, matcher, sample_job):
        """A candidate below minimum experience should score lower than one meeting it."""
        underexperienced = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 2,
            "location": "Remote",
            "expected_salary": 120_000,
        }
        experienced = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        under_score = matcher.calculate_match_score(sample_job, underexperienced)
        exp_score = matcher.calculate_match_score(sample_job, experienced)
        assert under_score < exp_score

    def test_calculate_match_score_salary_alignment(self, matcher, sample_job):
        """A candidate whose expected salary fits the range should score higher."""
        in_range = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        out_of_range = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 250_000,
        }
        in_score = matcher.calculate_match_score(sample_job, in_range)
        out_score = matcher.calculate_match_score(sample_job, out_of_range)
        assert in_score > out_score

    def test_calculate_match_score_location_match(self, matcher, sample_job):
        """A candidate in the preferred location should score higher."""
        remote_candidate = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        onsite_candidate = {
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "San Francisco, CA",
            "expected_salary": 150_000,
        }
        remote_score = matcher.calculate_match_score(sample_job, remote_candidate)
        onsite_score = matcher.calculate_match_score(sample_job, onsite_candidate)
        assert remote_score > onsite_score

    def test_calculate_match_score_empty_skills(self, matcher, sample_job):
        """A candidate with an empty skills list should score 0.0."""
        candidate = {
            "skills": [],
            "experience_years": 10,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        score = matcher.calculate_match_score(sample_job, candidate)
        assert score == pytest.approx(0.0)

    def test_calculate_match_score_deterministic(self, matcher, sample_job):
        """The same inputs should always produce the same score."""
        candidate = {
            "skills": ["python", "fastapi", "postgresql"],
            "experience_years": 6,
            "location": "Remote",
            "expected_salary": 140_000,
        }
        score1 = matcher.calculate_match_score(sample_job, candidate)
        score2 = matcher.calculate_match_score(sample_job, candidate)
        assert score1 == score2


# ---------------------------------------------------------------------------
# Tests — rank_candidates
# ---------------------------------------------------------------------------


class TestRankCandidates:
    """Tests for CandidateMatcher.rank_candidates."""

    def test_rank_candidates_returns_list(self, matcher, sample_job, sample_candidates):
        """rank_candidates should return a list."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        assert isinstance(result, list)

    def test_rank_candidates_sorted_descending(
        self, matcher, sample_job, sample_candidates
    ):
        """Results should be sorted by score in descending order."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        scores = [r.score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_rank_candidates_preserves_all_candidates(
        self, matcher, sample_job, sample_candidates
    ):
        """No candidates should be dropped during ranking."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        assert len(result) == len(sample_candidates)

    def test_rank_candidates_empty_list(self, matcher, sample_job, empty_candidates):
        """An empty candidate list should yield an empty result."""
        result = matcher.rank_candidates(sample_job, empty_candidates)
        assert result == []

    def test_rank_candidates_single_candidate(
        self, matcher, sample_job, single_candidate
    ):
        """A single candidate should produce a single-element list."""
        result = matcher.rank_candidates(sample_job, single_candidate)
        assert len(result) == 1

    def test_rank_candidates_top_candidate_is_best_match(
        self, matcher, sample_job, sample_candidates
    ):
        """The first element should be the candidate with the highest score."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        # Carol (cand-003) has the most matching skills and best fit
        assert result[0].candidate_id == "cand-003"

    def test_rank_candidates_returns_match_results(
        self, matcher, sample_job, sample_candidates
    ):
        """Every element should be a MatchResult."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        for item in result:
            assert isinstance(item, MatchResult)

    def test_rank_candidates_includes_rank_field(
        self, matcher, sample_job, sample_candidates
    ):
        """Each MatchResult should carry a 1-based rank."""
        result = matcher.rank_candidates(sample_job, sample_candidates)
        for idx, item in enumerate(result, start=1):
            assert hasattr(item, "rank")
            assert item.rank == idx

    def test_rank_candidates_ties_broken_consistently(
        self, matcher, sample_job
    ):
        """Candidates with identical profiles should receive adjacent ranks."""
        twin_a = {
            "id": "twin-a",
            "name": "Twin A",
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        twin_b = {
            "id": "twin-b",
            "name": "Twin B",
            "skills": ["python", "fastapi", "postgresql", "docker"],
            "experience_years": 7,
            "location": "Remote",
            "expected_salary": 150_000,
        }
        result = matcher.rank_candidates(sample_job, [twin_a, twin_b])
        assert len(result) == 2
        assert result[0].rank == 1
        assert result[1].rank == 2

    def test_rank_candidates_does_not_mutate_inputs(
        self, matcher, sample_job, sample_candidates
    ):
        """rank_candidates should not mutate the job or candidate dicts."""
        job_before = {k: v for k, v in sample_job.items()}
        cands_before = [
            {k: v for k, v in c.items()} for c in sample_candidates
        ]
        matcher.rank_candidates(sample_job, sample_candidates)
        assert sample_job == job_before
        assert sample_candidates == cands_before
