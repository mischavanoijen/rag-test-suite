"""Crews for the CrewAI Test Suite."""

from crewai_test_suite.crews.discovery.crew import DiscoveryCrew
from crewai_test_suite.crews.test_generation.crew import TestGenerationCrew
from crewai_test_suite.crews.evaluation.crew import EvaluationCrew
from crewai_test_suite.crews.reporting.crew import ReportingCrew

__all__ = ["DiscoveryCrew", "TestGenerationCrew", "EvaluationCrew", "ReportingCrew"]
