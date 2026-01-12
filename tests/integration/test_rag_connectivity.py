"""Integration test for RAG Engine MCP connectivity.

Run with: python tests/integration/test_rag_connectivity.py
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_rag_connectivity():
    """Test that we can connect to and query the RAG Engine MCP."""
    from rag_test_suite.tools.rag_query import RagQueryTool

    # Get configuration from environment
    mcp_url = os.environ.get("PG_RAG_MCP_URL")
    corpus = os.environ.get("PG_RAG_CORPUS")
    token = os.environ.get("PG_RAG_TOKEN")

    print("=" * 60)
    print("RAG Engine MCP Connectivity Test")
    print("=" * 60)

    # Check required environment variables
    missing = []
    if not mcp_url:
        missing.append("PG_RAG_MCP_URL")
    if not corpus:
        missing.append("PG_RAG_CORPUS")
    if not token:
        missing.append("PG_RAG_TOKEN")

    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these in your .env file:")
        for var in missing:
            print(f"  {var}=<value>")
        return False

    print(f"\n✓ MCP URL: {mcp_url}")
    print(f"✓ Corpus: {corpus[:50]}...")
    print(f"✓ Token: {'*' * 8}...{token[-4:]}")

    # Create tool
    tool = RagQueryTool(
        backend="ragengine",
        mcp_url=mcp_url,
        corpus=corpus,
        mcp_token_env_var="PG_RAG_TOKEN",
    )

    # Test query
    print("\n" + "-" * 60)
    print("Testing query: 'What is BPO?'")
    print("-" * 60)

    try:
        result = tool._run("What is BPO?", num_results=3)
        print("\nResult:")
        print(result[:1000] if len(result) > 1000 else result)

        if "Error" in result:
            print(f"\n❌ Query returned an error")
            return False

        if "No results" in result:
            print(f"\n⚠️  No results found (corpus may be empty or query not matching)")
            return True  # Connection works, just no results

        print(f"\n✓ Query successful!")
        return True

    except Exception as e:
        print(f"\n❌ Exception during query: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_discovery_topics():
    """Test querying for various topics to understand RAG content."""
    from rag_test_suite.tools.rag_query import RagQueryTool

    mcp_url = os.environ.get("PG_RAG_MCP_URL")
    corpus = os.environ.get("PG_RAG_CORPUS")

    if not mcp_url or not corpus:
        print("Skipping discovery test - missing env vars")
        return

    tool = RagQueryTool(
        backend="ragengine",
        mcp_url=mcp_url,
        corpus=corpus,
        mcp_token_env_var="PG_RAG_TOKEN",
    )

    test_queries = [
        "customer experience trends",
        "AI in contact centers",
        "market size projections",
        "competitor analysis",
    ]

    print("\n" + "=" * 60)
    print("RAG Content Discovery")
    print("=" * 60)

    for query in test_queries:
        print(f"\n→ Query: '{query}'")
        try:
            result = tool._run(query, num_results=2)
            if "Error" in result or "No results" in result:
                print(f"  ⚠️  {result[:100]}")
            else:
                # Extract first result preview
                lines = result.split("\n")
                for line in lines[:5]:
                    if line.strip():
                        print(f"  {line[:80]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    success = test_rag_connectivity()

    if success:
        test_discovery_topics()
        print("\n" + "=" * 60)
        print("✓ Integration test completed successfully")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ Integration test failed")
        print("=" * 60)
        sys.exit(1)
