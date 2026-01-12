"""Tests for tools."""

import json
import os
from unittest.mock import Mock, patch, MagicMock

import pytest

from crewai_test_suite.tools.crew_runner import (
    CrewRunnerTool,
    create_crew_runner_from_config,
)
from crewai_test_suite.tools.evaluator import (
    EvaluatorTool,
    create_evaluator_from_config,
)
from crewai_test_suite.tools.rag_query import (
    RagQueryTool,
    create_rag_query_from_config,
)


class TestCrewRunnerTool:
    """Tests for CrewRunnerTool."""

    def test_tool_attributes(self):
        """Test tool has correct attributes."""
        tool = CrewRunnerTool()
        assert tool.name == "run_target_crew"
        assert "question" in tool.description

    def test_api_mode_missing_token(self):
        """Test API mode raises error without token."""
        tool = CrewRunnerTool(mode="api", api_url="https://api.example.com")

        # Ensure env var is not set
        if "TARGET_API_TOKEN" in os.environ:
            del os.environ["TARGET_API_TOKEN"]

        with pytest.raises(RuntimeError) as exc_info:
            tool._run("test question")
        assert "TARGET_API_TOKEN" in str(exc_info.value)

    def test_local_mode_missing_module(self):
        """Test local mode raises error without module."""
        tool = CrewRunnerTool(mode="local", crew_module="")

        with pytest.raises(RuntimeError) as exc_info:
            tool._run("test question")
        assert "not configured" in str(exc_info.value).lower()

    @patch("crewai_test_suite.tools.crew_runner.requests.post")
    def test_api_mode_success(self, mock_post):
        """Test successful API call."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {"result": "Test answer"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        os.environ["TARGET_API_TOKEN"] = "test_token"

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.example.com/kickoff",
        )

        result = tool._run("What is AI?")

        del os.environ["TARGET_API_TOKEN"]

        assert result == "Test answer"
        mock_post.assert_called_once()

    def test_create_from_config_api(self):
        """Test creating tool from config (API mode)."""
        config = {
            "target": {
                "mode": "api",
                "api_url_env_var": "TARGET_API_URL",
                "api_token_env_var": "TARGET_API_TOKEN",
                "api_timeout_seconds": 120,
            }
        }

        os.environ["TARGET_API_URL"] = "https://api.example.com"
        tool = create_crew_runner_from_config(config)
        del os.environ["TARGET_API_URL"]

        assert tool.mode == "api"
        assert tool.api_url == "https://api.example.com"
        assert tool.api_timeout == 120

    def test_create_from_config_local(self):
        """Test creating tool from config (local mode)."""
        config = {
            "target": {
                "mode": "local",
                "crew_path": "/path/to/crew",
                "crew_module": "my_crew.main",
            }
        }

        tool = create_crew_runner_from_config(config)

        assert tool.mode == "local"
        assert tool.crew_path == "/path/to/crew"
        assert tool.crew_module == "my_crew.main"


class TestEvaluatorTool:
    """Tests for EvaluatorTool."""

    def test_tool_attributes(self):
        """Test tool has correct attributes."""
        tool = EvaluatorTool()
        assert tool.name == "evaluate_response"
        assert "expected" in tool.description

    def test_build_evaluation_prompt(self):
        """Test building evaluation prompt."""
        tool = EvaluatorTool(pass_threshold=0.7)

        prompt = tool._build_evaluation_prompt(
            expected="Expected answer",
            actual="Actual answer",
            question="Test question?",
        )

        assert "Expected answer" in prompt
        assert "Actual answer" in prompt
        assert "Test question?" in prompt
        assert "0.7" in prompt

    @patch("crewai_test_suite.tools.evaluator.requests.post")
    def test_evaluate_success(self, mock_post):
        """Test successful evaluation."""
        # Setup mock
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {"passed": True, "score": 0.85, "rationale": "Good match"}
                        )
                    }
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        os.environ["OPENAI_API_KEY"] = "test_key"
        os.environ["OPENAI_API_BASE"] = "https://api.example.com"

        tool = EvaluatorTool()
        result = tool._run(
            expected="AI is artificial intelligence",
            actual="AI stands for artificial intelligence",
            question="What is AI?",
        )

        del os.environ["OPENAI_API_KEY"]
        del os.environ["OPENAI_API_BASE"]

        result_dict = json.loads(result)
        assert result_dict["passed"] is True
        assert result_dict["score"] == 0.85

    def test_create_from_config(self):
        """Test creating evaluator from config."""
        config = {
            "evaluation": {
                "judge_model": "openai/gpt-4",
                "pass_threshold": 0.8,
            }
        }

        tool = create_evaluator_from_config(config)

        assert tool.judge_model == "openai/gpt-4"
        assert tool.pass_threshold == 0.8


class TestRagQueryTool:
    """Tests for RagQueryTool."""

    def test_tool_attributes(self):
        """Test tool has correct attributes."""
        tool = RagQueryTool()
        assert tool.name == "rag_query"
        assert "query" in tool.description

    def test_ragengine_missing_config(self):
        """Test RAG Engine mode fails without config."""
        tool = RagQueryTool(backend="ragengine", mcp_url="", corpus="")

        result = tool._run("test query")
        assert "not configured" in result.lower() or "not set" in result.lower()

    def test_qdrant_missing_config(self):
        """Test Qdrant mode fails without config."""
        tool = RagQueryTool(backend="qdrant", qdrant_url="", collection="")

        result = tool._run("test query")
        assert "not configured" in result.lower()

    def test_create_from_config_ragengine(self):
        """Test creating tool from config (RAG Engine)."""
        config = {
            "rag": {
                "backend": "ragengine",
                "ragengine": {
                    "mcp_url_env_var": "PG_RAG_MCP_URL",
                    "token_env_var": "PG_RAG_TOKEN",
                    "corpus_env_var": "PG_RAG_CORPUS",
                    "default_results": 5,
                },
            }
        }

        os.environ["PG_RAG_MCP_URL"] = "https://mcp.example.com"
        os.environ["PG_RAG_CORPUS"] = "test-corpus"

        tool = create_rag_query_from_config(config)

        del os.environ["PG_RAG_MCP_URL"]
        del os.environ["PG_RAG_CORPUS"]

        assert tool.backend == "ragengine"
        assert tool.mcp_url == "https://mcp.example.com"
        assert tool.corpus == "test-corpus"

    def test_create_from_config_qdrant(self):
        """Test creating tool from config (Qdrant)."""
        config = {
            "rag": {
                "backend": "qdrant",
                "qdrant": {
                    "url_env_var": "QDRANT_URL",
                    "collection_env_var": "QDRANT_COLLECTION",
                    "embedding_model": "text-embedding-004",
                },
            }
        }

        os.environ["QDRANT_URL"] = "https://qdrant.example.com"
        os.environ["QDRANT_COLLECTION"] = "test-collection"

        tool = create_rag_query_from_config(config)

        del os.environ["QDRANT_URL"]
        del os.environ["QDRANT_COLLECTION"]

        assert tool.backend == "qdrant"
        assert tool.qdrant_url == "https://qdrant.example.com"
        assert tool.collection == "test-collection"
