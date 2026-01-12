#!/usr/bin/env python3
"""Quick test for RAG connectivity."""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_rag_connectivity():
    """Test that we can connect to the RAG Engine."""
    from crewai_test_suite.tools.rag_query import RagQueryTool

    # Get credentials from env (note: mcp_token_env_var is used, not direct token)
    mcp_url = os.environ.get("PG_RAG_MCP_URL", "")
    corpus = os.environ.get("PG_RAG_CORPUS", "")
    token = os.environ.get("PG_RAG_TOKEN", "")

    print(f"MCP URL: {mcp_url[:40]}..." if mcp_url else "MCP URL: NOT SET")
    print(f"Token: {token[:10]}..." if token else "Token: NOT SET")
    print(f"Corpus: {corpus[:50]}..." if corpus else "Corpus: NOT SET")

    if not all([mcp_url, token, corpus]):
        print("\nERROR: Missing RAG credentials")
        return False

    # Create tool - uses env vars via mcp_token_env_var
    tool = RagQueryTool(
        backend="ragengine",
        mcp_url=mcp_url,
        mcp_token_env_var="PG_RAG_TOKEN",
        corpus=corpus,
    )

    print("\nQuerying RAG for 'What topics are covered in this knowledge base?'...")
    result = tool._run("What topics are covered in this knowledge base?")

    print(f"\nResult ({len(result)} chars):")
    print("-" * 50)
    print(result[:1500] if len(result) > 1500 else result)
    print("-" * 50)

    # Use assert instead of return to avoid pytest warning
    assert "error" not in result.lower(), f"RAG query returned error: {result}"


if __name__ == "__main__":
    try:
        test_rag_connectivity()
        print("\nSUCCESS: RAG connectivity test passed")
        sys.exit(0)
    except AssertionError as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
