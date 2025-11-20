"""Application Documents Agent - Loads and validates resume and job description files.

Based on Day 2b notebook patterns for MCP toolset integration.
Sprint 003: Uses MCP filesystem server for file reading operations.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
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
    tool_context.state["original_resume"] = content
    return {"status": "success", "message": "Resume saved to session state"}


def save_jd_to_session(tool_context: ToolContext, content: str) -> dict:
    """Save job description content to session state.

    Args:
        tool_context: ADK tool context with state access
        content: Job description text content

    Returns:
        Dictionary with status
    """
    tool_context.state["original_jd"] = content
    return {"status": "success", "message": "Job description saved to session state"}


def create_application_documents_agent():
    """Create and return the Application Documents Agent.

    This agent handles loading and validating resume and job description files
    using the MCP filesystem server. It ensures data quality before passing to the
    workflow.

    Returns:
        LlmAgent: The configured Application Documents Agent with MCP filesystem tools
    """

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
        description="Handles loading and validation of application documents (resume and job description).",
        instruction="""You are the Application Documents Agent, responsible for loading and validating resume and job description files.

Your workflow:
1. Use the read_file tool to load resume.md
2. Validate the resume content is non-empty and readable
3. Call save_resume_to_session with the resume content to save it to session state
4. Use the read_file tool to load job_description.md
5. Validate the job description content is non-empty and readable
6. Call save_jd_to_session with the job description content to save it to session state
7. If both files are valid and saved, confirm success
8. If either file is missing, empty, or unreadable, report the specific error

Quality checks:
- Verify files exist and can be read
- Check content is not empty
- Ensure content appears to be text (not binary or corrupted)

All data must be saved to session state using the save functions provided.
Only confirm success after both files are loaded, validated, and saved to session state.
""",
        tools=[
            filesystem_mcp,
            save_resume_to_session,
            save_jd_to_session,
        ],
    )

    return agent
