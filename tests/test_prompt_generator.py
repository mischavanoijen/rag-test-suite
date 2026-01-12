"""Tests for the prompt generator crew."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestParsePromptSuggestions:
    """Tests for _parse_prompt_suggestions function."""

    def test_parse_valid_json_in_markdown(self, mock_prompt_suggestions_json):
        """Test parsing valid JSON wrapped in markdown code blocks."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        result = _parse_prompt_suggestions(mock_prompt_suggestions_json)

        assert result is not None
        assert result.primary_agent.role == "Customer Service Expert"
        assert result.primary_agent.goal == "Help customers resolve issues quickly"
        assert "rag_search" in result.primary_agent.tools
        assert len(result.example_queries) == 2
        assert len(result.out_of_scope_examples) == 2

    def test_parse_raw_json(self):
        """Test parsing raw JSON without markdown wrapper."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        raw_json = """{
            "primary_agent": {
                "role": "Test Agent",
                "goal": "Test goal",
                "backstory": "Test backstory",
                "tools": ["tool1"],
                "expertise_areas": ["area1"]
            },
            "supporting_agents": [],
            "suggested_tasks": [],
            "system_prompt": "Test prompt",
            "example_queries": ["query1"],
            "out_of_scope_examples": ["out1"],
            "knowledge_summary": "Test summary",
            "limitations": ["limit1"],
            "suggested_tone": "professional",
            "response_format_guidance": "Be helpful"
        }"""

        result = _parse_prompt_suggestions(raw_json)

        assert result is not None
        assert result.primary_agent.role == "Test Agent"
        assert result.system_prompt == "Test prompt"

    def test_parse_invalid_json_returns_none(self):
        """Test that invalid JSON returns None."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        result = _parse_prompt_suggestions("This is not JSON at all")

        assert result is None

    def test_parse_incomplete_json_returns_none(self):
        """Test that incomplete JSON returns None."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        result = _parse_prompt_suggestions('{"primary_agent": {"role": "Test"')

        assert result is None

    def test_parse_json_with_supporting_agents(self):
        """Test parsing JSON with supporting agents."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        json_with_agents = """{
            "primary_agent": {
                "role": "Main Agent",
                "goal": "Main goal",
                "backstory": "Main backstory",
                "tools": ["tool1"],
                "expertise_areas": ["area1"]
            },
            "supporting_agents": [
                {
                    "role": "Support Agent",
                    "goal": "Support goal",
                    "backstory": "Support backstory",
                    "tools": ["tool2"],
                    "expertise_areas": ["area2"]
                }
            ],
            "suggested_tasks": [],
            "system_prompt": "Test",
            "example_queries": [],
            "out_of_scope_examples": [],
            "knowledge_summary": "Test",
            "limitations": [],
            "suggested_tone": "friendly",
            "response_format_guidance": "Test"
        }"""

        result = _parse_prompt_suggestions(json_with_agents)

        assert result is not None
        assert len(result.supporting_agents) == 1
        assert result.supporting_agents[0].role == "Support Agent"

    def test_parse_json_with_suggested_tasks(self):
        """Test parsing JSON with suggested tasks."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _parse_prompt_suggestions,
        )

        json_with_tasks = """{
            "primary_agent": {
                "role": "Agent",
                "goal": "Goal",
                "backstory": "Backstory",
                "tools": [],
                "expertise_areas": []
            },
            "supporting_agents": [],
            "suggested_tasks": [
                {
                    "name": "task1",
                    "description": "Task 1 description",
                    "expected_output": "Task 1 output"
                },
                {
                    "name": "task2",
                    "description": "Task 2 description",
                    "expected_output": "Task 2 output"
                }
            ],
            "system_prompt": "Test",
            "example_queries": [],
            "out_of_scope_examples": [],
            "knowledge_summary": "Test",
            "limitations": [],
            "suggested_tone": "technical",
            "response_format_guidance": "Test"
        }"""

        result = _parse_prompt_suggestions(json_with_tasks)

        assert result is not None
        assert len(result.suggested_tasks) == 2
        assert result.suggested_tasks[0].name == "task1"
        assert result.suggested_tasks[1].name == "task2"


class TestCreateDefaultSuggestions:
    """Tests for _create_default_suggestions function."""

    def test_create_defaults_with_valid_rag_summary(self):
        """Test creating default suggestions with valid RAG summary."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _create_default_suggestions,
        )

        rag_summary = json.dumps(
            {
                "domains": [
                    {"name": "Customer Service"},
                    {"name": "Technical Support"},
                ],
                "total_coverage_estimate": "Company knowledge base",
            }
        )

        result = _create_default_suggestions(rag_summary, "Customer support bot")

        assert result is not None
        assert result.primary_agent.role == "Knowledge Assistant"
        assert "Customer Service" in result.primary_agent.expertise_areas
        assert "Technical Support" in result.primary_agent.expertise_areas
        assert len(result.example_queries) == 3
        assert len(result.limitations) == 3

    def test_create_defaults_with_invalid_json(self):
        """Test creating defaults with invalid JSON summary."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _create_default_suggestions,
        )

        result = _create_default_suggestions("not valid json", "Test crew")

        assert result is not None
        assert result.primary_agent.role == "Knowledge Assistant"
        assert "General Knowledge" in result.primary_agent.expertise_areas

    def test_create_defaults_with_empty_domains(self):
        """Test creating defaults with empty domains list."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _create_default_suggestions,
        )

        rag_summary = json.dumps({"domains": [], "total_coverage_estimate": "Empty"})

        result = _create_default_suggestions(rag_summary, "")

        assert result is not None
        assert result.primary_agent.role == "Knowledge Assistant"

    def test_create_defaults_system_prompt_content(self):
        """Test that system prompt contains guidelines."""
        from crewai_test_suite.crews.prompt_generator.crew import (
            _create_default_suggestions,
        )

        rag_summary = json.dumps(
            {"domains": [{"name": "AI"}], "total_coverage_estimate": "AI topics"}
        )

        result = _create_default_suggestions(rag_summary, "AI assistant")

        assert "GUIDELINES" in result.system_prompt
        assert "LIMITATIONS" in result.system_prompt


class TestRunPromptGenerator:
    """Tests for run_prompt_generator function."""

    @patch("crewai_test_suite.crews.prompt_generator.crew.PromptGeneratorCrew")
    def test_run_prompt_generator_success(self, mock_crew_class):
        """Test successful prompt generation."""
        from crewai_test_suite.crews.prompt_generator.crew import run_prompt_generator

        # Setup mock
        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = """{
            "primary_agent": {
                "role": "Test Agent",
                "goal": "Test goal",
                "backstory": "Test backstory",
                "tools": ["tool1"],
                "expertise_areas": ["area1"]
            },
            "supporting_agents": [],
            "suggested_tasks": [],
            "system_prompt": "Test",
            "example_queries": ["q1"],
            "out_of_scope_examples": ["o1"],
            "knowledge_summary": "Test",
            "limitations": ["l1"],
            "suggested_tone": "professional",
            "response_format_guidance": "Test"
        }"""
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance

        result = run_prompt_generator(
            rag_summary='{"domains": []}',
            crew_description="Test crew",
            llm_model="openai/gemini-2.5-flash",
        )

        assert result is not None
        assert result.primary_agent.role == "Test Agent"

    @patch("crewai_test_suite.crews.prompt_generator.crew.PromptGeneratorCrew")
    def test_run_prompt_generator_fallback_on_parse_error(self, mock_crew_class):
        """Test fallback when parsing fails."""
        from crewai_test_suite.crews.prompt_generator.crew import run_prompt_generator

        # Setup mock to return invalid JSON
        mock_crew_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.raw = "This is not valid JSON"
        mock_crew_instance.crew.return_value.kickoff.return_value = mock_result
        mock_crew_class.return_value = mock_crew_instance

        result = run_prompt_generator(
            rag_summary='{"domains": [{"name": "AI"}]}',
            crew_description="AI assistant",
            llm_model="openai/gemini-2.5-flash",
        )

        # Should return default suggestions
        assert result is not None
        assert result.primary_agent.role == "Knowledge Assistant"

    @patch("crewai_test_suite.crews.prompt_generator.crew.PromptGeneratorCrew")
    def test_run_prompt_generator_fallback_on_exception(self, mock_crew_class):
        """Test fallback when crew raises exception."""
        from crewai_test_suite.crews.prompt_generator.crew import run_prompt_generator

        # Setup mock to raise exception
        mock_crew_class.side_effect = Exception("Crew initialization failed")

        result = run_prompt_generator(
            rag_summary='{"domains": []}',
            crew_description="Test",
            llm_model="openai/gemini-2.5-flash",
        )

        # Should return default suggestions
        assert result is not None
        assert result.primary_agent.role == "Knowledge Assistant"


class TestPromptGeneratorCrewInitialization:
    """Tests for PromptGeneratorCrew class initialization."""

    @pytest.mark.requires_env
    def test_crew_initialization_default_model(self, mock_env_vars):
        """Test crew initialization with default model."""
        from crewai_test_suite.crews.prompt_generator.crew import PromptGeneratorCrew

        crew = PromptGeneratorCrew()

        assert crew.llm is not None

    @pytest.mark.requires_env
    def test_crew_initialization_custom_model(self, mock_env_vars):
        """Test crew initialization with custom model."""
        from crewai_test_suite.crews.prompt_generator.crew import PromptGeneratorCrew

        crew = PromptGeneratorCrew(llm_model="openai/gpt-4")

        assert crew.llm is not None
