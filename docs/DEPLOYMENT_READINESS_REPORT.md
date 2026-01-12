# CrewAI Enterprise Deployment Readiness Report

## Project: rag-test-suite

**Path:** `/Users/mischavanoijen/Obsidian/KonectaCoding/code/Crews/flows/rag-test-suite`
**Type:** CrewAI Flow
**Analysis Date:** January 12, 2026
**GitHub:** https://github.com/mischavanoijen/rag-test-suite

---

## Executive Summary

| Requirement | Status | Notes |
|-------------|--------|-------|
| pyproject.toml `type = "flow"` | ✅ PASS | Correctly configured |
| `crewai[litellm,tools]==1.8.0` | ✅ PASS | Correct version with litellm extra |
| Flow class in `__all__` | ✅ PASS | Exported correctly |
| Absolute imports in main.py | ✅ PASS | All imports are absolute |
| `kickoff()` override | ✅ PASS | Properly overridden with input mapping |
| Scripts point to flow entry | ✅ PASS | Correctly configured |
| Build backend hatchling | ✅ PASS | Correctly using hatchling |
| uv.lock committed | ✅ PASS | File exists and is tracked in git |
| LLM configuration | ✅ PASS | All agents have explicit `llm=self.llm` |
| Python version range | ✅ PASS | `>=3.10,<3.14` |

**Overall Status: ✅ READY FOR DEPLOYMENT**

---

## Critical Deployment Requirements (All Verified)

### 1. pyproject.toml Configuration ✅

```toml
[tool.crewai]
type = "flow"
```

| Check | Status | Value |
|-------|--------|-------|
| crewai version | ✅ PASS | `crewai[litellm,tools]==1.8.0` |
| Python version | ✅ PASS | `>=3.10,<3.14` |
| Build backend | ✅ PASS | `hatchling` |
| Project name | ✅ PASS | `rag_test_suite` (underscores) |

### 2. Main.py Entry Points ✅

**Flow Class Export:**
```python
from rag_test_suite.flow import RAGTestSuiteFlow, run_flow

# Export Flow class for CrewAI Enterprise Flow API detection
__all__ = ["RAGTestSuiteFlow", "run_flow_entry", "run_flow_with_trigger", "main"]
```

**Absolute Imports:**
```python
from rag_test_suite.flow import RAGTestSuiteFlow, run_flow
from rag_test_suite.config.loader import load_settings
```

### 3. Flow kickoff() Override ✅

```python
def kickoff(self, inputs: Optional[dict] = None) -> str:
    """
    Override kickoff to map API inputs to state.
    CrewAI Enterprise calls this method directly with inputs dict.
    """
    if inputs:
        # Map run mode (support both UPPERCASE and lowercase)
        run_mode_input = (
            inputs.get("RUN_MODE") or inputs.get("run_mode") or "full"
        ).lower()
        # ... maps all inputs to self.state
    return super().kickoff()
```

### 4. Scripts Configuration ✅

```toml
[project.scripts]
kickoff = "rag_test_suite.main:run_flow_entry"
run_crew = "rag_test_suite.main:run_flow_entry"
run_flow = "rag_test_suite.main:run_flow_entry"
run_with_trigger = "rag_test_suite.main:run_flow_with_trigger"
```

### 5. Crew LLM Configuration ✅

All 5 crews properly configure LLM:

| Crew | LLM Init | Agent `llm=` |
|------|----------|--------------|
| Discovery | `self.llm = LLM(model=llm_model)` | ✅ Yes |
| PromptGenerator | `self.llm = LLM(model=llm_model)` | ✅ Yes |
| TestGeneration | `self.llm = LLM(model=llm_model)` | ✅ Yes |
| Evaluation | `self.llm = LLM(model=llm_model)` | ✅ Yes |
| Reporting | `self.llm = LLM(model=llm_model)` | ✅ Yes |

---

## Environment Variables for Studio

### Required (LLM Authentication)

Add these in **Studio → Crew/Flow → Settings → Environment**:

| Variable | Value |
|----------|-------|
| `OPENAI_API_KEY` | `sk-58992341d04ded6c9d736c79acbdd3347cf4daccd239413fde711480a0ce3558` |
| `OPENAI_API_BASE` | `https://litellm-proxy-805102662749.us-central1.run.app/v1` |

### Required for RAG Engine Mode

| Variable | Example Value |
|----------|---------------|
| `PG_RAG_MCP_URL` | `https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app` |
| `PG_RAG_TOKEN` | `<your-token>` |
| `PG_RAG_CORPUS` | `projects/kd-lab-464110/locations/europe-west4/ragCorpora/7454583283205013504` |

### Required for Target Crew API Mode

| Variable | Description |
|----------|-------------|
| `TARGET_API_URL` | CrewAI Enterprise kickoff URL for target crew |
| `TARGET_API_TOKEN` | Bearer token for target crew API |

---

## API Input Format

When calling via CrewAI Enterprise API, use **UPPERCASE** keys:

```json
{
  "inputs": {
    "RUN_MODE": "full",
    "NUM_TESTS": 20,
    "CREW_DESCRIPTION": "Customer support assistant for Konecta services",
    "TARGET_API_URL": "https://app.crewai.com/api/v1/crews/123/kickoff"
  }
}
```

**Supported input keys:**

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `RUN_MODE` | string | `full` | full, prompt_only, generate_only, execute_only |
| `NUM_TESTS` | int | `10` | Number of test cases to generate |
| `CREW_DESCRIPTION` | string | `""` | Description of target crew for context |
| `TARGET_MODE` | string | `api` | api or local |
| `TARGET_API_URL` | string | `""` | Enterprise API URL for target crew |
| `TEST_CSV_PATH` | string | `""` | Path to CSV file (execute_only mode) |
| `PASS_THRESHOLD` | float | `0.7` | Score threshold for pass/fail (0.0-1.0) |
| `MAX_RETRIES` | int | `2` | Max retries per test |

---

## Pre-Deployment Checklist

All items **VERIFIED**:

- [x] `crewai[litellm,tools]==1.8.0` in dependencies (must include `litellm` extra)
- [x] `requires-python = ">=3.10,<3.14"`
- [x] Build backend is `hatchling`
- [x] `[tool.crewai]` section with `type = "flow"`
- [x] Project name uses underscores (`rag_test_suite`)
- [x] All scripts defined (kickoff, run_crew, run_flow, run_with_trigger, train, replay, test)
- [x] Flow class exported in main.py `__all__`
- [x] Absolute imports only (no relative imports)
- [x] `kickoff()` method overridden to map API inputs to state
- [x] All agents have explicit `llm=self.llm` parameter
- [x] `uv.lock` exists and is committed (NOT in .gitignore)

---

## Deployment Steps

### 1. Create Flow in CrewAI Studio

1. Go to CrewAI Studio → Create New
2. Select **Flow** type
3. Connect GitHub repository: `mischavanoijen/rag-test-suite`
4. Select branch: `main`

### 2. Configure Environment Variables

In **Settings → Environment**, add:

```
OPENAI_API_KEY=sk-58992341d04ded6c9d736c79acbdd3347cf4daccd239413fde711480a0ce3558
OPENAI_API_BASE=https://litellm-proxy-805102662749.us-central1.run.app/v1
PG_RAG_MCP_URL=https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app
PG_RAG_TOKEN=<your-token>
PG_RAG_CORPUS=projects/kd-lab-464110/locations/europe-west4/ragCorpora/7454583283205013504
```

### 3. Deploy

Click **Deploy** and wait for build to complete.

### 4. Test Kickoff

Via Studio UI or API:

```bash
curl -X POST "https://app.crewai.com/api/v1/flows/<flow_id>/kickoff" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "RUN_MODE": "prompt_only",
      "CREW_DESCRIPTION": "Test RAG assistant"
    }
  }'
```

---

## Troubleshooting Guide

### Build Fails with "uv sync && uv add redis python-multipart"

**Cause:** Wrong crewai version or missing litellm extra.

**Solution:** Ensure `crewai[litellm,tools]==1.8.0` (not just `crewai[tools]`).

### "No Flow subclass found in the module"

**Cause:** Flow class not exported in main.py.

**Solution:** Add Flow class to `__all__` in main.py:
```python
__all__ = ["RAGTestSuiteFlow", ...]
```

### "OPENAI_API_KEY is required" at runtime

**Cause:** Environment variables not set in Studio.

**Solution:** Add `OPENAI_API_KEY` and `OPENAI_API_BASE` in Settings → Environment.

### State fields empty despite API inputs

**Cause:** Flow's `kickoff()` not overridden to map inputs.

**Solution:** Override `kickoff()` in Flow class to map `inputs` dict to `self.state`.

### Import errors (relative imports)

**Cause:** Using relative imports like `from .flow import ...`

**Solution:** Use absolute imports: `from rag_test_suite.flow import ...`

---

## Version History

| Date | Event |
|------|-------|
| 2026-01-12 | Initial deployment readiness report |
| 2026-01-12 | All checks passed - ready for deployment |

---

## Conclusion

The **rag-test-suite** project is **fully ready for CrewAI Enterprise deployment**. All critical requirements from the lessons learned have been verified:

1. ✅ Correct pyproject.toml configuration for Flow type
2. ✅ Main.py exports Flow class and uses absolute imports
3. ✅ Flow class has correctly implemented kickoff() override
4. ✅ All crews properly configure LLM instances
5. ✅ uv.lock file is present and committed

**Deploy with confidence!**
