"""Application Documents Agent - Loads resume and job description files.

Based on Day 2b notebook patterns.
"""

from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def create_application_documents_agent():
    """Create and return the Application Documents Agent.

    This agent coordinates the complete document processing workflow:
    1. Loads resume and job description files using MCP filesystem
    2. Delegates to ingest agents to convert raw documents to structured dicts
    3. Ingest agents save dicts directly to session state
    4. Returns success confirmation to parent agent

    Returns:
        LlmAgent: The configured Application Documents Agent with MCP filesystem and ingest agents
    """
    # Import ingest agents
    from src.agents.resume_ingest_agent import create_resume_ingest_agent
    from src.agents.job_description_ingest_agent import create_job_description_ingest_agent

    resume_ingest_agent = create_resume_ingest_agent()
    job_description_ingest_agent = create_job_description_ingest_agent()

    # Use home directory path (no /mnt/) for WSL compatibility
    mcp_dir = str(Path.home() / "capstone_mcp_test")

    # Create MCP filesystem toolset
    # Set cwd to the MCP directory so relative paths work correctly
    # Use tool_filter to expose only canonical MCP tools per ADK documentation
    filesystem_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    mcp_dir
                ],
                cwd=mcp_dir,  # Run from the MCP directory
            ),
            timeout=30,
        ),
        tool_filter=['read_file', 'list_directory']  # Only expose canonical MCP tools per ADK docs
    )

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

**STEP 1: LOAD RESUME FILE**
Call the read_file tool with path="resume.md"
Wait for the response and store the resume text content.

**STEP 2: LOAD JOB DESCRIPTION FILE**
Call the read_file tool with path="job_description.md"
Wait for the response and store the job description text content.

**STEP 3: CHECK FOR FILE READ ERRORS AND CONTINUE**
If either file read failed, log the error and return "ERROR: [application_documents_agent] <INSERT FULL FILE READ ERROR MESSAGE HERE>" to the parent agent and stop.
If files loaded successfully: YOU MUST IMMEDIATELY CONTINUE TO STEP 4
DO NOT STOP after loading files - this is only the beginning of the workflow

**STEP 4: INGEST RESUME (REQUIRED - DO NOT SKIP)**
Once you have the full text content of 'resume.md', you MUST immediately call the resume_ingest_agent.
- Call resume_ingest_agent with the following parameter:
  * resume: The complete text content from resume.md file
- DO NOT proceed until you call this agent

**STEP 5: CHECK RESUME INGEST RESPONSE AND CONTINUE**
Check the response from resume_ingest_agent for the keyword "ERROR:"
   - If "ERROR:" is present: Log error and return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE FROM resume_ingest_agent>" to parent agent and stop
   - If "SUCCESS:" is present: YOU MUST IMMEDIATELY CONTINUE TO STEP 6
   - The resume dict has been saved to session state by the ingest agent

**STEP 6: INGEST JOB DESCRIPTION (REQUIRED - DO NOT SKIP)**
Once you have the full text content of 'job_description.md', you MUST immediately call the job_description_ingest_agent.
- Call job_description_ingest_agent with the following parameter:
  * job_description: The complete text content from job_description.md file
- DO NOT proceed until you call this agent

**STEP 7: CHECK JOB DESCRIPTION INGEST RESPONSE AND CONTINUE**
Check the response from job_description_ingest_agent for the keyword "ERROR:"
   - If "ERROR:" is present: Log error and return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE FROM job_description_ingest_agent>" to parent agent and stop
   - If "SUCCESS:" is present: YOU MUST IMMEDIATELY CONTINUE TO STEP 8
   - The job description dict has been saved to session state by the ingest agent

**STEP 8: RETURN SUCCESS MESSAGE (FINAL STEP) - MANDATORY**
This is the FINAL step. You MUST execute this step to complete the workflow.
DO NOT RETURN None. DO NOT STOP without generating a response.
RETURN a success message confirming both documents have been processed and saved to session state.

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

When calling sub-agents (ingest agents):
- Check each sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found: Log error, immediately stop processing
- Return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE HERE>" to parent agent

When using tools (read_file):
- If tool fails: Log error and return "ERROR: [application_documents_agent] <INSERT FULL ERROR DESCRIPTION HERE>" to parent agent

Log all errors before returning them to parent agent.

MANDATORY FINAL RESPONSE FORMAT:
After all tools complete successfully, you MUST return a success message.

Use this EXACT format:
"SUCCESS: Both documents have been loaded, processed, and saved to session state."

The parent agent will NOT extract data from your response - the data is already in session state.
Do NOT include JSON in your response - it's already in session state.

Always pass complete text content to ingest agents as parameters, not variable names.
Use the canonical 'read_file' tool name for MCP filesystem operations.
""",
        tools=[
            filesystem_mcp,
            AgentTool(agent=resume_ingest_agent),
            AgentTool(agent=job_description_ingest_agent),
        ],
        sub_agents=[
            resume_ingest_agent,
            job_description_ingest_agent,
        ],
    )

    return agent
