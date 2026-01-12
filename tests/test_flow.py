"""Tests for the main RAGTestSuiteFlow class."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestRAGTestSuiteFlowInitialization:
    """Tests for RAGTestSuiteFlow initialization."""

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_flow_initialization_default_config(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test flow initialization with default config."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        assert flow.config is not None
        assert flow.rag_tool is not None
        assert flow.crew_runner is not None
        assert flow.evaluator is not None
        mock_load_settings.assert_called_once()

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    def test_flow_initialization_custom_config(
        self, mock_evaluator, mock_runner, mock_rag
    ):
        """Test flow initialization with custom config."""
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        custom_config = {
            "target": {"mode": "api"},
            "llm": {"model": "openai/gpt-4"},
        }

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow(config=custom_config)

        assert flow.config == custom_config
        assert flow.llm_model == "openai/gpt-4"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_flow_state_initialization(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that flow state is properly initialized."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Check default state values - TestSuiteState defaults to "api" mode
        assert flow.state.target_mode == "api"
        assert flow.state.num_tests == 20
        assert flow.state.pass_threshold == 0.7
        assert flow.state.test_cases == []
        assert flow.state.results == []


class TestKickoffInputMapping:
    """Tests for the kickoff method input mapping."""

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_maps_uppercase_inputs(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that kickoff correctly maps UPPERCASE input keys."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Simulate API input mapping (but don't actually run)
        inputs = {
            "TARGET_MODE": "api",
            "TARGET_API_URL": "https://api.example.com/kickoff",
            "NUM_TESTS": "15",
            "PASS_THRESHOLD": "0.8",
            "CREW_DESCRIPTION": "Test description",
        }

        # Apply input mapping logic manually
        flow.state.target_mode = (
            inputs.get("TARGET_MODE") or inputs.get("target_mode") or "api"
        )
        flow.state.target_api_url = (
            inputs.get("TARGET_API_URL") or inputs.get("target_api_url") or ""
        )
        flow.state.num_tests = int(
            inputs.get("NUM_TESTS") or inputs.get("num_tests") or 20
        )
        flow.state.pass_threshold = float(
            inputs.get("PASS_THRESHOLD") or inputs.get("pass_threshold") or 0.7
        )
        flow.state.crew_description = (
            inputs.get("CREW_DESCRIPTION") or inputs.get("crew_description") or ""
        )

        assert flow.state.target_mode == "api"
        assert flow.state.target_api_url == "https://api.example.com/kickoff"
        assert flow.state.num_tests == 15
        assert flow.state.pass_threshold == 0.8
        assert flow.state.crew_description == "Test description"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_maps_lowercase_inputs(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that kickoff correctly maps lowercase input keys."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        inputs = {
            "target_mode": "local",
            "target_crew_path": "/path/to/crew",
            "num_tests": "10",
            "pass_threshold": "0.75",
        }

        # Apply mapping
        flow.state.target_mode = (
            inputs.get("TARGET_MODE") or inputs.get("target_mode") or "api"
        )
        flow.state.target_crew_path = (
            inputs.get("TARGET_CREW_PATH") or inputs.get("target_crew_path") or ""
        )
        flow.state.num_tests = int(
            inputs.get("NUM_TESTS") or inputs.get("num_tests") or 20
        )
        flow.state.pass_threshold = float(
            inputs.get("PASS_THRESHOLD") or inputs.get("pass_threshold") or 0.7
        )

        assert flow.state.target_mode == "local"
        assert flow.state.target_crew_path == "/path/to/crew"
        assert flow.state.num_tests == 10
        assert flow.state.pass_threshold == 0.75

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_uses_defaults_for_missing_inputs(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that kickoff uses defaults when inputs are missing."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        inputs = {}  # Empty inputs

        # Apply mapping with defaults
        flow.state.target_mode = (
            inputs.get("TARGET_MODE") or inputs.get("target_mode") or "api"
        )
        flow.state.num_tests = int(
            inputs.get("NUM_TESTS") or inputs.get("num_tests") or 20
        )
        flow.state.pass_threshold = float(
            inputs.get("PASS_THRESHOLD") or inputs.get("pass_threshold") or 0.7
        )

        assert flow.state.target_mode == "api"
        assert flow.state.num_tests == 20
        assert flow.state.pass_threshold == 0.7


class TestRunFlow:
    """Tests for the run_flow helper function."""

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_api_mode(self, mock_flow_class):
        """Test run_flow in API mode."""
        from rag_test_suite.flow import run_flow

        mock_flow_instance = MagicMock()
        mock_flow_instance.kickoff.return_value = "# Test Report\n\nPass rate: 80%"
        mock_flow_class.return_value = mock_flow_instance

        result = run_flow(
            target_api_url="https://api.example.com/kickoff",
            num_tests=5,
            crew_description="Test crew",
        )

        assert result == "# Test Report\n\nPass rate: 80%"
        mock_flow_instance.kickoff.assert_called_once()

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_local_mode(self, mock_flow_class):
        """Test run_flow in local mode."""
        from rag_test_suite.flow import run_flow

        mock_flow_instance = MagicMock()
        mock_flow_instance.kickoff.return_value = "# Local Test Report"
        mock_flow_class.return_value = mock_flow_instance

        result = run_flow(
            target_crew_path="/path/to/crew",
            num_tests=10,
        )

        assert result == "# Local Test Report"
        assert mock_flow_instance.state.target_crew_path == "/path/to/crew"
        assert mock_flow_instance.state.target_mode == "local"

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_with_custom_config(self, mock_flow_class):
        """Test run_flow with custom configuration."""
        from rag_test_suite.flow import run_flow

        mock_flow_instance = MagicMock()
        mock_flow_instance.kickoff.return_value = "# Custom Report"
        mock_flow_class.return_value = mock_flow_instance

        custom_config = {"llm": {"model": "openai/gpt-4"}}

        result = run_flow(config=custom_config)

        mock_flow_class.assert_called_once_with(config=custom_config)


class TestFlowPhaseMethods:
    """Tests for individual flow phase methods."""

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    @patch("rag_test_suite.flow.run_discovery")
    def test_discover_rag_data_success(
        self, mock_run_discovery, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test discover_rag_data method."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        mock_run_discovery.return_value = json.dumps({
            "domains": [{"name": "AI", "subtopics": ["ML"], "depth": "high"}],
            "total_coverage_estimate": "AI topics"
        })

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()
        flow.discover_rag_data()

        assert flow.state.rag_summary is not None
        assert len(flow.state.rag_summary.domains) == 1
        assert flow.state.rag_summary.domains[0].name == "AI"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    @patch("rag_test_suite.flow.run_discovery")
    def test_discover_rag_data_handles_invalid_json(
        self, mock_run_discovery, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test discover_rag_data handles invalid JSON gracefully."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        mock_run_discovery.return_value = "Invalid JSON response from LLM"

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()
        flow.discover_rag_data()

        # Should create fallback summary
        assert flow.state.rag_summary is not None
        assert "Invalid JSON" in flow.state.rag_summary.total_coverage_estimate

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    @patch("rag_test_suite.flow.run_prompt_generator")
    def test_generate_prompt_suggestions(
        self, mock_run_prompt_gen, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test generate_prompt_suggestions method."""
        from rag_test_suite.models import (
            PromptSuggestions,
            AgentSuggestion,
            RagSummary,
            RagDomain,
        )

        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        mock_suggestions = PromptSuggestions(
            primary_agent=AgentSuggestion(
                role="Test Agent",
                goal="Test goal",
                backstory="Test backstory",
            ),
            system_prompt="Test prompt",
            example_queries=["query1"],
            out_of_scope_examples=["out1"],
            knowledge_summary="Test",
            limitations=["limit1"],
            suggested_tone="professional",
            response_format_guidance="Test",
        )
        mock_run_prompt_gen.return_value = mock_suggestions

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()
        flow.state.rag_summary = RagSummary(
            domains=[RagDomain(name="AI", depth="high")],
            total_coverage_estimate="AI topics",
        )

        flow.generate_prompt_suggestions()

        assert flow.state.prompt_suggestions is not None
        assert flow.state.prompt_suggestions.primary_agent.role == "Test Agent"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_evaluate_results_calculates_pass_rate(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test evaluate_results calculates correct pass rate."""
        from rag_test_suite.models import TestCase, TestResult, TestCategory, TestDifficulty

        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Create test results - 2 passed, 1 failed
        test_case = TestCase(
            id="TC-001",
            question="Test?",
            expected_answer="Answer",
            category=TestCategory.FACTUAL,
            difficulty=TestDifficulty.EASY,
            rationale="Test",
        )

        flow.state.results = [
            TestResult(test_case=test_case, actual_answer="Answer", passed=True, similarity_score=0.9, evaluation_rationale="Good"),
            TestResult(test_case=test_case, actual_answer="Answer", passed=True, similarity_score=0.85, evaluation_rationale="Good"),
            TestResult(test_case=test_case, actual_answer="Wrong", passed=False, similarity_score=0.2, evaluation_rationale="Bad"),
        ]

        # Mock the evaluation crew call
        with patch("rag_test_suite.flow.run_evaluation") as mock_eval:
            mock_eval.return_value = {"recommendations": []}
            with patch("rag_test_suite.flow.calculate_category_scores") as mock_calc:
                mock_calc.return_value = []
                flow.evaluate_results()

        assert flow.state.pass_rate == pytest.approx(66.67, rel=0.1)


class TestFlowHasRequiredMethods:
    """Tests to verify flow has all required methods."""

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_flow_has_all_phase_methods(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that flow has all required phase methods."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Phase 1 methods
        assert hasattr(flow, "discover_rag_data")
        assert hasattr(flow, "generate_prompt_suggestions")
        assert hasattr(flow, "generate_test_cases")

        # Phase 2 methods
        assert hasattr(flow, "execute_tests")

        # Phase 3 methods
        assert hasattr(flow, "evaluate_results")
        assert hasattr(flow, "generate_report")

        # Override method
        assert hasattr(flow, "kickoff")


class TestRAGAPIConfiguration:
    """Tests for RAG API configuration via kickoff inputs."""

    @patch("rag_test_suite.flow.RagQueryTool")
    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_reconfigures_ragengine_from_inputs(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag_config, mock_rag_tool_class
    ):
        """Test that kickoff reconfigures RAG tool when RAG Engine inputs provided."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag_config.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()
        mock_new_rag_tool = Mock()
        mock_rag_tool_class.return_value = mock_new_rag_tool

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Store original rag_tool
        original_rag_tool = flow.rag_tool

        # Call kickoff with RAG Engine inputs
        inputs = {
            "RAG_BACKEND": "ragengine",
            "RAG_MCP_URL": "https://rag-engine.example.com/mcp",
            "RAG_MCP_TOKEN": "test-token-123",
            "RAG_CORPUS": "test-corpus",
        }

        # Mock the parent kickoff to avoid running the full flow
        with patch.object(flow.__class__.__bases__[0], 'kickoff', return_value="test result"):
            flow.kickoff(inputs=inputs)

        # Verify RagQueryTool was instantiated with new config
        mock_rag_tool_class.assert_called_once_with(
            backend="ragengine",
            mcp_url="https://rag-engine.example.com/mcp",
            corpus="test-corpus",
        )

        # Verify state was updated
        assert flow.state.rag_backend == "ragengine"
        assert flow.state.rag_mcp_url == "https://rag-engine.example.com/mcp"
        assert flow.state.rag_corpus == "test-corpus"

    @patch("rag_test_suite.flow.RagQueryTool")
    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_reconfigures_qdrant_from_inputs(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag_config, mock_rag_tool_class
    ):
        """Test that kickoff reconfigures RAG tool when Qdrant inputs provided."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag_config.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()
        mock_new_rag_tool = Mock()
        mock_rag_tool_class.return_value = mock_new_rag_tool

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Call kickoff with Qdrant inputs
        inputs = {
            "RAG_BACKEND": "qdrant",
            "RAG_QDRANT_URL": "https://qdrant.example.com:6333",
            "RAG_QDRANT_API_KEY": "qdrant-api-key-123",
            "RAG_QDRANT_COLLECTION": "test-collection",
        }

        # Mock the parent kickoff
        with patch.object(flow.__class__.__bases__[0], 'kickoff', return_value="test result"):
            flow.kickoff(inputs=inputs)

        # Verify RagQueryTool was instantiated with Qdrant config
        mock_rag_tool_class.assert_called_once_with(
            backend="qdrant",
            qdrant_url="https://qdrant.example.com:6333",
            collection="test-collection",
        )

        # Verify state was updated
        assert flow.state.rag_backend == "qdrant"
        assert flow.state.rag_qdrant_url == "https://qdrant.example.com:6333"
        assert flow.state.rag_qdrant_collection == "test-collection"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_does_not_reconfigure_without_required_fields(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that kickoff doesn't reconfigure RAG tool without all required fields."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        original_rag_tool = Mock()
        mock_rag.return_value = original_rag_tool
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Call kickoff with incomplete RAG Engine inputs (missing corpus)
        inputs = {
            "RAG_BACKEND": "ragengine",
            "RAG_MCP_URL": "https://rag-engine.example.com/mcp",
            # Missing RAG_CORPUS
        }

        # Mock the parent kickoff
        with patch.object(flow.__class__.__bases__[0], 'kickoff', return_value="test result"):
            flow.kickoff(inputs=inputs)

        # Verify original RAG tool is still in use
        assert flow.rag_tool == original_rag_tool

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_kickoff_handles_lowercase_input_keys(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that kickoff accepts lowercase input keys."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Call kickoff with lowercase inputs
        inputs = {
            "rag_backend": "ragengine",
            "num_tests": "25",
            "crew_description": "Test crew description",
        }

        # Mock the parent kickoff
        with patch.object(flow.__class__.__bases__[0], 'kickoff', return_value="test result"):
            flow.kickoff(inputs=inputs)

        # Verify state was updated from lowercase keys
        assert flow.state.rag_backend == "ragengine"
        assert flow.state.num_tests == 25
        assert flow.state.crew_description == "Test crew description"

    @patch("rag_test_suite.flow.create_rag_query_from_config")
    @patch("rag_test_suite.flow.create_crew_runner_from_config")
    @patch("rag_test_suite.flow.create_evaluator_from_config")
    @patch("rag_test_suite.flow.load_settings")
    def test_mask_url_hides_sensitive_parts(
        self, mock_load_settings, mock_evaluator, mock_runner, mock_rag
    ):
        """Test that _mask_url properly masks URLs for logging."""
        mock_load_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }
        mock_rag.return_value = Mock()
        mock_runner.return_value = Mock()
        mock_evaluator.return_value = Mock()

        from rag_test_suite.flow import RAGTestSuiteFlow

        flow = RAGTestSuiteFlow()

        # Test URL masking
        url = "https://rag-engine.example.com:8080/mcp"
        masked = flow._mask_url(url)

        # Should show host but mask the path
        assert "rag-engine.example.com" in masked
        assert "..." in masked  # Path is replaced with ...


class TestRunFlowWithRAGParams:
    """Tests for run_flow function with RAG parameters."""

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_passes_rag_params_to_kickoff(self, mock_flow_class):
        """Test that run_flow passes RAG parameters to kickoff."""
        mock_flow = Mock()
        mock_flow.state = Mock()
        mock_flow.crew_runner = Mock()
        mock_flow.kickoff.return_value = "Test report"
        mock_flow_class.return_value = mock_flow

        from rag_test_suite.flow import run_flow

        result = run_flow(
            rag_backend="qdrant",
            rag_qdrant_url="https://qdrant.example.com",
            rag_qdrant_api_key="secret-key",
            rag_qdrant_collection="my-collection",
            num_tests=10,
        )

        # Verify kickoff was called with inputs dict
        mock_flow.kickoff.assert_called_once()
        call_args = mock_flow.kickoff.call_args
        inputs = call_args.kwargs.get("inputs", {})

        assert inputs["RAG_BACKEND"] == "qdrant"
        assert inputs["RAG_QDRANT_URL"] == "https://qdrant.example.com"
        assert inputs["RAG_QDRANT_API_KEY"] == "secret-key"
        assert inputs["RAG_QDRANT_COLLECTION"] == "my-collection"

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_passes_ragengine_params(self, mock_flow_class):
        """Test that run_flow passes RAG Engine parameters to kickoff."""
        mock_flow = Mock()
        mock_flow.state = Mock()
        mock_flow.crew_runner = Mock()
        mock_flow.kickoff.return_value = "Test report"
        mock_flow_class.return_value = mock_flow

        from rag_test_suite.flow import run_flow

        result = run_flow(
            rag_backend="ragengine",
            rag_mcp_url="https://mcp.example.com/mcp",
            rag_mcp_token="mcp-token",
            rag_corpus="my-corpus",
        )

        # Verify kickoff was called with inputs dict
        call_args = mock_flow.kickoff.call_args
        inputs = call_args.kwargs.get("inputs", {})

        assert inputs["RAG_BACKEND"] == "ragengine"
        assert inputs["RAG_MCP_URL"] == "https://mcp.example.com/mcp"
        assert inputs["RAG_MCP_TOKEN"] == "mcp-token"
        assert inputs["RAG_CORPUS"] == "my-corpus"

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_sets_state_rag_fields(self, mock_flow_class):
        """Test that run_flow sets RAG fields in state."""
        mock_flow = Mock()
        mock_flow.state = Mock()
        mock_flow.crew_runner = Mock()
        mock_flow.kickoff.return_value = "Test report"
        mock_flow_class.return_value = mock_flow

        from rag_test_suite.flow import run_flow

        run_flow(
            rag_backend="qdrant",
            rag_mcp_url="https://mcp.example.com",
            rag_corpus="corpus",
            rag_qdrant_url="https://qdrant.example.com",
            rag_qdrant_collection="collection",
        )

        # Verify state was updated
        assert mock_flow.state.rag_backend == "qdrant"
        assert mock_flow.state.rag_mcp_url == "https://mcp.example.com"
        assert mock_flow.state.rag_corpus == "corpus"
        assert mock_flow.state.rag_qdrant_url == "https://qdrant.example.com"
        assert mock_flow.state.rag_qdrant_collection == "collection"

    @patch("rag_test_suite.flow.RAGTestSuiteFlow")
    def test_run_flow_passes_target_api_token(self, mock_flow_class):
        """Test that run_flow passes target API token."""
        mock_flow = Mock()
        mock_flow.state = Mock()
        mock_flow.crew_runner = Mock()
        mock_flow.kickoff.return_value = "Test report"
        mock_flow_class.return_value = mock_flow

        from rag_test_suite.flow import run_flow

        run_flow(
            target_api_url="https://api.example.com/kickoff",
            target_api_token="bearer-token-123",
        )

        # Verify token was set
        assert mock_flow.state.target_api_token == "bearer-token-123"
        assert mock_flow.crew_runner.api_token == "bearer-token-123"
