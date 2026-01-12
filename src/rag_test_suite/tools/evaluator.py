"""Tool for evaluating responses using LLM-as-judge."""

import json
import os
from typing import Optional

import requests
from crewai.tools import BaseTool
from pydantic import Field


class EvaluatorTool(BaseTool):
    """Evaluate response quality using LLM-as-judge."""

    name: str = "evaluate_response"
    description: str = """
    Compare actual response to expected answer using LLM judgment.

    Args:
        expected: The expected/ideal answer
        actual: The crew's actual response
        question: The original question (for context)

    Returns:
        JSON with: passed (bool), score (float 0-1), rationale (str)
    """

    # Configuration
    judge_model: str = Field(
        default="openai/gemini-2.5-flash", description="Model to use for evaluation"
    )
    pass_threshold: float = Field(default=0.7, description="Score threshold for pass")
    temperature: float = Field(default=0.1, description="Temperature for judge model")

    def _run(
        self, expected: str, actual: str, question: str, criteria: Optional[str] = None
    ) -> str:
        """
        Evaluate the response quality.

        Args:
            expected: Expected answer
            actual: Actual response from crew
            question: Original question
            criteria: Optional additional evaluation criteria

        Returns:
            JSON string with evaluation results
        """
        prompt = self._build_evaluation_prompt(expected, actual, question, criteria)

        try:
            result = self._call_llm(prompt)
            return result
        except Exception as e:
            # Return failure result on error
            return json.dumps(
                {
                    "passed": False,
                    "score": 0.0,
                    "rationale": f"Evaluation error: {e}",
                }
            )

    def _build_evaluation_prompt(
        self,
        expected: str,
        actual: str,
        question: str,
        criteria: Optional[str] = None,
    ) -> str:
        """Build the evaluation prompt for LLM-as-judge."""
        base_criteria = """
Consider the following aspects:
1. **Factual Accuracy**: Does the response contain correct information?
2. **Completeness**: Does it address all parts of the question?
3. **Relevance**: Is the response focused on the question?
4. **Clarity**: Is the response clear and well-structured?
"""

        if criteria:
            base_criteria += f"\nAdditional criteria:\n{criteria}"

        return f"""You are an expert evaluator assessing AI response quality.

**Question Asked:**
{question}

**Expected Answer:**
{expected}

**Actual Response:**
{actual}

{base_criteria}

**Instructions:**
Compare the actual response to the expected answer. Score the response from 0.0 to 1.0:
- 1.0 = Perfect match or equivalent quality
- 0.8-0.9 = Very good, minor differences
- 0.6-0.7 = Acceptable, some important content missing
- 0.4-0.5 = Partial answer, significant gaps
- 0.2-0.3 = Poor, mostly incorrect or irrelevant
- 0.0-0.1 = Completely wrong or off-topic

**Output Format:**
Return ONLY a JSON object with these exact fields:
{{
    "passed": true/false,
    "score": 0.0-1.0,
    "rationale": "Brief explanation of the score"
}}

The response passes if score >= {self.pass_threshold}.

**Your Evaluation:**"""

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM for evaluation."""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        api_base = os.environ.get("OPENAI_API_BASE", "")

        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        # Extract model name (remove openai/ prefix if present)
        model = self.judge_model
        if model.startswith("openai/"):
            model = model[7:]

        # Use OpenAI-compatible API
        if api_base:
            url = f"{api_base}/chat/completions"
        else:
            url = "https://api.openai.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            # Gemini 2.5 Flash uses many tokens for internal reasoning
            # Need high max_tokens to ensure full response
            "max_tokens": 2000,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]

        # Parse JSON from response
        try:
            # Try to extract JSON from the response
            json_str = content.strip()

            # Handle markdown code blocks
            if "```json" in json_str:
                # Extract content after ```json
                json_str = json_str.split("```json")[1]
                # Remove closing ``` if present
                if "```" in json_str:
                    json_str = json_str.split("```")[0]
            elif "```" in json_str:
                # Generic code block
                json_str = json_str.split("```")[1]
                if "```" in json_str:
                    json_str = json_str.split("```")[0]

            json_str = json_str.strip()

            # If the JSON is incomplete (truncated), try to complete it
            if json_str.startswith("{") and not json_str.endswith("}"):
                # Try to find where the JSON was cut off and complete it
                # Count braces to see how many we need to close
                open_braces = json_str.count("{") - json_str.count("}")
                json_str = json_str.rstrip() + "}" * open_braces

            # Also handle truncated string values
            if '"rationale":' in json_str and not json_str.rstrip().endswith("}"):
                # Truncated rationale string - close it
                if json_str.count('"') % 2 != 0:
                    json_str = json_str.rstrip() + '"}'

            result = json.loads(json_str)

            # Ensure required fields
            score = float(result.get("score", 0))
            passed = result.get("passed", score >= self.pass_threshold)
            rationale = result.get("rationale", "No rationale provided")

            return json.dumps(
                {"passed": passed, "score": score, "rationale": rationale}
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Try regex fallback to extract score from text
            import re
            score_match = re.search(r'"score"\s*:\s*([\d.]+)', content)
            passed_match = re.search(r'"passed"\s*:\s*(true|false)', content, re.IGNORECASE)

            if score_match:
                score = float(score_match.group(1))
                passed = passed_match.group(1).lower() == "true" if passed_match else score >= self.pass_threshold
                return json.dumps(
                    {"passed": passed, "score": score, "rationale": f"Extracted from partial response: {content[:100]}"}
                )

            # Final fallback
            return json.dumps(
                {
                    "passed": False,
                    "score": 0.5,
                    "rationale": f"Could not parse evaluation: {content[:200]}",
                }
            )


def create_evaluator_from_config(config: dict) -> EvaluatorTool:
    """
    Create an EvaluatorTool from configuration dictionary.

    Args:
        config: Configuration dictionary with 'evaluation' section

    Returns:
        Configured EvaluatorTool instance
    """
    eval_config = config.get("evaluation", {})

    return EvaluatorTool(
        judge_model=eval_config.get("judge_model", "openai/gemini-2.5-flash"),
        pass_threshold=eval_config.get("pass_threshold", 0.7),
    )


def evaluate_batch(
    evaluator: EvaluatorTool,
    test_results: list,
) -> list[dict]:
    """
    Evaluate a batch of test results.

    Args:
        evaluator: Configured EvaluatorTool
        test_results: List of test result dictionaries with question, expected, actual

    Returns:
        List of evaluation results
    """
    evaluations = []

    for result in test_results:
        eval_result = evaluator._run(
            expected=result.get("expected", ""),
            actual=result.get("actual", ""),
            question=result.get("question", ""),
        )

        try:
            evaluations.append(json.loads(eval_result))
        except json.JSONDecodeError:
            evaluations.append(
                {"passed": False, "score": 0.0, "rationale": "Evaluation failed"}
            )

    return evaluations
