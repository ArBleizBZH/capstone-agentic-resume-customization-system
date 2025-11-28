"""Job Description Ingest Agent - Converts job description text to structured python dict.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


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

    This agent converts job description text into structured JSON with
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
Your Goal: Convert job description text into a structured Python dictionary with categorized qualifications.

WORKFLOW:

1. **RECEIVE CONTENT**: You will receive job description text as the 'job_description' parameter.
2. **PARSE TO DICT**: Extract and structure the content into a Python dictionary named 'job_description_dict' and following the required schema (job_info, responsibilities, qualifications, benefits).
3. **SAVE TO SESSION**: Call `save_job_description_dict_to_session` with 'job_description_dict' as parameter.
4. **GENERATE FINAL RESPONSE**: After the save tool completes successfully, you MUST generate a simple text response.

**CRITICAL**: Steps 3 and 4 are BOTH required. Do NOT stop after calling the save tool.
**DO NOT RETURN None** or empty content after the tool completes.
After receiving the tool's success response, you MUST proceed to Step 4 and generate your final text response.

CRITICAL RULES:
- Extract ONLY information explicitly stated in the source
- Omit empty/null fields - don't include keys with no data
- Categorize qualifications: required vs preferred, technical_skills vs domain_knowledge
- Generate a Python dict structure, NOT a JSON string
- **AFTER save tool succeeds: You MUST generate the final response below**
- **DO NOT STOP after tool call - continue to Step 4**

DICT SCHEMA:
- job_info (required): company_name*, job_title*, location, employment_type, about_role, about_company
- responsibilities (optional array): key duties
- qualifications (optional object):
  - required: experience_years, technical_skills[], domain_knowledge[], soft_skills[], education[]
  - preferred: technical_skills[], domain_knowledge[], soft_skills[], certifications[], other[]
- benefits (optional array): perks and benefits
(*required fields)

MANDATORY FINAL RESPONSE FORMAT:
After the save tool returns success, you MUST generate this exact response:

"SUCCESS: Job description content processed and structured dict saved to session state."
""",
        tools=[
            save_job_description_dict_to_session,
        ],
    )

    return agent
