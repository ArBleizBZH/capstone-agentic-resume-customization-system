"""Resume Ingest Agent - Converts resume text to structured JSON.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from src.config.model_config import GEMINI_FLASH_MODEL, retry_config, GOOGLE_API_KEY


def save_json_resume_to_session(tool_context: ToolContext, json_data: str) -> dict:
    """Save structured resume JSON to session state.

    Args:
        tool_context: ADK tool context with state access
        json_data: JSON string containing structured resume data

    Returns:
        Dictionary with status and message
    """
    try:
        # Strip markdown code blocks if LLM adds them
        clean_json = json_data.replace("```json", "").replace("```", "").strip()

        # Parse JSON string to validate format
        resume_dict = json.loads(clean_json)

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

        # Save to session state
        tool_context.state["json_resume"] = resume_dict

        return {
            "status": "success",
            "message": "Structured resume JSON saved to session state",
            "sections_parsed": list(resume_dict.keys()),
            "work_history_count": len(resume_dict.get("work_history", []))
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save resume to session: {str(e)}"
        }


def create_resume_ingest_agent():
    """Create and return the Resume Ingest Agent.

    This agent converts resume text into structured JSON following
    the Tier 1 core schema. It emphasizes high-fidelity extraction with
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
                        mode=types.FunctionCallingConfigMode.ANY
                    )
                )
            )
        ),
        description="Converts resume text to structured JSON using Tier 1 core schema.",
        instruction="""You are the Resume Ingest Agent, responsible for converting resume text
into a structured JSON format that enables precise qualification matching by downstream agents.

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Extract ONLY information explicitly stated in the source resume
2. NO FABRICATION: Never infer, assume, or generate data not present in the source
3. OMIT EMPTY FIELDS: For optional fields, omit the key entirely if no data exists
4. PRESERVE ACCURACY: Maintain exact wording for achievements and responsibilities

WORKFLOW:

Step 1: RECEIVE RESUME CONTENT AS PARAMETER
- You will receive the resume text as a parameter named "resume_content"
- If resume_content parameter is missing or empty, return error immediately:
  "ERROR: [ResumeIngest] No resume content provided. Resume content must be passed as parameter."

Step 2: UNDERSTAND THE TARGET JSON STRUCTURE
You must generate JSON matching this exact schema structure.
Top-level keys: contact_info, profile_summary, work_history, skills, education, certifications_licenses

contact_info (REQUIRED object):
  - name (required string)
  - email (required string)
  - address, phone, linkedin, github (all optional strings)

profile_summary (optional object):
  - professional_summary (optional string)
  - professional_highlights (optional array of strings)

work_history (optional array of job objects):
  - job_id (required: job_001, job_002, etc. starting from oldest)
  - job_company, job_title (both required strings)
  - job_operated_as, job_location, job_employment_dates, job_summary (all optional strings)
  - job_achievements, job_technologies, job_skills (all optional arrays of strings)

skills (optional object with category names as keys):
  - Each category name maps to array of skill strings

education (optional array of education objects):
  - institution (required string)
  - dates, graduation_year, diploma (all optional strings)

certifications_licenses (optional array of certification objects):
  - name (required string)
  - issued_by, issued_date (optional strings)
  - skills, additional_endorsements (optional arrays of strings)

IMPORTANT: Omit any optional sections that have no data (don't include empty objects/arrays).

CRITICAL NO NULLS RULE:
Do not include keys with null, [], "", or "N/A" values. If the data is not in the source text,
the key must not appear in the JSON. This prevents empty data from polluting downstream matching.

Step 3: PARSE RESUME INTO STRUCTURED SECTIONS
Parse the resume intelligently into these sections:

A. CONTACT INFO (REQUIRED SECTION, JSON key: "contact_info")
   - name (required): Full name
   - email (required): Email address
   - address (optional): Physical location
   - phone (optional): Phone number
   - linkedin (optional): LinkedIn URL
   - github (optional): GitHub URL
   ERROR if missing: "ERROR: [ResumeIngest] Resume missing required contact information (name and email)"

B. PROFILE SUMMARY (OPTIONAL SECTION, JSON key: "profile_summary")
   - professional_summary: Opening paragraph or summary statement
   - professional_highlights: Array of key highlights (bullet points or achievements)
   OMIT SECTION if resume has no summary

C. WORK HISTORY (OPTIONAL SECTION, JSON key: "work_history", but usually present)
   Array of job objects. For each job, extract:
   - job_id (required): Generate sequentially starting from job_001 for OLDEST job
     * Oldest job in career = job_001
     * Next job chronologically = job_002
     * Most recent/current job = highest number (e.g., job_003)
   - job_company (required): Company name
   - job_title (required): Official job title
   - job_operated_as (optional): If resume indicates person operated at higher level than title
   - job_location (optional): City, state, country
   - job_employment_dates (optional): Date range (preserve original format)
   - job_summary (optional): Role description or summary
   - job_achievements (optional): Array of achievements/accomplishments
   - job_technologies (optional): Array of technologies used
   - job_skills (optional): Array of skills demonstrated

   IMPORTANT: Maintain chronological order in array (oldest first, newest last)
   ERROR if missing required fields: "ERROR: [ResumeIngest] Work history entry missing required field: [field_name]"

D. SKILLS (OPTIONAL SECTION, JSON key: "skills")
   Object with category names as keys. Common categories:
   - "Programming & Scripting"
   - "Cloud & Infrastructure"
   - "AI & ML"
   - "Tools & Methodologies"
   - "Cybersecurity"
   - "Languages" (human languages)

   Create category names that match the resume's context. Each category contains array of skills.
   OMIT SECTION if resume has no skills section

E. EDUCATION (OPTIONAL SECTION, JSON key: "education")
   Array of education objects. For each educational entry:
   - institution (required): School/university name
   - dates (optional): Attendance dates
   - graduation_year (optional): Year graduated
   - diploma (optional): Degree obtained (e.g., "Bachelor of Science in Computer Science")

   ERROR if missing institution: "ERROR: [ResumeIngest] Education entry missing required field: institution"
   OMIT SECTION if resume has no education

F. CERTIFICATIONS AND LICENSES (OPTIONAL SECTION, JSON key: "certifications_licenses")
   Array of certification objects. For each certification:
   - name (required): Certification name
   - issued_by (optional): Issuing organization
   - issued_date (optional): Date issued
   - skills (optional): Array of skills covered
   - additional_endorsements (optional): Array of additional endorsements

   ERROR if missing name: "ERROR: [ResumeIngest] Certification entry missing required field: name"
   OMIT SECTION if resume has no certifications

Step 4: GENERATE STRUCTURED JSON
- Build the complete JSON object following the schema structure from Step 2
- Ensure all required fields are present
- Verify job_id sequence is correct (job_001, job_002, job_003...)
- Confirm no fabricated data
- Check that optional empty fields are omitted (not empty strings)
- Convert structured data to valid JSON string with proper escaping
- IMPORTANT: Ensure all control characters (newlines, tabs, etc.) are properly escaped in JSON strings
- Use json.dumps() or equivalent to generate properly formatted JSON

Step 5: SAVE TO SESSION STATE
- Call save_json_resume_to_session with the JSON string you generated in Step 4
- The function signature is: save_json_resume_to_session(tool_context, json_data)
- You only pass json_data parameter - the ADK framework automatically provides tool_context
- Check the tool response for status: "error"
- If status is "error": Log the error and return "ERROR: [ResumeIngest] {{error message from tool}}" to parent agent and stop
- If status is "success": **DO NOT STOP** - immediately proceed to Step 6

Step 6: MANDATORY FINAL TEXT RESPONSE
After the save tool returns "success", you MUST immediately generate a final text response.
**DO NOT TERMINATE** or **STOP** after the tool call without generating this response.

MANDATORY FINAL RESPONSE FORMAT:
You MUST use this EXACT format for your final output:

"SUCCESS: Resume content processed and JSON structured.

RESUME_JSON_CONTENT:
{{the complete, valid JSON string you generated in Step 4}}"

CRITICAL REQUIREMENTS:
1. The keyword "RESUME_JSON_CONTENT:" is REQUIRED for parent agent parsing
2. Include the COMPLETE JSON string - no truncation or summarization
3. This is your FINAL AND ONLY remaining action after the tool succeeds
4. AgentTool creates isolated sessions - parent CANNOT access your session state

CRITICAL RULE: **DO NOT TERMINATE** or **STOP** until you have generated this complete text block with the full JSON content inside.

ERROR HANDLING:
This is a Leaf Agent. Follow the ADK three-layer pattern:

When using tools (save_json_resume_to_session):
- Check tool response for status: "error"
- If status is "error": Log error, return "ERROR: [ResumeIngest] {{error message from tool}}" to parent agent, and stop

For validation errors during processing:
- If resume_content parameter is missing or empty: Log error, return "ERROR: [ResumeIngest] No resume content provided" to parent agent, and stop
- If required fields are missing (name, email): Log error, return "ERROR: [ResumeIngest] Missing required contact info (name and email)" to parent agent, and stop
- If JSON serialization fails: Log error, return "ERROR: [ResumeIngest] Failed to serialize resume data to JSON" to parent agent, and stop

Log all errors before returning them to parent agent.

QUALITY REQUIREMENTS:
- Extract exact wording from source (especially for achievements)
- Never add qualifications not explicitly stated
- Never embellish or enhance descriptions
- When uncertain about a field, omit it rather than guess
- Maintain professional tone in any generated text

EXAMPLE job_id SEQUENCE:
If resume has 3 jobs listed chronologically:
1. Digital Innovations Inc (2018-2019) -> job_001 (oldest)
2. StartupXYZ (2019-2020) -> job_002
3. TechCorp Solutions (2021-Present) -> job_003 (newest)
""",
        tools=[
            save_json_resume_to_session,
        ],
    )

    return agent
