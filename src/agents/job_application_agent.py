"""Job Application Agent - Root orchestrator for the resume customization system.

Based on Day 1a and Day 5a notebook patterns for LlmAgent with sub_agents.
Gen1: Orchestrates Resume Refiner Agent.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_job_application_agent():
    """Create and return the Job Application Agent.

    This is the root orchestrator that coordinates the entire
    resume customization workflow.

    Returns:
        LlmAgent: The configured Job Application Agent
    """

    # Import resume_refiner_agent here to avoid circular imports
    from src.agents.resume_refiner_agent import create_resume_refiner_agent

    resume_refiner_agent = create_resume_refiner_agent()

    agent = LlmAgent(
        name="job_application_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Orchestrates the complete resume customization workflow",
        instruction="""You are the Job Application Agent, responsible for orchestrating
        the resume customization process.

        Your workflow:
        1. Receive the resume and job description from the user
        2. Delegate to the Resume Refiner Agent to optimize the resume
        3. Return the final optimized resume

        [Gen1 Placeholder: Detailed prompts will be refined in later sprints]
        """,
        sub_agents=[resume_refiner_agent],
    )

    return agent
