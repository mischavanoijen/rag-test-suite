"""Tests for Pydantic models."""

import pytest

from crewai_test_suite.models import (
    TestCase,
    TestResult,
    TestSuiteState,
    TestCategory,
    TestDifficulty,
    RagDomain,
    RagSummary,
    CategoryScore,
)


class TestTestCase:
    """Tests for TestCase model."""

    def test_create_test_case(self):
        """Test creating a TestCase."""
        tc = TestCase(
            id="TEST-001",
            question="What is AI?",
            expected_answer="AI is artificial intelligence.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Tests basic knowledge retrieval",
        )

        assert tc.id == "TEST-001"
        assert tc.question == "What is AI?"
        assert tc.category == TestCategory.FACTUAL
        assert tc.difficulty == TestDifficulty.EASY

    def test_test_case_category_enum(self):
        """Test TestCategory enum values."""
        assert TestCategory.FACTUAL.value == "factual"
        assert TestCategory.REASONING.value == "reasoning"
        assert TestCategory.EDGE_CASE.value == "edge_case"

    def test_test_case_difficulty_enum(self):
        """Test TestDifficulty enum values."""
        assert TestDifficulty.EASY.value == "easy"
        assert TestDifficulty.MEDIUM.value == "medium"
        assert TestDifficulty.HARD.value == "hard"


class TestTestResult:
    """Tests for TestResult model."""

    def test_create_test_result(self):
        """Test creating a TestResult."""
        tc = TestCase(
            id="TEST-001",
            question="What is AI?",
            expected_answer="AI is artificial intelligence.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Tests basic knowledge retrieval",
        )

        result = TestResult(
            test_case=tc,
            actual_answer="AI stands for artificial intelligence.",
            passed=True,
            similarity_score=0.85,
            evaluation_rationale="Good match with expected answer",
        )

        assert result.passed is True
        assert result.similarity_score == 0.85
        assert result.retry_count == 0
        assert result.error is None

    def test_test_result_with_error(self):
        """Test TestResult with error."""
        tc = TestCase(
            id="TEST-002",
            question="What is ML?",
            expected_answer="ML is machine learning.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )

        result = TestResult(
            test_case=tc,
            actual_answer="",
            passed=False,
            similarity_score=0.0,
            evaluation_rationale="API error",
            error="Connection timeout",
        )

        assert result.passed is False
        assert result.error == "Connection timeout"


class TestTestSuiteState:
    """Tests for TestSuiteState model."""

    def test_default_state(self):
        """Test default state values."""
        state = TestSuiteState()

        assert state.target_mode == "api"
        assert state.num_tests == 20
        assert state.pass_threshold == 0.7
        assert state.max_retries == 2
        assert state.test_cases == []
        assert state.results == []

    def test_state_with_values(self):
        """Test state with custom values."""
        state = TestSuiteState(
            target_mode="local",
            target_api_url="https://api.example.com/kickoff",
            num_tests=10,
            pass_threshold=0.8,
        )

        assert state.target_mode == "local"
        assert state.target_api_url == "https://api.example.com/kickoff"
        assert state.num_tests == 10
        assert state.pass_threshold == 0.8


class TestRagModels:
    """Tests for RAG-related models."""

    def test_rag_domain(self):
        """Test RagDomain model."""
        domain = RagDomain(
            name="Technology",
            subtopics=["AI", "Cloud Computing"],
            depth="high",
            example_queries=["What is AI?"],
            sample_facts=["AI is used in many industries"],
        )

        assert domain.name == "Technology"
        assert len(domain.subtopics) == 2
        assert domain.depth == "high"

    def test_rag_summary(self):
        """Test RagSummary model."""
        summary = RagSummary(
            domains=[
                RagDomain(
                    name="Tech",
                    subtopics=["AI"],
                    depth="high",
                    example_queries=[],
                    sample_facts=[],
                )
            ],
            boundaries=["Finance", "Legal"],
            total_coverage_estimate="Covers technology topics well",
        )

        assert len(summary.domains) == 1
        assert len(summary.boundaries) == 2

    def test_category_score(self):
        """Test CategoryScore model."""
        score = CategoryScore(
            category=TestCategory.FACTUAL,
            total=10,
            passed=8,
            pass_rate=80.0,
            common_issues=["Minor accuracy gaps"],
        )

        assert score.category == TestCategory.FACTUAL
        assert score.total == 10
        assert score.passed == 8
        assert score.pass_rate == 80.0
