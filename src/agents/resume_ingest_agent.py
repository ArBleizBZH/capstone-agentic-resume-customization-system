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
Your Goal: Use read_from_session(key='resume') to read the resume. Then convert the resume into a structured Python dictionary that enables precise qualification matching and is saved to session state as "resume_dict" using save_resume_dict_to_session.

WORKFLOW:

Step 1: READ RESUME FROM SESSION STATE
- TOOL CALL: Use the `read_from_session` tool with 'resume' as key to retrieve the raw resume. THE ONLY KEY YOU ARE ALLOWED TO USE IS: key='resume'.
# tool_code_block_start
read_from_session(key='resume')
# tool_code_block_end
- Check the response: if "found" is false, return "ERROR: [resume_ingest_agent] Resume not found in session state" and stop
- Extract the resume text from the "value" field in the response

Step 2: PARSE TO DICT
- Extract and structure the content into a Python dictionary following the required schema (contact_info, profile_summary, work_history, skills, education, certifications_licenses)

Step 3: SAVE TO SESSION
- Call save_resume_dict_to_session with the Python dictionary
- Check the tool response for status: "error"
- If status is "error": Return "ERROR: [resume_ingest_agent] <INSERT ERROR MESSAGE FROM TOOL>" and stop

Step 4: GENERATE FINAL RESPONSE
- After the save tool completes successfully, you MUST generate a simple text response

**CRITICAL**: Steps 3 and 4 are BOTH required. Do NOT stop after calling the save tool.
**DO NOT RETURN None** or empty content after the tool completes.
After receiving the tool's success response, you MUST proceed to Step 4 and generate your final text response.

CRITICAL RULES:
- Extract ONLY information explicitly stated in the source - NO FABRICATION
- Omit empty/null fields - don't include keys with no data
- Preserve exact wording (especially achievements) - NO rephrasing
- Generate a Python dict structure, NOT a JSON string
- **AFTER save tool succeeds: You MUST generate the final response below**
- **DO NOT STOP after tool call - continue to Step 4**

DICT SCHEMA:
- contact_info (required): name*, email*, address, phone, linkedin, github
- profile_summary (optional object): professional_summary, professional_highlights[]
- work_history (optional array): job objects with job_id (job_001, job_002...), job_company*, job_title*, job_operated_as, job_location, job_employment_dates, job_summary, job_achievements[], job_technologies[], job_skills[]
- skills (optional object): category_name: [skills array]
- education (optional array): institution*, dates, graduation_year, diploma
- certifications_licenses (optional array): name*, issued_by, issued_date, skills[], additional_endorsements[]
(*required fields within that section)

IMPORTANT:
- job_id sequence: job_001 = OLDEST job, increment chronologically
- Jobs in array: chronological order (oldest first)
- NO assumptions - if data not in source, omit the key

MANDATORY FINAL RESPONSE FORMAT:
After the save tool returns success, you MUST generate this exact response:

"SUCCESS: Resume content processed and structured dict saved to session state."
""",

    tools=[
            read_from_session,
            save_resume_dict_to_session,
        ],
    )

    return agent
