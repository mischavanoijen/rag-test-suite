"""Pydantic models for the CrewAI Test Suite."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class RunMode(str, Enum):
    """Execution modes for the test suite flow."""

    FULL = "full"  # Run all phases: discovery → prompts → tests → execute → report
    PROMPT_ONLY = "prompt_only"  # Run only: discovery → prompt suggestions
    GENERATE_ONLY = "generate_only"  # Run only: discovery → prompts → test generation (no execution)
    EXECUTE_ONLY = "execute_only"  # Run only: execute tests from CSV → evaluate → report
    GENERATE_AND_EXECUTE = "generate_and_execute"  # Default: discovery → prompts → tests → execute → report


class TestCategory(str, Enum):
    """Categories of test cases."""

    FACTUAL = "factual"
    REASONING = "reasoning"
    EDGE_CASE = "edge_case"
    OUT_OF_SCOPE = "out_of_scope"
    AMBIGUOUS = "ambiguous"


class TestDifficulty(str, Enum):
    """Difficulty levels for test cases."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TestCase(BaseModel):
    """A single test case generated from RAG discovery."""

    id: str = Field(description="Unique identifier for the test case")
    question: str = Field(description="The exact query to send to the crew")
    expected_answer: str = Field(description="The ideal response based on RAG content")
    category: TestCategory = Field(description="Category of the test")
    difficulty: TestDifficulty = Field(description="Difficulty level")
    rationale: str = Field(description="Why this tests an important capability")


class TestResult(BaseModel):
    """Result of executing a single test."""

    test_case: TestCase = Field(description="The test case that was executed")
    actual_answer: str = Field(description="The crew's actual response")
    passed: bool = Field(description="Whether the test passed")
    similarity_score: float = Field(
        ge=0.0, le=1.0, description="Similarity score between expected and actual"
    )
    evaluation_rationale: str = Field(description="Explanation of the evaluation")
    retry_count: int = Field(default=0, description="Number of retries attempted")
    execution_time_ms: int = Field(default=0, description="Execution time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class RagDomain(BaseModel):
    """A knowledge domain discovered in the RAG system."""

    name: str = Field(description="Topic name")
    subtopics: list[str] = Field(default_factory=list, description="List of subtopics")
    depth: str = Field(description="Coverage depth: high/medium/low")
    example_queries: list[str] = Field(
        default_factory=list, description="Example queries for this domain"
    )
    sample_facts: list[str] = Field(
        default_factory=list, description="Sample facts from this domain"
    )


class RagSummary(BaseModel):
    """Summary of the RAG system's knowledge base."""

    domains: list[RagDomain] = Field(default_factory=list, description="Discovered domains")
    boundaries: list[str] = Field(
        default_factory=list, description="Topics NOT covered"
    )
    total_coverage_estimate: str = Field(
        default="", description="Brief description of coverage"
    )


class CategoryScore(BaseModel):
    """Score breakdown for a test category."""

    category: TestCategory
    total: int = 0
    passed: int = 0
    pass_rate: float = 0.0
    common_issues: list[str] = Field(default_factory=list)


class AgentSuggestion(BaseModel):
    """Suggested configuration for a CrewAI agent."""

    role: str = Field(description="Suggested agent role name")
    goal: str = Field(description="Suggested agent goal")
    backstory: str = Field(description="Suggested agent backstory")
    tools: list[str] = Field(default_factory=list, description="Recommended tools")
    expertise_areas: list[str] = Field(default_factory=list, description="Areas of expertise")


class TaskSuggestion(BaseModel):
    """Suggested configuration for a CrewAI task."""

    name: str = Field(description="Task name")
    description: str = Field(description="Task description")
    expected_output: str = Field(description="What the task should produce")


class PromptSuggestions(BaseModel):
    """Generated prompt and configuration suggestions based on RAG analysis."""

    # Agent configuration
    primary_agent: AgentSuggestion = Field(
        default_factory=lambda: AgentSuggestion(role="", goal="", backstory=""),
        description="Primary agent suggestion"
    )
    supporting_agents: list[AgentSuggestion] = Field(
        default_factory=list,
        description="Optional supporting agent suggestions"
    )

    # Task configuration
    suggested_tasks: list[TaskSuggestion] = Field(
        default_factory=list,
        description="Suggested task configurations"
    )

    # System prompt
    system_prompt: str = Field(
        default="",
        description="Suggested system prompt for the crew"
    )

    # Use cases and examples
    example_queries: list[str] = Field(
        default_factory=list,
        description="Example queries the crew should handle well"
    )
    out_of_scope_examples: list[str] = Field(
        default_factory=list,
        description="Example queries the crew should politely decline"
    )

    # Knowledge boundaries
    knowledge_summary: str = Field(
        default="",
        description="Summary of what the crew knows"
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known limitations to communicate"
    )

    # Tone and style
    suggested_tone: str = Field(
        default="professional",
        description="Suggested response tone"
    )
    response_format_guidance: str = Field(
        default="",
        description="Guidance on response formatting"
    )


class TestSuiteState(BaseModel):
    """Flow state - persists across all phases."""

    # Run mode configuration
    run_mode: str = Field(
        default="full",
        description="Execution mode: full, prompt_only, generate_only, execute_only, generate_and_execute"
    )
    test_csv_path: str = Field(
        default="",
        description="Path to CSV file with test cases (for execute_only mode)"
    )

    # Configuration
    target_mode: str = Field(default="api", description="Testing mode: 'api' or 'local'")
    target_api_url: str = Field(default="", description="CrewAI Enterprise API URL")
    target_crew_path: str = Field(default="", description="Path to crew for local testing")
    rag_endpoint: str = Field(default="", description="RAG endpoint URL")
    rag_backend: str = Field(default="ragengine", description="RAG backend type")
    num_tests: int = Field(default=20, description="Number of tests to generate")
    pass_threshold: float = Field(default=0.7, description="Pass/fail threshold")
    max_retries: int = Field(default=2, description="Max retries per test")
    crew_description: str = Field(default="", description="What the crew should do")

    # Phase 1 outputs
    rag_summary: Optional[RagSummary] = Field(default=None, description="Discovered RAG summary")
    prompt_suggestions: Optional[PromptSuggestions] = Field(
        default=None, description="Generated prompt/agent suggestions"
    )
    test_cases: list[TestCase] = Field(default_factory=list, description="Generated test cases")

    # Phase 2 state
    current_test_index: int = Field(default=0, description="Current test being executed")
    results: list[TestResult] = Field(default_factory=list, description="Test results")

    # Phase 3 outputs
    pass_rate: float = Field(default=0.0, description="Overall pass rate")
    category_scores: list[CategoryScore] = Field(
        default_factory=list, description="Scores by category"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    quality_report: str = Field(default="", description="Final quality report")
