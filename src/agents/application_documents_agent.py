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
    2. Delegates to ingest agents to convert raw documents to structured JSON
    3. Extracts JSON data from ingest agent responses
    4. Returns structured JSON to parent agent

    Sprint 012: Implements parameter passing pattern to handle session isolation.
    Ingest agents return JSON in their responses, this agent extracts and returns it.

    Returns:
        LlmAgent: The configured Application Documents Agent with MCP filesystem and ingest agents
    """
    # Import ingest agents (implemented in Sprints 004-005)
    from src.agents.resume_ingest_agent import create_resume_ingest_agent
    from src.agents.job_description_ingest_agent import create_job_description_ingest_agent

    resume_ingest_agent = create_resume_ingest_agent()
    job_description_ingest_agent = create_job_description_ingest_agent()

    # Use home directory path (no /mnt/) for WSL compatibility
    mcp_dir = str(Path.home() / "capstone_mcp_test")

    # Create MCP filesystem toolset
    # Set cwd to the MCP directory so relative paths work correctly
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
        )
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

**STEP 1: LOAD FILES**
Call the read_file tool to load BOTH files in parallel:
   - resume.md
   - job_description.md
If either file read fails, log the error and return "ERROR: [application_documents_agent] <INSERT FULL FILE READ ERROR MESSAGE HERE>" to the parent agent and stop.

**STEP 2: INGEST RESUME (REQUIRED - DO NOT SKIP)**
Once you have the full text content of 'resume.md', you MUST immediately call the resume_ingest_agent.
   - Pass the full resume text content as the 'resume_content' parameter
   - DO NOT proceed until you call this agent

**STEP 3: CHECK RESUME INGEST RESPONSE**
Check the response from resume_ingest_agent for the keyword "ERROR:"
   - If "ERROR:" is present: Log error and return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE FROM resume_ingest_agent>" to parent agent and stop
   - If "ERROR:" is not present: Extract the JSON from the response by locating the "JSON_RESUME:" keyword and extracting everything after it

**STEP 4: INGEST JOB DESCRIPTION (REQUIRED - DO NOT SKIP)**
Once you have the full text content of 'job_description.md', you MUST immediately call the job_description_ingest_agent.
   - Pass the full job description text content as the 'job_description_content' parameter
   - DO NOT proceed until you call this agent

**STEP 5: CHECK JD INGEST RESPONSE**
Check the response from job_description_ingest_agent for the keyword "ERROR:"
   - If "ERROR:" is present: Log error and return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE FROM job_description_ingest_agent>" to parent agent and stop
   - If "ERROR:" is not present: Extract the JSON from the response by locating the "JSON_JOB_DESCRIPTION:" keyword and extracting everything after it

**STEP 6: RETURN BOTH JSON OBJECTS (FINAL STEP)**
RETURN BOTH extracted JSON objects in your final response. This is the final step - you MUST complete all previous steps before reaching here.

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

When calling sub-agents (ingest agents):
- Check each sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found: Log error, immediately stop processing
- Return "ERROR: [application_documents_agent] -> <INSERT FULL ERROR MESSAGE HERE>" to parent agent

When using tools (read_file):
- If tool fails: Log error and return "ERROR: [application_documents_agent] <INSERT FULL ERROR DESCRIPTION HERE>" to parent agent

Log all errors before returning them to parent agent.

CRITICAL JSON EXTRACTION:
The ingest agents return text responses that include the JSON data. You MUST:
- Look for the JSON data in their response text
- Extract the complete JSON object (everything between the outermost curly braces)
- Include both JSON objects in your final response text

MANDATORY FINAL RESPONSE FORMAT:
After all tools complete successfully, you MUST return BOTH JSON objects in your response.

Use this EXACT format:
"SUCCESS: Both documents have been loaded and processed.

JSON_RESUME:
<INSERT THE COMPLETE JSON RESUME HERE>

JSON_JOB_DESCRIPTION:
<INSERT THE COMPLETE JSON JOB DESCRIPTION HERE>"

This format is CRITICAL - the parent agent will extract these JSON objects from your response.
Do NOT summarize or truncate the JSON - return the COMPLETE JSON objects.

Always pass complete text content to ingest agents as parameters, not variable names.
Use the canonical 'read_file' tool name for MCP filesystem operations.
""",
        tools=[
            filesystem_mcp,
            AgentTool(agent=resume_ingest_agent),
            AgentTool(agent=job_description_ingest_agent),
        ],
    )

    return agent
