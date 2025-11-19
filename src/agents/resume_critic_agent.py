"""Resume Critic Agent - Evaluates resume quality and provides feedback.

Based on Day 1a notebook patterns for LlmAgent.
Uses Gemini Pro for higher quality evaluation (per project design).
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from src.config.model_config import GEMINI_PRO_MODEL, retry_config, GOOGLE_API_KEY


def create_resume_critic_agent():
    """Create and return the Resume Critic Agent.

    This agent evaluates resume quality and controls the write-critique loop.
    Uses Gemini Pro model for better evaluation capabilities.

    Returns:
        LlmAgent: The configured Resume Critic Agent
    """

    agent = LlmAgent(
        name="resume_critic_agent",
        model=Gemini(
            model=GEMINI_PRO_MODEL,  # Using Pro model for evaluation
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Evaluates resume quality and controls the write-critique loop",
        instruction="""You are the Resume Critic Agent, responsible for ensuring
        high-quality, high-fidelity resume output.

        Your tasks:
        1. Review resume_candidate from the Writing Agent
        2. Compare against original resume for fidelity
        3. Compare against job description for relevance
        4. Evaluate quality on multiple criteria:
           - ATS keyword coverage (0-3 points)
           - Impact and metrics (0-3 points)
           - Clarity and relevance (0-2 points)
           - Grammar and formatting (0-2 points)

        Decision logic:
        - If issues found: Return JSON list of issues to Writing Agent
        - If no issues (score >= 8): Send optimized_resume to Resume Refiner Agent

        Important: Maintain high standards for accuracy. Never approve fabricated
        qualifications or exaggerated achievements.

        [Gen1 Placeholder: Detailed evaluation criteria will be refined in Sprint 009]
        """,
        tools=[],  # Tools will be added in later sprints
    )

    return agent
