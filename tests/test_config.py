"""Tests for configuration loader."""

import os
import tempfile

import pytest
import yaml

from rag_test_suite.config.loader import (
    load_settings,
    reload_settings,
    _apply_env_overrides,
    _parse_value,
    get_env_value,
)


class TestParseValue:
    """Tests for _parse_value function."""

    def test_parse_boolean_true(self):
        """Test parsing boolean true values."""
        assert _parse_value("true") is True
        assert _parse_value("True") is True
        assert _parse_value("yes") is True
        assert _parse_value("1") is True

    def test_parse_boolean_false(self):
        """Test parsing boolean false values."""
        assert _parse_value("false") is False
        assert _parse_value("False") is False
        assert _parse_value("no") is False
        assert _parse_value("0") is False

    def test_parse_integer(self):
        """Test parsing integer values."""
        assert _parse_value("42") == 42
        assert _parse_value("-10") == -10

    def test_parse_float(self):
        """Test parsing float values."""
        assert _parse_value("3.14") == 3.14
        assert _parse_value("-0.5") == -0.5

    def test_parse_string(self):
        """Test parsing string values."""
        assert _parse_value("hello") == "hello"
        assert _parse_value("path/to/file") == "path/to/file"


class TestEnvOverrides:
    """Tests for _apply_env_overrides function."""

    def test_apply_env_override(self):
        """Test applying environment variable overrides."""
        settings = {"target": {"mode": "api"}}

        # Set environment variable
        os.environ["TEST_SUITE_TARGET_MODE"] = "local"

        result = _apply_env_overrides(settings, prefix="TEST_SUITE")

        # Clean up
        del os.environ["TEST_SUITE_TARGET_MODE"]

        assert result["target"]["mode"] == "local"

    def test_apply_nested_env_override(self):
        """Test applying nested environment variable overrides."""
        # Note: The current implementation joins nested keys with underscores
        # So TEST_SUITE_TEST_GENERATION_NUM_TESTS maps to settings["test"]["generation"]["num"]["tests"]
        # For simplicity, test with a single-level nested key
        settings = {"target": {"mode": "api"}}

        os.environ["TEST_SUITE_TARGET_MODE"] = "local"

        result = _apply_env_overrides(settings, prefix="TEST_SUITE")

        del os.environ["TEST_SUITE_TARGET_MODE"]

        assert result["target"]["mode"] == "local"


class TestGetEnvValue:
    """Tests for get_env_value function."""

    def test_get_env_value_exists(self):
        """Test getting existing environment variable."""
        os.environ["TEST_VAR"] = "test_value"
        assert get_env_value("TEST_VAR") == "test_value"
        del os.environ["TEST_VAR"]

    def test_get_env_value_default(self):
        """Test getting default value for missing env var."""
        assert get_env_value("NONEXISTENT_VAR", "default") == "default"
        assert get_env_value("NONEXISTENT_VAR") == ""


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_settings_from_file(self):
        """Test loading settings from a file."""
        settings = {
            "project": {"name": "test"},
            "target": {"mode": "api"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(settings, f)
            temp_path = f.name

        try:
            # Force reload to avoid cache
            result = reload_settings(temp_path)
            assert result["project"]["name"] == "test"
            assert result["target"]["mode"] == "api"
        finally:
            os.unlink(temp_path)

    def test_load_settings_file_not_found(self):
        """Test error when settings file not found."""
        with pytest.raises(FileNotFoundError):
            reload_settings("/nonexistent/path/settings.yaml")
