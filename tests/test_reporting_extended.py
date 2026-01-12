"""Extended tests for the reporting crew."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestReportingCrew:
    """Tests for ReportingCrew class."""

    def test_crew_initialization(self):
        """Test reporting crew initialization."""
        from crewai_test_suite.crews.reporting.crew import ReportingCrew

        crew = ReportingCrew(llm_model="openai/gemini-2.5-flash")

        assert crew.llm is not None


class TestRunReporting:
    """Tests for run_reporting function."""

    @patch("crewai_test_suite.crews.reporting.crew.ReportingCrew")
    def test_run_reporting_success(self, mock_crew_class):
        """Test successful report generation."""
        from crewai_test_suite.crews.reporting.crew import run_reporting
        from crewai_test_suite.models import (
            TestCase, TestResult, TestCategory, TestDifficulty, CategoryScore
        )

        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "# Quality Report\n\nPass rate: 80%"
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance

        test_case = TestCase(
            id="TC-001",
            question="Test?",
            expected_answer="Answer",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )
        results = [
            TestResult(
                test_case=test_case,
                actual_answer="Answer",
                passed=True,
                similarity_score=0.9,
                evaluation_rationale="Good",
            )
        ]
        category_scores = [
            CategoryScore(
                category="factual",
                total=1,
                passed=1,
                pass_rate=1.0,
            )
        ]
        analysis = {"recommendations": {"priority_order": ["Improve edge cases"]}}

        report = run_reporting(
            results=results,
            category_scores=category_scores,
            analysis=analysis,
            target_name="test-crew",
            llm_model="openai/gemini-2.5-flash",
        )

        assert report is not None
        assert "Quality Report" in report or "Pass rate" in report

    @patch("crewai_test_suite.crews.reporting.crew.ReportingCrew")
    def test_run_reporting_with_empty_results(self, mock_crew_class):
        """Test report generation with empty results."""
        from crewai_test_suite.crews.reporting.crew import run_reporting

        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "# Report\n\nNo tests executed."
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance

        report = run_reporting(
            results=[],
            category_scores=[],
            analysis={},
            target_name="test-crew",
            llm_model="openai/gemini-2.5-flash",
        )

        assert report is not None


class TestFormatCategoryTable:
    """Tests for category table formatting."""

    def test_format_category_breakdown_single(self):
        """Test formatting single category."""
        from crewai_test_suite.crews.evaluation.crew import format_category_breakdown
        from crewai_test_suite.models import CategoryScore

        scores = [
            CategoryScore(
                category="factual",
                total=10,
                passed=8,
                pass_rate=0.8,
                common_issues=["Missing details"],
            )
        ]

        result = format_category_breakdown(scores)

        assert "factual" in result
        assert "80" in result or "0.8" in result

    def test_format_category_breakdown_multiple(self):
        """Test formatting multiple categories."""
        from crewai_test_suite.crews.evaluation.crew import format_category_breakdown
        from crewai_test_suite.models import CategoryScore

        scores = [
            CategoryScore(category="factual", total=10, passed=8, pass_rate=0.8),
            CategoryScore(category="reasoning", total=5, passed=3, pass_rate=0.6),
            CategoryScore(category="edge_case", total=3, passed=1, pass_rate=0.33),
        ]

        result = format_category_breakdown(scores)

        assert "factual" in result
        assert "reasoning" in result
        assert "edge_case" in result

    def test_format_category_breakdown_empty(self):
        """Test formatting empty categories."""
        from crewai_test_suite.crews.evaluation.crew import format_category_breakdown

        result = format_category_breakdown([])

        assert result == "" or "No categories" in result


class TestFormatFailedExamples:
    """Tests for failed examples formatting."""

    def test_format_failed_examples_with_failures(self):
        """Test formatting when there are failed tests."""
        from crewai_test_suite.crews.evaluation.crew import format_failed_examples
        from crewai_test_suite.models import (
            TestCase, TestResult, TestCategory, TestDifficulty
        )

        test_case = TestCase(
            id="TC-001",
            question="What is AI?",
            expected_answer="Artificial Intelligence",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )

        results = [
            TestResult(
                test_case=test_case,
                actual_answer="I don't know",
                passed=False,
                similarity_score=0.1,
                evaluation_rationale="Poor match",
            )
        ]

        result = format_failed_examples(results)

        assert "TC-001" in result
        assert "What is AI?" in result

    def test_format_failed_examples_no_failures(self):
        """Test formatting when all tests pass."""
        from crewai_test_suite.crews.evaluation.crew import format_failed_examples
        from crewai_test_suite.models import (
            TestCase, TestResult, TestCategory, TestDifficulty
        )

        test_case = TestCase(
            id="TC-001",
            question="What is AI?",
            expected_answer="Artificial Intelligence",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )

        results = [
            TestResult(
                test_case=test_case,
                actual_answer="Artificial Intelligence",
                passed=True,
                similarity_score=0.95,
                evaluation_rationale="Excellent match",
            )
        ]

        result = format_failed_examples(results)

        # format_failed_examples returns "No failed tests." when all pass
        assert result == "" or "No failed tests" in result or "All tests passed" in result


class TestCalculateCategoryScores:
    """Tests for calculate_category_scores function."""

    def test_calculate_scores_by_category(self):
        """Test calculating scores grouped by category."""
        from crewai_test_suite.crews.evaluation.crew import calculate_category_scores
        from crewai_test_suite.models import (
            TestCase, TestResult, TestCategory, TestDifficulty
        )

        factual_case = TestCase(
            id="TC-001",
            question="Fact?",
            expected_answer="Answer",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )
        reasoning_case = TestCase(
            id="TC-002",
            question="Reason?",
            expected_answer="Answer",
            category=TestCategory.REASONING,
            difficulty=TestDifficulty.MEDIUM,
            rationale="Test",
        )

        results = [
            TestResult(test_case=factual_case, actual_answer="A", passed=True, similarity_score=0.9, evaluation_rationale="Good"),
            TestResult(test_case=factual_case, actual_answer="B", passed=True, similarity_score=0.85, evaluation_rationale="Good"),
            TestResult(test_case=reasoning_case, actual_answer="C", passed=False, similarity_score=0.3, evaluation_rationale="Poor"),
        ]

        scores = calculate_category_scores(results)

        assert len(scores) == 2

        # Find factual and reasoning scores
        factual_score = next((s for s in scores if s.category == "factual"), None)
        reasoning_score = next((s for s in scores if s.category == "reasoning"), None)

        assert factual_score is not None
        assert factual_score.total == 2
        assert factual_score.passed == 2
        # pass_rate is stored as percentage (100.0) not decimal (1.0)
        assert factual_score.pass_rate == 100.0

        assert reasoning_score is not None
        assert reasoning_score.total == 1
        assert reasoning_score.passed == 0
        assert reasoning_score.pass_rate == 0.0

    def test_calculate_scores_empty_results(self):
        """Test calculating scores with no results."""
        from crewai_test_suite.crews.evaluation.crew import calculate_category_scores

        scores = calculate_category_scores([])

        assert scores == []
