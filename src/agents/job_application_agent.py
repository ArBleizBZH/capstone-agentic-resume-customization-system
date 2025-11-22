"""Job Application Agent - Root orchestrator for the resume customization system.

Based on Day 2a notebook patterns for LlmAgent with AgentTool.
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
1. Call application_documents_agent to load and ingest documents
   - Tell it to load resume.md and job_description.md
   - Wait for response

2. Check the response for the keyword "ERROR:"
   - If "ERROR:" is present: Log the error, Return "ERROR: {{JobApplicationAgent}} -> {{full error message from application_documents_agent}}", and stop
   - If "ERROR:" is not present: Continue to step 3

3. Extract the JSON data from the response
   - Look for RESUME_JSON and JOB_DESCRIPTION_JSON in the response
   - If extraction fails: Log error, Return "ERROR: {{JobApplicationAgent}} Failed to extract JSON data from Application Documents Agent response", and stop

4. Call resume_refiner_agent to optimize the resume
   - Pass the extracted JSON data as parameters

5. Check the response from resume_refiner_agent for the keyword "ERROR:"
   - If "ERROR:" is present: Log the error, Return "ERROR: {{JobApplicationAgent}} -> {{full error message from resume_refiner_agent}}", and stop
   - If "ERROR:" is not present: Continue to step 6

6. Return the final optimized resume to the user

DELEGATION PATTERN:
- Use application_documents_agent for all file loading and ingestion
- Use resume_refiner_agent for all resume optimization work
- You coordinate the overall workflow but do not perform the actual work
- Extract and pass data between agents as needed

QUALITY REQUIREMENTS:
- Ensure documents are loaded before proceeding to optimization
- All content in the optimized resume must be factually accurate and traceable
  to the original resume
- Never fabricate qualifications, achievements, or experience

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

When calling sub-agents:
- Check each sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found: Immediately stop processing
- Log the error message before returning to user
- Return "ERROR: {{JobApplicationAgent}} -> {{error message from child}}" to the user
- Maintain professional communication throughout

Error detection pattern:
- application_documents_agent response contains "ERROR:" → Stop and Return "ERROR: {{JobApplicationAgent}} -> {{error from child}}"
- JSON extraction fails → Log, Return "ERROR: {{JobApplicationAgent}} Failed to extract JSON data", stop
- resume_refiner_agent response contains "ERROR:" → Stop and Return "ERROR: {{JobApplicationAgent}} -> {{error from child}}"

Log all errors before returning them to the user.

RETURN FORMAT:
After successful completion, return the optimized resume to the user with clear indication
that the process is complete.
""",
        tools=[
            AgentTool(agent=application_documents_agent),
            AgentTool(agent=resume_refiner_agent),
        ],
    )

    return agent
