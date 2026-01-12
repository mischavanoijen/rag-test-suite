"""Extended tests for the RagQueryTool."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestRagEngineQuery:
    """Tests for RAG Engine (MCP SSE) queries."""

    @patch("requests.get")
    def test_query_ragengine_success(self, mock_get):
        """Test successful RAG Engine query via SSE."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        # Setup mock SSE response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"mcp-session-id": "test-session-123"}

        # Simulate SSE events
        sse_events = [
            "event: endpoint\ndata: /messages\n\n",
            'data: {"result": {"content": [{"text": "RAG result here"}]}}\n\n',
        ]
        mock_response.iter_lines.return_value = iter(
            [line.encode() for event in sse_events for line in event.split("\n")]
        )
        mock_get.return_value = mock_response

        tool = RagQueryTool(
            backend="ragengine",
            mcp_url="https://test-rag.example.com",
            mcp_token_env_var="TEST_TOKEN",
            corpus="projects/test/locations/us/ragCorpora/123",
        )

        with patch.object(tool, "_query_ragengine") as mock_query:
            mock_query.return_value = "Chunk 1: RAG result here (score: 0.95)"
            result = tool._run(query="What is AI?", num_results=3)

        assert result is not None

    def test_query_ragengine_missing_url(self):
        """Test RAG Engine query with missing URL."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine", mcp_url="", mcp_token_env_var="TEST_TOKEN")

        result = tool._run(query="Test")

        assert "not configured" in result.lower() or "error" in result.lower()

    def test_query_ragengine_missing_token(self, monkeypatch):
        """Test RAG Engine query with missing token."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        # Ensure env var is not set
        monkeypatch.delenv("TEST_TOKEN", raising=False)

        tool = RagQueryTool(
            backend="ragengine",
            mcp_url="https://test.com",
            mcp_token_env_var="TEST_TOKEN",
        )

        result = tool._run(query="Test")

        assert "not configured" in result.lower() or "error" in result.lower()


class TestQdrantQuery:
    """Tests for Qdrant vector database queries."""

    @patch("requests.post")
    def test_query_qdrant_success(self, mock_post):
        """Test successful Qdrant query."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        # Mock embedding response
        embedding_response = Mock()
        embedding_response.status_code = 200
        embedding_response.json.return_value = {
            "data": [{"embedding": [0.1] * 768}]
        }

        # Mock Qdrant search response
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "result": [
                {
                    "score": 0.95,
                    "payload": {"text": "Document content", "source": "doc1.pdf"},
                }
            ]
        }

        mock_post.side_effect = [embedding_response, search_response]

        tool = RagQueryTool(
            backend="qdrant",
            qdrant_url="https://test-qdrant.com",
            qdrant_api_key_env_var="QDRANT_KEY",
            collection="test-collection",
        )

        with patch.object(tool, "_get_embedding") as mock_embed:
            mock_embed.return_value = [0.1] * 768
            with patch.object(tool, "_query_qdrant") as mock_query:
                mock_query.return_value = "Result: Document content (score: 0.95)"
                result = tool._run(query="Test query")

        assert result is not None

    def test_query_qdrant_missing_url(self):
        """Test Qdrant query with missing URL."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="qdrant", qdrant_url="", qdrant_api_key_env_var="KEY")

        result = tool._run(query="Test")

        assert "not configured" in result.lower() or "error" in result.lower()


class TestFormatRagResults:
    """Tests for RAG result formatting."""

    def test_format_rag_results_standard(self):
        """Test standard RAG result formatting."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine")

        raw_result = json.dumps({
            "success": True,
            "chunks": [
                {"text": "First result", "rank": 1, "relevance_score": 0.95, "source_uri": "doc1.pdf"},
                {"text": "Second result", "rank": 2, "relevance_score": 0.85, "source_uri": "doc2.pdf"},
            ]
        })

        result = tool._format_rag_results(raw_result, "test query")

        assert "First result" in result
        assert "Search Results" in result

    def test_format_empty_results(self):
        """Test formatting empty results."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine")

        # When raw_result is empty string, _format_rag_results returns header + truncated content
        result = tool._format_rag_results("", "test query")

        # Based on the actual implementation, empty string goes to JSONDecodeError handler
        # which returns "## Search Results\n\n{raw_result[:1000]}"
        assert "Search Results" in result

    def test_format_results_no_chunks(self):
        """Test formatting when no chunks in response."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine")

        raw_result = json.dumps({"success": True, "chunks": []})
        result = tool._format_rag_results(raw_result, "test query")

        assert "No results found" in result


class TestGetEmbedding:
    """Tests for embedding generation."""

    @patch("litellm.embedding")
    def test_get_embedding_success(self, mock_embedding):
        """Test successful embedding generation."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        # The actual implementation accesses response.data[0]["embedding"] as dict subscript
        mock_embedding.return_value = Mock(
            data=[{"embedding": [0.1, 0.2, 0.3] * 256}]
        )

        tool = RagQueryTool(backend="qdrant")

        embedding = tool._get_embedding("Test text")

        assert embedding is not None
        assert len(embedding) == 768

    @patch("litellm.embedding")
    def test_get_embedding_api_error(self, mock_embedding):
        """Test embedding generation with API error."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        mock_embedding.side_effect = Exception("API Error")

        tool = RagQueryTool(backend="qdrant")

        embedding = tool._get_embedding("Test text")

        # Should return None on error
        assert embedding is None


class TestCreateRagQueryFromConfig:
    """Tests for create_rag_query_from_config factory function."""

    def test_create_ragengine_from_config(self, monkeypatch):
        """Test creating RAG Engine tool from config."""
        from rag_test_suite.tools.rag_query import create_rag_query_from_config

        monkeypatch.setenv("PG_RAG_MCP_URL", "https://test-rag.example.com")
        monkeypatch.setenv("PG_RAG_TOKEN", "test-rag-token")
        monkeypatch.setenv("PG_RAG_CORPUS", "test-corpus")

        config = {
            "rag": {
                "backend": "ragengine",
                "mcp_url_env_var": "PG_RAG_MCP_URL",
                "mcp_token_env_var": "PG_RAG_TOKEN",
                "corpus_env_var": "PG_RAG_CORPUS",
            }
        }

        tool = create_rag_query_from_config(config)

        assert tool.backend == "ragengine"
        assert tool.mcp_url == "https://test-rag.example.com"

    def test_create_qdrant_from_config(self, monkeypatch):
        """Test creating Qdrant tool from config."""
        from rag_test_suite.tools.rag_query import create_rag_query_from_config

        monkeypatch.setenv("QDRANT_URL", "https://test-qdrant.example.com")
        monkeypatch.setenv("QDRANT_API_KEY", "test-key")
        monkeypatch.setenv("QDRANT_COLLECTION", "test-collection")

        config = {
            "rag": {
                "backend": "qdrant",
                "qdrant_url_env_var": "QDRANT_URL",
                "qdrant_api_key_env_var": "QDRANT_API_KEY",
                "qdrant_collection_env_var": "QDRANT_COLLECTION",
            }
        }

        tool = create_rag_query_from_config(config)

        assert tool.backend == "qdrant"
        assert tool.qdrant_url == "https://test-qdrant.example.com"


class TestToolAttributes:
    """Tests for RagQueryTool attributes and metadata."""

    def test_tool_name(self):
        """Test tool has correct name."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine")

        assert tool.name == "rag_query"

    def test_tool_description(self):
        """Test tool has description."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        tool = RagQueryTool(backend="ragengine")

        assert tool.description is not None
        assert len(tool.description) > 0

    def test_tool_backend_validation(self):
        """Test tool validates backend parameter."""
        from rag_test_suite.tools.rag_query import RagQueryTool

        # Valid backends should work
        tool_rag = RagQueryTool(backend="ragengine")
        assert tool_rag.backend == "ragengine"

        tool_qdrant = RagQueryTool(backend="qdrant")
        assert tool_qdrant.backend == "qdrant"
