"""Tool for querying RAG systems (RAG Engine MCP or Qdrant)."""

import json
import os
import threading
from queue import Empty, Queue
from typing import Optional

import requests
from crewai.tools import BaseTool
from pydantic import Field


class RagQueryTool(BaseTool):
    """Query the target RAG system for discovery and testing."""

    name: str = "rag_query"
    description: str = """
    Query the RAG knowledge base to retrieve information.
    Use for exploring what topics are covered and testing retrieval.

    Args:
        query: The question or search query
        num_results: Number of results to return (default: 5)

    Returns:
        Retrieved chunks with sources and relevance scores
    """

    # Configuration
    backend: str = Field(default="ragengine", description="Backend type: 'ragengine' or 'qdrant'")

    # RAG Engine (MCP) settings
    mcp_url: str = Field(default="", description="MCP server URL")
    mcp_token_env_var: str = Field(default="PG_RAG_TOKEN", description="Env var for MCP token")
    corpus: str = Field(default="", description="RAG corpus path")

    # Qdrant settings
    qdrant_url: str = Field(default="", description="Qdrant server URL")
    qdrant_api_key_env_var: str = Field(default="QDRANT_API_KEY", description="Env var for API key")
    collection: str = Field(default="", description="Qdrant collection name")
    embedding_model: str = Field(default="text-embedding-004", description="Embedding model")

    # Common settings
    default_results: int = Field(default=5, description="Default number of results")
    max_results: int = Field(default=10, description="Maximum results allowed")

    def _run(self, query: str, num_results: int = 5) -> str:
        """Execute RAG query."""
        num_results = min(num_results, self.max_results)

        if self.backend == "ragengine":
            return self._query_ragengine(query, num_results)
        elif self.backend == "qdrant":
            return self._query_qdrant(query, num_results)
        else:
            return f"Unknown backend: {self.backend}"

    def _query_ragengine(self, query: str, num_results: int) -> str:
        """Query RAG Engine via MCP SSE transport protocol.

        Uses the same SSE transport pattern as simple-rag:
        1. Connect to /sse endpoint to get session
        2. Use session endpoint for messages
        3. Call query_rag tool
        """
        token = os.environ.get(self.mcp_token_env_var)
        if not token:
            return f"Error: {self.mcp_token_env_var} not set"

        if not self.mcp_url:
            return "Error: mcp_url not configured"

        if not self.corpus:
            return "Error: corpus not configured"

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
        }

        result_queue: Queue = Queue()
        session_endpoint: Optional[str] = None

        def sse_listener():
            """Listen to SSE stream for responses."""
            nonlocal session_endpoint
            try:
                with requests.get(
                    f"{self.mcp_url}/sse",
                    headers=headers,
                    stream=True,
                    timeout=120
                ) as resp:
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if "/messages/" in data_str:
                                session_endpoint = data_str
                                result_queue.put(("endpoint", data_str))
                            else:
                                try:
                                    data = json.loads(data_str)
                                    result_queue.put(("message", data))
                                except json.JSONDecodeError:
                                    result_queue.put(("raw", data_str))
            except Exception as e:
                result_queue.put(("error", str(e)))

        try:
            # Start SSE listener in background thread
            sse_thread = threading.Thread(target=sse_listener, daemon=True)
            sse_thread.start()

            # Wait for session endpoint
            for _ in range(10):
                try:
                    msg_type, msg = result_queue.get(timeout=2)
                    if msg_type == "endpoint":
                        session_endpoint = msg
                        break
                except Empty:
                    pass

            if not session_endpoint:
                return "Error: Failed to establish MCP session"

            messages_url = f"{self.mcp_url}{session_endpoint}"

            # Initialize session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "crewai-test-suite", "version": "0.1.0"},
                },
            }
            requests.post(messages_url, json=init_payload, headers=headers, timeout=30)

            # Wait for initialize response
            for _ in range(5):
                try:
                    msg_type, msg = result_queue.get(timeout=2)
                    if msg_type == "message" and isinstance(msg, dict) and msg.get("id") == 1:
                        break
                except Empty:
                    pass

            # Send initialized notification
            notif_payload = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            requests.post(messages_url, json=notif_payload, headers=headers, timeout=30)

            # Call query_rag tool
            search_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "query_rag",
                    "arguments": {
                        "query": query,
                        "corpus_name": self.corpus,
                        "max_results": num_results,
                    },
                },
            }
            requests.post(messages_url, json=search_payload, headers=headers, timeout=30)

            # Wait for response
            for _ in range(30):
                try:
                    msg_type, msg = result_queue.get(timeout=5)
                    if msg_type == "message" and isinstance(msg, dict) and msg.get("id") == 3:
                        result = msg.get("result", {})
                        if result.get("isError"):
                            error_content = result.get("content", [{}])
                            error_text = error_content[0].get("text", "Unknown error") if error_content else "Unknown error"
                            return f"RAG Error: {error_text}"

                        content = result.get("content", [])
                        for item in content:
                            if item.get("type") == "text":
                                return self._format_rag_results(item.get("text", ""), query)
                        return "No results found"
                except Empty:
                    pass

            return "Error: Search timed out"

        except requests.exceptions.Timeout:
            return "Error: Search timed out"
        except requests.RequestException as e:
            return f"RAG Engine Error: {e}"

    def _format_rag_results(self, raw_result: str, query: str) -> str:
        """Format RAG results for readability.

        Limits content size to prevent LLM context overflow and repetition loops.
        """
        try:
            data = json.loads(raw_result)
            if not data.get("success"):
                return f"RAG Error: {data.get('error', 'Unknown error')}"

            chunks = data.get("chunks", [])
            if not chunks:
                return "No results found"

            formatted = f"## Search Results for: {query}\n\n"
            formatted += f"Found {len(chunks)} relevant results.\n\n"

            # Limit to first 3 chunks and 500 chars per chunk to avoid context overflow
            max_chunks = min(3, len(chunks))
            for chunk in chunks[:max_chunks]:
                rank = chunk.get("rank", "?")
                text = chunk.get("text", "")
                source_uri = chunk.get("source_uri", "Unknown")
                relevance = chunk.get("relevance_score", 0.0)

                # Truncate text to avoid LLM repetition loops
                truncated_text = text[:500] + "..." if len(text) > 500 else text

                formatted += f"### Result {rank}\n"
                formatted += f"**Source:** {source_uri}\n"
                formatted += f"**Relevance:** {relevance:.2f}\n"
                formatted += f"**Content:**\n{truncated_text}\n\n"

            return formatted

        except json.JSONDecodeError:
            # Return raw result if not JSON (truncated to avoid overflow)
            return f"## Search Results\n\n{raw_result[:1000]}"

    def _query_qdrant(self, query: str, num_results: int) -> str:
        """Query Qdrant vector database."""
        api_key = os.environ.get(self.qdrant_api_key_env_var, "")

        if not self.qdrant_url:
            return "Error: qdrant_url not configured"

        if not self.collection:
            return "Error: collection not configured"

        try:
            # Get embedding for query
            embedding = self._get_embedding(query)
            if embedding is None:
                return "Error: Could not generate embedding"

            # Search Qdrant
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["api-key"] = api_key

            search_url = f"{self.qdrant_url}/collections/{self.collection}/points/search"
            payload = {
                "vector": embedding,
                "limit": num_results,
                "with_payload": True,
            }

            resp = requests.post(search_url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Format results
            results = []
            for point in data.get("result", []):
                payload = point.get("payload", {})
                score = point.get("score", 0)
                text = payload.get("text", payload.get("content", ""))
                source = payload.get("source", payload.get("file", ""))

                result = f"[Score: {score:.3f}]"
                if source:
                    result += f" [Source: {source}]"
                result += f"\n{text}"
                results.append(result)

            if results:
                return "\n\n---\n\n".join(results)
            return "No results found"

        except requests.RequestException as e:
            return f"Qdrant Error: {e}"

    def _get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding for text using LiteLLM."""
        try:
            import litellm

            response = litellm.embedding(
                model=f"vertex_ai/{self.embedding_model}",
                input=[text],
            )
            return response.data[0]["embedding"]
        except Exception:
            # Fallback: try OpenAI-compatible endpoint
            try:
                api_key = os.environ.get("OPENAI_API_KEY", "")
                api_base = os.environ.get("OPENAI_API_BASE", "")

                if not api_base:
                    return None

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.embedding_model,
                    "input": text,
                }

                resp = requests.post(
                    f"{api_base}/embeddings", json=payload, headers=headers, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
                return data["data"][0]["embedding"]
            except Exception:
                return None


def create_rag_query_from_config(config: dict) -> RagQueryTool:
    """
    Create a RagQueryTool from configuration dictionary.

    Args:
        config: Configuration dictionary with 'rag' section

    Returns:
        Configured RagQueryTool instance
    """
    rag_config = config.get("rag", {})
    backend = rag_config.get("backend", "ragengine")

    if backend == "ragengine":
        ragengine_config = rag_config.get("ragengine", {})
        mcp_url = os.environ.get(ragengine_config.get("mcp_url_env_var", "PG_RAG_MCP_URL"), "")
        corpus = os.environ.get(ragengine_config.get("corpus_env_var", "PG_RAG_CORPUS"), "")

        return RagQueryTool(
            backend="ragengine",
            mcp_url=mcp_url,
            mcp_token_env_var=ragengine_config.get("token_env_var", "PG_RAG_TOKEN"),
            corpus=corpus,
            default_results=ragengine_config.get("default_results", 5),
            max_results=ragengine_config.get("max_results", 10),
        )
    else:
        qdrant_config = rag_config.get("qdrant", {})
        qdrant_url = os.environ.get(qdrant_config.get("url_env_var", "QDRANT_URL"), "")
        collection = os.environ.get(
            qdrant_config.get("collection_env_var", "QDRANT_COLLECTION"), ""
        )

        return RagQueryTool(
            backend="qdrant",
            qdrant_url=qdrant_url,
            qdrant_api_key_env_var=qdrant_config.get("api_key_env_var", "QDRANT_API_KEY"),
            collection=collection,
            embedding_model=qdrant_config.get("embedding_model", "text-embedding-004"),
            default_results=qdrant_config.get("default_results", 5),
            max_results=qdrant_config.get("max_results", 10),
        )
