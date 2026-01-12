# CrewAI Test Suite - Deep Dive Code Review & Improvement Plan

**Date:** January 2026
**Status:** In Progress
**Target:** 100% unit tested, maintainable, CrewAI Enterprise compliant code

---

## Executive Summary

This plan outlines a comprehensive review and improvement of the `crewai-test-suite` project to ensure:
1. **Complete Unit Test Coverage** (currently 42%, target 80%+)
2. **CrewAI Enterprise Compliance** (verified ✅)
3. **Code Maintainability** (refactoring needed)
4. **Production Readiness**

---

## Current State Analysis

### Test Coverage Report

| Module | Coverage | Status | Priority |
|--------|----------|--------|----------|
| `models.py` | 100% | ✅ Complete | - |
| `config/loader.py` | 89% | ⚠️ Near Complete | P2 |
| `config/__init__.py` | 100% | ✅ Complete | - |
| `tools/__init__.py` | 100% | ✅ Complete | - |
| `tools/evaluator.py` | 62% | ⚠️ Needs Work | P1 |
| `tools/crew_runner.py` | 47% | ❌ Critical Gap | P1 |
| `tools/rag_query.py` | 25% | ❌ Critical Gap | P1 |
| `crews/evaluation/crew.py` | 80% | ⚠️ Near Complete | P2 |
| `crews/test_generation/crew.py` | 76% | ⚠️ Near Complete | P2 |
| `crews/discovery/crew.py` | 30% | ❌ Critical Gap | P1 |
| `crews/reporting/crew.py` | 25% | ❌ Critical Gap | P1 |
| `crews/prompt_generator/crew.py` | 0% | ❌ No Tests | P1 |
| `flow.py` | 0% | ❌ No Tests | P1 |
| `main.py` | 0% | ❌ No Tests | P1 |
| **TOTAL** | **42%** | ❌ Below Target | - |

### CrewAI Enterprise Compliance

| Requirement | Status |
|-------------|--------|
| `crewai[litellm,tools]==1.8.0` | ✅ Compliant |
| `requires-python = ">=3.10,<3.14"` | ✅ Compliant |
| Build backend = `hatchling` | ✅ Compliant |
| `[tool.crewai] type = "flow"` | ✅ Compliant |
| Project name with underscores | ✅ Compliant |
| All scripts defined | ✅ Compliant |
| No redis/python-multipart | ✅ Compliant |
| No google-cloud packages | ✅ Compliant |
| kickoff() override | ✅ Compliant |
| Absolute imports only | ✅ Compliant |
| Flow class exported | ✅ Compliant |
| uv.lock committed | ✅ Compliant |

### Code Quality Issues

1. **Pytest Collection Warnings** - Model classes named `TestCase`, `TestResult` etc. conflict with pytest
2. **Test Return Warning** - `test_rag_connectivity.py` returns value instead of using assert
3. **Missing .env.example** - File exists but may need updates
4. **Incomplete Error Handling** - Some tools lack comprehensive error handling
5. **Missing Type Hints** - Some functions lack return type annotations

---

## Improvement Plan

### Phase 1: Critical Test Coverage (Priority 1)

#### 1.1 Test `prompt_generator/crew.py` (0% → 80%+)

**Tests to add:**
```python
# tests/test_prompt_generator.py
class TestPromptGeneratorCrew:
    def test_crew_initialization()
    def test_prompt_engineer_agent_creation()
    def test_generate_prompts_task_creation()
    def test_crew_creation()

class TestParsePromptSuggestions:
    def test_parse_valid_json()
    def test_parse_json_in_markdown()
    def test_parse_invalid_json_returns_none()
    def test_parse_missing_primary_agent()
    def test_parse_with_supporting_agents()
    def test_parse_with_suggested_tasks()

class TestCreateDefaultSuggestions:
    def test_create_defaults_with_valid_rag_summary()
    def test_create_defaults_with_invalid_json()
    def test_create_defaults_with_empty_domains()

class TestRunPromptGenerator:
    def test_run_prompt_generator_success_mocked()
    def test_run_prompt_generator_fallback_on_error()
```

#### 1.2 Test `flow.py` (0% → 80%+)

**Tests to add:**
```python
# tests/test_flow.py
class TestRAGTestSuiteFlow:
    def test_flow_initialization()
    def test_flow_initialization_with_custom_config()
    def test_kickoff_maps_uppercase_inputs()
    def test_kickoff_maps_lowercase_inputs()
    def test_kickoff_with_empty_inputs()
    def test_state_initialization()

class TestFlowPhases:
    def test_discover_rag_data_mocked()
    def test_generate_prompt_suggestions_mocked()
    def test_generate_test_cases_mocked()
    def test_execute_tests_mocked()
    def test_evaluate_results_mocked()
    def test_generate_report_mocked()

class TestRunFlow:
    def test_run_flow_api_mode()
    def test_run_flow_local_mode()
```

#### 1.3 Test `main.py` (0% → 80%+)

**Tests to add:**
```python
# tests/test_main.py
class TestMain:
    def test_main_with_help_flag()
    def test_main_with_required_args()
    def test_main_missing_args()

class TestRunFlowEntry:
    def test_run_flow_entry_parses_env_vars()
    def test_run_flow_entry_uses_defaults()

class TestRunFlowWithTrigger:
    def test_run_flow_with_trigger_calls_entry()
```

#### 1.4 Test `tools/rag_query.py` (25% → 80%+)

**Tests to add:**
```python
# tests/test_rag_query_extended.py
class TestRagEngineQuery:
    def test_query_ragengine_success_mocked()
    def test_query_ragengine_connection_error()
    def test_query_ragengine_invalid_response()
    def test_format_rag_results()

class TestQdrantQuery:
    def test_query_qdrant_success_mocked()
    def test_query_qdrant_connection_error()
    def test_get_embedding_success()
    def test_get_embedding_failure()

class TestSSEParsing:
    def test_parse_sse_events()
    def test_handle_incomplete_sse()
```

#### 1.5 Test `tools/crew_runner.py` (47% → 80%+)

**Tests to add:**
```python
# tests/test_crew_runner_extended.py
class TestLocalModeExecution:
    def test_run_local_success()
    def test_run_local_with_result_markers()
    def test_run_local_import_error()
    def test_run_local_execution_error()
    def test_escape_python_string()

class TestApiModeExecution:
    def test_run_api_sync_response()
    def test_run_api_async_polling()
    def test_run_api_timeout()
    def test_poll_for_result_success()
    def test_poll_for_result_error()
```

#### 1.6 Test `crews/discovery/crew.py` (30% → 80%+)

**Tests to add:**
```python
# tests/test_discovery_extended.py
class TestDiscoveryCrew:
    def test_crew_initialization()
    def test_rag_analyst_agent_creation()
    def test_discover_knowledge_task()

class TestRunDiscovery:
    def test_run_discovery_success_mocked()
    def test_run_discovery_fallback()

class TestCreateFallbackSummary:
    def test_create_fallback_with_description()
    def test_create_fallback_without_description()
```

#### 1.7 Test `crews/reporting/crew.py` (25% → 80%+)

**Tests to add:**
```python
# tests/test_reporting_extended.py
class TestReportingCrew:
    def test_crew_initialization()
    def test_report_writer_agent()

class TestRunReporting:
    def test_run_reporting_success_mocked()
    def test_run_reporting_with_empty_results()

class TestReportFormatting:
    def test_format_category_table()
    def test_format_recommendations()
```

---

### Phase 2: Code Quality Improvements (Priority 2)

#### 2.1 Fix Pytest Collection Warnings

**Problem:** Model classes named `TestCase`, `TestResult` etc. conflict with pytest's test discovery.

**Solution:** Configure pytest to ignore these models.

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = "-v --tb=short"
# Ignore models with Test prefix
collect_ignore = []
filterwarnings = [
    "ignore::pytest.PytestCollectionWarning"
]
```

#### 2.2 Fix test_rag_connectivity Return Warning

**Current code:**
```python
def test_rag_connectivity():
    # ...
    return True  # <- This causes warning
```

**Fixed code:**
```python
def test_rag_connectivity():
    # ...
    assert True  # Use assert instead of return
```

#### 2.3 Add Missing Type Hints

Add return type annotations to all public functions:

```python
# Before
def run_discovery(rag_tool, crew_description, llm_model):
    ...

# After
def run_discovery(
    rag_tool: RagQueryTool,
    crew_description: str,
    llm_model: str
) -> str:
    ...
```

#### 2.4 Improve Error Handling

Add consistent error handling patterns:

```python
# Standard error handling pattern
class ToolError(Exception):
    """Base exception for tool errors."""
    pass

class RagQueryError(ToolError):
    """RAG query specific errors."""
    pass

class CrewExecutionError(ToolError):
    """Crew execution errors."""
    pass
```

---

### Phase 3: Maintainability Improvements (Priority 3)

#### 3.1 Extract Common Test Utilities

Create `tests/conftest.py` with shared fixtures:

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_rag_tool():
    """Mock RAG query tool."""
    tool = Mock()
    tool._run.return_value = '{"domains": [{"name": "Test"}]}'
    return tool

@pytest.fixture
def mock_crew_runner():
    """Mock crew runner tool."""
    tool = Mock()
    tool._run.return_value = "Test response"
    return tool

@pytest.fixture
def mock_evaluator():
    """Mock evaluator tool."""
    tool = Mock()
    tool._run.return_value = '{"passed": true, "score": 0.85, "rationale": "Good"}'
    return tool

@pytest.fixture
def sample_test_case():
    """Sample test case for testing."""
    from crewai_test_suite.models import TestCase, TestCategory, TestDifficulty
    return TestCase(
        id="TEST-001",
        question="What is AI?",
        expected_answer="Artificial Intelligence",
        category=TestCategory.FACTUAL,
        difficulty=TestDifficulty.EASY,
        rationale="Basic test"
    )

@pytest.fixture
def sample_test_result(sample_test_case):
    """Sample test result for testing."""
    from crewai_test_suite.models import TestResult
    return TestResult(
        test_case=sample_test_case,
        actual_answer="AI is artificial intelligence",
        passed=True,
        similarity_score=0.85,
        evaluation_rationale="Good semantic match"
    )

@pytest.fixture
def sample_rag_summary():
    """Sample RAG summary for testing."""
    from crewai_test_suite.models import RagSummary, RagDomain
    return RagSummary(
        domains=[
            RagDomain(name="AI", subtopics=["ML", "DL"]),
            RagDomain(name="Data", subtopics=["Analytics"])
        ],
        total_coverage_estimate="AI and Data topics"
    )
```

#### 3.2 Add Test Markers

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (no external dependencies)",
    "integration: Integration tests (may require external services)",
    "slow: Slow tests (skip with -m 'not slow')",
    "requires_env: Tests requiring environment variables"
]
```

#### 3.3 Documentation Improvements

Add docstrings to all public modules, classes, and functions following Google style:

```python
def run_discovery(
    rag_tool: RagQueryTool,
    crew_description: str,
    llm_model: str
) -> str:
    """Run the discovery crew to analyze RAG knowledge base.

    Args:
        rag_tool: Configured RAG query tool
        crew_description: Description of what the crew does
        llm_model: LLM model identifier (e.g., "openai/gemini-2.5-flash")

    Returns:
        JSON string containing RagSummary structure

    Raises:
        DiscoveryError: If discovery process fails

    Example:
        >>> summary = run_discovery(rag_tool, "Customer support bot", "openai/gemini-2.5-flash")
        >>> data = json.loads(summary)
        >>> print(data["domains"])
    """
```

---

## Implementation Order

### Week 1: Critical Tests

| Day | Task | Target Coverage |
|-----|------|-----------------|
| 1 | Test `prompt_generator/crew.py` | 80%+ |
| 1 | Test `flow.py` | 80%+ |
| 2 | Test `main.py` | 80%+ |
| 2 | Test `tools/rag_query.py` extended | 80%+ |
| 3 | Test `tools/crew_runner.py` extended | 80%+ |
| 3 | Test `crews/discovery/crew.py` extended | 80%+ |
| 4 | Test `crews/reporting/crew.py` extended | 80%+ |
| 4 | Fix pytest warnings | Complete |
| 5 | Integration testing | Complete |

### Week 2: Quality & Maintainability

| Day | Task |
|-----|------|
| 1 | Extract common test utilities to conftest.py |
| 2 | Add type hints throughout |
| 3 | Add comprehensive docstrings |
| 4 | Error handling improvements |
| 5 | Final review and cleanup |

---

## Success Criteria

### Must Have (Blocking Deployment)
- [ ] All 49 existing tests pass
- [ ] Total coverage ≥ 80%
- [ ] No pytest warnings
- [ ] CrewAI Enterprise compliance verified
- [ ] `uv lock` regenerated and committed

### Should Have
- [ ] Type hints on all public APIs
- [ ] Google-style docstrings on all public functions
- [ ] conftest.py with shared fixtures
- [ ] Test markers configured

### Nice to Have
- [ ] Coverage ≥ 90%
- [ ] Full integration test suite
- [ ] Performance benchmarks

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| External API dependencies in tests | Use mocks consistently |
| Async/subprocess complexity | Thorough testing with timeouts |
| LLM response variability | Test with deterministic mocks |
| Config file changes | Test with fixtures, not live files |

---

## Appendix: File Checklist

### Tests to Create/Extend

- [ ] `tests/test_prompt_generator.py` - New file
- [ ] `tests/test_flow.py` - New file
- [ ] `tests/test_main.py` - New file
- [ ] `tests/test_rag_query_extended.py` - New file
- [ ] `tests/test_crew_runner_extended.py` - New file
- [ ] `tests/test_discovery_extended.py` - New file
- [ ] `tests/test_reporting_extended.py` - New file
- [ ] `tests/conftest.py` - New file

### Files to Modify

- [ ] `pyproject.toml` - Add pytest markers, fix warnings
- [ ] `tests/test_rag_connectivity.py` - Fix return warning
- [ ] All source files - Add type hints and docstrings

---

*This plan will be updated as implementation progresses.*
