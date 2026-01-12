"""Main Flow orchestration for the CrewAI Test Suite."""

import csv
import json
import os
import time
from typing import Optional

from crewai.flow.flow import Flow, listen, start, router

from rag_test_suite.models import (
    TestCase,
    TestResult,
    TestSuiteState,
    CategoryScore,
    RagSummary,
    PromptSuggestions,
    RunMode,
    TestCategory,
    TestDifficulty,
)
from rag_test_suite.config.loader import load_settings
from rag_test_suite.tools.rag_query import RagQueryTool, create_rag_query_from_config
from rag_test_suite.tools.crew_runner import CrewRunnerTool, create_crew_runner_from_config
from rag_test_suite.tools.evaluator import EvaluatorTool, create_evaluator_from_config
from rag_test_suite.crews.discovery.crew import run_discovery
from rag_test_suite.crews.prompt_generator.crew import run_prompt_generator
from rag_test_suite.crews.test_generation.crew import run_test_generation
from rag_test_suite.crews.evaluation.crew import run_evaluation, calculate_category_scores
from rag_test_suite.crews.reporting.crew import run_reporting


class RAGTestSuiteFlow(Flow[TestSuiteState]):
    """
    Multi-phase test suite for evaluating RAG systems.

    Supports multiple run modes:
    - full: Discovery → Prompts → Test Generation → Execute → Report
    - prompt_only: Discovery → Prompt suggestions only
    - generate_only: Discovery → Prompts → Test Generation (no execution)
    - execute_only: Load tests from CSV → Execute → Report
    - generate_and_execute: Same as full (default)
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the test suite flow.

        Args:
            config: Optional configuration dictionary. If not provided,
                   loads from default settings.yaml
        """
        super().__init__()
        self.config = config or load_settings()

        # Initialize tools from config
        self.rag_tool = create_rag_query_from_config(self.config)
        self.crew_runner = create_crew_runner_from_config(self.config)
        self.evaluator = create_evaluator_from_config(self.config)

        # Get LLM model from config
        self.llm_model = self.config.get("llm", {}).get("model", "openai/gemini-2.5-flash")

    def kickoff(self, inputs: Optional[dict] = None) -> str:
        """
        Override kickoff to map API inputs to state.

        CrewAI Enterprise calls this method directly with inputs dict.

        Supported inputs:
        - RUN_MODE: full, prompt_only, generate_only, execute_only, generate_and_execute
        - TEST_CSV_PATH: Path to CSV file with test cases (for execute_only mode)
        - TARGET_MODE, TARGET_API_URL, TARGET_API_TOKEN, TARGET_CREW_PATH: Target crew config
        - RAG_BACKEND: "ragengine" or "qdrant"
        - RAG_MCP_URL, RAG_MCP_TOKEN, RAG_CORPUS: RAG Engine (MCP) configuration
        - RAG_QDRANT_URL, RAG_QDRANT_API_KEY, RAG_QDRANT_COLLECTION: Qdrant configuration
        - NUM_TESTS, PASS_THRESHOLD, MAX_RETRIES: Test parameters
        - CREW_DESCRIPTION: Description of what the crew does
        """
        if inputs:
            # Map run mode (support both UPPERCASE and lowercase)
            run_mode_input = (
                inputs.get("RUN_MODE") or inputs.get("run_mode") or "full"
            ).lower()

            # Validate run mode
            valid_modes = ["full", "prompt_only", "generate_only", "execute_only", "generate_and_execute"]
            if run_mode_input not in valid_modes:
                print(f"Warning: Invalid RUN_MODE '{run_mode_input}', defaulting to 'full'")
                run_mode_input = "full"
            self.state.run_mode = run_mode_input

            # CSV path for execute_only mode
            self.state.test_csv_path = (
                inputs.get("TEST_CSV_PATH") or inputs.get("test_csv_path") or ""
            )

            # Target crew configuration
            self.state.target_mode = (
                inputs.get("TARGET_MODE") or inputs.get("target_mode") or "api"
            )
            self.state.target_api_url = (
                inputs.get("TARGET_API_URL") or inputs.get("target_api_url") or ""
            )
            target_api_token = (
                inputs.get("TARGET_API_TOKEN") or inputs.get("target_api_token") or ""
            )
            if target_api_token:
                self.state.target_api_token = target_api_token
                os.environ["TARGET_API_TOKEN"] = target_api_token
            self.state.target_crew_path = (
                inputs.get("TARGET_CREW_PATH") or inputs.get("target_crew_path") or ""
            )

            # RAG backend configuration
            rag_backend = (
                inputs.get("RAG_BACKEND") or inputs.get("rag_backend") or "ragengine"
            ).lower()
            self.state.rag_backend = rag_backend

            # RAG Engine (MCP) configuration
            rag_mcp_url = inputs.get("RAG_MCP_URL") or inputs.get("rag_mcp_url") or ""
            rag_mcp_token = inputs.get("RAG_MCP_TOKEN") or inputs.get("rag_mcp_token") or ""
            rag_corpus = inputs.get("RAG_CORPUS") or inputs.get("rag_corpus") or ""

            # Qdrant configuration
            rag_qdrant_url = inputs.get("RAG_QDRANT_URL") or inputs.get("rag_qdrant_url") or ""
            rag_qdrant_api_key = inputs.get("RAG_QDRANT_API_KEY") or inputs.get("rag_qdrant_api_key") or ""
            rag_qdrant_collection = inputs.get("RAG_QDRANT_COLLECTION") or inputs.get("rag_qdrant_collection") or ""

            # Legacy RAG_ENDPOINT support (deprecated)
            rag_endpoint = inputs.get("RAG_ENDPOINT") or inputs.get("rag_endpoint") or ""
            if rag_endpoint and not rag_mcp_url:
                rag_mcp_url = rag_endpoint
            self.state.rag_endpoint = rag_endpoint

            # Store RAG config in state
            self.state.rag_mcp_url = rag_mcp_url
            self.state.rag_corpus = rag_corpus
            self.state.rag_qdrant_url = rag_qdrant_url
            self.state.rag_qdrant_collection = rag_qdrant_collection

            # Reconfigure RAG tool based on API inputs
            if rag_backend == "ragengine" and rag_mcp_url and rag_corpus:
                print(f"Configuring RAG Engine: {self._mask_url(rag_mcp_url)}")
                if rag_mcp_token:
                    os.environ["PG_RAG_TOKEN"] = rag_mcp_token
                self.rag_tool = RagQueryTool(
                    backend="ragengine",
                    mcp_url=rag_mcp_url,
                    corpus=rag_corpus,
                )
            elif rag_backend == "qdrant" and rag_qdrant_url and rag_qdrant_collection:
                print(f"Configuring Qdrant: {self._mask_url(rag_qdrant_url)}")
                if rag_qdrant_api_key:
                    os.environ["QDRANT_API_KEY"] = rag_qdrant_api_key
                self.rag_tool = RagQueryTool(
                    backend="qdrant",
                    qdrant_url=rag_qdrant_url,
                    collection=rag_qdrant_collection,
                )

            # Test parameters
            self.state.num_tests = int(
                inputs.get("NUM_TESTS") or inputs.get("num_tests") or 20
            )
            self.state.pass_threshold = float(
                inputs.get("PASS_THRESHOLD") or inputs.get("pass_threshold") or 0.7
            )
            self.state.max_retries = int(
                inputs.get("MAX_RETRIES") or inputs.get("max_retries") or 2
            )
            self.state.crew_description = (
                inputs.get("CREW_DESCRIPTION") or inputs.get("crew_description") or ""
            )

            # Update crew runner with target config
            if self.state.target_api_url:
                self.crew_runner.api_url = self.state.target_api_url
                self.crew_runner.mode = "api"

        print(f"\n{'=' * 60}")
        print(f"RAG TEST SUITE - Run Mode: {self.state.run_mode.upper()}")
        print(f"RAG Backend: {self.state.rag_backend}")
        if self.state.rag_mcp_url:
            print(f"RAG MCP URL: {self._mask_url(self.state.rag_mcp_url)}")
        if self.state.rag_qdrant_url:
            print(f"Qdrant URL: {self._mask_url(self.state.rag_qdrant_url)}")
        print(f"{'=' * 60}\n")

        # Call parent kickoff
        return super().kickoff()

    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of URL for logging."""
        if not url:
            return ""
        # Show domain but mask path details
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}/..."
        except Exception:
            return url[:30] + "..." if len(url) > 30 else url

    # ─────────────────────────────────────────────────────────────
    # ENTRY POINT WITH ROUTER
    # ─────────────────────────────────────────────────────────────

    @start()
    def route_by_mode(self):
        """Route to appropriate starting point based on run mode."""
        mode = self.state.run_mode.lower()

        if mode == "execute_only":
            # Load test cases from CSV and skip to execution
            return "load_from_csv"
        else:
            # All other modes start with discovery
            return "discover"

    @router(route_by_mode)
    def mode_router(self):
        """Router to branch based on run mode."""
        mode = self.state.run_mode.lower()
        if mode == "execute_only":
            return "load_from_csv"
        return "discover"

    # ─────────────────────────────────────────────────────────────
    # EXECUTE_ONLY MODE: Load from CSV
    # ─────────────────────────────────────────────────────────────

    @listen("load_from_csv")
    def load_tests_from_csv(self):
        """Load test cases from CSV file (for execute_only mode)."""
        print("\n" + "=" * 60)
        print("Loading test cases from CSV...")
        print("=" * 60 + "\n")

        csv_path = self.state.test_csv_path
        if not csv_path:
            print("ERROR: No CSV path provided. Use TEST_CSV_PATH parameter.")
            return

        try:
            test_cases = []
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Parse category
                    category_str = row.get("category", "factual").lower()
                    try:
                        category = TestCategory(category_str)
                    except ValueError:
                        category = TestCategory.FACTUAL

                    # Parse difficulty
                    difficulty_str = row.get("difficulty", "medium").lower()
                    try:
                        difficulty = TestDifficulty(difficulty_str)
                    except ValueError:
                        difficulty = TestDifficulty.MEDIUM

                    test_case = TestCase(
                        id=row.get("id", f"CSV-{len(test_cases)+1:03d}"),
                        question=row.get("question", ""),
                        expected_answer=row.get("expected_answer", ""),
                        category=category,
                        difficulty=difficulty,
                        rationale=row.get("rationale", "Loaded from CSV"),
                    )
                    test_cases.append(test_case)

            self.state.test_cases = test_cases
            print(f"Loaded {len(test_cases)} test cases from {csv_path}")

        except FileNotFoundError:
            print(f"ERROR: CSV file not found: {csv_path}")
        except Exception as e:
            print(f"ERROR: Failed to load CSV: {e}")

    # ─────────────────────────────────────────────────────────────
    # PHASE 1: Discovery and Test Generation
    # ─────────────────────────────────────────────────────────────

    @listen("discover")
    def discover_rag_data(self):
        """Query RAG system to understand its knowledge domains."""
        print("\n" + "=" * 60)
        print("PHASE 1: Discovery - Analyzing RAG knowledge base...")
        print("=" * 60 + "\n")

        result = run_discovery(
            rag_tool=self.rag_tool,
            crew_description=self.state.crew_description,
            llm_model=self.llm_model,
        )

        # Parse the result into RagSummary
        try:
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0].strip()
            else:
                start_idx = result.find("{")
                end_idx = result.rfind("}") + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = result[start_idx:end_idx]
                else:
                    json_str = result

            data = json.loads(json_str)
            self.state.rag_summary = RagSummary(**data)
        except Exception as e:
            print(f"Warning: Could not parse RAG summary: {e}")
            self.state.rag_summary = RagSummary(
                total_coverage_estimate=result[:500]
            )

        print(f"\nDiscovered {len(self.state.rag_summary.domains)} domains")

    @listen(discover_rag_data)
    def generate_prompt_suggestions(self):
        """Generate agent and prompt configuration suggestions based on RAG data."""
        print("\n" + "=" * 60)
        print("PHASE 1: Generating prompt suggestions...")
        print("=" * 60 + "\n")

        # Convert RagSummary to JSON string for the crew
        rag_summary_str = self.state.rag_summary.model_dump_json() if self.state.rag_summary else "{}"

        suggestions = run_prompt_generator(
            rag_summary=rag_summary_str,
            crew_description=self.state.crew_description,
            llm_model=self.llm_model,
        )

        if suggestions:
            self.state.prompt_suggestions = suggestions
            print(f"\nGenerated prompt suggestions:")
            print(f"  - Primary agent role: {suggestions.primary_agent.role}")
            print(f"  - Example queries: {len(suggestions.example_queries)}")
            print(f"  - Out-of-scope examples: {len(suggestions.out_of_scope_examples)}")
            print(f"  - Limitations: {len(suggestions.limitations)}")
        else:
            print("\nWarning: Could not generate prompt suggestions")

    @listen(generate_prompt_suggestions)
    def check_prompt_only_exit(self):
        """Check if we should exit after prompt generation (prompt_only mode)."""
        mode = self.state.run_mode.lower()

        if mode == "prompt_only":
            return "output_prompts"
        else:
            return "continue_to_test_gen"

    @router(check_prompt_only_exit)
    def prompt_exit_router(self):
        """Router to exit after prompts or continue to test generation."""
        mode = self.state.run_mode.lower()
        if mode == "prompt_only":
            return "output_prompts"
        return "continue_to_test_gen"

    @listen("output_prompts")
    def output_prompt_suggestions(self):
        """Output prompt suggestions and exit (for prompt_only mode)."""
        print("\n" + "=" * 60)
        print("PROMPT SUGGESTIONS OUTPUT (prompt_only mode)")
        print("=" * 60 + "\n")

        if self.state.prompt_suggestions:
            output = {
                "primary_agent": {
                    "role": self.state.prompt_suggestions.primary_agent.role,
                    "goal": self.state.prompt_suggestions.primary_agent.goal,
                    "backstory": self.state.prompt_suggestions.primary_agent.backstory,
                },
                "supporting_agents": [
                    {"role": a.role, "goal": a.goal}
                    for a in self.state.prompt_suggestions.supporting_agents
                ],
                "system_prompt": self.state.prompt_suggestions.system_prompt,
                "example_queries": self.state.prompt_suggestions.example_queries,
                "out_of_scope_examples": self.state.prompt_suggestions.out_of_scope_examples,
                "limitations": self.state.prompt_suggestions.limitations,
            }
            print(json.dumps(output, indent=2))
            return json.dumps(output, indent=2)

        return "{}"

    @listen("continue_to_test_gen")
    def generate_test_cases(self):
        """Generate test questions and expected answers."""
        print("\n" + "=" * 60)
        print("PHASE 1: Generating test cases...")
        print("=" * 60 + "\n")

        # Convert RagSummary to JSON string for the crew
        rag_summary_str = self.state.rag_summary.model_dump_json() if self.state.rag_summary else "{}"

        test_categories = self.config.get("test_generation", {}).get(
            "categories", ["factual", "reasoning", "edge_case"]
        )

        self.state.test_cases = run_test_generation(
            rag_summary=rag_summary_str,
            crew_description=self.state.crew_description,
            num_tests=self.state.num_tests,
            test_categories=test_categories,
            llm_model=self.llm_model,
        )

        print(f"\nGenerated {len(self.state.test_cases)} test cases")

    @listen(generate_test_cases)
    def check_generate_only_exit(self):
        """Check if we should exit after test generation (generate_only mode)."""
        mode = self.state.run_mode.lower()

        if mode == "generate_only":
            return "output_tests"
        else:
            return "continue_to_execute"

    @router(check_generate_only_exit)
    def generate_exit_router(self):
        """Router to exit after test generation or continue to execution."""
        mode = self.state.run_mode.lower()
        if mode == "generate_only":
            return "output_tests"
        return "continue_to_execute"

    @listen("output_tests")
    def output_test_cases(self):
        """Output generated test cases and exit (for generate_only mode)."""
        print("\n" + "=" * 60)
        print("TEST CASES OUTPUT (generate_only mode)")
        print("=" * 60 + "\n")

        output = {
            "test_cases": [
                {
                    "id": tc.id,
                    "question": tc.question,
                    "expected_answer": tc.expected_answer,
                    "category": tc.category.value,
                    "difficulty": tc.difficulty.value,
                    "rationale": tc.rationale,
                }
                for tc in self.state.test_cases
            ],
            "prompt_suggestions": {
                "primary_agent_role": self.state.prompt_suggestions.primary_agent.role if self.state.prompt_suggestions else "",
                "system_prompt": self.state.prompt_suggestions.system_prompt if self.state.prompt_suggestions else "",
            } if self.state.prompt_suggestions else None,
            "rag_summary": {
                "domains": [d.name for d in self.state.rag_summary.domains],
                "coverage": self.state.rag_summary.total_coverage_estimate,
            } if self.state.rag_summary else None,
        }

        print(f"Generated {len(self.state.test_cases)} test cases:")
        for tc in self.state.test_cases:
            print(f"  - [{tc.id}] {tc.category.value}/{tc.difficulty.value}: {tc.question[:50]}...")

        print("\n\nFull output (JSON):")
        print(json.dumps(output, indent=2))

        return json.dumps(output, indent=2)

    # ─────────────────────────────────────────────────────────────
    # PHASE 2: Test Execution Loop
    # ─────────────────────────────────────────────────────────────

    @listen("continue_to_execute")
    def execute_tests(self):
        """Execute all tests against the target crew."""
        print("\n" + "=" * 60)
        print("PHASE 2: Executing tests...")
        print("=" * 60 + "\n")

        for i, test in enumerate(self.state.test_cases):
            self.state.current_test_index = i
            print(f"\nExecuting test {i + 1}/{len(self.state.test_cases)}: {test.id}")

            # Execute the test
            start_time = time.time()
            actual_answer = self.crew_runner._run(question=test.question)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Evaluate the response
            eval_result = self.evaluator._run(
                expected=test.expected_answer,
                actual=actual_answer,
                question=test.question,
            )

            try:
                eval_data = json.loads(eval_result)
            except json.JSONDecodeError:
                eval_data = {"passed": False, "score": 0.0, "rationale": "Evaluation failed"}

            test_result = TestResult(
                test_case=test,
                actual_answer=actual_answer,
                passed=eval_data.get("passed", False),
                similarity_score=eval_data.get("score", 0.0),
                evaluation_rationale=eval_data.get("rationale", ""),
                execution_time_ms=execution_time_ms,
            )

            self.state.results.append(test_result)

            status = "PASS" if test_result.passed else "FAIL"
            print(f"  [{status}] Score: {test_result.similarity_score:.2f}")

    @listen(load_tests_from_csv)
    def execute_csv_tests(self):
        """Execute tests loaded from CSV (for execute_only mode)."""
        if self.state.run_mode.lower() == "execute_only" and self.state.test_cases:
            print("\n" + "=" * 60)
            print("Executing tests from CSV...")
            print("=" * 60 + "\n")

            for i, test in enumerate(self.state.test_cases):
                self.state.current_test_index = i
                print(f"\nExecuting test {i + 1}/{len(self.state.test_cases)}: {test.id}")

                # Execute the test
                start_time = time.time()
                actual_answer = self.crew_runner._run(question=test.question)
                execution_time_ms = int((time.time() - start_time) * 1000)

                # Evaluate the response
                eval_result = self.evaluator._run(
                    expected=test.expected_answer,
                    actual=actual_answer,
                    question=test.question,
                )

                try:
                    eval_data = json.loads(eval_result)
                except json.JSONDecodeError:
                    eval_data = {"passed": False, "score": 0.0, "rationale": "Evaluation failed"}

                test_result = TestResult(
                    test_case=test,
                    actual_answer=actual_answer,
                    passed=eval_data.get("passed", False),
                    similarity_score=eval_data.get("score", 0.0),
                    evaluation_rationale=eval_data.get("rationale", ""),
                    execution_time_ms=execution_time_ms,
                )

                self.state.results.append(test_result)

                status = "PASS" if test_result.passed else "FAIL"
                print(f"  [{status}] Score: {test_result.similarity_score:.2f}")

    # ─────────────────────────────────────────────────────────────
    # PHASE 3: Evaluation and Reporting
    # ─────────────────────────────────────────────────────────────

    @listen(execute_tests)
    def evaluate_results(self):
        """Analyze all test results and generate metrics."""
        self._run_evaluation()

    @listen(execute_csv_tests)
    def evaluate_csv_results(self):
        """Evaluate results from CSV tests."""
        if self.state.results:
            self._run_evaluation()

    def _run_evaluation(self):
        """Common evaluation logic."""
        print("\n" + "=" * 60)
        print("PHASE 3: Analyzing results...")
        print("=" * 60 + "\n")

        # Calculate pass rate
        passed = sum(1 for r in self.state.results if r.passed)
        total = len(self.state.results)
        self.state.pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"Pass rate: {self.state.pass_rate:.1f}% ({passed}/{total})")

        # Calculate category scores
        self.state.category_scores = calculate_category_scores(self.state.results)

        # Run evaluation crew for detailed analysis
        analysis = run_evaluation(
            results=self.state.results,
            llm_model=self.llm_model,
        )

        # Extract recommendations
        recommendations = analysis.get("recommendations", {})
        if isinstance(recommendations, dict):
            self.state.recommendations = recommendations.get("priority_order", [])
        elif isinstance(recommendations, list):
            self.state.recommendations = recommendations

        # Store analysis for reporting
        self._analysis = analysis

    @listen(evaluate_results)
    def generate_report(self):
        """Generate final quality report with recommendations."""
        self._generate_report()

    @listen(evaluate_csv_results)
    def generate_csv_report(self):
        """Generate report for CSV tests."""
        if self.state.results:
            self._generate_report()

    def _generate_report(self):
        """Common report generation logic."""
        print("\n" + "=" * 60)
        print("PHASE 3: Generating report...")
        print("=" * 60 + "\n")

        analysis = getattr(self, "_analysis", {})

        # Determine target name
        target_name = self.state.target_api_url or self.state.target_crew_path or "Unknown"

        self.state.quality_report = run_reporting(
            results=self.state.results,
            category_scores=self.state.category_scores,
            analysis=analysis,
            target_name=target_name,
            llm_model=self.llm_model,
        )

        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETE")
        print("=" * 60)
        print(f"\nRun Mode: {self.state.run_mode.upper()}")
        print(f"Overall Pass Rate: {self.state.pass_rate:.1f}%")
        print(f"Tests: {len(self.state.results)} total, {sum(1 for r in self.state.results if r.passed)} passed")
        print("\n")

        return self.state.quality_report


def run_flow(
    target_api_url: str = "",
    target_api_token: str = "",
    target_crew_path: str = "",
    rag_endpoint: str = "",
    rag_backend: str = "ragengine",
    rag_mcp_url: str = "",
    rag_mcp_token: str = "",
    rag_corpus: str = "",
    rag_qdrant_url: str = "",
    rag_qdrant_api_key: str = "",
    rag_qdrant_collection: str = "",
    num_tests: int = 20,
    crew_description: str = "",
    run_mode: str = "full",
    test_csv_path: str = "",
    config: Optional[dict] = None,
) -> str:
    """
    Run the test suite flow.

    Args:
        target_api_url: CrewAI Enterprise API URL for the target crew
        target_api_token: Bearer token for target crew API
        target_crew_path: Path to local crew (if testing locally)
        rag_endpoint: RAG endpoint URL (deprecated, use rag_mcp_url)
        rag_backend: RAG backend type ('ragengine' or 'qdrant')
        rag_mcp_url: RAG Engine MCP server URL
        rag_mcp_token: Bearer token for RAG Engine MCP
        rag_corpus: RAG corpus name/path
        rag_qdrant_url: Qdrant server URL
        rag_qdrant_api_key: Qdrant API key
        rag_qdrant_collection: Qdrant collection name
        num_tests: Number of tests to generate
        crew_description: Description of what the crew should do
        run_mode: Execution mode (full, prompt_only, generate_only, execute_only)
        test_csv_path: Path to CSV file with test cases (for execute_only mode)
        config: Optional configuration dictionary

    Returns:
        Output based on run_mode:
        - full/generate_and_execute: Quality report markdown
        - prompt_only: JSON with prompt suggestions
        - generate_only: JSON with test cases
        - execute_only: Quality report markdown
    """
    flow = RAGTestSuiteFlow(config=config)

    # Initialize state with basic settings
    flow.state.run_mode = run_mode
    flow.state.test_csv_path = test_csv_path
    flow.state.target_api_url = target_api_url
    flow.state.target_api_token = target_api_token
    flow.state.target_crew_path = target_crew_path
    flow.state.target_mode = "api" if target_api_url else "local"
    flow.state.rag_endpoint = rag_endpoint
    flow.state.num_tests = num_tests
    flow.state.crew_description = crew_description

    # Initialize RAG configuration in state
    flow.state.rag_backend = rag_backend
    flow.state.rag_mcp_url = rag_mcp_url
    flow.state.rag_corpus = rag_corpus
    flow.state.rag_qdrant_url = rag_qdrant_url
    flow.state.rag_qdrant_collection = rag_qdrant_collection

    # Update crew runner with target
    if target_api_url:
        flow.crew_runner.api_url = target_api_url
        if target_api_token:
            flow.crew_runner.api_token = target_api_token
        flow.crew_runner.mode = "api"
    elif target_crew_path:
        flow.crew_runner.crew_path = target_crew_path
        flow.crew_runner.mode = "local"

    # Build inputs dict for kickoff (for RAG tool reconfiguration)
    inputs = {
        "RAG_BACKEND": rag_backend,
        "RAG_MCP_URL": rag_mcp_url,
        "RAG_MCP_TOKEN": rag_mcp_token,
        "RAG_CORPUS": rag_corpus,
        "RAG_QDRANT_URL": rag_qdrant_url,
        "RAG_QDRANT_API_KEY": rag_qdrant_api_key,
        "RAG_QDRANT_COLLECTION": rag_qdrant_collection,
    }

    # Run the flow with inputs for RAG configuration
    result = flow.kickoff(inputs=inputs)

    return result
