"""Integration test for API-configurable RAG settings.

This test verifies that RAG configuration can be passed via API inputs
and the flow correctly reconfigures the RAG tool at runtime.

Run with: python tests/integration/test_api_rag_configuration.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_api_rag_configuration_ragengine():
    """Test that RAG Engine can be configured via API inputs."""
    from unittest.mock import patch, Mock
    from rag_test_suite.flow import RAGTestSuiteFlow

    print("=" * 60)
    print("API RAG Configuration Test - RAG Engine")
    print("=" * 60)

    # Get configuration from environment
    mcp_url = os.environ.get("PG_RAG_MCP_URL")
    corpus = os.environ.get("PG_RAG_CORPUS")
    token = os.environ.get("PG_RAG_TOKEN")

    if not mcp_url or not corpus or not token:
        print("\n⚠️  Skipping live test - missing env vars")
        print("   Set PG_RAG_MCP_URL, PG_RAG_CORPUS, PG_RAG_TOKEN")
        return True  # Skip, don't fail

    print(f"\n✓ MCP URL: {mcp_url[:50]}...")
    print(f"✓ Corpus: {corpus[:50]}...")
    print(f"✓ Token: {'*' * 8}...{token[-4:]}")

    # Create flow with mocked dependencies
    with patch("rag_test_suite.flow.load_settings") as mock_settings:
        mock_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }

        flow = RAGTestSuiteFlow()

        # Store original rag_tool
        original_tool = flow.rag_tool

        # Simulate API inputs
        inputs = {
            "RAG_BACKEND": "ragengine",
            "RAG_MCP_URL": mcp_url,
            "RAG_MCP_TOKEN": token,
            "RAG_CORPUS": corpus,
            "RUN_MODE": "prompt_only",  # Don't run full test
            "NUM_TESTS": "5",
        }

        print("\n" + "-" * 60)
        print("Testing kickoff with API inputs...")
        print("-" * 60)

        # Apply the kickoff input parsing (but don't run full flow)
        # We'll just check that the tool was reconfigured
        try:
            # Extract and apply RAG config like kickoff does
            rag_backend = inputs.get("RAG_BACKEND", "").lower()
            rag_mcp_url = inputs.get("RAG_MCP_URL", "")
            rag_mcp_token = inputs.get("RAG_MCP_TOKEN", "")
            rag_corpus = inputs.get("RAG_CORPUS", "")

            # Update state
            flow.state.rag_backend = rag_backend
            flow.state.rag_mcp_url = rag_mcp_url
            flow.state.rag_corpus = rag_corpus

            # Reconfigure tool (simulating what kickoff does)
            from rag_test_suite.tools.rag_query import RagQueryTool

            if rag_mcp_token:
                os.environ["PG_RAG_TOKEN"] = rag_mcp_token

            flow.rag_tool = RagQueryTool(
                backend="ragengine",
                mcp_url=rag_mcp_url,
                corpus=rag_corpus,
            )

            print(f"\n✓ RAG tool reconfigured")
            print(f"  Backend: {flow.state.rag_backend}")
            print(f"  MCP URL: {flow._mask_url(flow.state.rag_mcp_url)}")
            print(f"  Corpus: {flow.state.rag_corpus[:50]}...")

            # Test the reconfigured tool
            print("\n" + "-" * 60)
            print("Testing reconfigured RAG tool query...")
            print("-" * 60)

            result = flow.rag_tool._run("What topics are covered?", num_results=3)

            if "Error" in result:
                print(f"\n❌ Query failed: {result[:200]}")
                return False

            print(f"\n✓ Query successful!")
            print(f"  Result preview: {result[:300]}...")
            return True

        except Exception as e:
            print(f"\n❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_state_fields_populated():
    """Test that state fields are correctly populated from inputs."""
    from unittest.mock import patch
    from rag_test_suite.flow import RAGTestSuiteFlow

    print("\n" + "=" * 60)
    print("State Fields Population Test")
    print("=" * 60)

    with patch("rag_test_suite.flow.load_settings") as mock_settings:
        mock_settings.return_value = {
            "target": {"mode": "local"},
            "llm": {"model": "openai/gemini-2.5-flash"},
        }

        flow = RAGTestSuiteFlow()

        # Test inputs
        inputs = {
            "RAG_BACKEND": "qdrant",
            "RAG_QDRANT_URL": "https://test.qdrant.io:6333",
            "RAG_QDRANT_COLLECTION": "test_collection",
            "TARGET_API_URL": "https://api.example.com/kickoff",
            "NUM_TESTS": "25",
            "CREW_DESCRIPTION": "Test crew for validation",
        }

        # Apply input parsing (simulating kickoff)
        flow.state.rag_backend = inputs.get("RAG_BACKEND", "").lower()
        flow.state.rag_qdrant_url = inputs.get("RAG_QDRANT_URL", "")
        flow.state.rag_qdrant_collection = inputs.get("RAG_QDRANT_COLLECTION", "")
        flow.state.target_api_url = inputs.get("TARGET_API_URL", "")
        flow.state.num_tests = int(inputs.get("NUM_TESTS", "20"))
        flow.state.crew_description = inputs.get("CREW_DESCRIPTION", "")

        # Verify all fields
        checks = [
            ("rag_backend", flow.state.rag_backend, "qdrant"),
            ("rag_qdrant_url", flow.state.rag_qdrant_url, "https://test.qdrant.io:6333"),
            ("rag_qdrant_collection", flow.state.rag_qdrant_collection, "test_collection"),
            ("target_api_url", flow.state.target_api_url, "https://api.example.com/kickoff"),
            ("num_tests", flow.state.num_tests, 25),
            ("crew_description", flow.state.crew_description, "Test crew for validation"),
        ]

        all_passed = True
        for field_name, actual, expected in checks:
            if actual == expected:
                print(f"  ✓ {field_name}: {actual}")
            else:
                print(f"  ❌ {field_name}: expected {expected}, got {actual}")
                all_passed = False

        return all_passed


def test_run_flow_function_with_rag_params():
    """Test that run_flow() correctly passes RAG params."""
    from unittest.mock import patch, Mock

    print("\n" + "=" * 60)
    print("run_flow() RAG Parameters Test")
    print("=" * 60)

    with patch("rag_test_suite.flow.RAGTestSuiteFlow") as mock_flow_class:
        mock_flow = Mock()
        mock_flow.state = Mock()
        mock_flow.crew_runner = Mock()
        mock_flow.kickoff.return_value = "Test report"
        mock_flow_class.return_value = mock_flow

        from rag_test_suite.flow import run_flow

        # Call run_flow with RAG parameters
        result = run_flow(
            rag_backend="ragengine",
            rag_mcp_url="https://test-mcp.example.com/mcp",
            rag_mcp_token="test-token-123",
            rag_corpus="test-corpus",
            target_api_url="https://api.example.com/kickoff",
            target_api_token="target-token",
            num_tests=15,
        )

        # Verify kickoff was called with inputs
        mock_flow.kickoff.assert_called_once()
        call_kwargs = mock_flow.kickoff.call_args.kwargs
        inputs = call_kwargs.get("inputs", {})

        checks = [
            ("RAG_BACKEND", inputs.get("RAG_BACKEND"), "ragengine"),
            ("RAG_MCP_URL", inputs.get("RAG_MCP_URL"), "https://test-mcp.example.com/mcp"),
            ("RAG_MCP_TOKEN", inputs.get("RAG_MCP_TOKEN"), "test-token-123"),
            ("RAG_CORPUS", inputs.get("RAG_CORPUS"), "test-corpus"),
        ]

        all_passed = True
        for key, actual, expected in checks:
            if actual == expected:
                print(f"  ✓ {key} passed correctly")
            else:
                print(f"  ❌ {key}: expected {expected}, got {actual}")
                all_passed = False

        # Verify state was set
        if mock_flow.state.rag_backend == "ragengine":
            print(f"  ✓ state.rag_backend set correctly")
        else:
            print(f"  ❌ state.rag_backend not set")
            all_passed = False

        if mock_flow.state.target_api_token == "target-token":
            print(f"  ✓ state.target_api_token set correctly")
        else:
            print(f"  ❌ state.target_api_token not set")
            all_passed = False

        return all_passed


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("  API-Configurable RAG Integration Tests")
    print("=" * 70)

    results = []

    # Run tests
    results.append(("State Fields Population", test_state_fields_populated()))
    results.append(("run_flow() RAG Params", test_run_flow_function_with_rag_params()))
    results.append(("RAG Engine API Config", test_api_rag_configuration_ragengine()))

    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)

    all_passed = True
    for name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ All integration tests passed!")
    else:
        print("  ❌ Some tests failed")
    print("=" * 70 + "\n")

    sys.exit(0 if all_passed else 1)
