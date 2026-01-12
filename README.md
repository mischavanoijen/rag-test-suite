# RAG Test Suite

Automated testing framework for RAG-based CrewAI chat crews.

---

## Overview

This is a **CrewAI Flow** that automatically tests RAG-based chat crews by:

1. **Discovering** the RAG knowledge base and mapping its domains
2. **Generating** test cases with expected answers
3. **Executing** tests against the target crew
4. **Evaluating** responses using LLM-as-judge
5. **Reporting** with quality metrics and recommendations

## Features

- Multiple run modes for different testing scenarios
- Support for RAG Engine (MCP) and Qdrant backends
- API mode for testing deployed crews via CrewAI Enterprise
- Local mode for testing crews during development
- CSV import/export for test case management
- Comprehensive quality reports with actionable recommendations

---

## Quick Start

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run Tests

```bash
# Generate prompt suggestions (discovery only)
python -m rag_test_suite.main --run-mode prompt_only

# Generate test cases without executing
python -m rag_test_suite.main --run-mode generate_only --num-tests 10

# Execute tests from a CSV file
python -m rag_test_suite.main --run-mode execute_only --test-csv examples/sample_tests.csv

# Full test cycle
python -m rag_test_suite.main --run-mode full --target-api-url https://...
```

---

## Run Modes

| Mode | Description | Requires RAG | Requires Target |
|------|-------------|--------------|-----------------|
| `prompt_only` | Discovery + prompt suggestions | Yes | No |
| `generate_only` | Discovery + prompts + test cases | Yes | No |
| `execute_only` | Load CSV + execute + report | No | Yes |
| `full` | Complete cycle | Yes | Yes |

---

## Configuration

### Environment Variables

```bash
# LLM (Required for all modes)
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://litellm-proxy.../v1

# RAG Engine (Required for discovery modes)
PG_RAG_MCP_URL=https://your-rag-server.run.app
PG_RAG_TOKEN=your-token
PG_RAG_CORPUS=projects/.../ragCorpora/...

# Target Crew (Required for execution modes)
TARGET_API_URL=https://app.crewai.com/api/v1/crews/{id}/kickoff
TARGET_API_TOKEN=your-token
```

### CLI Options

```
--run-mode          Execution mode (default: full)
--target-api-url    CrewAI Enterprise kickoff URL
--target-crew-path  Path to local crew
--num-tests         Number of tests to generate (default: 20)
--crew-description  Description of the target crew
--test-csv          CSV file with test cases (for execute_only)
--output            Output file for report
```

---

## Test Case CSV Format

```csv
id,question,expected_answer,category,difficulty,rationale
TEST-001,What is X?,X is defined as...,factual,easy,Tests basic retrieval
TEST-002,How does Y work?,Y works by...,reasoning,medium,Tests explanation
```

### Categories

- `factual` - Direct knowledge retrieval
- `reasoning` - Multi-hop or inference questions
- `edge_case` - Boundary conditions
- `out_of_scope` - Questions outside the domain
- `ambiguous` - Vague or incomplete queries

### Difficulty Levels

- `easy` - Simple, direct questions
- `medium` - Moderate complexity
- `hard` - Complex, multi-part questions

---

## Architecture

```
RAGTestSuiteFlow
│
├── Phase 1: Discovery & Generation
│   ├── discover_rag_data (DiscoveryCrew)
│   ├── generate_prompt_suggestions (PromptGeneratorCrew)
│   └── generate_test_cases (TestGenerationCrew)
│
├── Phase 2: Execution
│   └── execute_tests (CrewRunnerTool + EvaluatorTool)
│
└── Phase 3: Evaluation & Reporting
    ├── evaluate_results (EvaluationCrew)
    └── generate_report (ReportingCrew)
```

---

## Programmatic Usage

```python
from rag_test_suite.flow import run_flow

result = run_flow(
    target_api_url="https://app.crewai.com/api/v1/crews/123/kickoff",
    num_tests=20,
    crew_description="Customer support assistant",
    run_mode="full",
)
```

---

## Development

### Run Tests

```bash
pytest tests/ -v
```

### Project Structure

```
src/rag_test_suite/
├── flow.py           # Main Flow orchestration
├── main.py           # CLI entry point
├── models.py         # Pydantic models
├── config/           # Configuration
├── crews/            # CrewAI crews
│   ├── discovery/
│   ├── prompt_generator/
│   ├── test_generation/
│   ├── evaluation/
│   └── reporting/
└── tools/            # Custom tools
    ├── rag_query.py
    ├── crew_runner.py
    └── evaluator.py
```

---

## Deployment to CrewAI Enterprise

1. Ensure `uv.lock` is committed
2. Push to GitHub
3. Create Flow in CrewAI Studio
4. Link GitHub repository
5. Add environment variables in Settings
6. Trigger via API or Studio UI

---

## License

Konecta Technology Incubation Center
