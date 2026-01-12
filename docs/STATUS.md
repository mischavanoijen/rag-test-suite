# CrewAI Test Suite — Project Status

*Last Updated: January 12, 2026 (15:30 UTC)*

---

## Executive Summary

The **rag-test-suite** is a CrewAI Flow that automatically tests RAG-based chat crews. The implementation is **COMPLETE** and **INTEGRATION TESTED** — all core components are built, 145/145 unit tests pass, and the test suite has been validated against a live RAG Engine MCP (Market Intelligence corpus).

### Recent Updates
- ✅ **Integration tested** against live MI RAG Engine MCP
- ✅ **Discovery mode** successfully mapped RAG knowledge domains
- ✅ **Test generation** created high-quality test cases from real RAG content
- Regenerated `uv.lock` for deployment
- Added comprehensive README.md and integration test plan
- Created integration test scripts

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Project Scaffold** | ✅ Complete | Standard CrewAI Flow structure with pyproject.toml |
| **Models & State** | ✅ Complete | Pydantic models for all data structures |
| **Configuration Loader** | ✅ Complete | YAML config with environment variable overrides |
| **Discovery Crew** | ✅ Complete | Queries RAG to map knowledge domains |
| **Prompt Generator Crew** | ✅ Complete | Generates agent/prompt suggestions from RAG data |
| **Test Generation Crew** | ✅ Complete | Creates test cases with expected answers |
| **Execution Flow** | ✅ Complete | Multi-mode flow with CSV import support |
| **Evaluation Crew** | ✅ Complete | Analyzes results and patterns |
| **Reporting Crew** | ✅ Complete | Generates markdown quality reports |
| **RagQueryTool** | ✅ Complete | RAG Engine MCP + Qdrant backends |
| **CrewRunnerTool** | ✅ Complete | API mode (Enterprise) + Local mode |
| **EvaluatorTool** | ✅ Complete | LLM-as-judge evaluation |
| **Unit Tests** | ✅ Complete | 145 tests, all passing |
| **Integration Testing** | ✅ Complete | Tested with MI RAG Engine MCP |
| **CrewAI Enterprise Deploy** | 🔄 Pending | Ready for deployment |

---

## Run Modes

The test suite supports multiple execution modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `full` | Discovery → Prompts → Tests → Execute → Report | Complete test cycle |
| `prompt_only` | Discovery → Prompt suggestions only | Get agent configuration recommendations |
| `generate_only` | Discovery → Prompts → Test cases (no execution) | Create test cases without running them |
| `execute_only` | Load tests from CSV → Execute → Report | Re-run specific test sets |
| `generate_and_execute` | Same as `full` | Default behavior |

---

## Key Files

```
rag-test-suite/
├── README.md                  # Usage documentation
├── pyproject.toml             # Project configuration
├── uv.lock                    # Dependency lock file
├── .env.example               # Environment variable template
├── examples/
│   └── sample_tests.csv       # Example test cases
└── src/rag_test_suite/
├── flow.py                    # Main Flow orchestration (RAGTestSuiteFlow)
├── main.py                    # CLI entry point + CrewAI Enterprise endpoints
├── models.py                  # Pydantic models (TestCase, TestResult, etc.)
├── config/
│   ├── loader.py              # YAML config loader with env overrides
│   └── settings.yaml          # Default configuration
├── crews/
│   ├── discovery/             # RAG knowledge discovery
│   ├── prompt_generator/      # Agent/prompt suggestions
│   ├── test_generation/       # Test case creation
│   ├── evaluation/            # Result analysis
│   └── reporting/             # Report generation
└── tools/
    ├── rag_query.py           # RAG query tool (MCP + Qdrant)
    ├── crew_runner.py         # Target crew execution (API + local)
    └── evaluator.py           # LLM-as-judge evaluation
```

---

## Environment Variables

### Required for RAG Engine (MCP)

| Variable | Description |
|----------|-------------|
| `PG_RAG_MCP_URL` | RAG Engine MCP server URL |
| `PG_RAG_TOKEN` | Bearer token for MCP authentication |
| `PG_RAG_CORPUS` | Corpus name/path for RAG queries |

### Required for Target Crew (API Mode)

| Variable | Description |
|----------|-------------|
| `TARGET_API_URL` | CrewAI Enterprise kickoff URL |
| `TARGET_API_TOKEN` | Bearer token for Enterprise API |

### Required for LLM

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | API key for LiteLLM proxy |
| `OPENAI_API_BASE` | LiteLLM proxy base URL |

---

## Usage Examples

### CLI Usage

```bash
# Generate prompt suggestions only
python -m rag_test_suite.main --run-mode prompt_only

# Generate test cases without executing
python -m rag_test_suite.main --run-mode generate_only --num-tests 10

# Execute tests from CSV file
python -m rag_test_suite.main --run-mode execute_only --test-csv tests.csv

# Full test run with API target
python -m rag_test_suite.main \
  --run-mode full \
  --target-api-url https://app.crewai.com/api/v1/crews/123/kickoff \
  --crew-description "Customer support assistant"
```

### Programmatic Usage

```python
from rag_test_suite.flow import run_flow

result = run_flow(
    target_api_url="https://app.crewai.com/api/v1/crews/123/kickoff",
    num_tests=20,
    crew_description="Customer support assistant for retail queries",
    run_mode="full",
)
```

---

## Test Results

```
$ python -m pytest tests/ -v
============================= 145 passed in 1.72s =============================
```

All tests passing:
- Configuration loader tests
- Model validation tests
- Tool unit tests (RagQueryTool, CrewRunnerTool, EvaluatorTool)
- Crew initialization tests (Discovery, TestGeneration, Evaluation, Reporting, PromptGenerator)
- Flow state and routing tests

---

## Integration Test Results

### Test Environment

- **RAG Backend:** MI RAG Engine MCP (`https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app`)
- **Corpus:** Market Intelligence documents (Gartner, Everest Group, TBR reports)
- **Date:** January 12, 2026

### Phase 1: RAG Connectivity ✅

```
✓ MCP URL: https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app
✓ Connection established
✓ Query returned results with relevance scores
```

Sample query "What is BPO?" returned relevant results from IT Services and Customer Experience documents.

### Phase 2: Discovery Mode (prompt_only) ✅

The Discovery Crew successfully:
- Mapped knowledge domains: CXM, Data & AI, Competitive Insights, Digital Solutions, BFSI
- Generated agent configuration: "Customer Experience & Support Strategist"
- Created system prompt with proper boundaries
- Identified out-of-scope examples (Ancient Roman history, etc.)

### Phase 3: Test Generation (generate_only) ✅

Generated 5 high-quality test cases:

| ID | Category | Difficulty | Question Preview |
|----|----------|------------|------------------|
| TEST-001 | factual | easy | "What is the definition of composable customer service?" |
| TEST-002 | reasoning | medium | "How might Generative AI capabilities influence CXM by 2028?" |
| TEST-003 | out_of_scope | hard | "Explain the historical significance of the Roman Empire..." |
| TEST-004 | ambiguous | medium | "What are the key competitive factors in the market..." |
| TEST-005 | reasoning | medium | "How are Cloud and Data & AI driving business success..." |

All test cases include expected answers derived from RAG content.

### Phase 4: Execution ⏸️ Pending

Requires a deployed target crew (e.g., simple-rag with MI RAG configuration). See `docs/INTEGRATION_TEST_PLAN.md` for setup instructions.

---

## Next Steps

### Immediate (Complete Execution Testing)

1. **Deploy simple-rag** — Configure with MI RAG credentials
2. **Run execute_only mode** — Test with generated CSV
3. **Run full mode** — Complete end-to-end test cycle
4. **Validate reports** — Review generated quality reports

### Deployment (CrewAI Enterprise)

1. **Push to GitHub** — Commit all changes (lock file already regenerated)
2. **Create flow in Studio** — Link GitHub repo to CrewAI Enterprise
3. **Configure environment** — Add required env vars in Studio Settings
4. **Test kickoff** — Trigger via API or Studio UI

### Enhancements (Future)

1. **Parallel test execution** — Speed up large test suites
2. **HTML report output** — Alternative to markdown for web viewing
3. **Regression tracking** — Compare results across runs
4. **Custom evaluators** — Domain-specific evaluation criteria
5. **Multi-turn conversation tests** — Test conversation flow with session IDs

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     RAGTestSuiteFlow                        │
├─────────────────────────────────────────────────────────────┤
│ @start()                                                    │
│ └─> route_by_mode                                           │
│     ├─> "execute_only" → load_from_csv                      │
│     └─> others → discover                                   │
├─────────────────────────────────────────────────────────────┤
│ Phase 1: Discovery & Generation                             │
│ ├─> discover_rag_data (DiscoveryCrew + RagQueryTool)        │
│ ├─> generate_prompt_suggestions (PromptGeneratorCrew)       │
│ ├─> check_prompt_only_exit                                  │
│ ├─> generate_test_cases (TestGenerationCrew)                │
│ └─> check_generate_only_exit                                │
├─────────────────────────────────────────────────────────────┤
│ Phase 2: Execution                                          │
│ └─> execute_tests / execute_csv_tests (CrewRunnerTool +     │
│                                        EvaluatorTool)       │
├─────────────────────────────────────────────────────────────┤
│ Phase 3: Evaluation & Reporting                             │
│ ├─> evaluate_results (EvaluationCrew)                       │
│ └─> generate_report (ReportingCrew)                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Known Issues

None currently. All unit tests pass. Integration testing validated Discovery and Test Generation phases. Execution phase requires a deployed target crew.

---

## Dependencies

```toml
[project]
requires-python = ">=3.10,<3.14"
dependencies = [
    "crewai[litellm,tools]==1.8.0",
    "python-dotenv>=1.0.0",
    "requests>=2.28.0",
    "pyyaml>=6.0.0",
    "pydantic>=2.0.0",
]
```

---

## Maintainers

- **Konecta Technology Incubation Center**
- Contact: tech@konecta.com
