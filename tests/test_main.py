"""Tests for the main module entry points."""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from io import StringIO


class TestMainCLI:
    """Tests for the CLI main function."""

    def test_main_with_help_flag(self):
        """Test main function with --help flag."""
        from crewai_test_suite.main import main

        with patch.object(sys, "argv", ["crewai_test_suite", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # --help exits with code 0
            assert exc_info.value.code == 0

    @patch("crewai_test_suite.main.run_flow")
    def test_main_with_required_args(self, mock_run_flow):
        """Test main function with required arguments."""
        mock_run_flow.return_value = "# Test Report"

        from crewai_test_suite.main import main

        test_args = [
            "crewai_test_suite",
            "--target-crew-path", "/path/to/crew",
            "--num-tests", "5",
            "--crew-description", "Test crew",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("builtins.print") as mock_print:
                result = main()

        mock_run_flow.assert_called_once()
        # main() doesn't return a value (returns None)
        assert result is None

    @patch("crewai_test_suite.main.run_flow")
    def test_main_with_output_file(self, mock_run_flow, tmp_path):
        """Test main function with output file option."""
        mock_run_flow.return_value = "# Test Report\n\nContent here"

        output_file = tmp_path / "report.md"

        from crewai_test_suite.main import main

        test_args = [
            "crewai_test_suite",
            "--target-crew-path", "/path/to/crew",
            "--output", str(output_file),
        ]

        with patch.object(sys, "argv", test_args):
            result = main()

        # main() doesn't return a value (returns None)
        assert result is None
        assert output_file.exists()
        assert "Test Report" in output_file.read_text()

    @patch("crewai_test_suite.main.run_flow")
    def test_main_with_api_mode(self, mock_run_flow):
        """Test main function with API mode arguments."""
        mock_run_flow.return_value = "# API Test Report"

        from crewai_test_suite.main import main

        test_args = [
            "crewai_test_suite",
            "--target-api-url", "https://api.example.com/kickoff",
            "--num-tests", "10",
        ]

        with patch.object(sys, "argv", test_args):
            with patch("builtins.print"):
                result = main()

        mock_run_flow.assert_called_once()
        call_kwargs = mock_run_flow.call_args[1]
        assert call_kwargs["target_api_url"] == "https://api.example.com/kickoff"
        assert call_kwargs["num_tests"] == 10


class TestRunFlowEntry:
    """Tests for the run_flow_entry function (CrewAI Enterprise entry point)."""

    @patch("crewai_test_suite.main.run_flow")
    def test_run_flow_entry_parses_env_vars(self, mock_run_flow, monkeypatch):
        """Test that run_flow_entry parses environment variables."""
        mock_run_flow.return_value = "# Report"

        # Set environment variables
        monkeypatch.setenv("TARGET_MODE", "api")
        monkeypatch.setenv("TARGET_API_URL", "https://api.example.com/kickoff")
        monkeypatch.setenv("NUM_TESTS", "15")
        monkeypatch.setenv("PASS_THRESHOLD", "0.8")
        monkeypatch.setenv("CREW_DESCRIPTION", "Test crew description")

        from crewai_test_suite.main import run_flow_entry

        with patch("builtins.print"):
            run_flow_entry()

        mock_run_flow.assert_called_once()
        call_kwargs = mock_run_flow.call_args[1]
        assert call_kwargs["target_api_url"] == "https://api.example.com/kickoff"
        assert call_kwargs["num_tests"] == 15
        assert call_kwargs["crew_description"] == "Test crew description"

    @patch("crewai_test_suite.main.run_flow")
    def test_run_flow_entry_uses_defaults(self, mock_run_flow, monkeypatch):
        """Test that run_flow_entry uses defaults for missing env vars."""
        mock_run_flow.return_value = "# Report"

        # Clear environment variables
        for var in ["TARGET_MODE", "TARGET_API_URL", "NUM_TESTS", "CREW_DESCRIPTION"]:
            monkeypatch.delenv(var, raising=False)

        from crewai_test_suite.main import run_flow_entry

        with patch("builtins.print"):
            run_flow_entry()

        mock_run_flow.assert_called_once()
        call_kwargs = mock_run_flow.call_args[1]
        assert call_kwargs["num_tests"] == 20  # Default
        assert call_kwargs["target_api_url"] == ""

    @patch("crewai_test_suite.main.run_flow")
    def test_run_flow_entry_with_local_mode(self, mock_run_flow, monkeypatch):
        """Test run_flow_entry with local mode configuration."""
        mock_run_flow.return_value = "# Local Report"

        monkeypatch.setenv("TARGET_MODE", "local")
        monkeypatch.setenv("TARGET_CREW_PATH", "/path/to/simple-rag")
        monkeypatch.setenv("NUM_TESTS", "5")

        from crewai_test_suite.main import run_flow_entry

        with patch("builtins.print"):
            run_flow_entry()

        call_kwargs = mock_run_flow.call_args[1]
        assert call_kwargs["target_crew_path"] == "/path/to/simple-rag"


class TestRunFlowWithTrigger:
    """Tests for the run_flow_with_trigger function."""

    @patch("crewai_test_suite.main.run_flow_entry")
    def test_run_flow_with_trigger_calls_entry(self, mock_entry):
        """Test that run_flow_with_trigger calls run_flow_entry."""
        from crewai_test_suite.main import run_flow_with_trigger

        run_flow_with_trigger()

        mock_entry.assert_called_once()


class TestPlaceholderFunctions:
    """Tests for placeholder functions (train, replay, test)."""

    def test_train_returns_none(self):
        """Test that train function returns None (placeholder)."""
        from crewai_test_suite.main import train

        result = train()

        assert result is None

    def test_replay_returns_none(self):
        """Test that replay function returns None (placeholder)."""
        from crewai_test_suite.main import replay

        result = replay()

        assert result is None

    def test_test_returns_none(self):
        """Test that test function returns None (placeholder)."""
        from crewai_test_suite.main import test

        result = test()

        assert result is None


class TestModuleExports:
    """Tests for module exports (__all__)."""

    def test_module_exports_flow_class(self):
        """Test that RAGTestSuiteFlow is exported."""
        from crewai_test_suite import main

        assert "RAGTestSuiteFlow" in main.__all__

    def test_module_exports_entry_points(self):
        """Test that entry point functions are exported."""
        from crewai_test_suite import main

        assert "run_flow_entry" in main.__all__
        assert "run_flow_with_trigger" in main.__all__
        assert "main" in main.__all__

    def test_can_import_flow_class_from_main(self):
        """Test that RAGTestSuiteFlow can be imported from main."""
        from crewai_test_suite.main import RAGTestSuiteFlow

        assert RAGTestSuiteFlow is not None


class TestArgumentParsing:
    """Tests for argument parsing edge cases."""

    def test_num_tests_conversion(self):
        """Test that num_tests is properly converted to int."""
        from crewai_test_suite.main import main

        with patch("crewai_test_suite.main.run_flow") as mock_run_flow:
            mock_run_flow.return_value = "# Report"

            test_args = [
                "crewai_test_suite",
                "--target-crew-path", "/path",
                "--num-tests", "25",
            ]

            with patch.object(sys, "argv", test_args):
                with patch("builtins.print"):
                    main()

            call_kwargs = mock_run_flow.call_args[1]
            assert isinstance(call_kwargs["num_tests"], int)
            assert call_kwargs["num_tests"] == 25

    def test_crew_description_argument(self):
        """Test that crew_description argument is passed correctly."""
        from crewai_test_suite.main import main

        with patch("crewai_test_suite.main.run_flow") as mock_run_flow:
            mock_run_flow.return_value = "# Report"

            test_args = [
                "crewai_test_suite",
                "--target-crew-path", "/path",
                "--crew-description", "Customer support assistant",
            ]

            with patch.object(sys, "argv", test_args):
                with patch("builtins.print"):
                    main()

            call_kwargs = mock_run_flow.call_args[1]
            assert call_kwargs["crew_description"] == "Customer support assistant"
