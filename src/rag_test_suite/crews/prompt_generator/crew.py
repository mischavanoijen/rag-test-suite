"""Prompt Generator Crew - Generates agent configs and prompts from RAG analysis."""

import json
from typing import Optional

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

from rag_test_suite.models import (
    PromptSuggestions,
    AgentSuggestion,
    TaskSuggestion,
)


@CrewBase
class PromptGeneratorCrew:
    """Crew that generates prompt and agent configuration suggestions."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm_model: str = "openai/gemini-2.5-flash"):
        """
        Initialize the Prompt Generator Crew.

        Args:
            llm_model: LLM model to use for the agent
        """
        self.llm = LLM(model=llm_model, temperature=0.5)

    @agent
    def prompt_engineer(self) -> Agent:
        """Prompt Engineering agent."""
        return Agent(
            config=self.agents_config["prompt_engineer"],
            llm=self.llm,
            verbose=True,
        )

    @task
    def generate_prompts(self) -> Task:
        """Task to generate prompt suggestions."""
        return Task(
            config=self.tasks_config["generate_prompts"],
        )

    @crew
    def crew(self) -> Crew:
        """Create the Prompt Generator crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


def _parse_prompt_suggestions(result: str) -> Optional[PromptSuggestions]:
    """Parse LLM output into PromptSuggestions model."""
    try:
        # Extract JSON from result
        if "```json" in result:
            json_str = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            json_str = result.split("```")[1].split("```")[0].strip()
        else:
            start_idx = result.find("{")
            end_idx = result.rfind("}") + 1
            if start_idx == -1 or end_idx <= start_idx:
                return None
            json_str = result[start_idx:end_idx]

        data = json.loads(json_str)

        # Parse primary agent
        primary_data = data.get("primary_agent", {})
        primary_agent = AgentSuggestion(
            role=primary_data.get("role", "Knowledge Assistant"),
            goal=primary_data.get("goal", "Help users find information"),
            backstory=primary_data.get("backstory", ""),
            tools=primary_data.get("tools", ["rag_search"]),
            expertise_areas=primary_data.get("expertise_areas", []),
        )

        # Parse supporting agents
        supporting_agents = []
        for agent_data in data.get("supporting_agents", []):
            supporting_agents.append(
                AgentSuggestion(
                    role=agent_data.get("role", ""),
                    goal=agent_data.get("goal", ""),
                    backstory=agent_data.get("backstory", ""),
                    tools=agent_data.get("tools", []),
                    expertise_areas=agent_data.get("expertise_areas", []),
                )
            )

        # Parse suggested tasks
        suggested_tasks = []
        for task_data in data.get("suggested_tasks", []):
            suggested_tasks.append(
                TaskSuggestion(
                    name=task_data.get("name", ""),
                    description=task_data.get("description", ""),
                    expected_output=task_data.get("expected_output", ""),
                )
            )

        return PromptSuggestions(
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            suggested_tasks=suggested_tasks,
            system_prompt=data.get("system_prompt", ""),
            example_queries=data.get("example_queries", []),
            out_of_scope_examples=data.get("out_of_scope_examples", []),
            knowledge_summary=data.get("knowledge_summary", ""),
            limitations=data.get("limitations", []),
            suggested_tone=data.get("suggested_tone", "professional"),
            response_format_guidance=data.get("response_format_guidance", ""),
        )

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"Error parsing prompt suggestions: {e}")
        return None


def run_prompt_generator(
    rag_summary: str,
    crew_description: str = "",
    llm_model: str = "openai/gemini-2.5-flash",
) -> Optional[PromptSuggestions]:
    """
    Run the prompt generator crew to create agent and prompt suggestions.

    Args:
        rag_summary: JSON string with RAG knowledge summary
        crew_description: Description of what the crew should do
        llm_model: LLM model to use

    Returns:
        PromptSuggestions object or None if generation fails
    """
    try:
        generator_crew = PromptGeneratorCrew(llm_model=llm_model)

        result = generator_crew.crew().kickoff(
            inputs={
                "rag_summary": rag_summary,
                "crew_description": crew_description or "General knowledge assistant",
            }
        )

        result_str = result.raw if hasattr(result, "raw") else str(result)

        suggestions = _parse_prompt_suggestions(result_str)
        if suggestions:
            return suggestions
        else:
            print("Failed to parse prompt suggestions, creating defaults")
            return _create_default_suggestions(rag_summary, crew_description)

    except Exception as e:
        print(f"Prompt generation failed: {e}")
        return _create_default_suggestions(rag_summary, crew_description)


def _create_default_suggestions(
    rag_summary: str,
    crew_description: str,
) -> PromptSuggestions:
    """Create default prompt suggestions as fallback."""
    # Try to extract domain info from summary
    try:
        data = json.loads(rag_summary) if isinstance(rag_summary, str) else rag_summary
        domains = data.get("domains", [])
        domain_names = [d.get("name", "Unknown") for d in domains[:3]]
        coverage = data.get("total_coverage_estimate", "General knowledge")
    except (json.JSONDecodeError, TypeError):
        domain_names = ["General Knowledge"]
        coverage = "Various topics"

    expertise = ", ".join(domain_names) if domain_names else "various topics"

    return PromptSuggestions(
        primary_agent=AgentSuggestion(
            role="Knowledge Assistant",
            goal="Help users find accurate information from the knowledge base",
            backstory=f"""You are a helpful knowledge assistant with expertise in {expertise}.
You are thorough in your research and always cite your sources.
When you don't know something, you say so honestly rather than making things up.
You communicate clearly and adapt your responses to the user's level of expertise.""",
            tools=["rag_search"],
            expertise_areas=domain_names,
        ),
        system_prompt=f"""You are a helpful assistant with access to a knowledge base covering {coverage}.

GUIDELINES:
1. Always search the knowledge base before answering
2. Cite sources in your responses
3. If you can't find information, say so clearly
4. Be concise but thorough
5. Ask clarifying questions if needed

LIMITATIONS:
- Only answer questions related to the knowledge base
- Do not make up information
- Redirect off-topic questions politely""",
        example_queries=[
            f"What is {domain_names[0]}?" if domain_names else "What topics do you cover?",
            "Tell me more about the available services",
            "How does this work?",
        ],
        out_of_scope_examples=[
            "What's the weather today?",
            "Tell me a joke",
            "What's happening in the news?",
        ],
        knowledge_summary=coverage,
        limitations=[
            "Limited to information in the knowledge base",
            "May not have the latest updates",
            "Cannot perform actions, only provide information",
        ],
        suggested_tone="professional",
        response_format_guidance="Use markdown formatting. Include source citations. Keep responses focused and relevant.",
    )
