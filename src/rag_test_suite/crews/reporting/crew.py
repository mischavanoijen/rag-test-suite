"""Reporting Crew - Generates quality reports."""

import json
from datetime import datetime
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from rag_test_suite.models import TestResult, CategoryScore


@CrewBase
class ReportingCrew:
    """Crew that generates quality reports from test results."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm_model: str = "openai/gemini-2.5-flash"):
        """
        Initialize the Reporting Crew.

        Args:
            llm_model: LLM model to use for the agent
        """
        self.llm = LLM(model=llm_model, temperature=0.3)

    @agent
    def report_writer(self) -> Agent:
        """Report Writer agent."""
        return Agent(
            config=self.agents_config["report_writer"],
            llm=self.llm,
            verbose=True,
        )

    @task
    def generate_report(self) -> Task:
        """Task to generate the quality report."""
        return Task(
            config=self.tasks_config["generate_report"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Reporting crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def run_reporting(
    results: list[TestResult],
    category_scores: list[CategoryScore],
    analysis: dict,
    target_name: str = "Unknown",
    llm_model: str = "openai/gemini-2.5-flash",
) -> str:
    """
    Run the reporting crew to generate a quality report.

    Args:
        results: List of TestResult objects
        category_scores: Category score breakdowns
        analysis: Analysis results from evaluation crew
        target_name: Name of the target being tested
        llm_model: LLM model to use

    Returns:
        Markdown report string
    """
    # Calculate statistics
    total_tests = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total_tests - passed_count
    pass_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0

    # Format category breakdown
    category_breakdown = format_category_table(category_scores)

    # Format analysis summary
    analysis_summary = format_analysis_summary(analysis)

    # Format recommendations
    recommendations = format_recommendations(analysis.get("recommendations", {}))

    reporting_crew = ReportingCrew(llm_model=llm_model)

    result = reporting_crew.crew().kickoff(
        inputs={
            "pass_rate": f"{pass_rate:.1f}",
            "total_tests": total_tests,
            "passed_count": passed_count,
            "failed_count": failed_count,
            "category_breakdown": category_breakdown,
            "analysis_summary": analysis_summary,
            "recommendations": recommendations,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "target_name": target_name,
        }
    )

    return result.raw if hasattr(result, "raw") else str(result)


def format_category_table(scores: list[CategoryScore]) -> str:
    """Format category scores as a markdown table."""
    lines = ["| Category | Pass Rate | Passed | Failed | Status |"]
    lines.append("|----------|-----------|--------|--------|--------|")

    for score in scores:
        failed = score.total - score.passed
        if score.pass_rate >= 80:
            status = "OK"
        elif score.pass_rate >= 60:
            status = "WARN"
        else:
            status = "FAIL"

        lines.append(
            f"| {score.category.value} | {score.pass_rate:.1f}% | {score.passed} | {failed} | {status} |"
        )

    return "\n".join(lines)


def format_analysis_summary(analysis: dict) -> str:
    """Format analysis results as a summary."""
    summary = analysis.get("summary", "")

    patterns = analysis.get("failure_patterns", [])
    if patterns:
        summary += "\n\n**Failure Patterns:**\n"
        for p in patterns[:3]:
            if isinstance(p, dict):
                summary += f"- {p.get('pattern', 'Unknown pattern')}\n"
            else:
                summary += f"- {p}\n"

    causes = analysis.get("root_causes", [])
    if causes:
        summary += "\n**Root Causes:**\n"
        for c in causes[:3]:
            if isinstance(c, dict):
                summary += f"- {c.get('cause', 'Unknown cause')}\n"
            else:
                summary += f"- {c}\n"

    return summary


def format_recommendations(recommendations: dict) -> str:
    """Format recommendations as markdown."""
    lines = []

    prompt_changes = recommendations.get("prompt_changes", [])
    if prompt_changes:
        lines.append("**Prompt Changes:**")
        for change in prompt_changes[:5]:
            if isinstance(change, dict):
                lines.append(f"- [{change.get('priority', 'medium')}] {change.get('change', '')}")
            else:
                lines.append(f"- {change}")

    rag_changes = recommendations.get("rag_changes", [])
    if rag_changes:
        lines.append("\n**RAG Changes:**")
        for change in rag_changes[:5]:
            if isinstance(change, dict):
                lines.append(f"- [{change.get('priority', 'medium')}] {change.get('change', '')}")
            else:
                lines.append(f"- {change}")

    priority = recommendations.get("priority_order", [])
    if priority:
        lines.append("\n**Priority Order:**")
        for i, item in enumerate(priority[:5], 1):
            lines.append(f"{i}. {item}")

    return "\n".join(lines) if lines else "No specific recommendations."
