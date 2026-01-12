"""Test Generation Crew - Creates test cases from RAG discovery."""

import json
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from rag_test_suite.models import TestCase, TestCategory, TestDifficulty


@CrewBase
class TestGenerationCrew:
    """Crew that generates test cases from RAG knowledge discovery."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm_model: str = "openai/gemini-2.5-flash"):
        """
        Initialize the Test Generation Crew.

        Args:
            llm_model: LLM model to use for the agent
        """
        self.llm = LLM(model=llm_model, temperature=0.5)

    @agent
    def test_designer(self) -> Agent:
        """Test Case Designer agent."""
        return Agent(
            config=self.agents_config["test_designer"],
            llm=self.llm,
            verbose=True,
        )

    @task
    def generate_test_cases(self) -> Task:
        """Task to generate test cases."""
        return Task(
            config=self.tasks_config["generate_test_cases"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Test Generation crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def run_test_generation(
    rag_summary: str,
    crew_description: str = "",
    num_tests: int = 20,
    test_categories: Optional[list[str]] = None,
    llm_model: str = "openai/gemini-2.5-flash",
) -> list[TestCase]:
    """
    Run the test generation crew to create test cases.

    Args:
        rag_summary: JSON string of discovered RAG knowledge
        crew_description: Description of what the crew should do
        num_tests: Number of tests to generate
        test_categories: Categories to include
        llm_model: LLM model to use

    Returns:
        List of TestCase objects
    """
    if test_categories is None:
        test_categories = ["factual", "reasoning", "edge_case", "out_of_scope", "ambiguous"]

    test_gen_crew = TestGenerationCrew(llm_model=llm_model)

    result = test_gen_crew.crew().kickoff(
        inputs={
            "rag_summary": rag_summary,
            "crew_description": crew_description or "General knowledge assistant",
            "num_tests": num_tests,
            "test_categories": ", ".join(test_categories),
        }
    )

    raw_result = result.raw if hasattr(result, "raw") else str(result)

    return parse_test_cases(raw_result)


def parse_test_cases(raw_output: str) -> list[TestCase]:
    """
    Parse test cases from LLM output.

    Args:
        raw_output: Raw string output from the crew

    Returns:
        List of TestCase objects
    """
    test_cases = []

    try:
        # Try to extract JSON from the output
        if "```json" in raw_output:
            json_str = raw_output.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_output:
            json_str = raw_output.split("```")[1].split("```")[0].strip()
        else:
            # Try to find JSON array
            start = raw_output.find("[")
            end = raw_output.rfind("]") + 1
            if start != -1 and end > start:
                json_str = raw_output[start:end]
            else:
                json_str = raw_output

        data = json.loads(json_str)

        if isinstance(data, list):
            for item in data:
                test_case = _parse_single_test_case(item)
                if test_case:
                    test_cases.append(test_case)

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # If parsing fails, create a minimal test case set
        print(f"Warning: Could not parse test cases: {e}")

    return test_cases


def _parse_single_test_case(item: dict) -> Optional[TestCase]:
    """Parse a single test case from a dictionary."""
    try:
        # Parse category
        category_str = item.get("category", "factual").lower()
        try:
            category = TestCategory(category_str)
        except ValueError:
            category = TestCategory.FACTUAL

        # Parse difficulty
        difficulty_str = item.get("difficulty", "medium").lower()
        try:
            difficulty = TestDifficulty(difficulty_str)
        except ValueError:
            difficulty = TestDifficulty.MEDIUM

        return TestCase(
            id=item.get("id", f"TEST-{len(item)}"),
            question=item.get("question", ""),
            expected_answer=item.get("expected_answer", ""),
            category=category,
            difficulty=difficulty,
            rationale=item.get("rationale", ""),
        )
    except Exception:
        return None
