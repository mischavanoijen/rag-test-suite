# API-Configurable RAG URL Implementation Plan

## Overview

Enable the RAG Test Suite Flow to receive all RAG configuration dynamically via API inputs, making it a universal testing tool for any RAGengine or Qdrant-based RAG system.

---

## Current State

The flow already supports API inputs via the `kickoff()` method:

**Currently supported inputs:**
| Input | Description |
|-------|-------------|
| `RUN_MODE` | Execution mode (full, prompt_only, etc.) |
| `TARGET_API_URL` | CrewAI crew to test |
| `NUM_TESTS` | Number of tests to generate |
| `CREW_DESCRIPTION` | Description of crew purpose |
| `RAG_ENDPOINT` | RAG endpoint (stored in state but not used) |
| `RAG_BACKEND` | Backend type (stored in state but not used) |

**Problem:** `RAG_ENDPOINT` and `RAG_BACKEND` are stored in state but the `RagQueryTool` is initialized from `settings.yaml` at flow construction time, NOT updated from API inputs.

---

## Implementation Plan

### Phase 1: Extend API Input Parameters

Add new API inputs for complete RAG configuration:

```python
# RAG Engine (MCP) configuration
RAG_BACKEND: str           # "ragengine" or "qdrant"
RAG_MCP_URL: str           # MCP server URL
RAG_MCP_TOKEN: str         # Bearer token for MCP
RAG_CORPUS: str            # Corpus name/path

# Qdrant configuration (alternative backend)
RAG_QDRANT_URL: str        # Qdrant server URL
RAG_QDRANT_API_KEY: str    # Qdrant API key
RAG_QDRANT_COLLECTION: str # Collection name

# Target crew to test
TARGET_API_URL: str        # CrewAI Enterprise kickoff URL
TARGET_API_TOKEN: str      # Bearer token for target crew
```

### Phase 2: Modify `kickoff()` Method

Update `flow.py` to extract RAG configuration from inputs and reconfigure tools:

```python
def kickoff(self, inputs: Optional[dict] = None) -> str:
    if inputs:
        # ... existing input parsing ...

        # RAG configuration
        rag_backend = inputs.get("RAG_BACKEND") or inputs.get("rag_backend") or "ragengine"

        if rag_backend == "ragengine":
            mcp_url = inputs.get("RAG_MCP_URL") or inputs.get("rag_mcp_url") or ""
            mcp_token = inputs.get("RAG_MCP_TOKEN") or inputs.get("rag_mcp_token") or ""
            corpus = inputs.get("RAG_CORPUS") or inputs.get("rag_corpus") or ""

            if mcp_url and corpus:
                # Reconfigure RagQueryTool for RAG Engine
                self.rag_tool = RagQueryTool(
                    backend="ragengine",
                    mcp_url=mcp_url,
                    corpus=corpus,
                )
                # Store token in env for tool to pick up
                if mcp_token:
                    os.environ["PG_RAG_TOKEN"] = mcp_token

        elif rag_backend == "qdrant":
            qdrant_url = inputs.get("RAG_QDRANT_URL") or inputs.get("rag_qdrant_url") or ""
            qdrant_key = inputs.get("RAG_QDRANT_API_KEY") or inputs.get("rag_qdrant_api_key") or ""
            collection = inputs.get("RAG_QDRANT_COLLECTION") or inputs.get("rag_qdrant_collection") or ""

            if qdrant_url and collection:
                # Reconfigure RagQueryTool for Qdrant
                self.rag_tool = RagQueryTool(
                    backend="qdrant",
                    qdrant_url=qdrant_url,
                    collection=collection,
                )
                if qdrant_key:
                    os.environ["QDRANT_API_KEY"] = qdrant_key
```

### Phase 3: Update State Model

Add new fields to `TestSuiteState` for RAG configuration tracking:

```python
class TestSuiteState(BaseModel):
    # ... existing fields ...

    # RAG configuration (new)
    rag_mcp_url: str = Field(default="", description="RAG Engine MCP URL")
    rag_corpus: str = Field(default="", description="RAG corpus name")
    rag_qdrant_url: str = Field(default="", description="Qdrant URL")
    rag_qdrant_collection: str = Field(default="", description="Qdrant collection")
```

### Phase 4: Update main.py Entry Points

Ensure `run_flow_entry()` parses all RAG-related env vars:

```python
def run_flow_entry():
    load_dotenv()

    # ... existing env var parsing ...

    # RAG configuration
    rag_backend = os.environ.get("RAG_BACKEND", "ragengine").strip().lower()
    rag_mcp_url = os.environ.get("RAG_MCP_URL", "").strip()
    rag_mcp_token = os.environ.get("RAG_MCP_TOKEN", "").strip()
    rag_corpus = os.environ.get("RAG_CORPUS", "").strip()
    rag_qdrant_url = os.environ.get("RAG_QDRANT_URL", "").strip()
    rag_qdrant_api_key = os.environ.get("RAG_QDRANT_API_KEY", "").strip()
    rag_qdrant_collection = os.environ.get("RAG_QDRANT_COLLECTION", "").strip()
```

---

## API Usage Examples

### Test a RAG Engine-based System

```bash
curl -X POST https://app.crewai.com/api/v1/flows/{flow_id}/kickoff \
  -H "Authorization: Bearer $CREWAI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "RUN_MODE": "full",
      "RAG_BACKEND": "ragengine",
      "RAG_MCP_URL": "https://my-rag-engine.run.app",
      "RAG_MCP_TOKEN": "my-rag-token",
      "RAG_CORPUS": "my-knowledge-base",
      "TARGET_API_URL": "https://app.crewai.com/api/v1/crews/123/kickoff",
      "TARGET_API_TOKEN": "crew-token",
      "CREW_DESCRIPTION": "Customer support assistant for product documentation",
      "NUM_TESTS": 15
    }
  }'
```

### Test a Qdrant-based System

```bash
curl -X POST https://app.crewai.com/api/v1/flows/{flow_id}/kickoff \
  -H "Authorization: Bearer $CREWAI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "RUN_MODE": "full",
      "RAG_BACKEND": "qdrant",
      "RAG_QDRANT_URL": "https://my-qdrant.cloud.qdrant.io",
      "RAG_QDRANT_API_KEY": "qdrant-api-key",
      "RAG_QDRANT_COLLECTION": "product_docs",
      "TARGET_API_URL": "https://app.crewai.com/api/v1/crews/456/kickoff",
      "CREW_DESCRIPTION": "FAQ bot for e-commerce",
      "NUM_TESTS": 20
    }
  }'
```

### Generate Tests Only (No Execution)

```bash
curl -X POST https://app.crewai.com/api/v1/flows/{flow_id}/kickoff \
  -d '{
    "inputs": {
      "RUN_MODE": "generate_only",
      "RAG_BACKEND": "ragengine",
      "RAG_MCP_URL": "https://my-rag.run.app",
      "RAG_MCP_TOKEN": "token",
      "RAG_CORPUS": "knowledge-base",
      "CREW_DESCRIPTION": "HR policy assistant",
      "NUM_TESTS": 30
    }
  }'
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `src/rag_test_suite/flow.py` | Add RAG input parsing in `kickoff()`, reconfigure `self.rag_tool` |
| `src/rag_test_suite/models.py` | Add RAG URL fields to `TestSuiteState` |
| `src/rag_test_suite/main.py` | Add RAG env vars to `run_flow_entry()` |
| `src/rag_test_suite/tools/rag_query.py` | Minor: ensure tool accepts direct URL values (already supported) |

---

## Security Considerations

1. **Token handling:** Tokens passed via API inputs are set as environment variables temporarily. They should not be logged or persisted to state.

2. **Validation:** Add URL validation to reject malformed endpoints.

3. **Token masking:** In logs/reports, mask tokens (show only last 4 chars).

---

## Testing

1. **Unit tests:** Mock `RagQueryTool` and verify it's reconfigured correctly from inputs
2. **Integration tests:** Test against a live RAG Engine with different configurations
3. **API tests:** Deploy to CrewAI Studio and test API kickoff with various RAG URLs

---

## Implementation Steps

1. [x] Update `TestSuiteState` with new RAG fields
2. [x] Modify `kickoff()` to parse RAG inputs and reconfigure tools
3. [x] Update `run_flow_entry()` for env var parsing
4. [x] Add token masking for logs (via `_mask_url()` helper)
5. [x] Write unit tests (9 tests in `test_flow.py`)
6. [x] Test with real RAG Engine endpoint (see `tests/integration/test_api_rag_configuration.py`)
7. [x] Update documentation (see `docs/STATUS.md`)

---

## Result

After implementation, the RAG Test Suite becomes a **universal testing tool** that can:

- Test ANY RAG Engine MCP server by providing URL + token + corpus
- Test ANY Qdrant vector store by providing URL + API key + collection
- Be triggered via API without modifying code or configuration files
- Support multiple RAG systems from a single deployed flow
