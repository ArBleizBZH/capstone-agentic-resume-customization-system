"""Job Description Ingest Agent - Converts job description text to structured python dict.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
"""

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY
from src.tools.session_tools import read_from_session


def save_job_description_dict_to_session(tool_context: ToolContext, job_description_dict: dict) -> dict:
    """Save structured job description dict to session state.

    Args:
        tool_context: ADK tool context with state access
        job_description_dict: Dictionary containing structured job description data

    Returns:
        Dictionary with status and message
    """
    try:
        if not isinstance(job_description_dict, dict):
            return {
                "status": "error",
                "message": "job_description_dict must be a dictionary"
            }

        # Validate required fields
        if "job_info" not in job_description_dict:
            return {
                "status": "error",
                "message": "Missing required section: job_info"
            }

        job_info = job_description_dict.get("job_info", {})

        if "company_name" not in job_info:
            return {
                "status": "error",
                "message": "Missing required field: job_info.company_name"
            }

        if "job_title" not in job_info:
            return {
                "status": "error",
                "message": "Missing required field: job_info.job_title"
            }

        # Save to session state with standardized key
        tool_context.state["job_description_dict"] = job_description_dict

        return {
            "status": "success",
            "message": "Structured job description dict saved to session state",
            "sections_parsed": list(job_description_dict.keys()),
            "company": job_info.get("company_name"),
            "title": job_info.get("job_title")
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save job description to session: {str(e)}"
        }


def create_job_description_ingest_agent():
    """Create and return the Job Description Ingest Agent.

    This agent converts job description text into a structured python dict with
    categorized qualifications (Option B structure) optimized for matching.

    Returns:
        LlmAgent: The configured Job Description Ingest Agent
    """

    agent = LlmAgent(
        name="job_description_ingest_agent",
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
        description="Converts job description text to structured Python dict with categorized qualifications.",
        instruction="""You are the Job Description Ingest Agent.

Your task: Convert raw job description text from session state into a structured Python dict and save it.

WORKFLOW:

Step 1: READ FROM SESSION
- Call read_from_session(key='job_description')
- The tool returns: {"key": "job_description", "value": "raw text...", "found": boolean}
- If found is False: Return "ERROR: Job description not found in session state" and stop
- If found is True: Extract the value field and proceed to Step 2

Step 2: CONVERT TO STRUCTURED DICT
- Parse the job description text into a Python dict named 'job_description_dict'
- Extract ONLY information explicitly stated in the source - NO FABRICATION
- Use flat arrays for qualifications
- Omit any section not present in the source

Step 3: SAVE AND RESPOND
- Call save_job_description_dict_to_session(job_description_dict=job_description_dict)
- The tool returns: {"status": "success|error", "message": "..."}
- If status is "error": Return "ERROR: Failed to save - [error message]" and stop
- If status is "success": Return "SUCCESS: Job description processed and saved to session state."

CRITICAL: Step 3 requires completing BOTH the tool call AND the text response.
After the save tool succeeds, you must generate the success message.

STRUCTURE GUIDE:
- job_info: company name, job title, location, employment type, about role, about company
- responsibilities: key duties as array of strings
- required_qualifications: all required items as flat array of strings
  - Include experience, technical skills, education, domain knowledge, soft skills
  - Example: ["5+ years Python", "AWS experience", "Bachelor's in CS", "Strong communication"]
- preferred_qualifications: all preferred items as flat array of strings
- benefits: perks and benefits if mentioned
""",
        tools=[
            read_from_session,
            save_job_description_dict_to_session,
        ],
    )

    return agent
