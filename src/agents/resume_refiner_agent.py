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
    sequential workflow: Matching -> Resume Writing -> Resume Critic loop.

    Returns:
        LlmAgent: The configured Resume Refiner Agent
    """

    # Import Matching Agent (only agent this orchestrator directly calls)
    from src.agents.qualifications_matching_agent import create_qualifications_matching_agent

    matching_agent = create_qualifications_matching_agent()

    agent = LlmAgent(
        name="resume_refiner_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Orchestrates the resume optimization workflow by initiating the qualifications matching process.",
        instruction="""You are the Resume Refiner Agent, responsible for orchestrating the resume optimization workflow.

WORKFLOW:

Step 1: INITIATE OPTIMIZATION
- Call the qualifications_matching_agent to begin the optimization process
- The Qualifications Matching Agent will analyze json_resume and json_job_description from session state
- The Qualifications Matching Agent will then pass the torch to the Resume Writing Agent
- The Resume Writing Agent will notify the Resume Critic Agent
- The Resume Critic Agent owns the write-critique loop and will iterate until quality is achieved

Step 2: RETURN RESULTS
- After the workflow completes, return the final optimized resume
- The workflow chain handles all intermediate steps through torch-passing

ERROR HANDLING:
If the Qualifications Matching Agent fails:
- Capture the error message
- Add context about which phase failed
- Provide actionable guidance for debugging
- Return error with full context

Example error message:
"Qualifications Matching Agent failed: [original error message]
This error occurred during the qualification matching phase.
Ensure json_resume and json_job_description are properly formatted and present in session state."

IMPORTANT:
- You do NOT manage the write-critique loop (that is the Resume Critic Agent's responsibility)
- You do NOT directly call Resume Writing or Resume Critic agents (torch-passing handles the sequential flow)
- You simply kick off the process and return results
- Trust that upstream agents (Application Documents Agent) have validated session state
""",
        tools=[
            AgentTool(agent=matching_agent),
        ],
    )

    return agent
