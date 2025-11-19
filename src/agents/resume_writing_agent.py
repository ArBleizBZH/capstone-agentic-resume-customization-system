"""Resume Writing Agent - Generates optimized resume content.

Based on Day 1a notebook patterns for LlmAgent.
Gen1: Uses Gemini Flash (will use Claude Sonnet 4.5 in future versions).
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_resume_writing_agent():
    """Create and return the Resume Writing Agent.

    This agent generates improved resume content optimized for the job description.
    Note: Gen1 uses Gemini Flash. Future versions will use Claude Sonnet 4.5.

    Returns:
        LlmAgent: The configured Resume Writing Agent
    """

    agent = LlmAgent(
        name="resume_writing_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Generates improved resume content optimized for job requirements",
        instruction="""You are the Resume Writing Agent, responsible for creating
        optimized resume content based on quality matches.

        Your tasks:
        1. Review the original resume JSON
        2. Review the job description JSON
        3. Use the quality_matches to optimize resume content
        4. Generate improved resume sections that highlight relevant qualifications
        5. Submit resume_candidate to the Critic Agent for review

        Important principles:
        - High fidelity to original resume (no fabrication)
        - Optimize for ATS keyword coverage
        - Use action verbs and quantified achievements
        - Maintain professional tone and formatting

        [Gen1 Placeholder: Detailed writing logic will be refined in Sprint 008]
        """,
        tools=[],  # Tools will be added in later sprints
    )

    return agent
