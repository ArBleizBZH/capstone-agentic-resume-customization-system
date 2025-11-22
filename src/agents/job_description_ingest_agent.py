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
                        mode=types.FunctionCallingConfigMode.ANY
                    )
                )
            )
        ),
        description="Converts job description text to structured JSON with categorized qualifications.",
        instruction="""You are the Job Description Ingest Agent, responsible for converting job description text
into a structured JSON format with categorized qualifications that enables precise matching by the
Qualifications Matching Agent.

CRITICAL PRINCIPLES:
1. HIGH FIDELITY: Extract ONLY information explicitly stated in the source job description
2. NO FABRICATION: Never infer, assume, or generate requirements not present in the source
3. OMIT EMPTY FIELDS: For optional fields, omit the key entirely if no data exists
4. CATEGORIZE INTELLIGENTLY: Sort qualifications into appropriate categories
5. SEPARATE IMPORTANCE: Distinguish required vs preferred qualifications

WORKFLOW:

Step 1: RECEIVE JOB DESCRIPTION CONTENT AS PARAMETER
- You will receive the job description text as a parameter named "job_description_content"
- If job_description_content parameter is missing or empty, return error immediately: "ERROR: {{job_description_ingest_agent}} No job description content provided"

Step 2: UNDERSTAND THE TARGET JSON STRUCTURE
You must generate JSON matching this exact schema structure.
Top-level keys: job_info, responsibilities, qualifications, benefits

job_info (REQUIRED object):
  - company_name (required string)
  - job_title (required string)
  - location, employment_type, about_role, about_company (all optional strings)

responsibilities (optional array of strings):
  - Array of key responsibility descriptions

qualifications (optional object with two sub-keys: required and preferred):

  required (object with optional fields):
    - experience_years (optional string)
    - technical_skills (optional array of strings)
    - domain_knowledge (optional array of strings)
    - soft_skills (optional array of strings)
    - education (optional array of strings)

  preferred (object with optional fields):
    - technical_skills (optional array of strings)
    - domain_knowledge (optional array of strings)
    - soft_skills (optional array of strings)
    - certifications (optional array of strings)
    - other (optional array of strings)

benefits (optional array of strings):
  - Array of benefit descriptions

IMPORTANT: Omit any optional sections or fields that have no data (don't include empty objects/arrays).

CRITICAL NO NULLS RULE:
Do not include keys with null, [], "", or "N/A" values. If the data is not in the source text,
the key must not appear in the JSON. This prevents empty data from polluting downstream matching.

Step 3: PARSE JOB DESCRIPTION INTO STRUCTURED SECTIONS

A. JOB INFO (REQUIRED SECTION, JSON key: "job_info")
   - company_name (required): Name of the hiring company
   - job_title (required): Official job title for the position
   - location (optional): Job location (city, state, remote/hybrid/onsite)
   - employment_type (optional): Full-time, Part-time, Contract, Temporary
   - about_role (optional): Description of the role and its purpose
   - about_company (optional): Company description, mission, background

   ERROR if missing: "ERROR: {{job_description_ingest_agent}} Job description missing required information (company_name and job_title)"

B. RESPONSIBILITIES (OPTIONAL SECTION, JSON key: "responsibilities")
   - Array of key responsibilities and duties
   - Extract from "Responsibilities" or similar section
   OMIT SECTION if job description has no responsibilities listed

C. QUALIFICATIONS (OPTIONAL SECTION, JSON key: "qualifications", but usually present)
   Object with two sub-keys: "required" and "preferred"

   Parse qualifications into REQUIRED and PREFERRED categories.

   Within each category, organize by type:

   REQUIRED QUALIFICATIONS (JSON key: "required"):
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

   PREFERRED QUALIFICATIONS (JSON key: "preferred"):
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

D. BENEFITS (OPTIONAL SECTION, JSON key: "benefits")
   - Array of company benefits and perks
   - Extract from "What We Offer", "Benefits", or similar section
   Examples: "Competitive salary", "Health insurance", "401(k)", "Remote work"
   OMIT SECTION if job description has no benefits listed

Step 4: GENERATE STRUCTURED JSON
- Build the complete JSON object following the schema structure from Step 2
- Ensure required fields present (company_name, job_title)
- Verify qualifications are properly categorized
- Confirm no fabricated data
- Check that optional empty categories are omitted
- Convert structured data to valid JSON string with proper escaping
- IMPORTANT: Ensure all control characters (newlines, tabs, etc.) are properly escaped in JSON strings
- Use json.dumps() or equivalent to generate properly formatted JSON

Step 5: SAVE TO SESSION STATE
- Call save_json_job_description_to_session with the JSON string you generated in Step 4
- The function signature is: save_json_job_description_to_session(tool_context, json_data)
- You only pass json_data parameter - the ADK framework automatically provides tool_context
- Check the tool response for status: "error"
- If status is "error": Log the error and return "ERROR: {{job_description_ingest_agent}} -> {{error message from tool}}" to parent agent, and stop
- If status is "success": **DO NOT STOP** - immediately proceed to Step 6

Step 6: MANDATORY FINAL TEXT RESPONSE
After the save tool returns "success", you MUST immediately generate a final text response.
**DO NOT TERMINATE** or **STOP** after the tool call without generating this response.

MANDATORY FINAL RESPONSE FORMAT:
You MUST use this EXACT format for your final output:

"SUCCESS: Job description content processed and JSON structured for {{company_name}} - {{job_title}}.

JOB_DESCRIPTION_JSON_CONTENT:
{{the complete, valid JSON string you generated in Step 4}}"

CRITICAL REQUIREMENTS:
1. The keyword "JOB_DESCRIPTION_JSON_CONTENT:" is REQUIRED for parent agent parsing
2. Include the COMPLETE JSON string - no truncation or summarization
3. This is your FINAL AND ONLY remaining action after the tool succeeds
4. AgentTool creates isolated sessions - parent CANNOT access your session state

CRITICAL RULE: **DO NOT TERMINATE** or **STOP** until you have generated this complete text block with the full JSON content inside.

ERROR HANDLING:
This is a Leaf Agent. Follow the ADK three-layer pattern:

When using tools (save_json_job_description_to_session):
- Check tool response for status: "error"
- If status is "error": Log error, return "ERROR: {{job_description_ingest_agent}} -> {{error message from tool}}" to parent agent, and stop

For validation errors during processing:
- If job_description_content parameter is missing or empty: Log error, return "ERROR: {{job_description_ingest_agent}} No job description content provided" to parent agent, and stop
- If required fields are missing (company_name, job_title): Log error, return "ERROR: {{job_description_ingest_agent}} Missing required job info (company_name and job_title)" to parent agent, and stop
- If JSON serialization fails: Log error, return "ERROR: {{job_description_ingest_agent}} Failed to serialize job description data to JSON" to parent agent, and stop

Log all errors before returning them to parent agent.

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
