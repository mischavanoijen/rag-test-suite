"""Configuration loader for CrewAI Test Suite."""

import os
from pathlib import Path
from typing import Any

import yaml

# Global cache for settings
_settings_cache: dict | None = None


def load_settings(settings_path: str | None = None) -> dict:
    """
    Load settings from YAML file with environment variable overrides.

    Args:
        settings_path: Optional path to settings file. If not provided,
                      uses the default settings.yaml in config directory.

    Returns:
        Dictionary of settings with env var overrides applied.
    """
    global _settings_cache

    if _settings_cache is not None:
        return _settings_cache

    if settings_path is None:
        config_dir = Path(__file__).parent
        settings_path = config_dir / "settings.yaml"
    else:
        settings_path = Path(settings_path)

    if not settings_path.exists():
        raise FileNotFoundError(f"Settings file not found: {settings_path}")

    with open(settings_path) as f:
        settings = yaml.safe_load(f)

    # Apply environment variable overrides
    settings = _apply_env_overrides(settings)

    _settings_cache = settings
    return settings


def reload_settings(settings_path: str | None = None) -> dict:
    """Force reload settings, ignoring cache."""
    global _settings_cache
    _settings_cache = None
    return load_settings(settings_path)


def _apply_env_overrides(settings: dict, prefix: str = "TEST_SUITE") -> dict:
    """
    Apply environment variable overrides to settings.

    Environment variable pattern: {PREFIX}_{SECTION}_{KEY}=value
    Example: TEST_SUITE_TARGET_MODE=local

    Args:
        settings: Original settings dictionary
        prefix: Environment variable prefix

    Returns:
        Settings with environment variable overrides applied.
    """
    for key, value in os.environ.items():
        if not key.startswith(f"{prefix}_"):
            continue

        # Parse the key: TEST_SUITE_SECTION_SUBSECTION_KEY
        parts = key[len(prefix) + 1 :].lower().split("_")

        if len(parts) < 2:
            continue

        # Navigate to the correct nested dict
        current = settings
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            if not isinstance(current[part], dict):
                break
            current = current[part]
        else:
            # Set the value with type inference
            current[parts[-1]] = _parse_value(value)

    return settings


def _parse_value(value: str) -> Any:
    """
    Parse a string value into appropriate Python type.

    Args:
        value: String value from environment variable

    Returns:
        Parsed value (bool, int, float, or string)
    """
    # Boolean
    if value.lower() in ("true", "yes", "1"):
        return True
    if value.lower() in ("false", "no", "0"):
        return False

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # String
    return value


def get_env_value(env_var_name: str, default: str = "") -> str:
    """
    Get a value from an environment variable.

    Args:
        env_var_name: Name of the environment variable
        default: Default value if not set

    Returns:
        Environment variable value or default
    """
    return os.environ.get(env_var_name, default)
