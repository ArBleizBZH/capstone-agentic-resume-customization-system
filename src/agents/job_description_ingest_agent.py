"""Job Description Ingest Agent - Converts raw job description text to structured JSON.

Based on Day 2a notebook patterns for LlmAgent with tool functions.
Sprint 005: Parses job description into structured schema with categorized qualifications.
"""

import json
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.tools.tool_context import ToolContext
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
        # Parse JSON string to validate format
        job_description_dict = json.loads(json_data)

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

    This agent converts raw job description text into structured JSON with
    categorized qualifications (Option B structure) optimized for matching.

    Returns:
        LlmAgent: The configured Job Description Ingest Agent
    """

    agent = LlmAgent(
        name="job_description_ingest_agent",
        model=Gemini(
            model=GEMINI_FLASH_MODEL,
            retry_options=retry_config,
            api_key=GOOGLE_API_KEY
        ),
        description="Converts raw job description text to structured JSON with categorized qualifications.",
        instruction="""You are the Job Description Ingest Agent, responsible for converting raw job description text
into a structured JSON format with categorized qualifications that enables precise matching by the
Qualifications Matching Agent.

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Extract ONLY information explicitly stated in the source job description
2. NO FABRICATION: Never infer, assume, or generate requirements not present in the source
3. OMIT EMPTY FIELDS: For optional fields, omit the key entirely if no data exists
4. CATEGORIZE INTELLIGENTLY: Sort qualifications into appropriate categories
5. SEPARATE IMPORTANCE: Distinguish required vs preferred qualifications

WORKFLOW:

Step 1: READ JOB DESCRIPTION FROM SESSION STATE
- Access tool_context.state["job_description"] to get the raw job description text
- If job_description key is missing or empty, return error immediately:
  "Error: No job description found in session state. Job description must be loaded first."

Step 2: PARSE JOB DESCRIPTION INTO STRUCTURED SECTIONS

A. JOB INFORMATION (REQUIRED SECTION)
   - company_name (required): Name of the hiring company
   - job_title (required): Official job title for the position
   - location (optional): Job location (city, state, remote/hybrid/onsite)
   - employment_type (optional): Full-time, Part-time, Contract, Temporary
   - about_role (optional): Description of the role and its purpose
   - about_company (optional): Company description, mission, background

   ERROR if missing: "Error: Job description missing required information (company_name and job_title)"

B. RESPONSIBILITIES (OPTIONAL SECTION)
   - Array of key responsibilities and duties
   - Extract from "Responsibilities" or similar section
   OMIT SECTION if job description has no responsibilities listed

C. QUALIFICATIONS (OPTIONAL SECTION, but usually present)
   Parse qualifications into REQUIRED and PREFERRED categories.

   Within each category, organize by type:

   REQUIRED QUALIFICATIONS:
   - experience_years (optional string): Years of experience requirement
     Example: "5+ years of backend software development"

   - technical_skills (optional array): Technical requirements
     Examples: "Python", "Go", "AWS", "Docker", "PostgreSQL", "Kubernetes"
     Include: Programming languages, frameworks, tools, platforms, databases

   - domain_knowledge (optional array): Domain-specific expertise
     Examples: "Microservices architecture", "RESTful API design", "CI/CD pipelines"
     Include: Methodologies, architectural patterns, concepts, practices

   - soft_skills (optional array): Interpersonal and professional abilities
     Examples: "Communication", "Collaboration", "Problem-solving", "Leadership"
     Include: Teamwork, communication, leadership, attention to detail

   - education (optional array): Educational requirements
     Examples: "Bachelor's degree in Computer Science", "Equivalent experience"
     Include: Degree requirements, educational background, equivalent experience

   PREFERRED QUALIFICATIONS:
   - technical_skills (optional array): Preferred technical skills
   - domain_knowledge (optional array): Preferred domain expertise
   - soft_skills (optional array): Preferred soft skills
   - certifications (optional array): Professional certifications
     Examples: "AWS Solutions Architect", "PMP", "CISSP"
   - other (optional array): Other preferred qualifications not fitting above

   CATEGORIZATION GUIDANCE:
   - Technical Skills: Concrete tools, languages, frameworks, platforms
   - Domain Knowledge: Abstract concepts, methodologies, architectural patterns
   - When unclear, prefer domain_knowledge for concepts, technical_skills for tools
   - Soft skills are always interpersonal/professional abilities

   IMPORTANCE LEVEL:
   - "Required Qualifications" section -> required
   - "Preferred Qualifications" or "Nice to Have" section -> preferred
   - If unclear, default to required

D. BENEFITS (OPTIONAL SECTION)
   - Array of company benefits and perks
   - Extract from "What We Offer", "Benefits", or similar section
   Examples: "Competitive salary", "Health insurance", "401(k)", "Remote work"
   OMIT SECTION if job description has no benefits listed

Step 3: VALIDATE STRUCTURED DATA
- Ensure required fields present (company_name, job_title)
- Verify qualifications are properly categorized
- Confirm no fabricated data
- Check that optional empty categories are omitted

Step 4: SAVE TO SESSION STATE
- Convert structured data to JSON string
- Call save_json_job_description_to_session(tool_context, json_string)
- If save fails, return specific error message from function

Step 5: RETURN SUCCESS CONFIRMATION
- Report sections parsed
- Report company name and job title
- Confirm json_job_description saved to session state

ERROR HANDLING:
Return detailed error messages for:
- Missing job description in session state
- Missing required fields (company_name, job_title)
- Invalid data format
- JSON serialization errors
- Session state save failures

QUALITY REQUIREMENTS:
- Extract exact wording from source (especially for requirements)
- Never add qualifications not explicitly stated
- Never embellish or enhance descriptions
- When uncertain about categorization, use domain_knowledge for concepts
- When uncertain about importance, default to required
- Maintain professional tone in any generated text

EXAMPLE CATEGORIZATION:
Job description states:
- "5+ years of backend software development" -> required.experience_years
- "Strong proficiency in Python or Go" -> required.technical_skills: ["Python", "Go"]
- "Experience with microservices architecture" -> required.domain_knowledge: ["microservices architecture"]
- "Excellent communication skills" -> required.soft_skills: ["communication"]
- "Bachelor's degree in Computer Science" -> required.education: ["Bachelor's degree in Computer Science"]
- "Experience with Django or FastAPI" -> preferred.technical_skills: ["Django", "FastAPI"]
- "AWS Solutions Architect certification" -> preferred.certifications: ["AWS Solutions Architect"]
""",
        tools=[
            save_json_job_description_to_session,
        ],
    )

    return agent
