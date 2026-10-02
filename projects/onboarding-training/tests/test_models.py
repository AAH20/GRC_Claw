"""Tests for onboarding/training agent implementations."""
from __future__ import annotations

import pytest

from onboarding.models import (
    AssessmentResult,
    Course,
    Learner,
    Lesson,
    QuizQuestion,
)


class TestModels:
    """Tests for onboarding data models."""

    def test_learner_creation(self) -> None:
        learner = Learner(
            learner_id="learn_1",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        assert learner.learner_id == "learn_1"
        assert learner.email == "test@example.com"

    def test_course_creation(self) -> None:
        course = Course(
            course_id="course_1",
            title="Test Course",
            description="A test course",
            role_target="engineer",
        )
        assert course.course_id == "course_1"
        assert course.title == "Test Course"

    def test_lesson_creation(self) -> None:
        lesson = Lesson(
            lesson_id="lesson_1",
            title="Test Lesson",
            content="Test content",
            order_index=0,
        )
        assert lesson.lesson_id == "lesson_1"
        assert lesson.title == "Test Lesson"

    def test_quiz_question_creation(self) -> None:
        question = QuizQuestion(
            question_id="q_1",
            prompt="What is 2+2?",
            question_type="multiple_choice",
            options=["1", "2", "3", "4"],
            correct_answer="4",
        )
        assert question.question_id == "q_1"
        assert question.correct_answer == "4"

    def test_assessment_result_creation(self) -> None:
        result = AssessmentResult(
            assessment_id="assess_1",
            learner_id="learn_1",
            course_id="course_1",
            lesson_id="lesson_1",
            score=0.85,
            passed=True,
            mastery_achieved=True,
        )
        assert result.score == 0.85
        assert result.passed is True
