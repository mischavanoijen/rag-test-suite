"""Tests for crew-related functions."""

import json

import pytest

from rag_test_suite.models import TestCase, TestResult, TestCategory, TestDifficulty
from rag_test_suite.crews.test_generation.crew import parse_test_cases, _parse_single_test_case
from rag_test_suite.crews.evaluation.crew import (
    calculate_category_scores,
    format_category_breakdown,
    format_failed_examples,
    parse_evaluation_result,
)


class TestParseTestCases:
    """Tests for test case parsing functions."""

    def test_parse_json_array(self):
        """Test parsing JSON array of test cases."""
        raw_output = json.dumps([
            {
                "id": "TEST-001",
                "question": "What is AI?",
                "expected_answer": "AI is artificial intelligence.",
                "category": "factual",
                "difficulty": "easy",
                "rationale": "Basic test",
            },
            {
                "id": "TEST-002",
                "question": "How does ML work?",
                "expected_answer": "ML learns from data.",
                "category": "reasoning",
                "difficulty": "medium",
                "rationale": "Reasoning test",
            },
        ])

        test_cases = parse_test_cases(raw_output)

        assert len(test_cases) == 2
        assert test_cases[0].id == "TEST-001"
        assert test_cases[0].category == TestCategory.FACTUAL
        assert test_cases[1].difficulty == TestDifficulty.MEDIUM

    def test_parse_json_in_markdown(self):
        """Test parsing JSON embedded in markdown."""
        raw_output = """
Here are the test cases:

```json
[
    {
        "id": "TEST-001",
        "question": "What is AI?",
        "expected_answer": "AI is artificial intelligence.",
        "category": "factual",
        "difficulty": "easy",
        "rationale": "Basic test"
    }
]
```

These tests cover the main topics.
"""

        test_cases = parse_test_cases(raw_output)

        assert len(test_cases) == 1
        assert test_cases[0].id == "TEST-001"

    def test_parse_invalid_json(self):
        """Test handling invalid JSON."""
        raw_output = "This is not JSON at all"

        test_cases = parse_test_cases(raw_output)

        # Should return empty list on parse failure
        assert len(test_cases) == 0

    def test_parse_single_test_case(self):
        """Test parsing a single test case dictionary."""
        item = {
            "id": "TEST-001",
            "question": "What is AI?",
            "expected_answer": "AI is artificial intelligence.",
            "category": "factual",
            "difficulty": "easy",
            "rationale": "Basic test",
        }

        test_case = _parse_single_test_case(item)

        assert test_case is not None
        assert test_case.id == "TEST-001"
        assert test_case.category == TestCategory.FACTUAL

    def test_parse_single_test_case_unknown_category(self):
        """Test parsing with unknown category defaults to FACTUAL."""
        item = {
            "id": "TEST-001",
            "question": "What is AI?",
            "expected_answer": "AI is artificial intelligence.",
            "category": "unknown_category",
            "difficulty": "easy",
            "rationale": "Basic test",
        }

        test_case = _parse_single_test_case(item)

        assert test_case is not None
        assert test_case.category == TestCategory.FACTUAL


class TestEvaluationHelpers:
    """Tests for evaluation helper functions."""

    def _create_test_results(self):
        """Create sample test results for testing."""
        tc1 = TestCase(
            id="TEST-001",
            question="What is AI?",
            expected_answer="AI is artificial intelligence.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Basic test",
        )
        tc2 = TestCase(
            id="TEST-002",
            question="How does ML work?",
            expected_answer="ML learns from data.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.MEDIUM,
            rationale="Reasoning test",
        )
        tc3 = TestCase(
            id="TEST-003",
            question="Why is deep learning useful?",
            expected_answer="Deep learning handles complex patterns.",
            category=TestCategory.REASONING,
            difficulty=TestDifficulty.HARD,
            rationale="Hard reasoning",
        )

        return [
            TestResult(
                test_case=tc1,
                actual_answer="AI is artificial intelligence.",
                passed=True,
                similarity_score=0.95,
                evaluation_rationale="Excellent match",
            ),
            TestResult(
                test_case=tc2,
                actual_answer="ML is machine learning.",
                passed=False,
                similarity_score=0.6,
                evaluation_rationale="Missing key details",
            ),
            TestResult(
                test_case=tc3,
                actual_answer="Deep learning uses neural networks.",
                passed=True,
                similarity_score=0.8,
                evaluation_rationale="Good explanation",
            ),
        ]

    def test_calculate_category_scores(self):
        """Test calculating category scores."""
        results = self._create_test_results()

        scores = calculate_category_scores(results)

        # Should have 2 categories: FACTUAL (2 tests) and REASONING (1 test)
        assert len(scores) == 2

        factual = next(s for s in scores if s.category == TestCategory.FACTUAL)
        assert factual.total == 2
        assert factual.passed == 1
        assert factual.pass_rate == 50.0

        reasoning = next(s for s in scores if s.category == TestCategory.REASONING)
        assert reasoning.total == 1
        assert reasoning.passed == 1
        assert reasoning.pass_rate == 100.0

    def test_format_category_breakdown(self):
        """Test formatting category breakdown."""
        results = self._create_test_results()
        scores = calculate_category_scores(results)

        breakdown = format_category_breakdown(scores)

        assert "factual" in breakdown
        assert "reasoning" in breakdown
        assert "50.0%" in breakdown or "100.0%" in breakdown

    def test_format_failed_examples(self):
        """Test formatting failed test examples."""
        results = self._create_test_results()

        failed_str = format_failed_examples(results, max_examples=5)

        # Should include the failed test (TEST-002)
        assert "TEST-002" in failed_str
        assert "Missing key details" in failed_str

    def test_format_failed_examples_no_failures(self):
        """Test formatting when no tests failed."""
        tc = TestCase(
            id="TEST-001",
            question="What is AI?",
            expected_answer="AI is artificial intelligence.",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Basic test",
        )
        results = [
            TestResult(
                test_case=tc,
                actual_answer="AI is artificial intelligence.",
                passed=True,
                similarity_score=0.95,
                evaluation_rationale="Perfect",
            )
        ]

        failed_str = format_failed_examples(results)

        assert "No failed tests" in failed_str

    def test_parse_evaluation_result_valid_json(self):
        """Test parsing valid evaluation JSON."""
        raw_output = json.dumps({
            "failure_patterns": [{"pattern": "Test pattern"}],
            "root_causes": [{"cause": "Test cause"}],
            "recommendations": {
                "prompt_changes": [{"change": "Update prompt"}],
                "rag_changes": [],
                "priority_order": ["Update prompt"],
            },
            "summary": "Test summary",
        })

        result = parse_evaluation_result(raw_output)

        assert len(result["failure_patterns"]) == 1
        assert result["summary"] == "Test summary"

    def test_parse_evaluation_result_json_in_markdown(self):
        """Test parsing evaluation JSON in markdown."""
        raw_output = """
Here is the analysis:

```json
{
    "failure_patterns": [],
    "root_causes": [],
    "recommendations": {},
    "summary": "All tests passed"
}
```
"""

        result = parse_evaluation_result(raw_output)

        assert result["summary"] == "All tests passed"

    def test_parse_evaluation_result_invalid(self):
        """Test handling invalid evaluation output."""
        raw_output = "Invalid output that is not JSON"

        result = parse_evaluation_result(raw_output)

        # Should return default structure with raw output in summary
        assert "failure_patterns" in result
        assert result["failure_patterns"] == []
