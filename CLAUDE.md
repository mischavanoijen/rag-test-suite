# CrewAI Test Suite — Project Context

## Purpose

Automated testing framework for RAG-based CrewAI chat crews. This is a **CrewAI Flow** (not a Crew) that tests crews like `simple-rag` by:

1. **Discovering** the RAG knowledge base and generating test cases
2. **Executing** tests against the target crew
3. **Evaluating** responses and generating quality reports

## Current Status

**Implementation: COMPLETE** — All core components built, 145/145 unit tests passing.

**Next Step:** Integration testing against a live RAG system.

See `docs/STATUS.md` for detailed status and next steps.

## Architecture Decision

**Why a Flow, not a Crew:**
- Multiple phases with dependencies
- State persistence across test iterations
- Conditional branching for retry logic
- Loop execution for batch testing

## Run Modes

| Mode | Description |
|------|-------------|
| `full` | Discovery → Prompts → Tests → Execute → Report |
| `prompt_only` | Discovery → Prompt suggestions only |
| `generate_only` | Discovery → Prompts → Tests (no execution) |
| `execute_only` | Load tests from CSV → Execute → Report |

## Target Crew Interface

For **local mode**, the target crew must expose a `run()` function:

```python
def run(inputs: dict) -> str:
    """
    Args:
        inputs: {"query": str, "session_id": str (optional)}
    Returns:
        Answer string
    """
```

For **API mode**, uses CrewAI Enterprise kickoff endpoint.

## Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| Main Flow | `src/crewai_test_suite/flow.py` | Orchestrates phases |
| Discovery Crew | `src/.../crews/discovery/` | Maps RAG knowledge |
| Prompt Generator | `src/.../crews/prompt_generator/` | Suggests agent configs |
| Test Gen Crew | `src/.../crews/test_generation/` | Creates test cases |
| Evaluation Crew | `src/.../crews/evaluation/` | Analyzes results |
| Reporting Crew | `src/.../crews/reporting/` | Generates reports |

## Configuration

Settings file: `src/crewai_test_suite/config/settings.yaml`

Key settings:
- `target.mode` — `api` or `local`
- `rag.backend` — `ragengine` or `qdrant`
- `test_generation.num_tests` — Number of tests to generate
- `evaluation.pass_threshold` — Score threshold for pass/fail

## Tools

| Tool | Purpose |
|------|---------|
| `RagQueryTool` | Query target RAG for discovery (MCP + Qdrant) |
| `CrewRunnerTool` | Execute target crew (API + local modes) |
| `EvaluatorTool` | LLM-as-judge for response evaluation |

## Implementation Status

- [x] Project scaffold
- [x] Models and state definition
- [x] Configuration loader with env overrides
- [x] Discovery Crew
- [x] Prompt Generator Crew
- [x] Test Generation Crew
- [x] Execution Flow loop
- [x] Evaluation Crew
- [x] Reporting Crew
- [x] Unit tests (145 passing)
- [ ] Integration testing with live RAG
- [ ] CrewAI Enterprise deployment

## Environment Variables

### RAG Engine (MCP)
- `PG_RAG_MCP_URL` — MCP server URL
- `PG_RAG_TOKEN` — Bearer token
- `PG_RAG_CORPUS` — Corpus name

### Target Crew (API Mode)
- `TARGET_API_URL` — Enterprise kickoff URL
- `TARGET_API_TOKEN` — Bearer token

### LLM
- `OPENAI_API_KEY` — LiteLLM proxy key
- `OPENAI_API_BASE` — LiteLLM proxy URL

## Usage

```bash
# Generate prompt suggestions only
python -m crewai_test_suite.main --run-mode prompt_only

# Generate tests without executing
python -m crewai_test_suite.main --run-mode generate_only --num-tests 10

# Execute tests from CSV
python -m crewai_test_suite.main --run-mode execute_only --test-csv tests.csv

# Full test run with API target
python -m crewai_test_suite.main \
  --run-mode full \
  --target-api-url https://app.crewai.com/api/v1/crews/123/kickoff \
  --crew-description "Customer support assistant"
```

## Related Documents

- Implementation plan: `docs/implementation-plan.md`
- Project status: `docs/STATUS.md`
- Architecture diagram: `diagrams/test-suite-architecture.png`
