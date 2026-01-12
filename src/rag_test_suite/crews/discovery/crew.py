"""Discovery Crew - Queries RAG system to map knowledge domains."""

import json
from pathlib import Path

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from rag_test_suite.tools.rag_query import RagQueryTool


@CrewBase
class DiscoveryCrew:
    """Crew that discovers and maps RAG knowledge domains."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, rag_tool: RagQueryTool = None, llm_model: str = "openai/gemini-2.5-flash"):
        """
        Initialize the Discovery Crew.

        Args:
            rag_tool: Configured RagQueryTool for querying the RAG system
            llm_model: LLM model to use for the agent
        """
        self.rag_tool = rag_tool or RagQueryTool()
        self.llm = LLM(model=llm_model, temperature=0.3)

    @agent
    def rag_analyst(self) -> Agent:
        """RAG System Analyst agent."""
        return Agent(
            config=self.agents_config["rag_analyst"],
            llm=self.llm,
            tools=[self.rag_tool],
            verbose=True,
        )

    @task
    def discover_knowledge(self) -> Task:
        """Task to discover RAG knowledge domains."""
        return Task(
            config=self.tasks_config["discover_knowledge"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Discovery crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def _is_valid_discovery_output(result: str) -> bool:
    """Check if discovery output contains valid JSON structure."""
    try:
        # Try to extract JSON from result
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            json_str = result.split("```")[1].split("```")[0].strip()
        else:
            start_idx = result.find("{")
            end_idx = result.rfind("}") + 1
            if start_idx == -1 or end_idx <= start_idx:
                return False
            json_str = result[start_idx:end_idx]

        data = json.loads(json_str)
        # Check for required fields
        return "domains" in data or "total_coverage_estimate" in data
    except (json.JSONDecodeError, ValueError):
        return False


def _create_fallback_summary(rag_tool: RagQueryTool) -> str:
    """Create a basic discovery summary from direct RAG queries."""
    print("Creating fallback discovery summary...")

    # Query for main topics
    topics_result = rag_tool._run("What are the main topics covered?", num_results=3)

    # Extract topic names from results
    domains = []

    # Parse common topics from source paths
    if "Employee Experience" in topics_result:
        domains.append({
            "name": "Employee Experience",
            "subtopics": ["helpdesk support", "service desk", "employee tools"],
            "depth": "medium",
            "example_queries": ["What is employee experience?"],
            "sample_facts": ["Employee experience covers internal support services"]
        })

    if "GenAI" in topics_result or "Advisory" in topics_result:
        domains.append({
            "name": "GenAI Advisory",
            "subtopics": ["AI strategy", "consulting", "implementation"],
            "depth": "medium",
            "example_queries": ["What is GenAI advisory?"],
            "sample_facts": ["GenAI consulting services for enterprise adoption"]
        })

    if "Data" in topics_result:
        domains.append({
            "name": "Data Foundation",
            "subtopics": ["data governance", "data management", "compliance"],
            "depth": "medium",
            "example_queries": ["What is data governance?"],
            "sample_facts": ["Data foundation services for enterprise data management"]
        })

    # If no domains found, create a generic one
    if not domains:
        domains.append({
            "name": "General Knowledge",
            "subtopics": ["various topics"],
            "depth": "unknown",
            "example_queries": ["General query"],
            "sample_facts": ["Knowledge base content"]
        })

    summary = {
        "domains": domains,
        "boundaries": ["topics outside business/technology domain"],
        "total_coverage_estimate": "Business and technology knowledge base with multiple domains",
        "quality_notes": "Fallback summary generated from direct RAG queries"
    }

    return json.dumps(summary, indent=2)


def run_discovery(
    rag_tool: RagQueryTool,
    crew_description: str = "",
    llm_model: str = "openai/gemini-2.5-flash",
    max_retries: int = 2,
) -> str:
    """
    Run the discovery crew to map RAG knowledge domains.

    Args:
        rag_tool: Configured RagQueryTool
        crew_description: Description of what the crew should do
        llm_model: LLM model to use
        max_retries: Maximum retry attempts if output is invalid

    Returns:
        JSON string with discovered knowledge summary
    """
    for attempt in range(max_retries):
        try:
            discovery_crew = DiscoveryCrew(rag_tool=rag_tool, llm_model=llm_model)

            result = discovery_crew.crew().kickoff(
                inputs={"crew_description": crew_description or "General knowledge assistant"}
            )

            result_str = result.raw if hasattr(result, "raw") else str(result)

            if _is_valid_discovery_output(result_str):
                return result_str
            else:
                print(f"Discovery attempt {attempt + 1} produced invalid output, retrying...")

        except Exception as e:
            print(f"Discovery attempt {attempt + 1} failed: {e}")

    # If all retries fail, use fallback
    print("All discovery attempts failed, using fallback summary")
    return _create_fallback_summary(rag_tool)
