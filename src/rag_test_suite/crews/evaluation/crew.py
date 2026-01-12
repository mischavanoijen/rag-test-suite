"""Evaluation Crew - Analyzes test results and identifies patterns."""

import json
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from rag_test_suite.models import TestResult, CategoryScore, TestCategory


@CrewBase
class EvaluationCrew:
    """Crew that analyzes test results and generates recommendations."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm_model: str = "openai/gemini-2.5-flash"):
        """
        Initialize the Evaluation Crew.

        Args:
            llm_model: LLM model to use for the agent
        """
        self.llm = LLM(model=llm_model, temperature=0.3)

    @agent
    def quality_analyst(self) -> Agent:
        """Quality Analyst agent."""
        return Agent(
            config=self.agents_config["quality_analyst"],
            llm=self.llm,
            verbose=True,
        )

    @task
    def analyze_results(self) -> Task:
        """Task to analyze test results."""
        return Task(
            config=self.tasks_config["analyze_results"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Evaluation crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def run_evaluation(
    results: list[TestResult],
    llm_model: str = "openai/gemini-2.5-flash",
) -> dict:
    """
    Run the evaluation crew to analyze test results.

    Args:
        results: List of TestResult objects
        llm_model: LLM model to use

    Returns:
        Dictionary with analysis and recommendations
    """
    # Calculate statistics
    total_tests = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total_tests - passed_count
    pass_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

    # Calculate category breakdown
    category_scores = calculate_category_scores(results)
    category_breakdown = format_category_breakdown(category_scores)

    # Get failed examples
    failed_examples = format_failed_examples(results, max_examples=5)

    eval_crew = EvaluationCrew(llm_model=llm_model)

    result = eval_crew.crew().kickoff(
        inputs={
            "pass_rate": f"{pass_rate:.1f}",
            "total_tests": total_tests,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "category_breakdown": category_breakdown,
            "failed_examples": failed_examples,
        }
    )

    raw_result = result.raw if hasattr(result, "raw") else str(result)

    return parse_evaluation_result(raw_result)


def calculate_category_scores(results: list[TestResult]) -> list[CategoryScore]:
    """Calculate scores by category."""
    category_stats = {}

    for result in results:
        cat = result.test_case.category
        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "issues": []}

        category_stats[cat]["total"] += 1
        if result.passed:
            category_stats[cat]["passed"] += 1
        else:
            category_stats[cat]["issues"].append(result.evaluation_rationale[:100])

    scores = []
    for category, stats in category_stats.items():
        pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        scores.append(
            CategoryScore(
                category=category,
                total=stats["total"],
                passed=stats["passed"],
                pass_rate=pass_rate,
                common_issues=stats["issues"][:3],
            )
        )

    return scores


def format_category_breakdown(scores: list[CategoryScore]) -> str:
    """Format category scores as a string."""
    lines = []
    for score in scores:
        lines.append(
            f"- {score.category.value}: {score.passed}/{score.total} ({score.pass_rate:.1f}%)"
        )
        if score.common_issues:
            for issue in score.common_issues[:2]:
                lines.append(f"  Issue: {issue}")

    return "\n".join(lines)


def format_failed_examples(results: list[TestResult], max_examples: int = 5) -> str:
    """Format failed test examples as a string."""
    failed = [r for r in results if not r.passed][:max_examples]

    if not failed:
        return "No failed tests."

    lines = []
    for result in failed:
        lines.append(f"\n**{result.test_case.id}** ({result.test_case.category.value}, {result.test_case.difficulty.value})")
        lines.append(f"Question: {result.test_case.question}")
        lines.append(f"Expected: {result.test_case.expected_answer[:200]}...")
        lines.append(f"Actual: {result.actual_answer[:200]}...")
        lines.append(f"Score: {result.similarity_score:.2f}")
        lines.append(f"Rationale: {result.evaluation_rationale}")

    return "\n".join(lines)


def parse_evaluation_result(raw_output: str) -> dict:
    """Parse evaluation result from LLM output."""
    try:
        # Try to extract JSON from the output
        if "```json" in raw_output:
            json_str = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            json_str = raw_output.split("```")[1].split("```")[0].strip()
        else:
            start = raw_output.find("{")
            end = raw_output.rfind("}") + 1
            if start != -1 and end > start:
                json_str = raw_output[start:end]
            else:
                json_str = raw_output

        return json.loads(json_str)

    except (json.JSONDecodeError, KeyError, ValueError):
        return {
            "failure_patterns": [],
            "root_causes": [],
            "recommendations": {"prompt_changes": [], "rag_changes": [], "priority_order": []},
            "summary": raw_output[:500],
        }
