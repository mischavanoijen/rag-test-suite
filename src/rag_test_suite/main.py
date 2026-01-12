"""Main entry point for CrewAI Test Suite."""

import argparse
import os
import sys
from typing import Optional

from dotenv import load_dotenv

from rag_test_suite.flow import RAGTestSuiteFlow, run_flow
from rag_test_suite.config.loader import load_settings

# Export Flow class for CrewAI Enterprise Flow API detection
__all__ = ["RAGTestSuiteFlow", "run_flow_entry", "run_flow_with_trigger", "main"]


def main():
    """CLI entry point with argument parsing."""
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="CrewAI Test Suite - Automated testing for RAG-based crews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Run Modes:
  full              Run all phases: discovery → prompts → tests → execute → report
  prompt_only       Run only: discovery → prompt suggestions (no tests)
  generate_only     Run only: discovery → prompts → test generation (no execution)
  execute_only      Execute tests from CSV file → evaluate → report
  generate_and_execute  Same as 'full'

Examples:
  # Generate prompt suggestions only
  python -m rag_test_suite.main --run-mode prompt_only

  # Generate test questions without executing
  python -m rag_test_suite.main --run-mode generate_only --num-tests 10

  # Execute tests from a CSV file
  python -m rag_test_suite.main --run-mode execute_only --test-csv tests.csv

  # Full test run with API target
  python -m rag_test_suite.main --run-mode full --target-api-url https://...
        """,
    )
    parser.add_argument(
        "--run-mode",
        type=str,
        default="full",
        choices=["full", "prompt_only", "generate_only", "execute_only", "generate_and_execute"],
        help="Execution mode (default: full)",
    )
    parser.add_argument(
        "--test-csv",
        type=str,
        default="",
        help="Path to CSV file with test cases (for execute_only mode)",
    )
    parser.add_argument(
        "--target-api-url",
        type=str,
        default=os.environ.get("TARGET_API_URL", ""),
        help="CrewAI Enterprise API URL for the target crew",
    )
    parser.add_argument(
        "--target-crew-path",
        type=str,
        default="",
        help="Path to local crew for testing",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=20,
        help="Number of test cases to generate (default: 20)",
    )
    parser.add_argument(
        "--crew-description",
        type=str,
        default="",
        help="Description of what the crew should do",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="Output file path for the report/results",
    )

    args = parser.parse_args()

    # Validate execute_only mode requires CSV
    if args.run_mode == "execute_only" and not args.test_csv:
        parser.error("--test-csv is required when using --run-mode execute_only")

    # Run the flow
    result = run_flow(
        target_api_url=args.target_api_url,
        target_crew_path=args.target_crew_path,
        num_tests=args.num_tests,
        crew_description=args.crew_description,
        run_mode=args.run_mode,
        test_csv_path=args.test_csv,
    )

    # Output the result
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"\nOutput saved to: {args.output}")
    elif args.run_mode not in ["prompt_only", "generate_only"]:
        # For full/execute modes, the report is already printed
        pass


def run_flow_entry():
    """
    Run the flow (entry point for kickoff script).

    This function is called by CrewAI Enterprise when triggering the flow.
    It reads inputs from environment variables.
    """
    load_dotenv()

    # Read inputs from environment variables
    run_mode = os.environ.get("RUN_MODE", "full").strip().lower()
    test_csv_path = os.environ.get("TEST_CSV_PATH", "").strip()
    target_api_url = os.environ.get("TARGET_API_URL", "").strip()
    target_crew_path = os.environ.get("TARGET_CREW_PATH", "").strip()
    num_tests = int(os.environ.get("NUM_TESTS", "20"))
    crew_description = os.environ.get("CREW_DESCRIPTION", "").strip()

    # Run the flow
    result = run_flow(
        target_api_url=target_api_url,
        target_crew_path=target_crew_path,
        num_tests=num_tests,
        crew_description=crew_description,
        run_mode=run_mode,
        test_csv_path=test_csv_path,
    )

    print(result)
    return result


def run_flow_with_trigger():
    """Run flow via Enterprise trigger."""
    return run_flow_entry()


def train():
    """Train the crew (placeholder for CrewAI compatibility)."""
    print("Training not implemented for flows.")


def replay(task_id: str = ""):
    """Replay a task (placeholder for CrewAI compatibility)."""
    print("Replay not implemented for flows.")


def test():
    """Test the crew (placeholder for CrewAI compatibility)."""
    print("Running test suite self-test...")
    # Could implement a self-test here


if __name__ == "__main__":
    main()
