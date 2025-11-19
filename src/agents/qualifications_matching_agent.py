"""Qualifications Matching Agent - Finds matches between resume and job description.

Based on Day 1a notebook patterns for LlmAgent.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_qualifications_matching_agent():
    """Create and return the Qualifications Matching Agent.

    This agent analyzes resume and job description to find quality matches
    between qualifications.

    Returns:
        LlmAgent: The configured Qualifications Matching Agent
    """

    agent = LlmAgent(
        name="qualifications_matching_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Finds and validates matches between resume qualifications and job requirements",
        instruction="""You are the Qualifications Matching Agent, responsible for
        analyzing the resume and job description to identify quality matches.

        Your tasks:
        1. Review the resume JSON and job description JSON
        2. Identify strong, direct matches between qualifications
        3. Identify possible quality matches that are near-certain
        4. Output quality_matches and possible_quality_matches lists

        Important: Only match actual qualifications from the resume.
        Never fabricate or exaggerate qualifications.

        [Gen1 Placeholder: Detailed matching logic and tools will be added in Sprint 007]
        """,
        tools=[],  # Tools will be added in later sprints
    )

    return agent
