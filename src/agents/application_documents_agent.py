"""Application Documents Agent - Loads and validates resume and job description files.

Based on Day 2b notebook patterns for MCP toolset integration.
Sprint 003: Uses MCP filesystem server for file reading operations.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.tool_context import ToolContext
from mcp import StdioServerParameters

from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_resume_to_session(tool_context: ToolContext, content: str) -> dict:
    """Save resume content to session state.

    Args:
        tool_context: ADK tool context with state access
        content: Resume text content

    Returns:
        Dictionary with status
    """
    tool_context.state["resume"] = content
    return {"status": "success", "message": "Resume saved to session state"}


def save_jd_to_session(tool_context: ToolContext, content: str) -> dict:
    """Save job description content to session state.

    Args:
        tool_context: ADK tool context with state access
        content: Job description text content

    Returns:
        Dictionary with status
    """
    tool_context.state["job_description"] = content
    return {"status": "success", "message": "Job description saved to session state"}


def create_application_documents_agent():
    """Create and return the Application Documents Agent.

    This agent coordinates the complete document processing workflow:
    1. Loads raw resume and job description files using MCP filesystem
    2. Saves raw content to session state
    3. Delegates to ingest agents to convert raw documents to structured JSON
    4. Ingest agents save structured data to session state

    Returns:
        LlmAgent: The configured Application Documents Agent with MCP filesystem and ingest agents
    """
    # Import ingest agents (will be implemented in Sprints 004-005)
    from src.agents.resume_ingest_agent import create_resume_ingest_agent
    from src.agents.jd_ingest_agent import create_jd_ingest_agent

    resume_ingest_agent = create_resume_ingest_agent()
    jd_ingest_agent = create_jd_ingest_agent()

    # Create MCP filesystem toolset
    # Restricts access to only the input_documents directory for security
    filesystem_mcp = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    "/mnt/e/_Data/_Education/DataScience/Google_AI_Agents_Intensive/CAPSTONE/src/input_documents"
                ],
            ),
            timeout=30,
        )
    )

    agent = LlmAgent(
        name="application_documents_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Coordinates loading, validation, and ingestion of application documents (resume and job description).",
        instruction="""You are the Application Documents Agent, responsible for the complete document processing workflow.

WORKFLOW (execute in this order):

PHASE 1: Load Raw Documents
1. Use read_file tool to load resume.md from the filesystem
2. Validate resume content is non-empty and readable
3. Call save_resume_to_session with the resume content to save to session state as 'resume'
4. Use read_file tool to load job_description.md from the filesystem
5. Validate job description content is non-empty and readable
6. Call save_jd_to_session with the job description content to save to session state as 'job_description'

PHASE 2: Convert to Structured JSON (can run in parallel)
7. Call resume_ingest_agent to convert the raw resume to structured JSON
   - This agent will read 'resume' from session state
   - It will save structured data to session state as 'json_resume'
8. Call jd_ingest_agent to convert the raw job description to structured JSON
   - This agent will read 'job_description' from session state
   - It will save structured data to session state as 'json_job_description'
9. You may call both ingest agents in parallel since they are independent

COMPLETION:
10. Confirm success only after all four session state keys are populated:
    - 'resume' (raw text)
    - 'job_description' (raw text)
    - 'json_resume' (structured JSON)
    - 'json_job_description' (structured JSON)

ERROR HANDLING:
- If any file is missing, empty, or unreadable, report the specific error
- If any ingest agent fails, report the specific error
- Do not proceed to next phase if current phase fails

QUALITY REQUIREMENTS:
- Verify files exist and can be read
- Ensure content is not empty or corrupted
- Validate that ingest agents successfully create structured data
""",
        tools=[
            filesystem_mcp,
            save_resume_to_session,
            save_jd_to_session,
            AgentTool(agent=resume_ingest_agent),
            AgentTool(agent=jd_ingest_agent),
        ],
    )

    return agent
