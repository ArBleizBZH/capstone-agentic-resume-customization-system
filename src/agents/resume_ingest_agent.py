"""Resume Ingest Agent - Converts resume text to structured JSON.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY
from src.tools.session_tools import read_from_session


def save_resume_dict_to_session(tool_context: ToolContext, resume_dict: dict) -> dict:
    """Save structured resume dict to session state.

    Args:
        tool_context: ADK tool context with state access
        resume_dict: Dictionary containing structured resume data

    Returns:
        Dictionary with status and message
    """
    try:
        if not isinstance(resume_dict, dict):
            return {
                "status": "error",
                "message": "resume_dict must be a dictionary"
            }

        # Validate required fields
        if "contact_info" not in resume_dict:
            return {
                "status": "error",
                "message": "Missing required field: contact_info"
            }

        if "name" not in resume_dict.get("contact_info", {}):
            return {
                "status": "error",
                "message": "Missing required field: contact_info.name"
            }

        if "email" not in resume_dict.get("contact_info", {}):
            return {
                "status": "error",
                "message": "Missing required field: contact_info.email"
            }

        # Save to session state with standardized key
        tool_context.state["resume_dict"] = resume_dict

        return {
            "status": "success",
            "message": "Structured resume dict saved to session state",
            "sections_parsed": list(resume_dict.keys()),
            "work_history_count": len(resume_dict.get("work_history", []))
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save resume to session: {str(e)}"
        }


def create_resume_ingest_agent():
    """Create and return the Resume Ingest Agent.

    This agent converts resume text into a python dict following
    the standard resume schema. It emphasizes high-fidelity extraction with
    no fabrication of data.

    Returns:
        LlmAgent: The configured Resume Ingest Agent
    """

    agent = LlmAgent(
        name="resume_ingest_agent",
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
        description="Converts resume text to structured Python dict using the DICT SCHEMA defined below.",
        instruction="""You are the Resume Ingest Agent.

Your task: Convert raw resume text from session state into a structured Python dict and save it.

WORKFLOW:

Step 1: READ FROM SESSION
- Call read_from_session(key='resume')
- The tool returns: {"key": "resume", "value": "raw text...", "found": boolean}
- If found is False: Return "ERROR: Resume not found in session state" and stop
- If found is True: Extract the value field and proceed to Step 2

Step 2: CONVERT TO STRUCTURED DICT
- Parse the resume text into a Python dict named 'resume_dict'
- Extract ONLY information explicitly stated in the source - NO FABRICATION
- Preserve exact wording from source, especially achievements and accomplishments
- Omit any section or field not present in the source
- Organize into logical sections (see structure guide below)

Step 3: SAVE AND RESPOND
- Call save_resume_dict_to_session(resume_dict=resume_dict)
- The tool returns: {"status": "success|error", "message": "..."}
- If status is "error": Return "ERROR: Failed to save - [error message]" and stop
- If status is "success": Return "SUCCESS: Resume processed and saved to session state."

CRITICAL: Step 3 requires completing BOTH the tool call AND the text response.
After the save tool succeeds, you must generate the success message.

STRUCTURE GUIDE:
- contact_info: name, email, and any contact details (phone, location, linkedin, github, etc)
- profile_summary: summary, objective, or highlights if present
- work_history: work experience in chronological order (oldest first)
  - For each job: company, title, dates, location, responsibilities, achievements, technologies/skills
  - Preserve achievements in exact wording
  - Assign job_id as job_001, job_002, etc (oldest = job_001)
- skills: organize by category if clear, otherwise group logically
- education: institution, degree/diploma, dates, notable details
- certifications_licenses: certifications, licenses, or credentials if present
""",

    tools=[
            read_from_session,
            save_resume_dict_to_session,
        ],
    )

    return agent
