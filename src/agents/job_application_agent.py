"""Job Application Agent - Root orchestrator for the resume customization system.

Based on Day 2a notebook patterns for LlmAgent with AgentTool.
Implements session state pattern for data sharing between agents.
"""

import json
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools import AgentTool
from google.adk.tools.tool_context import ToolContext
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_resume_to_session(tool_context: ToolContext, json_resume: str) -> dict:
    """Save resume JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_resume: JSON string containing structured resume data

    Returns:
        Dictionary with status and message
    """
    try:
        resume_data = json.loads(json_resume)
        tool_context.state['json_resume'] = json_resume
        return {
            "status": "success",
            "message": "Resume JSON saved to session state"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid resume JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save resume to session: {str(e)}"
        }


def save_job_description_to_session(tool_context: ToolContext, json_job_description: str) -> dict:
    """Save job description JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_job_description: JSON string containing structured job description data

    Returns:
        Dictionary with status and message
    """
    try:
        jd_data = json.loads(json_job_description)
        tool_context.state['json_job_description'] = json_job_description
        return {
            "status": "success",
            "message": "Job Description JSON saved to session state"
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid job description JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save job description to session: {str(e)}"
        }


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
            api_key=GOOGLE_API_KEY,
            generate_content_config=types.GenerateContentConfig(
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                )
            )
        ),
        description="Root orchestrator for resume customization.",
        instruction="""You are the Job Application Agent, the root orchestrator responsible for
coordinating the complete resume customization workflow.

ROLE AND AUTHORITY:
You orchestrate the entire resume optimization process by delegating to specialized
agents. You are responsible for coordinating the workflow and delivering the final
optimized resume.

WORKFLOW:

Step 1: CALL APPLICATION DOCUMENTS AGENT
- Call application_documents_agent to load and ingest documents
- Tell it to load resume.md and job_description.md
- Wait for response

Step 2: CHECK FOR ERRORS
- Check the response for the keyword "ERROR:"
- If "ERROR:" is present: Log the error, Return "ERROR: [job_application_agent] -> <INSERT FULL ERROR MESSAGE FROM application_documents_agent>", and stop
- If "ERROR:" is not present: Continue to step 3

Step 3: EXTRACT JSON DATA
- Look for JSON_RESUME and JSON_JOB_DESCRIPTION in the response
- Extract the complete JSON objects (everything between the outermost curly braces)
- If extraction fails: Log error, Return "ERROR: [job_application_agent] Failed to extract JSON data", and stop

Step 4: SAVE RESUME JSON TO SESSION STATE
- Call save_resume_to_session with json_resume parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [job_application_agent] <INSERT ERROR MESSAGE FROM TOOL>", then STOP

Step 5: SAVE JOB DESCRIPTION JSON TO SESSION STATE
- Call save_job_description_to_session with json_job_description parameter only
- Note: ADK framework automatically provides tool_context - do not pass it explicitly
- If the tool response indicates "error": Log the error and return "ERROR: [job_application_agent] <INSERT ERROR MESSAGE FROM TOOL>", then STOP

Step 6: CALL RESUME REFINER AGENT
- Call resume_refiner_agent with a SIMPLE request parameter:
  "Please optimize the resume for this job application"
- DO NOT pass JSON data as parameters - it is already in session state
- Wait for response

Step 7: CHECK REFINER RESPONSE FOR ERRORS
- Check the response from resume_refiner_agent for the keyword "ERROR:"
- If "ERROR:" is present: Log the error, Return "ERROR: [job_application_agent] -> <INSERT FULL ERROR MESSAGE FROM resume_refiner_agent>", and stop
- If "ERROR:" is not present: Continue to step 8

Step 8: RETURN FINAL OPTIMIZED RESUME

DELEGATION PATTERN:
- Use application_documents_agent for all file loading and ingestion
- Use resume_refiner_agent for all resume optimization work
- Save JSON data to session state for downstream agents to access
- Call agents with simple requests, not complex parameters
- You coordinate the overall workflow but do not perform the actual work

QUALITY REQUIREMENTS:
- Ensure documents are loaded before proceeding to optimization
- All content in the optimized resume must be factually accurate and traceable
  to the original resume
- Never fabricate qualifications, achievements, or experience

ERROR HANDLING:
This is a Coordinator Agent. Follow the ADK three-layer pattern:

When using tools (save functions):
- Check tool response for status: "error"
- If status is "error":
  * Log error
  * Return "ERROR: [job_application_agent] <INSERT ERROR MESSAGE FROM TOOL>"
  * Stop

When calling sub-agents:
- Check each sub-agent response for the keyword "ERROR:"
- If "ERROR:" is found: Immediately stop processing
- Log the error message before returning to user
- Return "ERROR: [job_application_agent] -> <INSERT ERROR MESSAGE FROM CHILD>" to the user
- Maintain professional communication throughout

Error detection pattern:
- application_documents_agent response contains "ERROR:" → Stop and Return "ERROR: [job_application_agent] -> <INSERT ERROR MESSAGE FROM CHILD>"
- JSON extraction fails → Log, Return "ERROR: [job_application_agent] Failed to extract JSON data", stop
- save tool returns error status → Log, Return "ERROR: [job_application_agent] <INSERT ERROR MESSAGE FROM TOOL>", stop
- resume_refiner_agent response contains "ERROR:" → Stop and Return "ERROR: [job_application_agent] -> <INSERT ERROR MESSAGE FROM CHILD>"

Log all errors before returning them to the user.

CRITICAL FINAL RESPONSE:
You MUST generate a final text response after all agents complete.
**DO NOT RETURN None** or empty content - this will break the workflow.
**DO NOT STOP** after sub-agent calls without generating this response.

MANDATORY FINAL RESPONSE FORMAT:
"SUCCESS: Resume customization workflow complete.

OPTIMIZED_RESUME:
<INSERT THE COMPLETE OPTIMIZED RESUME MARKDOWN HERE>

PROCESS_SUMMARY:
- Documents loaded and structured
- Qualifications matched
- Resume optimized based on job requirements"

If any sub-agent returns an ERROR, immediately relay it to the user.
""",
        tools=[
            AgentTool(agent=application_documents_agent),
            save_resume_to_session,
            save_job_description_to_session,
            AgentTool(agent=resume_refiner_agent),
        ],
        sub_agents=[
            application_documents_agent,
            resume_refiner_agent,
        ],
    )

    return agent
