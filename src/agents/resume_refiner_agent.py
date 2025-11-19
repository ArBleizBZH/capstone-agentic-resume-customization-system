"""Resume Refiner Agent - Coordinates the resume optimization process.

Based on Day 2a and Day 5a notebook patterns for LlmAgent with AgentTool.
Coordinates sequential workflow and write-critique loop.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_resume_refiner_agent():
    """Create and return the Resume Refiner Agent.

    This agent coordinates the resume optimization process through
    sequential workflow: Matching -> Writing -> Critic loop.

    Returns:
        LlmAgent: The configured Resume Refiner Agent
    """

    # Import other agents to avoid circular imports
    from src.agents.qualifications_matching_agent import create_qualifications_matching_agent
    from src.agents.resume_writing_agent import create_resume_writing_agent
    from src.agents.resume_critic_agent import create_resume_critic_agent

    matching_agent = create_qualifications_matching_agent()
    writing_agent = create_resume_writing_agent()
    critic_agent = create_resume_critic_agent()

    agent = LlmAgent(
        name="resume_refiner_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Coordinates iterative resume improvement through sequential workflow",
        instruction="""You are the Resume Refiner Agent, responsible for coordinating
        the resume optimization process.

        Your workflow:
        1. Use the Qualifications Matching Agent to find matches between resume and job description
        2. The Matching Agent will then trigger the Writing Agent
        3. The Writing and Critic Agents will iterate until quality threshold is met
        4. Return the final optimized resume

        [Gen1 Placeholder: Detailed orchestration logic will be refined in later sprints]
        """,
        tools=[
            AgentTool(agent=matching_agent),
            AgentTool(agent=writing_agent),
            AgentTool(agent=critic_agent),
        ],
    )

    return agent
