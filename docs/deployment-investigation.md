# RAG Test Suite — Deployment Investigation Report

*Investigation Date: January 12, 2026*

---

## Executive Summary

This report documents the investigation into deployment failures for the RAG Test Suite Flow on CrewAI Enterprise. The investigation leveraged lessons learned from previous deployments and consultation with the CrewAI Flow Expert.

**Key Finding:** The Qdrant embedding method was using `vertex_ai/` prefix which requires Google Cloud credentials not available in CrewAI Enterprise. This has been fixed.

---

## Investigation Checklist

### Compliance with Lessons Learned

| Requirement | Status | Notes |
|-------------|--------|-------|
| `crewai[litellm,tools]==1.8.0` | OK | Correct version in pyproject.toml |
| `requires-python = ">=3.10,<3.14"` | OK | Correctly set |
| Build backend = `hatchling` | OK | Correctly configured |
| `[tool.crewai] type = "flow"` | OK | Correctly set for Flow |
| Project name uses underscores | OK | `rag_test_suite` |
| Flow class exported in `__all__` | OK | `RAGTestSuiteFlow` exported in main.py |
| Absolute imports only | OK | All imports are absolute |
| `kickoff()` override | OK | Maps API inputs to state |
| Scripts include `run_with_trigger` | OK | Present in pyproject.toml |

### Files Reviewed

| File | Location |
|------|----------|
| pyproject.toml | `/code/Crews/flows/rag-test-suite/pyproject.toml` |
| main.py | `src/rag_test_suite/main.py` |
| flow.py | `src/rag_test_suite/flow.py` |
| rag_query.py | `src/rag_test_suite/tools/rag_query.py` |

---

## Issues Found

### Issue 1: Vertex AI Embedding Calls (FIXED)

**Problem:** The `_get_embedding()` method in `RagQueryTool` was attempting direct Vertex AI embedding calls:

```python
# OLD CODE (BROKEN)
response = litellm.embedding(
    model=f"vertex_ai/{self.embedding_model}",  # Requires Google Cloud credentials
    input=[text],
)
```

**Root Cause:** CrewAI Enterprise containers don't have Google Cloud credentials (`GOOGLE_APPLICATION_CREDENTIALS`). The `vertex_ai/` prefix in LiteLLM requires direct access to Google Cloud APIs.

**Solution:** Prioritize LiteLLM proxy endpoint for embeddings:

```python
# NEW CODE (FIXED)
# Prefer LiteLLM proxy (works in CrewAI Enterprise)
if api_base and api_key:
    resp = requests.post(
        f"{api_base}/embeddings", json=payload, headers=headers, timeout=30
    )
    return data["data"][0]["embedding"]

# Fallback: direct litellm (for local development only)
```

**File Changed:** `src/rag_test_suite/tools/rag_query.py` (line 293-340)

### Issue 2: LiteLLM Proxy Must Support Embeddings

**Requirement:** The Konecta LiteLLM proxy at `https://litellm-proxy-805102662749.us-central1.run.app/v1` must be configured to route embedding requests.

**Proxy Configuration Needed:**

```yaml
# litellm_config.yaml
model_list:
  - model_name: text-embedding-004
    litellm_params:
      model: vertex_ai/text-embedding-004
      vertex_project: your-project
      vertex_location: us-central1
```

**Action Required:** Verify the LiteLLM proxy supports embedding endpoints. Test with:

```bash
curl -X POST https://litellm-proxy-805102662749.us-central1.run.app/v1/embeddings \
  -H "Authorization: Bearer sk-58992341d04ded6c9d736c79acbdd3347cf4daccd239413fde711480a0ce3558" \
  -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-004", "input": "test query"}'
```

---

## Flow Deployment Verification

### pyproject.toml Analysis

```toml
[project]
name = "rag_test_suite"  # Underscores - OK
version = "0.1.0"
requires-python = ">=3.10,<3.14"  # Correct range - OK
dependencies = [
    "crewai[litellm,tools]==1.8.0",  # Includes litellm extra - OK
    ...
]

[build-system]
requires = ["hatchling"]  # Correct backend - OK
build-backend = "hatchling.build"

[tool.crewai]
type = "flow"  # Correct type - OK
```

### main.py Analysis

```python
# Exports Flow class - OK
__all__ = ["RAGTestSuiteFlow", "run_flow_entry", "run_flow_with_trigger", "main"]

# Absolute imports - OK
from rag_test_suite.flow import RAGTestSuiteFlow, run_flow
```

### flow.py Analysis

```python
# kickoff() override - OK
def kickoff(self, inputs: Optional[dict] = None) -> str:
    """Override kickoff to map API inputs to state."""
    if inputs:
        # Maps UPPERCASE and lowercase keys
        run_mode_input = (
            inputs.get("RUN_MODE") or inputs.get("run_mode") or "full"
        ).lower()
        ...
    return super().kickoff()
```

---

## Qdrant Client Support

### Current Implementation

The `RagQueryTool` supports Qdrant via **raw HTTP requests** (not the `qdrant-client` library).

| Approach | Pros | Cons |
|----------|------|------|
| HTTP Requests (current) | No extra dependencies, portable | Less type safety |
| qdrant-client library | Rich API, type hints | Adds dependency complexity |

**Recommendation:** Keep HTTP requests for CrewAI Enterprise deployment. The current implementation is correct.

### Qdrant Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Test Suite Flow                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      RagQueryTool                            │
│                                                              │
│  backend = "qdrant"                                          │
│      │                                                       │
│      ▼                                                       │
│  _get_embedding(query)                                       │
│      │                                                       │
│      ▼                                                       │
│  LiteLLM Proxy (OPENAI_API_BASE/embeddings)                  │
│      │                                                       │
│      ▼                                                       │
│  _query_qdrant(query, embedding)                             │
│      │                                                       │
│      ▼                                                       │
│  HTTP POST to Qdrant (RAG_QDRANT_URL)                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Variables for CrewAI Enterprise

### Required in Studio Settings

| Variable | Value | Purpose |
|----------|-------|---------|
| `OPENAI_API_KEY` | `sk-58992341...` | LiteLLM proxy auth |
| `OPENAI_API_BASE` | `https://litellm-proxy...run.app/v1` | LiteLLM proxy URL |

### Passed at Runtime via API Inputs

| Input | Example | Purpose |
|-------|---------|---------|
| `RAG_BACKEND` | `ragengine` or `qdrant` | Backend selector |
| `RAG_MCP_URL` | `https://...` | RAG Engine MCP URL |
| `RAG_MCP_TOKEN` | `token` | RAG Engine auth |
| `RAG_CORPUS` | `corpus-name` | RAG corpus |
| `RAG_QDRANT_URL` | `https://...` | Qdrant URL |
| `RAG_QDRANT_API_KEY` | `key` | Qdrant auth |
| `RAG_QDRANT_COLLECTION` | `collection` | Qdrant collection |

---

## Deployment Debugging Commands

### Check Build Logs

```bash
gcloud container clusters get-credentials crewai-cluster \
  --region europe-west1 \
  --project kn-corp-dgt-svc-crewai-dev

kubectl logs -n default -l app=buildkitd --tail=100
```

### Check Pod Status

```bash
kubectl get pods -n crewai-crews | grep rag-test-suite
kubectl describe pod <pod-name> -n crewai-crews
```

### Check for CrashLoopBackOff

```bash
kubectl logs <pod-name> -n crewai-crews --previous
```

### Test Local Import

```bash
cd /Users/mischavanoijen/Obsidian/KonectaCoding/code/Crews/flows/rag-test-suite
uv run python -c "from rag_test_suite.main import RAGTestSuiteFlow; print('Import OK')"
```

---

## Fixes Applied

| Issue | Fix | File |
|-------|-----|------|
| Vertex AI embedding calls | Prioritize LiteLLM proxy | `src/rag_test_suite/tools/rag_query.py` |

---

## Next Steps

1. **Verify LiteLLM Proxy Embeddings** — Test if the proxy supports `/embeddings` endpoint
2. **Regenerate Lock File** — Run `uv lock` and commit
3. **Push Changes** — Commit the rag_query.py fix
4. **Redeploy** — Trigger new deployment in CrewAI Studio
5. **Test with RAG Engine** — Use RAG Engine backend first (doesn't need embeddings)
6. **Test with Qdrant** — Test Qdrant backend after confirming proxy embeddings

---

## Conclusion

The RAG Test Suite Flow is correctly structured for CrewAI Enterprise deployment. The main issue was the Qdrant embedding method attempting direct Vertex AI calls. This has been fixed to prioritize the LiteLLM proxy.

**Note:** The RAG Engine (MCP) backend does NOT use embeddings — it uses the MCP server's native search. Only Qdrant requires embeddings. If the LiteLLM proxy doesn't support embeddings, use RAG Engine backend only.

---

*Report generated by Claude Code investigation*
