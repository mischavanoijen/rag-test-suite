"""Tool for executing target crews (API or local mode)."""

import importlib
import json
import os
import sys
import time
from typing import Optional

import requests
from crewai.tools import BaseTool
from pydantic import Field


class CrewRunnerTool(BaseTool):
    """Execute the target crew with a test question."""

    name: str = "run_target_crew"
    description: str = """
    Send a question to the crew being tested and get its response.
    Supports both local execution (direct import) and API execution
    (deployed crews via CrewAI Enterprise).

    Args:
        question: The test question to send
        session_id: Optional session for multi-turn tests

    Returns:
        The crew's response string
    """

    # Configuration
    mode: str = Field(default="api", description="Testing mode: 'api' or 'local'")

    # Local mode settings
    crew_path: str = Field(default="", description="Path to crew for local testing")
    crew_module: str = Field(default="", description="Module path e.g. 'simple_rag.main'")

    # API mode settings (for deployed crews)
    api_url: str = Field(default="", description="CrewAI Enterprise kickoff URL")
    api_token_env_var: str = Field(default="TARGET_API_TOKEN", description="Env var for token")
    api_timeout: int = Field(default=300, description="Max wait time in seconds")
    api_poll_interval: int = Field(default=5, description="Poll interval in seconds")

    def _run(self, question: str, session_id: Optional[str] = None) -> str:
        """Execute the crew with the given question."""
        if self.mode == "api":
            return self._run_api(question, session_id)
        else:
            return self._run_local(question, session_id)

    def _run_api(self, question: str, session_id: Optional[str] = None) -> str:
        """Execute via CrewAI Enterprise API."""
        token = os.environ.get(self.api_token_env_var)
        if not token:
            raise RuntimeError(f"{self.api_token_env_var} environment variable not set")

        if not self.api_url:
            raise RuntimeError("api_url not configured")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        # Kickoff the crew
        payload = {"inputs": {"QUERY": question}}
        if session_id:
            payload["inputs"]["SESSION_ID"] = session_id

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()
            kickoff_data = response.json()
        except requests.RequestException as e:
            return f"API Error: {e}"

        # Check if async (returns kickoff_id) or sync (returns result directly)
        kickoff_id = kickoff_data.get("kickoff_id")
        if kickoff_id:
            return self._poll_for_result(kickoff_id, headers)

        # Sync response - result is direct
        return kickoff_data.get("result", json.dumps(kickoff_data))

    def _poll_for_result(self, kickoff_id: str, headers: dict) -> str:
        """Poll for async kickoff result."""
        # Construct status URL
        status_url = self.api_url.replace("/kickoff", f"/kickoffs/{kickoff_id}")
        start_time = time.time()

        while time.time() - start_time < self.api_timeout:
            try:
                status_resp = requests.get(status_url, headers=headers, timeout=30)
                status_data = status_resp.json()

                status = status_data.get("status", "")
                if status == "completed":
                    return status_data.get("result", "")
                elif status == "failed":
                    error = status_data.get("error", "Unknown error")
                    return f"Crew failed: {error}"
                elif status in ("pending", "running"):
                    time.sleep(self.api_poll_interval)
                else:
                    # Unknown status, wait and retry
                    time.sleep(self.api_poll_interval)
            except requests.RequestException as e:
                return f"Poll Error: {e}"

        return "Timeout: Crew execution timed out"

    def _run_local(self, question: str, session_id: Optional[str] = None) -> str:
        """Execute via subprocess to avoid asyncio conflicts with nested CrewAI Flows."""
        if not self.crew_module:
            raise RuntimeError("crew_module not configured for local mode")

        if not self.crew_path:
            raise RuntimeError("crew_path not configured for local mode")

        import subprocess

        # Escape the question for safe embedding in Python code
        escaped_question = question.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")

        # Use unique markers to extract only the result from stdout
        # CrewAI flows output verbose logging, so we need to separate the actual result
        result_marker_start = "<<<CREW_RESULT_START>>>"
        result_marker_end = "<<<CREW_RESULT_END>>>"

        # Build the Python command with result markers
        # We suppress Rich console output using environment variables instead of redirects
        # because redirecting stdout breaks LLM API calls in CrewAI flows
        python_code = f'''
import sys
import os

# Suppress CrewAI Rich console output
os.environ["TERM"] = "dumb"
os.environ["NO_COLOR"] = "1"
os.environ["FORCE_COLOR"] = "0"

# Disable CrewAI's verbose output
import logging
logging.getLogger("crewai").setLevel(logging.ERROR)
logging.getLogger("rich").setLevel(logging.ERROR)

sys.path.insert(0, "{self.crew_path}")

try:
    from {self.crew_module} import run
    result = run(inputs={{"query": "{escaped_question}"}})
except Exception as e:
    result = f"Execution Error: {{e}}"

# Print result with markers so we can extract it from CrewAI's verbose output
print("{result_marker_start}")
print(result if result else "")
print("{result_marker_end}")
'''

        try:
            # Run in subprocess using the crew's own venv if available
            crew_venv_python = os.path.join(
                os.path.dirname(self.crew_path), ".venv", "bin", "python"
            )
            if os.path.exists(crew_venv_python):
                python_cmd = crew_venv_python
            else:
                python_cmd = sys.executable

            # Pass through relevant environment variables
            env = os.environ.copy()
            env["CREWAI_TRACING_ENABLED"] = "false"
            # Suppress rich console output
            env["TERM"] = "dumb"
            env["NO_COLOR"] = "1"

            result = subprocess.run(
                [python_cmd, "-c", python_code],
                capture_output=True,
                text=True,
                timeout=180,  # Increased timeout for flow execution
                cwd=os.path.dirname(self.crew_path),
                env=env,
            )

            if result.returncode != 0:
                # Check for common errors
                stderr = result.stderr.strip()
                if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
                    return f"Import Error: {stderr.split(chr(10))[-1]}"
                return f"Execution Error: {stderr}"

            # Extract result between markers
            stdout = result.stdout
            if result_marker_start in stdout and result_marker_end in stdout:
                start_idx = stdout.index(result_marker_start) + len(result_marker_start)
                end_idx = stdout.index(result_marker_end)
                extracted = stdout[start_idx:end_idx].strip()
                return extracted
            else:
                # Fallback: return all stdout (old behavior)
                return stdout.strip()

        except subprocess.TimeoutExpired:
            return "Timeout Error: Crew execution exceeded 180 seconds"
        except Exception as e:
            return f"Subprocess Error: {e}"


def create_crew_runner_from_config(config: dict) -> CrewRunnerTool:
    """
    Create a CrewRunnerTool from configuration dictionary.

    Args:
        config: Configuration dictionary with 'target' section

    Returns:
        Configured CrewRunnerTool instance
    """
    target_config = config.get("target", {})
    mode = target_config.get("mode", "api")

    if mode == "api":
        api_url = os.environ.get(
            target_config.get("api_url_env_var", "TARGET_API_URL"), ""
        )
        return CrewRunnerTool(
            mode="api",
            api_url=api_url,
            api_token_env_var=target_config.get("api_token_env_var", "TARGET_API_TOKEN"),
            api_timeout=target_config.get("api_timeout_seconds", 300),
            api_poll_interval=target_config.get("api_poll_interval_seconds", 5),
        )
    else:
        return CrewRunnerTool(
            mode="local",
            crew_path=target_config.get("crew_path", ""),
            crew_module=target_config.get("crew_module", ""),
        )
