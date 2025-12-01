"""Application Documents Agent - Loads resume and job description files.

Based on Day 2b notebook patterns.
"""

from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool, ToolContext, FunctionTool
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_application_documents_agent():
    """Create and return the Application Documents Agent.

This agent coordinates the complete document processing workflow:
    1. Delegates to resume_ingest_agents to convert raw document from session state to structured resume_dict
    2. Delegates to job_description_ingest_agents to convert raw document from session state to structured job_description_dict
    3. Ingest agents save their resulting dicts to session state
    5. Returns success confirmation to parent agent

    Returns:
        LlmAgent: The configured Application Documents Agent with ingest agents
    """
    # Import ingest agents
    from src.agents.resume_ingest_agent import create_resume_ingest_agent
    from src.agents.job_description_ingest_agent import create_job_description_ingest_agent

    resume_ingest_agent = create_resume_ingest_agent()
    job_description_ingest_agent = create_job_description_ingest_agent()

    # Use home directory path (no /mnt/) for WSL compatibility
    base_dir = str(Path.home() / "")
    #TODO: join base_dir to file names    

    agent = LlmAgent(
        name="application_documents_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Coordinates loading and ingestion of application documents (resume and job description).",
        instruction="""You coordinate loading and processing application documents.

When asked to load documents:

**STEP 1: CALL RESUME INGEST AGENT (MUST BE FIRST)**
Call resume_ingest_agent with request: "Please parse resume content from session state"
Wait for its full response.

**STEP 2: CHECK STEP 1 RESPONSE AND CONTINUE**
Check for the keyword "ERROR:". If found, return error and stop.
If "SUCCESS:", proceed to Step 3.

**STEP 3: CALL JOB DESCRIPTION INGEST AGENT (MUST BE SECOND)**
Call job_description_ingest_agent with request: "Please parse job description content from session state"
Wait for its full response.

**STEP 4: CHECK STEP 3 RESPONSE AND CONTINUE**
Check the response for the keyword "ERROR:". If found, return error and stop.
If "SUCCESS:": The final data has been saved, proceed to Step 5.

**STEP 5: CRITICAL: GENERATE MANDATORY FINAL SUCCESS RESPONSE NOW**
DO NOT STOP processing. DO NOT RETURN None.

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

When calling sub-agents (ingest agents):
- Check the sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found: Log error, immediately stop processing
- Return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE HERE>" to parent agent

When using tools:
- If tool fails: Log error and return "ERROR: [application_documents_agent] <INSERT FULL ERROR DESCRIPTION HERE>" to parent agent

Log all errors before returning them to parent agent.

MANDATORY FINAL RESPONSE FORMAT:
After all tools complete successfully, you MUST return a success message.

Use this EXACT format:
FINAL RESPONSE MUST BE ONLY THIS TEXT: "SUCCESS: Both documents have been loaded, processed, and saved to session state." DO NOT call any tool with this string. DO NOT use function_call.

The parent agent will NOT extract data from your response - the data is already in session state.

""",
        tools=[
            AgentTool(agent=resume_ingest_agent),
            AgentTool(agent=job_description_ingest_agent),
        ],
        sub_agents=[
            resume_ingest_agent,
            job_description_ingest_agent,
        ],
    )

    return agent
