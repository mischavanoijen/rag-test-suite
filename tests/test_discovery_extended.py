"""Extended tests for the discovery crew."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestRunDiscovery:
    """Tests for run_discovery function."""

    @patch("rag_test_suite.crews.discovery.crew.DiscoveryCrew")
    def test_run_discovery_success(self, mock_crew_class):
        """Test successful discovery run."""
        from rag_test_suite.crews.discovery.crew import run_discovery

        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = json.dumps({
            "domains": [{"name": "AI", "subtopics": ["ML"], "depth": "high"}],
            "total_coverage_estimate": "AI topics"
        })
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance

        mock_rag_tool = MagicMock()
        result = run_discovery(
            rag_tool=mock_rag_tool,
            crew_description="Test crew",
            llm_model="openai/gemini-2.5-flash",
        )

        assert result is not None
        assert "AI" in result

    @patch("rag_test_suite.crews.discovery.crew.DiscoveryCrew")
    @patch("rag_test_suite.crews.discovery.crew._create_fallback_summary")
    def test_run_discovery_fallback_on_error(self, mock_fallback, mock_crew_class):
        """Test fallback when discovery fails."""
        from rag_test_suite.crews.discovery.crew import run_discovery

        mock_crew_class.side_effect = Exception("Crew failed")
        mock_fallback.return_value = json.dumps({
            "domains": [{"name": "General", "subtopics": [], "depth": "low"}],
            "total_coverage_estimate": "Basic coverage"
        })

        mock_rag_tool = MagicMock()
        result = run_discovery(
            rag_tool=mock_rag_tool,
            crew_description="Test crew",
            llm_model="openai/gemini-2.5-flash",
        )

        # Should return fallback summary
        assert result is not None
        mock_fallback.assert_called()


class TestCreateFallbackSummary:
    """Tests for _create_fallback_summary function."""

    def test_create_fallback_returns_json(self):
        """Test fallback summary returns valid JSON."""
        from rag_test_suite.crews.discovery.crew import _create_fallback_summary

        # Create a mock RAG tool with proper _run method
        mock_rag_tool = MagicMock()
        mock_rag_tool._run.return_value = "Topics covered include: Customer Service, Technical Support"

        result = _create_fallback_summary(mock_rag_tool)

        assert result is not None
        # Should be valid JSON
        data = json.loads(result)
        assert "domains" in data
        assert "total_coverage_estimate" in data

    def test_create_fallback_with_employee_experience_topic(self):
        """Test fallback detects Employee Experience in RAG results."""
        from rag_test_suite.crews.discovery.crew import _create_fallback_summary

        mock_rag_tool = MagicMock()
        mock_rag_tool._run.return_value = "Employee Experience portal helps with helpdesk support"

        result = _create_fallback_summary(mock_rag_tool)

        data = json.loads(result)
        # Should have at least one domain
        assert len(data["domains"]) >= 1

    def test_create_fallback_handles_empty_response(self):
        """Test fallback handles empty RAG response."""
        from rag_test_suite.crews.discovery.crew import _create_fallback_summary

        mock_rag_tool = MagicMock()
        mock_rag_tool._run.return_value = ""

        result = _create_fallback_summary(mock_rag_tool)

        assert result is not None
        data = json.loads(result)
        assert "domains" in data


class TestIsValidDiscoveryOutput:
    """Tests for _is_valid_discovery_output function."""

    def test_valid_json_with_domains(self):
        """Test valid JSON with domains field."""
        from rag_test_suite.crews.discovery.crew import _is_valid_discovery_output

        valid_json = '{"domains": [{"name": "Test"}], "total_coverage_estimate": "Test coverage"}'

        assert _is_valid_discovery_output(valid_json) is True

    def test_valid_json_in_markdown(self):
        """Test valid JSON wrapped in markdown."""
        from rag_test_suite.crews.discovery.crew import _is_valid_discovery_output

        markdown_json = '```json\n{"domains": [], "total_coverage_estimate": "Test"}\n```'

        assert _is_valid_discovery_output(markdown_json) is True

    def test_invalid_json(self):
        """Test invalid JSON returns False."""
        from rag_test_suite.crews.discovery.crew import _is_valid_discovery_output

        invalid = "This is not JSON at all"

        assert _is_valid_discovery_output(invalid) is False

    def test_json_missing_required_fields(self):
        """Test JSON without required fields."""
        from rag_test_suite.crews.discovery.crew import _is_valid_discovery_output

        missing_fields = '{"other_field": "value"}'

        assert _is_valid_discovery_output(missing_fields) is False
