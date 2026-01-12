#!/usr/bin/env python3
"""End-to-end test for the CrewAI Test Suite.

This script tests the full test suite flow against simple-rag.

Required Environment Variables:
-------------------------------

For the test suite itself:
  OPENAI_API_KEY      - LiteLLM proxy key for test suite agents
  OPENAI_API_BASE     - LiteLLM proxy URL (e.g., https://litellm-proxy-xxx.run.app/v1)

For RAG discovery (querying simple-rag's knowledge base):
  PG_RAG_MCP_URL      - RAG Engine MCP server URL
  PG_RAG_TOKEN        - RAG Engine authentication token
  PG_RAG_CORPUS       - Vertex AI RAG corpus path

For local mode testing (simple-rag):
  (same as above - simple-rag uses the same RAG credentials)

For API mode testing (deployed crew):
  TARGET_API_URL      - CrewAI Enterprise kickoff URL
  TARGET_API_TOKEN    - Bearer token for API authentication

Usage:
------

1. Check what credentials are missing:
   python tests/e2e_test.py --check-env

2. Run dry-run test (mocked external calls):
   python tests/e2e_test.py --dry-run

3. Run full test (requires all credentials):
   python tests/e2e_test.py

4. Run with specific number of tests:
   python tests/e2e_test.py --num-tests 5
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def check_environment(mode: str = "local"):
    """Check which environment variables are set.

    Args:
        mode: Testing mode - "local" or "api"
    """
    # Core variables always needed
    required_vars = {
        "Test Suite LLM": [
            ("OPENAI_API_KEY", "LiteLLM proxy key", True),
            ("OPENAI_API_BASE", "LiteLLM proxy URL", True),
        ],
        "RAG Discovery": [
            ("PG_RAG_MCP_URL", "RAG Engine MCP server URL", True),
            ("PG_RAG_TOKEN", "RAG Engine auth token", True),
            ("PG_RAG_CORPUS", "Vertex AI RAG corpus path", True),
        ],
        "API Mode Testing": [
            ("TARGET_API_URL", "CrewAI Enterprise kickoff URL", mode == "api"),
            ("TARGET_API_TOKEN", "API Bearer token", mode == "api"),
        ],
    }

    print("\n" + "=" * 60)
    print(f"Environment Variable Check (mode: {mode})")
    print("=" * 60)

    all_required_set = True
    for category, vars_list in required_vars.items():
        print(f"\n{category}:")
        for var_name, description, required in vars_list:
            value = os.environ.get(var_name)
            if value:
                masked = value[:8] + "..." if len(value) > 10 else "***"
                print(f"  ✓ {var_name}: {masked}")
            else:
                status = "REQUIRED" if required else "optional"
                print(f"  ✗ {var_name}: NOT SET ({description}) [{status}]")
                if required:
                    all_required_set = False

    print("\n" + "-" * 60)
    if all_required_set:
        print("All required environment variables are set. Ready for test.")
    else:
        print("Some required variables are missing. Use --dry-run for mocked test.")
    print("-" * 60 + "\n")

    return all_required_set


def run_dry_run_test():
    """Run a dry-run test with mocked external dependencies."""
    print("\n" + "=" * 60)
    print("DRY-RUN TEST (Mocked External Calls)")
    print("=" * 60)

    # Import test suite components
    from rag_test_suite.models import (
        TestCase, TestResult, TestSuiteState,
        TestCategory, TestDifficulty, RagDomain, RagSummary
    )
    from rag_test_suite.tools.crew_runner import CrewRunnerTool
    from rag_test_suite.tools.evaluator import EvaluatorTool
    from rag_test_suite.tools.rag_query import RagQueryTool
    from rag_test_suite.config.loader import load_settings

    print("\n1. Testing Models...")
    # Test model creation
    state = TestSuiteState(
        target_mode="local",
        num_tests=3,
        pass_threshold=0.7,
    )
    print(f"   ✓ Created TestSuiteState: mode={state.target_mode}, tests={state.num_tests}")

    # Create test cases
    test_case = TestCase(
        id="E2E-001",
        question="What is artificial intelligence?",
        expected_answer="AI is the simulation of human intelligence in machines.",
        category=TestCategory.FACTUAL,
        difficulty=TestDifficulty.EASY,
        rationale="Tests basic knowledge retrieval",
    )
    state.test_cases.append(test_case)
    print(f"   ✓ Created TestCase: {test_case.id}")

    print("\n2. Testing Tools (Mocked)...")

    # Test CrewRunnerTool
    runner = CrewRunnerTool(mode="local", crew_path="", crew_module="")
    print(f"   ✓ Created CrewRunnerTool: mode={runner.mode}")

    # Test EvaluatorTool
    evaluator = EvaluatorTool(pass_threshold=0.7)
    print(f"   ✓ Created EvaluatorTool: threshold={evaluator.pass_threshold}")

    # Test RagQueryTool
    rag = RagQueryTool(backend="ragengine")
    print(f"   ✓ Created RagQueryTool: backend={rag.backend}")

    print("\n3. Testing Config Loader...")
    settings = load_settings()
    print(f"   ✓ Loaded settings: target.mode={settings['target']['mode']}")

    print("\n4. Creating Mock Test Results...")
    # Simulate a test result
    result = TestResult(
        test_case=test_case,
        actual_answer="AI refers to artificial intelligence, which simulates human cognition.",
        passed=True,
        similarity_score=0.85,
        evaluation_rationale="Good semantic match with expected answer.",
    )
    state.results.append(result)
    print(f"   ✓ Created TestResult: passed={result.passed}, score={result.similarity_score}")

    print("\n5. Testing Evaluation Functions...")
    from rag_test_suite.crews.evaluation.crew import (
        calculate_category_scores,
        format_category_breakdown,
    )

    scores = calculate_category_scores(state.results)
    print(f"   ✓ Calculated category scores: {len(scores)} categories")

    breakdown = format_category_breakdown(scores)
    print(f"   ✓ Generated breakdown: {len(breakdown)} chars")

    print("\n" + "=" * 60)
    print("DRY-RUN TEST COMPLETE - All components working")
    print("=" * 60)

    return True


def run_full_test(num_tests: int = 5):
    """Run the full test suite against simple-rag.

    Args:
        num_tests: Number of tests to generate
    """
    print("\n" + "=" * 60)
    print(f"FULL E2E TEST (num_tests={num_tests})")
    print("=" * 60)

    # Load settings to determine mode
    from rag_test_suite.config.loader import load_settings
    settings = load_settings()
    mode = settings.get("target", {}).get("mode", "local")

    # Check credentials first
    if not check_environment(mode):
        print("\nERROR: Missing required environment variables.")
        print("Set the missing variables or use --dry-run instead.")
        return False

    # Import flow
    from rag_test_suite.flow import RAGTestSuiteFlow
    from rag_test_suite.models import TestSuiteState

    print("\n1. Initializing Test Suite Flow...")
    flow = RAGTestSuiteFlow()
    print("   ✓ Flow initialized")

    print("\n2. Setting up state...")
    flow.state.num_tests = num_tests
    flow.state.target_mode = "local"
    print(f"   ✓ State configured: {num_tests} tests, local mode")

    # Disable CrewAI interactive prompts
    os.environ["CREWAI_TRACING_ENABLED"] = "false"

    print("\n3. Running flow (this may take several minutes)...")
    start_time = datetime.now()

    try:
        result = flow.kickoff()
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n4. Flow completed in {elapsed:.1f}s")
        print("\n" + "-" * 60)
        print("RESULTS:")
        print("-" * 60)

        # Print summary
        total = len(flow.state.results)
        if total == 0:
            print(f"   WARNING: No test results generated!")
            print(f"   Test cases generated: {len(flow.state.test_cases)}")
            if flow.state.rag_summary:
                print(f"   RAG domains discovered: {len(flow.state.rag_summary.domains)}")
            return False

        passed = sum(1 for r in flow.state.results if r.passed)
        print(f"   Tests: {passed}/{total} passed ({100*passed/total:.1f}%)")

        # Print report excerpt
        if flow.state.quality_report:
            print("\n   Report preview (first 500 chars):")
            print("   " + "-" * 40)
            print("   " + flow.state.quality_report[:500].replace("\n", "\n   "))

        print("\n" + "=" * 60)
        print("FULL E2E TEST COMPLETE")
        print("=" * 60)

        return True

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"\n   ERROR after {elapsed:.1f}s: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="End-to-end test for CrewAI Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check environment variables and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with mocked external dependencies",
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=5,
        help="Number of tests to generate (default: 5)",
    )

    args = parser.parse_args()

    if args.check_env:
        check_environment()
        return 0

    if args.dry_run:
        success = run_dry_run_test()
    else:
        success = run_full_test(args.num_tests)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
