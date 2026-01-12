"""Shared pytest fixtures for crewai-test-suite tests."""

import json
import pytest
from unittest.mock import Mock, MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Model Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_test_case():
    """Sample test case for testing."""
    from crewai_test_suite.models import TestCase, TestCategory, TestDifficulty

    return TestCase(
        id="TEST-001",
        question="What is artificial intelligence?",
        expected_answer="AI is the simulation of human intelligence in machines.",
        category=TestCategory.FACTUAL,
        difficulty=TestDifficulty.EASY,
        rationale="Basic knowledge retrieval test",
    )


@pytest.fixture
def sample_test_case_hard():
    """Sample hard test case for testing."""
    from crewai_test_suite.models import TestCase, TestCategory, TestDifficulty

    return TestCase(
        id="TEST-002",
        question="How does transformer architecture enable parallel processing?",
        expected_answer="Transformers use self-attention mechanisms that process all tokens simultaneously.",
        category=TestCategory.REASONING,
        difficulty=TestDifficulty.HARD,
        rationale="Deep technical understanding test",
    )


@pytest.fixture
def sample_test_result(sample_test_case):
    """Sample test result for testing."""
    from crewai_test_suite.models import TestResult

    return TestResult(
        test_case=sample_test_case,
        actual_answer="AI is artificial intelligence, simulating human cognition.",
        passed=True,
        similarity_score=0.85,
        evaluation_rationale="Good semantic match with expected answer.",
        execution_time_ms=1500,
    )


@pytest.fixture
def sample_test_result_failed(sample_test_case_hard):
    """Sample failed test result for testing."""
    from crewai_test_suite.models import TestResult

    return TestResult(
        test_case=sample_test_case_hard,
        actual_answer="I don't know.",
        passed=False,
        similarity_score=0.15,
        evaluation_rationale="Response does not address the question.",
        execution_time_ms=500,
    )


@pytest.fixture
def sample_rag_domain():
    """Sample RAG domain for testing."""
    from crewai_test_suite.models import RagDomain

    return RagDomain(
        name="Artificial Intelligence",
        subtopics=["Machine Learning", "Deep Learning", "NLP"],
        depth="comprehensive",
        example_queries=["What is AI?", "How does ML work?"],
        sample_facts=["AI simulates human intelligence", "ML is a subset of AI"],
    )


@pytest.fixture
def sample_rag_summary(sample_rag_domain):
    """Sample RAG summary for testing."""
    from crewai_test_suite.models import RagSummary, RagDomain

    return RagSummary(
        domains=[
            sample_rag_domain,
            RagDomain(
                name="Data Science",
                subtopics=["Analytics", "Visualization"],
                depth="moderate",
            ),
        ],
        boundaries=["No real-time data", "Limited to knowledge base"],
        total_coverage_estimate="AI and Data Science topics with comprehensive depth",
    )


@pytest.fixture
def sample_category_score():
    """Sample category score for testing."""
    from crewai_test_suite.models import CategoryScore

    return CategoryScore(
        category="factual",
        total=10,
        passed=8,
        pass_rate=0.8,
        common_issues=["Some answers lacked detail"],
    )


@pytest.fixture
def sample_agent_suggestion():
    """Sample agent suggestion for testing."""
    from crewai_test_suite.models import AgentSuggestion

    return AgentSuggestion(
        role="Knowledge Assistant",
        goal="Help users find accurate information from the knowledge base",
        backstory="You are a helpful assistant with expertise in AI and data science.",
        tools=["rag_search", "web_search"],
        expertise_areas=["AI", "Machine Learning", "Data Science"],
    )


@pytest.fixture
def sample_prompt_suggestions(sample_agent_suggestion):
    """Sample prompt suggestions for testing."""
    from crewai_test_suite.models import PromptSuggestions, TaskSuggestion

    return PromptSuggestions(
        primary_agent=sample_agent_suggestion,
        supporting_agents=[],
        suggested_tasks=[
            TaskSuggestion(
                name="answer_query",
                description="Answer user questions",
                expected_output="Clear, accurate response",
            )
        ],
        system_prompt="You are a helpful AI assistant.",
        example_queries=["What is AI?", "How does ML work?"],
        out_of_scope_examples=["What's the weather?", "Tell me a joke"],
        knowledge_summary="AI and Data Science knowledge base",
        limitations=["No real-time data", "Limited to knowledge base"],
        suggested_tone="professional",
        response_format_guidance="Be concise and cite sources.",
    )


@pytest.fixture
def sample_test_suite_state(sample_test_case, sample_test_result, sample_rag_summary):
    """Sample test suite state for testing."""
    from crewai_test_suite.models import TestSuiteState

    state = TestSuiteState(
        target_mode="local",
        target_crew_path="/path/to/crew",
        num_tests=5,
        pass_threshold=0.7,
    )
    state.test_cases = [sample_test_case]
    state.results = [sample_test_result]
    state.rag_summary = sample_rag_summary
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Tool Mocks
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_rag_tool():
    """Mock RAG query tool."""
    tool = Mock()
    tool.backend = "ragengine"
    tool._run.return_value = json.dumps(
        {
            "domains": [{"name": "AI", "subtopics": ["ML", "DL"]}],
            "total_coverage_estimate": "AI topics",
        }
    )
    return tool


@pytest.fixture
def mock_crew_runner():
    """Mock crew runner tool."""
    tool = Mock()
    tool.mode = "local"
    tool._run.return_value = "This is the response from the crew."
    return tool


@pytest.fixture
def mock_evaluator():
    """Mock evaluator tool."""
    tool = Mock()
    tool.pass_threshold = 0.7
    tool._run.return_value = json.dumps(
        {"passed": True, "score": 0.85, "rationale": "Good semantic match"}
    )
    return tool


# ─────────────────────────────────────────────────────────────────────────────
# Configuration Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_config():
    """Sample configuration dictionary for testing."""
    return {
        "project": {"name": "crewai-test-suite", "version": "0.1.0"},
        "target": {
            "mode": "local",
            "crew_path": "/path/to/simple-rag/src",
            "crew_module": "simple_rag.main",
            "api_url_env_var": "TARGET_API_URL",
            "api_token_env_var": "TARGET_API_TOKEN",
        },
        "rag": {
            "backend": "ragengine",
            "mcp_url_env_var": "PG_RAG_MCP_URL",
            "token_env_var": "PG_RAG_TOKEN",
            "corpus_env_var": "PG_RAG_CORPUS",
        },
        "test_generation": {
            "num_tests": 20,
            "categories": ["factual", "reasoning", "edge_case"],
        },
        "evaluation": {"pass_threshold": 0.7, "method": "llm_judge"},
        "llm": {"model": "openai/gemini-2.5-flash", "temperature": 0.1},
    }


@pytest.fixture
def mock_settings_yaml(tmp_path, sample_config):
    """Create a temporary settings.yaml file for testing."""
    import yaml

    settings_file = tmp_path / "settings.yaml"
    with open(settings_file, "w") as f:
        yaml.dump(sample_config, f)
    return settings_file


# ─────────────────────────────────────────────────────────────────────────────
# LLM Response Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_llm_response_json():
    """Mock LLM response with JSON in markdown."""
    return """Based on my analysis, here is the evaluation:

```json
{
    "passed": true,
    "score": 0.85,
    "rationale": "The response accurately answers the question with good semantic match."
}
```

This indicates a passing grade."""


@pytest.fixture
def mock_llm_response_raw_json():
    """Mock LLM response with raw JSON."""
    return '{"passed": true, "score": 0.9, "rationale": "Excellent match"}'


@pytest.fixture
def mock_llm_response_truncated():
    """Mock truncated LLM response."""
    return '{"passed": true, "score": 0.75, "rationale": "Good but incomp'


@pytest.fixture
def mock_rag_summary_json():
    """Mock RAG summary JSON response."""
    return """```json
{
    "domains": [
        {
            "name": "Customer Service",
            "subtopics": ["FAQ", "Support Tickets"],
            "depth": "comprehensive",
            "example_queries": ["How do I reset my password?"],
            "sample_facts": ["Support available 24/7"]
        }
    ],
    "boundaries": ["No financial advice", "No medical information"],
    "total_coverage_estimate": "Customer service and support topics"
}
```"""


@pytest.fixture
def mock_prompt_suggestions_json():
    """Mock prompt suggestions JSON response."""
    return """```json
{
    "primary_agent": {
        "role": "Customer Service Expert",
        "goal": "Help customers resolve issues quickly",
        "backstory": "You are an experienced customer service agent.",
        "tools": ["rag_search", "knowledge_base"],
        "expertise_areas": ["customer service", "technical support"]
    },
    "supporting_agents": [],
    "suggested_tasks": [
        {
            "name": "answer_query",
            "description": "Answer customer questions",
            "expected_output": "Clear and helpful response"
        }
    ],
    "system_prompt": "You are a helpful customer service assistant.",
    "example_queries": ["How do I reset my password?", "What are your hours?"],
    "out_of_scope_examples": ["Tell me a joke", "What's the weather?"],
    "knowledge_summary": "Customer service and support knowledge",
    "limitations": ["Cannot process payments", "No real-time data"],
    "suggested_tone": "professional",
    "response_format_guidance": "Be concise and helpful."
}
```"""


@pytest.fixture
def mock_test_cases_json():
    """Mock test cases JSON response."""
    return """```json
[
    {
        "id": "TC-001",
        "question": "What is AI?",
        "expected_answer": "AI is artificial intelligence.",
        "category": "factual",
        "difficulty": "easy",
        "rationale": "Basic test"
    },
    {
        "id": "TC-002",
        "question": "How does ML differ from DL?",
        "expected_answer": "ML is broader, DL uses neural networks.",
        "category": "reasoning",
        "difficulty": "medium",
        "rationale": "Comparison test"
    }
]
```"""


# ─────────────────────────────────────────────────────────────────────────────
# HTTP/API Mocks
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for API testing."""
    with patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_response.text = '{"result": "success"}'
        mock_response.headers = {"mcp-session-id": "test-session-123"}
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for local crew execution."""
    with patch("subprocess.run") as mock_run:
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "<<<CREW_RESULT_START>>>\nTest response\n<<<CREW_RESULT_END>>>"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        yield mock_run


# ─────────────────────────────────────────────────────────────────────────────
# Environment Variable Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "sk-test-key-12345",
        "OPENAI_API_BASE": "https://test-api.example.com/v1",
        "TARGET_API_URL": "https://app.crewai.com/api/v1/crews/123/kickoff",
        "TARGET_API_TOKEN": "test-api-token",
        "PG_RAG_MCP_URL": "https://test-rag.example.com",
        "PG_RAG_TOKEN": "test-rag-token",
        "PG_RAG_CORPUS": "projects/test/locations/us/ragCorpora/123",
        "QDRANT_URL": "https://test-qdrant.example.com",
        "QDRANT_API_KEY": "test-qdrant-key",
        "QDRANT_COLLECTION": "test-collection",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
