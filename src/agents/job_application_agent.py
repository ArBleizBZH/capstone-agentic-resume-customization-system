"""Job Application Agent - Root orchestrator for the resume customization system.

Based on Day 2a notebook patterns for LlmAgent with AgentTool.
Sprint 003: Orchestrates Application Documents Agent and Resume Refiner Agent.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_job_application_agent():
    """Create and return the Job Application Agent.

    This is the root orchestrator that coordinates the entire
    resume customization workflow.

    Returns:
        LlmAgent: The configured Job Application Agent
    """

    # Import agents here to avoid circular imports
    from src.agents.application_documents_agent import create_application_documents_agent
    from src.agents.resume_refiner_agent import create_resume_refiner_agent

    application_documents_agent = create_application_documents_agent()
    resume_refiner_agent = create_resume_refiner_agent()

    agent = LlmAgent(
        name="job_application_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Root orchestrator for resume customization.",
        instruction="""You are the Job Application Agent, the root orchestrator responsible for
coordinating the complete resume customization workflow.

ROLE AND AUTHORITY:
You orchestrate the entire resume optimization process by delegating to specialized
agents. You are responsible for coordinating the workflow and delivering the final
optimized resume.

WORKFLOW:
1. Call the application_documents_agent to load and validate input files
   - This agent will load resume.md and job_description.md
   - It will validate both files and save them to session state
   - Wait for confirmation that both files are loaded successfully

2. If document loading fails:
   - Report the specific error to the user
   - Do not proceed to resume optimization

3. If document loading succeeds:
   - Call the resume_refiner_agent to optimize the resume
   - The Resume Refiner will read the documents from session state
   - The Resume Refiner will coordinate the optimization workflow

4. Return the final optimized resume to the user

DELEGATION PATTERN:
- Use application_documents_agent for all file loading and validation
- Use resume_refiner_agent for all resume optimization work
- You coordinate the overall workflow but do not perform the actual work

QUALITY REQUIREMENTS:
- Ensure documents are loaded before proceeding to optimization
- All content in the optimized resume must be factually accurate and traceable
  to the original resume
- Never fabricate qualifications, achievements, or experience

ERROR HANDLING:
- If document loading fails, explain the issue clearly to the user
- If resume optimization fails, relay the error to the user
- Maintain professional communication throughout
""",
        tools=[
            AgentTool(agent=application_documents_agent),
            AgentTool(agent=resume_refiner_agent),
        ],
    )

    return agent
