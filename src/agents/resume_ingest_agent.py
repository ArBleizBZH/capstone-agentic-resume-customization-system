"""Resume Ingest Agent - Converts raw resume text to structured JSON.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
Sprint 004: Parses resume into Tier 1 core schema with job_id tracking.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
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
        # Parse JSON string to validate format
        resume_dict = json.loads(json_data)

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

    This agent converts raw resume text into structured JSON following
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
            api_key=GOOGLE_API_KEY
        ),
        description="Converts raw resume text to structured JSON using Tier 1 core schema.",
        instruction="""You are the Resume Ingest Agent, responsible for converting raw resume text
into a structured JSON format that enables precise qualification matching by downstream agents.

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Extract ONLY information explicitly stated in the source resume
2. NO FABRICATION: Never infer, assume, or generate data not present in the source
3. OMIT EMPTY FIELDS: For optional fields, omit the key entirely if no data exists
4. PRESERVE ACCURACY: Maintain exact wording for achievements and responsibilities

WORKFLOW:

Step 1: READ RESUME FROM SESSION STATE
- Access tool_context.state["resume"] to get the raw resume text
- If resume key is missing or empty, return error immediately:
  "Error: No resume found in session state. Resume must be loaded first."

Step 2: PARSE RESUME INTO STRUCTURED SECTIONS
Parse the resume intelligently into these sections:

A. CONTACT INFORMATION (REQUIRED SECTION)
   - name (required): Full name
   - email (required): Email address
   - address (optional): Physical location
   - phone (optional): Phone number
   - linkedin (optional): LinkedIn URL
   - github (optional): GitHub URL
   ERROR if missing: "Error: Resume missing required contact information (name and email)"

B. PROFILE SUMMARY (OPTIONAL SECTION)
   - professional_summary: Opening paragraph or summary statement
   - professional_highlights: Array of key highlights (bullet points or achievements)
   OMIT SECTION if resume has no summary

C. WORK HISTORY (OPTIONAL SECTION, but usually present)
   For each job, extract:
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
   ERROR if missing required fields: "Error: Work history entry missing required field: [field_name]"

D. SKILLS (OPTIONAL SECTION)
   Organize skills into logical categories. Common categories:
   - "Programming & Scripting"
   - "Cloud & Infrastructure"
   - "AI & ML"
   - "Tools & Methodologies"
   - "Cybersecurity"
   - "Languages" (human languages)

   Create category names that match the resume's context. Each category contains array of skills.
   OMIT SECTION if resume has no skills section

E. EDUCATION (OPTIONAL SECTION)
   For each educational entry:
   - institution (required): School/university name
   - dates (optional): Attendance dates
   - graduation_year (optional): Year graduated
   - diploma (optional): Degree obtained (e.g., "Bachelor of Science in Computer Science")

   ERROR if missing institution: "Error: Education entry missing required field: institution"
   OMIT SECTION if resume has no education

F. CERTIFICATIONS AND LICENSES (OPTIONAL SECTION)
   For each certification:
   - name (required): Certification name
   - issued_by (optional): Issuing organization
   - issued_date (optional): Date issued
   - skills (optional): Array of skills covered
   - additional_endorsements (optional): Array of additional endorsements

   ERROR if missing name: "Error: Certification entry missing required field: name"
   OMIT SECTION if resume has no certifications

Step 3: VALIDATE STRUCTURED DATA
- Ensure all required fields are present
- Verify job_id sequence is correct (job_001, job_002, job_003...)
- Confirm no fabricated data
- Check that optional empty fields are omitted (not empty strings)

Step 4: SAVE TO SESSION STATE
- Convert structured data to JSON string
- Call save_json_resume_to_session(tool_context, json_string)
- If save fails, return specific error message from function

Step 5: RETURN SUCCESS CONFIRMATION
- Report sections parsed
- Report number of work history entries processed
- Confirm json_resume saved to session state

ERROR HANDLING:
Return detailed error messages for:
- Missing resume in session state
- Missing required fields (name, email, job_id, job_company, job_title, institution, cert name)
- Invalid data format
- JSON serialization errors
- Session state save failures

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
