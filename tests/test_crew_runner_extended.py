"""Extended tests for the CrewRunnerTool."""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestLocalModeExecution:
    """Tests for local mode crew execution."""

    @patch("subprocess.run")
    def test_run_local_success(self, mock_run):
        """Test successful local crew execution."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "<<<CREW_RESULT_START>>>\nThis is the crew response.\n<<<CREW_RESULT_END>>>"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew/src",
            crew_module="simple_rag.main",
        )

        result = tool._run(question="What is AI?")

        assert "This is the crew response" in result

    @patch("subprocess.run")
    def test_run_local_with_special_characters(self, mock_run):
        """Test local execution with special characters in question."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "<<<CREW_RESULT_START>>>\nResponse here.\n<<<CREW_RESULT_END>>>"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew",
            crew_module="crew.main",
        )

        # Question with quotes and special characters
        result = tool._run(question='What is "AI"? Is it like O\'Brien\'s work?')

        assert "Response here" in result

    @patch("subprocess.run")
    def test_run_local_import_error(self, mock_run):
        """Test local execution with import error."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "<<<CREW_RESULT_START>>>\nExecution Error: ModuleNotFoundError\n<<<CREW_RESULT_END>>>"
        mock_result.stderr = "ModuleNotFoundError: No module named 'nonexistent'"
        mock_run.return_value = mock_result

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew",
            crew_module="nonexistent.main",
        )

        result = tool._run(question="Test")

        assert "Error" in result or "ModuleNotFoundError" in result

    @patch("subprocess.run")
    def test_run_local_execution_error(self, mock_run):
        """Test local execution with runtime error."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "<<<CREW_RESULT_START>>>\nExecution Error: ValueError: invalid input\n<<<CREW_RESULT_END>>>"
        mock_result.stderr = "ValueError: invalid input"
        mock_run.return_value = mock_result

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew",
            crew_module="crew.main",
        )

        result = tool._run(question="Test")

        assert "Error" in result

    @patch("subprocess.run")
    def test_run_local_no_markers(self, mock_run):
        """Test local execution when markers are missing."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Some output without markers"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew",
            crew_module="crew.main",
        )

        result = tool._run(question="Test")

        # Should return full stdout or handle gracefully
        assert result is not None

    @patch("subprocess.run")
    def test_run_local_timeout(self, mock_run):
        """Test local execution with timeout."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="python", timeout=300)

        tool = CrewRunnerTool(
            mode="local",
            crew_path="/path/to/crew",
            crew_module="crew.main",
        )

        result = tool._run(question="Test")

        assert "timeout" in result.lower() or "error" in result.lower()


class TestApiModeExecution:
    """Tests for API mode crew execution."""

    @patch("requests.post")
    def test_run_api_sync_response(self, mock_post, monkeypatch):
        """Test API mode with synchronous response."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        # Set token env var
        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "This is the API response"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        result = tool._run(question="What is AI?")

        assert "API response" in result

    @patch("requests.get")
    @patch("requests.post")
    def test_run_api_async_polling(self, mock_post, mock_get, monkeypatch):
        """Test API mode with async response requiring polling."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        # Initial kickoff returns kickoff_id
        kickoff_response = Mock()
        kickoff_response.status_code = 202
        kickoff_response.json.return_value = {"kickoff_id": "abc-123"}
        kickoff_response.raise_for_status = Mock()
        mock_post.return_value = kickoff_response

        # Polling returns completed status
        poll_response = Mock()
        poll_response.status_code = 200
        poll_response.json.return_value = {
            "status": "completed",
            "result": "Async result here"
        }
        mock_get.return_value = poll_response

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        with patch.object(tool, "_poll_for_result") as mock_poll:
            mock_poll.return_value = "Async result here"
            result = tool._run(question="Test")

        assert result is not None

    @patch("requests.post")
    def test_run_api_error_response(self, mock_post, monkeypatch):
        """Test API mode with error response."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool
        import requests

        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.RequestException("Server Error")
        mock_post.return_value = mock_response

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        result = tool._run(question="Test")

        assert "error" in result.lower()

    def test_run_api_missing_token(self, monkeypatch):
        """Test API mode with missing token."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        # Ensure env var is not set
        monkeypatch.delenv("TARGET_API_TOKEN", raising=False)

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        with pytest.raises(RuntimeError) as exc_info:
            tool._run(question="Test")

        assert "TARGET_API_TOKEN" in str(exc_info.value)


class TestPollForResult:
    """Tests for the _poll_for_result method."""

    @patch("requests.get")
    @patch("time.sleep", return_value=None)  # Skip sleep in tests
    def test_poll_for_result_success(self, mock_sleep, mock_get, monkeypatch):
        """Test successful polling for result."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "completed",
            "result": "Final result"
        }
        mock_get.return_value = mock_response

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        result = tool._poll_for_result(
            kickoff_id="abc-123",
            headers={"Authorization": "Bearer test-token"},
        )

        assert "Final result" in result

    @patch("requests.get")
    @patch("time.sleep", return_value=None)
    def test_poll_for_result_pending_then_complete(self, mock_sleep, mock_get, monkeypatch):
        """Test polling that starts pending then completes."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        # First call returns pending, second returns completed
        pending_response = Mock()
        pending_response.status_code = 200
        pending_response.json.return_value = {"status": "pending"}

        complete_response = Mock()
        complete_response.status_code = 200
        complete_response.json.return_value = {
            "status": "completed",
            "result": "Done!"
        }

        mock_get.side_effect = [pending_response, complete_response]

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        result = tool._poll_for_result(
            kickoff_id="abc-123",
            headers={"Authorization": "Bearer test-token"},
        )

        assert "Done!" in result

    @patch("requests.get")
    @patch("time.sleep", return_value=None)
    def test_poll_for_result_failed_status(self, mock_sleep, mock_get, monkeypatch):
        """Test polling with failed status."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        monkeypatch.setenv("TARGET_API_TOKEN", "test-token")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "failed",
            "error": "Crew execution failed"
        }
        mock_get.return_value = mock_response

        tool = CrewRunnerTool(
            mode="api",
            api_url="https://api.crewai.com/crews/123/kickoff",
            api_token_env_var="TARGET_API_TOKEN",
        )

        result = tool._poll_for_result(
            kickoff_id="abc-123",
            headers={"Authorization": "Bearer test-token"},
        )

        # Should return error message or the status
        assert result is not None


class TestCreateCrewRunnerFromConfig:
    """Tests for create_crew_runner_from_config factory function."""

    def test_create_api_mode_from_config(self, monkeypatch):
        """Test creating API mode runner from config."""
        from rag_test_suite.tools.crew_runner import create_crew_runner_from_config

        monkeypatch.setenv("TARGET_API_URL", "https://app.crewai.com/api/v1/crews/123/kickoff")

        config = {
            "target": {
                "mode": "api",
                "api_url_env_var": "TARGET_API_URL",
                "api_token_env_var": "TARGET_API_TOKEN",
            }
        }

        tool = create_crew_runner_from_config(config)

        assert tool.mode == "api"
        assert tool.api_url == "https://app.crewai.com/api/v1/crews/123/kickoff"

    def test_create_local_mode_from_config(self):
        """Test creating local mode runner from config."""
        from rag_test_suite.tools.crew_runner import create_crew_runner_from_config

        config = {
            "target": {
                "mode": "local",
                "crew_path": "/path/to/crew/src",
                "crew_module": "simple_rag.main",
            }
        }

        tool = create_crew_runner_from_config(config)

        assert tool.mode == "local"
        assert tool.crew_path == "/path/to/crew/src"
        assert tool.crew_module == "simple_rag.main"


class TestToolAttributes:
    """Tests for CrewRunnerTool attributes."""

    def test_tool_name(self):
        """Test tool has correct name."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        tool = CrewRunnerTool(mode="local")

        assert tool.name == "run_target_crew"

    def test_tool_description(self):
        """Test tool has description."""
        from rag_test_suite.tools.crew_runner import CrewRunnerTool

        tool = CrewRunnerTool(mode="local")

        assert tool.description is not None
        assert len(tool.description) > 0
