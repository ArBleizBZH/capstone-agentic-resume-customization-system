"""Job Description Ingest Agent - Converts job description text to structured JSON.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_json_job_description_to_session(tool_context: ToolContext, json_data: str) -> dict:
    """Save structured job description JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_data: JSON string containing structured job description data

    Returns:
        Dictionary with status and message
    """
    try:
        # Strip markdown code blocks if LLM adds them
        clean_json = json_data.replace("```json", "").replace("```", "").strip()

        # DEBUG: Log JSON and attempt to parse
        print(f"\n=== DEBUG JD JSON ===")
        print(f"Full JSON length: {len(clean_json)}")
        print(f"First 500 chars: {clean_json[:500]}")
        print(f"Last 500 chars: {clean_json[-500:]}")
        if len(clean_json) > 2140:
            print(f"Context around char 2140: {clean_json[2100:2180]}")
        print(f"===\n")

        # Parse JSON string to validate format
        job_description_dict = json.loads(clean_json)

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

        # Save to session state
        tool_context.state["json_job_description"] = job_description_dict

        return {
            "status": "success",
            "message": "Structured job description JSON saved to session state",
            "sections_parsed": list(job_description_dict.keys()),
            "company": job_info.get("company_name"),
            "title": job_info.get("job_title")
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
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
        description="Converts job description text to structured JSON with categorized qualifications.",
        instruction="""You are the Job Description Ingest Agent.
Your Goal: Convert job description text into structured JSON with categorized qualifications.

WORKFLOW:

1.  **RECEIVE CONTENT**: You will receive job description text as the 'job_description' parameter.
2.  **PARSE TO JSON**: Extract and structure the content into the required JSON schema (job_info, responsibilities, qualifications, benefits).
3.  **SAVE TO SESSION**: Call `save_json_job_description_to_session` with the JSON string.
4.  **GENERATE FINAL RESPONSE**: After the save tool completes successfully, you MUST generate a text response containing the JSON.

**CRITICAL**: Steps 3 and 4 are BOTH required. Do NOT stop after calling the save tool.
**DO NOT RETURN None** or empty content after the tool completes.
After receiving the tool's success response, you MUST proceed to Step 4 and generate your final text response.

CRITICAL RULES:
- Extract ONLY information explicitly stated in the source
- Omit empty/null fields - don't include keys with no data
- Categorize qualifications: required vs preferred, technical_skills vs domain_knowledge
- **AFTER save tool succeeds: You MUST generate the final response below**
- **DO NOT STOP after tool call - continue to Step 4**

JSON SCHEMA:
- job_info (required): company_name*, job_title*, location, employment_type, about_role, about_company
- responsibilities (optional array): key duties
- qualifications (optional object):
  - required: experience_years, technical_skills[], domain_knowledge[], soft_skills[], education[]
  - preferred: technical_skills[], domain_knowledge[], soft_skills[], certifications[], other[]
- benefits (optional array): perks and benefits
(*required fields)

MANDATORY FINAL RESPONSE FORMAT:
After the save tool returns success, you MUST generate this exact response:

"SUCCESS: Job description content processed and JSON structured.

JOB_DESCRIPTION_JSON_CONTENT:
<INSERT THE COMPLETE VALID JSON STRING GENERATED IN STEP 2>"
""",
        tools=[
            save_json_job_description_to_session,
        ],
    )

    return agent
